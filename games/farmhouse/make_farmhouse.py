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

TEX = os.path.join(HERE, "assets", "tex")
def photo(m, name, scale=1.0):
    """assets/tex/<name>_diff.jpg / _rough.jpg / _nor_gl.jpg があれば貼る（Poly Haven の 1k〜2k JPG）。
    なければ何もしない（今までの色のまま）。壁の向きに関係なく貼れるよう、箱の投影(BOX)を使う。"""
    f = lambda k: next((p for p in (os.path.join(TEX, f"{name}_{k}.{e}") for e in ("jpg", "png")) if os.path.exists(p)), None)
    d, r, n = f("diff"), f("rough"), f("nor_gl")
    if not d: return m
    nt = m.node_tree; N = nt.nodes; L = nt.links; b = N["Principled BSDF"]
    co = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(co.outputs["Object"], mp.inputs["Vector"])
    def img(path, cs):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.image.colorspace_settings.name = cs
        t.projection = 'BOX'; t.projection_blend = .2; L.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
    td = img(d, "sRGB")
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1
    L.new(td.outputs["Color"], mix.inputs[6])
    # 元の色は暗いので、写真の色を主役にして少しだけ色をのせる
    mix.inputs[7].default_value = tuple(min(1, c * 2.2 + .35) for c in b.inputs["Base Color"].default_value[:3]) + (1,)
    L.new(mix.outputs[2], b.inputs["Base Color"])
    if r: L.new(img(r, "Non-Color").outputs["Color"], b.inputs["Roughness"])
    if n:
        nm = N.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.0
        L.new(img(n, "Non-Color").outputs["Color"], nm.inputs["Color"]); L.new(nm.outputs["Normal"], b.inputs["Normal"])
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
    vine=mat("Vine", (.03, .13, .05), .8),
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


# ---------------------------------------------------------------- ノードで作る質感（画像なしで細部を出す）
class NB:
    """ノードをつなぐ小さな道具。Object 座標（=ワールド座標）で模様を決める。"""
    def __init__(self, name):
        self.m = bpy.data.materials.new(name); self.m.use_nodes = True
        self.N = self.m.node_tree.nodes; self.L = self.m.node_tree.links
        self.b = self.N["Principled BSDF"]
    def link(self, out, inp): self.L.new(out, inp)
    def coord(self, scale=(1, 1, 1), rot=None):
        out = self.N.new("ShaderNodeTexCoord").outputs["Object"]
        if rot is not None:
            r = self.N.new("ShaderNodeMapping"); r.inputs["Rotation"].default_value = rot
            self.link(out, r.inputs["Vector"]); out = r.outputs["Vector"]
        mp = self.N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = scale
        self.link(out, mp.inputs["Vector"]); return mp.outputs["Vector"]
    def tex(self, kind, vec, out="Fac", **kw):
        t = self.N.new(f"ShaderNodeTex{kind}")
        for k, v in kw.items():
            if k in t.inputs: t.inputs[k].default_value = v
            else: setattr(t, k, v)
        self.link(vec, t.inputs["Vector"]); return t.outputs[out]
    def ramp(self, fac, stops):
        r = self.N.new("ShaderNodeValToRGB"); cr = r.color_ramp
        while len(cr.elements) < len(stops): cr.elements.new(1.0)
        for e, (p, c) in zip(cr.elements, stops): e.position = p; e.color = (*c, 1)
        self.link(fac, r.inputs["Fac"]); return r.outputs["Color"]
    def math(self, op, a, b=0.5, c=None, clamp=False):
        n = self.N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, x in enumerate((a, b, c)):
            if x is None: continue
            if isinstance(x, bpy.types.NodeSocket): self.link(x, n.inputs[i])
            else: n.inputs[i].default_value = x
        return n.outputs[0]
    def mix(self, fac, a, b, blend='MIX'):
        n = self.N.new("ShaderNodeMix"); n.data_type = 'RGBA'; n.blend_type = blend
        for i, x in ((0, fac), (6, a), (7, b)):
            if isinstance(x, bpy.types.NodeSocket): self.link(x, n.inputs[i])
            elif isinstance(x, tuple): n.inputs[i].default_value = (*x, 1)
            else: n.inputs[i].default_value = x
        return n.outputs[2]
    def z(self):
        s = self.N.new("ShaderNodeSeparateXYZ")
        self.link(self.N.new("ShaderNodeTexCoord").outputs["Object"], s.inputs[0]); return s.outputs["Z"]
    def finish(self, color, rough=.9, bump=None, bump_str=.4, metal=0.0):
        self.link(color, self.b.inputs["Base Color"]); self.b.inputs["Roughness"].default_value = rough
        self.b.inputs["Metallic"].default_value = metal
        if bump is not None:
            bn = self.N.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = bump_str
            bn.inputs["Distance"].default_value = .05
            self.link(bump, bn.inputs["Height"]); self.link(bn.outputs["Normal"], self.b.inputs["Normal"])
        return self.m

