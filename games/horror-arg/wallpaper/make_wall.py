# 壁紙用の風景（夕暮れの家と丘）をBlenderで作って描画する。
# 使い方: blender -b -P make_wall.py -- 出力.png 幅 高さ サンプル数 [mood]
#   mood: dusk（黄色いもや）/ night（青い月）/ red（赤い月）/ lit（night＋窓の明かり）
import bpy, bmesh, math, random, sys
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, W, H, SAMPLES = argv[0], int(argv[1]), int(argv[2]), int(argv[3])
MOOD = argv[4] if len(argv) > 4 else "dusk"
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.filepath = OUT
sc.view_settings.view_transform = "Filmic" if "Filmic" in [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items] else "AgX"
sc.cycles.max_bounces = 4
sc.view_settings.exposure = float(__import__("os").environ.get("EXPO", {"dusk": "-2.6", "red": "-0.5", "night": "-0.3", "lit": "-0.3"}.get(MOOD, "-2.6")))
try:
    sc.view_settings.look = "High Contrast" if sc.view_settings.view_transform == "Filmic" else "AgX - High Contrast"
except TypeError:
    pass
sc.cycles.volume_bounces = 1

def mat(name, color, rough=0.8, emit=0.0, bump=None, shingle=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links
    b = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = emit
    if bump:  # 板張りのすじ
        wv = n.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = bump; wv.wave_type = "BANDS"; wv.bands_direction = "Z"
        bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 1.0
        tc = n.new("ShaderNodeTexCoord")
        l.new(tc.outputs["Object"], wv.inputs["Vector"]); l.new(wv.outputs["Fac"], bp.inputs["Height"]); l.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

_created = []
def add(obj, m=None, name=None):
    _created.append(obj)
    bpy.context.collection.objects.link(obj)
    if name: obj.name = name
    if m: obj.data.materials.append(m)
    return obj

def mesh_obj(name, verts, faces):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    return bpy.data.objects.new(name, me)

def box(name, cx, cy, cz, sx, sy, sz, m):
    v = [(cx + dx * sx / 2, cy + dy * sy / 2, cz + dz * sz / 2) for dz in (-1, 1) for dy in (-1, 1) for dx in (-1, 1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return add(mesh_obj(name, v, f), m)

def cyl(name, x, y, z0, z1, r, m, seg=10):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=z1 - z0, matrix=__import__("mathutils").Matrix.Translation((x, y, (z0 + z1) / 2)))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return add(bpy.data.objects.new(name, me), m)

yellow = mat("wall", (0.78, 0.62, 0.22), 0.7, bump=38)
trim = mat("trim", (0.62, 0.66, 0.72), 0.6)
roof = mat("roof", (0.34, 0.30, 0.27), 0.85)
_rn = roof.node_tree.nodes; _rl = roof.node_tree.links
_br = _rn.new("ShaderNodeTexBrick"); _br.inputs["Scale"].default_value = 9; _br.inputs["Mortar Size"].default_value = 0.04
_bp = _rn.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.9; _tc = _rn.new("ShaderNodeTexCoord")
_rl.new(_tc.outputs["Object"], _br.inputs["Vector"]); _rl.new(_br.outputs["Fac"], _bp.inputs["Height"]); _rl.new(_bp.outputs["Normal"], next(x for x in _rn if x.type == "BSDF_PRINCIPLED").inputs["Normal"])
white = mat("white", (0.82, 0.82, 0.80), 0.6)
dark = mat("dark", (0.01, 0.01, 0.012), 0.9)
wood = mat("pole", (0.10, 0.07, 0.05), 0.9)
steel = mat("steel", (0.12, 0.10, 0.09), 0.6)
glow = mat("glow", (1.0, 0.55, 0.16), 1.0, emit=(14 if MOOD == "lit" else 0.0))

def house(x, y, w, d, h, rot=0, big=True, lit_windows=False):
    # 壁
    box("wall", x, y, h / 2, w, d, h, yellow)
    # 屋根（三角柱）
    rh = w * 0.42
    v = [(x - w / 2 - .25, y - d / 2 - .25, h), (x + w / 2 + .25, y - d / 2 - .25, h), (x, y - d / 2 - .25, h + rh),
         (x - w / 2 - .25, y + d / 2 + .25, h), (x + w / 2 + .25, y + d / 2 + .25, h), (x, y + d / 2 + .25, h + rh)]
    add(mesh_obj("roof", v, [(0, 1, 2), (3, 5, 4), (0, 2, 5, 3), (1, 4, 5, 2), (0, 3, 4, 1)]), roof)
    if not big: return
    # 破風板（三角の斜めのふち）とひさし
    for sx in (-1, 1):
        a = (x + sx * (w / 2 + .25), y - d / 2 - .25, h); c = (x, y - d / 2 - .25, h + rh)
        t = .16
        v = [(a[0], a[1] - .06, a[2]), (c[0], c[1] - .06, c[2]), (c[0], c[1] - .06, c[2] - t * 1.6), (a[0] - sx * t * .4, a[1] - .06, a[2] - t)]
        v2 = [(q[0], q[1] + .14, q[2]) for q in v]
        add(mesh_obj("rake", v + v2, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]), trim)
    box("eave_f", x, y - d / 2 - .25, h - .02, w + .5, .14, .16, trim); box("eave_b", x, y + d / 2 + .25, h - .02, w + .5, .14, .16, trim)
    box("chimney", x + w * 0.18, y + d * 0.25, h + rh * 0.9, .45, .45, 1.6, roof)
    box("band", x, y - d / 2 - .02, h * 0.47, w * 1.0, .06, .22, trim)
    for cx in (-w / 2 - .02, w / 2 + .02):
        box("corner", x + cx, y - d / 2, h / 2, .16, .16, h, trim); box("corner", x + cx, y + d / 2, h / 2, .16, .16, h, trim)
    # 窓：正面（手前の面）
    wins = [(-1.7, 0.75), (1.7, 0.75), (-2.2, 2.7), (0, 2.7), (2.2, 2.7)] if False else []
    for (wx, wz) in [(-w * .28, h * .72), (w * .28, h * .72), (-w * .3, h * .22), (0, h * .22), (w * .3, h * .22)]:
        mm = glow if MOOD == "lit" else dark
        box("win", x + wx, y - d / 2 - .03, wz + 0.2, 1.0, .1, 1.3, trim)
        box("glass", x + wx, y - d / 2 - .09, wz + 0.2, .84, .06, 1.14, mm)
        box("bar_v", x + wx, y - d / 2 - .12, wz + 0.2, .05, .04, 1.14, trim)
        box("bar_h", x + wx, y - d / 2 - .12, wz + 0.2, .84, .04, .05, trim)
        box("sill", x + wx, y - d / 2 - .1, wz - .5, 1.2, .16, .07, white); box("head", x + wx, y - d / 2 - .08, wz + .92, 1.2, .1, .1, white)

# ---- 地面（丘）----
N = 140; SZ = 360
bm = bmesh.new()
g = bmesh.ops.create_grid(bm, x_segments=N, y_segments=N, size=SZ / 2)
from mathutils import noise
for vt in bm.verts:
    x, y = vt.co.x, vt.co.y
    r = math.hypot(x + 2, y - 6)
    flat = min(1.0, max(0.0, (r - 20) / 30))   # 家の周りは平ら
    hh = noise.noise(Vector((x * 0.012, y * 0.012, 3.1))) * 8 + noise.noise(Vector((x * 0.04, y * 0.04, 9))) * 1.6
    vt.co.z = max(0, hh + 3.5) * flat * (0.5 + 0.5 * min(1, max(0, y / 30)))  # 奥ほど高い
me = bpy.data.meshes.new("ground"); bm.to_mesh(me); bm.free()
gr = bpy.data.objects.new("ground", me); bpy.context.collection.objects.link(gr)
for p in gr.data.polygons: p.use_smooth = True
gm = mat("grass", (0.20, 0.24, 0.06), 0.95); gr.data.materials.append(gm)

house(0, 8, 7.0, 5.0, 5.0)
# 柵（先のとがった板を、まとめて1つのメッシュに）
def fence(x0, x1, y, step=0.24, hgt=1.0):
    V = []; F = []
    def quad_box(cx, cy, z0, z1, sx, sy):
        i = len(V)
        for dz in (z0, z1):
            for dy_ in (-1, 1):
                for dx_ in (-1, 1): V.append((cx + dx_ * sx / 2, cy + dy_ * sy / 2, dz))
        F.extend([(i, i + 1, i + 3, i + 2), (i + 4, i + 6, i + 7, i + 5), (i, i + 4, i + 5, i + 1), (i + 2, i + 3, i + 7, i + 6), (i, i + 2, i + 6, i + 4), (i + 1, i + 5, i + 7, i + 3)])
    x = x0
    while x < x1:
        quad_box(x, y, 0.0, hgt - .08, .11, .035)
        i = len(V); V.extend([(x - .055, y - .0175, hgt - .08), (x + .055, y - .0175, hgt - .08), (x, y - .0175, hgt + .06), (x - .055, y + .0175, hgt - .08), (x + .055, y + .0175, hgt - .08), (x, y + .0175, hgt + .06)])
        F.extend([(i, i + 1, i + 2), (i + 3, i + 5, i + 4), (i, i + 2, i + 5, i + 3), (i + 1, i + 4, i + 5, i + 2)])
        x += step
    for rz in (.28, .7):
        quad_box((x0 + x1) / 2, y + .05, rz - .04, rz + .04, x1 - x0, .05)
    for px in range(int(x0), int(x1) + 1, 3):
        quad_box(px, y + .05, 0, hgt + .1, .12, .12)
    add(mesh_obj("fence", V, F), white)
fence(-45, -3.8, 3.0); fence(3.8, 70, 3.0)
# 電柱
def pole(x, y, h=7.5, s=1.0):
    cyl("pole", x, y, 0, h * s, .16 * s, wood); box("arm", x, y, h * s - .5 * s, 2.2 * s, .12 * s, .14 * s, wood)
pole(-10, 1.0); pole(30, 70, 7.5, 1.6); pole(60, 110, 7.5, 2.2); pole(5, 90, 7.5, 1.8)
# 給水塔
def tower(x, y, z, s):
    V = []; F = []
    def bar(p0, p1, t):
        d = Vector(p1) - Vector(p0); d.normalize()
        u = d.cross(Vector((0, 0, 1)) if abs(d.z) < .9 else Vector((1, 0, 0))); u.normalize(); w = d.cross(u)
        i = len(V)
        for e in (p0, p1):
            for a_, b_ in ((-1, -1), (1, -1), (1, 1), (-1, 1)): V.append(tuple(Vector(e) + u * a_ * t + w * b_ * t))
        F.extend([(i, i + 1, i + 2, i + 3), (i + 4, i + 7, i + 6, i + 5), (i, i + 4, i + 5, i + 1), (i + 1, i + 5, i + 6, i + 2), (i + 2, i + 6, i + 7, i + 3), (i + 3, i + 7, i + 4, i)])
    H = 10 * s; L = 1.7 * s; Lt = 1.25 * s
    cs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for sx, sy in cs: bar((x + sx * L, y + sy * L, z), (x + sx * Lt, y + sy * Lt, z + H), .07 * s)
    for k in (.3, .62):   # 横の輪とすじかい
        zl = z + H * k; r = L + (Lt - L) * k
        for (ax, ay), (bx, by) in zip(cs, cs[1:] + cs[:1]):
            bar((x + ax * r, y + ay * r, zl), (x + bx * r, y + by * r, zl), .05 * s)
            bar((x + ax * r, y + ay * r, zl), (x + bx * Lt, y + by * Lt, z + H * (k + .32)), .03 * s)
            bar((x + bx * r, y + by * r, zl), (x + ax * Lt, y + ay * Lt, z + H * (k + .32)), .03 * s)
    add(mesh_obj("tower_legs", V, F), steel)
    cyl("tank", x, y, z + H, z + H + 4 * s, 2.4 * s, steel, 24)
    for k in (.8, 2.0, 3.2): cyl("band", x, y, z + H + k * s, z + H + k * s + .12 * s, 2.5 * s, wood, 24)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=2.5 * s, radius2=.15 * s, depth=1.6 * s, matrix=__import__("mathutils").Matrix.Translation((x, y, z + H + 4.8 * s)))
    me = bpy.data.meshes.new("cone"); bm.to_mesh(me); bm.free(); add(bpy.data.objects.new("cone", me), steel)
    cyl("base", x, y, z + H - .4 * s, z + H, 2.7 * s, steel, 24)
