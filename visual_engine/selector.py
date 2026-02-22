"""
Template Selector
==================
Auto-selects the best template + motion + atmosphere + SFX combo
based on section type and asset type.

Can be overridden via pipeline.json visual config.
"""
from __future__ import annotations
import random

# Template selection rules:
# section_type + asset_type → template name

SECTION_TEMPLATE_MAP = {
    # Title cards
    ("intro", "title_card"):       "neon_pulse",
    ("main", "title_card"):        "split_reveal",
    ("demo", "title_card"):        "typewriter_reveal",
    ("deep_dive", "title_card"):   "glitch_drop",
    ("comparison", "title_card"):  "countdown_slam",
    ("conclusion", "title_card"):  "neon_pulse",

    # Screenshots
    ("intro", "screenshot"):       "spotlight_zoom",
    ("main", "screenshot"):        "browser_mockup",
    ("demo", "screenshot"):        "dashboard_reveal",
    ("deep_dive", "screenshot"):   "browser_mockup",
    ("comparison", "screenshot"):  "comparison_split",
    ("conclusion", "screenshot"):  "polaroid_drop",
}

FALLBACK_TITLE_TEMPLATE = "typewriter_reveal"
FALLBACK_SCREENSHOT_TEMPLATE = "browser_mockup"

# Motion per section type
SECTION_MOTION_MAP = {
    "intro":      "slow_push_in",
    "main":       "drift_left",
    "demo":       "slow_pull_out",
    "deep_dive":  "diagonal_float",
    "comparison": "static",
    "conclusion": "slow_pull_out",
}

# Atmosphere per template
TEMPLATE_ATMOSPHERE_MAP = {
    "typewriter_reveal": "flicker",
    "glitch_drop":       "glitch_flicker",
    "neon_pulse":        "vignette_pulse",
    "countdown_slam":    "vignette_pulse",
    "split_reveal":      "none",
    "browser_mockup":    "none",
    "dashboard_reveal":  "none",
    "spotlight_zoom":    "vignette_pulse",
    "hologram_flicker":  "chromatic_drift",
    "matrix_rain":       "vhs_wobble",
    "particle_field":    "none",
}


def select_template(section_type: str, asset_type: str, override: str = None) -> str:
    """Return template name for a given section + asset type."""
    if override:
        return override
    key = (section_type, asset_type)
    if asset_type == "title_card":
        return SECTION_TEMPLATE_MAP.get(key, FALLBACK_TITLE_TEMPLATE)
    return SECTION_TEMPLATE_MAP.get(key, FALLBACK_SCREENSHOT_TEMPLATE)


def select_motion(section_type: str, asset_type: str, override: str = None) -> str:
    """Return motion preset for a section type and asset type."""
    if override:
        return override
    if asset_type == "title_card":
        return "static"
    if asset_type == "screenshot":
        valid_screenshot_motions = [
            "slow_push_in",
            "slow_pull_out",
            "drift_left",
            "drift_right",
            "diagonal_float"
        ]
        return random.choice(valid_screenshot_motions)
    return SECTION_MOTION_MAP.get(section_type, "slow_push_in")


def select_atmosphere(template_name: str, override: str = None) -> str:
    """Return atmosphere effect for a template."""
    if override:
        return override
    return TEMPLATE_ATMOSPHERE_MAP.get(template_name, "none")


def get_all_templates() -> dict:
    """Return dict of all available template names by category."""
    return {
        "kinetic": ["typewriter_reveal", "split_reveal", "glitch_drop", "neon_pulse", "countdown_slam"],
        "showcase": ["browser_mockup", "phone_frame_scroll", "spotlight_zoom",
                     "comparison_split", "polaroid_drop", "dashboard_reveal"],
        "data": ["counter_ticker", "bar_race", "progress_ring"],
        "transitions": ["film_burn", "lens_flare_wipe", "shatter_break"],
        "ambient": ["particle_field", "matrix_rain", "hologram_flicker"],
    }
