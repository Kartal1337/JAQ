# telegram/message_formatter.py
"""
JAQ-AI v2.0 — Telegram Mesaj Formatlayıcı

Tüm bot çıktısı bu modülden geçer. Sorumluluklar:
  - AgentResult → Telegram Markdown metni
  - 4096 karakter limitine göre güvenli bölme
  - MarkdownV2 özel karakterlerini escape etme
  - /status, /history, /agents sabit cevap şablonları
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
    """
    Metni max_len sınırına göre parçalara böler.
    Öncelik: paragraf sonu → satır sonu → boşluk → sert kesim.
    """
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


def format_help() -> str:
    return (
        "🛠 *JAQ Komutları*\n\n"
        "*Genel*\n"
        "/start — Hoş geldin mesajı\n"
        "/help — Bu ekran\n"
        "/status — Bot ve agent durumu\n"
        "/agents — Aktif agent listesi\n\n"
        "*Hafıza*\n"
        "/history — Son 10 konuşma turu\n"
        "/clear — Hafızayı sıfırla\n\n"
        "*Agent Zorlama*\n"
        "/research `<konu>` — ResearchAgent\n"
        "/write `<görev>` — WriterAgent\n"
        "/market `<sektör>` — MarketAnalysisAgent\n"
        "/code `<görev>` — CodeAgent\n\n"
        "_Agent belirtmezsen CEO otomatik yönlendirir\\._"
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
    emoji_map = _AGENT_EMOJI
    for name, desc in descriptions.items():
        emoji = emoji_map.get(name, "🔹")
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
