# agents/market_analysis_agent.py
from __future__ import annotations

import asyncio
import logging

from langchain_core.messages import HumanMessage

from agents.base_agent import BaseAgent
from config.prompts import MARKET_ANALYSIS_PROMPT
from tools.tavily_search import TavilySearchTool, format_results_for_prompt

logger = logging.getLogger(__name__)


class MarketAnalysisAgent(BaseAgent):
    name = "MarketAnalysisAgent"
    _base_system_prompt = MARKET_ANALYSIS_PROMPT
    tools = [TavilySearchTool(max_results=10)]

    _SEARCH_ANGLES = [
        "{topic} market size revenue 2025 2026",
        "{topic} competitors funding raised startup",
        "{topic} trends risks opportunities analysis",
    ]

    async def _execute(self, task: str, context: str) -> str:
        tool = self.tools[0]
        topic = task[:60].strip()

        # Tüm aramaları paralel olarak başlat
        queries = [angle.format(topic=topic) for angle in self._SEARCH_ANGLES]
        results_list = await asyncio.gather(*[tool._arun(q) for q in queries])

        seen, all_results = set(), []
        for results in results_list:
            for r in results:
                if r["url"] not in seen:
                    seen.add(r["url"])
                    all_results.append(r)

        top_results = sorted(all_results, key=lambda x: x["score"], reverse=True)[:12]
        search_block = format_results_for_prompt(top_results)

        prompt = self._build_prompt(task=task, context=context)
        full_prompt = (
            f"{prompt}\n\n"
            f"## Pazar Araştırması Verileri ({len(top_results)} kaynak)\n"
            f"{search_block}\n\n"
            "Yukarıdaki verileri kullanarak kapsamlı pazar analizi yap. "
            "Rakip tablosu, büyüme trendi ve stratejik öneriler mutlaka dahil et."
        )

        response = await self.llm.ainvoke([HumanMessage(content=full_prompt)])
        return response.content
