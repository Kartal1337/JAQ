# bot/telegrambot.py
"""
JAQ-AI v2.0 — Async Telegram Bot (python-telegram-bot v22)

NOT: Klasör adı 'bot/' — 'telegram/' yerine.
     'telegram' ismi python-telegram-bot paketiyle çakışıyor.

Yeni özellikler (v2.1):
  - Rate limiting (kullanıcı başına istek sınırı)
  - Input validation (uzunluk, injection guard)
  - Metrics toplama (her istek kayıt altına alınır)
  - /stats komutu — kullanım istatistikleri
  - /debug komutu — sistem detayları
  - /export komutu — geçmiş dışa aktarma
"""

from __future__ import annotations

import asyncio
import logging
import sys

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config.settings import get_settings
from config.prompts import AVAILABLE_AGENTS
from core.orchestrator import process_message
from core.rate_limiter import get_rate_limiter
from core.input_validator import get_validator
from core.metrics import get_metrics
from agents.base_agent import AgentResult
from agents.research_agent import ResearchAgent
from agents.writer_agent import WriterAgent
from agents.market_analysis_agent import MarketAnalysisAgent
from agents.code_agent import CodeAgent
from memory.database import get_memory_manager
from bot.message_formatter import (
    format_agent_response,
    format_agents,
    format_debug,
    format_export_header,
    format_help,
    format_history,
    format_stats,
    format_status,
    format_welcome,
    split_long_message,
)

logger = logging.getLogger(__name__)
settings = get_settings()

_AGENT_REGISTRY: dict[str, type] = {
    "research": ResearchAgent,
    "write":    WriterAgent,
    "market":   MarketAnalysisAgent,
    "code":     CodeAgent,
}

_AGENT_DESCRIPTIONS: dict[str, str] = {
    "ResearchAgent":       "Web araştırması, haber tarama, güncel veri toplama",
    "WriterAgent":         "Blog, LinkedIn, email, rapor yazımı",
    "MarketAnalysisAgent": "Rakip analizi, pazar büyüklüğü, trend takibi",
    "CodeAgent":           "Kod yazma, debug, review, refactor",
}


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def _authorized(update: Update) -> bool:
    return update.effective_chat.id == settings.telegram_chat_id


async def _typing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )


async def _send(update: Update, text: str, parse_mode: str = ParseMode.MARKDOWN) -> None:
    chunks = split_long_message(text)
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode=parse_mode)
        except Exception:
            await update.message.reply_text(chunk, parse_mode=None)


def _check_rate_limit(update: Update) -> tuple[bool, str]:
    """Rate limit kontrolü. (allowed, error_message) döner."""
    chat_id = update.effective_chat.id
    allowed, info = get_rate_limiter().check(chat_id)
    if not allowed:
        get_metrics().record_rate_limit()
        return False, info["message"]
    return True, ""


def _check_input(text: str) -> tuple[bool, str]:
    """Input doğrulama. (valid, error_message) döner."""
    valid, msg = get_validator().validate(text)
    if not valid:
        get_metrics().record_validation_error()
    return valid, msg


