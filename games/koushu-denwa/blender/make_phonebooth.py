"""
公衆電話ボックス＋緑の公衆電話機を作るBlender用スクリプト

【ひかるのパソコンで使うとき】
  1. Blender（無料・blender.org）を入れて起動
  2. 上の「Scripting」タブ → 「開く」でこのファイルを選ぶ → ▶（実行）
  3. 3D画面に電話ボックスが現れる。形や色を直したくなったら、下の数字を変えてもう一度実行
  4. 出力：games/koushu-denwa/assets/phonebooth.glb （ゲームが読み込む形式）

【Claudeのクラウドで使うとき】
  python make_phonebooth.py     （bpy を入れた環境）

単位はメートル。ゲーム側の大きさ（幅1.5m・高さ2.3m）に合わせてある。
名前：Door（蝶番が原点）、Booth_Frame、Booth_Glass、Booth_Roof、Phone、Phone_Handset、Phone_Cord
"""
import bpy, math, os, sys
import numpy as np

# ------------ 調整できる数字 ------------
BW = 1.5          # ボックスの幅（メートル）
BH = 2.3          # 高さ
RUST = 0.3        # さびの量 0〜1
DIRT = 0.5        # ガラスの汚れの量 0〜1
SEED = 19980714
# -----------------------------------------

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:                                   # BlenderのText画面から実行したとき
    HERE = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.path.expanduser('~')
OUT_DIR = os.path.normpath(os.path.join(HERE, '..', 'assets')) if os.path.basename(HERE) == 'blender' else os.path.join(HERE, 'assets')
os.makedirs(OUT_DIR, exist_ok=True)

rng = np.random.default_rng(SEED)
HALF = BW / 2

