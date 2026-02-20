"""
Cinematic Transition Templates (15–17)
These generate transition frame PNGs used between scenes.
"""
from __future__ import annotations
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from .base import BaseTemplate


class FilmBurn(BaseTemplate):
    """Template 15: Old film burn effect between scenes."""
    name = "film_burn"
    category = "transitions"

    def render_frame(self, output_path: Path, image_path: Path = None, **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        img = Image.new("RGB", (self.width, self.height), (10, 5, 0))

        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGB").resize(
                    (self.width, self.height), Image.LANCZOS)
                img.paste(ss)
            except Exception:
                pass

        draw = ImageDraw.Draw(img)

        # Film burn overlay — orange/red irregular patches
        random.seed(7)
        for _ in range(40):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            r = random.randint(20, 200)
            alpha = random.randint(60, 200)
            burn_col = (min(255, 200 + random.randint(0, 55)),
                         min(255, 80 + random.randint(0, 80)),
                         random.randint(0, 30))
            overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.ellipse([x - r, y - r, x + r, y + r], fill=(*burn_col, alpha))
            overlay = overlay.filter(ImageFilter.GaussianBlur(r // 2))
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay).convert("RGB")

        # Film grain
        draw = ImageDraw.Draw(img)
        for _ in range(3000):
            gx = random.randint(0, self.width)
            gy = random.randint(0, self.height)
            gb = random.randint(0, 255)
            draw.point((gx, gy), fill=(gb, gb, gb))

        # Horizontal scratches
        for _ in range(5):
            sy = random.randint(0, self.height)
            draw.line([(0, sy), (self.width, sy)], fill=(200, 180, 100), width=1)

        img.save(str(output_path), "PNG")
        return output_path


class LensFlareWipe(BaseTemplate):
    """Template 16: Bright lens flare wipe transition."""
    name = "lens_flare_wipe"
    category = "transitions"

    def render_frame(self, output_path: Path, image_path: Path = None,
                     flare_x: float = 0.5, **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        img = Image.new("RGB", (self.width, self.height), bg)

        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGB").resize(
                    (self.width, self.height), Image.LANCZOS)
                img.paste(ss)
            except Exception:
                pass

        # Lens flare overlay
        flare_cx = int(self.width * flare_x)
        flare_cy = self.height // 2
        accent = self.hex_to_rgb(self.accent_hex)

        for radius, alpha in [(800, 30), (400, 60), (200, 100), (80, 180), (30, 255)]:
            overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            flare_col = (min(255, accent[0] + 100), min(255, accent[1] + 100), 255)
            od.ellipse([flare_cx - radius, flare_cy - radius // 2,
                         flare_cx + radius, flare_cy + radius // 2],
                        fill=(*flare_col, alpha))
            overlay = overlay.filter(ImageFilter.GaussianBlur(radius // 3))
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay).convert("RGB")

        # Horizontal streak
        draw = ImageDraw.Draw(img)
        draw.line([(0, flare_cy), (self.width, flare_cy)],
                   fill=(255, 255, 255), width=3)

        img.save(str(output_path), "PNG")
        return output_path


class ShatterBreak(BaseTemplate):
    """Template 17: Frame shatters into geometric pieces."""
    name = "shatter_break"
    category = "transitions"

    def render_frame(self, output_path: Path, image_path: Path = None, **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)

        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGB").resize(
                    (self.width, self.height), Image.LANCZOS)
                img.paste(ss)
            except Exception:
                pass

        draw = ImageDraw.Draw(img)

        # Draw shatter crack lines from centre
        random.seed(13)
        cx, cy = self.width // 2, self.height // 2
        n_cracks = 12
        import math
        for i in range(n_cracks):
            angle = (360 / n_cracks) * i + random.randint(-15, 15)
            rad = math.radians(angle)
            length = random.randint(300, max(self.width, self.height))
            ex = cx + int(math.cos(rad) * length)
            ey = cy + int(math.sin(rad) * length)
            draw.line([(cx, cy), (ex, ey)], fill=accent, width=3)
            # Secondary crack
            mid_x = (cx + ex) // 2 + random.randint(-100, 100)
            mid_y = (cy + ey) // 2 + random.randint(-80, 80)
            ex2 = mid_x + random.randint(-200, 200)
            ey2 = mid_y + random.randint(-200, 200)
            draw.line([(mid_x, mid_y), (ex2, ey2)], fill=accent, width=2)

        # Centre bright point
        draw.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=accent)
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([cx - 80, cy - 80, cx + 80, cy + 80], fill=(*accent, 120))
        overlay = overlay.filter(ImageFilter.GaussianBlur(40))
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay).convert("RGB")

        img.save(str(output_path), "PNG")
        return output_path
