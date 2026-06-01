# memory/database.py
"""
JAQ-AI v2.0 — Hibrit Hafıza Katmanı

İki ayrı hafıza mekanizması tek sınıfta birleştirilir:

1. LangGraph SqliteSaver  →  Graph state checkpointing
   Her konuşma turu sonunda LangGraph'ın tüm state'i SQLite'a yazılır.
   Bot restart olsa bile konuşma tam olarak kaldığı yerden devam eder.

2. ChromaDB (per-user)  →  Semantik uzun-dönem hafıza
   Her kullanıcının mesajları + agent yanıtları vektör olarak saklanır.
   Yeni soru geldiğinde benzer geçmiş bağlam olarak prompt'a inject edilir.

⚠️  PRODUCTION NOTU:
    SqliteSaver tek process, düşük concurrency senaryolar içindir.
    Multi-worker deploy'da (Gunicorn, cloud run) PostgresSaver'a geçin:
        pip install langgraph-checkpoint-postgres
        from langgraph.checkpoint.postgres import PostgresSaver
    Ayrıca CVE-2026-28277 (SQLite WAL mode race condition) nedeniyle
    production'da PostgreSQL önerilir.
"""

import sqlite3
import logging
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone

from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langgraph.checkpoint.sqlite import SqliteSaver

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Embedding Model (singleton) ───────────────────────────────────────────────

_embeddings: SentenceTransformerEmbeddings | None = None


def get_embeddings() -> SentenceTransformerEmbeddings:
    """
    intfloat/multilingual-e5-large-instruct:
    - 2026 MTEB Türkçe benchmark'larında lider
    - 572M parametre, 1024-dim
    - Instruct prefix gerektirir:
        passage'lar için "passage: " prefix (save_turn içinde eklenir)
        query'ler için "query: " prefix (get_relevant_context içinde eklenir)

    Alternatif (hafif GPU/CPU için):
        "paraphrase-multilingual-mpnet-base-v2"  — 278M, 768-dim, prefix gerekmez
    """
    global _embeddings
    if _embeddings is None:
        model = "intfloat/multilingual-e5-large-instruct"
        logger.info(f"Embedding modeli yükleniyor: {model}")
        _embeddings = SentenceTransformerEmbeddings(model_name=model)
        logger.info("Embedding modeli hazır.")
    return _embeddings


# ── LangGraph Checkpointer (singleton) ───────────────────────────────────────

_checkpointer: SqliteSaver | None = None


