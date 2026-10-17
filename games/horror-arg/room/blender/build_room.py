"""六畳の部屋を作る（Blender 4.2 / Python）。参考絵：../reference/、計画：../PLAN.md
使い方（画面なし）：
  blender -b -P build_room.py -- --render プレビュー出力フォルダ   # 試し描き
  blender -b -P build_room.py -- --export ../room.glb               # Godot用に書き出し
座標：X=西(-)→東(+)、Y=南(-)→北(+)、Z=上。単位メートル。部屋は X[-1.35,1.35] Y[-1.8,1.8] Z[0,2.4]。
窓＝北の壁（机の上）、ドア＝西の壁、ベッド＝東の壁（頭が北）。"""
import bpy, bmesh, math, random, sys, pathlib
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
TEX = HERE.parent / "textures"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
random.seed(5)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
coll = bpy.data.collections.new("Room"); scene.collection.children.link(coll)

# ---------------- 材質 ----------------
_img = {}
def image(name, data=True):
    if name not in _img:
        im = bpy.data.images.load(str(TEX / name)); im.colorspace_settings.name = "Non-Color" if data else "sRGB"; _img[name] = im
    return _img[name]

def mat(name, base=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, albedo=None, normal=None, normal_strength=1.0, rough_tex=None,
        emit=None, emit_strength=1.0, alpha=1.0, emit_color=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]; nodes, links = nt.nodes, nt.links
    bsdf.inputs["Base Color"].default_value = (*base, 1); bsdf.inputs["Roughness"].default_value = rough; bsdf.inputs["Metallic"].default_value = metal
    def tex(fname, srgb):
        t = nodes.new("ShaderNodeTexImage"); t.image = image(fname, data=not srgb); t.image.colorspace_settings.name = "sRGB" if srgb else "Non-Color"; return t
    if albedo: links.new(tex(albedo, True).outputs["Color"], bsdf.inputs["Base Color"])
    if rough_tex:
        t = tex(rough_tex, False); sp = nodes.new("ShaderNodeSeparateColor"); links.new(t.outputs["Color"], sp.inputs["Color"]); links.new(sp.outputs["Green"], bsdf.inputs["Roughness"])
    if normal:
        t = tex(normal, False); nm = nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = normal_strength
        links.new(t.outputs["Color"], nm.inputs["Color"]); links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if emit:
        t = tex(emit, True); links.new(t.outputs["Color"], bsdf.inputs["Emission Color"]); bsdf.inputs["Emission Strength"].default_value = emit_strength
        bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    if emit_color:
        bsdf.inputs["Emission Color"].default_value = (*emit_color, 1); bsdf.inputs["Emission Strength"].default_value = emit_strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        try: m.blend_method = "BLEND"
        except Exception: pass
        try: m.surface_render_method = "BLENDED"
        except Exception: pass
    return m

