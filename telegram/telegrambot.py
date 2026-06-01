# telegram/telegrambot.py
"""
JAQ-AI v2.0 — Async Telegram Bot (python-telegram-bot v22)

Mimari:
  Serbest metin → orchestrator.process_message() (CEO routing + hafıza)
  /research /write /market /code → CEO bypass, doğrudan agent.run()

Güvenlik:
  Sadece settings.telegram_chat_id'e izin verilir, diğerleri sessizce reddedilir.
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
from agents.base_agent import AgentResult
from agents.research_agent import ResearchAgent
from agents.writer_agent import WriterAgent
from agents.market_analysis_agent import MarketAnalysisAgent
from agents.code_agent import CodeAgent
from memory.database import get_memory_manager
from telegram.message_formatter import (
    format_agent_response,
    format_agents,
    format_help,
    format_history,
    format_status,
    format_welcome,
    split_long_message,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Agent Registry ─────────────────────────────────────────────────────────────

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


# ── Yardımcı Fonksiyonlar ──────────────────────────────────────────────────────

def _authorized(update: Update) -> bool:
    """Yalnızca izin verilen chat_id'ye hizmet ver."""
    return update.effective_chat.id == settings.telegram_chat_id


async def _typing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Her LLM çağrısı öncesi 'typing' göstergesi gönder."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )


async def _send(
    update: Update,
    text: str,
    parse_mode: str = ParseMode.MARKDOWN,
) -> None:
    """
    Uzun metni parçalara bölerek gönder.

    ParseMode.MARKDOWN (v1) — agent çıktıları için: LLM yanıtları
      rastgele özel karakter içerebilir; v1 daha toleranslı.
    ParseMode.MARKDOWN_V2 — statik şablonlar için: zaten escape edilmiş.
    Parse hatasında otomatik olarak plain text'e düşer.
    """
    chunks = split_long_message(text)
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode=parse_mode)
        except Exception:
            await update.message.reply_text(chunk, parse_mode=None)


async def _run_agent_direct(
    agent_key: str,
    task: str,
    chat_id: int,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    CEO routing'i bypass ederek belirtilen agent'ı doğrudan çalıştırır.
    /research, /write, /market, /code komutları bu fonksiyonu kullanır.
    Hafızayı burada kaydeder (orchestrator kaydetmediği için).
    """
    agent = _AGENT_REGISTRY[agent_key]()
    await _typing(update, context)

    result: AgentResult = await agent.run(task=task, chat_id=chat_id)
    formatted = format_agent_response(result)
    await _send(update, formatted)

    if result.success:
        memory = get_memory_manager(chat_id)
        memory.save_turn(
            user_msg=task,
            assistant_msg=result.output,
            agent=agent.name,
        )


# ── Command Handlers ───────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    logger.info(f"/start — chat_id={update.effective_chat.id}")
    bot_name = (await context.bot.get_me()).username or "JAQ"
    await _send(update, format_welcome(bot_name), parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    logger.info("/help")
    await _send(update, format_help(), parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_agents(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    logger.info("/agents")
    await _send(update, format_agents(_AGENT_DESCRIPTIONS), parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    logger.info("/status")
    chat_id = update.effective_chat.id
    entries = get_memory_manager(chat_id).get_recent_history(limit=100)
    await _send(
        update,
        format_status(
            agents=AVAILABLE_AGENTS,
            model=settings.model_name,
            memory_entries=len(entries),
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    logger.info("/history")
    chat_id = update.effective_chat.id
    entries = get_memory_manager(chat_id).get_recent_history(limit=10)
    await _send(update, format_history(entries), parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    logger.info(f"/clear — chat_id={update.effective_chat.id}")
    count = get_memory_manager(update.effective_chat.id).clear_user_memory()
    await update.message.reply_text(
        f"🗑 Hafıza temizlendi — {count} kayıt silindi\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


# ── Forced Agent Commands ──────────────────────────────────────────────────────

async def _forced_handler(
    agent_key: str,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not _authorized(update):
        return
    chat_id = update.effective_chat.id
    task = " ".join(context.args) if context.args else ""

    if not task:
        await update.message.reply_text(
            f"Kullanım: `/{agent_key} <görev>`\nÖrnek: `/{agent_key} SaaS pazar büyüklüğü`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    logger.info(f"/{agent_key} — task={task!r}, chat_id={chat_id}")
    await _run_agent_direct(agent_key, task, chat_id, update, context)


async def cmd_research(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _forced_handler("research", update, context)

async def cmd_write(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _forced_handler("write", update, context)

async def cmd_market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _forced_handler("market", update, context)

async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _forced_handler("code", update, context)


# ── Ana Mesaj Handler ──────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Serbest metin → CEO routing → doğru agent → yanıt.
    Hafıza orchestrator içinde otomatik kaydedilir.
    """
    if not _authorized(update):
        logger.warning(f"Yetkisiz erişim: chat_id={update.effective_chat.id}")
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"Mesaj — chat_id={chat_id} | text={user_text!r}")

    await _typing(update, context)

    try:
        response = await asyncio.wait_for(
            process_message(chat_id=chat_id, user_input=user_text),
            timeout=settings.agent_timeout_seconds,
        )
        await _send(update, response)

    except asyncio.TimeoutError:
        logger.error(f"Timeout ({settings.agent_timeout_seconds}s) — chat_id={chat_id}")
        await update.message.reply_text(
            "⏱ İstek zaman aşımına uğradı\\. Lütfen tekrar dene\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    except Exception as e:
        logger.error(f"handle_message hatası: {e}", exc_info=True)
        await update.message.reply_text(
            f"⚠️ Beklenmedik hata:\n`{type(e).__name__}: {e}`\n\nTekrar dene\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )


# ── Bot İnşası ─────────────────────────────────────────────────────────────────

async def _post_init(application: Application) -> None:
    """Başlangıçta Telegram komut menüsünü güncelle."""
    await application.bot.set_my_commands([
        ("start",    "Hoş geldin mesajı"),
        ("help",     "Komut listesi"),
        ("status",   "Bot durumu"),
        ("agents",   "Aktif departmanlar"),
        ("history",  "Son konuşmalar"),
        ("clear",    "Hafızayı sıfırla"),
        ("research", "Web araştırması yap"),
        ("write",    "İçerik yaz"),
        ("market",   "Pazar analizi yap"),
        ("code",     "Kod yaz / debug et"),
    ])
    logger.info("Telegram komut menüsü güncellendi.")


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
    logger.info(f"JAQ-AI v2.0 başlatılıyor — model={settings.model_name}")
    build_application().run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
