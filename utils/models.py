"""
Shared data models for the YouTube AI Video Pipeline.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class ResearchFinding:
    title: str
    url: str
    snippet: str
    full_content: Optional[str] = None
    relevance_score: float = 0.0


@dataclass
class ResearchResult:
    topic: str
    query_used: str
    findings: list[ResearchFinding] = field(default_factory=list)
    key_facts: list[str] = field(default_factory=list)
    structured_summary: str = ""
    relevant_urls: list[str] = field(default_factory=list)


@dataclass
class VisualMarker:
    """Embedded in script to trigger a screenshot or visual."""
    marker_type: str          # "screenshot" | "visual" | "title_card"
    url: Optional[str] = None
    description: Optional[str] = None
    section_id: str = ""
    focus_text: Optional[str] = None


@dataclass
class ScriptSection:
    section_id: str
    section_type: str         # "intro" | "main" | "demo" | "conclusion"
    title: str
    narration_text: str
    visual_markers: list[VisualMarker] = field(default_factory=list)
    estimated_duration_seconds: float = 0.0
    start_time: float = 0.0   # filled in after TTS


@dataclass
class VideoScript:
    topic: str
    title: str
    sections: list[ScriptSection] = field(default_factory=list)
    full_text: str = ""
    total_estimated_seconds: float = 0.0


@dataclass
class AudioChunk:
    section_id: str
    text: str
    audio_path: Path
    duration_seconds: float
    start_time: float = 0.0


@dataclass
class VisualAsset:
    section_id: str
    asset_type: str           # "screenshot" | "title_card" | "generated"
    file_path: Path
    url: Optional[str] = None
    description: str = ""
    display_start: float = 0.0
    display_end: float = 0.0


@dataclass
class VideoMetadata:
    title: str
    description: str
    tags: list[str] = field(default_factory=list)
    thumbnail_path: Optional[Path] = None
    thumbnail_suggestions: list[str] = field(default_factory=list)
    category: str = "Science & Technology"


@dataclass
class PipelineResult:
    topic: str
    video_path: Optional[Path] = None
    metadata: Optional[VideoMetadata] = None
    metadata_json_path: Optional[Path] = None
    success: bool = False
    error_message: str = ""
    pipeline_log: list[str] = field(default_factory=list)
