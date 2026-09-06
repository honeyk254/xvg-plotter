"""Generate app icon assets from a PIL-drawn master (SPEC §11).

Writes icon.png / icon.ico / icon.icns into src/xvg_plotter/assets/.
Pillow ships with matplotlib, so no extra dependency.
"""
from pathlib import Path

from PIL import Image, ImageDraw

BASE = 512
SIZES = [16, 24, 32, 48, 64, 128, 256, 512]

OUT = Path(__file__).resolve().parents[1] / "src" / "xvg_plotter" / "assets"

img = Image.new("RGBA", (BASE, BASE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([16, 16, 496, 496], radius=96, fill=(26, 42, 74, 255))
d.line([(112, 116), (112, 384), (400, 384)], fill=(226, 234, 248, 255),
       width=20, joint="curve")
pts = [(146, 322), (196, 252), (244, 284), (294, 182), (342, 216), (392, 140)]
d.line(pts, fill=(96, 220, 160, 255), width=26, joint="curve")
for x, y in pts:
    d.ellipse([x - 17, y - 17, x + 17, y + 17], fill=(96, 220, 160, 255))

OUT.mkdir(parents=True, exist_ok=True)
img.save(OUT / "icon.png")
img.save(OUT / "icon.ico", sizes=[(s, s) for s in SIZES])
img.save(OUT / "icon.icns", sizes=[(s, s) for s in (16, 32, 64, 128, 256, 512)])
print("wrote", OUT / "icon.png", OUT / "icon.ico", OUT / "icon.icns")
