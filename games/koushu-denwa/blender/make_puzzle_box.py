"""
金庫の中に入っている「ボタン16個の箱」（昭和のからくり箱。黒い漆の木箱＋真鍮のかど金具＋象牙色のボタン）を作る（Blender用）。メートル単位。
  PuzzleBox.fbx … 大きさ 0.19(X) × 0.17(Y) × 約0.062(Z)。平らに置く。原点＝箱の底の真ん中。おもて面は -Y 向き（Unrealでは +Y 向き）
                  材質の穴：0=Lacquer（漆） 1=Brass（真鍮） 2=ButtonIvory（ボタン。数字の絵つき） 3=Black（ボタンの受け）
  画像（assets/tex/game/）… puzzlebox_buttons.png（1024。4×4のマスに1〜16）／puzzlebox_buttons_rough.png（つや）
ボタンの並び：上（+Z）から、手前（金庫の前）から見て、左上が1、右へ 2,3,4、そのうしろ…手前の列が 13〜16。1〜4が奥の列。
ゲームに必要な数字（実行すると画面にも出る）：ボタンの上面の高さ・間隔 0.032m・列の中心は箱の中心。
  ボタン n（1〜16）の中心：x = ((n-1)%4 - 1.5)*0.032 、 y = (1.5 - (n-1)//4)*0.032 （箱の原点から。y が + ＝奥）
画像は PIL を使わず、Blender の numpy だけで描く（手書き風の線で数字を引く）。
使い方：blender -b --python make_puzzle_box.py   （Blenderの「スクリプト」画面からも実行できる）
出力：assets/unreal/PuzzleBox.fbx、assets/puzzlebox_preview.png、assets/puzzlebox_in_safe.png
"""
import bpy, bmesh, math, os, random, struct, zlib
import numpy as np
from mathutils import Vector

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.path.expanduser('~')
ASSETS = os.path.normpath(os.path.join(HERE, '..', 'assets'))
OUT = os.path.join(ASSETS, 'unreal')
TEX = os.path.join(ASSETS, 'tex', 'game')
for d in (OUT, TEX):
    os.makedirs(d, exist_ok=True)
RENDER = True                  # False にすると書き出しだけ（画像の確認をはぶく）
random.seed(31)

W, D, H = 0.19, 0.17, 0.055    # 箱の本体
SEAM = 0.0355                  # ふたの合わせ目の高さ
PITCH = 0.032                  # ボタンの間隔
CAP = 0.026                    # ボタンの一辺
PANEL_Z = 0.055                # 漆のふたの上面
SLAB_TOP = 0.0565              # ボタンの受け（黒）の上面
CAP_H = 0.0055                 # ボタンの高さ
CAP_TOP = SLAB_TOP + CAP_H     # ボタンの上面（ゲームのクリック面の高さ）
BTN_TEX = os.path.join(TEX, 'puzzlebox_buttons.png')
BTN_ROUGH = os.path.join(TEX, 'puzzlebox_buttons_rough.png')


def new_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mats(names):
    return [bpy.data.materials.new(n) for n in names]


# ================= 数字の画像（numpy だけ）=================
def _smooth(rng, n, s):
    """やわらかいムラ（0〜1）"""
    a = rng.standard_normal((n, n))
    f = np.fft.fftfreq(n)
    g = np.exp(-((f[None, :] * s) ** 2 + (f[:, None] * s) ** 2) * 60.0)
    r = np.real(np.fft.ifft2(np.fft.fft2(a) * g))
    return (r - r.min()) / (r.max() - r.min() + 1e-9)


