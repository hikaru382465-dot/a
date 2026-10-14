"""
炎の5連撃エフェクト（下ぎり右→下ぎり左→横なぎ→たて斬り→しあげのX字）。元は炎の斬撃。1コマ 160×128 ドット、10コマ。
弧にそって炎がひろがり、先頭が一番熱く（白〜黄）、うしろへ行くほど赤くなって、上へ舞いあがって消える。
python gen_fire_combo.py → assets/effects/fire_combo_*.png / fire_combo.gif
"""
import os, math
import numpy as np
from PIL import Image
import pxl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "effects"); os.makedirs(OUT, exist_ok=True)
W, H, N = 160, 128, 10
pal, _ = pxl.load_palette(); FIRE = np.array(pal["f"], np.uint8)          # 炎の8段
rng = np.random.default_rng(3)

def h3(ix, iy, iz, seed=0):
    ix, iy, iz = (np.asarray(a, np.int64) for a in (ix, iy, iz))
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
    h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return (h % 100003) / 100003.0
def noise3(x, y, z, seed=0):
    x0, y0, z0 = np.floor(x), np.floor(y), np.floor(z); fx, fy, fz = x - x0, y - y0, z - z0
    sm = lambda t: t * t * (3 - 2 * t); fx, fy, fz = sm(fx), sm(fy), sm(fz)
    r = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                r = r + w * h3(x0 + dx, y0 + dy, z0 + dz, seed)
    return r
def fbm(x, y, z, seed=0):
    return .55 * noise3(x, y, z, seed) + .3 * noise3(x * 2.1, y * 2.1, z * 2.1, seed + 1) + .15 * noise3(x * 4.3, y * 4.3, z * 4.3, seed + 2)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
yy, xx = np.mgrid[0:H, 0:W].astype(float)

# 弧：左上から右下へふる。中心は画面の下のほう
ease = lambda t: t * t * (3 - 2 * t)

