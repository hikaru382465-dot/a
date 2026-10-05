# Blenderで稲妻を1コマずつ描画（光る立体の線）。実行：python3 make_fx_lightning.py
import bpy, random, os, math
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fx", "blender"); os.makedirs(OUT, exist_ok=True)
N, W, H = 6, 512, 192
for i in range(N):
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    R = random.Random(300 + i)
    pts = [(-3.0, 0, 0)]; x = -3.0
    while x < 2.9:
        x += R.uniform(.35, .7); pts.append((min(x, 3.0), 0, R.uniform(-.55, .55)))
    def bolt(pts, radius, mat, dy=0):
        cu = bpy.data.curves.new("b", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = radius; cu.bevel_resolution = 3
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for p, v in zip(sp.points, pts): p.co = (v[0], v[1] + dy, v[2], 1)
        ob = bpy.data.objects.new("b", cu); sc.collection.objects.link(ob); ob.data.materials.append(mat); return ob
    def emit(col, s):
        m = bpy.data.materials.new("m"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = s
        o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0]); return m
    bolt(pts, .11, emit((0.4, 0.3, 0.95), 1.0)); bolt(pts, .06, emit((1.0, 0.62, 0.15), 1.0), -0.2); bolt(pts, .025, emit((1, 0.97, 0.85), 1.0), -0.4)
    for k in range(3):  # 枝わかれ
        j = R.randint(1, len(pts) - 2); bx, _, bz = pts[j]; br = [(bx, 0, bz)]
        for s in range(3): bx += R.uniform(.2, .45); bz += R.uniform(-.5, .5) + (.2 if k % 2 else -.2); br.append((bx, 0, bz))
        bolt(br, .03, emit((1.0, 0.8, 0.4), 1.0), -0.3)
    bpy.ops.object.camera_add(location=(0, -8, 0), rotation=(math.radians(90), 0, 0)); cam = bpy.context.object
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 6.6; sc.camera = cam
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 24; sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    sc.render.filepath = os.path.join(OUT, f"lightning_raw_{i}.png"); bpy.ops.render.render(write_still=True)
print("done")
