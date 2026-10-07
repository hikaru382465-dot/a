"""
炎の精霊（ふわふわ待機・8コマ・右向き）。丸くひかる体、2つの明るい目、うしろへなびく炎のしっぽ。
1ドットの暗い輪郭、左上から光、まわりに点々とした光のもや（半透明っぽさは、網点で出す）。
python gen_fire_spirit.py → assets/effects/fire_spirit_sheet.png（64×64 を 4列×2行）/ fire_spirit.gif / fire_spirit_preview.png
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "effects"); os.makedirs(OUT, exist_ok=True)
CW = CH = 64; N = 8
pal, _ = pxl.load_palette(); FIRE = np.array(pal["f"], np.uint8)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
yy, xx = np.mgrid[0:CH, 0:CW]; X, Y = xx + .5, yy + .5

def h3(ix, iy, iz, seed=0):
    ix, iy, iz = (np.asarray(a, np.int64) for a in (ix, iy, iz))
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
    h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return (h % 100003) / 100003.0
def noise3(x, y, z, seed=0):
    x0, y0, z0 = np.floor(x), np.floor(y), np.floor(z); fx, fy, fz = x - x0, y - y0, z - z0
    sm = lambda t: t * t * (3 - 2 * t); fx, fy, fz = sm(fx), sm(fy), sm(fz); r = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz); r = r + w * h3(x0 + dx, y0 + dy, z0 + dz, seed)
    return r
def dilate(m):
    o = m.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): o |= np.roll(np.roll(m, dy, 0), dx, 1)
    return o

def frame(i):
    t = i / N; th = 2 * math.pi * t
    cx, cy = 36.0, 30.0 - math.sin(th) * 2.0                       # ふわふわ上下
    sq = .05 * math.cos(2 * th); rx, ry = 10.5 * (1 + sq), 10.5 * (1 - sq)
    # --- 体
    dB = np.hypot((X - cx) / rx, (Y - cy) / ry)
    lit = np.clip(-((X - cx) / rx * .55 + (Y - cy) / ry * .65), 0, 1)
    flick = .5 * (noise3(X * .22, Y * .22, math.cos(th) * 1.7, 3) + noise3(X * .22 + 17, Y * .22, math.sin(th) * 1.7, 4)) - .5
    heat_body = np.where(dB < 1, .42 + .5 * np.clip(1 - dB, 0, 1) ** .8 + .28 * lit + flick * .25, 0)
    # --- しっぽ：うしろ（左）へなびき、波うつ。先ほど細く、うす暗く
    best_d = np.full((CH, CW), 1e9); best_s = np.zeros((CH, CW)); best_w = np.ones((CH, CW))
    for s in np.linspace(0, 1, 44):
        tx = cx - 6 - s * 26; ty = cy + 3 + math.sin(th - s * 3.4) * 3.6 * (.25 + s) + s * s * 3
        w = 6.2 * (1 - s) ** .85 + .4
        d = np.hypot(X - tx, Y - ty) / w
        m = d < best_d; best_d = np.where(m, d, best_d); best_s = np.where(m, s, best_s); best_w = np.where(m, w, best_w)
    heat_tail = np.clip(1 - best_d, 0, 1) ** .8 * (1 - best_s) ** .55 * .85 + flick * .3 * (best_d < 1)
    heat_tail = np.where(best_d < 1, heat_tail, 0)
    # --- 頭の上のちいさな炎の舌（ゆれて高さが変わる）
    heat_t = np.zeros((CH, CW))
    for k, (ax, ph, hh) in enumerate(((-3.5, 0.0, 6.5), (2.5, 2.1, 8.0), (7.0, 4.0, 5.0))):
        by = cy - ry * .45; h = hh + ry * .45 + 2.4 * math.sin(2 * th + ph); bx = cx + ax + math.sin(th + ph) * 1.2
        up = by - Y; wd = 2.8 * np.clip(1 - up / h, 0, 1) ** .9
        m = (up > -2) & (up < h) & (np.abs(X - bx - math.sin(th * 2 + ph) * up * .12) < wd)
        heat_t = np.maximum(heat_t, np.where(m, .74 * np.clip(1 - up / (h + ry * .45 + 1), 0, 1) ** .7 + .06, 0))
    heat = np.maximum(np.maximum(heat_body, heat_tail), heat_t)
    on = (heat > .14) | (dB < 1)
    er = lambda m: ~dilate(~m)
    on = er(dilate(dilate(on)))                                   # すき間をうめる
    on = dilate(er(er(on)))                                       # 細いとげを消す
    on |= (dB < 1)
    q = heat * 7.0 + (BAYER[yy % 4, xx % 4] - .5) * .5
    idx = np.clip(np.floor(q).astype(int), 1, 7)
    # 浮いた点を消す
    nb = sum(np.roll(np.roll(on, dy, 0), dx, 1).astype(int) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    on &= ~((dB >= 1) & (nb == 0))
    img = np.zeros((CH, CW, 4), np.uint8); img[on, :3] = FIRE[idx[on]]; img[on, 3] = 255
    # --- 暗い輪郭（1ドット）
    outl = dilate(on) & ~on; img[outl, :3] = FIRE[0]; img[outl, 3] = 255
    # --- 光のもや：網点の半透明っぽさ（外へ行くほど少なく、色もうすく）
    M = on | outl; ring = M; cols = (3, 3, 2, 2, 1); prob = (.7, .45, .28, .16, .08)
    for k in range(5):
        nxt = dilate(ring); r_ = nxt & ~ring & ~M
        thr = h3(xx, yy, i * 0 + k, 11 + k)
        sel = r_ & (thr < prob[k] * .8); img[sel, :3] = FIRE[cols[k]]; img[sel, 3] = 255
        ring = nxt
    # --- 目：2つの明るい目（黒いふちに、白い芯）。7コマ目でまばたき
    bl = (i == 6)
    EYE = (".##.", "#WW#", "#WW#", "#WW#", ".##.")
    EYEB = (".##.", "####", ".##.")
    for ex in (cx + .4, cx + 5.4):
        x0 = int(round(ex)) - 1; rows = EYE if not bl else EYEB; y0 = int(round(cy - 3)) if not bl else int(round(cy - 1))
        for ry_, row in enumerate(rows):
            for rx_, ch in enumerate(row):
                if ch == ".": continue
                px, py = x0 + rx_, y0 + ry_
                if 0 <= px < CW and 0 <= py < CH: img[py, px, :3] = FIRE[7] if ch == "W" else FIRE[0]; img[py, px, 3] = 255
    # --- 火の粉：ゆっくり上へ
    for j in range(5):
        ph = (t * 1 + j * .21) % 1.0
        sx = cx - 12 + j * 7 + math.sin(ph * 6 + j) * 2; sy = cy + 4 - ph * 30
        if sy < 2: continue
        cc = FIRE[6] if ph < .35 else FIRE[5] if ph < .6 else FIRE[3] if ph < .85 else FIRE[2]
        px, py = int(sx), int(sy)
        if 0 <= px < CW and 0 <= py < CH and img[py, px, 3] == 0: img[py, px, :3] = cc; img[py, px, 3] = 255
    return img

frames = [frame(i) for i in range(N)]
sheet = np.zeros((CH * 2, CW * 4, 4), np.uint8)
for i, f in enumerate(frames): sheet[(i // 4) * CH:(i // 4 + 1) * CH, (i % 4) * CW:(i % 4 + 1) * CW] = f
Image.fromarray(sheet).save(os.path.join(OUT, "fire_spirit_sheet.png"))
bgc = (20, 18, 28, 255); k = 5
gifs = []
for f in frames:
    im = Image.fromarray(f).resize((CW * k, CH * k), Image.NEAREST); bg = Image.new("RGBA", im.size, bgc); bg.alpha_composite(im); gifs.append(bg.convert("RGB"))
gifs[0].save(os.path.join(OUT, "fire_spirit.gif"), save_all=True, append_images=gifs[1:], duration=110, loop=0)
big = Image.fromarray(sheet).resize((CW * 4 * 4, CH * 2 * 4), Image.NEAREST); bg = Image.new("RGBA", big.size, bgc); bg.alpha_composite(big); bg.convert("RGB").save(os.path.join(OUT, "fire_spirit_preview.png")); print("ok")
