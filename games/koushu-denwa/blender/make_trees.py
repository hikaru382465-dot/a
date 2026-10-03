"""
森の木・岩を作るBlender用スクリプト（夜の森向けの、暗いシルエットが主役のモデル）

作るもの：松（3種）、枯れ木（2種）、切り株、岩（2種）
出力：games/koushu-denwa/assets/unreal/Trees.fbx （Unreal Engine 用。画像は中に入る）

使い方：
  Blender の「Scripting」タブで開いて ▶（実行）。または  python make_trees.py [--norender]
単位はメートル。各部品の原点は「根もと」。
"""
import bpy, math, os, sys, random
from mathutils import Vector

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.path.expanduser('~')
OUT = os.path.normpath(os.path.join(HERE, '..', 'assets')) if os.path.basename(HERE) == 'blender' else os.path.join(HERE, 'assets')
TEX = os.path.join(OUT, 'tex'); UE = os.path.join(OUT, 'unreal')
os.makedirs(UE, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
R = random.Random(1998)

def load(f, srgb=True):
    im = bpy.data.images.load(os.path.join(TEX, f), check_existing=True)
    im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'; im.pack(); return im

def mat(name, color_f, normal_f, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; b.inputs['Roughness'].default_value = rough
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = load(color_f); nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.0
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = load(normal_f, False)
    nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m

M_BARK = mat('Bark', 'bark_color.png', 'bark_normal.png', .92)
M_LEAF = mat('Leaves', 'leaves_color.png', 'leaves_normal.png', .9)
M_ROCK = mat('Rock', 'rock_color.png', 'rock_normal.png', .88)

def cone(parts, start, direction, length, r1, r2, verts, material, jitter=0.0):
    d = Vector(direction).normalized()
    mid = Vector(start) + d * length / 2
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=length, location=mid)
    o = bpy.context.active_object
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    if jitter:
        for v in o.data.vertices:                      # 形をいびつにする
            v.co += Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))) * jitter
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    parts.append(o); return o

def join(parts, name):
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name; o.data.name = name
    scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return o

def pine(name, H, tiers, spread):
    parts = []
    lean = Vector((R.uniform(-.03, .03), R.uniform(-.03, .03), 1))
    cone(parts, (0, 0, 0), lean, H, .30 * H / 10, .07, 10, M_BARK, jitter=.01)
    for k in range(tiers):
        t = k / max(1, tiers - 1)
        z = H * (.24 + .74 * t)
        r = (2.5 - 2.0 * t) * spread * R.uniform(.85, 1.15)
        h = (3.4 - 1.4 * t) * spread * R.uniform(.9, 1.15)
        c = cone(parts, (R.uniform(-.1, .1), R.uniform(-.1, .1), z), (R.uniform(-.08, .08), R.uniform(-.08, .08), 1), h, r, 0.0, 12, M_LEAF, jitter=.12 * spread)
    return join(parts, name)

def dead_tree(name, H, depth):
    parts = []
    def branch(p, d, L, r, dep):
        c = cone(parts, p, d, L, r, r * .55, 7, M_BARK, jitter=.005)
        if dep == 0: return
        tip = Vector(p) + Vector(d).normalized() * L
        for _ in range(R.choice([2, 3])):
            nd = Vector(d).normalized() + Vector((R.uniform(-.9, .9), R.uniform(-.9, .9), R.uniform(-.1, .5)))
            branch(tip - Vector(d).normalized() * L * .15, nd, L * R.uniform(.6, .8), r * .55, dep - 1)
    branch((0, 0, 0), (R.uniform(-.06, .06), R.uniform(-.06, .06), 1), H, .28, depth)
    # 低い位置にも枝を出す
    for z in (H * .45, H * .6):
        a = R.uniform(0, math.tau); branch((0, 0, z), (math.cos(a), math.sin(a), .5), H * .35, .1, 1)
    return join(parts, name)

def stump(name):
    parts = []
    cone(parts, (0, 0, 0), (0, 0, 1), .75, .46, .38, 12, M_BARK, jitter=.03)
    for _ in range(4):                                         # 根っこ
        a = R.uniform(0, math.tau); cone(parts, (math.cos(a) * .3, math.sin(a) * .3, .05), (math.cos(a), math.sin(a), -.2), .6, .12, .04, 6, M_BARK)
    return join(parts, name)

def rock(name, size, squash):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1, location=(0, 0, 0))
    o = bpy.context.active_object
    for v in o.data.vertices:                                  # でこぼこ
        v.co *= 1 + R.uniform(-.18, .22)
    o.scale = (size * 1.2, size * .9, size * squash); o.location = (0, 0, size * squash * .55)
    bpy.ops.object.transform_apply(location=True, scale=True)
    bpy.ops.object.shade_flat()
    o.data.materials.append(M_ROCK); o.name = name; o.data.name = name
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66)); bpy.ops.object.mode_set(mode='OBJECT')
    return o

objs = [pine('Tree_Pine_A', 11, 9, 1.0), pine('Tree_Pine_B', 14, 11, 1.2), pine('Tree_Pine_C', 8.5, 7, .85),
        dead_tree('Tree_Dead_A', 6.5, 3), dead_tree('Tree_Dead_B', 8.5, 3), stump('Stump_A'),
        rock('Rock_A', 1.1, .7), rock('Rock_B', .55, .8)]
for o in objs:
    for q in o.data.polygons: q.use_smooth = q.use_smooth
print('作った部品:', [o.name for o in objs], '三角形の数:', sum(len(o.data.polygons) for o in objs))

for o in bpy.data.objects: o.select_set(o.type == 'MESH')
fbx = os.path.join(UE, 'Trees.fbx')
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_scale_options='FBX_SCALE_UNITS', path_mode='COPY',
                         embed_textures=True, mesh_smooth_type='FACE', add_leaf_bones=False, bake_space_transform=True)
print('書き出しました:', fbx, os.path.getsize(fbx) // 1024, 'KB')

if '--norender' not in sys.argv:                               # 確認画像（部品を横に並べて撮影）
    for i, o in enumerate(objs): o.location = ((i - len(objs) / 2) * 4.2, 0, 0)
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 24; scene.cycles.device = 'CPU'
    scene.render.resolution_x, scene.render.resolution_y = 1200, 600
    bpy.ops.object.camera_add(location=(0, -34, 7), rotation=(math.radians(84), 0, 0)); scene.camera = bpy.context.active_object
    scene.camera.data.lens = 40
    scene.world = bpy.data.worlds.new('w'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.03, .04, .06, 1)
    bpy.ops.object.light_add(type='SUN', rotation=(math.radians(55), 0, math.radians(35))); bpy.context.active_object.data.energy = 3
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0)); gp = bpy.context.active_object
    gm = bpy.data.materials.new('g'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.04, .03, .02, 1); gp.data.materials.append(gm)
    scene.render.filepath = os.path.join(OUT, 'trees_preview.png')
    bpy.ops.render.render(write_still=True)
    print('確認画像:', scene.render.filepath)
