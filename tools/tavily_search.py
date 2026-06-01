# tools/tavily_search.py
"""
JAQ-AI v2.0 — Tavily Web Arama Aracı

İki arayüz:
  1. TavilySearchTool  — LangChain BaseTool, agent'ların tools[] listesine eklenir
  2. tavily_search()   — geriye dönük uyumluluk fonksiyonu (eski kod için)
"""

import asyncio
import logging
from functools import partial
from typing import Any

from langchain_core.tools import BaseTool
from tavily import TavilyClient
from pydantic import Field

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Singleton client — her araçta tekrar oluşturulmuyor
_client: TavilyClient | None = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=settings.tavily_api_key.get_secret_value())
    return _client


# ── LangChain BaseTool ────────────────────────────────────────────────────────

class TavilySearchTool(BaseTool):
    """
    Tavily Advanced Search — agent'ların tools[] listesine eklenecek araç.

    Özellikler:
      - search_depth="advanced": daha derin, ham içerik döner
      - include_raw_content=True: sayfa tam metni (özetten fazlası)
      - max_results: Settings'ten alınır, agent override edebilir
    """

    name: str = "tavily_search"
    description: str = (
        "Güncel web araması yapar. Haberler, şirket bilgisi, pazar verileri, "
        "teknik dökümanlar için kullan. Input: arama sorgusu (string)."
    )
    max_results: int = Field(default_factory=lambda: settings.tavily_max_results)

    def _run(self, query: str, **kwargs: Any) -> list[dict]:
        """Senkron çalıştırma (LangChain gerektiriyor)."""
        return _search(query, max_results=self.max_results)

    async def _arun(self, query: str, **kwargs: Any) -> list[dict]:
        """Async çalıştırma — event loop'u bloklamamak için thread pool kullanır."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(_search, query, max_results=self.max_results)
        )


# ── Ortak Arama Mantığı ───────────────────────────────────────────────────────

def _search(query: str, max_results: int = 6) -> list[dict]:
    """
    Tavily advanced search — temizlenmiş sonuç listesi döner.

    Her sonuç:
        title   : str
        url     : str
        content : str  (max 800 karakter)
        score   : float (alaka skoru)
    """
    try:
        client = _get_client()
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_raw_content=False,  # True = çok büyük payload
            include_answer=True,         # Tavily'nin kendi özeti
        )
        results = []
        for r in response.get("results", []):
            results.append({
                "title":   r.get("title", ""),
                "url":     r.get("url", ""),
                "content": (r.get("content") or "")[:800],
                "score":   round(r.get("score", 0.0), 3),
            })
        # Skora göre sırala
        results.sort(key=lambda x: x["score"], reverse=True)
        logger.debug(f"Tavily: '{query}' → {len(results)} sonuç")
        return results
    except Exception as e:
        logger.error(f"Tavily arama hatası: {e}")
        return [{"title": "Arama hatası", "url": "", "content": str(e), "score": 0.0}]


def format_results_for_prompt(results: list[dict]) -> str:
    """Tavily sonuçlarını LLM prompt'una eklenecek metin bloğuna çevirir."""
    if not results:
        return "Arama sonucu bulunamadı."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']}\nURL: {r['url']}\n{r['content']}\n")
    return "\n".join(lines)


# ── Geriye Dönük Uyumluluk ────────────────────────────────────────────────────

def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """Eski kod için — yeni kod TavilySearchTool kullanmalı."""
    return _search(query, max_results=max_results)