def grime(nb, col, height=1.5, amount=1.0):
    """足もとほど汚れる（泥はね・苔）。"""
    z = nb.z()
    g = nb.math('MULTIPLY_ADD', z, -1.0 / height, 1.0)
    n2 = nb.tex("Noise", nb.coord((5, 5, 5)), Detail=5.0)
    g = nb.math('ADD', g, nb.math('SUBTRACT', n2, .5), clamp=True)
    return nb.math('MULTIPLY', g, amount, clamp=True)

def plaster_mat():
    nb = NB("Plaster")
    v = nb.coord((3, 3, 3))
    base = nb.ramp(nb.tex("Noise", v, Detail=7.0, Roughness=.6),
                   [(0, (.55, .45, .32)), (.5, (.72, .62, .45)), (1, (.84, .74, .55))])
    edge = nb.tex("Voronoi", nb.coord((1.6, 1.6, 1.6)), out="Distance", feature='DISTANCE_TO_EDGE')
    crack = nb.ramp(edge, [(0, (.35, .28, .2)), (.035, (1, 1, 1)), (1, (1, 1, 1))])
    c = nb.mix(.8, base, crack, 'MULTIPLY')
    specks = nb.tex("Voronoi", nb.coord((40, 40, 40)), out="Distance")
    c = nb.mix(nb.math('LESS_THAN', specks, .06, clamp=True), c, (.45, .36, .25), 'MIX')
    c = nb.mix(grime(nb, 0, 1.3, .9), c, (.07, .09, .05), 'MIX')
    h = nb.math('ADD', nb.tex("Noise", nb.coord((60, 60, 60)), Detail=2.0), edge)
    return nb.finish(c, .92, h, .5)

def wood_mat(name, dark, light, seams=False):
    nb = NB(name)
    g = nb.tex("Noise", nb.coord((5, 5, 22)), Detail=8.0, Roughness=.65)
    base = nb.ramp(g, [(0, dark), (.5, tuple((a + b) / 2 for a, b in zip(dark, light))), (1, light)])
    fine = nb.tex("Noise", nb.coord((40, 40, 160)), Detail=2.0)
    c = nb.mix(.35, base, nb.ramp(fine, [(0, (.55, .55, .55)), (1, (1.2, 1.2, 1.2))]), 'MULTIPLY')
    if seams:
        w = nb.tex("Wave", nb.coord((3.4, 3.4, 1)), wave_type='BANDS', bands_direction='X')
        c = nb.mix(.8, c, nb.ramp(w, [(0, (1, 1, 1)), (.9, (1, 1, 1)), (.97, (.25, .22, .2)), (1, (.25, .22, .2))]), 'MULTIPLY')
    c = nb.mix(grime(nb, 0, .8, .5), c, (.05, .08, .04), 'MIX')
    return nb.finish(c, .8, g, .6)

