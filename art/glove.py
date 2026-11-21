"""Gloved hand for the rock-paper-scissors profile, version 2. Built entirely by script.

Run:  blender -b -P art/glove.py -- <out_dir>        (GLOVE_FAST=1 for a quick preview)
Makes: poses.png (rock, paper, scissors) and versus.png (white glove vs blue AI glove).

How it is built
- A real hand skeleton: four fingers with three joints each and a thumb, posed by joint angles.
- Every bone is a row of overlapping spheres. All of it is then fused into ONE surface (voxel remesh)
  and smoothed, so fingers grow out of the palm without seams, with knuckles and creases.
- A separate flared cuff, and three stitched lines that follow the back of the hand.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
FAST = os.environ.get("GLOVE_FAST") == "1"
VOXEL = 0.015 if FAST else 0.008
SMOOTH_ITERS = 8 if FAST else 45

# ---------- the hand, in its own units (palm about 1 high). Back of the hand faces -Y, palm faces +Y ----------
#          name      base x, z     length  radius
FINGERS = [("index",  -0.365, 0.405, 0.70, 0.127),
           ("middle", -0.122, 0.450, 0.77, 0.131),
           ("ring",    0.122, 0.415, 0.72, 0.124),
           ("pinky",   0.355, 0.325, 0.57, 0.111)]
PHALANX = (0.46, 0.30, 0.24)          # share of the finger length per bone
# joint bends in degrees (knuckle, middle joint, end joint) and sideways spread per finger
CURLED = (88, 100, 58)
POSES = {
    "paper":    {"bend": [(7, 6, 4), (5, 5, 3), (7, 6, 4), (10, 8, 5)],   "spread": [-15, -5, 5, 16], "thumb": "open"},
    "rock":     {"bend": [CURLED, CURLED, CURLED, CURLED],                "spread": [-1.5, -0.5, 0.5, 1.5], "thumb": "fold"},
    "scissors": {"bend": [(4, 4, 3), (4, 4, 3), CURLED, CURLED],          "spread": [-14, 9, 0.5, 1.5], "thumb": "fold"},
}
PALM_SIDE = Vector((0, 1, 0))


def sphere(bm, c, r, s=(1, 1, 1)):
    m = Matrix.Translation(c) @ Matrix.Diagonal((r * s[0], r * s[1], r * s[2], 1))
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0, matrix=m)


def bone(bm, p0, p1, r0, r1, waist=0.035):
    """A bone as overlapping spheres from p0 to p1; slightly slimmer in the middle than at the joints."""
    L = (p1 - p0).length
    n = max(4, int(L / (0.10 * min(r0, r1))))
    for i in range(n + 1):
        u = i / n
        r = (r0 + (r1 - r0) * u) * (1 - waist * math.sin(math.pi * u))
        sphere(bm, p0.lerp(p1, u), r)


def finger_joints(base, length, bends, spread_deg):
    s = math.radians(spread_deg)
    d = Vector((math.sin(s), 0, math.cos(s)))
    pts = [base.copy()]; c = 0.0
    for share, b in zip(PHALANX, bends):
        c += math.radians(b)
        direction = math.cos(c) * d + math.sin(c) * PALM_SIDE
        pts.append(pts[-1] + direction * length * share)
    return pts


def chain(start, direction, normal, lengths, bends):
    d = direction.normalized(); n = (normal - normal.dot(d) * d).normalized()
    pts = [start.copy()]; c = 0.0
    for L, b in zip(lengths, bends):
        c += math.radians(b)
        pts.append(pts[-1] + (math.cos(c) * d + math.sin(c) * n) * L)
    return pts


def build_hand(name, pose, mat):
    P = POSES[pose] if isinstance(pose, str) else pose      # a pose name, or a dict of joint angles (used by animate.py)
    bm = bmesh.new()
    # palm: a rounded slab, wider at the knuckles than at the wrist
    ret = bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=1.0)
    for v in ret["verts"]:
        x, y, z = v.co
        k = (abs(x) ** 3.2 + abs(y) ** 3.2 + abs(z) ** 3.2) ** (1 / 3.2)
        x, y, z = x / k, y / k, z / k
        taper = 0.86 + 0.14 * (z + 1) / 2
        v.co = Vector((x * 0.50 * taper, y * 0.165, z * 0.50 - 0.04))
    sphere(bm, Vector((0.30, 0.07, -0.26)), 0.18, (1, 0.8, 1.25))      # heel of the hand, little-finger side
    for i in range(4):                                                   # wrist: a short oval column that ends inside the cuff
        sphere(bm, Vector((0, 0.0, -0.44 - 0.03 * i)), 0.31, (1, 0.50, 1))
    # fingers
    prev = None
    for (fname, bx, bz, length, r), bends, spread in zip(FINGERS, P["bend"], P["spread"]):
        base = Vector((bx, 0.0, bz))
        j = finger_joints(base, length, bends, spread)
        # curled neighbours share one knuckle ridge, so a fist shows soft scallops instead of four separate balls
        curl = max(0.0, min(1.0, (bends[0] - 30) / 50))
        if prev is not None and min(curl, prev[2]) > 0.15:
            c = min(curl, prev[2])
            lift = Vector((0, 0.0, -0.02))
            bone(bm, prev[0] + lift, base + lift, prev[1] * (0.55 + 0.42 * c), r * (0.55 + 0.42 * c), waist=0.0)
        prev = (base, r, curl)
        # straight, gently tapering bones: no beads at the joints, creases appear only where a finger bends
        root_dir = Vector((math.sin(math.radians(spread)), 0, math.cos(math.radians(spread))))
        bone(bm, j[0] - root_dir * 0.12, j[0], r * 1.0, r * 1.03, waist=0.0)      # the finger's root, sunk into the palm
        bone(bm, j[0], j[1], r * 1.03, r * 0.98, waist=0.0)
        bone(bm, j[1], j[2], r * 0.98, r * 0.93, waist=0.0)
        bone(bm, j[2], j[3], r * 0.93, r * 0.86, waist=0.0)
        sphere(bm, j[3], r * 0.86)
    # thumb: a bone inside the palm edge, then two free bones
    # thumb fold: 0 = open, sticking out; 1 = folded across the front of the curled fingers
    f = {"open": 0.0, "fold": 1.0}.get(P["thumb"], P["thumb"])
    mix = lambda a, b: Vector(a).lerp(Vector(b), f)
    t = chain(mix((-0.34, 0.03, -0.30), (-0.34, 0.05, -0.30)), mix((-0.72, 0.06, 0.69), (-0.50, 0.50, 0.70)),
              mix((-0.5, 0.3, -0.5), (0.90, 0.30, -0.30)), (0.34, 0.27, 0.22), tuple(mix((0, 12, 8), (8, 52, 48))))
    bone(bm, t[0], t[1], 0.185, 0.150, waist=0.0)
    bone(bm, t[1], t[2], 0.146, 0.136)
    bone(bm, t[2], t[3], 0.136, 0.124)
    sphere(bm, t[3], 0.124)
    # flatten the wrist spheres front to back
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    rm = ob.modifiers.new("Fuse", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = VOXEL; rm.adaptivity = 0.0; rm.use_smooth_shade = True
    sm = ob.modifiers.new("Smooth", "SMOOTH"); sm.factor = 0.6; sm.iterations = SMOOTH_ITERS
    ob.data.materials.append(mat)
    return ob


def sweep(name, pts, radius, mat, sides=8):
    """A thin tube along a list of points (used for the stitched lines)."""
    verts, faces = [], []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.cross(Vector((1, 0, 0))).normalized(); b = t.cross(a)
        r = radius * math.sin(math.pi * (0.12 + 0.76 * i / (len(pts) - 1))) ** 0.6
        for j in range(sides):
            ang = 2 * math.pi * j / sides
            verts.append(p + (math.cos(ang) * a + math.sin(ang) * b) * r)
    for i in range(len(pts) - 1):
        for j in range(sides):
            a0 = i * sides + j; a1 = i * sides + (j + 1) % sides
            faces.append((a0, a1, a1 + sides, a0 + sides))
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat)
    return ob


def cuff(name, mat, inside_mat):
    """A flared sleeve end with a rolled hem."""
    rings = [(-0.54, 0.375, 0.245), (-0.64, 0.385, 0.255), (-0.76, 0.415, 0.275), (-0.88, 0.455, 0.305)]
    sides = 40; verts, faces = [], []
    for z, rx, ry in rings:
        for j in range(sides):
            a = 2 * math.pi * j / sides
            verts.append((rx * math.cos(a), ry * math.sin(a), z))
    for i in range(len(rings) - 1):
        for j in range(sides):
            a0 = i * sides + j; a1 = i * sides + (j + 1) % sides
            faces.append((a0, a1, a1 + sides, a0 + sides))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat)
    so = ob.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.05; so.offset = 1.0
    ss = ob.modifiers.new("Sub", "SUBSURF"); ss.levels = 2; ss.render_levels = 2
    parts = [ob]
    for z, rx, ry, minor in ((-0.885, 0.485, 0.335, 0.058), (-0.545, 0.405, 0.272, 0.052)):   # hem roll, and a soft band at the top
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=minor / rx, major_segments=64, minor_segments=14, location=(0, 0, z))
        tor = bpy.context.object; tor.scale = (rx, ry, rx); tor.data.materials.append(mat)
        for poly in tor.data.polygons:
            poly.use_smooth = True
        parts.append(tor)
    bpy.ops.mesh.primitive_circle_add(vertices=40, radius=1.0, fill_type="NGON", location=(0, 0, -0.84))
    disk = bpy.context.object; disk.scale = (0.43, 0.285, 1); disk.data.materials.append(inside_mat); parts.append(disk)
    return parts


def stitches(hand, mat):
    """Three stitched lines on the back of the hand, laid onto the fused surface."""
    bpy.context.view_layer.update()
    ev = hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
    out = []
    for lx, z0, z1 in ((-0.22, -0.16, 0.14), (0.0, -0.18, 0.17), (0.22, -0.16, 0.14)):
        pts = []
        for i in range(15):
            z = z0 + (z1 - z0) * i / 14
            x = lx * (0.80 + 0.35 * (z - z0) / (z1 - z0))        # lines fan out towards the knuckles
            hit, loc, nor, _ = ev.ray_cast(Vector((x, -3, z)), Vector((0, 1, 0)))
            if hit:
                pts.append(loc + nor * 0.003)
        if len(pts) > 3:
            out.append(sweep("stitch", pts, 0.013, mat))
    return out


def glove(name, pose, M, kind, loc=(0, 0, 0), rot=(0, 0, 0), mirror=False):
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    hand = build_hand(name + "_hand", pose, M[kind])
    parts = [hand] + cuff(name + "_cuff", M[kind + "_cuff"], M["inside"]) + stitches(hand, M[kind + "_line"])
    for ob in parts:
        ob.parent = root
    root.location = loc; root.rotation_euler = [math.radians(a) for a in rot]
    root.scale = (-1 if mirror else 1, 1, 1)
    return root


def material(name, color, rough=0.55, emit=None, emit_strength=0.0, cloth=True, sheen=0.35):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    for key in ("Sheen Weight", "Sheen"):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = sheen; break
    if emit and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    if cloth:   # a very fine woven texture so it reads as fabric, not plastic
        noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 260
        bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.10; bump.inputs["Distance"].default_value = 0.01
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def mats():
    return {
        "white": material("white", (0.82, 0.84, 0.89)),
        "white_cuff": material("white_cuff", (0.74, 0.77, 0.85)),
        "white_line": material("white_line", (0.30, 0.37, 0.55), cloth=False),
        "blue": material("blue", (0.035, 0.15, 0.72), rough=0.42, emit=(0.05, 0.22, 1.0), emit_strength=0.22),
        "blue_cuff": material("blue_cuff", (0.02, 0.07, 0.36), rough=0.45, emit=(0.05, 0.22, 1.0), emit_strength=0.08),
        "blue_line": material("blue_line", (0.01, 0.04, 0.22), cloth=False),
        "inside": material("inside", (0.01, 0.015, 0.03), cloth=False, sheen=0.0),
    }


def light(loc, energy, color=(1, 1, 1), size=4.0, target=(0, 0, 0)):
    data = bpy.data.lights.new("area", "AREA"); data.energy = energy; data.color = color; data.size = size
    ob = bpy.data.objects.new("area", data); bpy.context.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def setup(res=(1600, 720), samples=96, cam=(0, -14.6, 0.45), look_at=(0, 0, 0.14)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
    sc.cycles.samples = 16 if FAST else samples; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 50 if FAST else 100
    sc.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("World"); sc.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.0015, 0.004, 0.012, 1)
    cd = bpy.data.cameras.new("Cam"); cd.lens = 85
    c = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(c); sc.camera = c
    c.location = cam; c.rotation_euler = (Vector(look_at) - Vector(cam)).to_track_quat("-Z", "Y").to_euler()
    light((-4.5, -6.0, 4.5), 520, (1.0, 0.97, 0.94), 6.0)       # soft key from the upper left
    light((5.5, 3.5, 3.0), 2400, (0.25, 0.48, 1.0), 4.0)        # blue rim from behind
    light((4.0, -6.5, -2.0), 150, (0.6, 0.72, 1.0), 7.0)        # gentle fill from below right
    return sc


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


if __name__ == "__main__":
    setup(); M = mats()
    for i, pose in enumerate(["rock", "paper", "scissors"]):
        glove("g_" + pose, pose, M, "white", loc=((i - 1) * 1.95, 0, 0), rot=(-6, 0, 14))
    render(OUT + "/poses.png")

    setup(); M = mats()
    glove("human", "paper", M, "white", loc=(-1.50, 0, 0.14), rot=(0, 80, 0))
    glove("ai", "scissors", M, "blue", loc=(1.50, 0, 0.14), rot=(0, -80, 0), mirror=True)
    render(OUT + "/versus.png")
