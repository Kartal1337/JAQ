# agents/writer_agent.py
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage

from agents.base_agent import BaseAgent
from config.prompts import WRITER_PROMPT
from tools.tavily_search import TavilySearchTool, format_results_for_prompt

logger = logging.getLogger(__name__)

_FORMAT_HINTS: dict[str, str] = {
    "blog":      "SEO başlıklı, H2/H3 bölümlü, 800-1200 kelime blog yazısı.",
    "linkedin":  "LinkedIn paylaşımı: güçlü hook (ilk satır), 3-5 paragraf, CTA ile bitir, emoji kullan.",
    "email":     "E-posta: konu satırı + selamlama + gövde + CTA + imza şablonu.",
    "rapor":     "Yönetici raporu: özet → bulgular → öneriler → sonuç. Madde madde, veri odaklı.",
    "bullet":    "Madde işaretli özet liste, max 10 madde, her madde 1 cümle.",
    "summary":   "Kısa özet paragrafı, max 150 kelime.",
}

# İçerik görevlerinde araştırma tetikleyen anahtar kelimeler
_RESEARCH_KEYWORDS = (
    "content", "post", "social media", "repurpose", "içerik", "araştır",
    "research", "trend", "haber", "news", "analiz",
)


def _detect_format(task: str) -> str:
    task_lower = task.lower()
    for keyword, hint in _FORMAT_HINTS.items():
        if keyword in task_lower:
            return hint
    return "En uygun formatta yaz. Başlık, bölümler ve net yapı kullan."


def _needs_research(task: str) -> bool:
    task_lower = task.lower()
    return any(kw in task_lower for kw in _RESEARCH_KEYWORDS)


class WriterAgent(BaseAgent):
    name = "WriterAgent"
    _base_system_prompt = WRITER_PROMPT
    tools = [TavilySearchTool(max_results=5)]

    def __init__(self) -> None:
        super().__init__(skill_name="content-repurposing")

    async def _execute(self, task: str, context: str) -> str:
        format_hint = _detect_format(task)
        prompt = self._build_prompt(task=task, context=context)

        # Araştırma gerektiren görevlerde Tavily'yi çalıştır
        search_block = ""
        if _needs_research(task):
            try:
                tool = self.tools[0]
                results = await tool._arun(task)
                if results:
                    search_block = "\n\n## Güncel Araştırma Sonuçları\n" + format_results_for_prompt(results)
                    logger.info(f"WriterAgent: {len(results)} Tavily sonucu alındı")
            except Exception as e:
                logger.warning(f"WriterAgent: Tavily araması başarısız → {e}")

        full_prompt = f"{prompt}{search_block}\n\n**Format Talimatı:** {format_hint}"
        response = await self.llm.ainvoke([HumanMessage(content=full_prompt)])
        return response.content
