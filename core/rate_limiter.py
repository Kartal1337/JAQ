# core/rate_limiter.py
"""
JAQ-AI v2.0 — Kullanıcı Başına Rate Limiter

Sliding window algoritması:
  - Her kullanıcı için son X saniyedeki istek sayısını tutar
  - Pencere dolduysa istek reddedilir
  - Burst koruması: kısa sürede yığılan istekleri engeller

Kullanım:
    limiter = get_rate_limiter()
    allowed, info = limiter.check(chat_id=123456)
    if not allowed:
        await update.message.reply_text(info["message"])
        return
"""

from __future__ import annotations

import time
import logging
from collections import deque
from dataclasses import dataclass, field
from threading import Lock

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class UserBucket:
    """Bir kullanıcının istek geçmişini tutan kova."""
    timestamps: deque = field(default_factory=deque)
    lock: Lock = field(default_factory=Lock)


class RateLimiter:
    """
    Thread-safe sliding window rate limiter.

    Her chat_id için ayrı kova tutar.
    Pencere süresi dolmuş istekleri otomatik temizler.
    """

    def __init__(
        self,
        max_requests: int | None = None,
        window_seconds: int | None = None,
        burst: int | None = None,
    ) -> None:
        self.max_requests = max_requests or settings.rate_limit_requests
        self.window_seconds = window_seconds or settings.rate_limit_window_seconds
        self.burst = burst or settings.rate_limit_burst
        self._buckets: dict[int, UserBucket] = {}
        self._global_lock = Lock()

    def _get_bucket(self, chat_id: int) -> UserBucket:
        if chat_id not in self._buckets:
            with self._global_lock:
                if chat_id not in self._buckets:
                    self._buckets[chat_id] = UserBucket()
        return self._buckets[chat_id]

    def check(self, chat_id: int) -> tuple[bool, dict]:
        """
        İstek izni kontrolü.

        Returns:
            (True, info)  — izin verildi
            (False, info) — reddedildi, info["message"] Türkçe açıklama içerir
        """
        bucket = self._get_bucket(chat_id)
        now = time.monotonic()

        with bucket.lock:
            # Pencere dışındaki istekleri temizle
            cutoff = now - self.window_seconds
            while bucket.timestamps and bucket.timestamps[0] < cutoff:
                bucket.timestamps.popleft()

            count = len(bucket.timestamps)
            remaining = self.max_requests - count

            # Burst kontrolü: son 10 saniyede çok fazla istek
            burst_cutoff = now - 10
            burst_count = sum(1 for ts in bucket.timestamps if ts > burst_cutoff)

            if burst_count >= self.burst:
                wait_time = 10 - int(now - (
                    next((ts for ts in bucket.timestamps if ts > burst_cutoff), now)
                ))
                logger.warning(f"Rate limit (burst): chat_id={chat_id}, burst={burst_count}")
                return False, {
                    "type": "burst",
                    "message": (
                        f"⚡ Çok hızlı istek gönderiyorsun\\. "
                        f"~{max(wait_time, 1)} saniye bekle\\."
                    ),
                    "remaining": remaining,
                }

            if count >= self.max_requests:
                oldest = bucket.timestamps[0]
                wait_minutes = int((oldest + self.window_seconds - now) / 60) + 1
                logger.warning(f"Rate limit (window): chat_id={chat_id}, count={count}")
                return False, {
                    "type": "window",
                    "message": (
                        f"🚫 Saat limitine ulaştın \\({self.max_requests} istek/saat\\)\\. "
                        f"~{wait_minutes} dakika bekle\\."
                    ),
                    "remaining": 0,
                }

            bucket.timestamps.append(now)
            return True, {
                "type": "ok",
                "message": "",
                "remaining": remaining - 1,
                "count": count + 1,
            }

    def get_stats(self, chat_id: int) -> dict:
        """Kullanıcının mevcut kullanım istatistiklerini döner."""
        bucket = self._get_bucket(chat_id)
        now = time.monotonic()

        with bucket.lock:
            cutoff = now - self.window_seconds
            while bucket.timestamps and bucket.timestamps[0] < cutoff:
                bucket.timestamps.popleft()
            count = len(bucket.timestamps)

        return {
            "used": count,
            "limit": self.max_requests,
            "remaining": max(0, self.max_requests - count),
            "window_hours": self.window_seconds // 3600,
        }

    def reset(self, chat_id: int) -> None:
        """Admin: kullanıcının limitini sıfırla."""
        if chat_id in self._buckets:
            with self._buckets[chat_id].lock:
                self._buckets[chat_id].timestamps.clear()
        logger.info(f"Rate limit sıfırlandı → chat_id={chat_id}")


# ── Singleton ─────────────────────────────────────────────────────────────────

_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
        logger.info(
            f"RateLimiter hazır → {settings.rate_limit_requests} istek/"
            f"{settings.rate_limit_window_seconds}s, burst={settings.rate_limit_burst}"
        )
    return _rate_limiter
