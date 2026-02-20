"""
Visual Engine
=============
4-layer visual rendering system for automated video creation.

Layers:
  1. Content    — Screenshot / title card PNG
  2. Template   — 20 dynamic visual treatments
  3. Motion+Atm — Camera motion + atmosphere effects  
  4. SFX        — Transition + ambient + UI sounds

Quick start:
  from visual_engine import VisualRenderer
  renderer = VisualRenderer(width=1920, height=1080, ...)
  assets = await renderer.render_all(timed_assets, work_dir, script)
"""

from .renderer import VisualRenderer
from .selector import select_template, select_motion, select_atmosphere, get_all_templates
from .motion import MotionEngine
from .sfx import SFXEngine

__all__ = [
    "VisualRenderer",
    "MotionEngine",
    "SFXEngine",
    "select_template",
    "select_motion",
    "select_atmosphere",
    "get_all_templates",
]
