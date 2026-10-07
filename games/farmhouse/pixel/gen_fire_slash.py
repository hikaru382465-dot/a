"""
炎の斬撃エフェクト（1回きり）。1コマ 160×128 ドット、10コマ。
弧にそって炎がひろがり、先頭が一番熱く（白〜黄）、うしろへ行くほど赤くなって、上へ舞いあがって消える。
python gen_fire_slash.py → assets/effects/fire_slash_sheet.png / fire_slash.gif / fire_slash_preview.png と、コマ個別 pxl
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
CX, CY, R = 80.0, 122.0, 82.0
A0, A1 = math.radians(-168), math.radians(-14)                    # はじまりの角度・おわりの角度（右が0度、上が-90度）
ease = lambda t: t * t * (3 - 2 * t)

def frame(i):
    t = i / (N - 1)
    head = A0 + (A1 - A0) * ease(min(1, t / .55))                   # 先頭の角度
    tail = A0 + (A1 - A0) * (max(0, (t - .22) / .78) ** 1.35)        # しっぽの角度（おくれて動く）
    life = 1.0 if t < .5 else max(0.0, 1 - ((t - .5) / .5) ** 1.6)    # だんだん消える
    # --- 炎をゆらす：位置を上向きにゆがめて読む（炎が上へなめるように）
    wx = (fbm(xx * .035, yy * .035 - t * 2.6, t * 1.7, 5) - .5) * 14
    wy = (fbm(xx * .035 + 9, yy * .035 - t * 3.2, t * 1.7, 9) - .5) * 12 + 14 * np.clip((yy - 20) / 100, 0, 1) * 0 + t * 9
    px, py = xx + wx, yy + wy
    dx, dy = px - CX, py - CY
    r = np.hypot(dx, dy); th = np.arctan2(dy, dx)
    # 弧の上の位置 u（しっぽ0 → 先頭1）
    span = max(1e-3, head - tail)
    u = (th - tail) / span
    inarc = (u >= 0) & (u <= 1)
    # 太さ：先頭が太く、しっぽは細い（なめらかに）
    prof = np.where(inarc, np.sin(np.pi * np.clip(u, 0, 1) ** .62), 0)
    half = (2 + 21 * prof ** 1.05) * (.4 + .6 * life)
    dsig = r - (R - 4 * np.sin(np.pi * np.clip(u, 0, 1)))                # 弧の中心線からの距離（外がわが＋）
    lick = fbm(th * 9 + 3, r * .05 - t * 3.5, t * 2.5, 33)               # 外がわへ伸びる炎の舌（ノイズでちぎれる）
    outer = half * (.9 + 2.4 * np.clip((lick - .35) * 2.2, 0, 1) * np.clip(u, 0, 1) ** .5)
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
    heat = np.clip(heat, 0, 1)
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
    nsp = 26
    for k in range(nsp):
        a = g.uniform(A0 + .2, A1); born = g.uniform(.1, .6); spd = g.uniform(14, 40); ang = g.uniform(-2.6, -.3)
        age = t - born
        if age < 0 or age > .45: continue
        sx = CX + R * math.cos(a) + math.cos(ang) * spd * age * 5; sy = CY + R * math.sin(a) + math.sin(ang) * spd * age * 5 + 40 * age * age
        lv = 1 - age / .45
        c = FIRE[7 if lv > .75 else 6 if lv > .55 else 5 if lv > .35 else 4 if lv > .2 else 3]
        s = 2 if lv > .5 else 1
        for ddy in range(s):
            for ddx in range(s):
                X, Y = int(sx) + ddx, int(sy) + ddy
                if 0 <= X < W and 0 <= Y < H: img[Y, X, :3] = c; img[Y, X, 3] = 255
    return img

frames = [frame(i) for i in range(N)]
sheet = np.zeros((H, W * N, 4), np.uint8)
for i, f in enumerate(frames): sheet[:, i * W:(i + 1) * W] = f
Image.fromarray(sheet).save(os.path.join(OUT, "fire_slash_sheet.png"))
bgc = (22, 18, 34, 255); gifs = []
for f in frames:
    im = Image.fromarray(f).resize((W * 3, H * 3), Image.NEAREST); bg = Image.new("RGBA", im.size, bgc); bg.alpha_composite(im); gifs.append(bg.convert("RGB"))
gifs[0].save(os.path.join(OUT, "fire_slash.gif"), save_all=True, append_images=gifs[1:], duration=70, loop=0)
cols = 5; rows = 2; cw, ch = W * 2, H * 2
prev = Image.new("RGB", (cols * cw, rows * ch), bgc[:3])
for i, f in enumerate(frames):
    im = Image.fromarray(f).resize((cw, ch), Image.NEAREST); bg = Image.new("RGBA", im.size, bgc); bg.alpha_composite(im); prev.paste(bg.convert("RGB"), ((i % cols) * cw, (i // cols) * ch))
prev.save(os.path.join(OUT, "fire_slash_preview.png")); print("ok", prev.size)