M = {}
def make_materials():
    M["floor"] = mat("floor", albedo="floor_albedo.png", normal="floor_normal.png", normal_strength=0.8, rough_tex="floor_roughness.png")
    M["wall"] = mat("wall", albedo="wall_albedo.png", normal="wall_normal.png", normal_strength=0.6, rough_tex="wall_roughness.png")
    M["ceiling"] = mat("ceiling", base=(0.30, 0.29, 0.27), rough=0.9)
    M["desk"] = mat("desk", albedo="desk_albedo.png", normal="desk_normal.png", normal_strength=0.3, rough_tex="desk_roughness.png")
    M["duvet"] = mat("duvet", albedo="duvet_albedo.png", normal="duvet_normal.png", normal_strength=0.5, rough=0.95)
    M["sheet"] = mat("sheet", base=(0.55, 0.55, 0.58), rough=0.95)
    M["rug"] = mat("rug", albedo="rug_albedo.png", normal="rug_normal.png", normal_strength=0.7, rough=0.98)
    M["black"] = mat("black_plastic", base=(0.015, 0.015, 0.018), rough=0.45)
    M["black_soft"] = mat("black_leather", base=(0.02, 0.02, 0.025), rough=0.55)
    M["metal"] = mat("metal", base=(0.35, 0.35, 0.38), rough=0.4, metal=1.0)
    M["steel_dark"] = mat("dark_metal", base=(0.04, 0.04, 0.045), rough=0.35, metal=0.9)
    M["white_plastic"] = mat("white_plastic", base=(0.62, 0.62, 0.60), rough=0.5)
    M["ceramic"] = mat("ceramic", base=(0.62, 0.60, 0.55), rough=0.3)
    M["screen"] = mat("screen", emit="screen_emissive.png", emit_strength=1.4)
    M["clock"] = mat("clock_display", emit="clock_emissive.png", emit_strength=1.6)
    M["phone"] = mat("phone", base=(0.01, 0.01, 0.012), rough=0.15, metal=0.2)
    M["bulb"] = mat("bulb", base=(0, 0, 0), emit_color=(1.0, 0.72, 0.38), emit_strength=18)
    M["lamp"] = mat("lamp", base=(0.02, 0.02, 0.022), rough=0.4, metal=0.8)
    M["sticky"] = mat("sticky", albedo="sticky.png", rough=0.9)
    M["window_frame"] = mat("window_frame", base=(0.30, 0.30, 0.31), rough=0.5, metal=0.6)
    M["glass"] = mat("glass", base=(0.5, 0.6, 0.8), rough=0.05, alpha=0.12)
    M["sheer"] = mat("sheer", base=(0.55, 0.57, 0.62), rough=0.9, alpha=0.32)
    M["curtain"] = mat("curtain", base=(0.07, 0.08, 0.13), rough=0.95)
    M["city_night"] = mat("city_night", emit="city_night.png", emit_strength=1.6)
    M["city_morning"] = mat("city_morning", emit="city_morning.png", emit_strength=1.2)
    M["door"] = mat("door", base=(0.13, 0.06, 0.03), rough=0.45)
    M["frame_wood"] = mat("frame_wood", base=(0.10, 0.05, 0.03), rough=0.5)
    M["photo_a"] = mat("photo_a", albedo="photo_a.png", rough=0.4)
    M["photo_b"] = mat("photo_b", albedo="photo_b.png", rough=0.4)
    M["plastic_w"] = mat("switch_plate", base=(0.55, 0.55, 0.50), rough=0.4)
    M["bin"] = mat("bin", base=(0.12, 0.12, 0.13), rough=0.6)
    M["plant"] = mat("plant", base=(0.03, 0.12, 0.04), rough=0.6)
    M["pot"] = mat("pot", base=(0.22, 0.12, 0.08), rough=0.7)
    M["bed_wood"] = mat("bed_wood", albedo="desk_albedo.png", normal="desk_normal.png", normal_strength=0.3, rough=0.5)
    for i, c in enumerate([(0.18, 0.05, 0.05), (0.05, 0.10, 0.18), (0.20, 0.17, 0.08), (0.08, 0.14, 0.09), (0.10, 0.08, 0.14), (0.22, 0.20, 0.17), (0.14, 0.07, 0.04)]):
        M[f"book{i}"] = mat(f"book{i}", base=c, rough=0.7)
    M["jacket"] = mat("jacket", base=(0.06, 0.07, 0.09), rough=0.9)
    M["backpack"] = mat("backpack", base=(0.03, 0.04, 0.05), rough=0.8)
make_materials()

