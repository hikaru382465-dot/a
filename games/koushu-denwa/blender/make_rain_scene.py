"""雨の夜の森の公衆電話ボックス：静止画・動画を作る（bpy ヘッドレス、Cycles CPU）。

使い方（クラウドでは pip の bpy で動く）：
  python make_rain_scene.py --stage blockout --shot still          # 箱だけの仮組み
  python make_rain_scene.py --stage model    --shot still          # 実物モデルに置き換え
  python make_rain_scene.py --stage look     --shot still          # 質感・汚れ・雨・霧・光
  python make_rain_scene.py --stage look     --shot closeup        # アップ4枚（電話機・ガラス・看板・足もと）
  python make_rain_scene.py --stage look     --shot anim --q proto # 動画（連番PNG→mp4）
  --q proto（640x360 16spp）/ final（1280x720 32spp）。--frames 0-143 で範囲、--step 2 で間引き。
連番PNGは OUT_TMP に出す（リポジトリ外）。確認用の絵と mp4 は assets/rain_scene/ へ。
"""
import argparse, math, os, random, subprocess, sys
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "assets", "rain_scene")
OUT_TMP = "/tmp/claude-0/rain_frames"
GLB = os.path.join(ROOT, "assets", "phonebooth.glb")
TREES = os.path.join(ROOT, "assets", "unreal", "Trees.fbx")
SIGN_FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

# ---- 置く数字の表（見本画像から読み取った配置。ここだけ直せば全部に効く） ----
FPS, N_FRAMES = 24, 144
BOOTH_XSCALE = 0.85            # 本物（見本）より太いので横だけ縮める
CAM_START = Vector((-2.0, -5.2, 1.45))
CAM_END = Vector((-1.4, -4.0, 1.40))
CAM_TARGET = Vector((-1.5, 0.0, 1.25))   # ボックスが画面の右1/3に来る
CAM_LENS = 32
TREE_COUNT = 46
RAIN_COUNT = 5000
RAIN_BOX = 9.0                 # 雨を降らせる範囲（正方形の一辺 m）
RAIN_H = 7.0
RAIN_SPEED = 9.0               # m/s
SEED = 7

Q = {"proto": (640, 360, 16), "final": (1280, 720, 32)}


# ------------------------------------------------------------------ 基本
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def new_mat(name, color, rough=0.6, metal=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1)
        b.inputs["Emission Strength"].default_value = emit[1]
    return m


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def import_glb():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=GLB)
    return [o for o in bpy.data.objects if o not in before]


def import_trees():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=TREES)
    return {o.name: o for o in bpy.data.objects if o not in before}


