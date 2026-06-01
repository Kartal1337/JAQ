# bot/message_formatter.py
"""
JAQ-AI v2.0 — Telegram Mesaj Formatlayıcı
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.base_agent import AgentResult
    from memory.database import MemoryEntry

_MDV2_SPECIAL = r"\_*[]()~`>#+-=|{}.!"
_ESCAPE_RE = re.compile(f"([{re.escape(_MDV2_SPECIAL)}])")

_AGENT_EMOJI: dict[str, str] = {
    "ResearchAgent":       "🔍",
    "WriterAgent":         "✍️",
    "MarketAnalysisAgent": "📊",
    "CodeAgent":           "💻",
    "DIRECT":              "💬",
}

TELEGRAM_MAX_LEN = 4000


def escape_mdv2(text: str) -> str:
    return _ESCAPE_RE.sub(r"\\\1", text)


def split_long_message(text: str, max_len: int = TELEGRAM_MAX_LEN) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks: list[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        slice_ = text[:max_len]
        cut = slice_.rfind("\n\n") or slice_.rfind("\n") or slice_.rfind(" ") or max_len - 1
        if cut <= 0:
            cut = max_len - 1
        chunks.append(text[:cut + 1].rstrip())
        text = text[cut + 1:].lstrip()
    return [c for c in chunks if c]


def format_agent_response(result: "AgentResult") -> str:
    if not result.success:
        return f"⚠️ *{result.agent_name}* hata:\n`{result.error}`"
    emoji = _AGENT_EMOJI.get(result.agent_name, "🤖")
    sep = "─" * 28
    duration = f" _{result.duration_s}s_" if result.duration_s else ""
    sources_block = ""
    sources = result.metadata.get("sources", [])
    if sources:
        lines = ["\n\n📎 *Kaynaklar*"]
        for s in sources[:5]:
            title = (s.get("title") or "Kaynak")[:60]
            url = s.get("url", "")
            if url:
                lines.append(f"• [{title}]({url})")
        sources_block = "\n".join(lines)
    header = f"{emoji} *{result.agent_name}*{duration}\n{sep}\n"
    return header + result.output + sources_block


def format_welcome(bot_username: str = "JAQ") -> str:
    return (
        f"👋 Merhaba\\! Ben *{bot_username}* — senin sanal AI ofisim\\.\n\n"
        "Ne yapmamı istersin?\n"
        "• Araştırma → `/research konu`\n"
        "• İçerik yaz → `/write ne yazayım`\n"
        "• Pazar analizi → `/market sektör`\n"
        "• Kod yaz/debug → `/code görev`\n"
        "• Veya sadece yaz, doğru ajana yönlendiririm 🧠\n\n"
        "Yardım için → /help"
    )




def format_status(agents: list[str], model: str, memory_entries: int) -> str:
    agent_lines = "\n".join(f"  ✅ {a}" for a in agents)
    return (
        f"📡 *JAQ Sistem Durumu*\n\n"
        f"*Model:* `{model}`\n"
        f"*Hafıza:* {memory_entries} kayıt\n\n"
        f"*Aktif Departmanlar:*\n{agent_lines}"
    )


def format_agents(descriptions: dict[str, str]) -> str:
    lines = ["🤖 *Aktif JAQ Departmanları*\n"]
    for name, desc in descriptions.items():
        emoji = _AGENT_EMOJI.get(name, "🔹")
        lines.append(f"{emoji} *{name}*\n   _{desc}_\n")
    return "\n".join(lines)


def format_history(entries: list["MemoryEntry"]) -> str:
    if not entries:
        return "📭 Henüz kayıtlı konuşma yok\\."
    lines = ["📜 *Son Konuşmalar*\n"]
    for e in entries:
        role_icon = "👤" if e.role == "user" else "🤖"
        ts = e.timestamp[:16].replace("T", " ") if e.timestamp else ""
        preview = e.content[:120].replace("\n", " ")
        lines.append(f"{role_icon} `{ts}` — {preview}")
    return "\n".join(lines)


def format_thinking(agent_name: str | None = None) -> str:
    if agent_name:
        return f"⏳ _{agent_name} çalışıyor, lütfen bekle\\.\\.\\._"
    return "🧠 _JAQ düşünüyor\\.\\.\\._"


def format_stats(stats: dict) -> str:
    """MetricsCollector.get_stats() çıktısını Telegram mesajına çevirir."""
    agent_lines = []
    emoji_map = {
        "ResearchAgent": "🔍",
        "WriterAgent": "✍️",
        "MarketAnalysisAgent": "📊",
        "CodeAgent": "💻",
        "DIRECT": "💬",
    }
    for name, a in sorted(stats.get("agents", {}).items(), key=lambda x: x[1]["count"], reverse=True):
        emoji = emoji_map.get(name, "🤖")
        escaped_name = escape_mdv2(name)
        agent_lines.append(
            f"  {emoji} {escaped_name}: `{a['count']}` istek, "
            f"ort `{a['avg_duration_s']}s`"
        )

    agent_block = "\n".join(agent_lines) if agent_lines else "  _Henüz istek yok\\._"

    uptime = escape_mdv2(stats.get("uptime", "?"))
    return (
        f"📊 *JAQ İstatistikleri*\n\n"
        f"⏱ Çalışma süresi: `{uptime}`\n"
        f"📨 Toplam istek: `{stats.get('total_requests', 0)}`\n"
        f"❌ Hata oranı: `{stats.get('error_rate_pct', 0)}%`\n"
        f"🚫 Rate limit: `{stats.get('rate_limited', 0)}`\n"
        f"⚠️ Validasyon: `{stats.get('validation_errors', 0)}`\n"
        f"⏱ Zaman aşımı: `{stats.get('timeouts', 0)}`\n\n"
        f"*Agent Dağılımı:*\n{agent_block}"
    )


def format_debug(
    chat_id: int,
    model: str,
    memory_stats: dict,
    rate_stats: dict,
    settings_debug: dict,
) -> str:
    """Debug bilgilerini Telegram mesajına çevirir."""
    agent_usage = memory_stats.get("agent_usage", {})
    usage_lines = "\n".join(
        f"  • {escape_mdv2(k)}: {v}" for k, v in agent_usage.items()
    ) or "  _Veri yok_"

    return (
        f"🔧 *Debug Bilgisi*\n\n"
        f"*Kimlik:* `{chat_id}`\n"
        f"*Model:* `{escape_mdv2(model)}`\n\n"
        f"*Hafıza:*\n"
        f"  • Toplam kayıt: `{memory_stats.get('total', 0)}`\n"
        f"  • Konuşma turu: `{memory_stats.get('turns', 0)}`\n"
        f"  • Agent dağılımı:\n{usage_lines}\n\n"
        f"*Rate Limit:*\n"
        f"  • Kullanılan: `{rate_stats.get('used', 0)}/{rate_stats.get('limit', 0)}`\n"
        f"  • Kalan: `{rate_stats.get('remaining', 0)}`\n"
        f"  • Pencere: `{rate_stats.get('window_hours', 1)}` saat\n\n"
        f"*Ayarlar:*\n"
        f"  • Timeout: `{settings_debug.get('timeout', '?')}s`\n"
        f"  • Max token: `{settings_debug.get('max_tokens', '?')}`\n"
        f"  • Sıcaklık: `{settings_debug.get('temperature', '?')}`"
    )


def format_export_header(chat_id: int, entry_count: int) -> str:
    """Export mesajının başlık kısmı."""
    return (
        f"📤 *Konuşma Geçmişi Export*\n\n"
        f"Chat ID: `{chat_id}`\n"
        f"Kayıt sayısı: `{entry_count}`\n\n"
        f"_Aşağıdaki metin dosyasını kopyalayabilirsin:_"
    )


def format_help() -> str:
    return (
        "🛠 *JAQ Komutları*\n\n"
        "*Genel*\n"
        "/start — Hoş geldin mesajı\n"
        "/help — Bu ekran\n"
        "/status — Bot ve agent durumu\n"
        "/agents — Aktif agent listesi\n"
        "/stats — Kullanım istatistikleri\n\n"
        "*Hafıza*\n"
        "/history — Son 10 konuşma turu\n"
        "/clear — Hafızayı sıfırla\n"
        "/export — Geçmişi dışa aktar\n\n"
        "*Agent Zorlama*\n"
        "/research `<konu>` — ResearchAgent\n"
        "/write `<görev>` — WriterAgent\n"
        "/market `<sektör>` — MarketAnalysisAgent\n"
        "/code `<görev>` — CodeAgent\n\n"
        "*Geliştirici*\n"
        "/debug — Sistem detayları\n\n"
        "_Agent belirtmezsen CEO otomatik yönlendirir\\._"
    )
