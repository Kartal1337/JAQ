"""HOOK_FORMULAS — proven TikTok opening-line structures for affiliate scripts.

Each formula has:
  - template : fill-in-the-blank structure (use {placeholder} syntax)
  - type     : category for pattern analysis by OptimizerAgent
  - notes    : guidance for ScriptForgeAgent on when to use this formula

Usage by ScriptForgeAgent:
    from affiliate_factory.prompts.script_templates.hook_formulas import HOOK_FORMULAS
    # Pass relevant formulas as context in the system prompt.
"""

from __future__ import annotations

HOOK_FORMULAS: dict[str, dict[str, str]] = {
    "curiosity_gap": {
        "template": "Nobody talks about the {adjective} way to {outcome}.",
        "type": "curiosity",
        "notes": "Works best when the 'way' is genuinely underused. Avoid if the offer is mainstream.",
    },
    "number_listicle": {
        "template": "{N} {niche} tricks that changed my {metric} in {timeframe}.",
        "type": "list",
        "notes": "Odd numbers (3, 5, 7) outperform even. Keep N ≤ 7 for TikTok pacing.",
    },
    "contrarian": {
        "template": "Stop {common_advice}. Here's what actually works.",
        "type": "contrarian",
        "notes": "High CTR but risks negative comments. Use only when contrarian claim is defensible.",
    },
    "story_open": {
        "template": "I was {relatable_struggle} until I found {vague_solution}.",
        "type": "story",
        "notes": "Highest watch-time formula. Requires authentic-sounding struggle framing.",
    },
    "direct_result": {
        "template": "How I made {result} in {timeframe} with {tool_or_method}.",
        "type": "result",
        "notes": "Highest conversion when result is specific and believable (not '$10k in 24h').",
    },
    "question_hook": {
        "template": "Why is no one using {tool_or_method} to {outcome}?",
        "type": "question",
        "notes": "Triggers comment engagement ('I use it!'). Good for algo boost.",
    },
    "warning": {
        "template": "Do NOT {action} before you see this.",
        "type": "warning",
        "notes": "High urgency but easily perceived as clickbait. Balance with credibility cues.",
    },
    "social_proof": {
        "template": "{N} {audience_segment} are using {method} to {outcome}.",
        "type": "social_proof",
        "notes": "Use real-sounding specifics (not 'millions'). Pairs well with result hooks.",
    },
}

__all__ = ["HOOK_FORMULAS"]
