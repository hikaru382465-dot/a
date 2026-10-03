"""
公衆電話ボックス（NTTの新しいタイプ）＋蛍光グリーンのデジタル公衆電話を作るBlender用スクリプト

【ひかるのパソコンで使うとき】
  1. Blender（無料・blender.org）を入れて起動
  2. 上の「Scripting」タブ → 「開く」でこのファイルを選ぶ → ▶（実行）
  3. 3D画面に電話ボックスが現れる。形や色を直したくなったら、下の数字を変えてもう一度実行
  4. 出力：games/koushu-denwa/assets/phonebooth.glb （ゲームが読み込む形式）

【Claudeのクラウドで使うとき】
  python make_phonebooth.py     （bpy を入れた環境）

単位はメートル。ゲーム側の大きさ（幅1.5m・高さ2.3m）に合わせてある。
名前：Door（蝶番が原点）、Booth_Frame、Booth_Glass、Booth_Roof、Phone、Phone_Handset、Phone_Cord
光る材質の名前：Tube（蛍光灯）、LCD（液晶）
"""
import bpy, math, os, sys
import numpy as np

# ------------ 調整できる数字 ------------
BW = 1.25         # ボックスの幅と奥行き（メートル。本物は約1m、ゲームで動けるよう少し広め）
BH = 2.3          # 高さ
AGE = float(os.environ.get('KD_AGE', '0.9'))   # 古びの強さ 0〜1（make_textures.py と同じ数字）
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
TEX_DIR = os.path.join(OUT_DIR, 'tex')
sys.path.insert(0, HERE)

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
# 青い料金案内板（青地に白い表）
info = np.zeros((160, 256, 3), np.float32); info[:] = (.05, .22, .55)
info[:22] = (.02, .12, .4); info[22:26] = (.9, .75, .1)
for r in range(6):
    y = 34 + r * 20
    info[y:y + 14, 10:246] = (.93, .95, .97)
    for c in range(1, 5): info[y:y + 14, 10 + c * 47:12 + c * 47] = (.05, .22, .55)
    info[y + 5:y + 8, 16:40] = (.1, .2, .5)
img_info = make_image('info_panel', np.clip(info + rng.normal(0, .015, info.shape).astype(np.float32), 0, 1))
def load_img(fname, srgb=True):
    im = bpy.data.images.load(os.path.join(TEX_DIR, fname), check_existing=True)
    im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'; im.pack(); return im
img_bronze = load_img('bronze_color.png'); img_bronze_r = load_img('bronze_rough.png', False)
img_glass_c = load_img('glass_color.png'); img_glass_r = load_img('glass_rough.png', False)
img_bronze_n = load_img('bronze_normal.png', False); img_gray_n = load_img('gray_paint_normal.png', False)
img_ceil_n = load_img('ceiling_normal.png', False); img_floor_n = load_img('floor_normal.png', False)
img_gray = load_img('gray_paint_color.png'); img_gray_r = load_img('gray_paint_rough.png', False)
img_ceil = load_img('ceiling_color.png'); img_floor = load_img('floor_color.png'); img_floor_r = load_img('floor_rough.png', False)

# ---------- 材質 ----------
def new_mat(name, color=(.5, .5, .5), metallic=0., rough=.5, alpha=1., color_img=None, rough_img=None, emis=None, emis_s=0., alpha_img=False, normal_img=None, normal_s=1.):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Roughness'].default_value = rough
    if alpha < 1 or alpha_img:
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
    if alpha_img and color_img:
        ta = [n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image == color_img][0]
        nt.links.new(ta.outputs['Alpha'], b.inputs['Alpha'])        # 汚れの濃いところは不透明に
    if rough_img: tex(rough_img, 'Roughness')
    if normal_img:
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = normal_s
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = normal_img
        nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m

