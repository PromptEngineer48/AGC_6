"""
Overlay & Ambient Templates (18–20)
"""
from __future__ import annotations
import random
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from .base import BaseTemplate


class ParticleField(BaseTemplate):
    """Template 18: Floating particle field behind screenshot."""
    name = "particle_field"
    category = "ambient"

    def render_frame(self, output_path: Path, image_path: Path = None, **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        # Draw particle network
        random.seed(99)
        particles = [(random.randint(0, self.width), random.randint(0, self.height))
                      for _ in range(80)]

        # Draw connection lines between nearby particles
        for i, (px, py) in enumerate(particles):
            for j, (qx, qy) in enumerate(particles[i+1:], i+1):
                dist = math.sqrt((px - qx)**2 + (py - qy)**2)
                if dist < 200:
                    alpha = int(60 * (1 - dist / 200))
                    col = tuple(int(c * alpha / 255) for c in accent)
                    draw.line([(px, py), (qx, qy)], fill=col, width=1)

        # Draw particles
        for px, py in particles:
            r = random.randint(2, 6)
            draw.ellipse([px - r, py - r, px + r, py + r], fill=accent)

        # Overlay screenshot (semi-transparent)
        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGBA")
                ss = ss.resize((self.width - 200, self.height - 150), Image.LANCZOS)
                # Make semi-transparent
                r2, g2, b2, a = ss.split()
                a = a.point(lambda x: int(x * 0.85))
                ss = Image.merge("RGBA", (r2, g2, b2, a))
                img = img.convert("RGBA")
                img.paste(ss, (100, 75), ss)
                img = img.convert("RGB")
            except Exception:
                pass

        img.save(str(output_path), "PNG")
        return output_path


class MatrixRain(BaseTemplate):
    """Template 19: Falling code characters as background layer."""
    name = "matrix_rain"
    category = "ambient"

    def render_frame(self, output_path: Path, image_path: Path = None, **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノ{}[]<>/|\\*#@!?="
        font_matrix = self.get_font(20, bold=False)

        # Draw falling columns
        random.seed(55)
        col_w = 28
        cols = self.width // col_w

        for col in range(cols):
            col_len = random.randint(5, 30)
            start_y = random.randint(-self.height, self.height)
            x = col * col_w

            for row in range(col_len):
                char = random.choice(chars)
                y = start_y + row * 24
                if 0 <= y < self.height:
                    # Leading character brighter
                    if row == col_len - 1:
                        char_col = (255, 255, 255)
                    else:
                        fade = 1 - (row / col_len)
                        char_col = tuple(int(c * fade * 0.7) for c in accent)
                    draw.text((x, y), char, fill=char_col, font=font_matrix)

        # Overlay screenshot
        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGBA")
                ss = ss.resize((self.width - 160, self.height - 120), Image.LANCZOS)
                r2, g2, b2, a = ss.split()
                a = a.point(lambda x: int(x * 0.88))
                ss = Image.merge("RGBA", (r2, g2, b2, a))
                img = img.convert("RGBA")
                img.paste(ss, (80, 60), ss)
                img = img.convert("RGB")
            except Exception:
                pass

        img.save(str(output_path), "PNG")
        return output_path


class HologramFlicker(BaseTemplate):
    """Template 20: Holographic scan lines and flicker overlay."""
    name = "hologram_flicker"
    category = "ambient"

    def render_frame(self, output_path: Path, image_path: Path = None, **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)

        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGB")
                ss = ss.resize((self.width, self.height), Image.LANCZOS)
                # Shift colour channels for holographic tint
                r, g, b = ss.split()
                # Tint toward accent colour
                from PIL import ImageEnhance
                img = ss
            except Exception:
                pass

        # Colour overlay tint
        overlay = Image.new("RGB", (self.width, self.height),
                              tuple(int(c * 0.3) for c in accent))
        img = Image.blend(img.convert("RGB"), overlay, 0.25)

        draw = ImageDraw.Draw(img)

        # Scan lines
        for y in range(0, self.height, 4):
            draw.line([(0, y), (self.width, y)], fill=(0, 0, 0), width=1)

        # Horizontal glitch bands
        random.seed(21)
        for _ in range(6):
            gy = random.randint(0, self.height)
            gh = random.randint(2, 10)
            gshift = random.randint(-15, 15)
            region = img.crop((0, gy, self.width, gy + gh))
            img.paste(region, (gshift, gy))

        # Corner circuit-board decoration
        draw = ImageDraw.Draw(img)
        for start, dirs in [((50, 50), [(1, 0), (0, 1), (1, 0)]),
                              ((self.width - 50, self.height - 50), [(-1, 0), (0, -1), (-1, 0)])]:
            cx2, cy2 = start
            for dx, dy in dirs:
                length = random.randint(40, 100)
                draw.line([(cx2, cy2), (cx2 + dx * length, cy2 + dy * length)],
                           fill=accent, width=2)
                draw.ellipse([cx2 + dx * length - 4, cy2 + dy * length - 4,
                               cx2 + dx * length + 4, cy2 + dy * length + 4], fill=accent)
                cx2 += dx * length
                cy2 += dy * length

        img.save(str(output_path), "PNG")
        return output_path
