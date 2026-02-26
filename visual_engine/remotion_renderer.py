"""
Remotion Renderer Engine
"""
import asyncio
import json
import logging
from pathlib import Path
from .abstract_renderer import BaseRenderer

logger = logging.getLogger(__name__)

class RemotionRenderer(BaseRenderer):
    """
    Renders beautiful, 60fps UI mockups and web animations using React (Remotion).
    Communicates with a local Node.js Remotion project via subprocess `npx remotion render`.
    """
    
    def __init__(self, remotion_dir: Path, width: int = 1920, height: int = 1080):
        super().__init__(width, height)
        self.remotion_dir = remotion_dir
        
    async def render(self, asset, output_path: Path, duration: float, **kwargs) -> Path:
        """
        Calls `npx remotion render` inside the remotion project directory.
        Passes down dynamic props (title, url, screenshot) via JSON.
        """
        # Remotion compositions need to know their exact frame count
        fps = 30
        frames = max(1, int(duration * fps))
        
        # Build the dynamic props to pass to React
        props = {
            "title": getattr(asset, "description", "") or "UI Showcase",
            "url": getattr(asset, "url", ""),
            "durationInFrames": frames,
            "fps": fps,
            "width": self.width,
            "height": self.height,
            "bgHex": kwargs.get("bg_hex", "#0F1117"),
            "accentHex": kwargs.get("accent_hex", "#4A9EFF")
        }
        
        # If the asset has an attached image (from the playwright step), pass the path
        # Note: Remotion can load local files via `file://` URIs if configured, or we can pass base64
        if getattr(asset, "file_path", None):
            props["imagePath"] = f"file://{asset.file_path}"
            
        composition_name = kwargs.get("remotion_composition", "DynamicBrowserMockup")
            
        props_json = json.dumps(props)
        
        # Command: npx remotion render src/index.ts <CompositionName> <output.mp4> --props='{...}'
        logger.info(f"[Remotion] Rendering composition '{composition_name}' (frames: {frames})")
        
        cmd = [
            "npx", "remotion", "render",
            "src/index.ts", 
            composition_name,
            str(output_path),
            "--props", props_json,
            "--gl=angle" # Better compatibility in headless environments
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.remotion_dir)
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            logger.error(f"[Remotion] Failed to render composition. Stderr: {stderr.decode()}")
            raise RuntimeError("Remotion subprocess failed.")
            
        logger.info(f"[Remotion] Successfully rendered to {output_path}")
        return output_path
