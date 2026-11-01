"""暗証番号の張り紙パズル（光る数字）の見た目確認用プレビューを作る。
本物のUnrealゲームではなく、Blenderで電話ボックスの中から見た絵を描くだけ。
使い方: /d/blender.exe -b --python render_code_preview.py   （環境変数 KD_ONLY=1,lit のように絞れる）
出力: assets/code_preview_1..4.png（暗い間）, code_preview_lit.png（明るい間）
その後 make_code_preview_sheet.py（同じ場所）でまとめ画像を作る。
"""
import bpy, os, math, random
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, '..', 'assets'))
TEX = os.path.join(ASSETS, 'tex', 'game')
SAMPLES = int(os.environ.get('KD_SAMPLES', '80'))
ONLY = os.environ.get('KD_ONLY', '1,2,3,4,lit').split(',')

W, H = 0.52, 0.73
# 張り紙: (ガラス文字, 光る数字, 位置, 回転z)  ※ i番目に貼った紙が数字i（仮の番号 3-6-1-8）
POSTERS = [
    ('glass_03', 'glass_glow_3', (0.585, 0.27, 1.30), 90),     # 右の壁・奥
    ('glass_05', 'glass_glow_6', (-0.585, -0.27, 1.30), -90),  # 左の壁・手前
    ('glass_07', 'glass_glow_1', (0.0, -0.545, 1.30), 180),    # 扉
    ('glass_10', 'glass_glow_8', (0.585, -0.30, 1.30), 90),    # 右の壁・手前
]
FLIP = float(os.environ.get('KD_FLIP', '0'))   # 文字が裏返るとき 180 にする

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, 'phonebooth.glb'))


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m


def poster_mat(name):
    """透明PNG。色×strengthで光る(emission) + 少し拡散"""
    m = new_mat(name)
    nt = m.node_tree
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(TEX, name + '.png'), check_existing=True)
    t.image.colorspace_settings.name = 'sRGB'
    t.interpolation = 'Cubic'
    t.extension = 'CLIP'
    em = nt.nodes.new('ShaderNodeEmission')
    df = nt.nodes.new('ShaderNodeBsdfDiffuse')
    add = nt.nodes.new('ShaderNodeAddShader')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    L = nt.links.new
    L(t.outputs['Color'], em.inputs['Color'])
    L(t.outputs['Color'], df.inputs['Color'])
    L(em.outputs[0], add.inputs[0])
    L(df.outputs[0], add.inputs[1])
    L(t.outputs['Alpha'], mix.inputs[0])
    L(tr.outputs[0], mix.inputs[1])
    L(add.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs['Surface'])
    return m, em, df


def quad(name, loc, rotz, mat):
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.object
    o.name = name
    o.scale = (W, H, 1)
    # 平面を立てる(法線が -Y を向く)→ z回転で壁の向きに合わせる
    o.rotation_euler = (math.radians(90), 0, math.radians(rotz + FLIP))
    o.location = loc
    o.data.materials.append(mat)
    o.visible_shadow = False
    return o


posters = []
for i, (g, d, loc, rz) in enumerate(POSTERS):
    mt, et, dt = poster_mat(g)
    mg, eg, dg = poster_mat(d)
    iv = Vector((-loc[0], -loc[1], 0))
    iv.normalize()
    to = quad(f'Poster{i+1}', loc, rz, mt)
    go = quad(f'Digit{i+1}', (loc[0] + iv.x * 0.01, loc[1] + iv.y * 0.01, loc[2]), rz, mg)
    posters.append((to, go, et, eg, dt, dg))

# 外の森: 暗い幹と地面
tm = new_mat('trunk')
b = tm.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
b.inputs[0].default_value = (.03, .028, .024, 1)
o = tm.node_tree.nodes.new('ShaderNodeOutputMaterial')
tm.node_tree.links.new(b.outputs[0], o.inputs[0])
random.seed(7)
for k in range(30):
    a = random.uniform(0, math.tau)
    r = random.uniform(2.0, 9)
    bpy.ops.mesh.primitive_cylinder_add(radius=random.uniform(.12, .3), depth=14,
                                        location=(math.cos(a) * r, math.sin(a) * r, 6))
    bpy.context.object.data.materials.append(tm)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.02))
