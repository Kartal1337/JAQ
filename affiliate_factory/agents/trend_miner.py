"""TrendMinerAgent — discovers current trending angles for the active niche.

Responsibilities:
  - Search TikTok / YouTube / Reddit / Google Trends for the niche keyword.
  - Score each trend by recency, engagement signal, and affiliate fit.
  - Store discovered trends as passages in the niche ChromaDB collection so
    BriefBuilderAgent can retrieve them in later pipeline steps.

Output (AgentResult.output):
    JSON-serialisable string representing a list of TrendItem dicts:
    [{"topic": str, "angle": str, "urgency_score": float, "source_url": str}, ...]
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from affiliate_factory.agents.base import AffiliateBaseAgent
from affiliate_factory.prompts.system_prompts import TREND_MINER_SYSTEM
from tools.tavily_search import TavilySearchTool


class TrendMinerAgent(AffiliateBaseAgent):
    """Discovers and scores trending content angles for the active niche.

    Uses Tavily to search multiple signal sources in parallel, then scores
    each trend by: (1) recency, (2) engagement keywords in snippets,
    (3) alignment with affiliate offer categories.

    The results are stored in ChromaDB as 'trend' passages for downstream
    retrieval by BriefBuilderAgent.
    """

    name = "TrendMinerAgent"
    _base_system_prompt = TREND_MINER_SYSTEM
    tools = [TavilySearchTool(max_results=10)]

    async def _execute(self, task: str, context: str) -> str:
        """Search for trends, score them, persist to ChromaDB, return JSON list.

        Args:
            task:    Niche keyword or specific trend-mining instruction.
            context: Injected semantic context from ChromaDB (recent offers,
                     previous trends) provided by BaseAgent.run().

        Returns:
            JSON string: list of TrendItem dicts sorted by urgency_score desc.
        """
        ...