# ---------- 初期化 ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- 画像（さび・汚れ）を数字から作る ----------
def fbm(n, octaves=6):
    """雲のような自然なむらを作る（0〜1）"""
    out = np.zeros((n, n), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        g = 2 ** (o + 2)
        small = rng.random((g + 1, g + 1)).astype(np.float32)
        xs = np.linspace(0, g, n, endpoint=False)
        i = xs.astype(int); f = (xs - i); f = f * f * (3 - 2 * f)
        a = (small[i][:, i] * (1 - f)[:, None] + small[i + 1][:, i] * f[:, None]) * (1 - f)[None, :] \
            + (small[i][:, i + 1] * (1 - f)[:, None] + small[i + 1][:, i + 1] * f[:, None]) * f[None, :]
        out += a * amp; tot += amp; amp *= .5
    return out / tot

def make_image(name, arr, srgb=True):
    h, w = arr.shape[:2]
    if arr.ndim == 2: arr = np.stack([arr] * 3, -1)
    rgba = np.concatenate([arr, np.ones((h, w, 1), np.float32)], -1)
    img = bpy.data.images.new(name, w, h, alpha=False)
    img.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'    # 色の種類は先に決める（後だと絵が消える）
    img.pixels.foreach_set(np.ascontiguousarray(np.flipud(rgba), dtype=np.float32).ravel())
    img.update()
    img.pack()
    return img

N = 512
n1, n2, n3 = fbm(N), fbm(N), fbm(N, 8)
rust_mask = np.clip((n1 * 1.6 - .55 + RUST * .6) * 2.2, 0, 1) * np.clip(n2 * 1.4, 0, 1)
scratch = (rng.random((N, N)) > .9992).astype(np.float32)
green = np.array([.13, .36, .19], np.float32); rustc = np.array([.32, .13, .05], np.float32); dark = np.array([.05, .05, .045], np.float32)
paint = green[None, None] * (.75 + .5 * n3[..., None])
paint = paint * (1 - rust_mask[..., None]) + rustc[None, None] * (.6 + .8 * n2[..., None]) * rust_mask[..., None]
paint = paint * (1 - .35 * np.clip(fbm(N, 4) - .55, 0, 1)[..., None]) + scratch[..., None] * .3
paint_rough = np.clip(.45 + rust_mask * .45 + (n3 - .5) * .2, 0, 1)
img_paint = make_image('paint_color', np.clip(paint, 0, 1))
img_paint_r = make_image('paint_rough', paint_rough, srgb=False)
dirt = np.clip((fbm(N, 7) - .35) * 1.8 * DIRT * 1.6, 0, 1)
img_glass_r = make_image('glass_rough', np.clip(.04 + dirt * .8, 0, 1), srgb=False)
img_glass_c = make_image('glass_color', np.clip(np.stack([.8 - dirt * .4, .92 - dirt * .35, .88 - dirt * .5], -1), 0, 1))

# ---------- 材質 ----------
def new_mat(name, color=(.5, .5, .5), metallic=0., rough=.5, alpha=1., color_img=None, rough_img=None, emis=None, emis_s=0.):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Roughness'].default_value = rough
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        try: m.blend_method = 'BLEND'
        except Exception: pass
    if emis:
        b.inputs['Emission Color'].default_value = (*emis, 1); b.inputs['Emission Strength'].default_value = emis_s
    nt = m.node_tree
    def tex(img, target):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
        nt.links.new(t.outputs['Color'], b.inputs[target])
    if color_img: tex(color_img, 'Base Color')
    if rough_img: tex(rough_img, 'Roughness')
    return m

M_PAINT = new_mat('PaintGreen', metallic=.35, color_img=img_paint, rough_img=img_paint_r)
M_PAINT2 = new_mat('PhonePaint', (.2, .45, .25), metallic=.3, rough=.4)
M_GLASS = new_mat('Glass', (.8, .92, .88), rough=.03, alpha=.12, color_img=img_glass_c, rough_img=img_glass_r)
M_METAL = new_mat('Chrome', (.75, .75, .72), metallic=1., rough=.28)
M_BLACK = new_mat('BlackPlastic', (.015, .015, .015), rough=.35)
M_KEY = new_mat('KeyBeige', (.7, .68, .6), rough=.5)
M_GRAY = new_mat('GrayMetal', (.22, .23, .22), metallic=.6, rough=.55)
M_LCD = new_mat('LCD', (.02, .05, .02), rough=.2, emis=(.1, 1., .2), emis_s=.9)
M_PAPER = new_mat('Paper', (.75, .72, .6), rough=.9)

# ---------- 部品を作る道具 ----------
GROUPS = {}
def add_box(group, name, size, loc, mat, bevel=.004):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        m = o.modifiers.new('bv', 'BEVEL'); m.width = min(bevel, min(size) * .45); m.segments = 2
    o.data.materials.append(mat)
    GROUPS.setdefault(group, []).append(o); return o

def add_cyl(group, name, r, depth, loc, mat, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name
    o.data.materials.append(mat); bpy.ops.object.shade_smooth()
    GROUPS.setdefault(group, []).append(o); return o

def join(group, final_name, origin=None):
    objs = GROUPS[group]
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    for o in objs:                                   # 面取りを確定してから合体
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    res = bpy.context.active_object; res.name = final_name
    if origin is not None:
        scene.cursor.location = origin
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return res

FRONT = -HALF     # 正面（プレイヤー側）は -Y、奥の壁は +Y

# ================= 枠（柱・横の桟・ネジ） =================
for sx in (-1, 1):
    for sy in (-1, 1):
        add_box('frame', 'post', (.09, .09, BH), (sx * HALF, sy * HALF, BH / 2), M_PAINT, .008)
rails_z = [.06, .95, 1.5, BH - .03]
for z in rails_z:
    add_box('frame', 'rail_back', (BW, .06, .07), (0, HALF, z), M_PAINT, .006)
    for sx in (-1, 1):
        add_box('frame', 'rail_side', (.06, BW, .07), (sx * HALF, 0, z), M_PAINT, .006)
add_box('frame', 'rail_front_top', (BW, .06, .07), (0, FRONT, BH - .03), M_PAINT, .006)
add_box('frame', 'sill_front', (BW - .1, .1, .05), (0, FRONT, .025), M_GRAY, .004)      # 足もとの敷居
for z in rails_z:                                # ネジ
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_cyl('frame', 'bolt', .009, .01, (sx * HALF * 1.0, sy * (HALF - .0), z), M_METAL, rot=(math.pi / 2, 0, 0), verts=10)
# 天井の明かり受け
add_box('frame', 'light_housing', (.6, .24, .05), (0, 0, BH - .05), M_GRAY, .008)
add_box('frame', 'light_cover', (.52, .18, .02), (0, 0, BH - .085), M_KEY, .004)

# ================= ガラス =================
panes = [(.09, .92), (.98, 1.47), (1.53, BH - .07)]
for (z0, z1) in panes:
    h = z1 - z0; zc = (z0 + z1) / 2
    add_box('glass', 'pane_back', (BW - .1, .012, h), (0, HALF - .01, zc), M_GLASS, 0)
    for sx in (-1, 1):
        add_box('glass', 'pane_side', (.012, BW - .1, h), (sx * (HALF - .01), 0, zc), M_GLASS, 0)

# ================= 屋根 =================
add_box('roof', 'roof_main', (BW + .3, BW + .3, .12), (0, 0, BH + .06), M_PAINT, .02)
add_box('roof', 'roof_lip', (BW + .36, BW + .36, .03), (0, 0, BH + .015), M_PAINT, .01)
add_box('roof', 'roof_top', (BW - .1, BW - .1, .05), (0, 0, BH + .145), M_PAINT, .015)

# ================= ドア（蝶番が原点） =================
HINGE = (-HALF + .02, FRONT, 0)
DW = BW - .05
def dbox(name, size, off, mat, bevel=.005):
    return add_box('door', name, size, (HINGE[0] + off[0], HINGE[1] + off[1], off[2]), mat, bevel)
dbox('d_v1', (.08, .05, BH - .1), (.04, 0, (BH - .1) / 2 + .05), M_PAINT, .006)
dbox('d_v2', (.08, .05, BH - .1), (DW - .04, 0, (BH - .1) / 2 + .05), M_PAINT, .006)
for z in (.08, .95, BH - .08):
    dbox('d_h', (DW, .05, .08), (DW / 2, 0, z), M_PAINT, .006)
for (z0, z1) in ((.12, .91), (.99, BH - .12)):
    dbox('d_glass', (DW - .14, .012, z1 - z0), (DW / 2, 0, (z0 + z1) / 2), M_GLASS, 0)
# 取っ手（縦の金属バー）と鍵穴板
dbox('d_hplate', (.05, .012, .5), (DW - .1, -.03, 1.05), M_GRAY, .003)
add_cyl('door', 'd_hbar', .014, .42, (HINGE[0] + DW - .1, HINGE[1] - .07, 1.05), M_METAL)
add_cyl('door', 'd_hpost1', .008, .06, (HINGE[0] + DW - .1, HINGE[1] - .04, .88), M_METAL, rot=(math.pi / 2, 0, 0), verts=12)
add_cyl('door', 'd_hpost2', .008, .06, (HINGE[0] + DW - .1, HINGE[1] - .04, 1.22), M_METAL, rot=(math.pi / 2, 0, 0), verts=12)
for z in (.35, 1.2, 2.05):                       # 蝶番
    add_cyl('door', 'd_hinge', .014, .12, (HINGE[0] - .01, HINGE[1], z), M_METAL, verts=12)

# ================= 電話機（奥の壁） =================
PY = HALF - .16          # 本体の奥行き位置
PZ = 1.18
add_box('phone', 'wall_plate', (.5, .02, .82), (0, HALF - .02, PZ - .05), M_GRAY, .006)
add_box('phone', 'p_body', (.36, .22, .56), (0, PY, PZ), M_PAINT2, .02)
add_box('phone', 'p_top', (.38, .24, .04), (0, PY, PZ + .29), M_PAINT2, .015)
face_y = PY - .11
add_box('phone', 'lcd', (.2, .008, .07), (0, face_y - .003, PZ + .2), M_LCD, .002)
add_box('phone', 'keyplate', (.22, .01, .27), (0, face_y - .002, PZ + .02), M_BLACK, .004)
for r in range(4):
    for c in range(3):
        add_box('phone', 'key', (.05, .012, .036), ((c - 1) * .064, face_y - .009, PZ + .1 - r * .058), M_KEY, .006)
add_box('phone', 'coin_slot', (.11, .014, .05), (0.0, face_y - .004, PZ - .17), M_METAL, .005)
add_box('phone', 'coin_return', (.08, .014, .035), (0.0, face_y - .004, PZ - .23), M_BLACK, .004)
# 棚と電話帳
add_box('phone', 'shelf', (.42, .42, .03), (0, HALF - .22, .86), M_GRAY, .006)
add_box('phone', 'directory', (.24, .06, .3), (0, HALF - .28, .86 + .17), M_PAPER, .004).rotation_euler = (math.radians(-12), 0, 0)
add_cyl('phone', 'directory_chain', .004, .3, (.13, HALF - .28, .78), M_METAL, verts=8)

# ================= 受話器 =================
HX = -.235
HYc = face_y - .055
for name, z, r, d in (('h_ear', PZ + .13, .04, .06), ('h_mouth', PZ - .13, .04, .06)):
    add_cyl('handset', name, r, d, (HX, HYc, z), M_BLACK, rot=(0, 0, 0), verts=24)
add_cyl('handset', 'h_grip', .022, .26, (HX, HYc, PZ), M_BLACK, verts=20)
add_box('handset', 'h_cradle', (.045, .05, .3), (HX, face_y - .025, PZ), M_GRAY, .006)

# ================= コード（曲がった金属コード） =================
bpy.ops.curve.primitive_bezier_curve_add()
cv = bpy.context.active_object; cv.name = 'Phone_Cord'
sp = cv.data.splines[0]
pts = [(HX, HYc, PZ - .16), (HX - .06, HYc - .06, PZ - .3), (HX + .02, HYc - .1, PZ - .42), (HX + .1, PZ * 0 + face_y - .02, PZ - .25)]
sp.bezier_points.add(len(pts) - 2)
for bp, p in zip(sp.bezier_points, pts):
    bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
cv.data.bevel_depth = .006; cv.data.bevel_resolution = 4; cv.data.resolution_u = 24
cv.data.materials.append(M_GRAY)
bpy.ops.object.select_all(action='DESELECT'); cv.select_set(True); bpy.context.view_layer.objects.active = cv
bpy.ops.object.convert(target='MESH')
cord = bpy.context.active_object

# ================= 合体して名前をつける =================
frame = join('frame', 'Booth_Frame')
glass = join('glass', 'Booth_Glass')
roof = join('roof', 'Booth_Roof')
door = join('door', 'Door', origin=HINGE)
phone = join('phone', 'Phone')
handset = join('handset', 'Phone_Handset')
cord.name = 'Phone_Cord'
for o in (frame, glass, roof, door, phone, handset, cord):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
bpy.ops.object.shade_flat() if False else None

# ---------- 見た目の確認用の光（ゲームには出力されない設定でもOK） ----------
if '--nolight' not in sys.argv:
    bpy.ops.object.light_add(type='POINT', location=(0, 0, BH - .2)); L = bpy.context.active_object
    L.data.energy = 60; L.data.color = (.85, 1., .85); L.name = 'PreviewLight'

# ---------- 書き出し ----------
glb = os.path.join(OUT_DIR, 'phonebooth.glb')
for o in bpy.data.objects: o.select_set(o.type == 'MESH')
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                          export_image_format='JPEG', export_jpeg_quality=85)
# ファイルを直接開いても読めるように、文字の形にした版も作る
import base64
with open(glb, 'rb') as f: b64 = base64.b64encode(f.read()).decode()
with open(os.path.join(OUT_DIR, 'phonebooth.glb.js'), 'w') as f:
    f.write('window.PHONEBOOTH_GLB_B64="' + b64 + '";\n')
print('書き出しました:', glb, os.path.getsize(glb) // 1024, 'KB')

# ---------- 確認画像（Blenderの絵作り。時間がかかるので省略可: --norender） ----------
if '--norender' not in sys.argv:
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 32; scene.cycles.device = 'CPU'
    scene.render.resolution_x, scene.render.resolution_y = 640, 800
    bpy.ops.object.camera_add(location=(1.9, -3.3, 1.6), rotation=(math.radians(80), 0, math.radians(30)))
    scene.camera = bpy.context.active_object
    scene.world = bpy.data.worlds.new('w'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.02, .025, .03, 1)
    bpy.ops.object.light_add(type='AREA', location=(2.5, -2.5, 3)); A = bpy.context.active_object; A.data.energy = 300; A.data.size = 3
    A.rotation_euler = (math.radians(50), 0, math.radians(40))
    scene.render.filepath = os.path.join(OUT_DIR, 'phonebooth_preview.png')
    bpy.ops.render.render(write_still=True)
    print('確認画像:', scene.render.filepath)
