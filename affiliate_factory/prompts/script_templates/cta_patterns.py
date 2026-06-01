"""CTA_PATTERNS — call-to-action phrasings tested for affiliate TikTok content.

Patterns are grouped by aggression level (soft / medium / hard) so
CaptionAgent can select the appropriate intensity for each platform and
OptimizerAgent can track which level correlates with link clicks.

Usage by CaptionAgent:
    from affiliate_factory.prompts.script_templates.cta_patterns import CTA_PATTERNS
"""

from __future__ import annotations

CTA_PATTERNS: dict[str, list[dict[str, str]]] = {
    "soft": [
        {
            "text": "Link in bio if you want to try it.",
            "platform": "tiktok",
            "notes": "Lowest resistance. Works for curiosity-gap hooks.",
        },
        {
            "text": "Full breakdown in my bio.",
            "platform": "tiktok",
            "notes": "Frames the click as information, not a sale.",
        },
        {
            "text": "I'll drop the resource below.",
            "platform": "instagram",
            "notes": "Conversational tone. Pair with story-open hooks.",
        },
    ],
    "medium": [
        {
            "text": "Free access through the link in my bio — grab it before it changes.",
            "platform": "tiktok",
            "notes": "Scarcity without false urgency. Use only if offer has a trial/free tier.",
        },
        {
            "text": "I linked the exact tool I use. Check my bio.",
            "platform": "tiktok",
            "notes": "Personal endorsement framing increases trust.",
        },
        {
            "text": "Comment '{keyword}' and I'll send you the link.",
            "platform": "instagram",
            "notes": "Triggers comment engagement for algorithm. Use ManyChat or manual reply.",
        },
    ],
    "hard": [
        {
            "text": "Don't sleep on this — link in bio, offer ends soon.",
            "platform": "tiktok",
            "notes": "Only use when offer genuinely has a limited-time discount.",
        },
        {
            "text": "Click the link in bio NOW — I got you a discount.",
            "platform": "tiktok",
            "notes": "Highest conversion but highest unfollow risk. Use sparingly.",
        },
    ],
    "comment_bait": [
        {
            "text": "Comment '{keyword}' for the free resource.",
            "platform": "tiktok",
            "notes": "Algorithm-boosting pattern. Requires automation or manual follow-up.",
        },
    ],
}

__all__ = ["CTA_PATTERNS"]
