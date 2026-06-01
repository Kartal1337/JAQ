"""HIGGSFIELD_PRESETS — reusable Higgsfield AI generation templates.

Each preset defines the stylistic wrapper (aesthetic, lighting, camera motion)
so VisualPromptAgent only needs to fill in subject and action per scene.
Presets are designed for TikTok vertical (9:16) format.

Prompt anatomy:
    [SUBJECT] + [ACTION] + [SETTING], [LIGHTING], [CAMERA_MOTION],
    [STYLE/MOOD], shot on [CAMERA_RIG], [ADDITIONAL_MODIFIERS]

Usage by VisualPromptAgent:
    from affiliate_factory.prompts.visual_prompts.higgsfield_templates import HIGGSFIELD_PRESETS
    base = HIGGSFIELD_PRESETS["ugc_authentic"]["template"]
    prompt = base.format(subject="person at laptop", action="smiling and nodding")
"""

from __future__ import annotations

HIGGSFIELD_PRESETS: dict[str, dict[str, str]] = {
    "ugc_authentic": {
        "template": (
            "{subject} {action}, casual home setting, natural window light, "
            "slight handheld shake, authentic documentary feel, "
            "shot on iPhone 15 Pro, 4K, warm color grade, vertical 9:16"
        ),
        "use_case": "hook and problem scenes — mimics organic UGC for trust",
        "notes": "Avoid polished backgrounds; cluttered desk or couch increases authenticity.",
    },
    "testimonial_close": {
        "template": (
            "{subject} {action}, neutral background, soft ring-light, "
            "direct-to-camera medium close-up, confident body language, "
            "clean minimalist look, shot on Sony ZV-E10, warm skin tones, vertical 9:16"
        ),
        "use_case": "proof and CTA scenes — builds credibility",
        "notes": "Direct eye contact is critical for CTA scenes.",
    },
    "results_reveal": {
        "template": (
            "close-up of {subject} showing {action}, bright overhead light, "
            "slow reveal camera push-in, excited reaction in background, "
            "crisp product focus, split-screen compatible, vertical 9:16"
        ),
        "use_case": "solution scenes — showing the offer's output/result",
        "notes": "Subject should be screen, product, or stat graphic.",
    },
    "lifestyle_aspirational": {
        "template": (
            "{subject} {action}, luxurious or serene environment, golden hour lighting, "
            "slow cinematic pan, aspirational mood, high-end travel/home aesthetic, "
            "shot on RED camera, 4K, cinematic color grade, vertical 9:16"
        ),
        "use_case": "dream outcome scene — the 'life after' visual",
        "notes": "Use sparingly; too much aspiration reads as scam. One scene max per video.",
    },
    "screen_capture": {
        "template": (
            "phone or laptop screen showing {subject}, {action} on screen, "
            "over-shoulder medium shot, natural desk environment, "
            "screen glow as key light, slight zoom-in during reveal, vertical 9:16"
        ),
        "use_case": "software/digital product demonstrations",
        "notes": "Ensure 'screen' content described is realistic to avoid hallucination.",
    },
    "b_roll_transition": {
        "template": (
            "{subject} {action}, dynamic urban or nature backdrop, "
            "fast whip-pan or jump cut, high energy motion, vibrant colors, "
            "trending TikTok visual style, vertical 9:16, 60fps"
        ),
        "use_case": "transition filler between hook and problem scenes",
        "notes": "Keep duration hint ≤ 2s; used for pacing, not information delivery.",
    },
}

__all__ = ["HIGGSFIELD_PRESETS"]