def _ell(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


# 数字の線（x 0〜0.6、y 0〜1、上が+y）。いくつかの折れ線
_six = [(0.5, 0.95), (0.2, 0.8), (0.03, 0.45), (0.05, 0.15), (0.3, 0.0), (0.55, 0.15), (0.55, 0.4), (0.3, 0.55), (0.05, 0.4)]
DIGITS = {
    '0': [_ell(0.3, 0.5, 0.28, 0.5, 0, 360, 20)],
    '1': [[(0.12, 0.75), (0.32, 1.0), (0.32, 0.0)], [(0.1, 0.0), (0.55, 0.0)]],
    '2': [[(0.0, 0.78), (0.1, 0.95), (0.3, 1.0), (0.5, 0.95), (0.6, 0.78), (0.5, 0.6), (0.0, 0.0), (0.6, 0.0)]],
    '3': [[(0.0, 0.9), (0.3, 1.0), (0.55, 0.88), (0.5, 0.62), (0.25, 0.52), (0.55, 0.42), (0.6, 0.15), (0.3, 0.0), (0.0, 0.1)]],
    '4': [[(0.45, 0.0), (0.45, 1.0), (0.0, 0.3), (0.62, 0.3)]],
    '5': [[(0.55, 1.0), (0.08, 1.0), (0.03, 0.55), (0.3, 0.62), (0.55, 0.5), (0.6, 0.2), (0.35, 0.0), (0.0, 0.1)]],
    '6': [_six],
    '7': [[(0.0, 1.0), (0.6, 1.0), (0.2, 0.0)]],
    '8': [_ell(0.3, 0.76, 0.21, 0.24, 0, 360, 16), _ell(0.3, 0.27, 0.28, 0.27, 0, 360, 16)],
    '9': [[(0.6 - x, 1.0 - y) for x, y in _six]],
}


def draw_digit(P, ch, cx, cy, h, rng, ang):
    """P: (n,n,2) 画素の座標（右が+x、下が+y）。1つの数字の線までの近さ（0〜1）"""
    best = np.full(P.shape[:2], 1e9)
    ca, sa = math.cos(ang), math.sin(ang)
    for stroke in DIGITS[ch]:
        pts = []
        for x, y in stroke:
            x += rng.normal(0, 0.012)
            y += rng.normal(0, 0.012)
            px, py = (x - 0.3) * h, -(y - 0.5) * h
            pts.append((cx + px * ca - py * sa, cy + px * sa + py * ca))
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            dx, dy = x1 - x0, y1 - y0
            L2 = dx * dx + dy * dy + 1e-9
            t = np.clip(((P[..., 0] - x0) * dx + (P[..., 1] - y0) * dy) / L2, 0, 1)
            d = np.hypot(P[..., 0] - (x0 + t * dx), P[..., 1] - (y0 + t * dy))
            best = np.minimum(best, d)
    return best


def write_png(path, arr):
    """numpy の (高さ, 幅, 3) の 0〜1 を、8bit の PNG に書く（PILなし。Blenderの画像保存は使わない）"""
    a = (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)
    h, w = a.shape[:2]
    raw = b''.join(b'\x00' + a[y].tobytes() for y in range(h))

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def make_textures():
    """4×4のマスに 1〜16 を書いた象牙色の画像と、つやの画像を保存する"""
    N, C = 1024, 256
    rng = np.random.default_rng(1964)
    yy, xx = np.mgrid[0:C, 0:C].astype(float)
    P = np.stack([xx, yy], axis=-1)
    col = np.zeros((N, N, 3))
    rough = np.zeros((N, N))
    big_low = _smooth(rng, N, 14.0)
    big_mid = _smooth(rng, N, 50.0)
    big_hi = rng.random((N, N))
    ivory = np.array([0.80, 0.73, 0.57])
    stain = np.array([0.52, 0.38, 0.20])
    for k in range(16):
        r, c = divmod(k, 4)
        sl = (slice(r * C, (r + 1) * C), slice(c * C, (c + 1) * C))
        low, mid, hi = big_low[sl], big_mid[sl], big_hi[sl]
        base = ivory[None, None, :] * (0.88 + 0.22 * mid[..., None])
        base = base * (1 - 0.18 * (low[..., None] > 0.66)) + stain * 0.18 * (low[..., None] > 0.66) * (0.5 + 0.5 * mid[..., None])
        edge = np.minimum(np.minimum(xx, C - 1 - xx), np.minimum(yy, C - 1 - yy)) / (C / 2)
        grime = np.clip(1.0 - edge * 3.2, 0, 1) ** 1.5                      # ふちほど黒ずむ（指の汚れ）
        base = base * (1 - 0.5 * grime[..., None]) + np.array([0.25, 0.17, 0.08]) * 0.2 * grime[..., None]
        base *= (0.95 + 0.1 * hi[..., None])
        # 数字
        s = str(k + 1)
        h = 150 if len(s) == 1 else 128
        ink = np.zeros((C, C))
        for i, ch in enumerate(s):
            off = 0 if len(s) == 1 else (i - 0.5) * h * 0.72
            cx = C / 2 + off + rng.normal(0, 3)
            cy = C / 2 + rng.normal(0, 3)
            d = draw_digit(P, ch, cx, cy, h, rng, math.radians(rng.normal(0, 4)))
            w = 8.5 + rng.normal(0, 0.6)
            ink = np.maximum(ink, np.clip((w - d) / 3.0 + 0.5, 0, 1))
        fade = np.clip(0.62 + 0.9 * (mid - 0.5) + 0.3 * (hi - 0.5), 0.45, 1.0)  # かすれ
        ink *= fade
        inkcol = np.array([0.06, 0.04, 0.035])
        base = base * (1 - ink[..., None]) + inkcol * ink[..., None]
        col[sl] = base
        rough[sl] = 0.58 + 0.12 * (1 - mid) + 0.25 * ink + 0.1 * grime
    col = np.clip(col, 0, 1)
    rough = np.clip(rough, 0, 1)
    write_png(BTN_TEX, col)
    write_png(BTN_ROUGH, np.repeat(rough[..., None], 3, axis=2))
    print('画像を保存しました:', BTN_TEX)


# ================= 材質 =================
def principled(m):
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return nt, bsdf


def setup_materials(ms):
    """ms = [Lacquer, Brass, ButtonIvory, Black]"""
    lac, brass, ivory, black = ms
    # 漆：黒茶。うすい凹凸
    nt, b = principled(lac)
    n1 = nt.nodes.new('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = 350.0
    n2 = nt.nodes.new('ShaderNodeTexNoise')
    n2.inputs['Scale'].default_value = 6.0
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (0.012, 0.007, 0.005, 1)
    mix.inputs['B'].default_value = (0.05, 0.026, 0.016, 1)
    nt.links.new(n2.outputs['Fac'], mix.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.3
    bump.inputs['Distance'].default_value = 0.001
    nt.links.new(n1.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.35
    # 真鍮：すり減った金色
    nt, b = principled(brass)
    n3 = nt.nodes.new('ShaderNodeTexNoise')
    n3.inputs['Scale'].default_value = 60.0
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (0.36, 0.22, 0.06, 1)
    mix.inputs['B'].default_value = (0.62, 0.45, 0.15, 1)
    nt.links.new(n3.outputs['Fac'], mix.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.45
    # ボタン：画像
    nt, b = principled(ivory)
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(BTN_TEX)
    t.image.colorspace_settings.name = 'sRGB'
    r = nt.nodes.new('ShaderNodeTexImage')
    r.image = bpy.data.images.load(BTN_ROUGH)
    r.image.colorspace_settings.name = 'Non-Color'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(r.outputs['Color'], b.inputs['Roughness'])
    # 黒
    nt, b = principled(black)
    b.inputs['Base Color'].default_value = (0.006, 0.006, 0.007, 1)
    b.inputs['Roughness'].default_value = 0.8


# ================= 形の道具（make_dial_safe.py と同じ形）=================
def box_uv(o, tile):
    """箱投影。1枚の画像が tile メートル"""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            p = l.vert.co
            u, v = ((p.y, p.z), (p.x, p.z), (p.x, p.y))[ax]
            l[uv].uv = (u / tile, v / tile)
    bm.to_mesh(o.data)
    bm.free()


def cap_uv(o, cx, cy, row, col):
    """ボタンの上面を、画像の自分のマス（row 行 col 列。上から数える）にそのまま貼る。ほかの面はマスの下のほうの無地"""
    hw = CAP / 2 - 0.0015
    u0, v0 = col / 4.0, 1.0 - (row + 1) / 4.0
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        top = f.normal.z > 0.99
        for l in f.loops:
            p = l.vert.co
            if top:
                l[uv].uv = (u0 + (p.x - cx + hw) / (2 * hw) * 0.25, v0 + (p.y - cy + hw) / (2 * hw) * 0.25)
            else:
                l[uv].uv = (u0 + 0.125, v0 + 0.015)
    bm.to_mesh(o.data)
    bm.free()


def finish(o, ms, mi, bevel=0.0, loc=None, rot=None, jitter=0.0, seg=3):
    if bevel > 0:
        m = o.modifiers.new('b', 'BEVEL')
        m.width = bevel
        m.segments = seg
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


def box(name, size, loc, mi, ms, bevel=0.0008, rot=None, jitter=0.0, seg=3, uv=True):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(o, ms, mi, bevel, loc, rot, jitter, seg)
    if uv:
        box_uv(o, 0.2)
    return o


def cyl(name, r, depth, loc, mi, ms, verts=20, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth)
    o = bpy.context.active_object
    o.name = name
    finish(o, ms, mi, bevel, loc)
    box_uv(o, 0.2)
    return o


def join(parts, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    o.data.name = name
    bpy.ops.object.shade_smooth()
    return o


def btn_center(n):
    """ボタン n（1〜16）の中心 (x, y)。y が + ＝奥"""
    r, c = divmod(n - 1, 4)
    return (c - 1.5) * PITCH, (1.5 - r) * PITCH


# ================= 箱を作る =================
def build_box():
    ms = mats(['Lacquer', 'Brass', 'ButtonIvory', 'Black'])
    setup_materials(ms)
    parts = []
    # 本体：下の箱とふた。合わせ目に 1mm のすきまと、奥の黒
    low_h = SEAM - 0.0005
    parts.append(box('low', (W, D, low_h), (0, 0, low_h / 2), 0, ms, 0.0025, jitter=0.0003))
    lid_h = H - SEAM - 0.0005
    parts.append(box('lid', (W - 0.001, D - 0.001, lid_h), (0, 0, H - lid_h / 2), 0, ms, 0.0025, jitter=0.0003))
    parts.append(box('gap', (W - 0.006, D - 0.006, 0.003), (0, 0, SEAM), 3, ms, 0.0003))
    # 真鍮のかど金具（8かど）
    g = 0.022
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (0, 1):
                z0 = 0.0 if sz == 0 else H - g
                parts.append(box('guard', (g + 0.0012, g + 0.0012, g), (sx * (W / 2 - g / 2 + 0.0006), sy * (D / 2 - g / 2 + 0.0006), z0 + g / 2),
                                 1, ms, 0.0028, jitter=0.0002))
    # ボタンの板：真鍮のふち、黒い受け、漆の仕切り
    rim_o, rim_i = 0.1385, 0.1300
    rz = 0.0026
    for s in (-1, 1):
        parts.append(box('rimY', (rim_o, (rim_o - rim_i) / 2, rz), (0, s * (rim_o + rim_i) / 4, PANEL_Z + rz / 2 - 0.0002), 1, ms, 0.0005, seg=2))
        parts.append(box('rimX', ((rim_o - rim_i) / 2, rim_i, rz), (s * (rim_o + rim_i) / 4, 0, PANEL_Z + rz / 2 - 0.0002), 1, ms, 0.0005, seg=2))
    parts.append(box('slab', (rim_i, rim_i, SLAB_TOP - PANEL_Z), (0, 0, (SLAB_TOP + PANEL_Z) / 2 - 0.0003), 3, ms, 0.0002, seg=1))
    lat_h = 0.0015
    for i in (-1, 0, 1):
        for rot90 in (False, True):
            size = (0.003, rim_i, lat_h) if not rot90 else (rim_i, 0.003, lat_h)
            loc = (i * PITCH, 0, SLAB_TOP + lat_h / 2 - 0.0002) if not rot90 else (0, i * PITCH, SLAB_TOP + lat_h / 2 - 0.0002)
            parts.append(box('lat', size, loc, 0, ms, 0.0004, seg=1))
    # ボタン16個（上面を画像のマスに貼る）
    for n in range(1, 17):
        cx, cy = btn_center(n)
        r, c = divmod(n - 1, 4)
        cap = box('cap%02d' % n, (CAP, CAP, CAP_H), (cx, cy, SLAB_TOP + CAP_H / 2), 2, ms, 0.0015, seg=2, uv=False)
        cap_uv(cap, cx, cy, r, c)
        parts.append(cap)
    # おもての真鍮の板（ぼんやりした、読めない彫り）
    fy = -D / 2 - 0.0008
    parts.append(box('plate', (0.052, 0.0022, 0.016), (0, fy, 0.018), 1, ms, 0.0004, seg=2))
    for i, (ww, dx) in enumerate(((0.030, -0.004), (0.022, 0.0), (0.034, -0.002))):
        parts.append(box('eng%d' % i, (ww, 0.0004, 0.0007), (dx, fy - 0.0012, 0.0215 - i * 0.0036), 3, ms, 0.0001, seg=1))
    return join(parts, 'PuzzleBox')


def export_box(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'PuzzleBox.fbx'), use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
                             path_mode='AUTO', embed_textures=False, mesh_smooth_type='FACE', add_leaf_bones=False, bake_space_transform=True)
    print('書き出しました: PuzzleBox.fbx  頂点=%d  大きさ(m)=%s  材質の穴=%d' % (len(o.data.vertices), tuple(round(v, 3) for v in o.dimensions), len(o.data.materials)))
    print('ボタンの上面の高さ(原点から)=%.4f m  漆のふた上面=%.4f m  黒い受けの面=%.4f m  間隔=%.3f m  1番=(%.3f, %.3f)  16番=(%.3f, %.3f)'
          % (CAP_TOP, PANEL_Z, SLAB_TOP, PITCH, *btn_center(1), *btn_center(16)))


# ================= プレビュー =================
def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def add_light(name, kind, loc, target, energy, color, size):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == 'AREA':
        ld.size = size
    o = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(o)
    o.location = loc
    look_at(o, target)
    return o


def setup_render(path, cam_loc, target, lens, key, fill, rim, samples=64):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = 1280, 960
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'Filmic' if 'Filmic' in bpy.types.ColorManagedViewSettings.bl_rna.properties['view_transform'].enum_items.keys() else 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    w = bpy.data.worlds.new('w')
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.004, 0.005, 0.008, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
    sc.world = w
    cd = bpy.data.cameras.new('cam')
    cd.lens = lens
    cam = bpy.data.objects.new('cam', cd)
    bpy.context.collection.objects.link(cam)
    cam.location = cam_loc
    look_at(cam, target)
    sc.camera = cam
    add_light('Key', 'AREA', key[0], target, key[1], (1.0, 0.72, 0.45), key[2])
    add_light('Fill', 'AREA', fill[0], target, fill[1], (0.55, 0.65, 1.0), fill[2])
    add_light('Rim', 'AREA', rim[0], target, rim[1], (0.6, 0.75, 1.0), rim[2])
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('画像を保存しました:', path)


def simple_mat(name, color, metallic=0.0, rough=0.6):
    m = bpy.data.materials.new(name)
    nt, b = principled(m)
    b.inputs['Base Color'].default_value = color
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Roughness'].default_value = rough
    return m


def preview_alone():
    new_scene()
    o = build_box()
    ground = simple_mat('ground', (0.025, 0.022, 0.02, 1), 0.0, 0.85)
    bpy.ops.mesh.primitive_plane_add(size=3)
    g = bpy.context.active_object
    g.data.materials.append(ground)
    setup_render(os.path.join(ASSETS, 'puzzlebox_preview.png'),
                 (0.12, -0.32, 0.26), (0, -0.005, 0.03), 50,
                 ((-0.32, -0.30, 0.42), 7, 0.25), ((0.40, -0.35, 0.25), 0.6, 0.4), ((0.15, 0.42, 0.20), 6, 0.2))


def preview_in_safe():
    new_scene()
    base_path = os.path.join(OUT, 'DialSafeBase.fbx')
    lid_path = os.path.join(OUT, 'DialSafeLid.fbx')
    objs = []
    for p in (base_path, lid_path):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=p)
        new = [x for x in bpy.data.objects if x not in before]
        meshes = [x for x in new if x.type == 'MESH']
        for x in new:
            print('取り込み:', x.name, x.type, tuple(round(v, 3) for v in x.dimensions), x.location[:], tuple(round(math.degrees(a), 1) for a in x.rotation_euler))
        bpy.ops.object.select_all(action='DESELECT')
        meshes[0].select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)     # 取り込みで付く90度の回転を形に焼く
        print('  焼いたあとの大きさ:', tuple(round(v, 3) for v in meshes[0].dimensions))
        objs.append(meshes[0])
    base, lid = objs
    # 金庫の色
    cols = {'Wood': ((0.16, 0.085, 0.04, 1), 0.0, 0.5), 'Nickel': ((0.55, 0.55, 0.57, 1), 1.0, 0.3), 'Plate': ((0.02, 0.02, 0.02, 1), 0.0, 0.5),
            'Black': ((0.01, 0.01, 0.01, 1), 0.0, 0.8), 'Inner': ((0.12, 0.012, 0.016, 1), 0.0, 0.7)}
    for ob in (base, lid):
        for slot in ob.material_slots:
            key = slot.material.name.split('.')[0]
            c, mt, rg = cols.get(key, ((0.3, 0.3, 0.3, 1), 0.0, 0.6))
            slot.material = simple_mat('s_' + key, c, mt, rg)
    # ふたを後ろへ開く（蝶番＝ふたの原点）
    lid.rotation_mode = 'XYZ'
    lid.location = (0, 0.12, 0.104)
    lid.rotation_euler = (math.radians(-105), 0, 0)
    # 箱を、内側の底に置く
    o = build_box()
    o.location = (0, 0.0, 0.025)
    ground = simple_mat('ground', (0.03, 0.025, 0.02, 1), 0.0, 0.85)
    bpy.ops.mesh.primitive_plane_add(size=3)
    gp = bpy.context.active_object
    gp.data.materials.append(ground)
    setup_render(os.path.join(ASSETS, 'puzzlebox_in_safe.png'),
                 (0.12, -0.38, 0.40), (0, 0.02, 0.07), 50,
                 ((-0.35, -0.35, 0.50), 7, 0.25), ((0.45, -0.30, 0.25), 0.8, 0.4), ((0.10, 0.60, 0.35), 8, 0.25))


make_textures()
new_scene()
_o = build_box()
export_box(_o)
if RENDER:
    preview_alone()
    preview_in_safe()
