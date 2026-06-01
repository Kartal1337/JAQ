"""AffiliateBaseAgent — base class for all affiliate_factory agents.

Extends the core BaseAgent with two ChromaDB helpers that target the shared
niche knowledge collection instead of per-user conversation memory.
Callers never write 'passage: ' or 'query: ' prefixes manually.

Inheritance chain:
    AffiliateBaseAgent → BaseAgent (agents/base_agent.py)
                         ↳ retry, LLM singleton, AgentResult, run()
"""

from __future__ import annotations

from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document

from agents.base_agent import BaseAgent
from memory.database import get_embeddings


class AffiliateBaseAgent(BaseAgent):
    """Shared base for all affiliate_factory agents.

    Adds two async helpers on top of BaseAgent:
      - store_passage  → write to niche ChromaDB collection
      - search_knowledge → semantic search in niche ChromaDB collection

    The underlying Chroma instance is a lazy per-instance singleton so the
    first call bears the embedding-model load cost; subsequent calls reuse it.
    The collection is separate from per-user 'jaq_user_<chat_id>' collections.
    """

    def __init__(self, skill_name: str | None = None) -> None:
        super().__init__(skill_name=skill_name)
        self._knowledge_store: Chroma | None = None

    # ── Internal ─────────────────────────────────────────────────────────────

    def _get_knowledge_store(self) -> Chroma:
        """Lazy singleton: niche-specific ChromaDB collection.

        Uses the same chroma_persist_dir as the core project so a single
        ChromaDB server/directory is shared across collections.
        """
        if self._knowledge_store is None:
            from pathlib import Path

            from affiliate_factory.config import get_affiliate_settings

            cfg = get_affiliate_settings()
            Path(cfg.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
            self._knowledge_store = Chroma(
                collection_name=cfg.chroma_collection_name,
                embedding_function=get_embeddings(),
                persist_directory=cfg.chroma_persist_dir,
            )
        return self._knowledge_store

    # ── Public helpers ────────────────────────────────────────────────────────

    async def store_passage(self, text: str, metadata: dict[str, Any]) -> None:
        """Store *text* in the niche knowledge collection.

        Automatically prepends 'passage: ' to match the embedding model's
        asymmetric instruction format (intfloat/multilingual-e5-large-instruct).
        The underlying Chroma.add_texts call is synchronous; offload to an
        executor if blocking becomes an issue under heavy load.

        Args:
            text:     Raw passage text (without any prefix).
            metadata: Arbitrary key-value metadata stored alongside the vector.
                      Recommended keys: source, agent, niche, recorded_at, type.
        """
        ...

    async def search_knowledge(
        self,
        query: str,
        k: int = 4,
        filter: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Semantic search in the niche knowledge collection.

        Automatically prepends 'query: ' to match the embedding model's
        asymmetric instruction format.

        Args:
            query:  Natural-language search query (without any prefix).
            k:      Maximum number of documents to return.
            filter: Optional metadata filter dict forwarded to Chroma
                    (e.g. {"type": "competitor_hook", "niche": "ai_side_hustle"}).

        Returns:
            List of LangChain Document objects ordered by similarity.
        """
        ...
