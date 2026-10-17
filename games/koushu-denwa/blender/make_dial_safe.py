"""
手提げ金庫（昭和の「HAND SAFE」：木目プリントの鉄の箱＋上の取っ手＋銘板＋ダイヤルのつまみ）を作る（Blender用）。メートル単位。
  DialSafe.fbx … 本体（幅0.36 × 奥行き0.24 × 高さ0.17m。足元が原点。おもて面は -Y 向き＝Unrealでは +Y 向き）
                 材質の穴：0=木目プリント 1=ニッケル（取っ手・ねじ・ちょうつがい） 2=銘板 3=黒（すきま・ダイヤル受け・足）
  SafeDial.fbx … ダイヤルのつまみ（中心が原点。Unrealで Pitch（Y軸まわり）で回す）  穴：0=ニッケル 1=黒
  つまみの位置（本体の原点から・メートル）：右へ +0.04、前へ 0.134、高さ 0.060
  DialSafeBase.fbx … 「開いた金庫」の下の箱（上が開いて、中に黒赤の内張り）。DialSafe.fbx と同じ原点・同じ向き
  DialSafeLid.fbx  … 「開いた金庫」のふた（取っ手・銘板つき）。原点＝うしろのちょうつがい（本体の原点から：うしろへ D/2・高さ SEAM）。Unrealで Roll（X軸まわり）で開く
  SafeKey.fbx … 金庫の中の小さな鍵（真鍮。ふちの輪＋軸＋ギザギザ。平らに置ける向き。長さ6cm、中心が原点）
使い方：python make_dial_safe.py     出力：assets/unreal/DialSafe.fbx, SafeDial.fbx, DialSafeBase.fbx, DialSafeLid.fbx, SafeKey.fbx
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
W, D, H = 0.36, 0.24, 0.17
Z0 = 0.010                     # 足の高さ
SEAM = 0.104                   # ふたの合わせ目の高さ


def new_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mats(names):
    return [bpy.data.materials.new(n) for n in names]


def finish_uv(o, tile):
    """木目用：箱投影。1枚の画像が tile メートル。横方向に木目が流れる"""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            p = l.vert.co
            if ax == 0:
                u, v = p.y, p.z
            elif ax == 1:
                u, v = p.x, p.z
            else:
                u, v = p.x, p.y
            l[uv].uv = (u / tile, v / tile)
    bm.to_mesh(o.data)
    bm.free()


def plate_uv(o):
    """銘板用：前（-Y）の面に、画像をそのまま貼る（0〜1）"""
    xs = [v.co.x for v in o.data.vertices]
    zs = [v.co.z for v in o.data.vertices]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for l in f.loops:
            p = l.vert.co
            l[uv].uv = ((p.x - x0) / (x1 - x0), (p.z - z0) / (z1 - z0))
    bm.to_mesh(o.data)
    bm.free()


def finish(o, ms, mi, bevel=0.0, loc=None, rot=None, jitter=0.0):
    if bevel > 0:
        m = o.modifiers.new('b', 'BEVEL')
        m.width = bevel
        m.segments = 3
        m.limit_method = 'NONE'
        bpy.ops.object.modifier_apply(modifier='b')
    if jitter > 0:
        for v in o.data.vertices:
            v.co += Vector((random.uniform(-jitter, jitter), random.uniform(-jitter, jitter), random.uniform(-jitter, jitter)))
    if rot is not None:
        o.rotation_euler = rot
    if loc is not None:
        o.location = loc
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for m in ms:
        o.data.materials.append(m)
    for p in o.data.polygons:
        p.material_index = mi
    return o


def box(name, size, loc, mi, ms, bevel=0.002, rot=None, jitter=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, ms, mi, bevel, loc, rot, jitter)


def cyl(name, r, depth, loc, mi, ms, verts=24, axis='Y', bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth)
    o = bpy.context.active_object
    o.name = name
    if axis == 'Y':
        o.rotation_euler = (math.radians(90), 0, 0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    return finish(o, ms, mi, bevel, loc)


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


# ================= 本体 =================
new_scene()
ms = mats(['Wood', 'Nickel', 'Plate', 'Black'])
parts = []
fy = -D / 2
# 下の箱とふた（合わせ目に 3mm のすきま）。木目は箱投影
low = box('low', (W, D, SEAM - Z0 - 0.002), (0, 0, Z0 + (SEAM - Z0 - 0.002) / 2), 0, ms, 0.004)
finish_uv(low, 0.36)
lid_h = H - SEAM - 0.002 + Z0
lid = box('lid', (W + 0.002, D + 0.002, lid_h), (0, 0, SEAM + 0.002 + lid_h / 2), 0, ms, 0.014)
finish_uv(lid, 0.36)
parts += [low, lid]
parts.append(box('gap', (W - 0.012, D - 0.012, 0.012), (0, 0, SEAM), 3, ms, 0.0005))               # すきまの奥の黒
for sx in (-1, 1):
    for sy in (-1, 1):
        parts.append(box('foot', (0.03, 0.03, Z0), (sx * 0.15, sy * 0.095, Z0 / 2), 3, ms, 0.002))
top = Z0 + (SEAM - Z0 - 0.002) + 0.002 + lid_h
# 取っ手（上。ニッケルの曲がった棒と、2本の柱）
for sx in (-1, 1):
    parts.append(cyl('post', 0.0075, 0.022, (sx * 0.055, 0.0, top + 0.009), 1, ms, 14, 'Z', 0.001))
    parts.append(cyl('postCap', 0.011, 0.005, (sx * 0.055, 0.0, top + 0.002), 1, ms, 14, 'Z', 0.001))
parts.append(box('barMid', (0.082, 0.011, 0.007), (0, 0, top + 0.027), 1, ms, 0.0025))
for sx in (-1, 1):
    parts.append(box('barEnd', (0.034, 0.011, 0.007), (sx * 0.066, 0.0, top + 0.022), 1, ms, 0.0025, rot=(0, sx * math.radians(-28), 0)))
# 銘板（ふたの前の面に、右よりに）
plate = box('plate', (0.115, 0.004, 0.045), (0.065, fy - 0.003, SEAM + 0.040), 2, ms, 0.0005)
plate_uv(plate)
parts.append(plate)
# ダイヤル受け（黒いエナメルの板＋ニッケルの縁）
DX, DZ = 0.04, 0.060
parts.append(box('escutcheon', (0.085, 0.010, 0.085), (DX, fy - 0.005, DZ), 3, ms, 0.008))
parts.append(cyl('ring', 0.037, 0.004, (DX, fy - 0.012, DZ), 1, ms, 36))
# 前の両はし：丸い鍵穴のふた（黒＋ニッケルの円盤）
for sx in (-1, 1):
    parts.append(cyl('plug', 0.017, 0.006, (sx * 0.145, fy - 0.003, 0.050), 3, ms, 20))
    parts.append(cyl('plugDisc', 0.011, 0.004, (sx * 0.145, fy - 0.008, 0.050), 1, ms, 20))
# うしろのちょうつがい
for sx in (-1, 1):
    parts.append(box('hinge', (0.045, 0.010, 0.02), (sx * 0.11, D / 2 + 0.003, SEAM + 0.001), 1, ms, 0.002))
# ふたの前の左右のかど当て
for sx in (-1, 1):
    parts.append(box('corner', (0.016, 0.006, 0.05), (sx * (W / 2 - 0.008), fy - 0.002, SEAM + 0.04), 1, ms, 0.002))
join_export(parts, 'DialSafe', 'DialSafe.fbx')

# ================= ダイヤルのつまみ =================
new_scene()
ms = mats(['Nickel', 'Black'])
parts = []
parts.append(cyl('knob', 0.027, 0.018, (0, -0.009, 0), 0, ms, 40, 'Y', 0.002))
parts.append(cyl('top', 0.020, 0.004, (0, -0.020, 0), 0, ms, 32, 'Y', 0.001))
for i in range(6):                                              # 面の6つの穴（黒）
    a = i * 2 * math.pi / 6
    parts.append(cyl('hole', 0.0045, 0.003, (math.cos(a) * 0.012, -0.0235, math.sin(a) * 0.012), 1, ms, 10))
parts.append(cyl('center', 0.0045, 0.004, (0, -0.0235, 0), 1, ms, 10))
for i in range(30):                                              # ふちのギザギザ
    a = i * 2 * math.pi / 30
    o = box('rib', (0.0035, 0.018, 0.005), (math.cos(a) * 0.0275, -0.009, math.sin(a) * 0.0275), 0, ms, 0.0003, rot=(0, -a, 0))
    parts.append(o)
join_export(parts, 'SafeDial', 'SafeDial.fbx')


# ================= 開いた金庫：下の箱（上が開いている）=================
def translate_parts(parts, d):
    for o in parts:
        for v in o.data.vertices:
            v.co += Vector(d)


T = 0.012                                    # 壁の厚さ
new_scene()
ms = mats(['Wood', 'Nickel', 'Plate', 'Black', 'Inner'])
parts = []
low_h = SEAM - Z0 - 0.002
zc = Z0 + low_h / 2
bottom = box('bottom', (W, D, T), (0, 0, Z0 + T / 2), 0, ms, 0.003)
finish_uv(bottom, 0.36)
parts.append(bottom)
for sx in (-1, 1):                           # 左右の壁
    w_ = box('wallX', (T, D, low_h), (sx * (W / 2 - T / 2), 0, zc), 0, ms, 0.003)
    finish_uv(w_, 0.36)
    parts.append(w_)
for sy in (-1, 1):                           # 前・うしろの壁
    w_ = box('wallY', (W - 2 * T, T, low_h), (0, sy * (D / 2 - T / 2), zc), 0, ms, 0.003)
    finish_uv(w_, 0.36)
    parts.append(w_)
# 内張り（くすんだ赤黒。壁の内がわと底）
inn_h = low_h - T
parts.append(box('innerBottom', (W - 2 * T - 0.002, D - 2 * T - 0.002, 0.003), (0, 0, Z0 + T + 0.0015), 4, ms, 0.0005))
for sx in (-1, 1):
    parts.append(box('innerX', (0.003, D - 2 * T - 0.002, inn_h), (sx * (W / 2 - T - 0.0015), 0, Z0 + T + inn_h / 2), 4, ms, 0.0005))
for sy in (-1, 1):
    parts.append(box('innerY', (W - 2 * T - 0.002, 0.003, inn_h), (0, sy * (D / 2 - T - 0.0015), Z0 + T + inn_h / 2), 4, ms, 0.0005))
# ふちの金具（ニッケルの細いふち）と足
for sx in (-1, 1):                           # ふちの金具（ニッケルの細い枠。真ん中は開いている）
    parts.append(box('rimX', (0.004, D - 0.002, 0.003), (sx * (W / 2 - 0.002), 0, SEAM - 0.001), 1, ms, 0.0005))
for sy in (-1, 1):
    parts.append(box('rimY', (W - 0.002, 0.004, 0.003), (0, sy * (D / 2 - 0.002), SEAM - 0.001), 1, ms, 0.0005))
for sx in (-1, 1):
    for sy in (-1, 1):
        parts.append(box('foot', (0.03, 0.03, Z0), (sx * 0.15, sy * 0.095, Z0 / 2), 3, ms, 0.002))
# ダイヤル受け・鍵穴のふた・ちょうつがい（下の半分）：閉じた金庫と同じ位置
parts.append(box('escutcheon', (0.085, 0.010, 0.085), (DX, fy - 0.005, DZ), 3, ms, 0.008))
parts.append(cyl('ring', 0.037, 0.004, (DX, fy - 0.012, DZ), 1, ms, 36))
for sx in (-1, 1):
    parts.append(cyl('plug', 0.017, 0.006, (sx * 0.145, fy - 0.003, 0.050), 3, ms, 20))
    parts.append(cyl('plugDisc', 0.011, 0.004, (sx * 0.145, fy - 0.008, 0.050), 1, ms, 20))
    parts.append(box('hingeLow', (0.045, 0.010, 0.02), (sx * 0.11, D / 2 + 0.003, SEAM - 0.012), 1, ms, 0.002))
join_export(parts, 'DialSafeBase', 'DialSafeBase.fbx')

# ================= 開いた金庫：ふた（原点＝ちょうつがい）=================
new_scene()
ms = mats(['Wood', 'Nickel', 'Plate', 'Black', 'Inner'])
parts = []
lid_h = H - SEAM - 0.002 + Z0
lid = box('lid', (W + 0.002, D + 0.002, lid_h), (0, 0, SEAM + 0.002 + lid_h / 2), 0, ms, 0.014)
finish_uv(lid, 0.36)
parts.append(lid)
parts.append(box('lidInner', (W - 0.02, D - 0.02, 0.003), (0, 0, SEAM + 0.0035), 4, ms, 0.0005))      # ふたの裏の内張り
top = Z0 + (SEAM - Z0 - 0.002) + 0.002 + lid_h
for sx in (-1, 1):
    parts.append(cyl('post', 0.0075, 0.022, (sx * 0.055, 0.0, top + 0.009), 1, ms, 14, 'Z', 0.001))
    parts.append(cyl('postCap', 0.011, 0.005, (sx * 0.055, 0.0, top + 0.002), 1, ms, 14, 'Z', 0.001))
parts.append(box('barMid', (0.082, 0.011, 0.007), (0, 0, top + 0.027), 1, ms, 0.0025))
for sx in (-1, 1):
    parts.append(box('barEnd', (0.034, 0.011, 0.007), (sx * 0.066, 0.0, top + 0.022), 1, ms, 0.0025, rot=(0, sx * math.radians(-28), 0)))
plate = box('plate', (0.115, 0.004, 0.045), (0.065, fy - 0.003, SEAM + 0.040), 2, ms, 0.0005)
plate_uv(plate)
parts.append(plate)
for sx in (-1, 1):
    parts.append(box('hingeUp', (0.045, 0.010, 0.02), (sx * 0.11, D / 2 + 0.003, SEAM + 0.012), 1, ms, 0.002))
    parts.append(box('corner', (0.016, 0.006, 0.05), (sx * (W / 2 - 0.008), fy - 0.002, SEAM + 0.04), 1, ms, 0.002))
translate_parts(parts, (0, -D / 2, -SEAM))          # 原点を、うしろのちょうつがいに
join_export(parts, 'DialSafeLid', 'DialSafeLid.fbx')


# ================= 金庫の中の小さな鍵（床に平らに置く。長さ約6cm）=================
new_scene()
ms = mats(['Brass'])
parts = []
bpy.ops.mesh.primitive_torus_add(major_radius=0.0105, minor_radius=0.0038, major_segments=28, minor_segments=10, location=(0, 0, 0))
ring_ = bpy.context.active_object
ring_.name = 'bow'
parts.append(finish(ring_, ms, 0, 0.0, (-0.0235, 0, 0.0038)))
parts.append(box('shaft', (0.040, 0.0065, 0.0065), (0.0095, 0, 0.0033), 0, ms, 0.0012))
for i, (xx_, hh) in enumerate(((0.022, 0.011), (0.0285, 0.0075), (0.0125, 0.0085))):
    parts.append(box('bit%d' % i, (0.0045, hh, 0.0055), (xx_, -hh / 2 - 0.003, 0.003), 0, ms, 0.0008))
join_export(parts, 'SafeKey', 'SafeKey.fbx')
