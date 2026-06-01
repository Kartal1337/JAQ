"""OptimizerAgent — extracts winning patterns from performance data.

Responsibilities:
  - Query the SQLite `performance` and `videos` tables for the past 30 days.
  - Identify top-performing videos by views, conversions, and engagement rate.
  - Cluster winning content by: hook type, visual style, CTA pattern, posting time.
  - Persist discovered patterns to the `winners_pattern` table.
  - Store pattern summaries as passages in ChromaDB for retrieval by downstream
    agents (ScriptForgeAgent, BriefBuilderAgent).
  - Generate actionable recommendations for the next weekly cycle.

Output (AgentResult.output):
    JSON string:
    {
      "patterns_found": int,
      "top_patterns": [
        {
          "pattern_type": str,   # hook | visual | cta | timing | niche
          "description": str,
          "confidence_score": float,
          "evidence_count": int
        }
      ],
      "recommendations": [str]
    }
"""

from __future__ import annotations

from affiliate_factory.agents.base import AffiliateBaseAgent
from affiliate_factory.prompts.system_prompts import OPTIMIZER_SYSTEM


class OptimizerAgent(AffiliateBaseAgent):
    """Identifies content patterns that drive conversions and stores them as knowledge.

    Pattern types extracted:
      - hook       : which opening line structures correlate with high watch-time
      - visual     : scene/shot styles that retain viewers
      - cta        : call-to-action phrasings with highest link-click rates
      - timing     : optimal posting hour / day of week
      - niche      : sub-topics within the niche generating most conversions

    Patterns are persisted to both SQLite (winners_pattern table) and
    ChromaDB (for semantic retrieval) so future pipeline runs automatically
    inherit learned optimisations.

    No external tools — operates entirely on local SQLite data + LLM analysis.
    """

    name = "OptimizerAgent"
    _base_system_prompt = OPTIMIZER_SYSTEM
    tools = []

    async def _execute(self, task: str, context: str) -> str:
        """Query performance data, extract patterns, persist, return recommendations.

        Args:
            task:    Date range or instruction ('last 30 days', 'since launch').
            context: Injected semantic context (previous patterns to compare).

        Returns:
            JSON string: patterns_found, top_patterns list, recommendations list.
        """
        ...
