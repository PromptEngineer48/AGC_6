"""
Pipeline Orchestrator (v2 — config-driven)
All wiring comes from RuntimeConfig; zero hardcoded provider names.
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

import json
import logging
import re
import time
from pathlib import Path

from config.loader import ConfigLoader, RuntimeConfig
from services.metadata_service import MetadataService
from services.research_service import ResearchService
from services.script_service import ScriptService
from services.sync_service import SyncService
from services.subtitle_service import SubtitleService
from services.video_service import VideoAssemblyService
from services.visual_service import VisualService
from services.voice_service import VoiceService
from utils.models import PipelineResult

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(self, cfg: RuntimeConfig):
        self.cfg = cfg
        self.research  = ResearchService(cfg)
        self.script    = ScriptService(cfg)
        self.visual    = VisualService(cfg)
        self.voice     = VoiceService(cfg)
        self.sync      = SyncService(cfg)
        self.subtitles = SubtitleService(Path(cfg.temp_dir) / "assembly")
        self.video     = VideoAssemblyService(cfg)
        self.metadata  = MetadataService(cfg)

    async def run(self, topic: str) -> PipelineResult:
        result = PipelineResult(topic=topic)
        t0 = time.time()

        def log(msg):
            logger.info(msg)
            result.pipeline_log.append(msg)

        try:
            # Create a dedicated run directory for this execution
            stem = _safe_stem(topic)
            run_timestamp = int(t0)
            run_dir = Path(self.cfg.output_dir) / f"{stem}_{run_timestamp}"
            run_dir.mkdir(parents=True, exist_ok=True)
            log(f"Output directory: {run_dir}")

            log(f"━━━ Pipeline: '{topic}' | LLM={self.cfg.llm.provider_name} "
                f"Search={self.cfg.search.provider_name} Voice={self.cfg.voice.provider_name} ━━━")

            # Helper to dump objects to JSON
            def save_step(name, data):
                try:
                    path = run_dir / f"{name}.json"
                    if hasattr(data, "__dict__"):
                        obj = data.__dict__
                    elif isinstance(data, list):
                        obj = [d.__dict__ if hasattr(d, "__dict__") else d for d in data]
                    else:
                        obj = data
                    path.write_text(json.dumps(obj, indent=2, default=str))
                    log(f"  💾 Saved {name}.json")
                except Exception as e:
                    log(f"  ⚠ Failed to save {name}: {e}")

            log("1/7 Research…")
            research = await self.research.research(topic)
            save_step("1_research", research)
            log(f"  ✓ {len(research.key_facts)} facts, {len(research.findings)} sources")

            log("2/7 Script…")
            script_obj = await self.script.generate_script(research)
            save_step("2_script", script_obj)
            log(f"  ✓ '{script_obj.title}' — {len(script_obj.sections)} sections")

            log("3/7 Visuals…")
            # script_obj is modified in place with visual markers, so we could save it again if we wanted
            # unique_stem is available from line 59-60, but let's make sure it's defined before here if we moved logic.
            # actually we defined run_dir earlier.
            unique_stem = f"{stem}_{run_timestamp}"
            raw_visuals = await self.visual.collect_visuals(script_obj, unique_stem)
            save_step("3_visuals_raw", raw_visuals)
            log(f"  ✓ {len(raw_visuals)} assets")
            if self.cfg.quality_checks_enabled and len(raw_visuals) < self.cfg.min_visual_assets:
                log(f"  ⚠ Only {len(raw_visuals)} visual assets (min {self.cfg.min_visual_assets})")

            log("4/7 Voice…")
            chunks = await self.voice.synthesise_script(script_obj)
            save_step("4_voice_chunks", chunks)
            log(f"  ✓ {sum(c.duration_seconds for c in chunks):.1f}s")
            
            # Save audio files mapping
            audio_map = {c.section_id: str(c.audio_path) for c in chunks}
            save_step("4_audio_map", audio_map)

            log("5/7 Sync…")
            timed = self.sync.assign_timings(script_obj, chunks, raw_visuals)
            save_step("5_sync", timed)
            log(f"  ✓ {len(timed)} assets timed")

            log("6/7 Video assembly…")
            unique_stem = f"{stem}_{run_timestamp}"

            # 1. Concat all audio so we have a single track for Whisper
            narration_audio = await self.video._concat_audio(chunks, unique_stem)

            # 2. Generate lovely animated subtitles using faster-whisper
            log(f"  [Subtitles] Generating from {narration_audio.name}")
            ass_path = await self.subtitles.generate_ass(narration_audio, unique_stem)
            log(f"  ✓ Subtitles ready: {ass_path.name}")

            # 3. Assemble and burn the subtitles onto the video track
            video_path = await self.video.assemble(chunks, timed, unique_stem, script=script_obj, subtitle_file=ass_path)
            
            # Move video to run_dir if successful
            final_video_path = run_dir / video_path.name
            if video_path.exists():
                video_path.replace(final_video_path)
                video_path = final_video_path
            
            log(f"  ✓ {video_path}")

            log("7/7 Metadata…")
            meta = await self.metadata.generate(script_obj, research)
            meta_path = run_dir / f"{stem}_metadata.json"
            meta_path.write_text(json.dumps({
                "title": meta.title, "description": meta.description,
                "tags": meta.tags, "category": meta.category,
                "thumbnail_suggestions": meta.thumbnail_suggestions,
            }, indent=2))
            log(f"  ✓ {meta_path}")

            log(f"━━━ Done in {time.time()-t0:.1f}s ━━━")
            result.video_path = video_path
            result.metadata = meta
            result.metadata_json_path = meta_path
            result.success = True

        except Exception as exc:
            logger.exception(f"[Pipeline] Fatal: {exc}")
            result.error_message = str(exc)
            result.success = False

        return result


def _safe_stem(title: str) -> str:
    s = re.sub(r"[^\w\s-]", "", title)
    return re.sub(r"\s+", "_", s.strip())[:80] or "video"
