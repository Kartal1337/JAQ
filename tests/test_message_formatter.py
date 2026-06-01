# tests/test_message_formatter.py
"""Message formatter birim testleri."""

import pytest
from bot.message_formatter import (
    escape_mdv2,
    split_long_message,
    format_stats,
    format_help,
    format_welcome,
)


def test_escape_mdv2_ozel_karakterler():
    result = escape_mdv2("Hello. World!")
    assert r"\." in result
    assert r"\!" in result


def test_escape_mdv2_normal_metin():
    result = escape_mdv2("merhaba dünya")
    assert result == "merhaba dünya"


def test_split_kisa_mesaj():
    text = "Kısa mesaj"
    chunks = split_long_message(text, max_len=4000)
    assert chunks == [text]


def test_split_uzun_mesaj():
    text = "x" * 9000
    chunks = split_long_message(text, max_len=4000)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 4000


def test_format_stats_bos():
    stats = {
        "uptime": "0s 0dk",
        "total_requests": 0,
        "error_rate_pct": 0,
        "rate_limited": 0,
        "validation_errors": 0,
        "timeouts": 0,
        "agents": {},
    }
    result = format_stats(stats)
    assert "İstatistikleri" in result


def test_format_stats_agent_var():
    stats = {
        "uptime": "1s 5dk",
        "total_requests": 10,
        "error_rate_pct": 5.0,
        "rate_limited": 1,
        "validation_errors": 0,
        "timeouts": 0,
        "agents": {
            "ResearchAgent": {
                "count": 7,
                "errors": 0,
                "error_rate_pct": 0.0,
                "avg_duration_s": 3.2,
                "min_duration_s": 2.1,
                "max_duration_s": 5.4,
            }
        },
    }
    result = format_stats(stats)
    assert "ResearchAgent" in result
    assert "7" in result


def test_format_help_icerigi():
    result = format_help()
    assert "/stats" in result
    assert "/export" in result
    assert "/debug" in result
    assert "/research" in result


def test_format_welcome():
    result = format_welcome("TestBot")
    assert "TestBot" in result
