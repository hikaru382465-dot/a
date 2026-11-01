"""Substance Painter風の「汚し」を、1つのノードグループ（SubstanceWear）にまとめる。
画像は使わず、すべてプロシージャル（ノードだけ）。Cycles用（BevelとAOのノードを使う）。

入っている汚し（強さは材質ごとに入力で変える）
  1. エッジの塗装剥げ   … 角を検出（Bevel）して、ノイズで欠けさせ、下地の色を出す
  2. 隙間の汚れ         … すき間・入り隅（AO）に、黒ずみがたまる
  3. 上面の埃           … 上を向いた面（法線のZ）に、まだらに積もる
  4. 床際の汚れ         … 低い所に、下から這い上がる汚れ＋部屋の四隅・壁ぎわ
  5. 垂れ跡             … 縦に引き伸ばしたノイズで、上から垂れた筋
  6. 指紋               … ボロノイの細胞ごとに、渦（輪）の脂のあと。ざらつきを下げる
段階：stage 1=汚しなし／2=エッジ＋隙間／3=＋埃＋床際／4=＋垂れ跡＋指紋（最終）"""
import bpy, math

ROOM_HX, ROOM_HY = 1.35, 1.80   # 部屋の半分の大きさ（床際の計算に使う）

def build_group(stage=4):
    ng = bpy.data.node_groups.get("SubstanceWear")
    if ng: bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new("SubstanceWear", "ShaderNodeTree")
    I = ng.interface
    def inp(name, kind, default):
        s = I.new_socket(name=name, in_out="INPUT", socket_type=kind); s.default_value = default; return s
    C, F = "NodeSocketColor", "NodeSocketFloat"
    inp("Base Color", C, (0.5, 0.5, 0.5, 1)); inp("Roughness", F, 0.5); inp("Metallic", F, 0.0)
    inp("Edge Wear", F, 0.0); inp("Edge Color", C, (0.55, 0.50, 0.42, 1)); inp("Wear Metallic", F, 0.0); inp("Edge Radius", F, 0.01)
    inp("Crevice Dirt", F, 0.0); inp("Dirt Color", C, (0.015, 0.012, 0.01, 1))
    inp("Top Dust", F, 0.0); inp("Dust Color", C, (0.33, 0.32, 0.30, 1))
    inp("Floor Grime", F, 0.0); inp("Grime Color", C, (0.035, 0.028, 0.02, 1))
    inp("Drips", F, 0.0); inp("Drip Color", C, (0.05, 0.035, 0.02, 1))
    inp("Fingerprints", F, 0.0); inp("Scale", F, 1.0)
    I.new_socket(name="Base Color", in_out="OUTPUT", socket_type=C); I.new_socket(name="Roughness", in_out="OUTPUT", socket_type=F)
    I.new_socket(name="Metallic", in_out="OUTPUT", socket_type=F)
    N, L = ng.nodes, ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    gi.location = (-2400, 0); go.location = (1800, 0)
    # --- 小さな道具 ---
    def S(sock):   # 数値・ソケットの入力を統一
        return sock
    def node(t, loc=(0, 0), **props):
        n = N.new(t); n.location = loc
        for k, v in props.items(): setattr(n, k, v)
        return n
    def setin(n, name_or_idx, v):
        s = n.inputs[name_or_idx]
        if isinstance(v, (int, float)): s.default_value = v
        elif hasattr(v, "bl_idname") and v.bl_idname.startswith("NodeSocket"): L.new(v, s)
        else: s.default_value = v
    def math(op, a, b=None, c=None, clamp=False, loc=(0, 0)):
        n = node("ShaderNodeMath", loc, operation=op, use_clamp=clamp)
        setin(n, 0, a)
        if b is not None: setin(n, 1, b)
        if c is not None: setin(n, 2, c)
        return n.outputs[0]
    def mrange(v, a, b, c=0.0, d=1.0, clamp=True):
        n = node("ShaderNodeMapRange"); n.clamp = clamp
        setin(n, "Value", v); setin(n, "From Min", a); setin(n, "From Max", b); setin(n, "To Min", c); setin(n, "To Max", d)
        return n.outputs["Result"]
    def lerp(a, b, f):   # 数値のまぜ合わせ  a + (b-a)*f
        return math("ADD", a, math("MULTIPLY", math("SUBTRACT", b, a), f))
    def mixc(a, b, f, blend="MIX"):
        n = node("ShaderNodeMixRGB", blend_type=blend, use_clamp=True)
        setin(n, "Fac", f); setin(n, "Color1", a); setin(n, "Color2", b); return n.outputs["Color"]
    def vscale(v, f):
        n = node("ShaderNodeVectorMath", operation="SCALE"); L.new(v, n.inputs[0]); setin(n, "Scale", f); return n.outputs["Vector"]
    def noise(vec, scale, detail=4.0, rough=0.55, distortion=0.0):
        n = node("ShaderNodeTexNoise", noise_dimensions="3D", normalize=True)
        setin(n, "Vector", vec); setin(n, "Scale", scale); setin(n, "Detail", detail); setin(n, "Roughness", rough); setin(n, "Distortion", distortion)
        return n.outputs["Fac"]
    def smul(a, b): return math("MULTIPLY", a, b)

    geo = node("ShaderNodeNewGeometry"); pos, nrm = geo.outputs["Position"], geo.outputs["Normal"]
    sep = node("ShaderNodeSeparateXYZ"); L.new(pos, sep.inputs[0]); px, py, pz = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
    scale = gi.outputs["Scale"]
    def amt(name, min_stage):   # 段階が足りないときは強さ0
        return gi.outputs[name] if stage >= min_stage else 0.0

    # ① エッジの塗装剥げ：角の検出 → ノイズで欠けさせる
    bev = node("ShaderNodeBevel", samples=6); L.new(gi.outputs["Edge Radius"], bev.inputs["Radius"])
    dot_e = node("ShaderNodeVectorMath", operation="DOT_PRODUCT"); L.new(bev.outputs["Normal"], dot_e.inputs[0]); L.new(nrm, dot_e.inputs[1])
    edge = mrange(math("SUBTRACT", 1.0, dot_e.outputs["Value"]), 0.0, 0.12, 0.0, 1.0)
    chip = noise(vscale(pos, math("MULTIPLY", scale, 90.0)), 1.0, 7.0, 0.6)
    # 平らな面（edge=0）には出ない：角の強さ × ノイズ（欠け方のムラ）
    edge_m = mrange(smul(edge, math("ADD", 0.45, math("MULTIPLY", chip, 1.1))), 0.22, 0.55)
    edge_m = smul(edge_m, amt("Edge Wear", 2))

    # ② 隙間の汚れ：AO（入り隅ほど黒い）＋砂粒のムラ
    ao = node("ShaderNodeAmbientOcclusion", samples=8, inside=False, only_local=False); ao.inputs["Distance"].default_value = 0.10
    crev = mrange(math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.12, 0.7)
    grit = noise(vscale(pos, math("MULTIPLY", scale, 55.0)), 1.0, 5.0, 0.6)
    dirt_m = smul(smul(crev, math("ADD", 0.45, math("MULTIPLY", grit, 0.8))), amt("Crevice Dirt", 2))

    # ③ 上面の埃：上向きの面に、まだらに。隙間にもたまる
    up = node("ShaderNodeVectorMath", operation="DOT_PRODUCT"); L.new(nrm, up.inputs[0]); up.inputs[1].default_value = (0, 0, 1)
    top = mrange(up.outputs["Value"], 0.55, 0.95)
    patch = mrange(noise(vscale(pos, math("MULTIPLY", scale, 6.0)), 1.0, 4.0, 0.5), 0.30, 0.65)
    fuzz = mrange(noise(vscale(pos, math("MULTIPLY", scale, 70.0)), 1.0, 3.0, 0.5), 0.2, 0.8, 0.55, 1.0)
    dust_m = math("ADD", smul(smul(top, patch), fuzz), smul(crev, 0.18), clamp=True)
    dust_m = smul(dust_m, amt("Top Dust", 3))

    # ④ 床際の汚れ：低い所ほど濃い（下から這い上がる）＋床の部屋の四隅・壁ぎわ
    wob = math("MULTIPLY", math("SUBTRACT", noise(vscale(pos, math("MULTIPLY", scale, 5.0)), 1.0, 5.0, 0.55), 0.5), 0.22)
    rise = mrange(math("ADD", pz, wob), 0.0, 0.30, 1.0, 0.0)
    ax = math("SUBTRACT", ROOM_HX, math("ABSOLUTE", px)); ay = math("SUBTRACT", ROOM_HY, math("ABSOLUTE", py))
    wall_d = math("MINIMUM", ax, ay)
    near_wall = mrange(math("ADD", wall_d, math("MULTIPLY", wob, 0.6)), 0.0, 0.26, 1.0, 0.0)
    low = mrange(pz, 0.03, 0.10, 1.0, 0.0)
    grime_m = math("MAXIMUM", rise, smul(near_wall, low))
    grime_m = smul(smul(grime_m, math("ADD", 0.55, math("MULTIPLY", grit, 0.6))), amt("Floor Grime", 3))

    # ⑤ 垂れ跡：縦に長いノイズ（Zを引き伸ばす）。縦の面だけ。まだらに出る
    stretch = node("ShaderNodeCombineXYZ")
    L.new(math("MULTIPLY", px, math("MULTIPLY", scale, 26.0)), stretch.inputs["X"])
    L.new(math("MULTIPLY", py, math("MULTIPLY", scale, 26.0)), stretch.inputs["Y"])
    L.new(math("MULTIPLY", pz, math("MULTIPLY", scale, 1.6)), stretch.inputs["Z"])
    streak = mrange(noise(stretch.outputs["Vector"], 1.0, 3.0, 0.5), 0.56, 0.68)
    vert = mrange(math("ABSOLUTE", up.outputs["Value"]), 0.45, 0.10)
    dpatch = mrange(noise(vscale(pos, math("MULTIPLY", scale, 3.0)), 1.0, 3.0, 0.5), 0.52, 0.72)
    top_fade = mrange(pz, 2.4, 0.4, 0.2, 1.0)   # 高い所ほど濃く（上から垂れる）
    drip_m = smul(smul(smul(streak, vert), math("ADD", dpatch, smul(crev, 0.3))), smul(top_fade, amt("Drips", 4)))

    # ⑥ 指紋：ボロノイの細胞ごとに、渦（輪）のあと
    vor = node("ShaderNodeTexVoronoi", voronoi_dimensions="3D", feature="F1"); vor.inputs["Randomness"].default_value = 1.0
    L.new(vscale(pos, math("MULTIPLY", scale, 17.0)), vor.inputs["Vector"]); vor.inputs["Scale"].default_value = 1.0
    cell_r = node("ShaderNodeSeparateColor"); L.new(vor.outputs["Color"], cell_r.inputs[0])
    present = mrange(cell_r.outputs["Red"], 0.72, 0.78)
    dist = vor.outputs["Distance"]
    blob = mrange(dist, 0.46, 0.20, 0.0, 1.0)
    rings = math("ADD", 0.55, math("MULTIPLY", math("SINE", math("MULTIPLY", dist, 85.0)), 0.45))
    fp = smul(smul(present, blob), rings)
    fp = smul(fp, amt("Fingerprints", 4))

    # --- 合成 ---
    base = gi.outputs["Base Color"]
    col = mixc(base, gi.outputs["Edge Color"], edge_m)
    col = mixc(col, gi.outputs["Dirt Color"], dirt_m)
    col = mixc(col, gi.outputs["Dust Color"], dust_m)
    col = mixc(col, gi.outputs["Grime Color"], grime_m)
    col = mixc(col, gi.outputs["Drip Color"], drip_m)
    col = mixc(col, (0.0, 0.0, 0.0, 1), math("MULTIPLY", fp, 0.30))   # 脂は少し暗い
    rough = gi.outputs["Roughness"]
    rough = lerp(rough, 0.40, edge_m)                        # 剥げた所は少しつるっと
    rough = lerp(rough, 0.95, math("MAXIMUM", dirt_m, math("MAXIMUM", dust_m, grime_m)))
    rough = lerp(rough, 0.80, drip_m)
    rough = smul(rough, math("SUBTRACT", 1.0, math("MULTIPLY", fp, 0.65)))   # 指紋はつやが出る
    metal = lerp(gi.outputs["Metallic"], gi.outputs["Wear Metallic"], edge_m)
    L.new(col, go.inputs["Base Color"]); L.new(rough, go.inputs["Roughness"]); L.new(metal, go.inputs["Metallic"])
    return ng