M_BRONZE = new_mat('Bronze', metallic=.85, color_img=img_bronze, rough_img=img_bronze_r, normal_img=img_bronze_n, normal_s=1.2)
M_GLASS = new_mat('Glass', (.8, .92, .88), rough=.03, alpha=.12, color_img=img_glass_c, rough_img=img_glass_r, alpha_img=True)
M_GRAY = new_mat('GrayPaint', (.36, .37, .38), metallic=.25, rough=.55, color_img=img_gray, rough_img=img_gray_r, normal_img=img_gray_n, normal_s=1.2)
M_STEEL = new_mat('Steel', (.7, .7, .7), metallic=1., rough=.3)
M_BLACK = new_mat('BlackPlastic', (.015, .015, .015), rough=.35)
M_TUBE = new_mat('Tube', (.9, .9, .85), rough=.3, emis=(1., 1. - .2 * AGE, 1. - .45 * AGE), emis_s=3.)   # 古い蛍光灯は黄ばむ
M_CEIL = new_mat('Ceiling', (.75, .75, .72), rough=.7, color_img=img_ceil, normal_img=img_ceil_n)
M_FLOOR = new_mat('FloorConcrete', (.4, .4, .38), rough=.8, color_img=img_floor, rough_img=img_floor_r, normal_img=img_floor_n, normal_s=1.3)
M_INFO = new_mat('InfoPanel', color_img=load_img('info_panel.png'), rough=.4)
M_CAUTION = new_mat('CautionSticker', color_img=load_img('caution_sticker.png'), rough=.5)
M_BOOK = [new_mat('Book%d' % i, tuple(v * (1 - .5 * AGE) for v in c), rough=.9) for i, c in enumerate([(.1, .2, .55), (.75, .65, .15), (.8, .8, .78), (.15, .35, .2)])]   # 古い電話帳は色あせて暗い

# ---------- 部品を作る道具 ----------
GROUPS = {}
def add_box(group, name, size, loc, mat, bevel=.004, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = size
    if rot: o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True, rotation=bool(rot))
    if bevel:
        m = o.modifiers.new('bv', 'BEVEL'); m.width = min(bevel, min(size) * .45); m.segments = 2
    o.data.materials.append(mat)
    GROUPS.setdefault(group, []).append(o); return o

