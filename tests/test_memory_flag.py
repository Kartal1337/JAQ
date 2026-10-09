# tests/test_memory_flag.py
"""
MEMORY_ENABLED bayrağı — bellek kapalıyken ChromaDB ve embedding modeli hiç
başlatılmaz, mevcut Chroma verisine dokunulmaz, bayrak açılınca bellek geri gelir.
"""

import inspect
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from config.settings import Settings
from memory import database


@pytest.fixture
def chroma_dir(monkeypatch, tmp_path):
    path = tmp_path / "chroma_db"
    monkeypatch.setattr(database.settings, "chroma_persist_dir", str(path))
    return path


@pytest.fixture
def forbid_heavy_init(monkeypatch):
    """Bellek kapalıyken bunlardan herhangi birine dokunmak testi patlatır."""
    def boom(*_a, **_k):
        raise AssertionError("bellek kapalıyken Chroma/embedding başlatıldı")

    monkeypatch.setattr(database, "Chroma", boom)
    monkeypatch.setattr(database, "SentenceTransformerEmbeddings", boom)
    monkeypatch.setattr(database, "get_embeddings", boom)
    monkeypatch.setattr(database, "_embeddings", None)
    monkeypatch.setattr(database, "_managers", {})
    # Model indirme/yükleme katmanları: bellek kapalıyken hiçbiri çağrılmamalı
    import huggingface_hub
    import sentence_transformers
    monkeypatch.setattr(sentence_transformers.SentenceTransformer, "__init__", boom)
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", boom)
    monkeypatch.setattr(huggingface_hub, "snapshot_download", boom)


# ── Ayar ──────────────────────────────────────────────────────────────────────

def test_memory_is_disabled_by_default_and_env_can_enable_it(monkeypatch):
    base = {
        "ANTHROPIC_API_KEY": "sk-ant-test-not-a-real-key",
        "TAVILY_API_KEY": "tvly-test-not-a-real-key",
        "TELEGRAM_BOT_TOKEN": "123456:TEST-NOT-A-REAL-TOKEN",
        "TELEGRAM_CHAT_ID": "1",
    }
    for k, v in base.items():
        monkeypatch.setenv(k, v)

    monkeypatch.delenv("MEMORY_ENABLED", raising=False)
    assert Settings(_env_file=None).memory_enabled is False   # unutulursa indirme tetiklenmez

    monkeypatch.setenv("MEMORY_ENABLED", "true")
    assert Settings(_env_file=None).memory_enabled is True


# ── Başlatma yok ──────────────────────────────────────────────────────────────

def test_disabled_memory_never_initializes_chroma_or_embeddings(
    monkeypatch, chroma_dir, forbid_heavy_init,
):
    monkeypatch.setattr(database.settings, "memory_enabled", False)

    memory = database.get_memory_manager(123)

    assert memory.enabled is False
    assert isinstance(memory, database.NullMemoryManager)
    assert database._managers == {}          # gerçek yönetici önbelleğine girmedi
    assert not chroma_dir.exists()           # Chroma dizini bile oluşturulmadı


# ── Null arayüzü ──────────────────────────────────────────────────────────────

def test_null_manager_covers_the_full_memory_interface():
    def public(cls):
        return {n for n, f in inspect.getmembers(cls, inspect.isfunction) if not n.startswith("_")}

    assert public(database.MemoryManager) <= public(database.NullMemoryManager)
    assert database.MemoryManager.enabled is True


def test_null_manager_is_side_effect_free_and_never_looks_like_a_wipe():
    memory = database.NullMemoryManager()

    assert memory.save_turn("a", "b", agent="DIRECT") is None
    assert memory.get_relevant_context("x") == ""
    assert memory.get_recent_history(limit=5) == []
    assert "devre dışı" in memory.get_history_summary()
    assert "devre dışı" in memory.export_history()
    assert memory.clear_user_memory() == 0
    stats = memory.get_memory_stats()
    assert stats["enabled"] is False and stats["total"] == 0


def test_null_manager_is_stateless_and_thread_safe():
    memory = database.NullMemoryManager()
    before = dict(vars(memory))

    def hammer(_):
        for i in range(200):
            memory.save_turn(f"u{i}", f"a{i}")
            memory.get_recent_history()
            memory.clear_user_memory()
        return True

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert all(pool.map(hammer, range(8)))

    assert dict(vars(memory)) == before


# ── Mevcut veri ve yeniden açılma ─────────────────────────────────────────────

def test_disabled_memory_leaves_existing_chroma_data_untouched(
    monkeypatch, chroma_dir, forbid_heavy_init,
):
    chroma_dir.mkdir()
    (chroma_dir / "chroma.sqlite3").write_bytes(b"EXISTING-USER-DATA")
    (chroma_dir / "segment").mkdir()
    (chroma_dir / "segment" / "data.bin").write_bytes(b"\x00\x01\x02")
    snapshot = {p.relative_to(chroma_dir): p.read_bytes()
                for p in chroma_dir.rglob("*") if p.is_file()}
    monkeypatch.setattr(database.settings, "memory_enabled", False)

    memory = database.get_memory_manager(5)
    memory.save_turn("u", "a")
    memory.clear_user_memory()               # kapalıyken "forget" hiçbir şey silmez
    memory.get_recent_history()

    after = {p.relative_to(chroma_dir): p.read_bytes()
             for p in chroma_dir.rglob("*") if p.is_file()}
    assert after == snapshot


def test_memory_can_be_reenabled_without_losing_the_cached_manager(monkeypatch):
    created: list[int] = []

    class FakeManager:
        enabled = True

        def __init__(self, chat_id):
            created.append(chat_id)

    monkeypatch.setattr(database, "MemoryManager", FakeManager)
    monkeypatch.setattr(database, "_managers", {})

    monkeypatch.setattr(database.settings, "memory_enabled", True)
    first = database.get_memory_manager(9)
    assert isinstance(first, FakeManager)

    monkeypatch.setattr(database.settings, "memory_enabled", False)
    assert database.get_memory_manager(9).enabled is False

    monkeypatch.setattr(database.settings, "memory_enabled", True)
    assert database.get_memory_manager(9) is first
    assert created == [9]


# ── Eski senkron checkpointer ─────────────────────────────────────────────────

def test_legacy_sync_get_checkpointer_is_deprecated_but_still_importable(monkeypatch):
    from memory import get_checkpointer            # dışa aktarım korunur (legacy kullanıcılar)

    sentinel = object()
    monkeypatch.setattr(database, "_checkpointer", sentinel)

    with pytest.warns(DeprecationWarning, match="open_async_checkpointer"):
        assert get_checkpointer() is sentinel
