"""
Manim Renderer Engine
"""
import asyncio
import logging
import textwrap
from pathlib import Path
import tempfile
from .abstract_renderer import BaseRenderer

logger = logging.getLogger(__name__)

class ManimRenderer(BaseRenderer):
    """
    Renders clean, highly technical animations using the Manim math/diagramming engine.
    Works by dynamically generating a temporary python script containing a Manim `Scene`
    and executing it via subprocess.
    """
    
    def __init__(self, width: int = 1920, height: int = 1080):
        super().__init__(width, height)
        # Determine manim quality flag based on height
        if height >= 2160:
            self.quality_flag = "-qk"
        elif height >= 1440:
            self.quality_flag = "-qh"
        elif height >= 1080:
            self.quality_flag = "-qh"
        elif height >= 720:
            self.quality_flag = "-qm"
        else:
            self.quality_flag = "-ql"

    async def render(self, asset, output_path: Path, duration: float, **kwargs) -> Path:
        """
        Dynamically constructs a Manim Scene script, runs the `manim` CLI,
        and moves the output file to `output_path`.
        """
        title = getattr(asset, "description", "") or "Visualization"
        
        # In a real scenario, you'd branch based on marker metadata to pick different diagram types.
        # Here we use a sleek text reveal and chart animation as a beautiful default.
        bg_hex = kwargs.get("bg_hex", "#0F1117")
        accent_hex = kwargs.get("accent_hex", "#4A9EFF")
        
        script_code = self._generate_manim_script(title, duration, bg_hex, accent_hex)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            script_file = tmpdir_path / "scene.py"
            script_file.write_text(script_code)
            
            # Run Manim
            # manim -q<quality> -o <output_name> <script.py> DynamicScene
            logger.info(f"[Manim] Rendering scene for '{title}' (duration: {duration}s)")
            cmd = [
                "manim", 
                self.quality_flag,
                "--format=mp4",
                "-o", "out",
                "--media_dir", str(tmpdir_path / "media"),
                str(script_file), 
                "DynamicScene"
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.error(f"[Manim] Failed to render scene. Stderr: {stderr.decode()}")
                raise RuntimeError("Manim subprocess failed.")
                
            # Locate the generated file. Manim outputs to media/videos/scene/1080p60/out.mp4
            # Rather than guess the exact resolution folder, just find it.
            video_files = list((tmpdir_path / "media").rglob("*.mp4"))
            if not video_files:
                raise RuntimeError(f"[Manim] No output video found in {tmpdir_path}/media")
                
            # Move the rendered file to the target output path
            import shutil
            shutil.move(str(video_files[0]), str(output_path))
            logger.info(f"[Manim] Successfully rendered to {output_path}")
            
        return output_path
        
    def _generate_manim_script(self, title: str, duration: float, bg_hex: str, accent_hex: str) -> str:
        """
        Generates the Python code for a Manim Scene.
        """
        # We wrap the text if it's too long
        title_escaped = title.replace('"', '\\"')
        
        return textwrap.dedent(f'''
        from manim import *

        # Set background colour globally
        config.background_color = "{bg_hex}"

        class DynamicScene(Scene):
            def construct(self):
                # We want to stretch animations to approximately hit the target duration
                target_duration = {duration}
                
                # Title
                title_text = Text("{title_escaped}", font="sans-serif", weight=BOLD, font_size=48)
                title_text.set_color("{accent_hex}")
                title_text.move_to(UP * 2)

                # Simple data/diagram placeholder: A growing bar chart or mathematical curve
                axes = Axes(
                    x_range=[0, 10, 1],
                    y_range=[0, 10, 2],
                    axis_config={{"color": WHITE}},
                )
                
                # Subtle grid background
                grid = NumberPlane(
                    x_range=[-10, 10, 1],
                    y_range=[-10, 10, 1],
                    background_line_style={{
                        "stroke_color": TEAL,
                        "stroke_width": 1,
                        "stroke_opacity": 0.2
                    }}
                )

                curve = axes.plot(lambda x: 0.1 * x**2, color="{accent_hex}")
                area = axes.get_area(curve, color="{accent_hex}", opacity=0.3)

                VGroup(axes, curve, area).scale(0.8).move_to(DOWN * 0.5)

                # Animation Sequence
                self.play(FadeIn(grid), run_time=1.0)
                
                self.play(Write(title_text), run_time=min(2.0, target_duration * 0.3))
                
                # Draw the axes then the curve
                self.play(Create(axes), run_time=min(1.0, target_duration * 0.2))
                self.play(Create(curve), FadeIn(area), run_time=min(2.0, target_duration * 0.3))
                
                # Hold the rest of the duration
                remaining_time = max(0.5, target_duration - (1.0 + min(2.0, target_duration * 0.3) + min(1.0, target_duration * 0.2) + min(2.0, target_duration * 0.3)))
                self.wait(remaining_time)
                
                # Gentle fade out
                self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        ''')