bpy.context.object.data.materials.append(tm)

sc.world = bpy.data.worlds.new('w')
sc.world.use_nodes = True
bg = sc.world.node_tree.nodes['Background']

lamp = bpy.data.lights.new('tube', 'AREA')
lamp.shape = 'RECTANGLE'
lamp.size = 0.9
lamp.size_y = 0.08
lo = bpy.data.objects.new('tube', lamp)
sc.collection.objects.link(lo)
lo.location = (0, 0.0, 2.1)
moon = bpy.data.lights.new('moon', 'SUN')
moon.color = (.55, .65, 1)
mo = bpy.data.objects.new('moon', moon)
sc.collection.objects.link(mo)
mo.rotation_euler = (math.radians(50), 0, math.radians(30))

for m in bpy.data.materials:
    if m.use_nodes and m.name.startswith('Glass'):
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs['Alpha'].default_value = 0.2
                n.inputs['Roughness'].default_value = 0.08
    if m.use_nodes and m.name == 'Tube':
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs['Emission Strength'].default_value = 0.0

# カメラ: ボックスの奥・左の角、目の高さ160cm、広角
cam = bpy.data.cameras.new('cam')
cam.sensor_width = 36
cam.lens = float(os.environ.get('KD_LENS', '11'))
cam.clip_start = 0.01
co = bpy.data.objects.new('cam', cam)
sc.collection.objects.link(co)
sc.camera = co
co.location = (-0.22, 0.12, 1.58)
tgt = Vector((0.10, -0.45, 1.25))
co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 8
sc.cycles.transmission_bounces = 8
sc.cycles.transparent_max_bounces = 16
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'None'

# コンポジタ: ブルーム風グレア
sc.use_nodes = True
nt = sc.node_tree
nt.nodes.clear()
rl = nt.nodes.new('CompositorNodeRLayers')
gl = nt.nodes.new('CompositorNodeGlare')
gl.glare_type = 'FOG_GLOW'
gl.quality = 'HIGH'
gl.threshold = 1.0
gl.size = 8
out = nt.nodes.new('CompositorNodeComposite')
nt.links.new(rl.outputs['Image'], gl.inputs['Image'])
nt.links.new(gl.outputs['Image'], out.inputs['Image'])

TXT_DARK = float(os.environ.get('KD_TXT_DARK', '0.01'))
DIGIT = float(os.environ.get('KD_DIGIT', '2.2'))
LAMP = float(os.environ.get('KD_LAMP', '14'))


def setup(phase):
    """phase: '1'..'4' = 暗い間, 'lit' = 明るい間"""
    lit = phase == 'lit'
    k = 4 if lit else int(phase)
    for i, (to, go, et, eg, dt, dg) in enumerate(posters):
        et.inputs['Strength'].default_value = 0.3 if lit else TXT_DARK
        dt.inputs['Color'].default_value = (1, 1, 1, 1)
        eg.inputs['Strength'].default_value = DIGIT
        dg.inputs['Color'].default_value = (0, 0, 0, 1)
        go.hide_render = lit or i >= k
    lamp.energy = LAMP if lit else 0.0
    lamp.color = (.8, 1.0, .85)
    moon.energy = 0.0 if lit else 0.03
    bg.inputs['Color'].default_value = (0.004, 0.006, 0.012, 1)
    bg.inputs['Strength'].default_value = 1.0
    sc.view_settings.exposure = 0.3 if lit else 0.0


for ph in ONLY:
    setup(ph)
    sc.render.filepath = os.path.join(ASSETS, f'code_preview_{ph}.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED', sc.render.filepath)