def zat(x, y):
    from mathutils.bvhtree import BVHTree
    bm2 = bmesh.new(); bm2.from_mesh(gr.data); bvh = BVHTree.FromBMesh(bm2)
    hit = bvh.ray_cast(Vector((x, y, 100)), Vector((0, 0, -1)))
    bm2.free(); return hit[0].z if hit[0] else 0
tower(45, 95, zat(45, 95) - .3, 1.8); tower(125, 150, zat(125, 150) - .3, 2.6); tower(-75, 150, zat(-75, 150) - .3, 2.2)
_b = math.atan2(0.5 + 6.5, 8 + 11.5)
for (ang, dist, s_) in [(-27, 125, 1.9), (-15, 95, 1.5), (-6, 160, 2.2), (9, 110, 1.7), (19, 175, 2.3), (28, 140, 2.0), (-21, 210, 2.6)]:
    hx = -6.5 + dist * math.sin(_b + math.radians(ang)); hy = -11.5 + dist * math.cos(_b + math.radians(ang))
    n0 = len(_created); house(hx, hy, 7.0 * s_, 5.0 * s_, 5.0 * s_, big=False)
    zz = zat(hx, hy) - 0.2
    for ob in _created[n0:]: ob.location.z += zz
# 草（手前だけ）
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -4, 0.02)); pl = bpy.context.object; pl.scale = (60, 30, 1); bpy.ops.object.transform_apply(scale=True)
pl.data.materials.append(gm)
ps = pl.modifiers.new("hair", "PARTICLE_SYSTEM").particle_system
st = ps.settings; st.type = "HAIR"; st.count = 60000 if W > 900 else 20000; st.hair_length = 0.7; st.use_advanced_hair = True
st.child_type = "INTERPOLATED"; st.rendered_child_count = 6; st.child_length = 0.9; st.child_length_threshold = 0.3; st.clump_factor = 0.4
st.root_radius = 0.9; st.tip_radius = 0.0; st.particle_size = 0.03; st.use_parent_particles = True
hm = bpy.data.materials.new("hair"); hm.use_nodes = True
b = next(x for x in hm.node_tree.nodes if x.type == "BSDF_PRINCIPLED"); b.inputs["Base Color"].default_value = (0.26, 0.32, 0.07, 1); b.inputs["Roughness"].default_value = .8
pl.data.materials.clear(); pl.data.materials.append(gm); pl.data.materials.append(hm); ps.settings.material = 2

