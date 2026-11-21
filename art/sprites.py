"""Single gloves on a transparent background, for the game page: rock, paper and scissors, for the player and for the AI.

Run:  blender -b -P art/sprites.py -- web/public/gloves
Makes: human-rock.png, human-paper.png, human-scissors.png, ai-rock.png, ai-paper.png, ai-scissors.png
The game page moves these pictures itself (swing, squash, stretch), so no clip has to be rendered per throw.
The player's glove points right, the AI's glove points left, both lit as in the loop.
"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glove as G

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
SIZE = 640            # pixels, square
SPAN = 3.3            # hand units shown across the picture
G.VOXEL = 0.010; G.SMOOTH_ITERS = 32

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for who, side in (("human", -1), ("ai", 1)):
        for pose in ("rock", "paper", "scissors"):
            sc = G.setup(res=(SIZE, SIZE), samples=64, cam=(0, -16.6, 0.0), look_at=(0, 0, 0))
            sc.render.film_transparent = True
            sc.render.image_settings.color_mode = "RGBA"
            sc.camera.data.type = "ORTHO"; sc.camera.data.ortho_scale = SPAN
            M = G.mats()
            G.glove(who, pose, M, "white" if side < 0 else "blue", loc=(side * 0.17, 0, -0.12), rot=(0, -side * 84, 0), mirror=side > 0)
            sc.render.filepath = os.path.join(OUT, f"{who}-{pose}.png")
            bpy.ops.render.render(write_still=True)
            print("sprite", who, pose, flush=True)
