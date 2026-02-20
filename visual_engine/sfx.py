"""
Sound Effects Engine
=====================
Manages SFX generation and mixing.

Three SFX types:
  1. Transition SFX  — plays as scene changes (whoosh, glitch burst, film click)
  2. Ambient SFX     — low-volume loop under scenes (hum, static)
  3. UI SFX          — tied to visual events (typing tick, counter tick, scan beep)

All SFX are generated synthetically via FFmpeg sine/noise filters — no external
files needed. Users can optionally drop WAV files into visual_engine/assets/sfx/
to override any sound.

SFX are mixed into a separate audio track and muxed with the narration.
"""
from __future__ import annotations
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ── SFX definitions (FFmpeg lavfi source) ─────────────────────────────────────

SFX_LIBRARY = {
    # Transition sounds
    "whoosh_soft": {
        "filter": "anoisesrc=d=0.4:c=pink:r=44100:a=0.4,highpass=f=800,lowpass=f=4000,afade=in:st=0:d=0.05,afade=out:st=0.3:d=0.1",
        "duration": 0.4,
    },
    "whoosh_sharp": {
        "filter": "anoisesrc=d=0.3:c=white:r=44100:a=0.5,highpass=f=2000,lowpass=f=8000,afade=in:st=0:d=0.02,afade=out:st=0.25:d=0.05",
        "duration": 0.3,
    },
    "glitch_burst": {
        "filter": "anoisesrc=d=0.15:c=white:r=44100:a=0.7,highpass=f=3000,lowpass=f=12000,aphaser=in_gain=0.9:out_gain=0.8:delay=3:speed=5",
        "duration": 0.15,
    },
    "film_click": {
        "filter": "anoisesrc=d=0.06:c=white:r=44100:a=0.9,highpass=f=5000,afade=out:st=0.03:d=0.03",
        "duration": 0.06,
    },
    "impact_thud": {
        "filter": "sine=f=60:d=0.3:r=44100,volume=0.8,afade=out:st=0.1:d=0.2",
        "duration": 0.3,
    },
    "power_up": {
        "filter": "sine=f='250+t*300':d=0.5:r=44100,afade=in:st=0:d=0.05,afade=out:st=0.4:d=0.1",
        "duration": 0.5,
    },
    "swoosh": {
        "filter": "anoisesrc=d=0.25:c=pink:r=44100:a=0.6,highpass=f=1500,lowpass=f=6000,afade=in:st=0:d=0.02,afade=out:st=0.2:d=0.05",
        "duration": 0.25,
    },

    # UI sounds
    "typing_tick": {
        "filter": "anoisesrc=d=0.04:c=white:r=44100:a=0.4,highpass=f=4000,afade=out:st=0.02:d=0.02",
        "duration": 0.04,
    },
    "counter_tick": {
        "filter": "sine=f=800:d=0.05:r=44100,volume=0.5,afade=out:st=0.02:d=0.03",
        "duration": 0.05,
    },
    "scan_beep": {
        "filter": "sine=f=1200:d=0.1:r=44100,volume=0.4,afade=in:st=0:d=0.01,afade=out:st=0.08:d=0.02",
        "duration": 0.1,
    },
    "notification_ping": {
        "filter": "sine=f=1400:d=0.08:r=44100,sine=f=1800:d=0.08:r=44100,amix=inputs=2,afade=out:st=0.05:d=0.03",
        "duration": 0.08,
    },

    # Ambient (loopable)
    "hum_tech": {
        "filter": "sine=f=60:d=4:r=44100,volume=0.15,aecho=0.5:0.5:100:0.3",
        "duration": 4.0,
    },
    "light_static": {
        "filter": "anoisesrc=d=4:c=pink:r=44100:a=0.08,lowpass=f=600",
        "duration": 4.0,
    },
}


# ── Template → SFX auto-matching ──────────────────────────────────────────────

