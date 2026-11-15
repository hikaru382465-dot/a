"""部屋の材質を、すべてプロシージャルにする（画像は使わない）。
下地の柄（板・壁・木目・キルト・毛足）もノードで作り、その上に SubstanceWear（汚しの共通グループ）を、材質ごとに強さを変えて重ねる。
例外：光る画面の中身（モニターの壁紙・置き時計の数字・窓の外の街・壁の写真）は『絵』なので、画像のまま。"""
import bpy
import wear_group as W

def _node(nt, t, loc=(0, 0), **props):
    n = nt.nodes.new(t); n.location = loc
    for k, v in props.items(): setattr(n, k, v)
    return n

def _pos(nt):
    return _node(nt, "ShaderNodeNewGeometry").outputs["Position"]

def _mapping(nt, vec, scale=(1, 1, 1), rot=(0, 0, 0)):
    m = _node(nt, "ShaderNodeMapping", vector_type="POINT")
    nt.links.new(vec, m.inputs["Vector"]); m.inputs["Scale"].default_value = scale; m.inputs["Rotation"].default_value = rot
    return m.outputs["Vector"]

def _noise(nt, vec, scale, detail=4.0, rough=0.5, distortion=0.0):
    n = _node(nt, "ShaderNodeTexNoise", noise_dimensions="3D", normalize=True)
    nt.links.new(vec, n.inputs["Vector"]); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough; n.inputs["Distortion"].default_value = distortion
    return n.outputs["Fac"]

def _ramp(nt, fac, stops):
    r = _node(nt, "ShaderNodeValToRGB")
    cr = r.color_ramp; cr.elements[0].position = stops[0][0]; cr.elements[0].color = (*stops[0][1], 1)
    cr.elements[1].position = stops[-1][0]; cr.elements[1].color = (*stops[-1][1], 1)
    for pos, c in stops[1:-1]:
        e = cr.elements.new(pos); e.color = (*c, 1)
    nt.links.new(fac, r.inputs["Fac"]); return r.outputs["Color"]

# ---- 下地の柄 ----
def floor_pattern(nt):
    pos = _pos(nt)
    br = _node(nt, "ShaderNodeTexBrick", offset=0.5, offset_frequency=2, squash=1.0, squash_frequency=2)
    nt.links.new(pos, br.inputs["Vector"])
    for k, v in {"Scale": 1.0, "Mortar Size": 0.006, "Mortar Smooth": 0.1, "Bias": 0.0, "Brick Width": 0.9, "Row Height": 0.09}.items(): br.inputs[k].default_value = v
    br.inputs["Color1"].default_value = (0.14, 0.075, 0.04, 1); br.inputs["Color2"].default_value = (0.26, 0.15, 0.08, 1); br.inputs["Mortar"].default_value = (0.012, 0.008, 0.005, 1)
    grain = _noise(nt, _mapping(nt, pos, (3.0, 90.0, 1.0)), 1.0, 5.0, 0.6, 0.4)
    mul = _node(nt, "ShaderNodeMixRGB", blend_type="MULTIPLY", use_clamp=True)
    nt.links.new(br.outputs["Color"], mul.inputs["Color1"])
    g = _ramp(nt, grain, [(0.2, (0.62, 0.62, 0.62)), (0.8, (1.0, 1.0, 1.0))])
    nt.links.new(g, mul.inputs["Color2"]); mul.inputs["Fac"].default_value = 1.0
    return mul.outputs["Color"]

def wall_pattern(nt):
    n = _noise(nt, _pos(nt), 2.2, 8.0, 0.6)
    return _ramp(nt, n, [(0.3, (0.38, 0.36, 0.32)), (0.7, (0.50, 0.48, 0.43))])
def wall_bump(nt):
    pos = _pos(nt); return _noise(nt, pos, 140.0, 3.0, 0.5), 0.12

