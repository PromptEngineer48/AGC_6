"""
Voice Service (v2 — config-driven)
Delegates synthesis to cfg.voice provider.
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
import hashlib
import logging
from pathlib import Path

from config.loader import RuntimeConfig
from utils.models import AudioChunk, VideoScript

logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(self, cfg: RuntimeConfig):
        self.cfg = cfg
        self.audio_dir = Path(cfg.temp_dir) / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def synthesise_script(self, script: VideoScript) -> list[AudioChunk]:
        logger.info(f"[Voice] Synthesising {len(script.sections)} sections via {self.cfg.voice.provider_name}")
        chunks: list[AudioChunk] = []
        t = 0.0

        for section in script.sections:
            text = section.narration_text.strip()
            if not text:
                continue

            # Cache key includes provider + voice settings hash so changing voices busts cache
            settings_hash = hashlib.md5(str(sorted(self.cfg.voice_settings.items())).encode()).hexdigest()[:8]
            cache_key = hashlib.md5(f"{self.cfg.voice.provider_name}:{settings_hash}:{text}".encode()).hexdigest()
            audio_path = self.audio_dir / f"{section.section_id}_{cache_key}.mp3"

            if not audio_path.exists():
                try:
                    await self.cfg.voice.synthesise(text, audio_path, self.cfg.voice_settings)
                except Exception as exc:
                    if self.cfg.abort_on_tts_failure:
                        raise
                    logger.error(f"[Voice] TTS failed for {section.section_id}: {exc}")
                    continue
            
            duration = await self.cfg.voice.get_duration(audio_path)
            chunk = AudioChunk(section_id=section.section_id, text=text, audio_path=audio_path, duration_seconds=duration, start_time=t)
            section.start_time = t
            section.estimated_duration_seconds = duration
            t += duration
            chunks.append(chunk)
            logger.info(f"[Voice] {section.section_id}: {duration:.1f}s")
            await asyncio.sleep(0.4)

        logger.info(f"[Voice] Total: {t:.1f}s across {len(chunks)} chunks")
        return chunks
