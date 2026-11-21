"""Turns the rendered glove pictures into small WebP files for the game page.

Run:  python3 art/to_webp.py web/public/gloves web/src/gloves
"""
import glob, os, sys
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
for f in sorted(glob.glob(os.path.join(src, "*.png"))):
    out = os.path.join(dst, os.path.basename(f)[:-4] + ".webp")
    Image.open(f).convert("RGBA").save(out, "WEBP", quality=88, method=6)
    print(os.path.basename(out), round(os.path.getsize(out) / 1024), "KB")