def thatch_mat(name, rotx, dark=False):
    nb = NB(name)
    v = nb.coord((9, 1.4, 9), rot=(rotx, 0, 0))
    n = nb.tex("Noise", v, Detail=6.0, Roughness=.7)
    st = [(0, (.30, .12, .03)), (.45, (.56, .26, .07)), (.75, (.74, .40, .11)), (1, (.88, .55, .18))]
    if dark: st = [(a, tuple(x * .42 for x in c)) for a, c in st]
    base = nb.ramp(n, st)
    strand = nb.tex("Noise", nb.coord((55, 3, 55), rot=(rotx, 0, 0)), Detail=2.0)
    c = nb.mix(.5, base, nb.ramp(strand, [(0, (.6, .6, .6)), (1, (1.25, 1.2, 1.1))]), 'MULTIPLY')
    return nb.finish(c, .96, nb.math('ADD', n, strand), .9)

def stone_mat():
    nb = NB("Stone")
    v = nb.coord((4.5, 4.5, 4.5))
    cell = nb.tex("Voronoi", v, out="Color")
    bw = nb.N.new("ShaderNodeRGBToBW"); nb.link(cell, bw.inputs[0])
    base = nb.ramp(bw.outputs[0], [(0, (.17, .17, .16)), (.5, (.30, .29, .27)), (1, (.44, .41, .36))])
    edge = nb.tex("Voronoi", v, out="Distance", feature='DISTANCE_TO_EDGE')
    c = nb.mix(nb.math('LESS_THAN', edge, .06, clamp=True), base, (.08, .08, .07), 'MIX')
    mo = nb.math('MULTIPLY', nb.tex("Noise", nb.coord((9, 9, 9)), Detail=4.0), 1.0)
    c = nb.mix(nb.math('MULTIPLY', grime(nb, 0, 1.0, 1.0), nb.math('GREATER_THAN', mo, .45), clamp=True), c, (.05, .15, .06), 'MIX')
    h = nb.math('ADD', nb.math('MULTIPLY', edge, 2.0), nb.tex("Noise", nb.coord((30, 30, 30)), Detail=3.0))
    return nb.finish(c, .92, h, .8)

def ground_mat():
    nb = NB("Ground")
    big = nb.tex("Noise", nb.coord((.45, .45, .45)), Detail=3.0)
    mid = nb.tex("Noise", nb.coord((3, 3, 3)), Detail=4.0)
    base = nb.ramp(big, [(0, (.05, .13, .13)), (.45, (.07, .18, .11)), (.7, (.09, .22, .11)), (1, (.05, .16, .09))])
    base = nb.mix(.5, base, nb.ramp(mid, [(0, (.7, .75, .8)), (1, (1.15, 1.2, 1.1))]), 'MULTIPLY')
    sp = nb.tex("Voronoi", nb.coord((26, 26, 26)), out="Distance")
    m1 = nb.math('MULTIPLY', nb.math('LESS_THAN', sp, .09), nb.math('GREATER_THAN', mid, .42), clamp=True)
    c = nb.mix(m1, base, (.13, .30, .10), 'MIX')
    sp2 = nb.tex("Voronoi", nb.coord((15, 15, 15)), out="Distance")
    m2 = nb.math('MULTIPLY', nb.math('LESS_THAN', sp2, .06), nb.math('LESS_THAN', mid, .35), clamp=True)
    c = nb.mix(m2, c, (.02, .05, .05), 'MIX')
    return nb.finish(c, .97, nb.tex("Noise", nb.coord((50, 50, 50)), Detail=3.0), .25)

def dirt_mat():
    nb = NB("Dirt")
    n = nb.tex("Noise", nb.coord((2.5, 2.5, 2.5)), Detail=5.0)
    base = nb.ramp(n, [(0, (.11, .065, .04)), (.5, (.19, .115, .07)), (1, (.27, .17, .10))])
    pe = nb.tex("Voronoi", nb.coord((22, 22, 22)), out="Distance")
    c = nb.mix(nb.math('LESS_THAN', pe, .08, clamp=True), base, (.26, .23, .20), 'MIX')
    return nb.finish(c, 1.0, nb.tex("Noise", nb.coord((45, 45, 45)), Detail=3.0), .5)

