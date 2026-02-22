import logging
import asyncio
from pathlib import Path
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# Basic Advanced SubStation Alpha (ASS) Header
# We use a bright yellow primary color (&H0000FFFF) with a thick black outline and shadow
# Alignment=2 means bottom center
_ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,84,&H0000FFFF,&H000000FF,&H00000000,&H88000000,-1,0,0,0,100,100,0,0,1,5,3,2,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

class SubtitleService:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.model = None

    def _load_model(self):
        if self.model is None:
            logger.info("[Subtitle] Loading faster-whisper 'base' model...")
            self.model = WhisperModel("base", device="cpu", compute_type="int8")

    async def generate_ass(self, audio_path: Path, output_stem: str) -> Path:
        """
        Transcribe the mixed narration audio and return an .ass subtitle file path.
        """
        out_path = self.temp_dir / f"{output_stem}_subtitles.ass"
        if out_path.exists():
            return out_path

        # Run transcription in a thread so we don't block the async event loop
        def _transcribe():
            self._load_model()
            logger.info(f"[Subtitle] Transcribing {audio_path.name}...")
            # word_timestamps=True gives us exact timings down to the word
            segments, _ = self.model.transcribe(str(audio_path), word_timestamps=True)
            
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(_ASS_HEADER)
                for segment in segments:
                    # Group words into chunks of ~3-5 words so it's punchy
                    chunk = []
                    chunk_start = None
                    chunk_end = None
                    
                    for word in segment.words:
                        if chunk_start is None:
                            chunk_start = word.start
                        chunk.append(word.word.strip())
                        chunk_end = word.end
                        
                        # Once we have 4 words, or if it's the end of a sentence
                        if len(chunk) >= 4 or word.word.strip().endswith(('.', '?', '!')):
                            self._write_ass_event(f, chunk_start, chunk_end, " ".join(chunk))
                            chunk = []
                            chunk_start = None
                            
                    # Write any remaining words in the segment
                    if chunk and chunk_start is not None:
                        self._write_ass_event(f, chunk_start, chunk_end, " ".join(chunk))

        await asyncio.to_thread(_transcribe)
        logger.info(f"[Subtitle] Generated highly-kinetic ASS subtitles: {out_path.name}")
        return out_path

    def _write_ass_event(self, f, start_sec: float, end_sec: float, text: str):
        """Format timestamp and write an ASS event line."""
        start_str = self._format_ass_time(start_sec)
        end_str = self._format_ass_time(end_sec)
        # Escape any potential commas if needed, though usually fine in the Text field
        clean_text = text.replace('\n', ' ')
        f.write(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{clean_text}\n")

    def _format_ass_time(self, seconds: float) -> str:
        """Format seconds into ASS time format: H:MM:SS.cs"""
        h = int(seconds / 3600)
        m = int((seconds % 3600) / 60)
        s = int(seconds % 60)
        cs = int((seconds - int(seconds)) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
