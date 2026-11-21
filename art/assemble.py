"""Builds the looping animation from the rendered frames, with overlay layers drawn on top.

Run:  python3 art/assemble.py art media      (takes seconds; no 3D re-render needed)
      first argument: the folder that holds frames/, second: where to write the result
Makes: rps-loop.webp (animated, for the GitHub profile) and rps-loop-poster.png (a still for visitors with motion off).

MODULAR: every overlay is one small function in LAYERS below. To add an element (a score, a caption, confetti),
write a function `layer(size, info) -> transparent image or None` and add it to LAYERS. To switch one off,
remove it from the list. `info` says, for this frame: which round, how far into the round, who wins,
and where each glove is on screen.
"""
import glob, json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFont

d = sys.argv[1] if len(sys.argv) > 1 else "."
out_dir = sys.argv[2] if len(sys.argv) > 2 else d
meta = json.load(open(os.path.join(d, "frames", "meta.json")))
FPS = meta["fps"]; R0 = meta["react_start"]; RL = meta["react_len"]
SS = 3                                                      # draw at 3x and scale down, for smooth edges
COL = {"human": (238, 242, 250), "ai": (150, 190, 255)}
PILL = (9, 20, 42, 235)                                     # dark navy behind the labels
FONT = "/Library/Fonts/SchibstedGrotesk-Bold.ttf"           # SIL Open Font Licence


def canvas(size):
    im = Image.new("RGBA", (size[0] * SS, size[1] * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def star(draw, cx, cy, r, rot, fill):
    pts = []
    for i in range(8):
        a = rot + i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.36
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    draw.polygon(pts, fill=fill)


# ---------- layer: burst around the winner ----------
def winner_burst(size, info):
    """Rays and stars popping around the winning glove, redrawn every second drawing so they boil."""
    r = info["k"] - R0
    who = info["winner"]
    if not who or not (0 <= r < RL):
        return None
    W, H = size
    layer, dr = canvas(size)
    cx, cy = info[who][0] * SS, info[who][1] * SS
    boil = (r // 2) % 2
    rng = random.Random(info["round"] * 10 + boil)
    grow = min(1.0, 0.55 + 0.25 * r)
    fade = 1.0 if r < RL - 3 else (RL - r) / 3
    col = COL[who] + (int(235 * max(0.0, fade)),)
    n = 14
    for i in range(n):
        a = 2 * math.pi * (i + 0.5 * boil) / n + rng.uniform(-0.05, 0.05)
        if abs(math.cos(a)) > 0.93 and (math.cos(a) > 0) == (who == "human"):
            continue                                        # keep the gap between the two gloves clear
        inner = (198 + rng.uniform(-8, 8)) * SS * grow
        length = (66 if i % 2 == boil else 34) * SS * grow * (1 + rng.uniform(-0.15, 0.15))
        wdt = 7.5 * SS
        ax, ay = math.cos(a), math.sin(a); px, py = -ay, ax
        x0, y0 = cx + ax * inner, cy + ay * inner * 0.86
        x1, y1 = cx + ax * (inner + length), cy + ay * (inner + length) * 0.86
        dr.polygon([(x0 + px * wdt, y0 + py * wdt), (x0 - px * wdt, y0 - py * wdt), (x1, y1)], fill=col)
    for i in range(4):
        a = rng.uniform(0, 2 * math.pi); rad = rng.uniform(235, 285) * SS * grow
        sx, sy = cx + math.cos(a) * rad, cy + math.sin(a) * rad * 0.8
        if 0.04 * W * SS < sx < 0.96 * W * SS and 0.06 * H * SS < sy < 0.94 * H * SS:
            star(dr, sx, sy, rng.uniform(13, 22) * SS * grow, rng.uniform(0, 1), col)
    return layer.resize(size, Image.LANCZOS)


# ---------- layer: who is who ----------
def side_labels(size, info):
    """'YOU' under the white glove's side and 'AI' under the blue one, as two fixed labels in the bottom corners."""
    W, H = size
    layer, dr = canvas(size)
    font = ImageFont.truetype(FONT, 34 * SS)
    pad_x, pad_y, h, gap, icon = 20 * SS, 9 * SS, 54 * SS, 12 * SS, 22 * SS
    y0 = (H - 30) * SS - h
    for who, text in (("human", "YOU"), ("ai", "AI")):
        tw = dr.textlength(text, font=font)
        w = pad_x * 2 + icon + gap + tw
        x0 = 30 * SS if who == "human" else W * SS - 30 * SS - w
        dr.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=h / 2, fill=PILL)
        cx, cy = x0 + pad_x + icon / 2, y0 + h / 2
        if who == "human":        # an arrow pointing up at your glove
            dr.polygon([(cx, cy - icon * 0.55), (cx + icon * 0.55, cy + icon * 0.05), (cx + icon * 0.2, cy + icon * 0.05),
                        (cx + icon * 0.2, cy + icon * 0.55), (cx - icon * 0.2, cy + icon * 0.55), (cx - icon * 0.2, cy + icon * 0.05),
                        (cx - icon * 0.55, cy + icon * 0.05)], fill=COL[who])
        else:                     # a spark, the usual sign for AI
            star(dr, cx, cy, icon * 0.62, math.pi / 2, COL[who])
        dr.text((x0 + pad_x + icon + gap, y0 + h / 2), text, font=font, fill=COL[who], anchor="lm")
    return layer.resize(size, Image.LANCZOS)


LAYERS = [winner_burst, side_labels]        # drawn in this order; remove a name to switch that layer off


def compose(path):
    fr = int(os.path.basename(path)[2:6]); info = meta["items"][str(fr)]
    im = Image.open(path).convert("RGBA")
    for layer in LAYERS:
        over = layer(im.size, info)
        if over is not None:
            im = Image.alpha_composite(im, over)
    return im.convert("RGB")


if __name__ == "__main__":
    frames = [compose(f) for f in sorted(glob.glob(os.path.join(d, "frames", "f_*.png")))]
    out = os.path.join(out_dir, "rps-loop.webp")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=round(1000 / FPS), loop=0, quality=84, method=6)
    poster = os.path.join(out_dir, "rps-loop-poster.png")
    frames[R0 + 3].save(poster, optimize=True)
    print(len(frames), "frames,", len(LAYERS), "layers →", out, f"{os.path.getsize(out) / 1e6:.2f} MB;", poster)
