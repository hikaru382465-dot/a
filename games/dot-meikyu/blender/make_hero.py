# 頭の大きい戦士（真横・右向き）を作って、すき間が透明の絵に書き出す。
# 実行：blender -b -P make_hero.py   （Blender 内の Scripting タブなら [Alt]+[P]）
import bpy, math, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else ".", "..", "assets", "hero_side.png")
SIZE = 512

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def mat(name, rgb, rough=0.55, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

M = {
    "skin": mat("skin", (0.95, 0.68, 0.52)),
    "hair": mat("hair", (0.95, 0.62, 0.15)),
    "tunic": mat("tunic", (0.45, 0.27, 0.13)),
    "cloth": mat("cloth", (0.82, 0.78, 0.65)),
    "boot": mat("boot", (0.18, 0.10, 0.06)),
    "scarf": mat("scarf", (0.78, 0.12, 0.12)),
    "steel": mat("steel", (0.8, 0.85, 0.92), 0.25, 0.9),
    "gold": mat("gold", (0.95, 0.75, 0.2), 0.3, 0.8),
    "eye": mat("eye", (0.04, 0.03, 0.05), 0.2),
    "white": mat("white", (1, 1, 1), 0.2),
}

def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True

def sphere(name, loc, scale, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=48, ring_count=24, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scale
    o.data.materials.append(M[m]); smooth(o); return o

def cyl(name, loc, r, h, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=32, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    o.data.materials.append(M[m]); smooth(o); return o

def cone(name, loc, r, h, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0, depth=h, vertices=24, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    o.data.materials.append(M[m]); smooth(o); return o

def box(name, loc, size, m, rot=(0, 0, 0), bevel=0.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    md = o.modifiers.new("bevel", "BEVEL"); md.width = bevel; md.segments = 3
    o.data.materials.append(M[m]); smooth(o); return o

D = math.radians
Y = -0.0  # 横から見るので、体はほぼ Y=0 の平面にならべる

# --- あし ---
for x, tag in ((-0.12, "back"), (0.14, "front")):
    cyl("leg_" + tag, (x, Y, 0.30), 0.085, 0.38, "cloth")
    sphere("boot_" + tag, (x + 0.05, Y, 0.10), (0.17, 0.12, 0.10), "boot")
# --- からだ ---
sphere("body", (0, Y, 0.66), (0.27, 0.22, 0.30), "tunic")
cyl("belt", (0, Y, 0.55), 0.265, 0.06, "boot")
sphere("buckle", (0.0, -0.215, 0.55), (0.05, 0.02, 0.05), "gold")
# --- マフラー ---
sphere("scarf", (0.03, Y, 0.90), (0.25, 0.21, 0.07), "scarf")
sphere("scarf_tail", (-0.30, Y, 0.84), (0.22, 0.05, 0.06), "scarf", rot=(0, D(-25), 0))
# --- あたま ---
sphere("head", (0.04, Y, 1.22), (0.46, 0.42, 0.42), "skin")
sphere("hair_cap", (-0.04, 0.03, 1.36), (0.50, 0.46, 0.36), "hair")
sphere("hair_front", (0.27, -0.10, 1.47), (0.22, 0.28, 0.14), "hair", rot=(0, D(-15), 0))
for i, (x, z, r, a) in enumerate(((-0.28, 1.62, 0.12, 35), (-0.10, 1.72, 0.14, 15), (0.12, 1.70, 0.13, -10), (0.30, 1.60, 0.11, -30), (-0.42, 1.45, 0.11, 70))):
    cone("spike%d" % i, (x, 0.02, z), r, 0.30, "hair", rot=(0, D(a), 0))
# --- 顔（右向き） ---
sphere("eye", (0.30, -0.37, 1.22), (0.060, 0.030, 0.085), "eye")
sphere("eye_hl", (0.315, -0.395, 1.25), (0.020, 0.012, 0.025), "white")
sphere("cheek", (0.25, -0.36, 1.12), (0.07, 0.02, 0.04), "scarf")
box("brow", (0.33, -0.37, 1.34), (0.11, 0.02, 0.03), "hair", rot=(0, D(-10), 0), bevel=0.008)
# --- うで・剣 ---
sphere("arm_back", (-0.02, 0.18, 0.70), (0.08, 0.08, 0.20), "skin", rot=(0, D(10), 0))
sphere("arm_front", (0.27, -0.24, 0.72), (0.085, 0.085, 0.20), "tunic", rot=(0, D(-55), 0))
sphere("hand", (0.40, -0.25, 0.80), (0.085, 0.085, 0.085), "skin")
tilt = (D(0), D(28), D(0))
cx, cz = 0.40, 0.80
def along(d, off=0.0):  # 剣の軸にそった位置
    return (cx + math.sin(D(28)) * d, -0.25 + off, cz + math.cos(D(28)) * d)
cyl("grip", along(0.0), 0.030, 0.18, "boot", rot=tilt)
box("guard", along(0.12), (0.07, 0.30, 0.04), "gold", rot=tilt)
box("blade", along(0.52), (0.09, 0.03, 0.78), "steel", rot=tilt, bevel=0.012)
cone("tip", along(0.96), 0.045, 0.14, "steel", rot=tilt)

# --- ライト（上前から、やわらかい影） ---
def light(name, kind, loc, rot, energy, size=None, color=(1, 1, 1)):
    bpy.ops.object.light_add(type=kind, location=loc, rotation=rot)
    l = bpy.context.object; l.name = name
    l.data.energy = energy; l.data.color = color
    if size: l.data.angle = size if kind == "SUN" else l.data.size
    return l
light("key", "SUN", (0, 0, 3), (D(50), D(10), D(-30)), 3.5, D(25), (1.0, 0.95, 0.88))
light("fill", "SUN", (0, 0, 3), (D(70), D(0), D(40)), 1.0, D(40), (0.7, 0.8, 1.0))
light("rim", "SUN", (0, 0, 3), (D(110), D(0), D(160)), 2.0, D(20), (0.6, 0.7, 1.0))
world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.40, 0.55, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.6

# --- カメラ（ななめでなく真横・平行投影） ---
bpy.ops.object.camera_add(location=(0, -8, 0.95), rotation=(D(90), 0, 0))
cam = bpy.context.object; cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.2
scene.camera = cam

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = SIZE; scene.render.resolution_y = SIZE
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"
scene.render.filepath = os.path.abspath(OUT)
bpy.ops.render.render(write_still=True)
print("書き出し:", scene.render.filepath)
