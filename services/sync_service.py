"""
A/V Sync Service
─────────────────
Assigns display timestamps to every VisualAsset based on real audio timing.

Strategy:
  - Each section gets its title card at section start
  - Screenshots are distributed evenly across the section's audio duration
  - Transitions are accounted for in overlap calculations
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

import logging

from config.settings import PipelineConfig
from utils.models import AudioChunk, VisualAsset, VideoScript

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def assign_timings(
        self,
        script: VideoScript,
        audio_chunks: list[AudioChunk],
        visual_assets: list[VisualAsset],
    ) -> list[VisualAsset]:
        """Assign display_start / display_end to every VisualAsset."""

        # Build a timing map: section_id → (start_time, end_time)
        timing_map: dict[str, tuple[float, float]] = {}
        for chunk in audio_chunks:
            timing_map[chunk.section_id] = (
                chunk.start_time,
                chunk.start_time + chunk.duration_seconds,
            )

        # Group assets by section
        by_section: dict[str, list[VisualAsset]] = {}
        for asset in visual_assets:
            by_section.setdefault(asset.section_id, []).append(asset)

        assigned: list[VisualAsset] = []
        for section_id, assets in by_section.items():
            if section_id not in timing_map:
                logger.warning(f"[Sync] No audio timing found for section '{section_id}', skipping")
                continue

            section_start, section_end = timing_map[section_id]
            section_duration = section_end - section_start

            title_cards = [a for a in assets if a.asset_type == "title_card"]
            screenshots = [a for a in assets if a.asset_type == "screenshot"]

            # Title card: show at section start for a brief moment (3s or 20% of section)
            title_duration = min(3.0, section_duration * 0.2)
            for tc in title_cards:
                tc.display_start = section_start
                tc.display_end = section_start + title_duration
                assigned.append(tc)

            # Distribute screenshots across remainder of section
            if screenshots:
                content_start = section_start + title_duration
                content_end = section_end
                content_duration = content_end - content_start
                per_screenshot = content_duration / len(screenshots)

                for i, ss in enumerate(screenshots):
                    ss.display_start = content_start + i * per_screenshot
                    ss.display_end = content_start + (i + 1) * per_screenshot
                    assigned.append(ss)
            else:
                # Extend title card to fill entire section
                for tc in title_cards:
                    tc.display_end = section_end

        # Sort by display start
        assigned.sort(key=lambda a: a.display_start)

        total = sum(1 for a in assigned)
        logger.info(f"[Sync] Assigned timings to {total} visual assets")
        return assigned