def frame(i, N, P):
    CX, CY, R, RY = P['cx'], P['cy'], P['r'], P.get('ry', 1.0)
    A0, A1 = math.radians(P['a0']), math.radians(P['a1'])
    MH = P.get('half', 21); LICK = P.get('lick', 1.0)
    t = i / (N - 1)
    head = A0 + (A1 - A0) * ease(min(1, t / .55))                   # 先頭の角度
    tail = A0 + (A1 - A0) * (max(0, (t - .34) / .66) ** 1.7)        # しっぽの角度（おくれて動く）
    life = 1.0 if t < .5 else max(0.0, 1 - ((t - .5) / .5) ** 1.6)    # だんだん消える
    # --- 炎をゆらす：位置を上向きにゆがめて読む（炎が上へなめるように）
    wx = (fbm(xx * .035, yy * .035 - t * 2.6, t * 1.7, 5) - .5) * 14
    wy = (fbm(xx * .035 + 9, yy * .035 - t * 3.2, t * 1.7, 9) - .5) * 12 + 14 * np.clip((yy - 20) / 100, 0, 1) * 0 + t * 9
    px, py = xx + wx, yy + wy
    dx, dy = px - CX, (py - CY) / RY
    r = np.hypot(dx, dy); th = np.arctan2(dy, dx)
    # 弧の上の位置 u（しっぽ0 → 先頭1）
    span = max(1e-3, head - tail)
    dth = (th - tail + math.pi) % (2 * math.pi) - math.pi
    u = dth / span
    inarc = (u >= 0) & (u <= 1)
    # 太さ：先頭が太く、しっぽは細い（なめらかに）
    prof = np.where(inarc, np.clip(u, 0, 1) ** .85 * np.clip((1 - np.clip(u, 0, 1)) * 12, 0, 1), 0)      # 先頭が太く、先はするどく、うしろへ細く尾を引く
    half = (1.5 + MH * prof) * (.4 + .6 * life)
    dsig = r - (R - 4 * np.sin(np.pi * np.clip(u, 0, 1)))                # 弧の中心線からの距離（外がわが＋）
    lick = fbm(th * 9 + 3, r * .05 - t * 3.5, t * 2.5, 33)               # 外がわへ伸びる炎の舌（ノイズでちぎれる）
    outer = half * (.9 + 2.4 * LICK * np.clip((lick - .35) * 2.2, 0, 1) * np.clip(u, 0, 1) ** .5)
    inner = half * .75
    dn = np.where(dsig > 0, dsig / np.maximum(outer, 1e-3), -dsig / np.maximum(inner, 1e-3))
    core = np.clip(1 - dn, 0, 1) * inarc
    # 熱：中心線が熱く、先頭が熱く、しっぽは冷たい
    heat = core ** .8 * (.45 + .55 * np.clip(u, 0, 1) ** .7) * (.3 + .7 * life)
    # 炎のゆらぎ（ノイズ）：ふちをちぎらせ、舌のように上へ伸ばす
    n = fbm(xx * .06, yy * .06 - t * 3.0, t * 2.0, 21)
    heat = heat + (n - .5) * .35 * (heat > .02) + (n - .5) * .08
    # 上へ舞いあがる炎の舌（弧の上がわ）：弧のうち先頭に近い所から
    tongue = np.clip(1 - np.abs(xx - (CX + R * np.cos(head - .25))) / 22, 0, 1) * np.clip((CY + R * np.sin(head - .25) - yy) / 38, 0, 1) * np.clip(yy / 70, 0, 1) * (1 if t < .45 else 0) * 0
    heat = np.clip(heat * P.get('gain', 1.0), 0, 1)                    # 打が進むほど熱く（白寄り）
    # --- 網点（ディザ）で段階に切る
    q = heat * 7.4 + (BAYER[(yy.astype(int) % 4), (xx.astype(int) % 4)] - .5) * .45
    idx = np.clip(np.floor(q), -1, 7).astype(int)
    on = (heat > .1) & (idx >= 0)
    idx = np.where(on, idx, -1)
    # --- ぽつんと浮いた点を消す（4近傍に仲間がいない点）
    m = idx >= 0; nb = np.zeros_like(m, int)
    for sy, sx in ((1, 0), (-1, 0), (0, 1), (0, -1)): nb += np.roll(np.roll(m, sy, 0), sx, 1)
    idx = np.where(m & (nb == 0), -1, idx)
    img = np.zeros((H, W, 4), np.uint8)
    ok = idx >= 0; img[ok, :3] = FIRE[idx[ok]]; img[ok, 3] = 255
    # --- 火の粉：先頭から飛び散る（コマごとに位置が動く）
    g = np.random.default_rng(100)                                    # 同じ火の粉を、時間で動かす
    nsp = P.get('sparks', 26)
    for k in range(nsp):
        a = g.uniform(A0 + .2, A1); born = g.uniform(.1, .6); spd = g.uniform(14, 40); ang = g.uniform(-2.6, -.3)
        age = t - born
        if age < 0 or age > .45: continue
        sx = CX + R * math.cos(a) + math.cos(ang) * spd * age * 5; sy = CY + R * RY * math.sin(a) + math.sin(ang) * spd * age * 5 + 40 * age * age
        lv = 1 - age / .45
        c = FIRE[7 if lv > .75 else 6 if lv > .55 else 5 if lv > .35 else 4 if lv > .2 else 3]
        s = 2 if lv > .5 else 1
        for ddy in range(s):
            for ddx in range(s):
                X, Y = int(sx) + ddx, int(sy) + ddy
                if 0 <= X < W and 0 <= Y < H: img[Y, X, :3] = c; img[Y, X, 3] = 255
    # 剣の軌道の光：弧の中心線に、細い白い線。はやく消える
    tr = np.clip(1 - np.abs(dsig) / 1.6, 0, 1) * inarc * np.clip(u, 0, 1) ** 1.2 * max(0.0, 1 - t / .62)
    img[tr > .5, :3] = FIRE[7]; img[tr > .5, 3] = 255
    return img


def arc_from_points(S, E, bulge):
    """始点S→終点Eへふる弧。bulge＞0 で、進行方向の左がわ（画面では上や外）へふくらむ"""
    S = np.array(S, float); E = np.array(E, float); mid = (S + E) / 2; d = E - S; L = np.hypot(*d)
    nrm = np.array([d[1], -d[0]]) / L                                  # 進行方向に対して画面の「上寄り」の法線（y下向き座標）
    M = mid + nrm * bulge
    ax, ay = S; bx, by = M; cx, cy = E
    D = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / D
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / D
    r = math.hypot(ax - ux, ay - uy)
    a_s = math.atan2(ay - uy, ax - ux); a_m = math.atan2(by - uy, bx - ux); a_e = math.atan2(cy - uy, cx - ux)
    wrap = lambda a, ref: (a - ref + math.pi) % (2 * math.pi) - math.pi
    dm = wrap(a_m, a_s); de = wrap(a_e, a_s)
    if abs(de) < abs(dm) or dm * de < 0: de += 2 * math.pi * (1 if dm > 0 else -1)      # Mを通るほうの向きにする
    return dict(cx=ux, cy=uy, r=r, a0=math.degrees(a_s), a1=math.degrees(a_s + de))

