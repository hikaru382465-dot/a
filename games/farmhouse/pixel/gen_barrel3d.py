# 3Dで樽を作る → 「形と明るさ」と「材料のぬり分け」を2枚出す → パレット(木D・鉄I)の色だけで小さいドット絵にする
# 実行: /tmp/claude-0/venv/bin/python gen_barrel3d.py   （bpy が要る）
import bpy, bmesh, math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pxl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "props3d"); os.makedirs(OUT, exist_ok=True)
RS = 512                       # 3Dの出力サイズ
PH = 40                        # できあがりのドットの高さ

def new_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.cycles.device = "CPU"
    sc.cycles.use_denoising = False
    sc.render.resolution_x = sc.render.resolution_y = RS
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    return sc

def mat(name, rgb, emit=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if emit:
        e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1)
        nt.links.new(e.outputs[0], out.inputs[0])
    else:
        b = nt.nodes.new("ShaderNodeBsdfDiffuse"); b.inputs["Color"].default_value = (*rgb, 1)
        nt.links.new(b.outputs[0], out.inputs[0])
    return m

def lathe(name, prof, seg=64, staves=0, depth=0.0):
    """prof=[(半径,高さ)...]を回して面を作る。staves>0 で板のすき間のへこみをつける"""
    bm = bmesh.new(); rings = []
    for (r, z) in prof:
        ring = []
        for i in range(seg):
            t = 2 * math.pi * i / seg
            rr = r * (1 - depth * (1 - abs(math.cos(t * staves / 2)))) if staves else r
            ring.append(bm.verts.new((rr * math.cos(t), rr * math.sin(t), z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    return o

def build(mode):
    """mode='lit' 形と明るさ / 'mask' 材料のぬり分け(木=赤・鉄=緑・上のふた=青)"""
    sc = new_scene()
    W = mat("w", (0.8, 0.8, 0.8)) if mode == "lit" else mat("w", (1, 0, 0), True)
    I = mat("i", (0.8, 0.8, 0.8)) if mode == "lit" else mat("i", (0, 1, 0), True)
    T = mat("t", (0.8, 0.8, 0.8)) if mode == "lit" else mat("t", (0, 0, 1), True)
    H = 1.0
    prof = []
    for k in range(0, 21):                    # 胴：まん中がふくらむ
        z = k / 20 * H
        r = 0.40 + 0.09 * math.sin(math.pi * k / 20) ** 1.3
        prof.append((r, z))
    body = lathe("body", prof, 96, staves=12, depth=0.05); body.data.materials.append(W)
    def hoop(z, r, w=0.07, th=0.025):
        o = lathe("hoop", [(r, z - w / 2), (r + th, z - w / 2 + 0.01), (r + th, z + w / 2 - 0.01), (r, z + w / 2)], 96); o.data.materials.append(I); return o
    def R(z): return 0.40 + 0.09 * math.sin(math.pi * z / H) ** 1.3
    for z in (0.10, 0.28, 0.72, 0.90): hoop(z, R(z) - 0.004)
    bpy.ops.mesh.primitive_circle_add(vertices=96, radius=R(H) - 0.02, fill_type="NGON", location=(0, 0, H - 0.05))
    top = bpy.context.object; top.data.materials.append(T)
    lip = lathe("lip", [(R(H) - 0.02, H - 0.05), (R(H) - 0.02, H + 0.0), (R(H) + 0.005, H + 0.0)], 96); lip.data.materials.append(W)
    cam = bpy.data.cameras.new("c"); cam.type = "ORTHO"; cam.ortho_scale = 1.75
    co = bpy.data.objects.new("c", cam); bpy.context.collection.objects.link(co); sc.camera = co
    el = math.radians(30)
    d = 6
    co.location = (0, -d * math.cos(el), 0.5 + d * math.sin(el)); co.rotation_euler = (math.pi / 2 - el, 0, 0)
    if mode == "lit":
        sc.world = bpy.data.worlds.new("w"); sc.world.use_nodes = True
        sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.6, 0.7, 1)
        sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.3
        s = bpy.data.lights.new("s", "SUN"); s.energy = 1.7; s.angle = math.radians(12)
        so = bpy.data.objects.new("s", s); bpy.context.collection.objects.link(so)
        so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
    path = os.path.join("/tmp/claude-0/b3d", f"barrel_{mode}.png")
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    return np.array(Image.open(path).convert("RGBA"))

lit = build("lit"); mask = build("mask")

# ---- ドット絵へ ----
a = mask[..., 3] > 128
ys, xs = np.nonzero(a); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
lit = lit[y0:y1, x0:x1]; mask = mask[y0:y1, x0:x1]; a = a[y0:y1, x0:x1]
PW = round((x1 - x0) * PH / (y1 - y0))
pal, _ = pxl.load_palette()
lum = (lit[..., :3].astype(float) @ [0.3, 0.59, 0.11]) / 255.0
def block(arr, f):                      # PH×PW に区切って、各ブロックの代表値を出す
    out = np.zeros((PH, PW) + (arr.shape[2:] if f == "mean" else ()), float if f == "mean" else int)
    for j in range(PH):
        for i in range(PW):
            ys_, ye = j * arr.shape[0] // PH, (j + 1) * arr.shape[0] // PH
            xs_, xe = i * arr.shape[1] // PW, (i + 1) * arr.shape[1] // PW
            b = arr[ys_:ye, xs_:xe]
            if f == "mean": out[j, i] = b[a[ys_:ye, xs_:xe]].mean(0) if a[ys_:ye, xs_:xe].any() else 0
            else:
                v = b.reshape(-1, b.shape[-1]); v = v[a[ys_:ye, xs_:xe].reshape(-1)] if a[ys_:ye, xs_:xe].any() else v
                k = np.argmax(v, axis=1); out[j, i] = np.bincount(k, minlength=3).argmax()
    return out
cov = block(a[..., None].astype(float), "mean")[..., 0] if False else None
fam = block(mask[..., :3], "major")                 # 0=木 1=鉄 2=ふた
L = block(lum, "mean") if lum.ndim == 2 else None
L = np.array([[lum[j * lum.shape[0] // PH:(j + 1) * lum.shape[0] // PH, i * lum.shape[1] // PW:(i + 1) * lum.shape[1] // PW][a[j * a.shape[0] // PH:(j + 1) * a.shape[0] // PH, i * a.shape[1] // PW:(i + 1) * a.shape[1] // PW]].mean() if a[j * a.shape[0] // PH:(j + 1) * a.shape[0] // PH, i * a.shape[1] // PW:(i + 1) * a.shape[1] // PW].mean() > .5 else np.nan for i in range(PW)] for j in range(PH)])
alpha = ~np.isnan(L)
Lv = L[alpha]; lo, hi = np.percentile(Lv, 3), np.percentile(Lv, 97)
img = np.zeros((PH + 2, PW + 2, 4), np.uint8)
FAM = ["D", "I", "D"]
for j in range(PH):
    for i in range(PW):
        if not alpha[j, i]: continue
        t = np.clip((L[j, i] - lo) / (hi - lo + 1e-6), 0, 1)
        f = FAM[fam[j, i]]
        sh = int(round(1 + t * 5))                          # 木は1〜6
        if fam[j, i] == 1: sh = int(round(1 + t * 4))       # 鉄は少し暗め
        if fam[j, i] == 2: sh = int(round(3 + t * 3))       # ふた(上を向く面)は明るめ
        img[j + 1, i + 1, :3] = pal[f][sh]; img[j + 1, i + 1, 3] = 255
# 輪郭(1ドット)：となりの色の一番暗い色
al = img[..., 3] > 0
for y in range(PH + 2):
    for x in range(PW + 2):
        if al[y, x]: continue
        nb = [(y + dy, x + dx) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= y + dy < PH + 2 and 0 <= x + dx < PW + 2 and al[y + dy, x + dx]]
        if nb: img[y, x, :3] = pal["D"][0]; img[y, x, 3] = 255
Image.fromarray(img).save(os.path.join(OUT, "barrel.png"))
S = 12
big = Image.fromarray(img).resize((img.shape[1] * S, img.shape[0] * S), Image.NEAREST)
sheet = Image.new("RGBA", (big.width + 540 + 60, max(big.height, 520) + 40), (40, 44, 58, 255))
sheet.alpha_composite(big, (20, 20))
sheet.alpha_composite(Image.open("/tmp/claude-0/b3d/barrel_lit.png").convert("RGBA").resize((512, 512)), (big.width + 40, 20))
sheet.save(os.path.join(OUT, "barrel_check.png"))
print(img.shape, "colors:", len({tuple(p) for p in img.reshape(-1, 4) if p[3]}))
