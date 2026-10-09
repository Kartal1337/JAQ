# tests/conftest.py
"""
Test izolasyonu — gerçek .env, gerçek API ve gerçek depolama kullanılmaz.

Bu dosya test modülleri import edilmeden ÖNCE yüklenir; çünkü core.* modülleri
import anında get_settings() çağırır.

  - Ortam değişkenleri sahte değerlerle ezilir.
  - Settings'in .env okuması kapatılır (gerçek anahtarlar hiç yüklenmez).
  - Checkpoint / Chroma / log yolları geçici dizine yönlendirilir.
  - Canlı LLM, Tavily ve embedding indirme çağrıları hata fırlatacak şekilde bloklanır.
"""

import atexit
import os
import shutil
import tempfile
from pathlib import Path

import pytest

_TMP_ROOT = Path(tempfile.mkdtemp(prefix="jaq-tests-"))
atexit.register(shutil.rmtree, _TMP_ROOT, ignore_errors=True)

os.environ.update({
    "ANTHROPIC_API_KEY":   "sk-ant-test-not-a-real-key",
    "TAVILY_API_KEY":      "tvly-test-not-a-real-key",
    "TELEGRAM_BOT_TOKEN":  "123456:TEST-NOT-A-REAL-TOKEN",
    "TELEGRAM_CHAT_ID":    "1",
    "CHECKPOINT_DB_PATH":  str(_TMP_ROOT / "checkpoints.db"),
    "CHROMA_PERSIST_DIR":  str(_TMP_ROOT / "chroma_db"),
    "LOG_FILE":            str(_TMP_ROOT / "jaq.log"),
})

from config import settings as _settings_module  # noqa: E402

_settings_module.Settings.model_config["env_file"] = None  # gerçek .env okunmasın
_settings_module.get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _block_live_services(monkeypatch):
    """Yanlışlıkla canlı servis çağrısı yapan test sessizce geçmesin, patlasın."""
    def _blocked(*_a, **_k):
        raise AssertionError("Test içinde canlı dış servis çağrısı engellendi")

    from langchain_anthropic import ChatAnthropic
    from tavily import TavilyClient

    monkeypatch.setattr(ChatAnthropic, "_generate", _blocked)
    monkeypatch.setattr(ChatAnthropic, "_agenerate", _blocked)
    monkeypatch.setattr(TavilyClient, "search", _blocked)
    # MemoryManager.__init__ get_embeddings() çağırır → gerçek model indirilmesin
    monkeypatch.setattr("memory.database.get_embeddings", _blocked)
