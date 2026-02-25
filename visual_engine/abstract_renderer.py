"""
Base Renderer Interface for Visual Engine
"""
from abc import ABC, abstractmethod
from pathlib import Path

class BaseRenderer(ABC):
    """
    Abstract base class for all programmatic video renderers (HTML/Playwright, Manim, Remotion).
    """
    
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height

    @abstractmethod
    async def render(self, asset, output_path: Path, duration: float, **kwargs) -> Path:
        """
        Renders a video clip based on the asset data and saves it to output_path.
        
        Args:
            asset: The VisualAsset containing data (title, url, etc.)
            output_path: Where the final .mp4 should be saved
            duration: Target duration of the clip in seconds
            **kwargs: Additional engine-specific arguments (e.g., bg_hex, accent_hex)
            
        Returns:
            The Path to the generated .mp4 file.
        """
        pass
