"""
Visual Renderer
================
The orchestrator of all 4 visual layers:
  Layer 1 — Content     (screenshot / PIL-rendered title card)
  Layer 2 — Template    (20 templates applied to content)
  Layer 3 — Motion+Atm  (camera motion + atmosphere effects)
  Layer 4 — SFX         (transition + ambient + UI sounds)

Usage:
  renderer = VisualRenderer(cfg)
  animated_clips = await renderer.render_all(timed_assets, output_dir)

Each VisualAsset comes out with a .clip_path pointing to an animated MP4.
The video_service then uses these clips instead of raw PNGs.
"""
from __future__ import annotations
import asyncio
import logging
from pathlib import Path
from typing import Optional

from .motion import MotionEngine, auto_select_motion, auto_select_atmosphere
from .selector import select_template, select_motion, select_atmosphere
from .sfx import SFXEngine

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
        motion_intensity: float = 0.35,
        atmosphere_intensity: float = 0.3,
        template_override: Optional[str] = None,
        motion_override: Optional[str] = None,
        atmosphere_override: Optional[str] = None,
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.codec = codec
        self.preset = preset
        self.bg_hex = bg_hex
        self.accent_colours = accent_colours or ["#4A9EFF", "#FF6B35", "#00C896", "#9B59B6"]
        self.motion_intensity = motion_intensity
        self.atmosphere_intensity = atmosphere_intensity
        self.template_override = template_override
        self.motion_override = motion_override
        self.atmosphere_override = atmosphere_override

        self.motion_engine = MotionEngine(width, height, fps, codec, preset)
        self.sfx_engine = None  # Initialized per render call with sfx_dir
        self.sfx_style = sfx_style
        self.sfx_enabled = sfx_enabled
        self.ambient_enabled = ambient_enabled

    def _get_accent(self, index: int) -> str:
        return self.accent_colours[index % len(self.accent_colours)]

    def _build_template(self, template_name: str, accent_hex: str):
        """Instantiate the right template class."""
        from .templates.kinetic import (TypewriterReveal, SplitReveal, GlitchDrop,
                                         NeonPulse, CountdownSlam)
        from .templates.showcase import (BrowserMockup, PhoneFrameScroll, SpotlightZoom,
                                          ComparisonSplit, PolaroidDrop, DashboardReveal)
        from .templates.data import CounterTicker, BarRace, ProgressRing
        from .templates.transitions import FilmBurn, LensFlareWipe, ShatterBreak
        from .templates.ambient import ParticleField, MatrixRain, HologramFlicker

        template_map = {
            "typewriter_reveal": TypewriterReveal,
            "split_reveal": SplitReveal,
            "glitch_drop": GlitchDrop,
            "neon_pulse": NeonPulse,
            "countdown_slam": CountdownSlam,
            "browser_mockup": BrowserMockup,
            "phone_frame_scroll": PhoneFrameScroll,
            "spotlight_zoom": SpotlightZoom,
            "comparison_split": ComparisonSplit,
            "polaroid_drop": PolaroidDrop,
            "dashboard_reveal": DashboardReveal,
            "counter_ticker": CounterTicker,
            "bar_race": BarRace,
            "progress_ring": ProgressRing,
            "film_burn": FilmBurn,
            "lens_flare_wipe": LensFlareWipe,
            "shatter_break": ShatterBreak,
            "particle_field": ParticleField,
            "matrix_rain": MatrixRain,
            "hologram_flicker": HologramFlicker,
        }

        cls = template_map.get(template_name, BrowserMockup)
        return cls(width=self.width, height=self.height,
                   bg_hex=self.bg_hex, accent_hex=accent_hex)

    async def render_asset(
        self,
        asset,
        section_type: str,
        accent_index: int,
        frames_dir: Path,
        clips_dir: Path,
    ):
        """
        Render one VisualAsset through all 4 layers.
        Sets asset.clip_path to the resulting animated MP4.
        """
        asset_id = f"{asset.section_id}_{asset.asset_type}"
        accent_hex = self._get_accent(accent_index)

        # ── Layer 1+2: Content + Template ────────────────────────────────────
        template_name = select_template(
            section_type, asset.asset_type, self.template_override
        )

        template = self._build_template(template_name, accent_hex)

        # Determine render kwargs
        render_kwargs = {}
        if asset.asset_type == "title_card":
            render_kwargs["title"] = getattr(asset, "description", "") or ""
            render_kwargs["section_type"] = section_type
        elif asset.asset_type == "screenshot":
            render_kwargs["image_path"] = asset.file_path
            render_kwargs["url"] = getattr(asset, "url", "")
            render_kwargs["title"] = getattr(asset, "description", "")

        frame_path = frames_dir / f"{asset_id}_{template_name}.png"

        if not frame_path.exists():
            try:
                template.render_frame(frame_path, **render_kwargs)
            except Exception as exc:
                logger.warning(f"[Renderer] Template render failed for {asset_id}: {exc}")
                # Fallback: use original file if available
                if asset.file_path and Path(asset.file_path).exists():
                    import shutil
                    shutil.copy(asset.file_path, frame_path)
                else:
                    _make_fallback_frame(frame_path, self.bg_hex, self.width, self.height)

        # ── Layer 3: Motion + Atmosphere ──────────────────────────────────────
        motion = select_motion(section_type, asset.asset_type, self.motion_override)
        atmosphere = select_atmosphere(template_name, self.atmosphere_override)

        duration = max(1.0, asset.display_end - asset.display_start)
        clip_path = clips_dir / f"{asset_id}_{template_name}_animated.mp4"

        await self.motion_engine.render_animated_clip(
            frame_path=frame_path,
            output_path=clip_path,
            duration=duration,
            motion=motion,
            atmosphere=atmosphere,
            intensity=self.motion_intensity,
        )

        # Attach clip_path and template_name to asset for downstream use
        asset.clip_path = clip_path
        asset.template_name = template_name

        logger.debug(f"[Renderer] {asset_id}: {template_name} + {motion} + {atmosphere}")
        return asset

    async def render_all(
        self,
        timed_assets: list,
        work_dir: Path,
        script=None,
    ) -> list:
        """
        Render all visual assets through the full 4-layer pipeline.
        Returns the asset list with .clip_path set on each.
        """
        frames_dir = work_dir / "frames"
        clips_dir = work_dir / "clips"
        sfx_dir = work_dir / "sfx"
        frames_dir.mkdir(parents=True, exist_ok=True)
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

        # Render all assets (can be parallelised but we keep sequential for stability)
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
                frames_dir=frames_dir,
                clips_dir=clips_dir,
            )

        logger.info(f"[Renderer] Rendered {len(timed_assets)} animated clips")
        return timed_assets


def _make_fallback_frame(path: Path, bg_hex: str, width: int, height: int):
    """Generate a plain coloured fallback frame."""
    import subprocess
    colour = bg_hex.lstrip("#")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"color=c=0x{colour}:s={width}x{height}",
         "-vframes", "1", str(path)],
        capture_output=True,
    )
