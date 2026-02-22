"""
Video Assembly Service (v2 — style and codec from config)
"""
from __future__ import annotations
import sys as _sys
import os as _os
# Add the project root (this file's parent or grandparent) to sys.path
_this_file = _os.path.abspath(__file__)
_project_root = _os.path.dirname(_os.path.dirname(_this_file))  # goes up to AGC_4/
if _project_root not in _sys.path:
    _sys.path.insert(0, _project_root)
# Also add project root itself (for files directly in AGC_4/)
_self_dir = _os.path.dirname(_this_file)
if _self_dir not in _sys.path:
    _sys.path.insert(0, _self_dir)

import asyncio
import logging
import shutil
from pathlib import Path

from config.loader import RuntimeConfig
from utils.models import AudioChunk, VisualAsset

logger = logging.getLogger(__name__)


class VideoAssemblyService:
    def __init__(self, cfg: RuntimeConfig):
        self.cfg = cfg
        self.temp_dir = Path(cfg.temp_dir) / "assembly"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = Path(cfg.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def assemble(self, audio_chunks: list[AudioChunk], visual_assets: list[VisualAsset],
                       output_stem: str, script=None, subtitle_file: Path=None) -> Path:
        logger.info("[Video] Assembling with Visual Engine")
        narration = await self._concat_audio(audio_chunks, output_stem)
        total_dur = sum(c.duration_seconds for c in audio_chunks)
        visual_assets = await self._run_visual_engine(visual_assets, output_stem, script)
        video_track = await self._build_video_track(visual_assets, total_dur, output_stem)
        mixed_audio = await self._mix_audio(narration, total_dur, output_stem)
        out = self.output_dir / f"{output_stem}.mp4"
        await self._mux(video_track, mixed_audio, out, subtitle_file)
        actual = await self._duration(out)
        drift = abs(actual - total_dur)
        logger.info(f"[Video] Done: {out} | {actual:.1f}s (drift: {drift:.2f}s)")
        if self.cfg.quality_checks_enabled and drift > self.cfg.max_sync_drift_sec:
            logger.warning(f"[Video] Sync drift {drift:.2f}s exceeds threshold {self.cfg.max_sync_drift_sec}s")
        return out

    async def _run_visual_engine(self, assets, stem, script):
        """Run the 4-layer Visual Engine over all assets."""
        try:
            import sys as _sys2, os as _os2
            _sys2.path.insert(0, _os2.path.dirname(_os2.path.dirname(_os2.path.abspath(__file__))))
            from visual_engine import VisualRenderer

            style = self.cfg.video_style
            visual_cfg = self.cfg._raw.get("visual", {})

            renderer = VisualRenderer(
                width=self.cfg.canvas_width,
                height=self.cfg.canvas_height,
                fps=self.cfg.fps,
                codec=self.cfg.video_codec,
                preset=self.cfg.ffmpeg_preset,
                bg_hex=style.get("background_colour", "#0F1117"),
                accent_colours=style.get("accent_colours", ["#4A9EFF", "#FF6B35", "#00C896", "#9B59B6"]),
                sfx_style=visual_cfg.get("sfx_style", "subtle"),
                sfx_enabled=visual_cfg.get("sfx_enabled", True),
                ambient_enabled=visual_cfg.get("ambient_enabled", True),
                motion_intensity=visual_cfg.get("motion_intensity", 0.35),
                atmosphere_intensity=visual_cfg.get("atmosphere_intensity", 0.3),
                template_override=visual_cfg.get("template") if not visual_cfg.get("auto_select", True) else None,
                motion_override=visual_cfg.get("motion"),
                atmosphere_override=visual_cfg.get("atmosphere"),
            )

            work_dir = self.temp_dir / f"{stem}_engine"
            assets = await renderer.render_all(assets, work_dir, script)
            logger.info(f"[Video] Visual Engine complete — {len(assets)} animated clips")
        except Exception as exc:
            logger.warning(f"[Video] Visual Engine failed ({exc}), falling back to static clips")

        return assets

    async def _concat_audio(self, chunks, stem):
        out = self.temp_dir / f"{stem}_narration.mp3"
        if out.exists():
            return out
        lst = self.temp_dir / f"{stem}_audio_list.txt"
        lst.write_text("\n".join(f"file '{c.audio_path.resolve()}'" for c in chunks))
        await self._ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])
        return out

    async def _build_video_track(self, assets, total_dur, stem):
        out = self.temp_dir / f"{stem}_video_track.mp4"
        if out.exists():
            return out
        if not assets:
            return await self._black(total_dur, out)
        clips = []
        for i, a in enumerate(assets):
            dur = max(a.display_end - a.display_start, 1.0)
            clip_path = getattr(a, "clip_path", None)
            clips.append((await self._img_to_clip(a.file_path, dur, i, stem, clip_path), dur))
        concat = await self._xfade(clips, stem)
        await self._trim_pad(concat, total_dur, out)
        return out

    async def _img_to_clip(self, img_path, duration, idx, stem, clip_path=None):
        # Use pre-rendered animated clip from Visual Engine if available
        if clip_path and Path(clip_path).exists():
            return Path(clip_path)
        out = self.temp_dir / f"{stem}_clip_{idx:04d}.mp4"
        if out.exists():
            return out
        w, h = self.cfg.canvas_width, self.cfg.canvas_height
        style = self.cfg.video_style
        if style.get("ken_burns", True):
            zoom = style.get("ken_burns_zoom", 0.0004)
            vf = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
                  f"zoompan=z='min(zoom+{zoom},1.05)':d={int(duration*self.cfg.fps)}:s={w}x{h}:fps={self.cfg.fps}")
        else:
            vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"
        await self._ffmpeg(["-loop", "1", "-framerate", str(self.cfg.fps), "-i", str(img_path),
                            "-vf", vf, "-t", str(duration), "-c:v", self.cfg.video_codec,
                            "-preset", self.cfg.ffmpeg_preset, "-pix_fmt", "yuv420p", str(out)])
        return out

    async def _xfade(self, clips, stem):
        out = self.temp_dir / f"{stem}_clips_concat.mp4"
        if out.exists():
            return out
        if len(clips) == 1:
            shutil.copy(clips[0][0], out)
            return out
        td = self.cfg.transition_duration
        tt = self.cfg.transition_type
        inputs = sum([["-i", str(p)] for p, _ in clips], [])
        parts, prev, cum = [], "[0:v]", 0.0
        for i in range(1, len(clips)):
            cum += clips[i-1][1] - td
            nxt = f"[xf{i}]" if i < len(clips) - 1 else "[vout]"
            parts.append(f"{prev}[{i}:v]xfade=transition={tt}:duration={td}:offset={cum:.3f}{nxt}")
            prev = f"[xf{i}]"
        await self._ffmpeg(inputs + ["-filter_complex", ";".join(parts), "-map", "[vout]",
                                     "-c:v", self.cfg.video_codec, "-preset", self.cfg.ffmpeg_preset,
                                     "-pix_fmt", "yuv420p", str(out)])
        return out

    async def _black(self, dur, out):
        w, h = self.cfg.canvas_width, self.cfg.canvas_height
        await self._ffmpeg(["-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={self.cfg.fps}",
                            "-t", str(dur), "-c:v", self.cfg.video_codec, "-pix_fmt", "yuv420p", str(out)])
        return out

    async def _trim_pad(self, src, target, out):
        actual = await self._duration(src)
        if abs(actual - target) < 0.1:
            shutil.copy(src, out)
            return
        if actual > target:
            await self._ffmpeg(["-i", str(src), "-t", str(target), "-c", "copy", str(out)])
        else:
            await self._ffmpeg(["-i", str(src), "-vf", f"tpad=stop_mode=clone:stop_duration={target - actual}",
                                "-c:v", self.cfg.video_codec, "-pix_fmt", "yuv420p", str(out)])

    async def _mix_audio(self, narration, duration, stem):
        out = self.temp_dir / f"{stem}_audio_mixed.aac"
        if out.exists():
            return out
        if self.cfg.bg_music_enabled and self.cfg.bg_music_path and Path(self.cfg.bg_music_path).exists():
            vol = self.cfg.bg_music_volume
            fi = self.cfg._raw["video"]["background_music"].get("fade_in_sec", 2)
            fo = self.cfg._raw["video"]["background_music"].get("fade_out_sec", 3)
            await self._ffmpeg([
                "-i", str(narration), "-stream_loop", "-1", "-i", self.cfg.bg_music_path,
                "-filter_complex",
                f"[1:a]volume={vol},atrim=duration={duration},afade=in:st=0:d={fi},afade=out:st={duration-fo}:d={fo}[music];"
                f"[0:a][music]amix=inputs=2:duration=first[aout]",
                "-map", "[aout]", "-c:a", self.cfg.audio_codec, "-b:a", self.cfg.audio_bitrate, str(out),
            ])
        else:
            await self._ffmpeg(["-i", str(narration), "-c:a", self.cfg.audio_codec, "-b:a", self.cfg.audio_bitrate, str(out)])
        return out

    async def _mux(self, video, audio, out, subtitle_file=None):
        if subtitle_file and subtitle_file.exists():
            # Burn subtitles into the video track using a filter
            # Also re-encode the video track so the filter applies permanently
            vf_string = f"subtitles='{str(subtitle_file)}'"
            await self._ffmpeg([
                "-i", str(video), "-i", str(audio), 
                "-map", "0:v", "-map", "1:a",
                "-vf", vf_string,
                "-c:v", self.cfg.video_codec, "-preset", self.cfg.ffmpeg_preset,
                "-c:a", "copy", "-shortest", str(out)
            ])
        else:
            await self._ffmpeg(["-i", str(video), "-i", str(audio), "-map", "0:v", "-map", "1:a",
                                "-c:v", "copy", "-c:a", "copy", "-shortest", str(out)])

    async def _ffmpeg(self, args):
        cmd = ["ffmpeg", "-y"] + args
        logger.debug(f"[Video] {' '.join(cmd[:8])}...")
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed:\n{stderr.decode()[-2000:]}")

    @staticmethod
    async def _duration(path):
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        try:
            return float(stdout.decode().strip())
        except ValueError:
            return 0.0
