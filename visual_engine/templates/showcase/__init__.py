"""
Screenshot & Image Showcase Templates (6–11)
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from .base import BaseTemplate


class BrowserMockup(BaseTemplate):
    """Template 6: Screenshot inside a floating browser chrome frame."""
    name = "browser_mockup"
    category = "showcase"

    def render_frame(self, output_path: Path, image_path: Path = None,
                     url: str = "https://example.com", **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        # Browser window dimensions
        margin = 80
        chrome_h = 70
        bw = self.width - margin * 2
        bh = self.height - margin * 2

        # Drop shadow
        shadow = Image.new("RGB", (self.width, self.height), bg)
        sdraw = ImageDraw.Draw(shadow)
        sdraw.rectangle([margin + 8, margin + 8, margin + bw + 8, margin + bh + 8], fill=(10, 10, 20))
        shadow = shadow.filter(ImageFilter.GaussianBlur(20))
        img = Image.blend(img, shadow, 0.7)
        draw = ImageDraw.Draw(img)

        # Browser frame background
        draw.rectangle([margin, margin, margin + bw, margin + bh], fill=(30, 32, 40))

        # Chrome bar
        draw.rectangle([margin, margin, margin + bw, margin + chrome_h], fill=(45, 47, 55))

        # Traffic light dots
        dot_y = margin + chrome_h // 2
        for i, col in enumerate([(255, 95, 87), (255, 189, 68), (40, 201, 64)]):
            draw.ellipse([margin + 20 + i * 28, dot_y - 8, margin + 36 + i * 28, dot_y + 8], fill=col)

        # URL bar
        url_x = margin + 110
        url_w = bw - 200
        draw.rectangle([url_x, margin + 15, url_x + url_w, margin + chrome_h - 15], fill=(55, 57, 65),
                        outline=(80, 82, 90))
        font_sm = self.get_font(22, bold=False)
        draw.text((url_x + 12, margin + 22), url[:60], fill=(180, 180, 180), font=font_sm)

        # Screenshot content area
        content_y = margin + chrome_h
        content_h = bh - chrome_h
        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGB")
                ss = ss.resize((bw, content_h), Image.LANCZOS)
                img.paste(ss, (margin, content_y))
            except Exception:
                draw.rectangle([margin, content_y, margin + bw, margin + bh], fill=(20, 22, 30))
        else:
            draw.rectangle([margin, content_y, margin + bw, margin + bh], fill=(20, 22, 30))
            font_lg = self.get_font(48)
            draw.text((margin + bw // 2 - 100, margin + bh // 2 - 30), "Loading...", fill=accent, font=font_lg)

        img.save(str(output_path), "PNG")
        return output_path


class PhoneFrameScroll(BaseTemplate):
    """Template 7: Screenshot inside a phone frame."""
    name = "phone_frame_scroll"
    category = "showcase"

    def render_frame(self, output_path: Path, image_path: Path = None, **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        # Phone frame dimensions (portrait, centred)
        pw = 380
        ph = 720
        px = (self.width - pw) // 2
        py = (self.height - ph) // 2

        # Phone body shadow
        for r in range(20, 0, -1):
            alpha = int(255 * (1 - r / 20) * 0.4)
            shadow_col = tuple(min(255, int(c * 0.1)) for c in accent)
            draw.rounded_rectangle([px - r, py - r, px + pw + r, py + ph + r],
                                    radius=50, outline=shadow_col)

        # Phone body
        draw.rounded_rectangle([px, py, px + pw, py + ph], radius=40, fill=(30, 32, 40))

        # Screen area
        screen_margin = 16
        screen_top = py + 60
        screen_bottom = py + ph - 30
        screen_x = px + screen_margin
        screen_w = pw - screen_margin * 2

        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGB")
                screen_h = screen_bottom - screen_top
                ss = ss.resize((screen_w, screen_h), Image.LANCZOS)
                img.paste(ss, (screen_x, screen_top))
            except Exception:
                draw.rectangle([screen_x, screen_top, screen_x + screen_w, screen_bottom], fill=(20, 22, 30))
        else:
            draw.rectangle([screen_x, screen_top, screen_x + screen_w, screen_bottom], fill=(20, 22, 30))

        # Notch
        notch_w = 120
        notch_h = 28
        draw.rounded_rectangle([px + pw // 2 - notch_w // 2, py + 12,
                                  px + pw // 2 + notch_w // 2, py + 12 + notch_h],
                                radius=14, fill=(20, 22, 28))

        # Home indicator
        draw.rounded_rectangle([px + pw // 2 - 50, py + ph - 22, px + pw // 2 + 50, py + ph - 12],
                                radius=5, fill=(80, 80, 90))

        img.save(str(output_path), "PNG")
        return output_path


class SpotlightZoom(BaseTemplate):
    """Template 8: Screenshot with spotlight/vignette focus effect."""
    name = "spotlight_zoom"
    category = "showcase"

    def render_frame(self, output_path: Path, image_path: Path = None, **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        img = Image.new("RGB", (self.width, self.height), bg)

        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGB")
                ss = ss.resize((self.width, self.height), Image.LANCZOS)
                img.paste(ss, (0, 0))
            except Exception:
                pass

        # Vignette overlay (dark edges, bright centre)
        vignette = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        vdraw = ImageDraw.Draw(vignette)
        cx, cy = self.width // 2, self.height // 2
        for r in range(min(self.width, self.height) // 2, 0, -5):
            alpha = int(180 * (1 - r / (min(self.width, self.height) / 2)) ** 2)
            vdraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, alpha))

        img = img.convert("RGBA")
        img = Image.alpha_composite(img, vignette).convert("RGB")

        # Accent border
        draw = ImageDraw.Draw(img)
        accent = self.hex_to_rgb(self.accent_hex)
        draw.rectangle([0, 0, self.width - 1, self.height - 1], outline=accent, width=4)

        img.save(str(output_path), "PNG")
        return output_path


class ComparisonSplit(BaseTemplate):
    """Template 9: Two screenshots side by side with animated divider."""
    name = "comparison_split"
    category = "showcase"

    def render_frame(self, output_path: Path, image_path: Path = None,
                     image_path_2: Path = None, label_left: str = "Before",
                     label_right: str = "After", **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        half = self.width // 2
        font_lg = self.get_font(52)

        # Left side
        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGB").resize((half - 4, self.height), Image.LANCZOS)
                img.paste(ss, (0, 0))
            except Exception:
                pass
        else:
            draw.rectangle([0, 0, half - 4, self.height], fill=(20, 22, 30))

        # Right side
        if image_path_2 and Path(image_path_2).exists():
            try:
                ss2 = Image.open(str(image_path_2)).convert("RGB").resize((half - 4, self.height), Image.LANCZOS)
                img.paste(ss2, (half + 4, 0))
            except Exception:
                pass
        else:
            draw.rectangle([half + 4, 0, self.width, self.height], fill=(25, 27, 35))

        draw = ImageDraw.Draw(img)

        # Centre divider with accent colour
        draw.rectangle([half - 4, 0, half + 4, self.height], fill=accent)

        # Labels
        draw.rectangle([0, 0, half - 4, 80], fill=(0, 0, 0))
        draw.text((30, 20), label_left, fill="white", font=font_lg)
        draw.rectangle([half + 4, 0, self.width, 80], fill=(0, 0, 0))
        draw.text((half + 30, 20), label_right, fill="white", font=font_lg)

        img.save(str(output_path), "PNG")
        return output_path


class PolaroidDrop(BaseTemplate):
    """Template 10: Screenshot as a polaroid photo with shadow."""
    name = "polaroid_drop"
    category = "showcase"

    def render_frame(self, output_path: Path, image_path: Path = None,
                     caption: str = "", **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        # Subtle background texture lines
        for y in range(0, self.height, 60):
            draw.line([(0, y), (self.width, y)], fill=(255, 255, 255), width=1)

        # Polaroid dimensions
        pw = 700
        ph = 760
        margin_top = 40
        margin_bottom = 120
        photo_h = ph - margin_top - margin_bottom
        px = (self.width - pw) // 2
        py = (self.height - ph) // 2

        # Rotation (slight tilt)
        import math
        tilt = 3  # degrees

        # Create polaroid on separate canvas
        polaroid = Image.new("RGB", (pw, ph), "white")
        pdraw = ImageDraw.Draw(polaroid)

        # Photo area
        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGB")
                ss = ss.resize((pw - 60, photo_h), Image.LANCZOS)
                polaroid.paste(ss, (30, margin_top))
            except Exception:
                pdraw.rectangle([30, margin_top, pw - 30, margin_top + photo_h], fill=(200, 200, 210))
        else:
            pdraw.rectangle([30, margin_top, pw - 30, margin_top + photo_h], fill=(200, 200, 210))

        # Caption
        font_sm = self.get_font(32, bold=False)
        cap_y = margin_top + photo_h + 20
        pdraw.text((pw // 2 - 150, cap_y), caption[:30] or "Screenshot", fill=(60, 60, 60), font=font_sm)

        # Rotate polaroid
        polaroid_rotated = polaroid.rotate(tilt, expand=True, fillcolor=self.hex_to_rgb(self.bg_hex))

        # Drop shadow
        shadow = Image.new("RGB", (self.width, self.height), bg)
        shadow.paste(Image.new("RGB", polaroid_rotated.size, (0, 0, 10)),
                     (px - 10 + 20, py - 10 + 20))
        shadow = shadow.filter(ImageFilter.GaussianBlur(25))
        img = Image.blend(img, shadow, 0.6)

        # Paste polaroid
        img.paste(polaroid_rotated, (px - 10, py - 10))

        img.save(str(output_path), "PNG")
        return output_path


class DashboardReveal(BaseTemplate):
    """Template 11: Screenshot presented as a dashboard with panel borders."""
    name = "dashboard_reveal"
    category = "showcase"

    def render_frame(self, output_path: Path, image_path: Path = None,
                     title: str = "Dashboard", **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        panel_bg = tuple(min(255, c + 10) for c in bg)

        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        # Header bar
        draw.rectangle([0, 0, self.width, 80], fill=panel_bg)
        font_lg = self.get_font(44)
        font_sm = self.get_font(28, bold=False)
        draw.rectangle([0, 0, 6, 80], fill=accent)
        draw.text((30, 18), title[:60], fill="white", font=font_lg)

        # Status dots
        for i, col in enumerate([(40, 201, 64), (255, 189, 68), accent]):
            draw.ellipse([self.width - 120 + i * 35, 28, self.width - 108 + i * 35, 52], fill=col)

        # Main content area with screenshot
        content_margin = 16
        content_top = 96
        content_h = self.height - content_top - content_margin

        # Border glow
        draw.rectangle([content_margin - 2, content_top - 2,
                         self.width - content_margin + 2, content_top + content_h + 2],
                        outline=accent, width=2)

        if image_path and Path(image_path).exists():
            try:
                ss = Image.open(str(image_path)).convert("RGB")
                ss = ss.resize((self.width - content_margin * 2, content_h), Image.LANCZOS)
                img.paste(ss, (content_margin, content_top))
            except Exception:
                draw.rectangle([content_margin, content_top,
                                  self.width - content_margin, content_top + content_h], fill=panel_bg)
        else:
            draw.rectangle([content_margin, content_top,
                              self.width - content_margin, content_top + content_h], fill=panel_bg)

        # Bottom status bar
        draw = ImageDraw.Draw(img)  # redraw after paste
        draw.rectangle([0, self.height - 36, self.width, self.height], fill=panel_bg)
        draw.text((16, self.height - 28), "● LIVE", fill=(40, 201, 64), font=font_sm)

        img.save(str(output_path), "PNG")
        return output_path