# ---- 空・光・もや ----
wd = bpy.data.worlds.new("w"); wd.use_nodes = True; sc.world = wd
nt = wd.node_tree; nt.nodes.clear()
sky = nt.nodes.new("ShaderNodeTexSky"); bg = nt.nodes.new("ShaderNodeBackground"); out = nt.nodes.new("ShaderNodeOutputWorld")
sky.sky_type = "NISHITA"
moods = {
  "dusk": dict(el=12, dust=24, ai=1.0, fog=(0.9, 0.72, 0.18), fd=0.012, sun=(1, .8, .45), sunE=3.2, strength=1.0),
  "night": dict(el=-12, dust=2, ai=1.0, fog=(0.10, 0.16, 0.32), fd=0.004, sun=(.4, .55, 1), sunE=0.0, strength=0.5),
  "red": dict(el=-2, dust=30, ai=1.0, fog=(0.60, 0.07, 0.03), fd=0.006, sun=(1, .25, .1), sunE=1.2, strength=0.9),
}
moods["lit"] = dict(moods["night"])
M = moods[MOOD]
SUNROT = float(__import__("os").environ.get("SUNROT", "0"))
sky.sun_size = math.radians(5); sky.sun_intensity = 0.7; sky.sun_elevation = math.radians(M["el"]); sky.sun_rotation = math.radians(SUNROT); sky.dust_density = M["dust"]; sky.air_density = M["ai"]
bg.inputs["Strength"].default_value = M["strength"]
TINT = None if __import__("os").environ.get("NOTINT") else {"dusk": (1.0, 0.82, 0.35), "red": (1.0, 0.10, 0.04)}.get(MOOD)
if TINT:
    mx = nt.nodes.new("ShaderNodeMixRGB"); mx.blend_type = "MULTIPLY"; mx.inputs["Fac"].default_value = 1.0; mx.inputs["Color2"].default_value = (*TINT, 1)
    nt.links.new(sky.outputs["Color"], mx.inputs["Color1"]); nt.links.new(mx.outputs["Color"], bg.inputs["Color"])