HITS = [   # 打が進むほど、太く・熱く・火の粉が多く・炎の舌が長くなる
 dict(name="hit1_ななめ下ぎり", half=13, gain=.9, sparks=18, lick=.9, **arc_from_points((20, 30), (140, 102), 30)),
 dict(name="hit2_ななめ下ぎり左", half=15, gain=.97, sparks=26, lick=1.1, **arc_from_points((140, 30), (20, 100), 30)),
 dict(name="hit3_横なぎ", half=17, gain=1.05, sparks=36, lick=1.25, **arc_from_points((152, 90), (8, 70), 26)),
 dict(name="hit4_たて斬り", half=23, gain=1.12, sparks=48, lick=1.5, **arc_from_points((90, 14), (70, 108), 26)),
]
NH = 8
allf = []
for h in HITS:
    fr = [frame(i, NH, h) for i in range(NH)]
    allf.append(fr)
# --- 5撃目：しあげ（大きなX字を2本重ねて、中央から衝撃のわ）
NF = 12
P1 = dict(half=21, gain=1.12, lick=1.4, sparks=72, **arc_from_points((26, 30), (134, 96), 26)); P2 = dict(half=21, gain=1.12, lick=1.4, sparks=0, **arc_from_points((134, 30), (26, 96), 26))
x1 = [frame(i, NF, P1) for i in range(NF)]; x2 = [frame(i, NF, P2) for i in range(NF)]
fin = []
yy_, xx_ = np.mgrid[0:H, 0:W].astype(float)
for i in range(NF):
    f = np.zeros((H, W, 4), np.uint8)
    for src in (x1[i], x2[i]):
        m = src[..., 3] > 0; f[m] = src[m]
    t = i / (NF - 1)
    if .3 < t < .9:                                                 # 交点で爆発：白い閃光→炎のわ（ふとい）
        k = (t - .3) / .6; rr = 8 + k * 56; wd = 9 * (1 - k) + 1.5
        d = np.hypot((xx_ - 80) * 1.0, (yy_ - 76) * .8) - rr
        ring = (np.abs(d) < wd) & (f[..., 3] == 0)
        lv = np.clip(1 - np.abs(d) / wd, 0, 1) * (1 - k * .6)
        idx = np.clip((lv * 7.6).astype(int), 0, 7)
        f[ring, :3] = FIRE[idx[ring]]; f[ring, 3] = 255
        if k < .35:
            fl = (np.hypot(xx_ - 80, (yy_ - 76) * .9) < 16 * (1 - k * 2)) & (f[..., 3] == 0); f[fl, :3] = FIRE[7]; f[fl, 3] = 255
    fin.append(f)
allf.append(fin)
bgc = (22, 18, 34, 255)
# --- 出力：打ごとのシート、全部をつなげたシート、GIF（つなぎ目で少しためる）
frames = [f for fr in allf for f in fr]
for n, fr in enumerate(allf, 1):
    sh = np.zeros((H, W * len(fr), 4), np.uint8)
    for i, f in enumerate(fr): sh[:, i * W:(i + 1) * W] = f
    Image.fromarray(sh).save(os.path.join(OUT, f"fire_combo_hit{n}_sheet.png"))
tot = np.zeros((H, W * len(frames), 4), np.uint8)
for i, f in enumerate(frames): tot[:, i * W:(i + 1) * W] = f
Image.fromarray(tot).save(os.path.join(OUT, "fire_combo_all_sheet.png"))
gifs, dur = [], []
for n, fr in enumerate(allf):
    for i, f in enumerate(fr):
        im = Image.fromarray(f).resize((W * 3, H * 3), Image.NEAREST); bg = Image.new("RGBA", im.size, bgc); bg.alpha_composite(im); gifs.append(bg.convert("RGB"))
        dur.append(60 if i < len(fr) - 2 else 90)
    gifs.append(Image.new("RGB", (W * 3, H * 3), bgc[:3])); dur.append(120 if n < 4 else 400)           # 打と打のあいだ
gifs[0].save(os.path.join(OUT, "fire_combo.gif"), save_all=True, append_images=gifs[1:], duration=dur, loop=0)
cols = 8; rows = len(allf); cw, ch = W, H
prev = Image.new("RGB", (cols * cw + 0, rows * ch), bgc[:3])
for r, fr in enumerate(allf):
    for i, f in enumerate(fr[:cols]):
        im = Image.fromarray(f); bg = Image.new("RGBA", im.size, bgc); bg.alpha_composite(im); prev.paste(bg.convert("RGB"), (i * cw, r * ch))
prev = prev.resize((prev.width * 2, prev.height * 2), Image.NEAREST); prev.save(os.path.join(OUT, "fire_combo_preview.png")); print("ok", len(frames), "コマ")
