import asyncio
import os
import sys
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.loader import ConfigLoader
from services.visual_service import VisualService
from utils.models import VisualMarker
from dotenv import load_dotenv

async def test_scrolling():
    print("Testing 6-image scrolling screenshot capture...")
    load_dotenv()
    cfg = ConfigLoader().load()
    service = VisualService(cfg)
    
    # Create a dummy marker pointing to a tall webpage
    marker = VisualMarker(
        marker_type="screenshot",
        url="https://en.wikipedia.org/wiki/Artificial_intelligence",
        section_id="test_scroll"
    )
    
    class DummyCtx:
        pass
        
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright not installed.")
        return
        
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": cfg.canvas_width, "height": cfg.canvas_height}
        )
        ctx.set_default_timeout(20000)
        
        print("Navigating to Wikipedia and capturing 6 scrolling images...")
        assets = await service._screenshots(ctx, marker, section_id="test_scroll", stem="preview")
        
        await browser.close()
        
    print(f"\nSuccess! Captured {len(assets)} images:")
    for a in assets:
        print(f" - {a.file_path}")

if __name__ == "__main__":
    asyncio.run(test_scrolling())