elif MOOD in ("night", "lit"):
    bg.inputs["Color"].default_value = (0.012, 0.03, 0.12, 1); bg.inputs["Strength"].default_value = 1.0
else:
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
if M["sunE"] > 0:
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = M["sunE"]; sun.color = M["sun"]; sun.angle = math.radians(2.2)
    so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so)
    so.rotation_euler = Euler((math.radians(90 - M["el"]), 0, math.radians(SUNROT + 180)), "XYZ")
if MOOD in ("night", "lit"):  # 月
    mo = bpy.data.lights.new("moon", "SUN"); mo.energy = 0.45; mo.color = (.55, .7, 1); mo.angle = math.radians(1.2)
    mob = bpy.data.objects.new("moon", mo); bpy.context.collection.objects.link(mob); mob.rotation_euler = Euler((math.radians(125), 0, math.radians(-25)))
    _cam = Vector((-6.5, -11.5, 1.9)); _f = (Vector((0.5, 8, 3.4)) - _cam).normalized(); _l = Vector((-_f.y, _f.x, 0)).normalized()
    _dir = (_f + 0.36 * _l + 0.33 * Vector((0, 0, 1))).normalized()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=9, location=_cam + _dir * 230); mn = bpy.context.object
    mn.data.materials.append(mat("moon", (0.8, 0.88, 1.0), 1, emit=6))
