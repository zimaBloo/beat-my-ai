"""Rock-paper-scissors loop, version 2: timed and posed like a very old cartoon.

Run:  blender -b -P art/animate.py -- art     (FRAMES="0,5,20" renders only those frames; about 9 minutes for all)
Then: python3 art/assemble.py art media       (adds the overlay layers and builds the animated WebP)

Borrowed from the rubber-hose era, as technique only:
- 12 drawings a second ("on twos"), so every pose is held long enough to read;
- each glove swings on a long arc from an elbow off screen, not straight up and down;
- squash and stretch: it stretches while moving fast and squashes when it stops;
- anticipation before the throw, overshoot after it, and big reactions: the winner jumps, the loser deflates.

There is no rig. Every frame the hand is rebuilt from joint angles and placed by a few numbers.
"""
import bpy, json, math, os, sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glove as G

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
FPS = 12
ROUNDS = [("paper", "scissors"), ("rock", "scissors")]     # (human, AI): the AI wins the first, the human the second
G.VOXEL = 0.011; G.SMOOTH_ITERS = 28
FIST = G.POSES["rock"]

# one key per frame: (swing in degrees, stretch along the arm, pose weight 0=fist 1=thrown, slide along the arm)
SHAKE = [(12, 1.12, 0, 0), (30, 1.14, 0, 0), (38, 0.94, 0, 0), (35, 1.00, 0, 0), (10, 1.20, 0, 0), (-8, 0.78, 0, 0)]
THROW = [(-5, 0.90, 0, 0), (16, 1.06, 0, -0.20), (3, 1.30, 0.75, 0.18), (-3, 0.88, 1.12, 0.10), (0, 1.05, 1.0, 0.03)]
HOLD = [(0, 1.0, 1, 0), (1, 1.0, 1, 0), (0, 1.0, 1, 0)]
JUMP = [(-3, 0.84, 1, 0.04), (17, 1.20, 1, 0.10), (25, 0.98, 1, 0.12), (22, 1.02, 1, 0.12), (6, 1.16, 1, 0.08), (-5, 0.84, 1, 0.04)]
WIN = JUMP + JUMP + [(0, 1.06, 1, 0.02), (0, 1.0, 1, 0)]
LOSE = [(0, 1.0, 1, 0), (7, 1.10, 1, -0.04), (-5, 0.92, 1, -0.10), (-10, 0.84, 1, -0.15), (-13, 0.80, 1, -0.18)] + \
       [(-13 + (1.5 if i % 2 else -1.5), 0.80, 1, -0.18) for i in range(9)]
TIE = [(0, 1.0, 1, 0), (6, 1.08, 1, 0), (0, 0.94, 1, 0), (0, 1.0, 1, 0)] * 3 + [(0, 1.0, 1, 0)] * 2
CLOSE = [(-4, 0.95, 0.7, -0.05), (2, 1.06, 0.3, 0), (0, 0.97, 0, 0), (0, 1.0, 0, 0)]
PER_ROUND = 3 * len(SHAKE) + len(THROW) + len(HOLD) + len(WIN) + len(CLOSE)
REACT_START = 3 * len(SHAKE) + len(THROW) + len(HOLD)


def beats(a, b):
    return (a, b) in (("rock", "scissors"), ("scissors", "paper"), ("paper", "rock"))


def keys_for(mine, theirs):
    react = WIN if beats(mine, theirs) else LOSE if beats(theirs, mine) else TIE
    return SHAKE * 3 + THROW + HOLD + react + CLOSE


def blend(pose_name, w):
    P = G.POSES[pose_name]
    lerp = lambda a, b: a + (b - a) * w
    return {"bend": [tuple(lerp(f, p) for f, p in zip(fb, pb)) for fb, pb in zip(FIST["bend"], P["bend"])],
            "spread": [lerp(f, p) for f, p in zip(FIST["spread"], P["spread"])],
            "thumb": max(0.0, min(1.0, lerp(1.0, 0.0 if P["thumb"] == "open" else 1.0)))}


def clear(objs):
    for ob in objs:
        data = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if data is not None and data.users == 0:
            bpy.data.meshes.remove(data)


if __name__ == "__main__":
    frames_dir = os.path.join(OUT, "frames"); os.makedirs(frames_dir, exist_ok=True)
    total = PER_ROUND * len(ROUNDS)
    only = [int(x) for x in os.environ["FRAMES"].split(",")] if os.environ.get("FRAMES") else range(total)
    sc = G.setup(res=(1200, 540), samples=40, cam=(0, -16.6, 0.60), look_at=(0, 0, 0.36)); M = G.mats()
    meta = {"fps": FPS, "frames": total, "per_round": PER_ROUND, "react_start": REACT_START, "react_len": len(WIN), "items": {}}
    live = []
    for fr in only:
        human, ai = ROUNDS[fr // PER_ROUND]
        k = fr % PER_ROUND
        clear(live); live = []
        info = {"round": fr // PER_ROUND, "k": k,
                "winner": "human" if beats(human, ai) else "ai" if beats(ai, human) else None}
        for who, mine, theirs, side in (("human", human, ai, -1), ("ai", ai, human, 1)):
            swing, stretch, w, slide = keys_for(mine, theirs)[k]
            th = math.radians(swing)
            elbow = Vector((side * 3.35, 0, -0.15))                      # off screen; the glove swings around it
            reach = 1.85 + slide
            loc = elbow + Vector((-side * math.cos(th), 0, math.sin(th))) * reach
            root = G.glove(who, blend(mine, w), M, "white" if side < 0 else "blue",
                           loc=tuple(loc), rot=(0, -side * (84 - swing), 0), mirror=side > 0)
            squash = 1 / math.sqrt(stretch)                              # keep the volume: thinner when longer
            root.scale = (root.scale[0] * squash, squash, stretch)
            live += [root] + list(root.children)
            bpy.context.view_layer.update()
            uv = world_to_camera_view(sc, sc.camera, loc + Vector((-side * 0.25, 0, 0.1)))
            info[who] = [round(uv.x * 1200), round((1 - uv.y) * 540)]
        meta["items"][str(fr)] = info
        sc.render.filepath = os.path.join(frames_dir, f"f_{fr:04d}.png")
        bpy.ops.render.render(write_still=True)
        print("frame", fr, "of", total, flush=True)
    if not os.environ.get("FRAMES"):
        json.dump(meta, open(os.path.join(OUT, "frames", "meta.json"), "w"))
