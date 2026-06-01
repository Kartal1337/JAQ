"""CompetitorScoutAgent — analyses competitor TikTok content in the niche.

Responsibilities:
  - Search for top-performing competitor videos on TikTok / YouTube Shorts
    in the active niche using Tavily.
  - Extract: hook structure, video format, CTA pattern, visual style.
  - Identify content gaps (angles competitors are NOT covering).
  - Store competitor hooks as passages in ChromaDB for hook differentiation
    during ScriptForgeAgent execution.

Output (AgentResult.output):
    JSON string:
    {
      "top_hooks": [{"hook_text": str, "format": str, "source_url": str}],
      "content_gaps": [str],
      "dominant_cta": str,
      "visual_style_notes": str
    }
"""

from __future__ import annotations

from affiliate_factory.agents.base import AffiliateBaseAgent
from affiliate_factory.prompts.system_prompts import COMPETITOR_SCOUT_SYSTEM
from tools.tavily_search import TavilySearchTool


class CompetitorScoutAgent(AffiliateBaseAgent):
    """Scouts competitor content to inform differentiated hook and script creation.

    Runs two parallel Tavily searches:
      1. Top-performing videos (sorted by engagement signals in snippets).
      2. Sponsored / affiliate content to detect CTA patterns in use.

    Results are de-duplicated by URL and stored in ChromaDB under
    metadata type='competitor_hook' for retrieval by ScriptForgeAgent.
    """

    name = "CompetitorScoutAgent"
    _base_system_prompt = COMPETITOR_SCOUT_SYSTEM
    tools = [TavilySearchTool(max_results=10)]

    async def _execute(self, task: str, context: str) -> str:
        """Scout competitor content, store hooks in ChromaDB, return analysis.

        Args:
            task:    Niche + optional offer angle to focus the search.
            context: Injected semantic context (recent trends, existing hooks).

        Returns:
            JSON string with top_hooks, content_gaps, dominant_cta, visual_style_notes.
        """
        ...