def add_cyl(group, name, r, depth, loc, mat, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name
    o.data.materials.append(mat); bpy.ops.object.shade_smooth()
    GROUPS.setdefault(group, []).append(o); return o

def add_plane(group, name, size, loc, mat, rot):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    GROUPS.setdefault(group, []).append(o); return o

def join(group, final_name, origin=None):
    objs = GROUPS[group]
    for o in bpy.context.selected_objects: o.select_set(False)
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
POST = .06

# ================= 枠（ブロンズ色のアルミ） =================
for sx in (-1, 1):
    for sy in (-1, 1):
        add_box('frame', 'post', (POST, POST, BH), (sx * HALF, sy * HALF, BH / 2), M_BRONZE, .006)
# 足もとの幅木（3面）と、前の敷居
add_box('frame', 'kick_back', (BW, .05, .12), (0, HALF, .07), M_BRONZE, .004)
for sx in (-1, 1):
    add_box('frame', 'kick_side', (.05, BW, .12), (sx * HALF, 0, .07), M_BRONZE, .004)
add_box('frame', 'sill_front', (BW - .1, .12, .05), (0, FRONT, .025), M_GRAY, .004)
# 上の帯（ヘッダー）
add_box('frame', 'header_back', (BW, .05, .15), (0, HALF, BH - .075), M_BRONZE, .004)
for sx in (-1, 1):
    add_box('frame', 'header_side', (.05, BW, .15), (sx * HALF, 0, BH - .075), M_BRONZE, .004)
add_box('frame', 'header_front', (BW, .1, .17), (0, FRONT, BH - .085), M_BRONZE, .006)
# 外側の台座（鉄の台）
for (sz, loc) in (((BW + .1, .05, .06), (0, HALF + .05, .03)), ((BW + .1, .05, .06), (0, FRONT - .05, .03)),
                  ((.05, BW + .1, .06), (-HALF - .05, 0, .03)), ((.05, BW + .1, .06), (HALF + .05, 0, .03))):
    add_box('frame', 'plinth', sz, loc, M_GRAY, .004)
# 床（コンクリート。落ち葉・泥・ひび）
add_box('frame', 'floor', (BW - .08, BW - .08, .036), (0, 0, .02), M_FLOOR, .002)
# 天井（白っぽい板）と蛍光灯2本
add_box('frame', 'ceiling', (BW - .08, BW - .08, .03), (0, 0, BH - .17), M_CEIL, .004)
for sx in (-1, 1):
    add_cyl('frame', 'tube', .02, .85, (sx * .27, 0, BH - .2), M_TUBE, rot=(math.pi / 2, 0, 0), verts=14)
    add_box('frame', 'tube_holder', (.06, .07, .02), (sx * .27, .45, BH - .19), M_GRAY, .003)
    add_box('frame', 'tube_holder', (.06, .07, .02), (sx * .27, -.45, BH - .19), M_GRAY, .003)
# 角のゴムのふち（黒）
for sx in (-1, 1):
    for sy in (-1, 1):
        add_box('frame', 'gasket', (.012, .012, BH - .3), (sx * (HALF - POST / 2 - .006), sy * (HALF - POST / 2 - .006), BH / 2 - .02), M_BLACK, 0)

# ================= ガラス（下は幅木の上から、上はヘッダーの下まで） =================
GZ0, GZ1 = .13, BH - .16
gh = GZ1 - GZ0; gzc = (GZ0 + GZ1) / 2
add_box('glass', 'pane_back', (BW - POST, .01, gh), (0, HALF - .01, gzc), M_GLASS, 0)
for sx in (-1, 1):
    add_box('glass', 'pane_side', (.01, BW - POST, gh), (sx * (HALF - .01), 0, gzc), M_GLASS, 0)

# ================= 屋根 =================
add_box('roof', 'roof_main', (BW + .22, BW + .22, .1), (0, 0, BH + .05), M_BRONZE, .015)
add_box('roof', 'roof_cap', (BW + .1, BW + .1, .05), (0, 0, BH + .125), M_BRONZE, .01)
add_cyl('roof', 'antenna', .008, .9, (HALF - .15, HALF - .15, BH + .55), M_STEEL, verts=8)

# ================= ドア（ガラスの折りたたみドアに見える形。蝶番が原点） =================
HINGE = (-HALF + .02, FRONT, 0)
DW = BW - .05
def dbox(name, size, off, mat, bevel=.004):
    return add_box('door', name, size, (HINGE[0] + off[0], HINGE[1] + off[1], off[2]), mat, bevel)
DZ0, DZ1 = .1, BH - .17
dh = DZ1 - DZ0
for x in (.025, DW / 2 - .02, DW / 2 + .02, DW - .025):      # 縦の枠（中央は2本で折り目に見える）
    dbox('d_v', (.04, .045, dh), (x, 0, DZ0 + dh / 2), M_BRONZE, .004)
for z in (DZ0 + .04, DZ1 - .04):
    dbox('d_h', (DW, .045, .08), (DW / 2, 0, z), M_BRONZE, .004)
dbox('d_glassL', (DW / 2 - .085, .008, dh - .1), (DW / 4 - .005, 0, DZ0 + dh / 2), M_GLASS, 0)
dbox('d_glassR', (DW / 2 - .085, .008, dh - .1), (DW * .75 + .005, 0, DZ0 + dh / 2), M_GLASS, 0)
# 引き手（縦のステンレスの棒）
add_cyl('door', 'd_pull', .012, .5, (HINGE[0] + DW / 2 + .1, HINGE[1] - .06, 1.05), M_STEEL)
for z in (.85, 1.25):
    add_cyl('door', 'd_pullpost', .007, .05, (HINGE[0] + DW / 2 + .1, HINGE[1] - .035, z), M_STEEL, rot=(math.pi / 2, 0, 0), verts=10)
# 蝶番
for z in (.35, 1.2, 2.0):
    add_cyl('door', 'd_hinge', .012, .1, (HINGE[0] - .008, HINGE[1], z), M_STEEL, verts=10)

# ================= 奥の壁：灰色の柱・青い料金案内板・台 =================
PILLAR_Y = HALF - .12                 # 柱の中心
PF = PILLAR_Y - .10                   # 柱の手前の面（電話機はここに取り付く）
add_box('phone', 'pillar', (.4, .2, 1.4), (0, PILLAR_Y, .78 + .7), M_GRAY, .006)
add_box('phone', 'pillar_cap', (.42, .22, .03), (0, PILLAR_Y, 2.17), M_GRAY, .004)
for sx in (-1, 1):                    # 柱の下の脚
    add_box('phone', 'leg', (.04, .04, .78), (sx * .17, PILLAR_Y, .39), M_GRAY, .004)
# 青い料金案内板（少し前に傾ける）
tilt = math.radians(-12)
add_box('phone', 'info_frame', (.5, .035, .32), (0, PF - .02, 1.86), M_GRAY, .004, rot=(tilt, 0, 0))
add_plane('phone', 'info_face', (.46, .28), (0, PF - .0435, 1.86), M_INFO, rot=(math.pi / 2 + tilt, 0, 0))
# 右側の灰色の台（電話帳）と、足のせ
add_box('phone', 'desk', (.42, .42, .03), (.41, HALF - .23, .95), M_GRAY, .005)
add_box('phone', 'desk_lip', (.42, .02, .05), (.41, HALF - .445, .965), M_GRAY, .004)
add_box('phone', 'desk_leg', (.03, .03, .93), (.58, HALF - .05, .47), M_GRAY, .003)
add_box('phone', 'desk_leg', (.03, .03, .93), (.58, HALF - .4, .47), M_GRAY, .003)
for i, m_ in enumerate(M_BOOK):
    add_box('phone', 'book', (.2 - i * .015, .26, .035), (.42, HALF - .25, .985 + i * .037), m_, .003, rot=(0, 0, math.radians(i * 7 - 8)))
add_box('phone', 'footrest', (.4, .04, .03), (0, HALF - .09, .28), M_GRAY, .004)
# 注意シール（右の壁のガラスの内側）
add_plane('phone', 'caution', (.22, .33), (HALF - .022, -.05, 1.5), M_CAUTION, rot=(math.pi / 2, 0, -math.pi / 2))

# ================= 電話機（実物の写真を見本にした、別スクリプトの部品） =================
import phone_builder
phone_parts = phone_builder.build_phone(TEX_DIR, (0, PF, 1.0))

# ================= 合体して名前をつける =================
frame = join('frame', 'Booth_Frame')
glass = join('glass', 'Booth_Glass')
roof = join('roof', 'Booth_Roof')
door = join('door', 'Door', origin=HINGE)
phone = join('phone', 'Booth_Interior')

# ---------- 見た目の確認用の光（ゲームには出力されない設定でもOK） ----------
if '--nolight' not in sys.argv:
    bpy.ops.object.light_add(type='POINT', location=(0, 0, BH - .2)); L = bpy.context.active_object
    L.data.energy = 60; L.data.color = (.85, 1., .85); L.name = 'PreviewLight'

# ---------- 書き出し ----------
glb = os.path.join(OUT_DIR, 'phonebooth.glb')
for o in bpy.data.objects: o.select_set(o.type == 'MESH')
# Unreal Engine 用（FBX。1単位=1メートルのまま。画像も中に入れる）
UE_DIR = os.path.join(OUT_DIR, 'unreal'); os.makedirs(UE_DIR, exist_ok=True)
bpy.ops.export_scene.fbx(filepath=os.path.join(UE_DIR, 'PhoneBooth.fbx'), use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
                         path_mode='COPY', embed_textures=True, mesh_smooth_type='FACE', add_leaf_bones=False, bake_space_transform=True)
print('Unreal用:', os.path.join(UE_DIR, 'PhoneBooth.fbx'))
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_image_format='AUTO')
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
    bpy.ops.object.camera_add(location=(1.7, -3.0, 1.5), rotation=(math.radians(82), 0, math.radians(30)))
    scene.camera = bpy.context.active_object
    scene.world = bpy.data.worlds.new('w'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.02, .025, .03, 1)
    bpy.ops.object.light_add(type='AREA', location=(2.5, -2.5, 3)); A = bpy.context.active_object; A.data.energy = 300; A.data.size = 3
    A.rotation_euler = (math.radians(50), 0, math.radians(40))
    scene.render.filepath = os.path.join(OUT_DIR, 'phonebooth_preview.png')
    bpy.ops.render.render(write_still=True)
    # 電話機のアップ
    from mathutils import Vector
    bpy.ops.object.camera_add(location=(.42, -.42, 1.42))
    cam2 = bpy.context.active_object
    cam2.rotation_euler = (Vector((0, .25, 1.2)) - cam2.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam2; scene.render.resolution_x, scene.render.resolution_y = 800, 900
    scene.render.filepath = os.path.join(OUT_DIR, 'phone_preview.png')
    bpy.ops.render.render(write_still=True)
    # 正面（受話器の向きの確認用）
    bpy.ops.object.camera_add(location=(-.12, -.5, 1.22))
    cam3 = bpy.context.active_object
    cam3.rotation_euler = (Vector((0, .3, 1.2)) - cam3.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam3
    scene.render.filepath = os.path.join(OUT_DIR, 'phone_front.png')
    bpy.ops.render.render(write_still=True)
    print('確認画像:', scene.render.filepath)
