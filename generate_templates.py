import os
import random

TEMPLATES_DIR = "visual_engine/html_templates"
os.makedirs(TEMPLATES_DIR, exist_ok=True)

BACKGROUND_STYLES = [
    # 1. Animated Blob Mesh Gradient
    """
        .bg-glow {
            position: absolute; width: 100%; height: 100%; z-index: 1; overflow: hidden;
            background-color: {{BG_HEX}};
        }
        .blob1, .blob2 {
            position: absolute; border-radius: 50%; filter: blur(150px); opacity: 0.6;
            animation: orbit 15s infinite alternate ease-in-out;
        }
        .blob1 { width: 800px; height: 800px; background: {{ACCENT_HEX}}; top: -200px; left: -200px; }
        .blob2 { width: 600px; height: 600px; background: {{ACCENT_HEX}}; bottom: -100px; right: -100px; animation-delay: -5s; animation-duration: 20s; }
        @keyframes orbit { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(300px, 200px) scale(1.2); } }
    """,
    # 2. Retrowave Infinite Grid
    """
        .bg-glow {
            position: absolute; width: 100%; height: 100%; z-index: 1; overflow: hidden;
            background-color: {{BG_HEX}}; perspective: 1000px;
        }
        .grid {
            position: absolute; bottom: -50%; left: -50%; width: 200%; height: 150%;
            background-image: 
                linear-gradient(to right, {{ACCENT_HEX}}33 1px, transparent 1px),
                linear-gradient(to bottom, {{ACCENT_HEX}}33 1px, transparent 1px);
            background-size: 80px 80px;
            transform: rotateX(75deg);
            animation: gridScroll 10s linear infinite;
        }
        @keyframes gridScroll { from { transform: rotateX(75deg) translateY(0); } to { transform: rotateX(75deg) translateY(80px); } }
    """,
    # 3. Floating Particles / Bokeh
    """
        .bg-glow {
            position: absolute; width: 100%; height: 100%; z-index: 1; overflow: hidden;
            background-color: {{BG_HEX}};
        }
        .particle {
            position: absolute; border-radius: 50%; background: radial-gradient(circle, {{ACCENT_HEX}}aa 0%, transparent 70%);
            animation: floatUp 12s linear infinite;
        }
        .p1 { width: 300px; height: 300px; left: 10%; bottom: -300px; animation-duration: 15s; }
        .p2 { width: 500px; height: 500px; left: 60%; bottom: -500px; animation-delay: -4s; opacity: 0.5; }
        .p3 { width: 200px; height: 200px; left: 80%; bottom: -200px; animation-duration: 10s; animation-delay: -2s; }
        @keyframes floatUp { 0% { transform: translateY(0) scale(0.8); opacity: 0; } 50% { opacity: 0.8; } 100% { transform: translateY(-1500px) scale(1.2); opacity: 0; } }
    """,
    # 4. CRT Noise + Moving Spotlight
    """
        .bg-glow {
            position: absolute; width: 100%; height: 100%; z-index: 1; overflow: hidden;
            background-color: {{BG_HEX}};
        }
        .noise {
            position: absolute; inset: 0; opacity: 0.05;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
        }
        .spotlight {
            position: absolute; inset: 0;
            background: radial-gradient(circle at 10% 50%, {{ACCENT_HEX}}20 0%, transparent 40%);
            animation: sweep 10s infinite alternate ease-in-out;
        }
        @keyframes sweep { from { background-position: 0% 0%; } to { background-position: 800px 0; } }
    """
]

BACKGROUND_DOM = [
    '<div class="bg-glow"><div class="blob1"></div><div class="blob2"></div></div>',
    '<div class="bg-glow"><div class="grid"></div></div>',
    '<div class="bg-glow"><div class="particle p1"></div><div class="particle p2"></div><div class="particle p3"></div></div>',
    '<div class="bg-glow"><div class="noise"></div><div class="spotlight"></div></div>'
]

