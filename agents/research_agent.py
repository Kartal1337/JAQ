# agents/research_agent.py
from __future__ import annotations

import asyncio
import logging

from langchain_core.messages import HumanMessage

from agents.base_agent import BaseAgent, AgentResult
from config.prompts import RESEARCH_PROMPT
from tools.tavily_search import TavilySearchTool, format_results_for_prompt

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    _base_system_prompt = RESEARCH_PROMPT
    tools = [TavilySearchTool(max_results=8)]

    async def _execute(self, task: str, context: str) -> str:
        tool = self.tools[0]
        narrow_query = f"{task} detaylı analiz 2025 2026"

        # Paralel arama — ikisi aynı anda çalışır
        broad_results, narrow_results = await asyncio.gather(
            tool._arun(task),
            tool._arun(narrow_query),
        )

        # Tekrar eden URL'leri kaldır, skora göre en iyi 8'i al
        seen, combined = set(), []
        for r in broad_results + narrow_results:
            if r["url"] not in seen:
                seen.add(r["url"])
                combined.append(r)
        top_results = sorted(combined, key=lambda x: x["score"], reverse=True)[:8]

        search_block = format_results_for_prompt(top_results)
        prompt = self._build_prompt(task=task, context=context)
        full_prompt = f"{prompt}\n\n## Tavily Arama Sonuçları\n{search_block}"

        response = await self.llm.ainvoke([HumanMessage(content=full_prompt)])
        return response.content

    async def run(self, task: str, chat_id: int = 0, extra_context: str = "") -> AgentResult:
        """run() override: kaynakları AgentResult.metadata["sources"]'a ekler."""
        result = await super().run(task=task, chat_id=chat_id, extra_context=extra_context)
        if result.success:
            try:
                sources = await self.tools[0]._arun(task)
                result.metadata["sources"] = [
                    {"title": s["title"], "url": s["url"]}
                    for s in sources[:5]
                ]
            except Exception:
                pass
        return result
