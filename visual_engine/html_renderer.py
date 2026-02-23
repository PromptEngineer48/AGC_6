from __future__ import annotations
import asyncio
import base64
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)

class HTMLTemplateRenderer:
    """
    Renders beautiful HTML/CSS templates into 1920x1080 static PNG frames using Playwright.
    Replaces the legacy PIL-based drawing to allow for modern web styling (glassmorphism, gradients, CSS drop shadows).
    """
    
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        # Ensure Playwright is available and optionally keep a browser instance alive
        try:
            from playwright.async_api import async_playwright
            self._async_playwright = async_playwright
        except ImportError:
            raise ImportError("playwright is not installed. Run: pip install playwright && playwright install chromium")
            
    def _image_to_base64(self, image_path: Path) -> str:
        """Reads an image file and returns a base64 data URI string."""
        if not image_path or not Path(image_path).exists():
            return ""
        
        ext = image_path.suffix.lower()
        mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
        
        with open(image_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")
            
        return f"data:{mime_type};base64,{b64_data}"
        
    async def render_html_to_video(self, html_content: str, output_path: Path, duration: float):
        """
        Uses Playwright to render the HTML, waits for `duration` seconds to record the CSS animations,
        then transcodes the resulting WebM to the output MP4 path.
        """
        import tempfile
        import subprocess

        async with self._async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            with tempfile.TemporaryDirectory() as tmpdir:
                context = await browser.new_context(
                    viewport={"width": self.width, "height": self.height},
                    device_scale_factor=1,
                    record_video_dir=tmpdir,
                    record_video_size={"width": self.width, "height": self.height}
                )
                page = await context.new_page()
                
                # Load the HTML
                await page.set_content(html_content, wait_until="networkidle")
                
                # Wait for the CSS animations to play out while recording
                await asyncio.sleep(duration)
                
                # Closing context finalizes the webm file
                await context.close()
                await browser.close()
                
                webm_files = list(Path(tmpdir).glob("*.webm"))
                if not webm_files:
                    raise RuntimeError("Playwright failed to record video.")
                
                webm_file = webm_files[0]
                
                # Convert to mp4
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(webm_file),
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    str(output_path)
                ]
                proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    logger.error(f"[HTMLRenderer] FFmpeg conversion failed: {stderr.decode()}")
                    raise RuntimeError("Failed to transcode Playwright webm to mp4")
            
        return output_path
        
    async def render_template(self, template_name: str, title: str, url: str, image_path: Path, bg_hex: str, accent_hex: str, output_path: Path, duration: float) -> Path:
        """
        Loads the specified modern HTML/CSS template and records the animation.
        """
        template_file = Path(__file__).parent / "html_templates" / f"{template_name}.html"
        if not template_file.exists():
            # Fallback
            template_file = Path(__file__).parent / "html_templates" / "browser_mockup.html"
            
        html = template_file.read_text()
        
        # Load screenshot
        b64_image = self._image_to_base64(image_path) if image_path else ""
        
        # Simple string replacement for templating
        html = html.replace("{{BG_HEX}}", str(bg_hex or ""))
        html = html.replace("{{ACCENT_HEX}}", str(accent_hex or ""))
        html = html.replace("{{URL}}", str(url or ""))
        html = html.replace("{{TITLE}}", str(title or ""))
        html = html.replace("{{IMAGE_DATA}}", str(b64_image or ""))
        
        # Render Video
        return await self.render_html_to_video(html, output_path, duration)
