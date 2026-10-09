# tests/test_memory_threadsafety.py
"""
process_message bellek çağrılarını thread'e alır (event loop bloklanmasın diye).
Soğuk başlangıçta birden çok thread aynı anda get_embeddings()/get_memory_manager()
çağırabilir; ağır nesneler (572M model, Chroma istemcisi) tek sefer oluşturulmalı.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from memory import database

# conftest'in autouse patch'i test başına uygulanır; modül import anında gerçek fonksiyon alınır.
_real_get_embeddings = database.get_embeddings


def _run_concurrently(fn, n=6):
    barrier = threading.Barrier(n)

    def call(_):
        barrier.wait()                       # hepsi aynı anda başlasın
        return fn()

    with ThreadPoolExecutor(max_workers=n) as pool:
        return list(pool.map(call, range(n)))


def test_embedding_model_is_loaded_once_under_concurrent_cold_start(monkeypatch):
    created: list[str] = []

    class FakeEmbeddings:
        def __init__(self, model_name):
            time.sleep(0.2)                  # model yüklemesi
            created.append(model_name)

    monkeypatch.setattr(database, "SentenceTransformerEmbeddings", FakeEmbeddings)
    monkeypatch.setattr(database, "_embeddings", None)

    results = _run_concurrently(_real_get_embeddings)

    assert len(created) == 1
    assert len({id(r) for r in results}) == 1


def test_one_memory_manager_per_chat_under_concurrent_cold_start(monkeypatch):
    created: list[int] = []

    class FakeManager:
        def __init__(self, chat_id):
            time.sleep(0.2)                  # Chroma istemcisi + koleksiyon açılışı
            created.append(chat_id)

    monkeypatch.setattr(database, "MemoryManager", FakeManager)
    monkeypatch.setattr(database, "_managers", {})

    results = _run_concurrently(lambda: database.get_memory_manager(7))

    assert created == [7]
    assert len({id(r) for r in results}) == 1
