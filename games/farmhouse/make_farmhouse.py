"""
農家の家（夕方のジオラマ）を作る Blender スクリプト。

使い方（bpy を入れた Python で）:
    python make_farmhouse.py            # 作る → farmhouse.glb → 絵を出す
    python make_farmhouse.py --norender # 形だけ作って farmhouse.glb を出す

出力: assets/farmhouse.glb, farmhouse_raw.png, farmhouse.png(色づけ後), farmhouse_pixel.png(ドット絵風)
座標: メートル、Z が上、家の正面は -Y。カメラは (+X,-Y) 側から見る。納屋の戸は左(-X)、畑は右(+X)。
"""
import bpy, bmesh, math, sys, os
import numpy as np
from math import radians, sin, cos, atan2, sqrt
from mathutils import Matrix, Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")
os.makedirs(OUT, exist_ok=True)
NORENDER = "--norender" in sys.argv
SEED = 7
RES = (640, 360) if os.environ.get("FH_QUICK") else (1280, 720)
SAMPLES = 8 if os.environ.get("FH_QUICK") else 32
rng = np.random.default_rng(SEED)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
G = {}  # グループ名 → 部品のリスト

# ---------------------------------------------------------------- 材質
def mat(name, col, rough=0.9, metal=0.0, emit=None, bump=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    b = n["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1)
        b.inputs["Emission Strength"].default_value = emit[1]
    if bump:  # (ノイズの細かさ, 強さ)
        t = n.new("ShaderNodeTexNoise"); t.inputs["Scale"].default_value = bump[0]
        bn = n.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = bump[1]
        m.node_tree.links.new(t.outputs["Fac"], bn.inputs["Height"])
        m.node_tree.links.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m

M = dict(
    plaster=mat("Plaster", (.72, .64, .48), .9, bump=(12, .15)),
    beam=mat("Beam", (.10, .055, .03), .75, bump=(20, .25)),
    thatch=mat("Thatch", (.55, .25, .07), .95, bump=(30, .4)),
    thatchd=mat("ThatchDark", (.22, .09, .03), .95, bump=(30, .4)),
    ridge=mat("Ridge", (.06, .04, .03), .8),
    door=mat("DoorWood", (.24, .13, .06), .8, bump=(15, .3)),
    iron=mat("Iron", (.04, .04, .045), .55, metal=.8),
    stone=mat("Stone", (.30, .30, .28), .9, bump=(8, .5)),
    moss=mat("Moss", (.04, .12, .09), .95, bump=(25, .3)),
    teal=mat("Teal", (.03, .10, .10), .95, bump=(25, .3)),
    dirt=mat("Dirt", (.16, .10, .06), 1.0),
    leaf=mat("Leaf", (.05, .18, .04), .8),
    blade=mat("Blade", (.03, .10, .12), .8),
    tomato=mat("Tomato", (.6, .04, .02), .35),
    flower=mat("Flower", (.9, .35, .03), .6),
    water=mat("Water", (.02, .05, .07), .05),
    glass=mat("Glass", (.02, .03, .05), .1, emit=((1, .6, .3), .6)),
    inside=mat("Interior", (0, 0, 0), 1.0),
    endgrain=mat("EndGrain", (.35, .22, .10), .9),
    soil=mat("Soil", (.09, .05, .03), 1.0),
)

# ---------------------------------------------------------------- 部品の道具
def reg(o, grp, m):
    o.data.materials.append(M[m] if isinstance(m, str) else m)
    G.setdefault(grp, []).append(o)
    return o

def xf(loc, rot=(0, 0, 0), s=(1, 1, 1)):
    return (Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()
            @ Matrix.Diagonal((*s, 1)))

def box(loc, size, m, grp, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.matrix_world = xf(loc, rot, size)
    return reg(o, grp, m)

def box_m(Mx, c, size, m, grp):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.matrix_world = Mx @ Matrix.Translation(c) @ Matrix.Diagonal((*size, 1))
    return reg(o, grp, m)

def cyl(loc, r, h, m, grp, rot=(0, 0, 0), v=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=h)
    o = bpy.context.object
    o.matrix_world = xf(loc, rot)
    return reg(o, grp, m)

def cone(loc, r1, r2, h, m, grp, rot=(0, 0, 0), v=8):
    bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=r1, radius2=r2, depth=h)
    o = bpy.context.object
    o.matrix_world = xf(loc, rot)
    return reg(o, grp, m)

def ball(loc, r, m, grp, s=(1, 1, 1)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r)
    o = bpy.context.object
    o.matrix_world = xf(loc, (0, 0, 0), s)
    return reg(o, grp, m)

def poly(name, verts, faces, m, grp, Mx=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    if Mx is not None: o.matrix_world = Mx
    return reg(o, grp, m)

# ---------------------------------------------------------------- 地面（苔と土）
bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=40, size=44)
ground = bpy.context.object
bm = bmesh.new(); bm.from_mesh(ground.data)
for v in bm.verts: v.co.z += rng.uniform(-.06, .06)
bm.to_mesh(ground.data); bm.free()
ground.data.materials.append(M["moss"]); ground.data.materials.append(M["teal"])
for p in ground.data.polygons: p.material_index = int(rng.random() < .35)
G["Ground"] = [ground]
for pi, (x, y, r, sx) in enumerate([(-2, -3.6, 1.8, 1.6), (1.2, -3.6, 1.4, 1.8), (-4.2, -1.2, 1.2, 1.3),
                      (-6.5, -4.2, 1.5, 1.6), (6.5, -5, 1.6, 1.7), (-1, 5.5, 1.5, 1.6)]):
    cyl((x, y, .03 + pi * .004), r, .02, "dirt", "Ground", v=16).scale = (sx * r / r, 1, 1)

# ---------------------------------------------------------------- 家の本体
box((0, 1, .15), (8.3, 5.3, .3), "stone", "House")                       # 土台
box((0, 1, 1.5), (8, 5, 3), "plaster", "House")                          # 壁
box((-2.6, -1.52, 1.35), (2.2, .06, 2.1), "inside", "House")             # 戸口（真っ黒）
box((-2.6, 1.6, 1.0), (2.1, 2.0, 1.5), "inside", "House")

# 切妻（左右の三角壁）と梁
for sx in (-1, 1):
    x0 = sx * 4.0
    verts = [(x0 - .15, -1.5, 3), (x0 - .15, 3.5, 3), (x0 - .15, 1, 7.1),
             (x0 + .15, -1.5, 3), (x0 + .15, 3.5, 3), (x0 + .15, 1, 7.1)]
    poly("Gable", verts, [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)], "plaster", "House")
    xb = x0 + sx * .17
    box((xb, 1, 5.0), (.14, .2, 4.1), "beam", "House")                    # 大黒柱
    for sy in (-1, 1):
        box((xb, 1 + sy * 1.2, 4.0), (.14, .16, 2.9), "beam", "House", rot=(radians(-sy * 40), 0, 0))
    box((xb, 1, 3.0), (.14, 5.2, .2), "beam", "House")
    for yy in (-1.5, 3.5):
        box((xb, yy, 1.5), (.14, .2, 3), "beam", "House")
    box((xb, 1, 1.3), (.14, 5.2, .16), "beam", "House")

# 正面の梁
def front_beams():
    yb = -1.56
    for x in (-4, -3.7, -1.5, .5, 2.5, 4):
        box((x, yb, 1.5), (.2, .14, 3), "beam", "House")
    box((0, yb, 2.95), (8.2, .14, .2), "beam", "House")                   # 上の桁
    box((0, yb, 1.3), (8.2, .14, .16), "beam", "House")                   # 中の桁
    box((.7, yb, .4), (6.0, .14, .16), "beam", "House")                   # 下の桁
    box((-2.6, yb, 2.5), (2.4, .14, .2), "beam", "House")                 # 戸の上の梁
    for x in (-.5, 1.5, 3.2):
        box((x, yb, 1.9), (.96, .1, .86), "beam", "House")                # 窓枠
        box((x, yb - .03, 1.9), (.78, .04, .68), "glass", "House")        # 窓ガラス
        box((x, yb - .06, 1.9), (.05, .05, .68), "beam", "House")
        for (hx, dx, ang) in ((x - .4, 1, -70), (x + .4, -1, 70)):        # 開いた鎧戸
            d = radians(ang if dx == 1 else 180 - ang + 180)
            dirv = Vector((cos(radians(-70) if dx == 1 else radians(-110)),
                           sin(radians(-70) if dx == 1 else radians(-110)), 0))
            c = Vector((hx, yb - .05, 1.9)) + dirv * .21
            box(c, (.42, .05, .75), "door", "House", rot=(0, 0, radians(-70 if dx == 1 else 70)))
    for x in (-.5, 1.5):                                                  # 下段の小窓
        box((x + .5, yb, .85), (.5, .1, .4), "beam", "House")
        box((x + .5, yb - .03, .85), (.36, .04, .26), "glass", "House")
    for x in (-1.5, .5): pass
    box((-1.0, yb, .85), (.14, .14, .9), "beam", "House", rot=(0, radians(40), 0))
front_beams()

# 納屋の戸（開いた片扉）
hinge = Vector((-3.7, -1.62, 0)); ang = radians(-105)
dv = Vector((cos(ang), sin(ang), 0)); pv = Vector((-sin(ang), cos(ang), 0))
def dpos(s, t, z): return hinge + dv * s + pv * t + Vector((0, 0, z))
for i in range(7):
    box(dpos(.15 + .3 * i, 0, 1.2), (.29, .08, 2.3), "door", "BarnDoor", rot=(0, 0, ang))
for z in (.5, 1.95):
    box(dpos(1.05, .065, z), (2.1, .05, .2), "door", "BarnDoor", rot=(0, 0, ang))
for z in (.5, 1.95):
    box(dpos(.4, .1, z), (.7, .03, .12), "iron", "BarnDoor", rot=(0, 0, ang))
    for s in (.15, .6):
        cyl(dpos(s, .12, z), .03, .02, "iron", "BarnDoor", rot=(radians(90), 0, ang), v=6)
box(dpos(1.05, .1, 1.2), (.15, .03, 2.0), "iron", "BarnDoor", rot=(0, 0, ang))

# ---------------------------------------------------------------- 屋根
EAVE_Z, RIDGE_Z, RY, OVER = 2.9, 7.2, 1.0, 3.1
dy, dz = OVER, RIDGE_Z - EAVE_Z
L = sqrt(dy * dy + dz * dz); th = atan2(dz, dy)
mid = Vector((0, RY - OVER / 2, (EAVE_Z + RIDGE_Z) / 2))
for side in (1, -1):
    Mm = Matrix.Translation(Vector((0, RY, 0)) + Vector((0, (mid.y - RY) * side, mid.z))) @ \
         (Matrix.Rotation(math.pi, 4, 'Z') if side == -1 else Matrix.Identity(4)) @ Matrix.Rotation(th, 4, 'X')
    box_m(Mm, (0, 0, -.175), (9.2, L + .3, .35), "thatch", "Roof")
    nc = 7; h = L / nc
    for k in range(1, nc, 2):
        v0 = -L / 2 + k * h; v1 = v0 + h * .8
        xs = np.arange(-4.6, 4.61, .25)
        bot = [(x, v0 + (.2 if i % 2 else 0.0), .02) for i, x in enumerate(xs)]
        top = [(xs[-1], v1, .02), (xs[0], v1, .02)]
        vs = bot + top
        poly("Zig", vs, [tuple(range(len(vs)))], "thatchd", "Roof", Mm)
    # 棟の黒い梁
    box_m(Mm, (0, L / 2 - .1, .1), (9.8, .3, .3), "ridge", "Roof")
    box_m(Mm, (0, -L / 2 + .05, -.05), (9.6, .22, .22), "ridge", "Roof")  # 軒の梁
for sx in (-1, 1):
    for a in (-35, 35):
        box((sx * 4.8, RY, RIDGE_Z + .45), (.12, .12, 1.6), "ridge", "Roof", rot=(0, radians(a), 0))

# ---------------------------------------------------------------- 井戸
wx, wy = -5.4, -3.4
for k in range(10):
    a = k * radians(36)
    box((wx + .75 * cos(a), wy + .75 * sin(a), .4 + rng.uniform(-.03, .03)),
        (.5, .36, .8 + rng.uniform(-.05, .05)), "stone", "Well", rot=(0, 0, a + radians(90) + rng.uniform(-.1, .1)))
cyl((wx, wy, .62), .66, .02, "water", "Well", v=12)
for sx in (-1, 1):
    box((wx + sx * .9, wy, 1.0), (.15, .15, 2.0), "beam", "Well")
cyl((wx, wy, 1.8), .06, 1.9, "beam", "Well", rot=(0, radians(90), 0))
for sy in (-1, 1):
    box((wx, wy + sy * .3, 2.15), (2.0, .75, .06), "door", "Well", rot=(radians(sy * 35), 0, 0))
cyl((wx, wy, 1.5), .015, .6, "door", "Well", v=4)
cone((wx, wy, 1.18), .18, .15, .25, "door", "Well")
cyl((wx, wy, 1.0), .165, .02, "water", "Well", v=8)

# ---------------------------------------------------------------- 畑と柵
gx0, gx1, gy0, gy1 = 5.0, 9.4, -3.2, 1.2
box(((gx0 + gx1) / 2, (gy0 + gy1) / 2, .07), (gx1 - gx0, gy1 - gy0, .14), "soil", "Garden")
fp = []
for x in np.arange(gx0, gx1 + .01, .8): fp += [(x, gy0), (x, gy1)]
for y in np.arange(gy0, gy1 + .01, .8): fp.append((gx1, y))
for (x, y) in fp: box((x, y, .45), (.09, .09, .9), "door", "Garden")
for z in (.35, .7):
    box(((gx0 + gx1) / 2, gy0, z), (gx1 - gx0, .05, .07), "door", "Garden")
    box(((gx0 + gx1) / 2, gy1, z), (gx1 - gx0, .05, .07), "door", "Garden")
    box((gx1, (gy0 + gy1) / 2, z), (.05, gy1 - gy0, .07), "door", "Garden")
for i in range(7):                                                      # トマト
    px = gx0 + .7 + (i % 4) * 1.0 + rng.uniform(-.1, .1); py = gy0 + .8 + (i // 4) * 1.5 + rng.uniform(-.2, .2)
    cyl((px, py, .6), .02, 1.2, "door", "Garden", v=4)
    for j in range(3):
        ball((px + rng.uniform(-.15, .15), py + rng.uniform(-.15, .15), .45 + j * .3), .24, "leaf", "Garden", s=(1, 1, .8))
    for j in range(5):
        a = rng.uniform(0, 6.28)
        ball((px + .22 * cos(a), py + .22 * sin(a), .35 + rng.uniform(0, .7)), .065, "tomato", "Garden")
for (fx, fy) in [(4.7, -2.2), (5.0, -1.0), (4.65, .3), (4.9, 1.1), (5.6, .7), (4.4, -.4)]:  # 背の高い橙の花
    h = rng.uniform(1.3, 1.7)
    cyl((fx, fy, h / 2), .025, h, "leaf", "Garden", v=6)
    for j in range(4):
        a = rng.uniform(0, 6.28); zz = h * (.55 + j * .12)
        ball((fx + .09 * cos(a), fy + .09 * sin(a), zz), .075, "flower", "Garden", s=(1, 1, 1.5))
    for j in range(3):
        a = j * 2.1 + rng.uniform(-.3, .3)
        cone((fx + .22 * cos(a), fy + .22 * sin(a), .55), .09, 0, 1.1, "blade", "Garden",
             rot=(radians(18) * -sin(a), radians(18) * cos(a), 0), v=4)

# ---------------------------------------------------------------- 木箱・樽・バケツ・薪・切り株
for (cx, cy, cz) in [(-1.0, -2.4, .25), (-.35, -2.55, .25), (-.7, -2.45, .75)]:
    box((cx, cy, cz), (.5, .5, .5), "door", "Props", rot=(0, 0, rng.uniform(-.15, .15)))
    for z in (-.15, 0, .15):
        box((cx, cy, cz + z), (.54, .54, .06), "beam", "Props")
for (bx, by) in [(3.2, -3.1), (3.9, -3.5)]:
    cyl((bx, by, .4), .35, .8, "door", "Props", v=12).scale = (1.05, 1.05, 1)
    for z in (.2, .6): cyl((bx, by, z), .37, .05, "iron", "Props", v=12)
    cyl((bx, by, .76), .31, .02, "water", "Props", v=12)
for (bx, by) in [(2.5, -3.7), (4.5, -2.8)]:
    cone((bx, by, .15), .2, .17, .3, "door", "Props")
    cyl((bx, by, .29), .16, .02, "water", "Props", v=8)
for (lx, ly, lz) in [(0, 0, .15), (.32, 0, .15), (.64, 0, .15), (.16, 0, .43), (.48, 0, .43), (.32, 0, .7)]:
    cyl((9.0 + lx - .3, -4.6 + ly, lz), .15, 1.6, "door", "Props", rot=(radians(90), 0, radians(25)), v=8)
cyl((8.0, -4.6, .22), .32, .45, "door", "Props", v=9)
cyl((8.0, -4.6, .45), .30, .02, "endgrain", "Props", v=9)

# ---------------------------------------------------------------- 草むら
bm = bmesh.new()
for i in range(260):
    cx, cy = rng.uniform(-14, 14), rng.uniform(-12, 12)
    if abs(cx - 0) < 4.6 and -2 < cy < 4: continue
    if gx0 - .3 < cx < gx1 + .3 and gy0 - .3 < cy < gy1 + .3: continue
    if abs(cx - wx) < 1.2 and abs(cy - wy) < 1.2: continue
    for j in range(3):
        a = rng.uniform(0, 6.28); hh = rng.uniform(.15, .32)
        bmesh.ops.create_cone(bm, cap_ends=False, segments=3, radius1=.035, radius2=0, depth=hh,
                              matrix=Matrix.Translation((cx + .06 * cos(a), cy + .06 * sin(a), hh / 2))
                              @ Matrix.Rotation(rng.uniform(-.3, .3), 4, 'X'))
me = bpy.data.meshes.new("Grass"); bm.to_mesh(me); bm.free()
go = bpy.data.objects.new("Grass", me); bpy.context.collection.objects.link(go)
reg(go, "Grass", "leaf")

# ---------------------------------------------------------------- まとめて GLB
def join(grp):
    objs = G[grp]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = grp
    return o
for g in list(G): join(g)
bpy.ops.object.select_all(action='DESELECT')
glb = os.path.join(OUT, "farmhouse.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_apply=True, export_yup=True)
print("GLB:", glb, os.path.getsize(glb) // 1024, "KB")
if NORENDER: sys.exit(0)

# ---------------------------------------------------------------- 光とカメラ
w = bpy.data.worlds.new("W"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (.035, .05, .09, 1)
scene.world = w
def sun(name, e, col, rot):
    l = bpy.data.lights.new(name, 'SUN'); l.energy = e; l.color = col; l.angle = radians(4)
    o = bpy.data.objects.new(name, l); o.rotation_euler = [radians(r) for r in rot]
    bpy.context.collection.objects.link(o)
sun("Key", 3.0, (1, .62, .35), (62, 0, 30))
sun("Fill", .5, (.45, .6, 1), (60, 0, 160))
rim = bpy.data.lights.new("Rim", 'AREA'); rim.energy = 800; rim.size = 6; rim.color = (.6, .75, 1)
ro = bpy.data.objects.new("Rim", rim); ro.location = (-6, 10, 9); bpy.context.collection.objects.link(ro)
tr = ro.constraints.new('TRACK_TO'); tgt = bpy.data.objects.new("T", None); tgt.location = (0, 1, 4)
bpy.context.collection.objects.link(tgt); tr.target = tgt; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
for (x, y, z) in [(-.5, -2.3, 2.0), (3.2, -2.3, 2.0), (-2.6, -2.5, 1.2)]:
    p = bpy.data.lights.new("P", 'POINT'); p.energy = 60; p.color = (1, .55, .25); p.shadow_soft_size = .3
    po = bpy.data.objects.new("P", p); po.location = (x, y, z); bpy.context.collection.objects.link(po)

cam = bpy.data.cameras.new("Cam"); cam.type = 'ORTHO'; cam.ortho_scale = 25
co = bpy.data.objects.new("Cam", cam); bpy.context.collection.objects.link(co)
ct = bpy.data.objects.new("CT", None); ct.location = (2.2, -1.2, 2.4); bpy.context.collection.objects.link(ct)
el, az, d = radians(35), radians(45), 40
co.location = ct.location + Vector((d * cos(el) * sin(az), -d * cos(el) * cos(az), d * sin(el)))
tc = co.constraints.new('TRACK_TO'); tc.target = ct; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
scene.camera = co

scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = RES
scene.view_settings.view_transform = 'AgX'; scene.view_settings.exposure = -.3
try: scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
raw = os.path.join(OUT, "farmhouse_raw.png")
scene.render.filepath = raw; scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)

# ---------------------------------------------------------------- 色づけ（持ち上げ・暖色・四隅を暗く）
from PIL import Image
im = np.asarray(Image.open(raw).convert("RGB")).astype(np.float32) / 255
lift = np.array([.02, .025, .05]); gain = np.array([1.08, 1.0, .92])
im = im * (1 - lift) + lift
im = im * gain
hh, ww = im.shape[:2]
yy, xx = np.mgrid[0:hh, 0:ww]
r = np.sqrt(((xx - ww / 2) / (ww / 2)) ** 2 + ((yy - hh / 2) / (hh / 2)) ** 2)
im *= (1 - .25 * np.clip(r - .5, 0, 1) ** 1.5)[..., None]
im = np.clip(im, 0, 1)
fin = Image.fromarray((im * 255).astype(np.uint8)); fin.save(os.path.join(OUT, "farmhouse.png"))
px = fin.resize((RES[0] // 4, RES[1] // 4), Image.BOX).quantize(40, dither=Image.Dither.NONE).convert("RGB")
px.resize(RES, Image.NEAREST).save(os.path.join(OUT, "farmhouse_pixel.png"))
print("done")