# Base template wrapper
def get_base(css, body_html, bg_index=0):
    bg_css = BACKGROUND_STYLES[bg_index]
    bg_dom = BACKGROUND_DOM[bg_index]
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            width: 1920px; height: 1080px; 
            background-color: {{{{BG_HEX}}}};
            display: flex; align-items: center; justify-content: center;
            font-family: 'Inter', sans-serif; overflow: hidden; position: relative;
        }}
        {bg_css}
        .container {{ position: relative; z-index: 10; }}
        .image-box {{ width: 100%; height: 100%; object-fit: cover; object-position: top; }}
        
        {css}
    </style>
</head>
<body>
    {bg_dom}
    {body_html}
</body>
</html>"""

templates_data = {
    # 1. Subtle Zoom Browser
    "browser_zoom.html": (
        """
        .browser {
            width: 1600px; height: 900px; background: #191B21; border-radius: 20px;
            box-shadow: 0 40px 100px -20px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.05);
            display: flex; flex-direction: column; overflow: hidden;
            animation: slowZoom 5s forwards linear;
        }
        .chrome { height: 60px; background: #2D2F37; display: flex; align-items: center; padding: 0 20px; }
        .dots { display: flex; gap: 8px; }
        .dot { width: 12px; height: 12px; border-radius: 50%; background: #555; }
        .dot:nth-child(1) { background: #FF5F56; } .dot:nth-child(2) { background: #FFBD2E; } .dot:nth-child(3) { background: #27C93F; }
        .content { flex-grow: 1; overflow: hidden; position: relative; }
        @keyframes slowZoom { from { transform: scale(0.95); } to { transform: scale(1.02); } }
        """,
        """<div class="container browser">
            <div class="chrome"><div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>
            <div class="content"><img src="{{IMAGE_DATA}}" class="image-box"></div>
        </div>"""
    ),
    # 2. Cinematic Pan
    "cinematic_pan.html": (
        """
        body { background: #000; }
        .bg-glow { display: none; }
        .pan-container {
            width: 1920px; height: 800px; overflow: hidden; position: relative;
            border-top: 2px solid {{ACCENT_HEX}}; border-bottom: 2px solid {{ACCENT_HEX}};
        }
        .image-box { width: 110%; height: 110%; animation: panLeft 5s alternate ease-in-out; }
        @keyframes panLeft { from { transform: translateX(0) scale(1.1); } to { transform: translateX(-5%) scale(1.1); } }
        """,
        """<div class="container pan-container"><img src="{{IMAGE_DATA}}" class="image-box"></div>"""
    ),
    # 3. 3D Floating Glass
    "glass_float.html": (
        """
        .glass {
            width: 1500px; height: 850px; background: rgba(255,255,255,0.03);
            backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1);
            border-radius: 30px; padding: 20px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            animation: float 6s ease-in-out infinite;
        }
        .img-wrap { width: 100%; height: 100%; border-radius: 15px; overflow: hidden; }
        @keyframes float { 0%, 100% { transform: translateY(0) rotateX(2deg); } 50% { transform: translateY(-20px) rotateX(-2deg); } }
        """,
        """<div class="container glass"><div class="img-wrap"><img src="{{IMAGE_DATA}}" class="image-box"></div></div>"""
    ),
    # 4. Polaroid Sway
    "polaroid_sway.html": (
        """
        .polaroid {
            width: 1200px; padding: 30px 30px 120px 30px; background: #fff;
            box-shadow: 0 30px 60px rgba(0,0,0,0.4); transform-origin: top center;
            animation: sway 5s ease-in-out infinite;
        }
        .img-wrap { width: 100%; height: 800px; background: #111; overflow: hidden; }
        .caption { color: #333; font-size: 36px; text-align: center; margin-top: 40px; font-weight: 600; font-family: 'Courier New', monospace; }
        @keyframes sway { 0%, 100% { transform: rotate(-3deg); } 50% { transform: rotate(3deg); } }
        """,
        """<div class="container polaroid">
            <div class="img-wrap"><img src="{{IMAGE_DATA}}" class="image-box"></div>
            <div class="caption">{{TITLE}}</div>
        </div>"""
    ),
    # 5. Neon Pulse Frame
    "neon_pulse.html": (
        """
        .neon-frame {
            width: 1600px; height: 900px; padding: 10px;
            background: #000; border-radius: 10px;
            box-shadow: 0 0 20px {{ACCENT_HEX}}, 0 0 50px {{ACCENT_HEX}};
            animation: pulse 2s infinite alternate;
        }
        .img-wrap { width: 100%; height: 100%; border-radius: 5px; overflow: hidden; }
        @keyframes pulse { from { box-shadow: 0 0 20px {{ACCENT_HEX}}, 0 0 40px {{ACCENT_HEX}}; } to { box-shadow: 0 0 40px {{ACCENT_HEX}}, 0 0 80px {{ACCENT_HEX}}; } }
        """,
        """<div class="container neon-frame"><div class="img-wrap"><img src="{{IMAGE_DATA}}" class="image-box"></div></div>"""
    ),
    # 6. Cyber Glitch
    "cyber_glitch.html": (
        """
        .cyber { width: 1600px; height: 900px; border: 4px solid {{ACCENT_HEX}}; position: relative; animation: glitchRotate 3s infinite; }
        .cyber::before { content: ''; position: absolute; top: -10px; left: -10px; right: -10px; bottom: -10px; border: 2px solid #0ff; z-index:-1; animation: glitch2 2s infinite reverse; }
        @keyframes glitchRotate { 0%, 100% { transform: skewX(0); } 10% { transform: skewX(2deg); } }
        @keyframes glitch2 { 0%, 100% { transform: translate(0); } 20% { transform: translate(-5px, 5px); } }
        """,
        """<div class="container cyber"><img src="{{IMAGE_DATA}}" class="image-box"></div>"""
    ),
    # 7. Slide In Left
    "slide_in.html": (
        """
        .slide { width: 1600px; height: 900px; border-radius: 20px; overflow: hidden; box-shadow: 30px 30px 80px rgba(0,0,0,0.5); animation: slideIn 1s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }
        @keyframes slideIn { from { transform: translateX(-1920px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        """,
        """<div class="container slide"><img src="{{IMAGE_DATA}}" class="image-box"></div>"""
    ),
    # 8. Scale Fade
    "scale_fade.html": (
        """
        .scale { width: 1700px; height: 950px; border-radius: 15px; overflow: hidden; animation: scaleFade 0.8s ease-out forwards; }
        @keyframes scaleFade { from { transform: scale(1.2); opacity: 0; filter: blur(20px); } to { transform: scale(1); opacity: 1; filter: blur(0); } }
        """,
        """<div class="container scale"><img src="{{IMAGE_DATA}}" class="image-box"></div>"""
    ),
    # 9. Phone Portrait Scroll
    "phone_portrait.html": (
        """
        .phone { width: 500px; height: 950px; background: #111; border-radius: 50px; border: 12px solid #333; box-shadow: 0 30px 60px rgba(0,0,0,0.6); overflow: hidden; position: relative; animation: floatPhone 4s ease-in-out infinite; }
        .notch { width: 150px; height: 30px; background: #333; position: absolute; top: 0; left: 50%; transform: translateX(-50%); border-radius: 0 0 15px 15px; }
        .img-wrap { width: 100%; height: 120%; /* Taller to allow scroll */ animation: scrollY 6s alternate ease-in-out; }
        @keyframes floatPhone { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
        @keyframes scrollY { from { transform: translateY(0); } to { transform: translateY(-15%); } }
        """,
        """<div class="container phone"><div class="notch"></div><div class="img-wrap"><img src="{{IMAGE_DATA}}" class="image-box"></div></div>"""
    ),
    # 10. Dashboard Split
    "dash_split.html": (
        """
        .dash { display: flex; width: 1700px; height: 900px; background: rgba(30,30,35,0.9); border-radius: 20px; overflow: hidden; box-shadow: 0 20px 80px rgba(0,0,0,0.6); }
        .sidebar { width: 300px; background: rgba(20,20,25,0.9); border-right: 1px solid rgba(255,255,255,0.05); padding: 40px; }
        .main { flex-grow: 1; padding: 40px; animation: gentleZoom 4s forwards; transform-origin: left center;}
        .bubble { width: 40px; height: 40px; border-radius: 50%; background: {{ACCENT_HEX}}; margin-bottom: 30px; }
        .line { height: 12px; border-radius: 6px; background: rgba(255,255,255,0.1); margin-bottom: 20px; }
        .img-wrap { width: 100%; height: 100%; border-radius: 10px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); }
        @keyframes gentleZoom { from { transform: scale(0.98); } to { transform: scale(1.02); } }
        """,
        """<div class="container dash">
            <div class="sidebar"><div class="bubble"></div><div class="line"></div><div class="line" style="width:70%"></div></div>
            <div class="main"><div class="img-wrap"><img src="{{IMAGE_DATA}}" class="image-box"></div></div>
        </div>"""
    ),
    # 11. Retro CRT Scanner
    "crt_scan.html": (
        """
        .crt { width: 1600px; height: 900px; overflow: hidden; position: relative; border-radius: 40px; border: 20px solid #111; box-shadow: inset 0 0 100px rgba(0,0,0,0.9); }
        .scanline { position: absolute; width: 100%; height: 10px; background: rgba(255,255,255,0.1); opacity: 0.5; animation: scan 3s linear infinite; }
        @keyframes scan { 0% { top: -10%; } 100% { top: 110%; } }
        .image-box { filter: contrast(1.2) sepia(0.2) hue-rotate(-10deg); }
        """,
        """<div class="container crt"><div class="scanline"></div><img src="{{IMAGE_DATA}}" class="image-box"></div>"""
    ),
    # 12. Minimal Outline
    "minimal_outline.html": (
        """
        body { background: #EAEAEA; }
        .bg-glow { display: none; }
        .outline { width: 1500px; height: 850px; background: #fff; padding: 20px; border: 2px solid #ccc; box-shadow: 20px 20px 0px {{ACCENT_HEX}}; animation: pop 0.5s ease-out forwards; }
        .img-wrap { width: 100%; height: 100%; }
        @keyframes pop { 0% { transform: scale(0.9) rotate(-2deg); } 100% { transform: scale(1) rotate(0deg); } }
        """,
        """<div class="container outline"><div class="img-wrap"><img src="{{IMAGE_DATA}}" class="image-box"></div></div>"""
    ),
    # 13. Tilt Shift Blur
    "tilt_shift.html": (
        """
        .blur { width: 1920px; height: 1080px; position: relative; animation: panUp 5s alternate ease-in-out; }
        .overlay { position: absolute; inset: 0; background: linear-gradient(to bottom, {{BG_HEX}} 0%, transparent 20%, transparent 80%, {{BG_HEX}} 100%); z-index: 2; pointer-events: none; }
        @keyframes panUp { from { transform: scale(1.1) translateY(2%); } to { transform: scale(1.1) translateY(-2%); } }
        """,
        """<div class="container blur"><div class="overlay"></div><img src="{{IMAGE_DATA}}" class="image-box"></div>"""
    ),
    # 14. Circle Reveal
    "circle_reveal.html": (
        """
        .circle { width: 1600px; height: 900px; border-radius: 20px; overflow: hidden; clip-path: circle(0% at 50% 50%); animation: expand 1s cubic-bezier(0.1, 0.8, 0.1, 1) forwards; }
        @keyframes expand { to { clip-path: circle(150% at 50% 50%); } }
        """,
        """<div class="container circle"><img src="{{IMAGE_DATA}}" class="image-box"></div>"""
    ),
    # 15. Mac Window Bounce
    "mac_bounce.html": (
        """
        .mac { width: 1500px; height: 850px; background: #222; border-radius: 12px; box-shadow: 0 50px 100px rgba(0,0,0,0.5); overflow: hidden; animation: bounceWindow 1.5s cubic-bezier(0.2, 0.8, 0.2, 1); }
        .bar { height: 40px; background: linear-gradient(to bottom, #444, #333); border-bottom: 1px solid #111; display: flex; align-items: center; padding-left: 15px; }
        .dot { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; background: #666; }
        .img-wrap { height: calc(100% - 40px); }
        @keyframes bounceWindow { 0% { transform: translateY(1000px); } 60% { transform: translateY(-30px); } 80% { transform: translateY(10px); } 100% { transform: translateY(0); } }
        """,
        """<div class="container mac"><div class="bar"><div class="dot" style="background:#FF5F56;"></div><div class="dot" style="background:#FFBD2E;"></div><div class="dot" style="background:#27C93F;"></div></div><div class="img-wrap"><img src="{{IMAGE_DATA}}" class="image-box"></div></div>"""
    ),
    # 16. Perspective 3D
    "perspective_3d.html": (
        """
        .persp { width: 1400px; height: 800px; border-radius: 20px; overflow: hidden; box-shadow: -30px 30px 60px rgba(0,0,0,0.6); animation: turn3D 5s infinite alternate; }
        @keyframes turn3D { from { transform: perspective(2000px) rotateY(15deg) rotateX(5deg); } to { transform: perspective(2000px) rotateY(-15deg) rotateX(-5deg); } }
        """,
        """<div class="container persp"><img src="{{IMAGE_DATA}}" class="image-box"></div>"""
    ),
    # 17. Cinematic Wide Pan Right
    "wide_pan.html": (
        """
        body { background: #000; }
        .wide { width: 1920px; height: 700px; border-top: 1px solid #333; border-bottom: 1px solid #333; overflow: hidden; }
        .image-box { width: 120%; height: 120%; animation: panWide 6s linear forwards; }
        @keyframes panWide { from { transform: scale(1.1) translateX(-5%); } to { transform: scale(1.1) translateX(5%); } }
        """,
        """<div class="container wide"><img src="{{IMAGE_DATA}}" class="image-box"></div>"""
    ),
    # 18. Floating Screens
    "float_screens.html": (
        """
        .screens { display: flex; gap: 40px; }
        .screen { width: 700px; height: 800px; border-radius: 20px; overflow: hidden; box-shadow: 0 40px 80px rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.1); }
        .s1 { animation: upDown 4s ease-in-out infinite; }
        .s2 { animation: upDown 4s ease-in-out infinite 2s; transform: scale(0.9); opacity: 0.8; }
        @keyframes upDown { 0%, 100% { transform: translateY(-20px); } 50% { transform: translateY(20px); } }
        """,
        """<div class="container screens"><div class="screen s1"><img src="{{IMAGE_DATA}}" class="image-box"></div><div class="screen s2"><img src="{{IMAGE_DATA}}" class="image-box" style="filter: grayscale(1);"></div></div>"""
    ),
    # 19. Typing Terminal
    "terminal.html": (
        """
        .term { width: 1400px; height: 800px; background: rgba(10,15,20,0.95); border: 1px solid {{ACCENT_HEX}}; border-radius: 10px; padding: 40px; font-family: monospace; color: {{ACCENT_HEX}}; box-shadow: 0 0 50px rgba(0,255,100,0.1); }
        .header { font-size: 24px; margin-bottom: 20px; }
        .img-wrap { width: 100%; height: 650px; border: 1px solid rgba(255,255,255,0.1); opacity: 0; animation: fadeTerm 1s forwards 1s; }
        .cursor { display: inline-block; width: 12px; height: 24px; background: {{ACCENT_HEX}}; animation: blink 1s infinite; vertical-align: middle; }
        @keyframes fadeTerm { to { opacity: 1; } }
        @keyframes blink { 50% { opacity: 0; } }
        """,
        """<div class="container term"><div class="header">> loading {{TITLE}}...<span class="cursor"></span></div><div class="img-wrap"><img src="{{IMAGE_DATA}}" class="image-box"></div></div>"""
    ),
    # 20. Simple Drop in
    "drop_in.html": (
        """
        .drop { width: 1600px; height: 900px; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.3); animation: dropDown 0.8s cubic-bezier(0.3, 1.5, 0.4, 1) forwards; }
        @keyframes dropDown { from { transform: translateY(-1080px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
        """,
        """<div class="container drop"><img src="{{IMAGE_DATA}}" class="image-box"></div>"""
    )
}

def generate_all():
    print("Generating 20 HTML templates...")
    for name, (css, body) in templates_data.items():
        bg_index = random.randint(0, 3)
        content = get_base(css, body, bg_index)
        out_path = os.path.join(TEMPLATES_DIR, name)
        with open(out_path, "w") as f:
            f.write(content)
        print(f"Created {out_path} with background style {bg_index}")
        
    print(f"\\nAll 20 templates generated in {TEMPLATES_DIR}!")

if __name__ == "__main__":
    generate_all()
