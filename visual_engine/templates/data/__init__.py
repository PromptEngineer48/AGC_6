"""
Data & Stats Templates (12–14)
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
from .base import BaseTemplate


class CounterTicker(BaseTemplate):
    """Template 12: Large stat number with label and context."""
    name = "counter_ticker"
    category = "data"

    def render_frame(self, output_path: Path, stat_value: str = "0",
                     stat_label: str = "Metric", context: str = "",
                     title: str = "", **kwargs) -> Path:
        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        font_huge = self.get_font(200)
        font_lg = self.get_font(64)
        font_md = self.get_font(44, bold=False)
        font_sm = self.get_font(32, bold=False)

        # Background number ghost
        ghost_col = tuple(int(c * 0.08) for c in accent)
        draw.text((60, self.height // 2 - 120), "000", fill=ghost_col, font=font_huge)

        # Accent divider line
        draw.rectangle([80, self.height // 2 - 130, 80 + 6, self.height // 2 + 130], fill=accent)

        # Stat value (big)
        draw.text((120, self.height // 2 - 110), stat_value, fill=accent, font=font_huge)

        # Label
        draw.text((120, self.height // 2 + 110), stat_label.upper(), fill="white", font=font_lg)

        # Context text
        if context:
            draw.text((120, self.height // 2 + 180), context[:80], fill=(160, 160, 160), font=font_sm)

        # Title top
        if title:
            draw.text((80, 60), title[:80], fill=(180, 180, 180), font=font_md)

        # Corner accent
        draw.rectangle([self.width - 8, 0, self.width, self.height], fill=accent)

        img.save(str(output_path), "PNG")
        return output_path


class BarRace(BaseTemplate):
    """Template 13: Horizontal bar chart with animated fill feel."""
    name = "bar_race"
    category = "data"

    def render_frame(self, output_path: Path, data: list[dict] = None,
                     title: str = "Comparison", **kwargs) -> Path:
        if data is None:
            data = [
                {"label": "Item A", "value": 85},
                {"label": "Item B", "value": 65},
                {"label": "Item C", "value": 45},
                {"label": "Item D", "value": 30},
            ]

        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        font_lg = self.get_font(56)
        font_md = self.get_font(38)
        font_sm = self.get_font(30, bold=False)

        # Title
        draw.text((80, 60), title, fill="white", font=font_lg)
        draw.rectangle([80, 130, 80 + 100, 136], fill=accent)

        # Bars
        max_val = max(d.get("value", 0) for d in data) or 100
        bar_area_w = self.width - 400
        bar_start_x = 320
        bar_y_start = 200
        bar_h = 70
        bar_gap = 30

        accent_colours = [accent, (accent[0] // 2, accent[1], accent[2]),
                           (accent[0], accent[1] // 2, accent[2]),
                           (accent[0], accent[1], accent[2] // 2)]

        for i, item in enumerate(data[:8]):
            by = bar_y_start + i * (bar_h + bar_gap)
            bar_w = int(bar_area_w * item.get("value", 0) / max_val)
            col = accent_colours[i % len(accent_colours)]

            # Background track
            draw.rectangle([bar_start_x, by, bar_start_x + bar_area_w, by + bar_h],
                            fill=(30, 32, 40))

            # Value bar with gradient feel (lighter end)
            draw.rectangle([bar_start_x, by, bar_start_x + bar_w, by + bar_h], fill=col)
            # Highlight stripe on top of bar
            draw.rectangle([bar_start_x, by, bar_start_x + bar_w, by + 12],
                            fill=tuple(min(255, c + 60) for c in col))

            # Label
            draw.text((80, by + bar_h // 2 - 18), item.get("label", "")[:15], fill="white", font=font_md)

            # Value label at end of bar
            val_str = str(item.get("value", 0))
            draw.text((bar_start_x + bar_w + 12, by + bar_h // 2 - 18), val_str, fill=col, font=font_md)

        img.save(str(output_path), "PNG")
        return output_path


class ProgressRing(BaseTemplate):
    """Template 14: Circular progress indicators."""
    name = "progress_ring"
    category = "data"

    def render_frame(self, output_path: Path, metrics: list[dict] = None,
                     title: str = "", **kwargs) -> Path:
        if metrics is None:
            metrics = [
                {"label": "Performance", "value": 87, "unit": "%"},
                {"label": "Adoption", "value": 64, "unit": "%"},
                {"label": "Growth", "value": 92, "unit": "%"},
            ]

        bg = self.hex_to_rgb(self.bg_hex)
        accent = self.hex_to_rgb(self.accent_hex)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)

        font_lg = self.get_font(56)
        font_md = self.get_font(72)
        font_sm = self.get_font(36, bold=False)

        # Title
        if title:
            draw.text((80, 60), title, fill="white", font=font_lg)

        # Draw rings
        ring_r = 160
        ring_w = 24
        n = min(len(metrics), 4)
        spacing = self.width // (n + 1)

        accent_variants = [accent,
                            (min(255, accent[0] + 60), accent[1] // 2, accent[2]),
                            (accent[0] // 2, min(255, accent[1] + 60), accent[2]),
                            (accent[0], accent[1] // 2, min(255, accent[2] + 60))]

        for i, m in enumerate(metrics[:n]):
            cx = spacing * (i + 1)
            cy = self.height // 2 + 30

            col = accent_variants[i % len(accent_variants)]
            pct = max(0, min(100, m.get("value", 0))) / 100

            import math
            start_angle = -90
            end_angle = -90 + 360 * pct

            # Background ring
            draw.arc([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
                      0, 360, fill=(40, 42, 50), width=ring_w)

            # Progress arc
            if pct > 0:
                draw.arc([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
                          start_angle, end_angle, fill=col, width=ring_w)

            # Centre value
            val_str = f"{m.get('value', 0)}{m.get('unit', '%')}"
            bbox = draw.textbbox((0, 0), val_str, font=font_md)
            draw.text((cx - (bbox[2] - bbox[0]) // 2, cy - (bbox[3] - bbox[1]) // 2),
                       val_str, fill="white", font=font_md)

            # Label below
            label = m.get("label", "")
            bbox2 = draw.textbbox((0, 0), label, font=font_sm)
            draw.text((cx - (bbox2[2] - bbox2[0]) // 2, cy + ring_r + 20),
                       label, fill=(180, 180, 180), font=font_sm)

        img.save(str(output_path), "PNG")
        return output_path
