"""
Base Template Class
All 20 templates inherit from this. Each template renders a static PNG,
then the motion + atmosphere + SFX layers are applied on top by the renderer.
"""
from __future__ import annotations
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BaseTemplate:
    """
    Every template must implement render_frame() which produces a static PNG.
    The renderer then wraps it with motion, atmosphere, and SFX.
    """

    name: str = "base"
    category: str = "base"

    def __init__(self, width: int = 1920, height: int = 1080,
                 bg_hex: str = "#0F1117", accent_hex: str = "#4A9EFF"):
        self.width = width
        self.height = height
        self.bg_hex = bg_hex
        self.accent_hex = accent_hex

    def hex_to_rgb(self, h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def render_frame(self, output_path: Path, **kwargs) -> Path:
        """Render a static PNG. Override in subclasses."""
        raise NotImplementedError

    def ffmpeg(self, args: list[str]) -> None:
        cmd = ["ffmpeg", "-y"] + args
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {result.stderr.decode()[-1500:]}")

    def get_font(self, size: int, bold: bool = True):
        from PIL import ImageFont
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        for fp in font_paths:
            try:
                return ImageFont.truetype(fp, size)
            except OSError:
                pass
        return ImageFont.load_default()

    def draw_wrapped_text(self, draw, text: str, font, pos: tuple, max_width: int,
                           colour: str, line_spacing: int = 10):
        words = text.split()
        lines, current = [], ""
        for word in words:
            test = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        x, y = pos
        for line in lines:
            draw.text((x, y), line, fill=colour, font=font)
            bbox = draw.textbbox((0, 0), line, font=font)
            y += (bbox[3] - bbox[1]) + line_spacing
        return y
