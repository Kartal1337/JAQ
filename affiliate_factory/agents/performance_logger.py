"""PerformanceLoggerAgent — fetches video metrics and persists to SQLite.

Responsibilities:
  - Accept a list of posted video records (video_id, tiktok_url).
  - Fetch current metrics: views, likes, comments, shares, link_clicks,
    conversions (via TikTok unofficial API or manual input until API access).
  - Upsert rows into the SQLite `performance` table.
  - Flag videos that cross the 'winner' threshold for OptimizerAgent.

Output (AgentResult.output):
    JSON string:
    {
      "logged_count": int,
      "winner_candidates": [{"video_id": str, "views": int, "conversions": int}],
      "errors": [{"video_id": str, "reason": str}]
    }

Note:
    Until official TikTok API access is available, this agent accepts metrics
    as structured text input from the user (via /affiliate_log Telegram command)
    and parses them into the expected schema.
"""

from __future__ import annotations

from affiliate_factory.agents.base import AffiliateBaseAgent
from affiliate_factory.prompts.system_prompts import PERFORMANCE_LOGGER_SYSTEM


class PerformanceLoggerAgent(AffiliateBaseAgent):
    """Logs video performance metrics into the SQLite performance table.

    Winner threshold (configurable via AffiliateSettings — TBD):
      views > 10_000 OR conversions > 0

    Videos crossing the threshold are returned in winner_candidates so the
    weekly review pipeline can prioritise them for pattern extraction.

    No external tools in skeleton — Tavily may be added later for scraping.
    """

    name = "PerformanceLoggerAgent"
    _base_system_prompt = PERFORMANCE_LOGGER_SYSTEM
    tools = []

    async def _execute(self, task: str, context: str) -> str:
        """Parse metrics input, persist to SQLite, identify winner candidates.

        Args:
            task:    JSON or natural-language string with video metrics.
                     Structured input: list of {video_id, views, likes, ...}
                     Natural-language: Telegram message pasted from TikTok app.
            context: Injected semantic context (existing performance baselines).

        Returns:
            JSON string: logged_count, winner_candidates, errors.
        """
        ...