# ------------------------------------------------------------------ 汚れ（画像なし・ノードだけ）
def _n(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def _ramp(nt, a, b, src):
    r = _n(nt, "ShaderNodeValToRGB")
    r.color_ramp.elements[0].position = a
    r.color_ramp.elements[1].position = b
    nt.links.new(src, r.inputs["Fac"])
    return r.outputs["Color"]


def add_grime(mat, strength=1.0, rust=True, drips=True, dust=True, rain_bump=False, finger=False):
    """材質の色・粗さの途中に、塗装剥げ・埃・垂れ跡・指紋を重ねる。"""
    if not mat or not mat.use_nodes:
        return
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return
    L = nt.links
    tc = _n(nt, "ShaderNodeTexCoord")
    obj = tc.outputs["Object"]

    def noise(scale, detail=6.0, stretch=(1, 1, 1), offset=0.0):
        mp = _n(nt, "ShaderNodeMapping")
        mp.inputs["Scale"].default_value = stretch
        mp.inputs["Location"].default_value = (offset, offset, offset)
        L.new(obj, mp.inputs["Vector"])
        nz = _n(nt, "ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = scale
        nz.inputs["Detail"].default_value = detail
        L.new(mp.outputs["Vector"], nz.inputs["Vector"])
        return nz.outputs["Fac"]

    # 元の色
    col_in = bsdf.inputs["Base Color"]
    base_col = _n(nt, "ShaderNodeRGB")
    if col_in.is_linked:
        src = col_in.links[0].from_socket
    else:
        base_col.outputs[0].default_value = col_in.default_value
        src = base_col.outputs[0]
    rough_in = bsdf.inputs["Roughness"]
    rough_src = rough_in.links[0].from_socket if rough_in.is_linked else None
    cur, cur_r = src, rough_src
    rough_val = rough_in.default_value

    def mix_col(a, b, fac):
        m = _n(nt, "ShaderNodeMix", data_type="RGBA")
        L.new(fac, m.inputs["Factor"])
        L.new(a, m.inputs["A"])
        if isinstance(b, tuple):
            m.inputs["B"].default_value = (*b, 1)
        else:
            L.new(b, m.inputs["B"])
        return m.outputs["Result"]

    def mix_val(a, b, fac):
        m = _n(nt, "ShaderNodeMix", data_type="FLOAT")
        L.new(fac, m.inputs["Factor"])
        if a is None:
            m.inputs["A"].default_value = rough_val
        else:
            L.new(a, m.inputs["A"])
        m.inputs["B"].default_value = b
        return m.outputs["Result"]

    def scale(sock, k):
        m = _n(nt, "ShaderNodeMath", operation="MULTIPLY")
        L.new(sock, m.inputs[0])
        m.inputs[1].default_value = k
        return m.outputs["Value"]

    def mulv(a, b):
        m = _n(nt, "ShaderNodeMath", operation="MULTIPLY")
        L.new(a, m.inputs[0]); L.new(b, m.inputs[1])
        return m.outputs["Value"]

    geo = _n(nt, "ShaderNodeNewGeometry")
    sep = _n(nt, "ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], sep.inputs["Vector"])

    if rust:  # 塗装の剥げ＝ノイズ＋ふちの摩耗 → 下地（さび色の金属）
        edge = _ramp(nt, 0.5, 0.56, geo.outputs["Pointiness"])
        flake = _ramp(nt, 0.5, 0.58, noise(9.0))
        peel = mulv(scale(mulv(flake, edge), 1.0), _ramp(nt, 0.1, 0.45, noise(2.5)))
        peel = scale(peel, 1.4 * strength)
        cur = mix_col(cur, (0.10, 0.045, 0.02), peel)
        cur_r = mix_val(cur_r, 0.75, peel)
    if drips:  # 垂れ跡＝縦に引き伸ばしたノイズ
        d = _ramp(nt, 0.45, 0.65, noise(14.0, 4.0, stretch=(1.0, 1.0, 0.08)))
        d = scale(d, 0.9 * strength)
        cur = mix_col(cur, (0.02, 0.018, 0.012), d)
    if dust:  # 埃＝上向きの面だけ
        up = _ramp(nt, 0.7, 0.95, sep.outputs["Z"])
        dd = mulv(up, _ramp(nt, 0.3, 0.7, noise(30.0, 8.0)))
        dd = scale(dd, 0.9 * strength)
        cur = mix_col(cur, (0.11, 0.105, 0.09), dd)
        cur_r = mix_val(cur_r, 0.95, dd)
    if finger:  # 指紋＝ガラスの手の高さにだけ、うすい点の渦
        sx = _n(nt, "ShaderNodeSeparateXYZ")
        L.new(obj, sx.inputs["Vector"])
        band = _ramp(nt, 0.0, 1.0, _band(nt, sx.outputs["Z"], 0.9, 1.5))
        vo = _n(nt, "ShaderNodeTexVoronoi", feature="F1")
        vo.inputs["Scale"].default_value = 120.0
        L.new(obj, vo.inputs["Vector"])
        ring = _ramp(nt, 0.15, 0.5, vo.outputs["Distance"])
        fp = scale(mulv(band, mulv(ring, _ramp(nt, 0.55, 0.7, noise(6.0)))), 0.6 * strength)
        cur_r = mix_val(cur_r, 0.55, fp)
    L.new(cur, bsdf.inputs["Base Color"])
    if cur_r is not None:
        L.new(cur_r, bsdf.inputs["Roughness"])

    if rain_bump:  # ガラスの雨粒＝Voronoi の凹凸。時間で下へずらす
        mp = _n(nt, "ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1.0, 1.0, 0.35)
        L.new(obj, mp.inputs["Vector"])
        mat["rain_map"] = mp.name
        vo = _n(nt, "ShaderNodeTexVoronoi", feature="F1")
        vo.inputs["Scale"].default_value = 90.0
        L.new(mp.outputs["Vector"], vo.inputs["Vector"])
        drop = _ramp(nt, 0.0, 0.3, vo.outputs["Distance"])
        bump = _n(nt, "ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.3
        bump.inputs["Distance"].default_value = 0.01
        L.new(scale(drop, -1.0), bump.inputs["Height"])
        L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        rr = mix_val(None, 0.08, mulv(_ramp(nt, 0.0, 0.3, vo.outputs["Distance"]), _ramp(nt, 0.3, 0.6, noise(3.0))))
        bsdf.inputs["Roughness"].default_value = 0.12


def _band(nt, z, lo, hi):
    """lo〜hi の間だけ1になる値。"""
    a = _n(nt, "ShaderNodeMath", operation="GREATER_THAN")
    nt.links.new(z, a.inputs[0]); a.inputs[1].default_value = lo
    b = _n(nt, "ShaderNodeMath", operation="LESS_THAN")
    nt.links.new(z, b.inputs[0]); b.inputs[1].default_value = hi
    m = _n(nt, "ShaderNodeMath", operation="MULTIPLY")
    nt.links.new(a.outputs[0], m.inputs[0]); nt.links.new(b.outputs[0], m.inputs[1])
    return m.outputs[0]


# ------------------------------------------------------------------ 場面の部品
def clear_glass(mat):
    """買った/書き出し済みのくもりガラス画像をやめて、透明なガラスにする（汚れはノードで重ねる）。"""
    nt = mat.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for k in ("Base Color", "Roughness", "Alpha", "Metallic"):
        for l in list(b.inputs[k].links):
            nt.links.remove(l)
    b.inputs["Base Color"].default_value = (0.75, 0.85, 0.82, 1)
    b.inputs["Roughness"].default_value = 0.06
    b.inputs["Alpha"].default_value = 1.0
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.45


def make_ground(stage):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=300 if stage != "blockout" else 20,
                                    y_subdivisions=300 if stage != "blockout" else 20, size=70)
    g = bpy.context.object
    g.name = "Ground"
    if stage == "blockout":
        assign(g, new_mat("blk_ground", (0.12, 0.12, 0.12)))
        return g
    # でこぼこ（地面全体）＋わだち（道のくぼみ）
    tex = bpy.data.textures.new("gnoise", "CLOUDS")
    tex.noise_scale = 3.5
    dm = g.modifiers.new("Bump", "DISPLACE")
    dm.texture = tex
    dm.strength = 0.22
    dm.mid_level = 0.5
    mat = bpy.data.materials.new("MudGround")
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    L = nt.links
    tc = _n(nt, "ShaderNodeTexCoord")
    sep = _n(nt, "ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs["Vector"])
    # 道：手前から奥へ曲がる帯（x = 中心線 ± 幅）。中心線は y の2次式
    cl = _n(nt, "ShaderNodeMath", operation="MULTIPLY")
    L.new(sep.outputs["Y"], cl.inputs[0]); cl.inputs[1].default_value = 0.06
    cl2 = _n(nt, "ShaderNodeMath", operation="MULTIPLY")
    L.new(cl.outputs[0], cl2.inputs[0]); L.new(sep.outputs["Y"], cl2.inputs[1])
    off = _n(nt, "ShaderNodeMath", operation="SUBTRACT")
    L.new(sep.outputs["X"], off.inputs[0]); L.new(cl2.outputs[0], off.inputs[1])
    ab = _n(nt, "ShaderNodeMath", operation="ABSOLUTE")
    L.new(off.outputs[0], ab.inputs[0])
    nz = _n(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.2
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    wob = _n(nt, "ShaderNodeMath", operation="MULTIPLY_ADD")
    L.new(nz.outputs["Fac"], wob.inputs[0]); wob.inputs[1].default_value = 1.5
    L.new(ab.outputs[0], wob.inputs[2])
    path = _ramp(nt, 0.8, 2.6, wob.outputs[0])        # 0=道 / 1=森の地面
    # 水たまり
    pn = _n(nt, "ShaderNodeTexNoise"); pn.inputs["Scale"].default_value = 0.9; pn.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], pn.inputs["Vector"])
    pud = _ramp(nt, 0.52, 0.56, pn.outputs["Fac"])
    inv = _n(nt, "ShaderNodeMath", operation="SUBTRACT"); inv.inputs[0].default_value = 1.0
    L.new(path, inv.inputs[1])
    pud = _n(nt, "ShaderNodeMath", operation="MULTIPLY")
    L.new(_ramp(nt, 0.52, 0.56, pn.outputs["Fac"]), pud.inputs[0]); L.new(inv.outputs[0], pud.inputs[1])
    # 色：道＝茶色い泥、森＝暗い落ち葉
    fn = _n(nt, "ShaderNodeTexNoise"); fn.inputs["Scale"].default_value = 18; fn.inputs["Detail"].default_value = 10
    L.new(tc.outputs["Object"], fn.inputs["Vector"])
    mud = _n(nt, "ShaderNodeMix", data_type="RGBA")
    L.new(fn.outputs["Fac"], mud.inputs["Factor"])
    mud.inputs["A"].default_value = (0.045, 0.028, 0.016, 1); mud.inputs["B"].default_value = (0.09, 0.06, 0.03, 1)
    leaf = _n(nt, "ShaderNodeMix", data_type="RGBA")
    L.new(fn.outputs["Fac"], leaf.inputs["Factor"])
    leaf.inputs["A"].default_value = (0.008, 0.016, 0.01, 1); leaf.inputs["B"].default_value = (0.03, 0.03, 0.012, 1)
    c = _n(nt, "ShaderNodeMix", data_type="RGBA")
    L.new(path, c.inputs["Factor"]); L.new(mud.outputs["Result"], c.inputs["A"]); L.new(leaf.outputs["Result"], c.inputs["B"])
    L.new(c.outputs["Result"], b.inputs["Base Color"])
    # 粗さ：水たまり0.03、泥0.35、葉0.8
    r0 = _n(nt, "ShaderNodeMix", data_type="FLOAT")
    L.new(path, r0.inputs["Factor"]); r0.inputs["A"].default_value = 0.35; r0.inputs["B"].default_value = 0.8
    r1 = _n(nt, "ShaderNodeMix", data_type="FLOAT")
    L.new(pud.outputs[0], r1.inputs["Factor"]); L.new(r0.outputs["Result"], r1.inputs["A"]); r1.inputs["B"].default_value = 0.03
    L.new(r1.outputs["Result"], b.inputs["Roughness"])
    # 凹凸（小石・泥）＋水たまりの波紋（時間で動く）
    bn = _n(nt, "ShaderNodeBump"); bn.inputs["Strength"].default_value = 0.5
    L.new(fn.outputs["Fac"], bn.inputs["Height"])
    L.new(bn.outputs["Normal"], b.inputs["Normal"])
    g.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return g


def tree_up(o):
    """Trees.fbx の木の『上』の向きを調べ、回して立てる（確認用に最初の1回だけ）。"""
    d = o.dimensions
    return d


def place_trees(stage, src, rng):
    objs = []
    names = ["Tree_Pine_A", "Tree_Pine_B", "Tree_Pine_C", "Tree_Dead_A", "Tree_Dead_B"]
    for o in src.values():
        o.hide_set(True); o.hide_render = True
    if stage == "blockout":
        mats = new_mat("blk_tree", (0.25, 0.25, 0.25))
    spots = []
    tries = 0
    while len(spots) < TREE_COUNT and tries < 5000:
        tries += 1
        x, y = rng.uniform(-26, 26), rng.uniform(-8, 40)
        # 道・ボックス・カメラまわりをあける
        if abs(x - 0.06 * y * y * 0.0) < 3.2 and y < 22:
            continue
        if math.hypot(x, y) < 3.0:
            continue
        if any(math.hypot(x - sx, y - sy) < 2.4 for sx, sy in spots):
            continue
        spots.append((x, y))
    # 右はしの太い幹（見本1枚目）
    spots.append((4.2, 2.6))
    for i, (x, y) in enumerate(spots):
        name = "Tree_Pine_B" if i == len(spots) - 1 else rng.choice(names)
        s = src.get(name)
        if stage == "blockout":
            h = rng.uniform(9, 14)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.28, depth=h, location=(x, y, h / 2))
            o = bpy.context.object
            assign(o, mats)
        else:
            o = s.copy()                  # 形は共有（同じ形を何本も置く）
            bpy.context.collection.objects.link(o)
            o.hide_set(False); o.hide_render = False
            k = rng.uniform(0.85, 1.35) * (1.6 if i == len(spots) - 1 else 1.0)
            o.scale = (k, k, k)
            o.location = (x, y, -0.15)
            o.rotation_euler = (s.rotation_euler[0], s.rotation_euler[1], s.rotation_euler[2] + rng.uniform(0, 6.28))
        objs.append(o)
    return objs


def make_bushes(rng, n=26):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0)
    base = bpy.context.object
    base.name = "BushBase"
    tex = bpy.data.textures.new("bushnz", "CLOUDS"); tex.noise_scale = 0.35
    dm = base.modifiers.new("d", "DISPLACE"); dm.texture = tex; dm.strength = 0.55
    bpy.ops.object.modifier_apply(modifier="d")
    m = bpy.data.materials.new("Bush"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = _n(nt, "ShaderNodeTexCoord"); vo = _n(nt, "ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 14
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    cr = _n(nt, "ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.004, 0.02, 0.008, 1); cr.color_ramp.elements[1].color = (0.03, 0.09, 0.03, 1)
    nt.links.new(vo.outputs["Distance"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35   # ぬれた葉
    assign(base, m)
    bpy.ops.object.shade_smooth()
    out = []
    for _ in range(n):
        o = base.copy(); bpy.context.collection.objects.link(o)
        side = rng.choice([-1, 1])
        o.location = (rng.uniform(-14, 14), rng.uniform(-7, 18), 0.2)
        if abs(o.location.x) < 3.3 or math.hypot(o.location.x, o.location.y) < 2.4:
            o.location.x = side * rng.uniform(3.5, 10)
        s = rng.uniform(0.5, 1.4)
        o.scale = (s * 1.3, s * 1.3, s * 0.7)
        o.rotation_euler.z = rng.uniform(0, 6.28)
        out.append(o)
    base.hide_render = True; base.hide_set(True)
    return out


def make_sign(parent):
    """屋根の緑の看板「公衆電話」（4面）。板＋白い立体文字、板はうっすら光る。"""
    mat_g = new_mat("SignGreen", (0.01, 0.2, 0.07), 0.45, 0.0, emit=((0.02, 0.5, 0.16), 0.8))
    mat_w = new_mat("SignWhite", (0.8, 0.85, 0.8), 0.4, emit=((0.8, 0.9, 0.8), 0.3))
    hw, hd, z = 0.53, 0.66, 2.02      # 横方向は縮めたあとの半幅（1.24*0.85/2）
    for k in range(4):
        face = k % 2 == 0
        wide = 2 * hw if face else 2 * hd
        off = hd + 0.02 if face else hw + 0.02
        piv = bpy.data.objects.new(f"SignPivot_{k}", None)
        bpy.context.collection.objects.link(piv)
        piv.rotation_euler.z = k * math.pi / 2
        piv.location = (0, 0, 0)
        bpy.ops.mesh.primitive_cube_add(size=1)
        p = bpy.context.object; p.name = f"Sign_{k}"
        p.scale = (wide, 0.03, 0.22)
        assign(p, mat_g)
        p.parent = piv; p.location = (0, -off, z)
        bpy.ops.object.text_add()
        t = bpy.context.object; t.name = f"SignText_{k}"
        t.data.body = "公衆電話"
        try:
            t.data.font = bpy.data.fonts.load(SIGN_FONT)
        except Exception:
            pass
        t.data.align_x = "CENTER"; t.data.align_y = "CENTER"
        t.data.size = 0.15; t.data.extrude = 0.006
        t.rotation_euler = (math.pi / 2, 0, 0)
        t.data.materials.append(mat_w)
        t.parent = piv; t.location = (0, -off - 0.02, z)


def make_rain(rng):
    """雨の筋＝細い板のメッシュ。毎フレーム numpy で位置を更新（保存が要らず、何度やっても同じ）。"""
    import numpy as np
    n = RAIN_COUNT
    me = bpy.data.meshes.new("rain")
    me.from_pydata([(0, 0, 0)] * (4 * n), [], [(4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3) for i in range(n)])
    ob = bpy.data.objects.new("Rain", me)
    bpy.context.collection.objects.link(ob)
    r = np.random.default_rng(SEED)
    base = dict(x=r.uniform(-RAIN_BOX / 2, RAIN_BOX / 2, n) + 0.5, y=r.uniform(-RAIN_BOX / 2, RAIN_BOX / 2, n) - 0.5,
                z0=r.uniform(0, RAIN_H, n), v=RAIN_SPEED * r.uniform(0.85, 1.15, n), ln=r.uniform(0.15, 0.32, n))
    mat = bpy.data.materials.new("RainMat")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    # ボックスに近いほど明るい（蛍光灯に照らされて見える）
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = "DISTANCE"
    vm.inputs[1].default_value = (0, 0, 1.4)
    nt.links.new(tc.outputs["Object"], vm.inputs[0])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.5; cr.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr.color_ramp.elements[1].position = 6.0; cr.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1)
    nt.links.new(vm.outputs["Value"], cr.inputs["Fac"])
    sc = nt.nodes.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = 10.0
    nt.links.new(cr.outputs["Color"], sc.inputs[0])
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = "ADD"; ad.inputs[1].default_value = 0.35   # 遠くも青白く見える下駄
    nt.links.new(sc.outputs[0], ad.inputs[0])
    nt.links.new(ad.outputs[0], em.inputs["Strength"])
    em.inputs["Color"].default_value = (0.55, 0.7, 1.0, 1)
    mx.inputs["Fac"].default_value = 0.16
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    me.materials.append(mat)
    for attr in ("visible_shadow", "visible_glossy", "visible_transmission", "visible_diffuse"):
        setattr(ob, attr, False)
    cam = bpy.context.scene.camera

    def update(frame):
        t = frame / FPS
        z = (base["z0"] - base["v"] * t) % RAIN_H
        cr_ = np.array(cam.matrix_world.to_3x3() @ Vector((1, 0, 0)))
        cr_[2] = 0
        cr_ = cr_ / (np.linalg.norm(cr_) + 1e-9)
        w = 0.0022
        x, y, ln = base["x"], base["y"], base["ln"]
        # 斜めに降る（風）：長さ方向に少し流す
        dx = 0.05 * ln
        co = np.zeros((n, 4, 3), dtype=np.float32)
        for i, (sx, sz) in enumerate([(-w, 0.0), (w, 0.0), (w, ln), (-w, ln)]):
            co[:, i, 0] = x + cr_[0] * sx + dx * (sz / np.maximum(ln, 1e-6))
            co[:, i, 1] = y + cr_[1] * sx
            co[:, i, 2] = z + sz
        me.vertices.foreach_set("co", co.reshape(-1))
        me.update()
    return ob, update


def make_lights(stage):
    lights = {}
    # 主役：ボックスの天井の小さな面光源（カメラには映さない）
    bpy.ops.object.light_add(type="AREA", location=(0, 0.0, 1.95))
    a = bpy.context.object; a.name = "BoothLight"
    a.data.shape = "RECTANGLE"; a.data.size = 0.5; a.data.size_y = 0.9
    a.data.energy = 170; a.data.color = (0.8, 0.95, 1.0)
    a.rotation_euler = (0, 0, 0)       # 下向き
    a.visible_camera = False if hasattr(a, "visible_camera") else None
    lights["booth"] = a
    # 逆光：奥から青い光（雨を浮かせる）
    bpy.ops.object.light_add(type="AREA", location=(-1.0, 12.0, 6.5))
    r = bpy.context.object; r.name = "RimBlue"
    r.data.shape = "RECTANGLE"; r.data.size = 9; r.data.size_y = 5
    r.data.energy = 1500; r.data.color = (0.18, 0.32, 0.8)
    r.rotation_euler = (math.radians(65), 0, 0)
    r.visible_camera = False if hasattr(r, "visible_camera") else None
    # 弱い月明かり（Fill）：ほぼ見えない青
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 10))
    s = bpy.context.object; s.name = "MoonFill"
    s.data.energy = 0.08; s.data.color = (0.45, 0.55, 1.0); s.data.angle = math.radians(8)
    s.rotation_euler = (math.radians(50), 0, math.radians(30))
    return lights


def make_world(stage, fog=True):
    w = bpy.data.worlds.new("World"); w.use_nodes = True
    bpy.context.scene.world = w
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (0.004, 0.008, 0.02, 1); bg.inputs["Strength"].default_value = 1.0
    if fog and stage == "look":
        out = nt.nodes["World Output"]
        vs = nt.nodes.new("ShaderNodeVolumeScatter")
        vs.inputs["Density"].default_value = 0.007
        vs.inputs["Color"].default_value = (0.35, 0.5, 0.9, 1)
        vs.inputs["Anisotropy"].default_value = 0.4
        nt.links.new(vs.outputs[0], out.inputs["Volume"])


def make_camera():
    bpy.ops.object.camera_add(location=CAM_START)
    c = bpy.context.object; c.name = "Cam"
    c.data.lens = CAM_LENS; c.data.dof.use_dof = True
    c.data.dof.aperture_fstop = 4.0
    bpy.context.scene.camera = c
    tgt = bpy.data.objects.new("CamTarget", None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = CAM_TARGET
    con = c.constraints.new("TRACK_TO"); con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    c.data.dof.focus_object = tgt
    return c, tgt


def cam_pos(frame, rng_seed=3):
    """6秒かけてゆっくり前へ。手ぶれは小さな波を足す。"""
    t = frame / (N_FRAMES - 1)
    e = t * t * (3 - 2 * t)
    p = CAM_START.lerp(CAM_END, e)
    p.x += 0.025 * math.sin(frame * 0.37) + 0.015 * math.sin(frame * 0.91)
    p.z += 0.02 * math.sin(frame * 0.29 + 1.0) + 0.01 * math.sin(frame * 1.3)
    return p


def flicker_gain(frame):
    """蛍光灯の点滅（0〜1の倍率）。ふだんは安定、ときどきパッパッと切り替わる。"""
    bursts = [(26, 34), (58, 61), (92, 104), (118, 121)]
    for a, b in bursts:
        if a <= frame <= b:
            rr = random.Random(frame * 7919 + 13).random()
            return 0.04 if rr < 0.55 else (0.55 if rr < 0.8 else 1.0)
    return 0.96 + 0.04 * math.sin(frame * 1.7)


# ------------------------------------------------------------------ 組み立て
def build(stage):
    rng = random.Random(SEED)
    reset()
    sc = bpy.context.scene
    ctx = {"stage": stage}
    cam, tgt = make_camera()
    make_world(stage)
    ctx["lights"] = make_lights(stage)
    ground = make_ground(stage)
    if stage == "blockout":
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.15))
        b = bpy.context.object; b.scale = (1.05, 1.1, 2.3); assign(b, new_mat("blk_booth", (0.5, 0.5, 0.5)))
        src = None
        place_trees("blockout", {}, rng)
        return ctx
    # --- 実物 ---
    objs = import_glb()
    root = bpy.data.objects.new("Booth", None)
    bpy.context.collection.objects.link(root)
    root.scale = (BOOTH_XSCALE, 1, 1)
    for o in objs:
        if o.parent is None:
            o.parent = root
    # 足もとを地面に（箱の下端をz=0）
    ctx["booth"] = root
    src = import_trees()
    place_trees(stage, src, rng)
    if stage == "model":
        make_sign(root)
        make_bushes(rng)
        return ctx
    # --- look ---
    make_sign(root)
    make_bushes(rng)
    for m in bpy.data.materials:
        n = m.name
        if n.startswith(("Bronze", "GrayPaint")):
            add_grime(m, 1.0)
        elif n.startswith("Phone") and n not in ("PhoneKeys", "PhonePanel"):
            add_grime(m, 0.8)
        elif n.startswith("Glass"):
            clear_glass(m)
            add_grime(m, 0.7, rust=False, drips=True, dust=False, rain_bump=True, finger=True)
        elif n.startswith(("FloorConcrete", "Ceiling", "Steel")):
            add_grime(m, 0.9, rust=False)
    rain_ob, ctx["rain_update"] = make_rain(rng)
    ctx["tube_mats"] = [m for m in bpy.data.materials if m.name.startswith("Tube")]
    return ctx


def configure(q, closeup=False):
    sc = bpy.context.scene
    w, h, spp = Q[q]
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.render.resolution_x, sc.render.resolution_y = (w, h) if not closeup else (800, 800)
    sc.render.resolution_percentage = 100
    sc.cycles.samples = spp if not closeup else 24
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 1
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 8
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.volume_bounces = 0
    sc.cycles.volume_max_steps = 64
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.use_animated_seed = False
    sc.render.use_persistent_data = True
    sc.render.fps = FPS
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.file_format = "PNG"


def apply_frame(ctx, frame):
    sc = bpy.context.scene
    sc.frame_set(frame)
    cam = sc.camera
    cam.location = cam_pos(frame)
    g = flicker_gain(frame) if ctx["stage"] == "look" else 1.0
    ctx["lights"]["booth"].data.energy = 170 * g
    for m in ctx.get("tube_mats", []):
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                n.inputs["Emission Strength"].default_value = 12.0 * g
    if "rain_update" in ctx:
        ctx["rain_update"](frame)
    for m in bpy.data.materials:                 # ガラスの雨粒を下へ流す
        mp = m.get("rain_map") if m.node_tree else None
        if mp:
            m.node_tree.nodes[mp].inputs["Location"].default_value = (0, 0, frame * 0.012)


CLOSEUPS = {
    "phone": ((-0.35, -1.2, 1.35), (0.0, 0.35, 1.2), 50),
    "glass": ((-0.9, -1.4, 1.2), (0.0, -0.6, 1.2), 50),
    "sign": ((-1.6, -2.4, 2.2), (0.0, -0.6, 2.1), 50),
    "foot": ((-0.8, -2.2, 0.5), (0.0, -0.6, 0.15), 40),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="look", choices=["blockout", "model", "look"])
    ap.add_argument("--shot", default="still", choices=["still", "closeup", "anim"])
    ap.add_argument("--q", default="proto", choices=list(Q))
    ap.add_argument("--frame", type=int, default=0)
    ap.add_argument("--frames", default=None)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--only", default=None, help="closeup の名前（phone/glass/sign/foot）")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    os.makedirs(OUT_DIR, exist_ok=True)
    ctx = build(a.stage)
    configure(a.q if a.stage != "blockout" else "proto", a.shot == "closeup")
    sc = bpy.context.scene
    if a.stage == "blockout":
        sc.cycles.samples = 8
        sc.render.resolution_x, sc.render.resolution_y = 480, 270
    if a.shot == "still":
        apply_frame(ctx, a.frame)
        sc.render.filepath = os.path.join(OUT_DIR, f"{a.stage}_still.png")
        bpy.ops.render.render(write_still=True)
    elif a.shot == "closeup":
        for name, (loc, tg, lens) in CLOSEUPS.items():
            if a.only and name != a.only:
                continue
            apply_frame(ctx, a.frame)
            cam = sc.camera
            cam.constraints[0].target.location = Vector(tg)
            cam.data.lens = lens
            cam.location = Vector(loc)
            cam.data.dof.use_dof = False
            sc.render.filepath = os.path.join(OUT_DIR, f"{a.stage}_close_{name}.png")
            bpy.ops.render.render(write_still=True)
    else:
        os.makedirs(OUT_TMP, exist_ok=True)
        lo, hi = (0, N_FRAMES - 1) if not a.frames else map(int, a.frames.split("-"))
        for f in range(lo, hi + 1, a.step):
            path = os.path.join(OUT_TMP, f"f_{a.q}_{f:04d}.png")
            if os.path.exists(path):
                continue                      # 途中で止まっても続きから
            apply_frame(ctx, f)
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            print("frame", f, flush=True)
        if a.step == 1 and lo == 0 and hi == N_FRAMES - 1:
            encode(a.q)


def encode(q):
    out = os.path.join(OUT_DIR, f"rain_booth_{q}.mp4")
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(OUT_TMP, f"f_{q}_%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
    print("mp4:", out)


if __name__ == "__main__":
    main()
