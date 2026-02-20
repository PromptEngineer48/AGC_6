"""
Central configuration for the YouTube AI Video Pipeline.
Copy .env.example to .env and fill in your credentials.
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PipelineConfig:
    # ── API Keys ──────────────────────────────────────────────────────────────
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    elevenlabs_voice_id: str = field(default_factory=lambda: os.getenv("ELEVENLABS_VOICE_ID", ""))
    google_search_api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_SEARCH_API_KEY", ""))
    google_search_cx: str = field(default_factory=lambda: os.getenv("GOOGLE_SEARCH_CX", ""))

    # ── Model settings ────────────────────────────────────────────────────────
    claude_model: str = "claude-opus-4-6"
    script_target_minutes: int = 12          # Target video length in minutes
    words_per_minute: int = 150              # Average narration speed

    # ── Video settings ────────────────────────────────────────────────────────
    canvas_width: int = 1920
    canvas_height: int = 1080
    fps: int = 30
    transition_duration: float = 0.5        # seconds for fade transitions
    screenshot_display_duration: float = 8  # Default seconds per screenshot

    # ── ElevenLabs settings ───────────────────────────────────────────────────
    elevenlabs_model: str = "eleven_turbo_v2_5"
    elevenlabs_stability: float = 0.5
    elevenlabs_similarity_boost: float = 0.75
    elevenlabs_style: float = 0.0
    elevenlabs_use_speaker_boost: bool = True

    # ── Output settings ───────────────────────────────────────────────────────
    output_dir: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "./output"))
    cache_dir: str = field(default_factory=lambda: os.getenv("CACHE_DIR", "./cache"))
    temp_dir: str = field(default_factory=lambda: os.getenv("TEMP_DIR", "./temp"))

    # ── Background music (optional) ───────────────────────────────────────────
    background_music_path: Optional[str] = field(
        default_factory=lambda: os.getenv("BACKGROUND_MUSIC_PATH")
    )
    background_music_volume: float = 0.08   # Very low – just ambiance

    # ── Search settings ───────────────────────────────────────────────────────
    max_search_results: int = 10
    search_provider: str = field(
        default_factory=lambda: os.getenv("SEARCH_PROVIDER", "google")
    )  # "google" | "searx"
    searx_base_url: str = field(
        default_factory=lambda: os.getenv("SEARX_BASE_URL", "http://localhost:8080")
    )

    def validate(self) -> list[str]:
        """Return list of missing required config values."""
        errors = []
        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required")
        if not self.elevenlabs_api_key:
            errors.append("ELEVENLABS_API_KEY is required")
        if not self.elevenlabs_voice_id:
            errors.append("ELEVENLABS_VOICE_ID is required")
        if self.search_provider == "google":
            if not self.google_search_api_key:
                errors.append("GOOGLE_SEARCH_API_KEY is required when SEARCH_PROVIDER=google")
            if not self.google_search_cx:
                errors.append("GOOGLE_SEARCH_CX is required when SEARCH_PROVIDER=google")
        return errors
