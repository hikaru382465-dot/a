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

def mat(name, color, rough=0.8, emit=0.0, bump=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links
    b = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = emit
    if bump:  # 板張りのすじ
        wv = n.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = bump; wv.wave_type = "BANDS"; wv.bands_direction = "Z"
        bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35
        tc = n.new("ShaderNodeTexCoord")
        l.new(tc.outputs["Object"], wv.inputs["Vector"]); l.new(wv.outputs["Fac"], bp.inputs["Height"]); l.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def add(obj, m=None, name=None):
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

yellow = mat("wall", (0.78, 0.62, 0.22), 0.7, bump=60)
trim = mat("trim", (0.62, 0.66, 0.72), 0.6)
roof = mat("roof", (0.30, 0.27, 0.25), 0.8)
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
gm = mat("grass", (0.16, 0.19, 0.05), 0.95); gr.data.materials.append(gm)

house(0, 8, 7.0, 5.0, 5.0)
# 柵
for i in range(-34, 36):
    px = i * 0.7 + 3.6
    if -4.2 < px - 0 < 4.2 and False: continue
    box("p", px if px > 4.2 else px, 3.0, .52, .22, .06, 1.0, white)
for rz in (.3, .8):
    box("rail", 14, 3.0, rz, 50, .06, .08, white)
# 電柱
def pole(x, y, h=7.5, s=1.0):
    cyl("pole", x, y, 0, h * s, .16 * s, wood); box("arm", x, y, h * s - .5 * s, 2.2 * s, .12 * s, .14 * s, wood)
pole(-10, 1.0); pole(30, 70, 7.5, 1.6); pole(60, 110, 7.5, 2.2); pole(5, 90, 7.5, 1.8)
# 給水塔
def tower(x, y, z, s):
    for dx in (-1, 1):
        for dy in (-1, 1): cyl("leg", x + dx * 1.4 * s, y + dy * 1.4 * s, z, z + 10 * s, .1 * s, steel, 6)
    cyl("tank", x, y, z + 10 * s, z + 14 * s, 2.4 * s, steel, 16)
    cyl("dome", x, y, z + 14 * s, z + 15 * s, 1.8 * s, steel, 16)
    cyl("base", x, y, z + 9.5 * s, z + 10 * s, 2.6 * s, steel, 16)
def zat(x, y):
    from mathutils.bvhtree import BVHTree
    bm2 = bmesh.new(); bm2.from_mesh(gr.data); bvh = BVHTree.FromBMesh(bm2)
    hit = bvh.ray_cast(Vector((x, y, 100)), Vector((0, 0, -1)))
    bm2.free(); return hit[0].z if hit[0] else 0
tower(45, 95, zat(45, 95), 1.8); tower(125, 150, zat(125, 150), 2.6)
for (hx, hy, s) in [(30, 110, 1.4), (75, 130, 1.2), (110, 150, 1.4), (-30, 140, 1.5)]:
    house(hx, hy, 6 * s, 4 * s, 4 * s, big=False)
    ob = bpy.context.collection.objects[-1]; ob.location.z += zat(hx, hy) - 0.1
# 草（手前だけ）
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -4, 0.02)); pl = bpy.context.object; pl.scale = (60, 30, 1); bpy.ops.object.transform_apply(scale=True)
pl.data.materials.append(gm)
ps = pl.modifiers.new("hair", "PARTICLE_SYSTEM").particle_system
st = ps.settings; st.type = "HAIR"; st.count = 60000 if W > 900 else 20000; st.hair_length = 0.7; st.use_advanced_hair = True
st.child_type = "INTERPOLATED"; st.rendered_child_count = 6; st.child_length = 0.9; st.child_length_threshold = 0.3; st.clump_factor = 0.4
st.root_radius = 0.9; st.tip_radius = 0.0; st.particle_size = 0.03; st.use_parent_particles = True
hm = bpy.data.materials.new("hair"); hm.use_nodes = True
b = next(x for x in hm.node_tree.nodes if x.type == "BSDF_PRINCIPLED"); b.inputs["Base Color"].default_value = (0.20, 0.25, 0.05, 1); b.inputs["Roughness"].default_value = .8
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

# ---- カメラ ----
cam = bpy.data.cameras.new("cam"); cam.lens = 27; cam.dof.use_dof = False
co = bpy.data.objects.new("cam", cam); bpy.context.collection.objects.link(co); sc.camera = co
co.location = (-6.5, -11.5, 1.9)
d = Vector((0.5, 8, 3.4)) - co.location
co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

bpy.ops.render.render(write_still=True)
print("DONE", OUT)
