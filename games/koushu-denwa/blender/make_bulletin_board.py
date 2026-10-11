"""
掲示板（本番版）を作る（Blender用）。メートル単位。足元（地面）の中央が原点、おもて面は -Y 向き（Unrealでは +Y 向き）。
  板5枚（すきま・反り・厚みのばらつき）／柱2本（地面の下までのびる）／ふち4本／屋根（細い板6枚＋ささえ）／釘／うしろの補強
  UVは「0.5m で1回くりかえし」の大きさをそろえた箱投影。木目は横向き（柱だけ縦向き）。
出力：assets/unreal/BulletinBoard.fbx（材質の穴は2つ：0=木、1=金属）   使い方：python make_bulletin_board.py
"""
import bpy, bmesh, math, os, random
from mathutils import Vector

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.path.expanduser('~')
OUT = os.path.normpath(os.path.join(HERE, '..', 'assets', 'unreal'))
os.makedirs(OUT, exist_ok=True)
random.seed(714)
bpy.ops.wm.read_factory_settings(use_empty=True)

wood = bpy.data.materials.new('Wood')
metal = bpy.data.materials.new('Metal')
parts = []


def finish_uv(o, vertical=False, tile=0.5):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            p = l.vert.co + o.location
            if ax == 0:
                u, v = p.y, p.z
            elif ax == 1:
                u, v = p.x, p.z
            else:
                u, v = p.x, p.y
            if vertical:
                u, v = v, u
            l[uv].uv = (u / tile, v / tile)
    bm.to_mesh(o.data)
    bm.free()


def box(name, size, loc, mat=wood, bevel=0.004, jitter=0.0015, rot=(0, 0, 0), vertical=False):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        m = o.modifiers.new('bev', 'BEVEL')
        m.width = bevel
        m.segments = 2
        m.limit_method = 'NONE'
        bpy.ops.object.modifier_apply(modifier='bev')
    if jitter > 0 and mat is wood:
        for v in o.data.vertices:
            v.co += Vector((random.uniform(-jitter, jitter), random.uniform(-jitter, jitter), random.uniform(-jitter, jitter)))
    o.location = loc
    o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    o.data.materials.append(mat)
    if mat is wood:
        o.data.materials.append(metal)          # 穴を2つに（join後も 0=木・1=金属 の順をそろえる）
    else:
        o.data.materials.append(wood)
        for p in o.data.polygons:
            p.material_index = 0
        o.data.materials.clear()
        o.data.materials.append(metal)
        o.data.materials.append(wood)
        for p in o.data.polygons:
            p.material_index = 0
    if mat is wood:
        for p in o.data.polygons:
            p.material_index = 0
    finish_uv(o, vertical)
    parts.append(o)
    return o


# 柱（うしろ側。地面の下 0.2m までのばす）
for sx in (-1, 1):
    box('post%d' % sx, (0.12, 0.12, 2.25), (sx * 1.05, 0.05, 0.925), bevel=0.006, vertical=True)
# 板5枚（z 0.70〜1.90）
for i in range(5):
    h = 0.236
    z = 0.70 + 0.12 + i * 0.24
    th = 0.04 + random.uniform(-0.004, 0.004)
    box('plank%d' % i, (2.18 + random.uniform(-0.01, 0.01), th, h), (random.uniform(-0.006, 0.006), random.uniform(-0.003, 0.003), z),
        rot=(random.uniform(-0.004, 0.004), 0, random.uniform(-0.004, 0.004)), bevel=0.003)
# ふち
box('frameTop', (2.34, 0.06, 0.09), (0, -0.025, 1.945), bevel=0.006)
box('frameBottom', (2.34, 0.06, 0.09), (0, -0.025, 0.655), bevel=0.006)
for sx in (-1, 1):
    box('frameSide%d' % sx, (0.09, 0.06, 1.32), (sx * 1.125, -0.025, 1.30), bevel=0.006, vertical=True)
# うしろの補強（横木と斜め）
box('backRail', (2.2, 0.035, 0.08), (0, 0.04, 1.30), bevel=0.003)
box('backBrace', (1.5, 0.03, 0.07), (0, 0.075, 1.0), rot=(0, math.radians(28), 0), bevel=0.003)
# 屋根：細い板6枚をななめに並べる（前が低い）＋ささえ
th = math.radians(10)
d = Vector((0, math.cos(th), math.sin(th)))
base = Vector((0, 0.02, 2.17))
for i in range(6):
    s = -0.30 + i * 0.12
    c = base + d * s
    box('roof%d' % i, (2.64, 0.115, 0.03), c, rot=(th, 0, 0), bevel=0.004)
box('fascia', (2.64, 0.03, 0.07), base + d * -0.37 + Vector((0, -0.01, -0.03)), rot=(th, 0, 0), bevel=0.003)
for sx in (-1, 1):
    box('bracket%d' % sx, (0.06, 0.55, 0.07), (sx * 1.05, 0.0, 2.10), bevel=0.004, rot=(th, 0, 0))
# 釘（金属）：板の左右のはし
for i in range(5):
    z = 0.70 + 0.12 + i * 0.24
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.009, depth=0.008, location=(sx * 1.0, -0.023, z))
        n = bpy.context.active_object
        n.rotation_euler = (math.radians(90), 0, 0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        n.data.materials.append(metal)
        n.data.materials.append(wood)
        n.name = 'nail'
        parts.append(n)
        for p in n.data.polygons:
            p.material_index = 0
bpy.ops.object.select_all(action='DESELECT')
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
o = bpy.context.active_object
o.name = 'BulletinBoard'
o.data.name = 'BulletinBoard'
bpy.ops.object.shade_smooth()
try:
    o.data.use_auto_smooth = True
except Exception:
    pass
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'BulletinBoard.fbx'), use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
                         path_mode='COPY', embed_textures=False, mesh_smooth_type='FACE', add_leaf_bones=False, bake_space_transform=True)
print('書き出しました: BulletinBoard.fbx  頂点=%d 面=%d  大きさ(m)=%s  材質の穴=%d' % (len(o.data.vertices), len(o.data.polygons), tuple(round(v, 2) for v in o.dimensions), len(o.data.materials)))