def wood_pattern(light=(0.40, 0.22, 0.11), dark=(0.20, 0.10, 0.05), scale=9.0):
    def f(nt):
        pos = _pos(nt)
        w = _node(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y", wave_profile="SIN")
        nt.links.new(_mapping(nt, pos, (1.0, 1.0, 1.0)), w.inputs["Vector"])
        w.inputs["Scale"].default_value = scale; w.inputs["Distortion"].default_value = 7.0; w.inputs["Detail"].default_value = 3.0; w.inputs["Detail Scale"].default_value = 1.5
        stretch = _noise(nt, _mapping(nt, pos, (2.0, 60.0, 60.0)), 1.0, 4.0, 0.55)
        mix = _node(nt, "ShaderNodeMath", operation="ADD", use_clamp=True)
        t = _node(nt, "ShaderNodeMath", operation="MULTIPLY"); nt.links.new(w.outputs["Fac"], t.inputs[0]); t.inputs[1].default_value = 0.55
        t2 = _node(nt, "ShaderNodeMath", operation="MULTIPLY"); nt.links.new(stretch, t2.inputs[0]); t2.inputs[1].default_value = 0.45
        nt.links.new(t.outputs[0], mix.inputs[0]); nt.links.new(t2.outputs[0], mix.inputs[1])
        return _ramp(nt, mix.outputs[0], [(0.0, dark), (1.0, light)])
    return f
def wood_bump(nt):
    pos = _pos(nt); return _noise(nt, _mapping(nt, pos, (1.0, 70.0, 70.0)), 1.0, 5.0, 0.6), 0.1

def duvet_pattern(nt):
    pos = _pos(nt)
    ck = _node(nt, "ShaderNodeTexChecker"); nt.links.new(_mapping(nt, pos, (9.0, 9.0, 9.0), (0, 0, 0.7854)), ck.inputs["Vector"])
    ck.inputs["Scale"].default_value = 1.0
    fine = _noise(nt, pos, 90.0, 3.0, 0.5)
    mix = _node(nt, "ShaderNodeMixRGB", blend_type="MIX"); mix.inputs["Fac"].default_value = 0.0
    c = _ramp(nt, fine, [(0.0, (0.31, 0.33, 0.39)), (1.0, (0.43, 0.45, 0.52))])
    return c
def duvet_bump(nt):
    pos = _pos(nt); return _noise(nt, pos, 40.0, 5.0, 0.6, 0.3), 0.5

def rug_pattern(nt):
    n = _noise(nt, _pos(nt), 260.0, 3.0, 0.5)
    return _ramp(nt, n, [(0.2, (0.075, 0.08, 0.09)), (0.8, (0.15, 0.155, 0.17))])
def rug_bump(nt): return _noise(nt, _pos(nt), 300.0, 2.0, 0.5), 0.5

def apply(M, stage=4):
    W.build_group(stage)
    wm = W.wear_material
    d = {}
    # 床：板、下からの汚れが主役
    d["floor"] = wm("floor", rough=0.24, dirt=0.5, dust=0.40, grime=0.65, drips=0.0, fp=0.12, scale=1.0, dust_color=(0.16, 0.14, 0.12), pattern=floor_pattern)
    d["wall"] = wm("wall", base=(0.45, 0.43, 0.39), rough=0.9, edge=0.7, edge_color=(0.60, 0.58, 0.52), dirt=0.55, dust=0.12, grime=1.0, drips=0.6, fp=0.12, pattern=wall_pattern, bump=wall_bump)
    d["ceiling"] = wm("ceiling", base=(0.30, 0.29, 0.27), rough=0.9, dirt=0.5, dust=0.1, grime=0.0, drips=0.5, fp=0.0, pattern=wall_pattern)
    wood = lambda nm, light, dark, rough, fpv=0.35: wm(nm, rough=rough, edge=0.9, edge_color=(0.46, 0.30, 0.17), dirt=0.65, dust=0.42, grime=0.5, drips=0.15, fp=fpv, edge_radius=0.006, pattern=wood_pattern(light, dark), bump=wood_bump)
    d["desk"] = wood("desk", (0.34, 0.18, 0.09), (0.15, 0.07, 0.035), 0.32, 0.5)
    d["bed_wood"] = wood("bed_wood", (0.28, 0.15, 0.07), (0.12, 0.06, 0.03), 0.40, 0.25)
    d["door"] = wm("door", rough=0.42, edge=0.9, edge_color=(0.42, 0.28, 0.16), dirt=0.7, dust=0.32, grime=0.7, drips=0.3, fp=0.55, edge_radius=0.006, pattern=wood_pattern((0.22, 0.10, 0.05), (0.10, 0.045, 0.02), 7.0), bump=wood_bump)
    d["frame_wood"] = wm("frame_wood", rough=0.5, edge=0.9, edge_color=(0.40, 0.27, 0.15), dirt=0.7, dust=0.4, grime=1.0, drips=0.2, fp=0.2, edge_radius=0.005, pattern=wood_pattern((0.17, 0.085, 0.045), (0.08, 0.04, 0.02), 6.0), bump=wood_bump)
    d["duvet"] = wm("duvet", rough=0.95, dirt=0.35, dust=0.30, grime=0.0, drips=0.0, fp=0.0, pattern=duvet_pattern, bump=duvet_bump)
    d["sheet"] = wm("sheet", base=(0.55, 0.55, 0.58), rough=0.95, dirt=0.3, dust=0.4)
    d["rug"] = wm("rug", rough=0.98, dirt=0.3, dust=0.45, grime=0.9, pattern=rug_pattern, bump=rug_bump)
    # 金属・プラスチック・陶器・ガラス
    d["black"] = wm("black_plastic", base=(0.015, 0.015, 0.018), rough=0.45, edge=0.7, edge_color=(0.13, 0.13, 0.14), dirt=0.5, dust=0.40, dust_color=(0.22, 0.22, 0.22), grime=0.2, fp=0.9, edge_radius=0.003)
    d["black_soft"] = wm("black_leather", base=(0.02, 0.02, 0.025), rough=0.55, edge=0.55, edge_color=(0.12, 0.11, 0.11), dirt=0.55, dust=0.40, dust_color=(0.22, 0.22, 0.22), fp=0.6, edge_radius=0.006)
    d["metal"] = wm("metal", base=(0.35, 0.35, 0.38), rough=0.4, metal=1.0, edge=0.5, edge_color=(0.65, 0.65, 0.68), wear_metal=1.0, dirt=0.5, dust=0.25, fp=0.7, edge_radius=0.003)
    d["steel_dark"] = wm("dark_metal", base=(0.04, 0.04, 0.045), rough=0.35, metal=0.9, edge=0.7, edge_color=(0.50, 0.50, 0.53), wear_metal=1.0, dirt=0.5, dust=0.3, grime=0.3, fp=0.6, edge_radius=0.003)
    d["lamp"] = wm("lamp", base=(0.02, 0.02, 0.022), rough=0.4, metal=0.8, edge=0.6, edge_color=(0.48, 0.47, 0.46), wear_metal=1.0, dirt=0.4, dust=0.35, fp=0.7, edge_radius=0.003)
    d["white_plastic"] = wm("white_plastic", base=(0.62, 0.62, 0.60), rough=0.5, edge=0.4, edge_color=(0.72, 0.70, 0.62), dirt=0.55, dust=0.5, fp=0.6, edge_radius=0.004)
    d["plastic_w"] = wm("switch_plate", base=(0.55, 0.55, 0.50), rough=0.4, edge=0.4, edge_color=(0.66, 0.62, 0.52), dirt=0.7, dust=0.4, fp=1.0, edge_radius=0.002)
    d["ceramic"] = wm("ceramic", base=(0.62, 0.60, 0.55), rough=0.3, edge=0.45, edge_color=(0.68, 0.64, 0.56), dirt=0.45, dust=0.15, fp=1.0, edge_radius=0.003)
    d["phone"] = wm("phone", base=(0.01, 0.01, 0.012), rough=0.15, metal=0.2, edge=0.3, edge_color=(0.2, 0.2, 0.22), dirt=0.2, dust=0.30, dust_color=(0.22, 0.22, 0.22), fp=1.0, edge_radius=0.002)
    d["window_frame"] = wm("window_frame", base=(0.30, 0.30, 0.31), rough=0.5, metal=0.6, edge=0.8, edge_color=(0.60, 0.60, 0.62), wear_metal=1.0, dirt=0.85, dust=0.5, grime=0.7, drips=0.6, fp=0.3, edge_radius=0.004)
    d["glass"] = wm("glass", base=(0.5, 0.6, 0.8), rough=0.05, dirt=0.5, dust=0.4, grime=0.2, drips=0.9, fp=1.0, alpha=0.12)
    d["sheer"] = wm("sheer", base=(0.55, 0.57, 0.62), rough=0.9, dirt=0.3, dust=0.5, grime=0.5, drips=0.1, alpha=0.32)
    d["curtain"] = wm("curtain", base=(0.07, 0.08, 0.13), rough=0.95, dirt=0.3, dust=0.6, grime=0.6, drips=0.0)
    d["bin"] = wm("bin", base=(0.12, 0.12, 0.13), rough=0.6, edge=0.5, edge_color=(0.30, 0.30, 0.32), dirt=0.6, dust=0.6, grime=0.7, fp=0.3, edge_radius=0.004)
    d["plant"] = wm("plant", base=(0.03, 0.12, 0.04), rough=0.6, dirt=0.3, dust=0.55, fp=0.0)
    d["pot"] = wm("pot", base=(0.22, 0.12, 0.08), rough=0.7, edge=0.5, edge_color=(0.45, 0.30, 0.20), dirt=0.5, dust=0.5, grime=0.6, edge_radius=0.004)
    d["jacket"] = wm("jacket", base=(0.06, 0.07, 0.09), rough=0.9, dirt=0.3, dust=0.7)
    d["backpack"] = wm("backpack", base=(0.03, 0.04, 0.05), rough=0.8, dirt=0.4, dust=0.7, grime=0.6, edge=0.3, edge_color=(0.15, 0.15, 0.16))
    d["sticky"] = wm("sticky", base=(0.85, 0.72, 0.30), rough=0.9, edge=0.4, edge_color=(0.9, 0.82, 0.5), dirt=0.2, dust=0.2, fp=0.4, edge_radius=0.002)
    for i, c in enumerate([(0.18, 0.05, 0.05), (0.05, 0.10, 0.18), (0.20, 0.17, 0.08), (0.08, 0.14, 0.09), (0.10, 0.08, 0.14), (0.22, 0.20, 0.17), (0.14, 0.07, 0.04)]):
        d[f"book{i}"] = wm(f"book{i}", base=c, rough=0.7, edge=0.85, edge_color=tuple(min(1.0, x * 2.2 + 0.18) for x in c), dirt=0.5, dust=0.45, fp=0.3, edge_radius=0.003)
    M.update(d)
    return d