M["plaster"] = plaster_mat()
M["beam"] = wood_mat("Beam", (.045, .022, .012), (.15, .08, .04))
M["door"] = wood_mat("DoorWood", (.12, .06, .028), (.38, .21, .10), seams=True)
M["stone"] = stone_mat()
M["ground"] = ground_mat()
M["dirt"] = dirt_mat()
TH = atan2(7.2 - 2.9, 3.1)
M["thatch_f"] = thatch_mat("ThatchF", -TH); M["thatch_b"] = thatch_mat("ThatchB", TH)
M["thatchd_f"] = thatch_mat("ThatchDF", -TH, True); M["thatchd_b"] = thatch_mat("ThatchDB", TH, True)
# .glb には模様のノードが入らないので、代わりになる平均の色を入れておく（Three.js などで使う色）
for k, c in dict(plaster=(.68, .58, .42), beam=(.09, .05, .027), door=(.25, .14, .065), stone=(.30, .29, .27),
                 ground=(.06, .16, .10), dirt=(.18, .11, .065), thatch_f=(.62, .32, .09), thatch_b=(.62, .32, .09),
                 thatchd_f=(.26, .13, .04), thatchd_b=(.26, .13, .04)).items():
    M[k].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*c, 1)
M["sack"] = mat("Sack", (.42, .30, .15), .95, bump=(40, .5))
M["cap"] = mat("Cap", (.5, .1, .05), .6)
M["white"] = mat("White", (.8, .8, .75), .7)
M["blue"] = mat("BlueFlower", (.25, .35, .8), .7)
M["pebble"] = mat("Pebble", (.2, .2, .2), .9, bump=(30, .4))

photo(M["plaster"], "plaster", .35); photo(M["beam"], "wood", .5); photo(M["door"], "wood", .5)
photo(M["stone"], "stone", .4); photo(M["thatch"], "thatch", .3)

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
ground.data.materials.append(M["ground"])
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
    box_m(Mm, (0, 0, -.175), (9.2, L + .3, .35), "thatch_f" if side == 1 else "thatch_b", "Roof")
    nc = 7; h = L / nc
    for k in range(1, nc, 2):
        v0 = -L / 2 + k * h; v1 = v0 + h * .8
        xs = np.arange(-4.6, 4.61, .25)
        bot = [(x, v0 + (.2 if i % 2 else 0.0), .02) for i, x in enumerate(xs)]
        top = [(xs[-1], v1, .02), (xs[0], v1, .02)]
        vs = bot + top
        poly("Zig", vs, [tuple(range(len(vs)))], "thatchd_f" if side == 1 else "thatchd_b", "Roof", Mm)
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

# ---------------------------------------------------------------- 細かい作り込み
# 屋根：軒先のわらのふさ、屋根の苔
for side in (1, -1):
    Mm = Matrix.Translation(Vector((0, RY, 0)) + Vector((0, (mid.y - RY) * side, mid.z))) @ \
         (Matrix.Rotation(math.pi, 4, 'Z') if side == -1 else Matrix.Identity(4)) @ Matrix.Rotation(th, 4, 'X')
    tm = "thatch_f" if side == 1 else "thatch_b"
    for x in np.arange(-4.6, 4.61, .1):
        hl = rng.uniform(.08, .26)
        box_m(Mm, (x, -L / 2 - hl / 2 + .03, -.2), (.09, hl, .22), tm, "Roof")
    for _ in range(9):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
        o = bpy.context.object; r_ = rng.uniform(.12, .26)
        o.matrix_world = Mm @ Matrix.Translation((rng.uniform(-4.4, 4.4), rng.uniform(-L / 2 + .3, L / 2 - .5), .03)) \
            @ Matrix.Diagonal((r_ * 1.4, r_, .06, 1))
        reg(o, "Roof", "vine")