def get_checkpointer() -> SqliteSaver:
    """
    LangGraph graph state'ini SQLite'a persist eden checkpointer.
    Thread-safe bağlantı (check_same_thread=False).
    """
    global _checkpointer
    if _checkpointer is None:
        db_path = Path(settings.checkpoint_db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        _checkpointer = SqliteSaver(conn)
        logger.info(f"LangGraph checkpointer hazır → {db_path}")
    return _checkpointer


# ── Veri Modeli ───────────────────────────────────────────────────────────────

@dataclass
class MemoryEntry:
    role: str        # "user" | "assistant"
    content: str
    agent: str       # "CEOAgent" | "ResearchAgent" | "DIRECT" vb.
    timestamp: str   # ISO 8601


# ── Hibrit Hafıza Yöneticisi ──────────────────────────────────────────────────

class MemoryManager:
    """
    Kullanıcı başına izole hafıza yöneticisi.

    Kullanım:
        manager = MemoryManager(chat_id=123456)
        manager.save_turn(user_msg="...", assistant_msg="...", agent="ResearchAgent")
        context = manager.get_relevant_context("rakip analizi")
        history = manager.get_recent_history(limit=5)
    """

    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.collection_name = settings.get_chroma_collection_name(chat_id)

        chroma_path = Path(settings.chroma_persist_dir)
        chroma_path.mkdir(parents=True, exist_ok=True)

        self._vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=get_embeddings(),
            persist_directory=str(chroma_path),
        )
        logger.debug(f"MemoryManager hazır → chat_id={chat_id}, koleksiyon={self.collection_name}")

    # ── Yazma ─────────────────────────────────────────────────────────────

    def save_turn(self, user_msg: str, assistant_msg: str, agent: str = "DIRECT") -> None:
        """
        Bir konuşma turunu ChromaDB'ye kaydeder.
        multilingual-e5-instruct modeli için "passage: " prefix eklenir.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        turn_id = f"{self.chat_id}_{timestamp}"

        documents = [
            f"passage: Kullanıcı: {user_msg}",
            f"passage: JAQ ({agent}): {assistant_msg}",
        ]
        metadatas = [
            {"role": "user",      "agent": agent, "timestamp": timestamp, "chat_id": str(self.chat_id)},
            {"role": "assistant", "agent": agent, "timestamp": timestamp, "chat_id": str(self.chat_id)},
        ]
        ids = [f"{turn_id}_user", f"{turn_id}_assistant"]

        self._vector_store.add_texts(texts=documents, metadatas=metadatas, ids=ids)
        logger.debug(f"Tur kaydedildi → agent={agent}, chat_id={self.chat_id}")

    # ── Okuma: Semantik Arama ─────────────────────────────────────────────

    def get_relevant_context(self, query: str, k: int = 4) -> str:
        """
        Mevcut sorguya semantik olarak en yakın geçmiş mesajları döner.
        multilingual-e5-instruct için "query: " prefix eklenir.
        filter={"chat_id": ...} ile kullanıcı izolasyonu sağlanır.
        """
        try:
            results = self._vector_store.similarity_search(
                f"query: {query}",
                k=k,
                filter={"chat_id": str(self.chat_id)},
            )
            if not results:
                return ""
            return "\n".join(doc.page_content for doc in results)
        except Exception as e:
            logger.warning(f"Semantik arama hatası: {e}")
            return ""

    # ── Okuma: Son N Tur ──────────────────────────────────────────────────

    def get_recent_history(self, limit: int | None = None) -> list[MemoryEntry]:
        """
        Zaman damgasına göre sıralanmış son N kaydı döner.
        where={"chat_id": ...} ile kullanıcı izolasyonu sağlanır.
        """
        max_results = limit or settings.memory_history_limit
        try:
            results = self._vector_store.get(
                where={"chat_id": str(self.chat_id)},
                limit=max_results * 2,
                include=["documents", "metadatas"],
            )
            entries = [
                MemoryEntry(
                    role=meta.get("role", "unknown"),
                    content=doc,
                    agent=meta.get("agent", "DIRECT"),
                    timestamp=meta.get("timestamp", ""),
                )
                for doc, meta in zip(results["documents"], results["metadatas"])
            ]
            entries.sort(key=lambda e: e.timestamp)
            return entries[-max_results:]
        except Exception as e:
            logger.warning(f"Geçmiş okuma hatası: {e}")
            return []

    def get_history_summary(self, limit: int | None = None) -> str:
        """CEO prompt'una inject edilecek kısa geçmiş özeti."""
        entries = self.get_recent_history(limit=limit)
        if not entries:
            return "Önceki konuşma yok."
        lines = []
        for e in entries:
            label = "👤 Kullanıcı" if e.role == "user" else f"🤖 JAQ ({e.agent})"
            lines.append(f"{label}: {e.content[:200]}")
        return "\n".join(lines)

    # ── Temizlik ──────────────────────────────────────────────────────────

    def export_history(self, limit: int = 50) -> str:
        """
        Kullanıcının konuşma geçmişini düz metin olarak export eder.
        /export komutu için kullanılır.
        """
        entries = self.get_recent_history(limit=limit)
        if not entries:
            return "Dışa aktarılacak konuşma bulunamadı."

        lines = [f"=== JAQ-AI Konuşma Geçmişi (chat_id: {self.chat_id}) ===\n"]
        for e in entries:
            ts = e.timestamp[:19].replace("T", " ") if e.timestamp else "?"
            role = "Kullanıcı" if e.role == "user" else f"JAQ ({e.agent})"
            # "passage: " prefix'ini kaldır
            content = e.content
            if content.startswith("passage: "):
                content = content[9:]
            lines.append(f"[{ts}] {role}:\n{content}\n")

        return "\n".join(lines)

    def get_memory_stats(self) -> dict:
        """Hafıza kullanım istatistiklerini döner."""
        try:
            all_entries = self._vector_store.get(
                where={"chat_id": str(self.chat_id)},
                include=["metadatas"],
            )
            metadatas = all_entries.get("metadatas", [])
            total = len(metadatas)
            user_count = sum(1 for m in metadatas if m.get("role") == "user")
            agent_count = total - user_count

            agent_usage: dict[str, int] = {}
            for m in metadatas:
                agent = m.get("agent", "DIRECT")
                agent_usage[agent] = agent_usage.get(agent, 0) + 1

            return {
                "total": total,
                "turns": user_count,
                "user_messages": user_count,
                "agent_messages": agent_count,
                "agent_usage": agent_usage,
            }
        except Exception as e:
            logger.warning(f"Hafıza istatistikleri hatası: {e}")
            return {"total": 0, "turns": 0, "user_messages": 0, "agent_messages": 0, "agent_usage": {}}

    def clear_user_memory(self) -> int:
        """
        Kullanıcının tüm ChromaDB hafızasını siler. /forget komutu için.
        Silinen kayıt sayısını döner.
        """
        try:
            existing = self._vector_store.get(where={"chat_id": str(self.chat_id)})
            ids = existing.get("ids", [])
            if ids:
                self._vector_store.delete(ids=ids)
            logger.info(f"Hafıza temizlendi → chat_id={self.chat_id}, {len(ids)} kayıt silindi")
            return len(ids)
        except Exception as e:
            logger.error(f"Hafıza temizleme hatası: {e}")
            return 0


# ── Memory Manager Cache (chat_id başına singleton) ──────────────────────────

_managers: dict[int, MemoryManager] = {}


def get_memory_manager(chat_id: int) -> MemoryManager:
    """
    Her chat_id için bir MemoryManager instance'ı döner.
    Birden fazla kez çağrılsa da aynı instance'ı verir.
    """
    if chat_id not in _managers:
        _managers[chat_id] = MemoryManager(chat_id)
    return _managers[chat_id]
