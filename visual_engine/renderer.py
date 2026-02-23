"""
Visual Renderer
================
The orchestrator of all visual layers:
  Layer 1 — HTML Animated Template (Record WebM via Playwright)
  Layer 2 — SFX (transition + ambient + UI sounds)

Usage:
  renderer = VisualRenderer(cfg)
  animated_clips = await renderer.render_all(timed_assets, output_dir)
"""
from __future__ import annotations
import asyncio
import logging
import random
from pathlib import Path
from typing import Optional

from .sfx import SFXEngine
from .html_renderer import HTMLTemplateRenderer

logger = logging.getLogger(__name__)


class VisualRenderer:
    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        codec: str = "libx264",
        preset: str = "fast",
        bg_hex: str = "#0F1117",
        accent_colours: list = None,
        sfx_style: str = "subtle",
        sfx_enabled: bool = True,
        ambient_enabled: bool = True,
        motion_intensity: float = 0.35,  # Unused but kept for config compatibility
        atmosphere_intensity: float = 0.3, # Unused but kept for config compatibility
        template_override: Optional[str] = None,
        motion_override: Optional[str] = None, # Unused
        atmosphere_override: Optional[str] = None, # Unused
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.codec = codec
        self.preset = preset
        self.bg_hex = bg_hex
        self.accent_colours = accent_colours or ["#4A9EFF", "#FF6B35", "#00C896", "#9B59B6"]
        self.template_override = template_override

        self.html_renderer = HTMLTemplateRenderer(self.width, self.height)
        self.sfx_engine = None  # Initialized per render call with sfx_dir
        self.sfx_style = sfx_style
        self.sfx_enabled = sfx_enabled
        self.ambient_enabled = ambient_enabled
        
        # We will generate 20 robust animated HTML templates inside html_templates later.
        self.available_templates = [
            "browser_zoom", "cinematic_pan", "glass_float", "polaroid_sway",
            "neon_pulse", "cyber_glitch", "slide_in", "scale_fade",
            "phone_portrait", "dash_split", "crt_scan", "minimal_outline",
            "tilt_shift", "circle_reveal", "mac_bounce", "perspective_3d",
            "wide_pan", "float_screens", "terminal", "drop_in", "browser_mockup"
        ]

    def _get_accent(self, index: int) -> str:
        return self.accent_colours[index % len(self.accent_colours)]

    async def render_asset(
        self,
        asset,
        section_type: str,
        accent_index: int,
        clips_dir: Path,
    ):
        """
        Record the HTML animation to MP4 via Playwright.
        Sets asset.clip_path to the resulting animated MP4.
        """
        asset_id = f"{asset.section_id}_{asset.asset_type}"
        accent_hex = self._get_accent(accent_index)

        # Select a random template or override
        template_name = self.template_override if self.template_override else random.choice(self.available_templates)

        clip_path = clips_dir / f"{asset_id}_{template_name}_animated.mp4"
        duration = max(1.0, asset.display_end - asset.display_start)

        if not clip_path.exists():
            try:
                title = getattr(asset, "description", "") or ""
                url = getattr(asset, "url", "")
                image_path = asset.file_path if asset.asset_type == "screenshot" else None
                
                await self.html_renderer.render_template(
                    template_name=template_name,
                    title=title,
                    url=url,
                    image_path=image_path,
                    bg_hex=self.bg_hex,
                    accent_hex=accent_hex,
                    output_path=clip_path,
                    duration=duration
                )
            except Exception as exc:
                logger.warning(f"[Renderer] HTML Video Template failed for {asset_id}: {exc}")
                raise

        # Attach clip_path and template_name to asset for downstream use
        asset.clip_path = clip_path
        asset.template_name = template_name

        logger.debug(f"[Renderer] {asset_id}: {template_name} video recorded")
        return asset

    async def render_all(
        self,
        timed_assets: list,
        work_dir: Path,
        script=None,
    ) -> list:
        """
        Render all visual assets through the new Playwright HTML video pipeline.
        Returns the asset list with .clip_path set on each.
        """
        clips_dir = work_dir / "clips"
        sfx_dir = work_dir / "sfx"
        clips_dir.mkdir(parents=True, exist_ok=True)
        sfx_dir.mkdir(parents=True, exist_ok=True)

        # SFX engine setup
        self.sfx_engine = SFXEngine(
            sfx_dir=sfx_dir,
            style=self.sfx_style,
            sfx_enabled=self.sfx_enabled,
            ambient_enabled=self.ambient_enabled,
        )

        # Build section_type lookup from script
        section_map = {}
        if script:
            for section in script.sections:
                section_map[section.section_id] = section.section_type

        # Render all assets
        accent_counter = {}
        for asset in timed_assets:
            section_type = section_map.get(asset.section_id, "main")
            if section_type not in accent_counter:
                accent_counter[section_type] = len(accent_counter)
            accent_idx = accent_counter[section_type]

            await self.render_asset(
                asset=asset,
                section_type=section_type,
                accent_index=accent_idx,
                clips_dir=clips_dir,
            )

        logger.info(f"[Renderer] Rendered {len(timed_assets)} HTML animated clips")
        return timed_assets