async def _run_agent_direct(
    agent_key: str, task: str, chat_id: int,
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> None:
    agent = _AGENT_REGISTRY[agent_key]()
    await _typing(update, context)
    result: AgentResult = await agent.run(task=task, chat_id=chat_id)

    get_metrics().record_request(
        agent=agent.name,
        duration_s=result.duration_s,
        success=result.success,
        chat_id=chat_id,
    )

    await _send(update, format_agent_response(result))
    if result.success:
        get_memory_manager(chat_id).save_turn(
            user_msg=task, assistant_msg=result.output, agent=agent.name,
        )


# ── Komutlar ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    logger.info(f"/start — chat_id={update.effective_chat.id}")
    bot_name = (await context.bot.get_me()).username or "JAQ"
    await _send(update, format_welcome(bot_name), parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    await _send(update, format_help(), parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_agents(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    await _send(update, format_agents(_AGENT_DESCRIPTIONS), parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    entries = get_memory_manager(update.effective_chat.id).get_recent_history(limit=100)
    await _send(
        update,
        format_status(agents=AVAILABLE_AGENTS, model=settings.model_name, memory_entries=len(entries)),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    entries = get_memory_manager(update.effective_chat.id).get_recent_history(limit=10)
    await _send(update, format_history(entries), parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    count = get_memory_manager(update.effective_chat.id).clear_user_memory()
    await update.message.reply_text(
        f"🗑 Hafıza temizlendi — {count} kayıt silindi\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanım istatistiklerini göster."""
    if not _authorized(update):
        return
    stats = get_metrics().get_stats()
    await _send(update, format_stats(stats), parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sistem debug bilgilerini göster."""
    if not _authorized(update):
        return
    chat_id = update.effective_chat.id
    memory = get_memory_manager(chat_id)
    memory_stats = memory.get_memory_stats()
    rate_stats = get_rate_limiter().get_stats(chat_id)
    settings_debug = {
        "timeout": settings.agent_timeout_seconds,
        "max_tokens": settings.model_max_tokens,
        "temperature": settings.model_temperature,
    }
    await _send(
        update,
        format_debug(
            chat_id=chat_id,
            model=settings.model_name,
            memory_stats=memory_stats,
            rate_stats=rate_stats,
            settings_debug=settings_debug,
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Konuşma geçmişini düz metin olarak dışa aktar."""
    if not _authorized(update):
        return
    chat_id = update.effective_chat.id
    memory = get_memory_manager(chat_id)

    # Limit: context.args'dan al, yoksa 50
    limit = 50
    if context.args:
        try:
            limit = max(1, min(200, int(context.args[0])))
        except ValueError:
            pass

    export_text = memory.export_history(limit=limit)
    entry_count = len(memory.get_recent_history(limit=limit))

    header = format_export_header(chat_id, entry_count)
    await _send(update, header, parse_mode=ParseMode.MARKDOWN_V2)

    # Export metnini code block olarak gönder
    if export_text and export_text != "Dışa aktarılacak konuşma bulunamadı.":
        chunks = split_long_message(f"```\n{export_text}\n```")
        for chunk in chunks:
            try:
                await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await update.message.reply_text(chunk, parse_mode=None)
    else:
        await update.message.reply_text("📭 Dışa aktarılacak konuşma bulunamadı\\.", parse_mode=ParseMode.MARKDOWN_V2)


# ── Agent Zorlama Komutları ───────────────────────────────────────────────────

async def _forced_handler(agent_key: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    chat_id = update.effective_chat.id
    task = " ".join(context.args) if context.args else ""
    if not task:
        await update.message.reply_text(
            f"Kullanım: `/{agent_key} <görev>`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    # Rate limit kontrolü
    allowed, rate_msg = _check_rate_limit(update)
    if not allowed:
        await update.message.reply_text(rate_msg, parse_mode=ParseMode.MARKDOWN_V2)
        return

    # Input doğrulama
    valid, val_msg = _check_input(task)
    if not valid:
        await update.message.reply_text(val_msg, parse_mode=ParseMode.MARKDOWN_V2)
        return

    task = get_validator().sanitize(task)
    logger.info(f"/{agent_key} — task={task!r}")
    await _run_agent_direct(agent_key, task, chat_id, update, context)


async def cmd_research(u, c): await _forced_handler("research", u, c)
async def cmd_write(u, c):    await _forced_handler("write", u, c)
async def cmd_market(u, c):   await _forced_handler("market", u, c)
async def cmd_code(u, c):     await _forced_handler("code", u, c)


# ── Ana Mesaj Handler ─────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        logger.warning(f"Yetkisiz: chat_id={update.effective_chat.id}")
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id

    # Rate limit
    allowed, rate_msg = _check_rate_limit(update)
    if not allowed:
        await update.message.reply_text(rate_msg, parse_mode=ParseMode.MARKDOWN_V2)
        return

    # Input doğrulama
    valid, val_msg = _check_input(user_text)
    if not valid:
        await update.message.reply_text(val_msg, parse_mode=ParseMode.MARKDOWN_V2)
        return

    user_text = get_validator().sanitize(user_text)
    logger.info(f"Mesaj — {chat_id} | {user_text!r}")
    await _typing(update, context)

    import time
    start = time.monotonic()
    agent_used = "DIRECT"
    success = True

    try:
        response, agent_used = await asyncio.wait_for(
            process_message(chat_id=chat_id, user_input=user_text),
            timeout=settings.agent_timeout_seconds,
        )
        await _send(update, response)
    except asyncio.TimeoutError:
        get_metrics().record_timeout()
        success = False
        agent_used = "TIMEOUT"
        await update.message.reply_text("⏱ Zaman aşımı\\. Tekrar dene\\.", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"handle_message hatası: {e}", exc_info=True)
        success = False
        agent_used = "ERROR"
        await update.message.reply_text(
            f"⚠️ Hata: `{type(e).__name__}`\nTekrar dene\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    finally:
        duration = time.monotonic() - start
        get_metrics().record_request(
            agent=agent_used,
            duration_s=round(duration, 2),
            success=success,
            chat_id=chat_id,
        )


# ── Uygulama Kurulumu ─────────────────────────────────────────────────────────

async def _post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        ("start",   "Hoş geldin"),
        ("help",    "Komut listesi"),
        ("status",  "Bot durumu"),
        ("agents",  "Departmanlar"),
        ("history", "Geçmiş"),
        ("clear",   "Hafızayı sıfırla"),
        ("export",  "Geçmişi dışa aktar"),
        ("stats",   "İstatistikler"),
        ("debug",   "Sistem detayları"),
        ("research","Araştır"),
        ("write",   "Yaz"),
        ("market",  "Pazar analizi"),
        ("code",    "Kod"),
    ])
    logger.info("Komut menüsü güncellendi.")


def build_application() -> Application:
    app = (
        Application.builder()
        .token(settings.telegram_bot_token.get_secret_value())
        .post_init(_post_init)
        .build()
    )
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("status",   cmd_status))
    app.add_handler(CommandHandler("agents",   cmd_agents))
    app.add_handler(CommandHandler("history",  cmd_history))
    app.add_handler(CommandHandler("clear",    cmd_clear))
    app.add_handler(CommandHandler("stats",    cmd_stats))
    app.add_handler(CommandHandler("debug",    cmd_debug))
    app.add_handler(CommandHandler("export",   cmd_export))
    app.add_handler(CommandHandler("research", cmd_research))
    app.add_handler(CommandHandler("write",    cmd_write))
    app.add_handler(CommandHandler("market",   cmd_market))
    app.add_handler(CommandHandler("code",     cmd_code))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        level=getattr(logging, settings.log_level),
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger.info(f"JAQ-AI v2.1 — model={settings.model_name}")
    build_application().run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
