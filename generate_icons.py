"""Run this once to generate the PNG icons needed for the PWA / iOS home screen."""
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "--quiet"])
    from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(OUT, exist_ok=True)

def make_icon(size):
    img = Image.new("RGB", (size, size), color="#1a1a24")
    draw = ImageDraw.Draw(img)

    # Draw a simple upward chart line
    pad = size * 0.18
    points = [
        (pad,          size * 0.70),
        (size * 0.35,  size * 0.55),
        (size * 0.55,  size * 0.65),
        (size - pad,   size * 0.28),
    ]
    draw.line(points, fill="#30d878", width=max(3, size // 32))

    # Draw a small dot at the end
    dot = size // 20
    ex, ey = points[-1]
    draw.ellipse([ex - dot, ey - dot, ex + dot, ey + dot], fill="#30d878")

    # Dollar sign in top-left corner area
    try:
        font_size = max(10, size // 6)
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    draw.text((pad * 0.8, pad * 0.6), "$", fill="#ffffff", font=font)

    return img

for sz in (192, 512):
    path = os.path.join(OUT, f"icon-{sz}.png")
    make_icon(sz).save(path)
    print(f"Created {path}")

print("Icons generated successfully.")
