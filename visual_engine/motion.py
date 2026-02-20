"""
Motion & Atmosphere Engine
===========================
Takes a static PNG frame and produces an animated MP4 clip by applying:
  - Motion: how the camera moves through the scene
  - Atmosphere: mood/texture effects layered on top
  - Intensity: 0.0 (invisible) to 1.0 (dramatic)

All rendering is done via FFmpeg filter_complex — no extra dependencies.

MOTION TYPES:
  slow_push_in     - classic Ken Burns zoom in
  slow_pull_out    - zoom out reveal
  drift_left       - pan left
  drift_right      - pan right
  diagonal_float   - diagonal drift
  pendulum_sway    - subtle left-right sway
  static           - no motion

ATMOSPHERE TYPES:
  none             - clean, no effect
  flicker          - candle-like brightness pulses
  glitch_flicker   - digital corruption frames
  vhs_wobble       - slight horizontal shake
  vignette_pulse   - edges darken/lighten slowly
  chromatic_drift  - subtle RGB separation movement
"""
from __future__ import annotations
import asyncio
import logging
import math
from pathlib import Path

logger = logging.getLogger(__name__)

MOTION_PRESETS = {
    "slow_push_in": {
        "zoom_start": 1.0,
        "zoom_end": 1.08,
        "pan_x_start": 0, "pan_x_end": 0,
        "pan_y_start": 0, "pan_y_end": 0,
    },
    "slow_pull_out": {
        "zoom_start": 1.08,
        "zoom_end": 1.0,
        "pan_x_start": 0, "pan_x_end": 0,
        "pan_y_start": 0, "pan_y_end": 0,
    },
    "drift_left": {
        "zoom_start": 1.05,
        "zoom_end": 1.05,
        "pan_x_start": 30, "pan_x_end": -30,
        "pan_y_start": 0, "pan_y_end": 0,
    },
    "drift_right": {
        "zoom_start": 1.05,
        "zoom_end": 1.05,
        "pan_x_start": -30, "pan_x_end": 30,
        "pan_y_start": 0, "pan_y_end": 0,
    },
    "diagonal_float": {
        "zoom_start": 1.03,
        "zoom_end": 1.08,
        "pan_x_start": -20, "pan_x_end": 20,
        "pan_y_start": -15, "pan_y_end": 15,
    },
    "pendulum_sway": {
        "zoom_start": 1.02,
        "zoom_end": 1.02,
        "pan_x_start": -15, "pan_x_end": 15,
        "pan_y_start": 0, "pan_y_end": 0,
    },
    "static": {
        "zoom_start": 1.0,
        "zoom_end": 1.0,
        "pan_x_start": 0, "pan_x_end": 0,
        "pan_y_start": 0, "pan_y_end": 0,
    },
}

# Auto-motion selection based on section type
SECTION_MOTION_MAP = {
    "intro":      "slow_push_in",
    "main":       "drift_left",
    "demo":       "slow_pull_out",
    "deep_dive":  "diagonal_float",
    "comparison": "static",
    "conclusion": "slow_pull_out",
}

# Auto-atmosphere selection based on template type
TEMPLATE_ATMOSPHERE_MAP = {
    "typewriter_reveal":  "flicker",
    "glitch_drop":        "glitch_flicker",
    "neon_pulse":         "vignette_pulse",
    "browser_mockup":     "none",
    "dashboard_reveal":   "none",
    "hologram_flicker":   "chromatic_drift",
    "matrix_rain":        "vhs_wobble",
    "counter_ticker":     "vignette_pulse",
    "bar_race":           "none",
    "film_burn":          "vhs_wobble",
}


