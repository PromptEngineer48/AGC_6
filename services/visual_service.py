"""
Visual Service (v3 — Visual Engine with 20 templates + motion + atmosphere + SFX)
"""
from __future__ import annotations
import sys as _sys
import os as _os
_this_file = _os.path.abspath(__file__)
_project_root = _os.path.dirname(_os.path.dirname(_this_file))
if _project_root not in _sys.path:
    _sys.path.insert(0, _project_root)
_self_dir = _os.path.dirname(_this_file)
if _self_dir not in _sys.path:
    _sys.path.insert(0, _self_dir)

import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Optional

from config.loader import RuntimeConfig
from utils.models import ScriptSection, VideoScript, VisualAsset, VisualMarker

logger = logging.getLogger(__name__)


class VisualService:
    def __init__(self, cfg: RuntimeConfig):
        self.cfg = cfg
        self.screenshot_dir = Path(cfg.temp_dir) / "screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.url_counts = {}

    async def collect_visuals(self, script: VideoScript, stem: str = "") -> list[VisualAsset]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("playwright not installed: pip install playwright && playwright install chromium")

        assets: list[VisualAsset] = []
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
            ctx = await browser.new_context(
                viewport={"width": self.cfg.canvas_width, "height": self.cfg.canvas_height}
            )
            ctx.set_default_timeout(20_000)
            for section in script.sections:
                assets.extend(await self._process_section(ctx, section, stem))
            await browser.close()

        logger.info(f"[Visual] {len(assets)} assets collected")
        return assets

    async def _process_section(self, ctx, section: ScriptSection, stem: str) -> list[VisualAsset]:
        assets = [await self._title_card(section, stem)]
        for marker in section.visual_markers:
            if marker.marker_type == "screenshot" and marker.url:
                a = await self._screenshot(ctx, marker, section.section_id, stem)
                if a:
                    assets.append(a)
        return assets

    async def _screenshot(self, ctx, marker: VisualMarker, section_id: str, stem: str = "") -> Optional[VisualAsset]:
        url = marker.url
        count = self.url_counts.get(url, 0)
        self.url_counts[url] = count + 1
        cache_key = hashlib.md5(url.encode()).hexdigest()
        pfx = f"{stem}_" if stem else ""
        out = self.screenshot_dir / f"{pfx}ss_{section_id}_{cache_key}_{count}.png"
        if out.exists():
            return VisualAsset(section_id=section_id, asset_type="screenshot", file_path=out, url=url)
        try:
            page = await ctx.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            await asyncio.sleep(1.5)
            
            found_target = False
            if marker.focus_text:
                try:
                    # Attempt to find the specific text on the page
                    loc = page.get_by_text(marker.focus_text, exact=False).first
                    if await loc.count() > 0:
                        # Scroll it into view
                        await loc.scroll_into_view_if_needed()
                        
                        # Calculate its bounding box to attempt to center it in the viewport
                        box = await loc.bounding_box()
                        if box:
                            # Scroll up slightly to center the element
                            offset = - (self.cfg.canvas_height / 2) + (box['height'] / 2)
                            await page.evaluate(f"window.scrollBy(0, {offset})")
                        
                        logger.info(f"[Visual] Found exact text target '{marker.focus_text}' at {url}")
                        found_target = True
                        await asyncio.sleep(1.0)
                except Exception as e:
                    logger.debug(f"[Visual] Failed to find text '{marker.focus_text}': {e}")
            
            # Fallback to standard blind scroll if text targeting didn't work
            if not found_target and count > 0:
                await page.evaluate(f"window.scrollBy(0, window.innerHeight * 0.8 * {count})")
                await asyncio.sleep(1.0)
                
            await page.screenshot(path=str(out), full_page=False, type="png")
            await page.close()
            return VisualAsset(section_id=section_id, asset_type="screenshot", file_path=out, url=url)
        except Exception as exc:
            logger.warning(f"[Visual] Screenshot failed {url}: {exc}")
            try:
                await page.close()
            except Exception:
                pass
            return None

    async def _title_card(self, section: ScriptSection, stem: str = "") -> VisualAsset:
        pfx = f"{stem}_" if stem else ""
        out = self.screenshot_dir / f"{pfx}title_{section.section_id}.png"
        if not out.exists():
            style = self.cfg.video_style
            accent_colours = style.get("accent_colours", ["#4A9EFF", "#FF6B35", "#00C896"])
            section_types = ["intro", "main", "demo", "deep_dive", "comparison", "conclusion"]
            idx = section_types.index(section.section_type) if section.section_type in section_types else 0
            accent = accent_colours[idx % len(accent_colours)]
            bg = style.get("background_colour", "#0F1117")
            try:
                _make_title_card_pil(out, section.title, section.section_type,
                                     (self.cfg.canvas_width, self.cfg.canvas_height),
                                     bg_hex=bg, accent_hex=accent)
            except Exception as exc:
                logger.warning(f"[Visual] PIL title card failed: {exc}, using ffmpeg fallback")
                _ffmpeg_placeholder(out, bg, self.cfg.canvas_width, self.cfg.canvas_height)

        asset = VisualAsset(
            section_id=section.section_id,
            asset_type="title_card",
            file_path=out,
            description=section.title,
        )
        asset.section_type = section.section_type
        return asset


def _hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _make_title_card_pil(path, title, section_type, size, bg_hex, accent_hex):
    from PIL import Image, ImageDraw, ImageFont
    w, h = size
    bg = _hex_to_rgb(bg_hex)
    accent = _hex_to_rgb(accent_hex)
    img = Image.new("RGB", (w, h), color=bg)
    draw = ImageDraw.Draw(img)
    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except OSError:
        font_lg = ImageFont.load_default()
        font_sm = ImageFont.load_default()
    draw.rectangle([0, 0, 12, h], fill=accent)
    draw.text((80, h // 2 - 60), section_type.replace("_", " ").upper(), fill=accent, font=font_sm)
    _draw_wrapped(draw, title, font_lg, (80, h // 2 - 10), w - 160, "white")
    img.save(str(path), "PNG")


def _draw_wrapped(draw, text, font, pos, max_width, colour):
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
        y += 90


def _ffmpeg_placeholder(path, bg_hex, w, h):
    import subprocess
    colour = bg_hex.lstrip("#")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x{colour}:s={w}x{h}",
                    "-vframes", "1", str(path)], capture_output=True)
