"""BriefBuilderAgent — orchestrates research outputs into a production brief.

Responsibilities:
  - Accept trend data, evaluated offers, and competitor analysis as context.
  - Select the best offer × trend angle combination.
  - Synthesise a complete BriefDocument ready for ScriptForgeAgent.
  - Persist the brief to the SQLite `briefs` table (status='draft').

Output (AgentResult.output):
    JSON string matching the BriefDocument schema:
    {
      "brief_id": str,          # UUID
      "date": str,              # YYYY-MM-DD
      "offer_id": str,
      "offer_name": str,
      "payout": float,
      "trend_angle": str,
      "target_audience": str,
      "hook_options": [str],    # populated later by ScriptForgeAgent
      "chosen_hook": null,
      "script": null,
      "visual_prompts": [],
      "status": "draft"
    }
"""

from __future__ import annotations

from affiliate_factory.agents.base import AffiliateBaseAgent
from affiliate_factory.prompts.system_prompts import BRIEF_BUILDER_SYSTEM


class BriefBuilderAgent(AffiliateBaseAgent):
    """Synthesises trend + offer + competitor data into a production brief.

    Selection logic (implemented in _execute):
      1. Rank offer × trend combinations by (evaluation_score × urgency_score).
      2. Apply novelty filter: deprioritise angles used in the last 7 days
         (queried from ChromaDB).
      3. Output the top-ranked combination as a structured brief.

    No external tools — operates on context injected by the pipeline state.
    """

    name = "BriefBuilderAgent"
    _base_system_prompt = BRIEF_BUILDER_SYSTEM
    tools = []

    async def _execute(self, task: str, context: str) -> str:
        """Synthesise inputs into a brief and persist to SQLite.

        Args:
            task:    JSON-serialised pipeline state containing trends,
                     evaluated_offers, and competitor_analysis fields.
            context: Injected semantic context (recent brief angles to avoid).

        Returns:
            JSON string: BriefDocument with status='draft' and brief_id set.
        """
        ...
