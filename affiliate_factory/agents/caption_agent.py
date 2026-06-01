"""CaptionAgent — generates platform-specific captions and hashtag sets.

Responsibilities:
  - Generate TikTok caption (≤150 chars) with soft CTA.
  - Generate Instagram Reels caption (≤300 chars) with line breaks.
  - Produce two hashtag sets: niche hashtags (15) + broad discovery (5).
  - Optionally generate a YouTube Shorts description (≤500 chars).
  - Ensure the affiliate link placeholder [LINK] is positioned correctly.

Output (AgentResult.output):
    JSON string:
    {
      "tiktok":    {"caption": str, "hashtags": [str]},
      "instagram": {"caption": str, "hashtags": [str]},
      "youtube":   {"description": str, "tags": [str]}
    }
"""

from __future__ import annotations

from affiliate_factory.agents.base import AffiliateBaseAgent
from affiliate_factory.prompts.script_templates.cta_patterns import CTA_PATTERNS
from affiliate_factory.prompts.system_prompts import CAPTION_AGENT_SYSTEM


class CaptionAgent(AffiliateBaseAgent):
    """Produces multi-platform captions and hashtags optimised for affiliate reach.

    Pulls winning CTA language from CTA_PATTERNS and filters out hashtags
    already flagged as shadowbanned in the niche knowledge collection.

    No external tools — pure LLM generation.
    """

    name = "CaptionAgent"
    _base_system_prompt = CAPTION_AGENT_SYSTEM
    tools = []

    async def _execute(self, task: str, context: str) -> str:
        """Generate captions and hashtags for all target platforms.

        Args:
            task:    JSON-serialised input with: script_excerpt, offer_name,
                     trend_angle, affiliate_link_placeholder, target_platform.
            context: Injected semantic context (past caption performance,
                     shadowbanned hashtags stored in ChromaDB).

        Returns:
            JSON string with tiktok, instagram, and youtube caption objects.
        """
        ...
