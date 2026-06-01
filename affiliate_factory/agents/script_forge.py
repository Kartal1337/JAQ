"""ScriptForgeAgent — generates TikTok video scripts from a production brief.

Responsibilities:
  - Accept a production brief (selected offer, chosen hook, trend angle).
  - Generate AffiliateSettings.hook_variants_per_brief alternative hooks.
  - Produce a full script (~AffiliateSettings.target_script_words words):
      [HOOK] → [PROBLEM] → [AGITATE] → [SOLUTION] → [PROOF] → [CTA]
  - Vary pacing cues: pauses, emphasis markers, B-roll cut points.
  - Ensure the affiliate link / offer name appears naturally, not forced.

Output (AgentResult.output):
    JSON string:
    {
      "hook_options": [str, ...],     # N variants for brief storage
      "chosen_script": str,           # full script with pacing markers
      "word_count": int,
      "estimated_duration_s": int
    }
"""

from __future__ import annotations

from affiliate_factory.agents.base import AffiliateBaseAgent
from affiliate_factory.prompts.script_templates.hook_formulas import HOOK_FORMULAS
from affiliate_factory.prompts.system_prompts import SCRIPT_FORGE_SYSTEM


class ScriptForgeAgent(AffiliateBaseAgent):
    """Generates differentiated video scripts informed by competitor analysis.

    Retrieves competitor hooks from ChromaDB to ensure the generated hooks
    are distinct.  Uses the HOOK_FORMULAS library for structural variety and
    the PROBLEM-AGITATE-SOLUTION framework for persuasion structure.

    No external tools — pure LLM generation with ChromaDB retrieval context.
    """

    name = "ScriptForgeAgent"
    _base_system_prompt = SCRIPT_FORGE_SYSTEM
    tools = []

    async def _execute(self, task: str, context: str) -> str:
        """Generate hook variants and full script from brief context.

        Args:
            task:    JSON-serialised brief dict containing: offer_name, payout,
                     trend_angle, chosen_hook (optional), target_audience.
            context: Injected semantic context (competitor hooks, past winners).

        Returns:
            JSON string with hook_options, chosen_script, word_count,
            estimated_duration_s.
        """
        ...
