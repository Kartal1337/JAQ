# tests/test_rate_limiter.py
"""Rate limiter birim testleri."""

import time
import pytest
from core.rate_limiter import RateLimiter


@pytest.fixture
def limiter():
    """Her test için sıfır başlangıçlı limiter."""
    return RateLimiter(max_requests=5, window_seconds=3600, burst=3)


def test_ilk_istek_gecerli(limiter):
    allowed, info = limiter.check(chat_id=1)
    assert allowed is True
    assert info["type"] == "ok"


def test_limit_dolunca_reddedilir(limiter):
    for _ in range(5):
        limiter.check(chat_id=2)
    allowed, info = limiter.check(chat_id=2)
    assert allowed is False
    assert info["type"] == "window"


def test_burst_korumasi(limiter):
    """3 istek burst limiti — 4. reddedilmeli."""
    for _ in range(3):
        limiter.check(chat_id=3)
    allowed, info = limiter.check(chat_id=3)
    assert allowed is False
    assert info["type"] == "burst"


def test_farkli_kullanicilar_izole(limiter):
    """Her chat_id'nin kendi kovası var."""
    for _ in range(5):
        limiter.check(chat_id=10)
    # chat_id=11 henüz hiç istek yapmadı → geçmeli
    allowed, _ = limiter.check(chat_id=11)
    assert allowed is True


def test_reset_limiti_sifirlar(limiter):
    for _ in range(5):
        limiter.check(chat_id=20)
    limiter.reset(chat_id=20)
    allowed, _ = limiter.check(chat_id=20)
    assert allowed is True


def test_get_stats(limiter):
    limiter.check(chat_id=30)
    limiter.check(chat_id=30)
    stats = limiter.get_stats(chat_id=30)
    assert stats["used"] == 2
    assert stats["limit"] == 5
    assert stats["remaining"] == 3
