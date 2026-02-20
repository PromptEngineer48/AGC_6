"""
Kinetic Text & Title Card Templates (1–5)
Each renders a static PNG that the motion engine then animates.
"""
from __future__ import annotations
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from .base import BaseTemplate


class TypewriterReveal(BaseTemplate):
    """Template 1: Clean dark card with typewriter-style text layout."""
    name = "typewriter_reveal"
    category = "kinetic"

    def render_frame(self, output_path: Path, title: str = "", section_type: str = "", **kwargs) -> Path:
        img = Image.new("RGB", (self.width, self.height), self.hex_to_rgb(self.bg_hex))
        draw = ImageDraw.Draw(img)
        accent = self.hex_to_rgb(self.accent_hex)

        font_lg = self.get_font(80)
        font_sm = self.get_font(36, bold=False)
        font_cursor = self.get_font(84)

        # Blinking cursor line at top
        draw.rectangle([100, 80, 100 + 4, 160], fill=accent)

        # Section type label
        draw.text((120, 90), section_type.replace("_", " ").upper(), fill=accent, font=font_sm)

        # Main title with cursor at end
        self.draw_wrapped_text(draw, title, font_lg, (100, self.height // 2 - 60),
                               self.width - 200, "white")

        # Cursor blink indicator (static representation)
        draw.rectangle([100, self.height - 120, 140, self.height - 70], fill=accent)

        # Subtle scanline effect
        for y in range(0, self.height, 4):
            draw.line([(0, y), (self.width, y)], fill=(0, 0, 0, 15))

        img.save(str(output_path), "PNG")
        return output_path


class SplitReveal(BaseTemplate):
    """Template 2: Title split across two colour panels."""
    name = "split_reveal"
    category = "kinetic"

    def render_frame(self, output_path: Path, title: str = "", section_type: str = "", **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        # Left panel - dark with accent stripe
        draw.rectangle([0, 0, self.width // 2 - 20, self.height], fill=bg)
        # Right panel - accent tinted
        right_colour = tuple(min(255, int(c * 0.15)) for c in accent)
        draw.rectangle([self.width // 2 + 20, 0, self.width, self.height], fill=right_colour)

        # Centre divider
        draw.rectangle([self.width // 2 - 3, 0, self.width // 2 + 3, self.height], fill=accent)

        font_lg = self.get_font(88)
        font_sm = self.get_font(38, bold=False)

        # Section label top-left
        draw.text((60, 60), section_type.replace("_", " ").upper(), fill=accent, font=font_sm)

        # Title spanning centre
        words = title.split()
        mid = max(1, len(words) // 2)
        left_text = " ".join(words[:mid])
        right_text = " ".join(words[mid:])

        # Left half text (right-aligned)
        bbox = draw.textbbox((0, 0), left_text, font=font_lg)
        text_w = bbox[2] - bbox[0]
        draw.text((self.width // 2 - 40 - text_w, self.height // 2 - 50), left_text, fill="white", font=font_lg)

        # Right half text (left-aligned)
        draw.text((self.width // 2 + 40, self.height // 2 - 50), right_text, fill="white", font=font_lg)

        img.save(str(output_path), "PNG")
        return output_path


class GlitchDrop(BaseTemplate):
    """Template 3: RGB-offset glitch aesthetic title card."""
    name = "glitch_drop"
    category = "kinetic"

    def render_frame(self, output_path: Path, title: str = "", section_type: str = "", **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        font_lg = self.get_font(90)
        font_sm = self.get_font(36, bold=False)

        # Glitch horizontal bars (random noise bands)
        random.seed(42)
        for _ in range(8):
            y = random.randint(0, self.height)
            h = random.randint(2, 8)
            shift = random.randint(-30, 30)
            col = random.choice([(accent[0], 0, 0), (0, accent[1], 0), (0, 0, accent[2])])
            draw.rectangle([shift, y, self.width + shift, y + h], fill=col)

        # Section type
        draw.text((80, 70), section_type.replace("_", " ").upper(), fill=accent, font=font_sm)

        # Title with RGB split ghost layers
        tx, ty = 80, self.height // 2 - 50
        # Red channel ghost (offset left)
        draw.text((tx - 6, ty), title[:50], fill=(255, 0, 0, 80), font=font_lg)
        # Blue channel ghost (offset right)
        draw.text((tx + 6, ty + 4), title[:50], fill=(0, 0, 255, 80), font=font_lg)
        # Clean white main text
        self.draw_wrapped_text(draw, title, font_lg, (tx, ty), self.width - 200, "white")

        # Bottom accent bar
        draw.rectangle([0, self.height - 8, self.width, self.height], fill=accent)

        img.save(str(output_path), "PNG")
        return output_path


class NeonPulse(BaseTemplate):
    """Template 4: Neon glow text on dark background."""
    name = "neon_pulse"
    category = "kinetic"

    def render_frame(self, output_path: Path, title: str = "", section_type: str = "", **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)

        # Create glow layer
        glow_layer = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        font_lg = self.get_font(96)
        font_sm = self.get_font(40, bold=False)

        # Draw text on glow layer
        glow_draw.text((80, self.height // 2 - 60), title[:60], fill=accent, font=font_lg)

        # Blur for glow effect
        glow_blur = glow_layer.filter(ImageFilter.GaussianBlur(radius=20))
        img = Image.blend(img, glow_blur, 0.8)

        # Sharp text on top
        draw = ImageDraw.Draw(img)
        draw.text((80, 60), section_type.replace("_", " ").upper(), fill=accent, font=font_sm)
        self.draw_wrapped_text(draw, title, font_lg, (80, self.height // 2 - 60), self.width - 200, "white")

        # Corner accents
        corner_size = 40
        draw.rectangle([0, 0, corner_size, 4], fill=accent)
        draw.rectangle([0, 0, 4, corner_size], fill=accent)
        draw.rectangle([self.width - corner_size, self.height - 4, self.width, self.height], fill=accent)
        draw.rectangle([self.width - 4, self.height - corner_size, self.width, self.height], fill=accent)

        img.save(str(output_path), "PNG")
        return output_path


class CountdownSlam(BaseTemplate):
    """Template 5: Large number/stat slam with topic context."""
    name = "countdown_slam"
    category = "kinetic"

    def render_frame(self, output_path: Path, title: str = "", section_type: str = "",
                     countdown_number: int = 3, **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        font_huge = self.get_font(300)
        font_lg = self.get_font(72)
        font_sm = self.get_font(36, bold=False)

        # Big number (ghost/watermark)
        num_str = str(countdown_number)
        bbox = draw.textbbox((0, 0), num_str, font=font_huge)
        nx = (self.width - (bbox[2] - bbox[0])) // 2
        ny = (self.height - (bbox[3] - bbox[1])) // 2 - 60
        # Draw faint number
        faint_accent = tuple(int(c * 0.2) for c in accent)
        draw.text((nx, ny), num_str, fill=faint_accent, font=font_huge)

        # Title overlaid in centre
        bbox2 = draw.textbbox((0, 0), title[:40], font=font_lg)
        tx = (self.width - (bbox2[2] - bbox2[0])) // 2
        draw.text((tx, self.height // 2 - 30), title[:40], fill="white", font=font_lg)

        # Section type bottom
        draw.text((80, self.height - 100), section_type.replace("_", " ").upper(), fill=accent, font=font_sm)

        # Side accent lines
        draw.rectangle([0, 0, 6, self.height], fill=accent)
        draw.rectangle([self.width - 6, 0, self.width, self.height], fill=accent)

        img.save(str(output_path), "PNG")
        return output_path