# 妻壁の窓（屋根裏と、下の窓）
box((4.22, 1, 4.6), (.1, .95, .85), "beam", "House")
box((4.26, 1, 4.6), (.05, .78, .68), "glass", "House")
box((4.3, 1, 4.6), (.04, .05, .68), "beam", "House"); box((4.3, 1, 4.6), (.04, .78, .05), "beam", "House")
box((4.22, 1.2, 1.9), (.1, .95, .85), "beam", "House")
box((4.26, 1.2, 1.9), (.05, .78, .68), "glass", "House")
for sy in (-1, 1):
    box((4.35, 1.2 + sy * .62, 1.9), (.05, .42, .75), "door", "House", rot=(0, 0, radians(sy * -20)))
# 足もとの苔、飛び石、小石、花、キノコ、麻袋
for _ in range(26):
    x = rng.uniform(-4, 4); box((x, -1.72, .32 + rng.uniform(0, .05)), (rng.uniform(.2, .6), .12, .1), "vine", "House")
for i, x in enumerate(np.arange(.3, 2.3, .55)):
    cyl((x, -2.5 + .15 * (i % 2), .05), .27, .1, "stone", "Props", v=7, rot=(0, 0, rng.uniform(0, 3)))
for _ in range(34):
    ball((rng.uniform(-11, 11), rng.uniform(-9, 8), .03), rng.uniform(.04, .1), "pebble", "Props", s=(1, 1, .6))
for _ in range(70):
    ball((rng.uniform(-11, 11), rng.uniform(-9, 8), .05), .035, "white" if rng.random() < .6 else "blue", "Props")
for (mx, my) in [(-4.3, -2.4), (-4.1, -2.55), (-6.4, -2.6)]:
    cyl((mx, my, .07), .02, .14, "white", "Props", v=5); cone((mx, my, .17), .07, 0, .1, "cap", "Props", v=7)
for (sx_, sy_, sz_) in [(2.5, -3.05, .2), (2.15, -3.4, .17)]:
    ball((sx_, sy_, sz_), .3, "sack", "Props", s=(1, .75, 1.0))
    cone((sx_, sy_, sz_ + .27), .1, .05, .12, "sack", "Props", v=6)
for (x, y) in fp:
    cone((x, y, .94), .075, .03, .08, "door", "Garden", v=6)

# ---------------------------------------------------------------- つる（壁をはう）
def vine(start, axis, top, wobble=.12):
    """axis='x': 正面の壁をのぼる（start=(x,y)）、axis='y': 右の妻壁をのぼる"""
    z, u = .3, 0.0
    while z < top:
        u += rng.uniform(-.05, .05); u = max(-wobble, min(wobble, u))
        p = (start[0] + u, start[1], z) if axis == 'x' else (start[0], start[1] + u, z)
        ball(p, .04, "vine", "Vines")
        if rng.random() < .75:
            a = rng.uniform(-.2, .2) if True else 0
            q = (p[0] + rng.uniform(-.1, .1), p[1], z + rng.uniform(0, .08)) if axis == 'x' else \
                (p[0], p[1] + rng.uniform(-.1, .1), z + rng.uniform(0, .08))
            ball(q, .11, "vine" if rng.random() < .6 else "leaf", "Vines",
                 s=(1.5, .35, 1.1) if axis == 'x' else (.35, 1.5, 1.1))
        if rng.random() < .08 and axis == 'x':
            ball((p[0] + .05, p[1] - .02, z), .035, "tomato", "Vines")  # 小さな赤い実
        z += rng.uniform(.05, .08)
for x, t in [(-3.85, 2.8), (-1.4, 2.2), (-1.7, 1.2), (.6, 2.6), (2.6, 1.8), (3.9, 2.9), (-.3, 1.0)]:
    vine((x, -1.69), 'x', t)