def wear_material(name, base=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, edge=0.0, dirt=0.0, dust=0.0, grime=0.0, drips=0.0, fp=0.0,
                  edge_color=(0.55, 0.5, 0.42), wear_metal=0.0, dust_color=None, dirt_color=None, grime_color=None, scale=1.0,
                  edge_radius=0.01, pattern=None, bump=None, alpha=1.0):
    """pattern: (color出力ソケットを作る関数 nt→socket) ／ bump: (高さを作る関数 nt→socket, 強さ)"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    g = nt.nodes.new("ShaderNodeGroup"); g.node_tree = bpy.data.node_groups["SubstanceWear"]
    def put(n, v):
        if n in g.inputs:
            s = g.inputs[n]
            s.default_value = (*v, 1) if (isinstance(v, tuple) and len(v) == 3) else v
    put("Base Color", base); put("Roughness", rough); put("Metallic", metal); put("Edge Wear", edge); put("Edge Color", edge_color)
    put("Wear Metallic", wear_metal); put("Edge Radius", edge_radius); put("Crevice Dirt", dirt); put("Top Dust", dust); put("Floor Grime", grime)
    put("Drips", drips); put("Fingerprints", fp); put("Scale", scale)
    if dust_color: put("Dust Color", dust_color)
    if dirt_color: put("Dirt Color", dirt_color)
    if grime_color: put("Grime Color", grime_color)
    if pattern:
        col = pattern(nt); nt.links.new(col, g.inputs["Base Color"])
    nt.links.new(g.outputs["Base Color"], bsdf.inputs["Base Color"]); nt.links.new(g.outputs["Roughness"], bsdf.inputs["Roughness"])
    nt.links.new(g.outputs["Metallic"], bsdf.inputs["Metallic"])
    if bump:
        height, strength = bump(nt)
        b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = strength; b.inputs["Distance"].default_value = 0.01
        nt.links.new(height, b.inputs["Height"]); nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        try: m.blend_method = "BLEND"
        except Exception: pass
        try: m.surface_render_method = "BLENDED"
        except Exception: pass
    return m
