import asyncio
from pathlib import Path

# Need to ensure the python path covers the visual_engine
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from visual_engine.html_renderer import HTMLTemplateRenderer

async def test():
    renderer = HTMLTemplateRenderer()
    
    # We need a dummy image path
    dummy_img = Path("temp_dummy_test.jpg")
    if not dummy_img.exists():
        # Create a quick dummy image
        from PIL import Image
        img = Image.new("RGB", (1280, 800), color=(80, 50, 120))
        img.save(dummy_img)

    test_templates = [
        ("browser_zoom", "style1_grid"),
        ("cyber_glitch", "style2_particles"),
        ("neon_pulse", "style0_mesh"),
        ("glass_float", "style3_crt")
    ]
    
    for template_name, style_name in test_templates:
        out_path = Path(f"preview_{style_name}_{template_name}.mp4")
        print(f"Recording {template_name} to {out_path} (3 seconds)...")
        await renderer.render_template(
            template_name=template_name,
            title=f"Testing {style_name}",
            url="https://docs.ai-automation.com/setup",
            image_path=dummy_img,
            bg_hex="#0F111A",
            accent_hex="#FF6B35",
            output_path=out_path,
            duration=3.0
        )
        print(f"Success! Saved video to {out_path.absolute()}")
    
    # Cleanup dummy image
    if dummy_img.exists():
        dummy_img.unlink()

if __name__ == "__main__":
    asyncio.run(test())