class MotionEngine:
    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30,
                 codec: str = "libx264", preset: str = "fast"):
        self.width = width
        self.height = height
        self.fps = fps
        self.codec = codec
        self.preset = preset

    async def render_animated_clip(
        self,
        frame_path: Path,
        output_path: Path,
        duration: float,
        motion: str = "slow_push_in",
        atmosphere: str = "none",
        intensity: float = 0.3,
    ) -> Path:
        """
        Convert a static PNG into an animated MP4 clip with motion + atmosphere.
        """
        if output_path.exists():
            return output_path

        motion = motion if motion in MOTION_PRESETS else "slow_push_in"
        preset_vals = MOTION_PRESETS[motion]

        # Build FFmpeg filter chain
        vf = self._build_motion_filter(preset_vals, duration, intensity)
        atm_filter = self._build_atmosphere_filter(atmosphere, duration, intensity)

        if atm_filter:
            vf = f"{vf},{atm_filter}"

        frames = int(duration * self.fps)
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-framerate", str(self.fps),
            "-i", str(frame_path),
            "-vf", vf,
            "-t", str(duration),
            "-c:v", self.codec,
            "-preset", self.preset,
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning(f"[Motion] FFmpeg error: {stderr.decode()[-500:]}")
            # Fallback: simple static clip
            await self._static_fallback(frame_path, output_path, duration)

        return output_path

    def _build_motion_filter(self, preset: dict, duration: float, intensity: float) -> str:
        """Build zoompan filter for motion."""
        w, h = self.width, self.height
        fps = self.fps
        total_frames = max(1, int(duration * fps))

        zs = preset["zoom_start"]
        ze = preset["zoom_end"]
        # Scale intensity (reduce effect at low intensity)
        zoom_range = (ze - zs) * intensity
        ze = zs + zoom_range

        pxs = int(preset["pan_x_start"] * intensity)
        pxe = int(preset["pan_x_end"] * intensity)
        pys = int(preset["pan_y_start"] * intensity)
        pye = int(preset["pan_y_end"] * intensity)

        # Zoom expression (linear interpolation)
        if abs(ze - zs) < 0.001:
            zoom_expr = f"{zs:.4f}"
        else:
            zoom_expr = f"{zs:.4f}+{(ze-zs)/total_frames:.8f}*on"

        # Pan expressions
        x_expr = f"iw/2-(iw/zoom/2)+{pxs}+{(pxe-pxs)}/{total_frames}*on" if pxs != pxe else f"iw/2-(iw/zoom/2)"
        y_expr = f"ih/2-(ih/zoom/2)+{pys}+{(pye-pys)}/{total_frames}*on" if pys != pye else f"ih/2-(ih/zoom/2)"

        # Scale input to slightly larger than output to allow pan room
        scale_w = int(w * max(zs, ze) * 1.1)
        scale_w += scale_w % 2
        scale_h = int(h * max(zs, ze) * 1.1)
        scale_h += scale_h % 2

        return (
            f"scale={scale_w}:{scale_h}:force_original_aspect_ratio=decrease,"
            f"pad={scale_w}:{scale_h}:(ow-iw)/2:(oh-ih)/2:black,"
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':"
            f"d={total_frames}:s={w}x{h}:fps={fps}"
        )

    def _build_atmosphere_filter(self, atmosphere: str, duration: float, intensity: float) -> str:
        """Build atmosphere FFmpeg filter."""
        if atmosphere == "none" or not atmosphere:
            return ""

        i = max(0.05, min(1.0, intensity))

        if atmosphere == "flicker":
            # Brightness pulses — random-ish via sin wave
            depth = 0.08 * i
            return f"eq=brightness='sin(t*7)*{depth:.3f}'"

        elif atmosphere == "glitch_flicker":
            # Occasional bright flashes
            return (f"geq=r='p(X,Y)+if(between(mod(T,0.5),0,0.03*{i:.2f}),30,0)':"
                    f"g='p(X,Y)+if(between(mod(T,0.5),0,0.03*{i:.2f}),30,0)':"
                    f"b='p(X,Y)+if(between(mod(T,0.5),0,0.03*{i:.2f}),50,0)'")

        elif atmosphere == "vhs_wobble":
            # Horizontal shake
            amp = int(8 * i)
            return f"hue=h='sin(t*20)*{i:.2f}'&geq=r='p(X+{amp}*sin(T*15+Y/50),Y)':g='p(X,Y)':b='p(X-{amp//2}*sin(T*15+Y/50),Y)'"

        elif atmosphere == "vignette_pulse":
            # Pulsing vignette (approximate via eq)
            depth = 0.05 * i
            return f"vignette=angle=PI/4,eq=brightness='sin(t*3)*{depth:.3f}-0.02'"

        elif atmosphere == "chromatic_drift":
            # Subtle RGB channel drift
            return (f"split=3[r][g][b];"
                    f"[r]lutrgb=r='val':g=0:b=0[r1];"
                    f"[g]lutrgb=r=0:g='val':b=0[g1];"
                    f"[b]lutrgb=r=0:g=0:b='val'[b1];"
                    f"[r1][g1]blend=all_mode=addition[rg];"
                    f"[rg][b1]blend=all_mode=addition")

        return ""

    async def _static_fallback(self, frame_path: Path, output_path: Path, duration: float):
        """Simple static clip fallback if motion filter fails."""
        w, h = self.width, self.height
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", str(self.fps),
            "-i", str(frame_path),
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black",
            "-t", str(duration),
            "-c:v", self.codec, "-preset", self.preset, "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()


def auto_select_motion(section_type: str, asset_type: str) -> str:
    """Pick the best motion preset for a given section + asset type."""
    if asset_type == "title_card":
        return SECTION_MOTION_MAP.get(section_type, "slow_push_in")
    return "drift_left"


def auto_select_atmosphere(template_name: str, section_type: str) -> str:
    """Pick the best atmosphere effect for a template."""
    return TEMPLATE_ATMOSPHERE_MAP.get(template_name, "none")