# ---------------- 部品の作り方 ----------------
def link(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    coll.objects.link(o)
    return o

def finish(o, m, uv=None, bevel=0.0, smooth=False):
    o = link(o)
    if m: o.data.materials.append(m)
    if uv:
        bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.uv.cube_project(cube_size=uv); bpy.ops.object.mode_set(mode="OBJECT")
    if bevel:
        b = o.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = 2; b.limit_method = "ANGLE"
    if smooth:
        for p in o.data.polygons: p.use_smooth = True
    return o

def box(name, dims, loc, m, uv=1.0, bevel=0.004, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = dims; bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, m, uv=uv, bevel=bevel)

def cyl(name, r, h, loc, m, rot=(0, 0, 0), verts=32, r2=None, uv=None, smooth=True):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=h, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    return finish(o, m, uv=uv, smooth=smooth)

def sphere(name, r, loc, m, scale=(1, 1, 1), seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=seg // 2, location=loc); o = bpy.context.object; o.name = name
    o.scale = scale; bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(scale=True)
    return finish(o, m, smooth=True)

def between(name, p1, p2, r, m, verts=16):
    p1, p2 = Vector(p1), Vector(p2); d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, vertices=verts, location=(p1 + p2) / 2)
    o = bpy.context.object; o.name = name; o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return finish(o, m, smooth=True)

def set_uv(o, fn, face_ok=lambda f: True):
    """面ごとに、世界座標から UV を決める。fn(世界座標) → (u, v)"""
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT"); bm = bmesh.from_edit_mesh(o.data); uvl = bm.loops.layers.uv.verify()
    mw = o.matrix_world
    for f in bm.faces:
        if face_ok(f):
            for l in f.loops: l[uvl].uv = fn(mw @ l.vert.co)
    bmesh.update_edit_mesh(o.data); bpy.ops.object.mode_set(mode="OBJECT")

def subdivided(o, cuts=1, disp=None, subsurf=0):
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    if cuts:
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.subdivide(number_cuts=cuts); bpy.ops.object.mode_set(mode="OBJECT")
    if disp:
        t = bpy.data.textures.new(o.name + "_n", "CLOUDS"); t.noise_scale = disp[0]
        d = o.modifiers.new("disp", "DISPLACE"); d.texture = t; d.strength = disp[1]; d.mid_level = 0.5
    if subsurf:
        s = o.modifiers.new("sub", "SUBSURF"); s.levels = subsurf; s.render_levels = subsurf
    for p in o.data.polygons: p.use_smooth = True
    return o

# ---------------- 部屋の殻 ----------------
W, D, H = 2.7, 3.6, 2.4
X0, X1, Y0, Y1 = -W / 2, W / 2, -D / 2, D / 2
T = 0.12   # 壁の厚さ
box("floor", (W + 2 * T, D + 2 * T, 0.06), (0, 0, -0.03), M["floor"], uv=1.0, bevel=0)
ceil = box("ceiling", (W + 2 * T, D + 2 * T, 0.06), (0, 0, H + 0.03), M["ceiling"], uv=1.0, bevel=0)
# 北の壁（窓あり：x[-1.3,-0.05] z[0.9,2.0]）
WX0, WX1, WZ0, WZ1 = -1.30, -0.05, 0.90, 2.00
def wall_n(name, x0, x1, z0, z1):
    box(name, (x1 - x0, T, z1 - z0), ((x0 + x1) / 2, Y1 + T / 2, (z0 + z1) / 2), M["wall"], bevel=0)
wall_n("wall_n_low", X0 - T, X1 + T, 0, WZ0); wall_n("wall_n_high", X0 - T, X1 + T, WZ1, H)
wall_n("wall_n_right", WX1, X1 + T, WZ0, WZ1); wall_n("wall_n_left", X0 - T, WX0, WZ0, WZ1)
# 西の壁（ドアあり：y[-0.5,0.3] z[0,2.0]）
DY0, DY1, DZ1 = -0.50, 0.30, 2.00
def wall_w(name, y0, y1, z0, z1):
    box(name, (T, y1 - y0, z1 - z0), (X0 - T / 2, (y0 + y1) / 2, (z0 + z1) / 2), M["wall"], bevel=0)
wall_w("wall_w_south", Y0 - T, DY0, 0, H); wall_w("wall_w_north", DY1, Y1 + T, 0, H); wall_w("wall_w_over_door", DY0, DY1, DZ1, H)
box("wall_e", (T, D + 2 * T, H), (X1 + T / 2, 0, H / 2), M["wall"], bevel=0)
box("wall_s", (W + 2 * T, T, H), (0, Y0 - T / 2, H / 2), M["wall"], bevel=0)
# 幅木
BH = 0.09
def skirt(name, dims, loc): box(name, dims, loc, M["frame_wood"], bevel=0.003)
skirt("skirt_n_l", (WX0 - X0, 0.015, BH), ((X0 + WX0) / 2, Y1 - 0.0075, BH / 2)); skirt("skirt_n_r", (X1 - WX1 + 0.05, 0.015, BH), ((X1 + WX1) / 2, Y1 - 0.0075, BH / 2))
skirt("skirt_n_mid", (WX1 - WX0, 0.015, BH), ((WX0 + WX1) / 2, Y1 - 0.0075, BH / 2))
skirt("skirt_e", (0.015, D, BH), (X1 - 0.0075, 0, BH / 2)); skirt("skirt_s", (W, 0.015, BH), (0, Y0 + 0.0075, BH / 2))
skirt("skirt_w_s", (0.015, DY0 - Y0, BH), (X0 + 0.0075, (Y0 + DY0) / 2, BH / 2)); skirt("skirt_w_n", (0.015, Y1 - DY1, BH), (X0 + 0.0075, (Y1 + DY1) / 2, BH / 2))
# 天井の照明（消えている）
cl_light = cyl("ceiling_light", 0.24, 0.05, (0, 0, H - 0.025), M["white_plastic"])

# ---------------- 窓 ----------------
wx, wz = (WX0 + WX1) / 2, (WZ0 + WZ1) / 2; ww, wh = WX1 - WX0, WZ1 - WZ0
fy = Y1 - 0.03
for nm, dims, loc in [("win_top", (ww, 0.05, 0.04), (wx, fy, WZ1 - 0.02)), ("win_bot", (ww, 0.05, 0.05), (wx, fy, WZ0 + 0.025)),
                      ("win_l", (0.04, 0.05, wh), (WX0 + 0.02, fy, wz)), ("win_r", (0.04, 0.05, wh), (WX1 - 0.02, fy, wz)), ("win_mid", (0.05, 0.06, wh), (wx, fy - 0.01, wz))]:
    box(nm, dims, loc, M["window_frame"], bevel=0.002)
box("win_glass_l", (ww / 2 - 0.03, 0.006, wh - 0.1), (wx - ww / 4, fy - 0.005, wz), M["glass"], bevel=0)
box("win_glass_r", (ww / 2 - 0.03, 0.006, wh - 0.1), (wx + ww / 4, fy + 0.012, wz), M["glass"], bevel=0)
box("win_lock", (0.02, 0.02, 0.05), (wx + 0.04, fy - 0.045, wz), M["metal"], bevel=0.002)
box("sill", (ww + 0.1, 0.16, 0.03), (wx, Y1 - 0.02, WZ0 - 0.005), M["frame_wood"], bevel=0.003)
# 窓の外：夜の街の絵（Godotでは朝の絵に差し替える）
back = box("outside_city", (4.6, 0.01, 2.9), (wx, Y1 + 1.6, 1.55), M["city_night"], bevel=0, uv=None)
set_uv(back, lambda v: ((v.x - (wx - 2.3)) / 4.6, (v.z - (1.55 - 1.45)) / 2.9), lambda f: abs(f.normal.y) > 0.9)
box("balcony_rail", (1.9, 0.03, 0.035), (wx, Y1 + 0.55, 1.0), M["steel_dark"], bevel=0.002)
# カーテン：レース（半透明）と厚手の2枚
rod_z = 2.12
cyl("curtain_rod", 0.013, 1.9, (wx, Y1 - 0.09, rod_z), M["steel_dark"], rot=(0, math.radians(90), 0))
sh = box("curtain_sheer", (1.8, 0.012, 1.95), (wx, Y1 - 0.075, rod_z - 0.975), M["sheer"], bevel=0, uv=None)
subdivided(sh, 40, disp=(0.18, 0.05)); sh.modifiers["disp"].direction = "Y"
for nm, cx in [("curtain_l", WX0 - 0.1), ("curtain_r", WX1 + 0.12)]:
    c = box(nm, (0.38, 0.05, 2.0), (cx, Y1 - 0.11, rod_z - 1.0), M["curtain"], bevel=0, uv=None)
    subdivided(c, 30, disp=(0.12, 0.05)); c.modifiers["disp"].direction = "Y"

# ---------------- ドア（内側から見る：西の壁）----------------
dx = X0 + 0.03; dyc = (DY0 + DY1) / 2
box("door_leaf", (0.04, DY1 - DY0 - 0.02, DZ1 - 0.01), (dx, dyc, DZ1 / 2), M["door"], bevel=0.003)
box("door_slit", (0.012, 0.09, 0.45), (dx + 0.025, dyc + 0.20, 1.45), M["glass"], bevel=0)
for nm, dims, loc in [("doorframe_top", (0.06, DY1 - DY0 + 0.08, 0.05), (dx - 0.005, dyc, DZ1 + 0.015)), ("doorframe_s", (0.06, 0.05, DZ1), (dx - 0.005, DY0 - 0.015, DZ1 / 2)), ("doorframe_n", (0.06, 0.05, DZ1), (dx - 0.005, DY1 + 0.015, DZ1 / 2))]:
    box(nm, dims, loc, M["frame_wood"], bevel=0.003)
cyl("door_knob_rose", 0.03, 0.01, (dx + 0.03, dyc + 0.32, 1.0), M["metal"], rot=(0, math.radians(90), 0))
between("door_lever", (dx + 0.04, dyc + 0.32, 1.0), (dx + 0.07, dyc + 0.20, 1.0), 0.008, M["metal"])
box("light_switch", (0.012, 0.08, 0.12), (X0 + 0.006, DY1 + 0.20, 1.2), M["plastic_w"], bevel=0.002)

# ---------------- 机まわり ----------------
DT = 0.74   # 机の天板の高さ
dxc, dyc2 = -0.70, 1.49
box("desk_top", (1.20, 0.60, 0.03), (dxc, dyc2, DT - 0.015), M["desk"], bevel=0.004)
box("desk_leg_l", (0.03, 0.54, DT - 0.03), (-1.285, dyc2, (DT - 0.03) / 2), M["desk"], bevel=0.003)
box("desk_back_panel", (1.15, 0.015, 0.30), (dxc - 0.02, 1.78, DT - 0.18), M["desk"], bevel=0.003)
ped_x, ped_y = -0.32, 1.50
box("ped_body", (0.40, 0.52, DT - 0.03), (ped_x, ped_y, (DT - 0.03) / 2), M["desk"], bevel=0.003)
for i in range(3):
    z = 0.10 + i * 0.195
    box(f"drawer{i}", (0.37, 0.018, 0.18), (ped_x, ped_y - 0.265, z + 0.095), M["desk"], bevel=0.004)
    box(f"drawer_handle{i}", (0.12, 0.012, 0.012), (ped_x, ped_y - 0.283, z + 0.16), M["metal"], bevel=0.002)
box("pc_tower", (0.20, 0.45, 0.42), (-1.15, 1.54, 0.21), M["black"], bevel=0.004)
box("pc_vent", (0.005, 0.30, 0.20), (-1.05, 1.54, 0.25), M["steel_dark"], bevel=0)
# 椅子
chx, chy = -0.80, 0.86
box("chair_seat", (0.47, 0.46, 0.08), (chx, chy, 0.47), M["black_soft"], bevel=0.02)
box("chair_back", (0.44, 0.07, 0.52), (chx, chy - 0.24, 0.80), M["black_soft"], bevel=0.025, rot=(math.radians(-8), 0, 0))
for s in (-1, 1):
    box(f"chair_arm{s}", (0.04, 0.30, 0.03), (chx + s * 0.255, chy - 0.02, 0.66), M["black_soft"], bevel=0.008)
    box(f"chair_arm_post{s}", (0.03, 0.03, 0.17), (chx + s * 0.255, chy + 0.07, 0.575), M["steel_dark"], bevel=0.003)
cyl("chair_column", 0.025, 0.30, (chx, chy, 0.28), M["steel_dark"])
for i in range(5):
    a = math.radians(72 * i + 20); ex, ey = chx + 0.28 * math.cos(a), chy + 0.28 * math.sin(a)
    between(f"chair_leg{i}", (chx, chy, 0.12), (ex, ey, 0.06), 0.017, M["steel_dark"], verts=8)
    sphere(f"caster{i}", 0.028, (ex, ey, 0.03), M["black"], seg=12)
# モニター
mx, my = -0.80, 1.60
box("mon_base", (0.24, 0.17, 0.012), (mx, my - 0.02, DT + 0.006), M["black"], bevel=0.003)
box("mon_neck", (0.045, 0.025, 0.13), (mx, my + 0.02, DT + 0.077), M["black"], bevel=0.003)
MZ = DT + 0.012 + 0.07 + 0.165
box("mon_panel", (0.58, 0.032, 0.34), (mx, my + 0.02, MZ), M["black"], bevel=0.006)
sc = box("mon_screen", (0.54, 0.002, 0.30), (mx, my + 0.02 - 0.0165, MZ + 0.005), M["screen"], bevel=0, uv=None)
set_uv(sc, lambda v: ((v.x - (mx - 0.27)) / 0.54, (v.z - (MZ + 0.005 - 0.15)) / 0.30), lambda f: f.normal.y < -0.9)
# 付箋（モニターの左のふち）
for i, z in enumerate([MZ + 0.09, MZ + 0.02, MZ - 0.05]):
    box(f"sticky{i}", (0.045, 0.001, 0.045), (mx - 0.31 - 0.003, my + 0.0, z), M["sticky"], bevel=0, uv=1.0, rot=(0, math.radians(random.uniform(-6, 6)), 0))
# キーボード・マウス
kb_c = (mx + 0.02, 1.37, DT + 0.012)
box("kb_body", (0.44, 0.15, 0.022), kb_c, M["black"], bevel=0.004, rot=(math.radians(4), 0, 0))
keys = []
for r in range(5):
    for c in range(17):
        kx = kb_c[0] - 0.205 + c * 0.0245; ky = kb_c[1] + 0.058 - r * 0.026
        keys.append((kx, ky))
for i, (kx, ky) in enumerate(keys):
    box(f"key{i}", (0.019, 0.019, 0.007), (kx, ky, kb_c[2] + 0.014 + (0.058 - (ky - kb_c[1])) * 0.07), M["steel_dark"], bevel=0.0015, uv=None)
box("mousepad", (0.23, 0.20, 0.004), (-0.45, 1.37, DT + 0.002), M["black_soft"], bevel=0.001)
ms = sphere("mouse", 0.05, (-0.45, 1.375, DT + 0.019), M["black"], scale=(0.65, 1.0, 0.45), seg=16)
# 卓上ライト
bx, by = -0.22, 1.63
cyl("lamp_base", 0.075, 0.022, (bx, by, DT + 0.011), M["lamp"])
j1 = (bx + 0.00, by - 0.01, DT + 0.28); j2 = (bx - 0.13, by - 0.06, DT + 0.40)
between("lamp_arm1", (bx, by, DT + 0.02), j1, 0.008, M["lamp"]); sphere("lamp_joint1", 0.014, j1, M["lamp"], seg=12)
between("lamp_arm2", j1, j2, 0.008, M["lamp"]); sphere("lamp_joint2", 0.014, j2, M["lamp"], seg=12)
head = Vector(j2) + Vector((-0.04, -0.02, -0.01))
aim = Vector((-0.50, 1.38, DT)) - head
shade = cyl("lamp_shade", 0.09, 0.12, head, M["lamp"], r2=0.03, verts=32)
shade.rotation_mode = "QUATERNION"; shade.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(aim.normalized())
bulb = sphere("lamp_bulb", 0.028, head + aim.normalized() * 0.045, M["bulb"], seg=16)
# マグカップ・スマホ・時計・ペン立て・本
mugp = (-0.34, 1.38, DT)
cyl("mug", 0.045, 0.095, (mugp[0], mugp[1], DT + 0.0475), M["ceramic"], verts=32)
cyl("mug_inside", 0.038, 0.004, (mugp[0], mugp[1], DT + 0.088), M["black"], verts=24)
bpy.ops.mesh.primitive_torus_add(location=(mugp[0] + 0.05, mugp[1], DT + 0.05), major_radius=0.025, minor_radius=0.007, rotation=(math.radians(90), 0, 0))
mh = bpy.context.object; mh.name = "mug_handle"; mh.scale = (0.9, 1, 1.1); finish(mh, M["ceramic"], smooth=True)
box("phone", (0.072, 0.150, 0.008), (-0.19, 1.27, DT + 0.004), M["phone"], bevel=0.003, rot=(0, 0, math.radians(22)))
box("alarm_clock", (0.15, 0.065, 0.062), (-1.10, 1.50, DT + 0.031), M["black"], bevel=0.004, rot=(0, 0, math.radians(-8)))
cl = box("alarm_clock_face", (0.135, 0.002, 0.046), (-1.10 - 0.0 , 1.50 - 0.0335 + 0.004, DT + 0.031), M["clock"], bevel=0, uv=None, rot=(0, 0, math.radians(-8)))
set_uv(cl, lambda v: (0.1 + (v.x - (-1.10)) / 0.135 * 0.8 + 0.4, 0.5 + (v.z - (DT + 0.031)) / 0.046 * 0.55), lambda f: f.normal.y < -0.5)
cyl("pen_holder", 0.04, 0.10, (-1.24, 1.62, DT + 0.05), M["steel_dark"], verts=20)
for i in range(5):
    a = i * 1.3; tilt = random.uniform(-0.12, 0.12)
    between(f"pencil{i}", (-1.24 + 0.012 * math.cos(a), 1.62 + 0.012 * math.sin(a), DT + 0.06), (-1.24 + 0.012 * math.cos(a) + tilt, 1.62 + 0.012 * math.sin(a) + tilt * 0.5, DT + 0.20), 0.004, M[f"book{i % 7}"], verts=6)
bk = [(0.03, 0.17, 0.22, 0), (0.025, 0.16, 0.21, 1), (0.035, 0.18, 0.23, 4), (0.022, 0.15, 0.20, 3), (0.028, 0.16, 0.22, 5)]
x = -1.05
for i, (bw, bd, bh, mi) in enumerate(bk):
    box(f"desk_book{i}", (bw, bd, bh), (x, 1.69, DT + bh / 2), M[f"book{mi}"], bevel=0.002, uv=None); x += bw + 0.002

# ---------------- ベッド ----------------
bedx, bed_y0, bed_y1 = 0.865, -0.17, 1.78
bl = bed_y1 - bed_y0
box("bed_frame", (0.97, bl, 0.20), (bedx, (bed_y0 + bed_y1) / 2, 0.20), M["bed_wood"], bevel=0.005)
box("bed_head", (0.99, 0.05, 0.62), (bedx, bed_y1 - 0.025, 0.55), M["bed_wood"], bevel=0.006)
box("bed_foot", (0.99, 0.05, 0.34), (bedx, bed_y0 + 0.025, 0.40), M["bed_wood"], bevel=0.006)
for i in range(2):
    box(f"bed_drawer{i}", (0.40, 0.012, 0.13), (bedx - 0.245 + i * 0.49, bed_y0 + 0.003, 0.17), M["bed_wood"], bevel=0.003)
box("mattress", (0.93, bl - 0.08, 0.17), (bedx, (bed_y0 + bed_y1) / 2, 0.385), M["sheet"], bevel=0.04)
dv = box("duvet", (1.05, 1.30, 0.13), (bedx, bed_y0 + 0.65 + 0.05, 0.52), M["duvet"], bevel=0.0, uv=1.0)
subdivided(dv, 26, disp=(0.11, 0.07), subsurf=1)
pw = box("pillow", (0.52, 0.34, 0.12), (bedx, bed_y1 - 0.26, 0.52), M["duvet"], bevel=0.0, uv=1.0)
subdivided(pw, 8, disp=(0.1, 0.02), subsurf=2)
# ラグ・ゴミ箱・小さな棚
box("rug", (1.5, 1.7, 0.018), (0.02, -0.40, 0.009), M["rug"], bevel=0.004, uv=1.0)
cyl("trash_bin", 0.13, 0.28, (X0 + 0.20, Y0 + 0.20, 0.14), M["bin"], verts=24)
box("cabinet_s", (0.35, 0.46, 0.62), (X0 + 0.18, Y0 + 0.78, 0.31), M["desk"], bevel=0.004)
box("cabinet_drawer", (0.012, 0.40, 0.17), (X0 + 0.37, Y0 + 0.78, 0.46), M["desk"], bevel=0.003)
box("cabinet_handle", (0.012, 0.10, 0.012), (X0 + 0.385, Y0 + 0.78, 0.50), M["metal"], bevel=0.002)

# ---------------- 本棚（机の左）と背の高い棚（右・南）----------------
def shelf(name, x, y, w, d, h, rows, along):   # along: 'y' なら奥行きがX方向（壁ぎわ）
    side = M["desk"]
    sx, sy = (d, w) if along == "y" else (w, d)
    for i in range(rows + 1):
        z = 0.03 + i * (h - 0.03) / rows
        box(f"{name}_board{i}", (sx, sy, 0.02), (x, y, z), side, bevel=0.002)
    for s in (-1, 1):
        px, py = (x, y + s * (w / 2 - 0.01)) if along == "y" else (x + s * (w / 2 - 0.01), y)
        box(f"{name}_side{s}", (sx if along == "x" else d, 0.02 if along == "y" else d, h), (px, py, h / 2), side, bevel=0.002) if False else None
        if along == "y": box(f"{name}_side{s}", (d, 0.02, h), (x, y + s * (w / 2 - 0.01), h / 2), side, bevel=0.002)
        else: box(f"{name}_side{s}", (0.02, d, h), (x + s * (w / 2 - 0.01), y, h / 2), side, bevel=0.002)
    back_pos = (x - d / 2 + 0.005, y, h / 2) if along == "y" and x < 0 else (x + d / 2 - 0.005, y, h / 2)
    box(f"{name}_back", (0.01, w, h), back_pos, M["frame_wood"], bevel=0) if along == "y" else None
    # 本
    for r in range(rows):
        zb = 0.04 + r * (h - 0.03) / rows; rowh = (h - 0.03) / rows - 0.03
        cur = -w / 2 + 0.03
        while cur < w / 2 - 0.05:
            bw = random.uniform(0.018, 0.040); bh = random.uniform(rowh * 0.65, rowh * 0.95)
            if random.random() < 0.2: cur += random.uniform(0.04, 0.09); continue
            px, py = (x, y + cur + bw / 2) if along == "y" else (x + cur + bw / 2, y)
            box(f"{name}_b{r}_{int(cur*100)}", (d * 0.8 if along == "y" else bw, bw if along == "y" else d * 0.8, bh), (px, py, zb + bh / 2), M[f"book{random.randint(0, 6)}"], bevel=0.0015, uv=None)
            cur += bw + 0.002
shelf("shelf_w", X0 + 0.15, 0.78, 0.70, 0.30, 1.45, 5, "y")
shelf("shelf_e", X1 - 0.18, -1.24, 0.90, 0.34, 1.80, 5, "y")
# 棚の上の観葉植物
cyl("plant_pot", 0.07, 0.12, (X1 - 0.18, -1.24, 1.86), M["pot"], r2=0.055)
for i in range(9):
    a = i * 0.7; sphere(f"leaf{i}", 0.07, (X1 - 0.18 + 0.05 * math.cos(a), -1.24 + 0.05 * math.sin(a), 2.0 + (i % 3) * 0.06), M["plant"], scale=(0.5, 1.0, 1.6), seg=8)
# 棚の下の段に掛けたジャケットとリュック
box("jacket", (0.04, 0.34, 0.55), (X1 - 0.30, -0.78, 1.2), M["jacket"], bevel=0.015)
box("backpack", (0.30, 0.16, 0.40), (X1 - 0.30, -0.45, 0.20), M["backpack"], bevel=0.03, rot=(0, 0, math.radians(10)))
# 壁の写真（北の壁、ベッドの頭の上）
for nm, mt, w2, h2, px, pz in [("photo_a", M["photo_a"], 0.20, 0.25, 0.68, 1.78), ("photo_b", M["photo_b"], 0.18, 0.22, 0.88, 1.46)]:
    ph = box(nm, (w2, 0.006, h2), (px, Y1 - 0.003, pz), mt, bevel=0.0, uv=None)
    set_uv(ph, lambda v, px=px, pz=pz, w2=w2, h2=h2: ((v.x - (px - w2 / 2)) / w2, (v.z - (pz - h2 / 2)) / h2), lambda f: f.normal.y < -0.5)

# ---------------- ライト ----------------
def light(name, kind, loc, color, energy, **kw):
    ld = bpy.data.lights.new(name, kind); ld.color = color; ld.energy = energy
    for k, v in kw.items(): setattr(ld, k, v)
    o = bpy.data.objects.new(name, ld); o.location = loc; coll.objects.link(o); return o
spot = light("lamp_spot", "SPOT", tuple(head + aim.normalized() * 0.05), (1.0, 0.62, 0.30), 130, spot_size=math.radians(75), spot_blend=0.6, shadow_soft_size=0.04)
spot.rotation_mode = "QUATERNION"; spot.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(aim.normalized())
mon_l = light("monitor_glow", "AREA", (mx, my - 0.12, MZ), (0.35, 0.5, 1.0), 4, shape="RECTANGLE", size=0.54, size_y=0.30)
mon_l.rotation_euler = (math.radians(-90), 0, 0)   # 部屋（南）へ向ける
moon = light("window_moon", "AREA", (wx, Y1 + 0.6, wz), (0.30, 0.42, 1.0), 5, shape="RECTANGLE", size=1.2, size_y=1.0)
moon.rotation_euler = (math.radians(-90), 0, 0)   # 室内（南）へ向ける

# うすい全体の青い明かり（形が読める程度。ホラーなので、ごく弱く）
amb = light("ambient_fill", "AREA", (0, 0, H - 0.08), (0.35, 0.45, 0.85), 22, shape="RECTANGLE", size=2.2, size_y=3.0)
amb.rotation_euler = (0, 0, 0)   # 下向き
# 世界の色（とても暗い青）
world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.012, 0.017, 0.035, 1); bg.inputs["Strength"].default_value = 1.0

