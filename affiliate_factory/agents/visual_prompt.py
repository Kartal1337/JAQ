"""VisualPromptAgent — generates scene-by-scene Higgsfield AI video prompts.

Responsibilities:
  - Parse a video script into logical scenes (hook, problem, solution, CTA).
  - Map each scene to a Higgsfield prompt using templates from
    prompts/visual_prompts/higgsfield_templates.py and shot library.
  - Output prompts ready to paste directly into Higgsfield's generation API.
  - Store generated prompts in the production brief's visual_prompts JSON field.

Output (AgentResult.output):
    JSON string:
    {
      "scenes": [
        {
          "scene_index": int,
          "scene_label": str,        # "hook" | "problem" | "solution" | "cta"
          "script_excerpt": str,
          "higgsfield_prompt": str,
          "shot_type": str,          # from SHOT_TYPES in shot_library.py
          "duration_hint_s": int
        },
        ...
      ]
    }
"""

from __future__ import annotations

from affiliate_factory.agents.base import AffiliateBaseAgent
from affiliate_factory.prompts.system_prompts import VISUAL_PROMPT_SYSTEM
from affiliate_factory.prompts.visual_prompts.higgsfield_templates import (
    HIGGSFIELD_PRESETS,
)
from affiliate_factory.prompts.visual_prompts.shot_library import SHOT_TYPES


class VisualPromptAgent(AffiliateBaseAgent):
    """Translates video scripts into structured Higgsfield scene prompts.

    Uses the HIGGSFIELD_PRESETS library for style consistency and the
    SHOT_TYPES library for cinematographic variety.  Each scene prompt is
    self-contained so the scenes can be generated independently or as a batch
    in the Higgsfield API.

    No external tools — pure LLM generation.
    """

    name = "VisualPromptAgent"
    _base_system_prompt = VISUAL_PROMPT_SYSTEM
    tools = []

    async def _execute(self, task: str, context: str) -> str:
        """Parse script into scenes and generate a Higgsfield prompt per scene.

        Args:
            task:    Full video script text (with pacing markers).
            context: Injected semantic context (winning visual patterns from
                     ChromaDB, niche aesthetic preferences).

        Returns:
            JSON string: list of scene dicts each containing a higgsfield_prompt.
        """
        ...