for y, t in [(-1.4, 3.6), (3.2, 3.0), (.2, 1.4)]:
    vine((4.24, y), 'y', t)

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
import base64
open(os.path.join(OUT, "farmhouse.glb.js"), "w").write('window.FARMHOUSE_GLB_B64="' + base64.b64encode(open(glb, "rb").read()).decode() + '";')
print("GLB:", glb, os.path.getsize(glb) // 1024, "KB")

# ---------------------------------------------------------------- 質感のベイク（ノードの模様を画像に焼いて .glb に入れる）
def bake_all():
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
    scene.cycles.samples = 1; scene.cycles.use_denoising = False
    sizes = dict(House=2048, Roof=2048, Ground=2048, BarnDoor=1024, Well=1024, Garden=1024, Props=1024)
    for name, size in sizes.items():
        o = bpy.data.objects[name]
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=radians(66), island_margin=0.004)
        bpy.ops.object.mode_set(mode='OBJECT')
        ic = bpy.data.images.new(name + "_color", size, size)
        inr = bpy.data.images.new(name + "_normal", size, size); inr.colorspace_settings.name = 'Non-Color'
        mats = [sl.material for sl in o.material_slots]
        nodes = {}
        for m in mats:
            nodes[m] = []
            for im in (ic, inr):
                t = m.node_tree.nodes.new("ShaderNodeTexImage"); t.image = im; nodes[m].append(t)
        for i, kw in enumerate((dict(type='DIFFUSE', pass_filter={'COLOR'}), dict(type='NORMAL', normal_space='TANGENT'))):
            for m in mats:
                m.node_tree.nodes.active = nodes[m][i]
            bpy.ops.object.bake(margin=6, margin_type='EXTEND', use_clear=True, **kw)
            print("baked", name, kw["type"], size)
        for m in mats:  # 焼いた画像につなぎかえる
            nt = m.node_tree; b = nt.nodes["Principled BSDF"]
            nt.links.new(nodes[m][0].outputs["Color"], b.inputs["Base Color"])
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nt.links.new(nodes[m][1].outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    out = os.path.join(OUT, "farmhouse_baked.glb")
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True, export_yup=True,
                              export_image_format='JPEG', export_jpeg_quality=85)
    open(os.path.join(OUT, "farmhouse_baked.glb.js"), "w").write(
        'window.FARMHOUSE_GLB_B64="' + base64.b64encode(open(out, "rb").read()).decode() + '";')
    print("BAKED GLB:", os.path.getsize(out) // 1024, "KB")
if "--bake" in sys.argv:
    bake_all(); sys.exit(0)
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
sun("Fill", 1.1, (.45, .6, 1), (60, 0, 160))
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


# ---------------------------------------------------------------- 農夫（ドット絵の板を、カメラに向けて立てる）
FARMER = os.path.join(OUT, "character", "farmer_front.png")
if os.path.exists(FARMER):
    img = bpy.data.images.load(FARMER)
    fm = bpy.data.materials.new("Farmer"); fm.use_nodes = True
    fn = fm.node_tree.nodes; fb = fn["Principled BSDF"]
    ft = fn.new("ShaderNodeTexImage"); ft.image = img; ft.interpolation = 'Closest'
    fm.node_tree.links.new(ft.outputs["Color"], fb.inputs["Base Color"])
    fm.node_tree.links.new(ft.outputs["Color"], fb.inputs["Emission Color"]); fb.inputs["Emission Strength"].default_value = .25
    fm.node_tree.links.new(ft.outputs["Alpha"], fb.inputs["Alpha"]); fb.inputs["Roughness"].default_value = 1
    FARMER_POS = (1.0, -4.3); FARMER_OBJS = []
    for (fx, fy) in [FARMER_POS]:
        hgt = 2.3; wid = hgt * 32 / 40
        bpy.ops.mesh.primitive_plane_add(size=1)
        fo = bpy.context.object; fo.name = "Farmer"
        fo.matrix_world = xf((fx, fy, hgt / 2 * .86 + .02), (radians(90), 0, radians(45)), (wid, hgt, 1))
        fo.data.materials.append(fm); FARMER_OBJS.append(fo)
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=.4, depth=.02)
        sh = bpy.context.object; sh.matrix_world = xf((fx + .12, fy + .1, .05), (0, 0, 0), (1, .8, 1)); sh.data.materials.append(M["inside"]); FARMER_OBJS.append(sh)
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = RES
scene.view_settings.view_transform = 'AgX'; scene.view_settings.exposure = .35
try: scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
from PIL import Image, ImageFilter