# ---------------- 朝の見た目（試し描き用。Godotでは同じ入れかえをする）----------------
if "--morning" in argv:
    back.data.materials[0] = M["city_morning"]
    spot.data.energy = 0; M["bulb"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0
    moon.data.color = (1.0, 0.88, 0.68); moon.data.energy = 90
    amb.data.energy = 60; amb.data.color = (0.9, 0.9, 1.0); mon_l.data.energy = 1.5
    bg.inputs["Color"].default_value = (0.25, 0.28, 0.35, 1)

# ---------------- カメラと出力 ----------------
def camera(name, loc, target, lens=24):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    o = bpy.data.objects.new(name, cd); o.location = loc; coll.objects.link(o)
    d = Vector(target) - Vector(loc); o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); return o
CAMS = {
    "01_topdown": camera("cam_topdown", (0.55, -1.55, 3.9), (-0.05, 0.1, 0.4), 22),
    "02_desk_front": camera("cam_desk", (-0.80, 0.42, 1.28), (-0.80, 1.60, 0.88), 30),
    "03_bed_wide": camera("cam_bed", (-1.0, -1.55, 1.25), (0.1, 1.3, 0.8), 18),
}

if "--render" in argv:
    out = pathlib.Path(argv[argv.index("--render") + 1]); out.mkdir(parents=True, exist_ok=True)
    samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 48
    scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = samples
    scene.cycles.use_denoising = True; scene.cycles.max_bounces = 6
    scene.render.resolution_x, scene.render.resolution_y = 960, 720
    scene.view_settings.view_transform = "Filmic" if "Filmic" in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items.keys() else "Standard"
    scene.view_settings.exposure = float(argv[argv.index("--exposure") + 1]) if "--exposure" in argv else 0.0
    which = argv[argv.index("--cams") + 1].split(",") if "--cams" in argv else list(CAMS)
    for k in which:
        ceil.hide_render = cl_light.hide_render = (k == "01_topdown")
        scene.camera = CAMS[k]; scene.render.filepath = str(out / f"{k}.png"); bpy.ops.render.render(write_still=True); print("RENDERED", k)

if "--export" in argv:
    path = argv[argv.index("--export") + 1]
    bpy.ops.object.select_all(action="DESELECT")
    for o in coll.objects: o.select_set(o.type in {"MESH", "LIGHT"})
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_lights=True, export_image_format="AUTO", export_yup=True)
    print("EXPORTED", path)
if "--save" in argv:
    bpy.ops.wm.save_as_mainfile(filepath=argv[argv.index("--save") + 1]); print("SAVED")
print("OBJECTS", len(coll.objects))
