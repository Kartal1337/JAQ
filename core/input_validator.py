# core/input_validator.py
"""
JAQ-AI v2.0 — Kullanıcı Girdisi Doğrulayıcı

Kontroller:
  1. Uzunluk sınırı (min/max)
  2. Boş/sadece boşluk girdi
  3. Tekrarlayan karakter saldırısı (spam algılama)
  4. Temel prompt injection işaretleri
  5. Sadece özel karakter içeren girdiler

Kullanım:
    validator = get_validator()
    valid, issue = validator.validate(user_text)
    if not valid:
        await update.message.reply_text(issue)
        return
"""

from __future__ import annotations

import re
import logging

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Şüpheli prompt injection kalıpları (basit heuristic)
_INJECTION_PATTERNS = [
    r"ignore\s+.{0,30}instructions?",
    r"you are now\s+(a|an|the)\s+",
    r"act as\s+(a |an )?(different|new|another|evil|jailbreak)",
    r"(disregard|forget|override)\s+.{0,20}(instructions?|rules?|guidelines?|training)",
    r"(system prompt|system message).{0,30}(reveal|show|print|output|display)",
    r"<\|.*?\|>",          # özel token kalıpları
    r"\[\[.*?\]\]",        # bazı injection vektörleri
    r"do\s+not\s+follow\s+.{0,20}(instructions?|rules?)",
    r"pretend\s+(you\s+are|to\s+be)\s+.{0,30}(no\s+restrictions|unrestricted|jailbreak)",
]

_INJECTION_RE = re.compile(
    "|".join(_INJECTION_PATTERNS),
    flags=re.IGNORECASE | re.DOTALL,
)

# Aşırı tekrar: aynı karakter arka arkaya 20+ kez
_REPEAT_RE = re.compile(r"(.)\1{19,}")


class InputValidator:
    """Kullanıcı girdisini doğrular. Hızlı, saf Python — async gerekmez."""

    def __init__(
        self,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        self.min_length = min_length or settings.min_input_length
        self.max_length = max_length or settings.max_input_length

    def validate(self, text: str) -> tuple[bool, str]:
        """
        Girdiyi doğrular.

        Returns:
            (True, "")         — geçerli
            (False, "mesaj")   — hatalı, mesaj Telegram'a gönderilecek açıklama
        """
        # 1. Boş veya sadece boşluk
        stripped = text.strip()
        if not stripped:
            return False, "⚠️ Boş mesaj gönderilemez\\."

        # 2. Minimum uzunluk
        if len(stripped) < self.min_length:
            return False, f"⚠️ Mesaj çok kısa \\(en az {self.min_length} karakter\\)\\."

        # 3. Maksimum uzunluk
        if len(text) > self.max_length:
            return False, (
                f"⚠️ Mesaj çok uzun \\({len(text):,} karakter\\)\\. "
                f"En fazla {self.max_length:,} karakter girebilirsin\\."
            )

        # 4. Tekrarlayan karakter saldırısı
        if _REPEAT_RE.search(stripped):
            return False, "⚠️ Geçersiz girdi: tekrarlayan karakterler\\."

        # 5. Sadece özel karakter içeren girdi
        if not re.search(r"[a-zA-ZğüşıöçĞÜŞİÖÇ0-9]", stripped):
            return False, "⚠️ Mesaj yeterli metin içermiyor\\."

        # 6. Prompt injection tespiti
        if _INJECTION_RE.search(stripped):
            logger.warning(f"Olası prompt injection tespit edildi: {stripped[:100]!r}")
            return False, (
                "⚠️ Bu mesaj sistem talimatlarını manipüle etmeye çalışıyor gibi görünüyor\\. "
                "Lütfen normal bir görev gir\\."
            )

        return True, ""

    def sanitize(self, text: str) -> str:
        """
        Geçerli girdiden tehlikeli karakterleri temizler.
        Validation'dan geçtikten sonra çağrılır.
        """
        # Baştaki/sondaki boşlukları temizle
        text = text.strip()
        # Çoklu boşluk satırlarını tek satıra indir
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text


# ── Singleton ─────────────────────────────────────────────────────────────────

_validator: InputValidator | None = None


def get_validator() -> InputValidator:
    global _validator
    if _validator is None:
        _validator = InputValidator()
        logger.info(
            f"InputValidator hazır → "
            f"min={settings.min_input_length}, max={settings.max_input_length}"
        )
    return _validator
