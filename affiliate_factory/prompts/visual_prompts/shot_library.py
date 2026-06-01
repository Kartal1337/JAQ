"""SHOT_TYPES — cinematographic shot vocabulary for VisualPromptAgent.

Maps short identifiers to full Higgsfield-compatible descriptions.
VisualPromptAgent selects a shot type per scene based on narrative function.

Usage by VisualPromptAgent:
    from affiliate_factory.prompts.visual_prompts.shot_library import SHOT_TYPES
    description = SHOT_TYPES["ecu"]["description"]
    ideal_for    = SHOT_TYPES["ecu"]["ideal_for"]
"""

from __future__ import annotations

SHOT_TYPES: dict[str, dict[str, str]] = {
    "ecu": {
        "name": "Extreme Close-Up",
        "description": "Fills the frame with a face detail (eyes, lips) or small object.",
        "ideal_for": "Hook scene — maximum pattern interrupt to stop the scroll.",
        "duration_hint": "1-2s",
    },
    "cu": {
        "name": "Close-Up",
        "description": "Head and shoulders; face clearly visible with minimal background.",
        "ideal_for": "Proof and CTA scenes — personal connection and trust.",
        "duration_hint": "3-8s",
    },
    "mcu": {
        "name": "Medium Close-Up",
        "description": "Chest to top of head; shows upper body language.",
        "ideal_for": "Problem and solution scenes — balances information and emotion.",
        "duration_hint": "3-10s",
    },
    "ms": {
        "name": "Medium Shot",
        "description": "Waist to top of head; shows hand gestures and posture.",
        "ideal_for": "Testimonial scenes; works well with sit-down formats.",
        "duration_hint": "5-15s",
    },
    "ots": {
        "name": "Over-The-Shoulder",
        "description": "Camera behind subject looking at screen or product.",
        "ideal_for": "Software/digital product demos and screen reveals.",
        "duration_hint": "3-8s",
    },
    "pov": {
        "name": "Point-Of-View",
        "description": "Camera simulates subject's eye perspective.",
        "ideal_for": "Immersive experience scenes; aspirational 'imagine yourself' moments.",
        "duration_hint": "2-5s",
    },
    "insert": {
        "name": "Insert Shot",
        "description": "Tight shot of a specific detail: phone notification, stat on screen.",
        "ideal_for": "Results reveal scenes; draws attention to proof elements.",
        "duration_hint": "1-3s",
    },
    "wide": {
        "name": "Wide Shot",
        "description": "Full environment visible; subject occupies ≤1/3 of frame.",
        "ideal_for": "Lifestyle aspirational scenes; establishing context.",
        "duration_hint": "2-4s",
    },
}

__all__ = ["SHOT_TYPES"]