if MOOD == "red":
    _cam = Vector((-6.5, -11.5, 1.9)); _f = (Vector((0.5, 8, 3.4)) - _cam).normalized(); _l = Vector((-_f.y, _f.x, 0)).normalized()
    _dir = (_f + 0.36 * _l + 0.33 * Vector((0, 0, 1))).normalized()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=9, location=_cam + _dir * 230); mn = bpy.context.object
    mn.data.materials.append(mat("rmoon", (1.0, 0.3, 0.1), 1, emit=7))
# 空気のもや（大きな箱）
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 60, 40)); fg = bpy.context.object; fg.scale = (500, 400, 90); fg.display_type = "WIRE"
fm = bpy.data.materials.new("fog"); fm.use_nodes = True; fn = fm.node_tree.nodes; fl = fm.node_tree.links
for x in list(fn): fn.remove(x)
pv = fn.new("ShaderNodeVolumeScatter"); pv.inputs["Color"].default_value = (*M["fog"], 1); pv.inputs["Density"].default_value = M["fd"]; pv.inputs["Anisotropy"].default_value = 0.45
fo = fn.new("ShaderNodeOutputMaterial"); fl.new(pv.outputs["Volume"], fo.inputs["Volume"]); fg.data.materials.append(fm)

# 補助光：家と手前の草を少し見せる（夜・赤・明かり）
FILL = {"night": ((0.45, 0.6, 1.0), 750), "lit": ((0.45, 0.6, 1.0), 650), "red": ((1.0, 0.28, 0.14), 1500), "dusk": ((1.0, 0.85, 0.5), 600)}[MOOD]
if FILL[1] > 0:
    fl = bpy.data.lights.new("fill", "AREA"); fl.energy = FILL[1]; fl.color = FILL[0]; fl.shape = "DISK"; fl.size = 14
    fo = bpy.data.objects.new("fill", fl); bpy.context.collection.objects.link(fo); fo.location = (-9, -6, 5.5)
    fo.rotation_euler = (Vector((1.0, 12, 3.2)) - fo.location).to_track_quat("-Z", "Y").to_euler()
    rm = bpy.data.lights.new("rim", "AREA"); rm.energy = FILL[1] * 0.5; rm.color = FILL[0]; rm.size = 10
    ro = bpy.data.objects.new("rim", rm); bpy.context.collection.objects.link(ro); ro.location = (12, 18, 8)
    ro.rotation_euler = (Vector((0, 8, 3)) - ro.location).to_track_quat("-Z", "Y").to_euler()

# ---- カメラ ----
cam = bpy.data.cameras.new("cam"); cam.lens = 27; cam.dof.use_dof = False
co = bpy.data.objects.new("cam", cam); bpy.context.collection.objects.link(co); sc.camera = co
co.location = (-6.5, -11.5, 1.9)
d = Vector((0.5, 8, 3.4)) - co.location
co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

bpy.ops.render.render(write_still=True)
print("DONE", OUT)
