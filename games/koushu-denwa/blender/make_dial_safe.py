"""
ダイヤル式の金庫を作る（Blender用）。メートル単位。
  DialSafe.fbx … 本体（幅0.42 × 奥行き0.38 × 高さ0.44m。足元が原点。おもて面は -Y 向き＝Unrealでは +Y 向き）
  SafeDial.fbx … ダイヤルのつまみ（中心が原点。回すと Unreal の Pitch（Y軸まわり）で回る。おもて面は -Y 向き）
  材質の穴：本体 0=塗装の鉄 1=真ちゅう／つまみ 0=真ちゅう 1=黒
使い方：python make_dial_safe.py     出力：assets/unreal/DialSafe.fbx, SafeDial.fbx
"""
import bpy, bmesh, math, os, random
from mathutils import Vector

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.path.expanduser('~')
OUT = os.path.normpath(os.path.join(HERE, '..', 'assets', 'unreal'))
os.makedirs(OUT, exist_ok=True)
random.seed(29)


def new_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mats(names):
    return [bpy.data.materials.new(n) for n in names]


def box(name, size, loc, mat_index, ms, bevel=0.003):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        m = o.modifiers.new('b', 'BEVEL')
        m.width = bevel
        m.segments = 2
        m.limit_method = 'NONE'
        bpy.ops.object.modifier_apply(modifier='b')
    o.location = loc
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    for m in ms:
        o.data.materials.append(m)
    for p in o.data.polygons:
        p.material_index = mat_index
    return o


def cyl(name, r, depth, loc, mat_index, ms, verts=24, axis='Y'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth)
    o = bpy.context.active_object
    o.name = name
    if axis == 'Y':
        o.rotation_euler = (math.radians(90), 0, 0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    o.location = loc
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    for m in ms:
        o.data.materials.append(m)
    for p in o.data.polygons:
        p.material_index = mat_index
    return o


def join_export(parts, name, fname):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    o.data.name = name
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, fname), use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
                             path_mode='COPY', embed_textures=False, mesh_smooth_type='FACE', add_leaf_bones=False, bake_space_transform=True)
    print('書き出しました: %s  頂点=%d  大きさ(m)=%s  材質の穴=%d' % (fname, len(o.data.vertices), tuple(round(v, 3) for v in o.dimensions), len(o.data.materials)))


# ---- 本体 ----
new_scene()
ms = mats(['Paint', 'Brass'])
W, D, H = 0.42, 0.38, 0.44
parts = []
parts.append(box('body', (W, D, H), (0, 0, 0.03 + H / 2), 0, ms, 0.008))
for sx in (-1, 1):
    for sy in (-1, 1):
        parts.append(box('foot', (0.05, 0.05, 0.03), (sx * 0.17, sy * 0.15, 0.015), 0, ms, 0.004))
# 扉（本体の前面にかぶせる。すこし出っぱる）
fy = -D / 2
parts.append(box('door', (W - 0.05, 0.022, H - 0.05), (0, fy - 0.009, 0.03 + H / 2), 0, ms, 0.006))
parts.append(box('doorFrame', (W - 0.02, 0.012, H - 0.02), (0, fy - 0.002, 0.03 + H / 2), 0, ms, 0.004))
# 蝶番（左）
for z in (0.12, 0.40):
    parts.append(cyl('hinge', 0.012, 0.07, (-W / 2 + 0.018, fy - 0.022, z), 1, ms, 12, axis='Z'))
# ダイヤルの受け皿（真ちゅうの輪）
parts.append(cyl('dialPlate', 0.082, 0.008, (0, fy - 0.024, 0.03 + H * 0.56), 1, ms, 32))
# 目盛りの印（本体側の三角の目印＝上に1つ）
parts.append(box('pointer', (0.012, 0.006, 0.02), (0, fy - 0.030, 0.03 + H * 0.56 + 0.092), 1, ms, 0.001))
# ハンドル（右側。縦の棒）
parts.append(box('handleBase', (0.045, 0.012, 0.09), (0.125, fy - 0.026, 0.03 + H * 0.30), 1, ms, 0.003))
parts.append(box('handle', (0.018, 0.04, 0.07), (0.125, fy - 0.048, 0.03 + H * 0.30), 1, ms, 0.004))
# ボルト（扉の四すみ）
for sx in (-1, 1):
    for sz in (-1, 1):
        parts.append(cyl('bolt', 0.007, 0.008, (sx * 0.17, fy - 0.022, 0.03 + H / 2 + sz * 0.175), 1, ms, 8))
join_export(parts, 'DialSafe', 'DialSafe.fbx')

# ---- ダイヤルのつまみ ----
new_scene()
ms = mats(['Brass', 'Black'])
parts = []
parts.append(cyl('knob', 0.058, 0.026, (0, -0.013, 0), 0, ms, 40))
parts.append(cyl('cap', 0.022, 0.012, (0, -0.032, 0), 1, ms, 24))
# ふちのギザギザ（24本）
for i in range(24):
    a = i * 2 * math.pi / 24
    o = box('rib', (0.008, 0.026, 0.012), (math.cos(a) * 0.060, -0.013, math.sin(a) * 0.060), 0, ms, 0.001)
    o.rotation_euler = (0, -a, 0)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    parts.append(o)
# 目盛り（100分割のうち 10ごとに太い印）：つまみの面に、黒い小さな箱で
for i in range(20):
    a = i * 2 * math.pi / 20
    big = (i % 5 == 0)
    o = box('tick', (0.004, 0.003, 0.016 if big else 0.010), (math.cos(a) * 0.043, -0.0275, math.sin(a) * 0.043), 1, ms, 0.0005)
    o.rotation_euler = (0, -a + math.pi / 2, 0)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    parts.append(o)
join_export(parts, 'SafeDial', 'SafeDial.fbx')