def render_to(path, res, samples, filt=None):
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.cycles.samples = samples
    if filt is not None: scene.cycles.filter_width = filt
    scene.render.filepath = path; scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)

def grade(path, outline=False):
    """持ち上げ・暖色・遠くのもや・四隅を暗く（・輪郭線）。"""
    im = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255
    lift = np.array([.02, .025, .05]); gain = np.array([1.08, 1.0, .92])
    im = (im * (1 - lift) + lift) * gain
    hh, ww = im.shape[:2]
    yy, xx = np.mgrid[0:hh, 0:ww]
    haze = ((1 - yy / hh) ** 2.2 * .28)[..., None]                       # 奥（画面の上）ほど青くかすむ
    im = im * (1 - haze) + np.array([.10, .15, .24]) * haze
    r = np.sqrt(((xx - ww / 2) / (ww / 2)) ** 2 + ((yy - hh / 2) / (hh / 2)) ** 2)
    im *= (1 - .25 * np.clip(r - .5, 0, 1) ** 1.5)[..., None]
    im = np.clip(im, 0, 1)
    g_ = im @ np.array([.3, .59, .11]); im = np.clip(g_[..., None] + (im - g_[..., None]) * (1.3 if outline else 1.1), 0, 1)  # 彩度
    if outline:                                                           # 暗いほうのふちを濃くする
        lum = im @ np.array([.3, .59, .11]); k = np.ones_like(lum)
        for ax in (0, 1):
            d = lum - np.roll(lum, -1, ax)
            dark = (d < -.14) & (lum > .07)                                # 自分が暗い
            k = np.where(dark, k * .62, k)
            d2 = np.roll(d, 1, ax)
            k = np.where((d2 > .14) & (lum > .07), k * .62, k)
        im = im * k[..., None]
    return Image.fromarray((im * 255).astype(np.uint8))

raw = os.path.join(OUT, "farmhouse_raw.png")
if "--pixel-only" not in sys.argv:
    render_to(raw, RES, SAMPLES)
    grade(raw).save(os.path.join(OUT, "farmhouse.png"))

# ドット絵：小さく描いて（270行）、色を32色にしぼり、輪郭線をつけ、4倍に拡大
PX = (480, 270)
rawpx = os.path.join(OUT, "farmhouse_raw_px.png")
for o_ in globals().get("FARMER_OBJS", []): o_.hide_render = True      # ドット絵版は、あとで原寸のまま貼る
scene.render.resolution_x, scene.render.resolution_y = PX
from bpy_extras.object_utils import world_to_camera_view
render_to(rawpx, PX, 24 if os.environ.get("FH_QUICK") else 96, filt=.01)
pix = grade(rawpx, outline=True).quantize(32, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
if os.path.exists(FARMER):
    sp = Image.open(FARMER).convert("RGBA")
    cx, cy, _ = world_to_camera_view(scene, co, Vector((*FARMER_POS, 0)))
    fx_, fy_ = int(cx * PX[0]), int((1 - cy) * PX[1])
    pix = pix.convert("RGBA")
    shade = Image.new("RGBA", pix.size, (0, 0, 0, 0))
    from PIL import ImageDraw
    ImageDraw.Draw(shade).ellipse((fx_ - 8, fy_ - 4, fx_ + 8, fy_ + 2), fill=(10, 14, 20, 120))
    pix = Image.alpha_composite(pix, shade)
    pix.alpha_composite(sp, (fx_ - 16, fy_ - 39))
    pix = pix.convert("RGB")
pix.save(os.path.join(OUT, "farmhouse_pixel_1x.png"))
pix.resize((PX[0] * 4, PX[1] * 4), Image.NEAREST).save(os.path.join(OUT, "farmhouse_pixel.png"))
os.remove(rawpx)
print("done")
