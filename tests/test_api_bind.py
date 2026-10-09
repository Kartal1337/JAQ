# tests/test_api_bind.py
"""
Dashboard API varsayılanı yalnızca yerel makineye bağlanır, auto-reload kapalıdır.
Kimlik doğrulaması olmayan API ağa açılmamalı; açmak bilinçli bir .env kararıdır.
Sunucu BAŞLATILMAZ: uvicorn sahtelenir.
"""

import logging
import sys
from types import SimpleNamespace

import pytest

import main as jaq_main
from config.settings import Settings

ENV = {
    "ANTHROPIC_API_KEY": "sk-ant-test-not-a-real-key",
    "TAVILY_API_KEY": "tvly-test-not-a-real-key",
    "TELEGRAM_BOT_TOKEN": "123456:TEST-NOT-A-REAL-TOKEN",
    "TELEGRAM_CHAT_ID": "1",
}


@pytest.fixture
def clean_env(monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)
    for k in ("API_HOST", "API_PORT", "API_RELOAD"):
        monkeypatch.delenv(k, raising=False)


def test_api_settings_default_to_loopback_without_reload(clean_env):
    s = Settings(_env_file=None)

    assert s.api_host == "127.0.0.1"
    assert s.api_port == 8000
    assert s.api_reload is False


def test_api_settings_can_be_overridden_from_env(clean_env, monkeypatch):
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    monkeypatch.setenv("API_RELOAD", "true")

    s = Settings(_env_file=None)

    assert (s.api_host, s.api_reload) == ("0.0.0.0", True)


@pytest.fixture
def fake_uvicorn(monkeypatch):
    runs: list[tuple[tuple, dict]] = []
    fake = SimpleNamespace(run=lambda *a, **k: runs.append((a, k)))
    monkeypatch.setitem(sys.modules, "uvicorn", fake)
    monkeypatch.setattr(jaq_main, "_bootstrap", lambda: None)
    monkeypatch.setattr(jaq_main, "_setup_logging", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["main.py"])
    return runs


def test_dashboard_mode_binds_loopback_without_reload_by_default(fake_uvicorn):
    jaq_main.main()

    assert len(fake_uvicorn) == 1
    args, kwargs = fake_uvicorn[0]
    assert args == ("api.server:app",)
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["reload"] is False
    assert kwargs["host"] != "0.0.0.0"


def test_exposing_the_api_is_explicit_and_warns_loudly(fake_uvicorn, monkeypatch, caplog):
    from config.settings import get_settings

    monkeypatch.setattr(get_settings(), "api_host", "0.0.0.0")

    with caplog.at_level(logging.WARNING):
        jaq_main.main()

    assert fake_uvicorn[0][1]["host"] == "0.0.0.0"
    assert any("kimlik doğrulaması yok" in r.message for r in caplog.records)