TEMPLATE_SFX_MAP = {
    "typewriter_reveal":  ("typing_tick", None),
    "split_reveal":       ("swoosh", None),
    "glitch_drop":        ("glitch_burst", "light_static"),
    "neon_pulse":         ("power_up", "hum_tech"),
    "countdown_slam":     ("impact_thud", None),
    "browser_mockup":     ("whoosh_soft", None),
    "phone_frame_scroll": ("whoosh_soft", None),
    "spotlight_zoom":     ("whoosh_soft", None),
    "comparison_split":   ("swoosh", None),
    "polaroid_drop":      ("film_click", None),
    "dashboard_reveal":   ("scan_beep", "hum_tech"),
    "counter_ticker":     ("counter_tick", None),
    "bar_race":           ("swoosh", None),
    "progress_ring":      ("notification_ping", "hum_tech"),
    "film_burn":          ("film_click", None),
    "lens_flare_wipe":    ("whoosh_sharp", None),
    "shatter_break":      ("glitch_burst", None),
    "particle_field":     (None, "hum_tech"),
    "matrix_rain":        (None, "hum_tech"),
    "hologram_flicker":   ("scan_beep", "hum_tech"),
}

# Style presets (scale volume / frequency)
SFX_STYLES = {
    "subtle":   {"volume": 0.06, "ambient_volume": 0.02},
    "medium":   {"volume": 0.12, "ambient_volume": 0.04},
    "dramatic": {"volume": 0.22, "ambient_volume": 0.07},
}


class SFXEngine:
    def __init__(self, sfx_dir: Path, style: str = "subtle",
                 sfx_enabled: bool = True, ambient_enabled: bool = True):
        self.sfx_dir = Path(sfx_dir)
        self.sfx_dir.mkdir(parents=True, exist_ok=True)
        self.style = SFX_STYLES.get(style, SFX_STYLES["subtle"])
        self.sfx_enabled = sfx_enabled
        self.ambient_enabled = ambient_enabled

    async def generate_sfx(self, sfx_name: str, volume_override: float = None) -> Path:
        """Generate a single SFX WAV file using FFmpeg lavfi."""
        out = self.sfx_dir / f"{sfx_name}.wav"
        if out.exists():
            return out

        if sfx_name not in SFX_LIBRARY:
            logger.warning(f"[SFX] Unknown SFX: {sfx_name}")
            return None

        sfx = SFX_LIBRARY[sfx_name]
        vol = volume_override or self.style["volume"]

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", sfx["filter"],
            "-t", str(sfx["duration"]),
            "-af", f"volume={vol}",
            "-ar", "44100",
            "-ac", "2",
            str(out),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning(f"[SFX] Failed to generate {sfx_name}: {stderr.decode()[-300:]}")
            return None
        return out

    async def build_sfx_track(self, timed_assets: list, total_duration: float,
                               output_path: Path) -> Path:
        """
        Build a full-length SFX audio track aligned to visual asset timings.
        Returns path to the mixed SFX audio file.
        """
        if not self.sfx_enabled or output_path.exists():
            return output_path

        # Collect SFX events
        events: list[tuple[float, Path]] = []  # (timestamp, sfx_file)

        for asset in timed_assets:
            template_name = getattr(asset, "template_name", "browser_mockup")
            transition_sfx, ambient_sfx = TEMPLATE_SFX_MAP.get(template_name, ("whoosh_soft", None))

            if transition_sfx and self.sfx_enabled:
                sfx_path = await self.generate_sfx(transition_sfx)
                if sfx_path:
                    events.append((asset.display_start, sfx_path))

        if not events:
            # Generate silence
            await self._silence(total_duration, output_path)
            return output_path

        # Build filter_complex to place SFX at exact timestamps
        inputs = []
        filter_parts = []
        mix_inputs = [f"[silence]"]

        # Create silence base
        silence_path = self.sfx_dir / "silence_base.wav"
        await self._silence(total_duration, silence_path)

        inputs.extend(["-i", str(silence_path)])
        filter_parts.append(f"[0:a]acopy[silence]")

        for idx, (ts, sfx_path) in enumerate(events):
            inputs.extend(["-i", str(sfx_path)])
            stream = f"[sfx{idx}]"
            filter_parts.append(f"[{idx+1}:a]adelay={int(ts*1000)}|{int(ts*1000)}[sfx{idx}]")
            mix_inputs.append(stream)

        mix_filter = f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:normalize=0[aout]"
        filter_parts.append(mix_filter)

        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", ";".join(filter_parts),
            "-map", "[aout]",
            "-t", str(total_duration),
            "-ar", "44100", "-ac", "2",
            str(output_path),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning(f"[SFX] Track build failed: {stderr.decode()[-500:]}")
            await self._silence(total_duration, output_path)

        return output_path

    async def _silence(self, duration: float, output_path: Path) -> Path:
        if output_path.exists():
            return output_path
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(duration),
            "-ar", "44100", "-ac", "2",
            str(output_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return output_path
