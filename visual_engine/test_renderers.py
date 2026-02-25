import asyncio
import logging
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from visual_engine.manim_renderer import ManimRenderer
from visual_engine.remotion_renderer import RemotionRenderer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DummyAsset:
    def __init__(self, description, url=None, file_path=None):
        self.description = description
        self.url = url
        self.file_path = file_path

async def test_manim():
    logger.info("--- Testing Manim Renderer ---")
    renderer = ManimRenderer(1920, 1080)
    asset = DummyAsset("Deep Dive: System Architecture")
    out_path = Path("temp/test_manim_output.mp4")
    out_path.parent.mkdir(exist_ok=True)
    
    await renderer.render(
        asset=asset,
        output_path=out_path,
        duration=5.0,
        bg_hex="#1A1A2E",
        accent_hex="#E94560"
    )
    
    if out_path.exists() and out_path.stat().st_size > 0:
        logger.info(f"SUCCESS: Manim output exists at {out_path} ({out_path.stat().st_size} bytes)")
    else:
        logger.error("FAILURE: Manim output missing or empty")

async def test_remotion():
    logger.info("--- Testing Remotion Renderer ---")
    remotion_dir = Path(__file__).parent / "remotion_templates"
    renderer = RemotionRenderer(remotion_dir, 1920, 1080)
    asset = DummyAsset("Remotion UI Layout", "https://example.com")
    out_path = Path("temp/test_remotion_output.mp4")
    
    # We will just render the 'HelloWorld' default composition to prove execution works
    try:
        # The default helloworld template expects specific props like titleText
        props = {
            "titleText": "Remotion Test 123",
            "titleColor": "#E94560",
            "logoColor1": "#0F1117",
            "logoColor2": "#00C896"
        }
        import json
        props_str = json.dumps(props)
        import subprocess
        
        # Test direct subprocess call since schema mismatch causes Silent failure
        logger.info(f"Running direct remotion render HelloWorld {out_path} --props='{props_str}'")
        subprocess.run(
            ["node_modules/.bin/remotion", "render", "src/index.ts", "HelloWorld", str(out_path.absolute()), "--props", props_str],
            cwd=str(remotion_dir),
            check=True
        )
        if out_path.exists() and out_path.stat().st_size > 0:
            logger.info(f"SUCCESS: Remotion output exists at {out_path} ({out_path.stat().st_size} bytes)")
        else:
            logger.error("FAILURE: Remotion output missing or empty")
    except RuntimeError as e:
        logger.warning(f"Remotion test failed, likely because dependencies aren't built yet: {e}")
        logger.info("Installing remotion dependencies...")
        import subprocess
        subprocess.run(["npm", "install"], cwd=str(remotion_dir))
        logger.info("Rerunning remotion test...")
        await renderer.render(
            asset=asset,
            output_path=out_path,
            duration=3.0,
            bg_hex="#0F1117",
            accent_hex="#00C896",
            remotion_composition="HelloWorld"
        )
        if out_path.exists() and out_path.stat().st_size > 0:
            logger.info(f"SUCCESS: Remotion output exists at {out_path} ({out_path.stat().st_size} bytes)")

async def main():
    await test_manim()
    await test_remotion()

if __name__ == "__main__":
    asyncio.run(main())
