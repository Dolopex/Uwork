"""Genera íconos PNG para el PWA usando Pillow."""
import os
import math
from PIL import Image, ImageDraw

SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'static', 'icons')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def make_icon(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rectangle background (indigo gradient simulation via solid color)
    radius = size // 5
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=(79, 70, 229, 255))

    # Draw "U" letter
    font_size = int(size * 0.62)
    # Manual "U" shape using arcs and rectangles
    lw = max(2, size // 14)  # line width
    pad = int(size * 0.18)
    
    # Left vertical bar
    draw.rectangle([pad, pad, pad + lw, size - pad - int(size*0.15)], fill=(255, 255, 255, 255))
    # Right vertical bar
    draw.rectangle([size - pad - lw, pad, size - pad, size - pad - int(size*0.15)], fill=(255, 255, 255, 255))
    # Bottom arc (semicircle)
    arc_top = size - pad - int(size * 0.38)
    arc_bottom = size - pad
    arc_left = pad
    arc_right = size - pad
    draw.arc([arc_left, arc_top, arc_right, arc_bottom], start=0, end=180, fill=(255, 255, 255, 255), width=lw)

    return img

for size in SIZES:
    icon = make_icon(size)
    path = os.path.join(OUTPUT_DIR, f'icon-{size}.png')
    icon.save(path, 'PNG')
    print(f'  Generado: icon-{size}.png')

print('Íconos PWA generados en static/icons/')
