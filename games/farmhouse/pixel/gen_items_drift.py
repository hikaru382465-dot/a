"""
漂流物が、上下にゆれて水をはねながら、海を流れてくる場面（桟橋にちびキャラ）。
python gen_items_drift.py → assets/items/float/drift_scene.gif / drift_scene_frame0.png
漂流物は細かい版を半分の大きさにして、パレットの一番近い色にそろえて使う。
"""
import os, math
import numpy as np
from PIL import Image
import pxl
import gen_blonde_chibi as CH
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "assets", "items", "hd"); OUT = os.path.join(HERE, "..", "assets", "items", "float")
pal, _ = pxl.load_palette()
def col(f, s): return tuple(int(v) for v in pal[f][int(max(0, min(7, s)))])
ALL = np.array([pal[f][s] for f in pal for s in range(8)], float)
BAY = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
TAU = math.tau
W, H = 256, 120; HOR = 44; NF = 48
SPEED = (W + 56) / NF

def half(name):
    im = np.array(Image.open(os.path.join(SRC, name + ".png")).convert("RGBA")).astype(float)
    h, w = im.shape[:2]; h2, w2 = h // 2, w // 2
    out = np.zeros((h2, w2, 4), np.uint8)
    for y in range(h2):
        for x in range(w2):
            blk = im[y * 2:y * 2 + 2, x * 2:x * 2 + 2].reshape(-1, 4); a = blk[:, 3] > 0
            if a.sum() < 2: continue
            c = blk[a, :3].mean(0); j = ((ALL - c) ** 2).sum(1).argmin(); out[y, x, :3] = ALL[j]; out[y, x, 3] = 255
    return out

ITEMS = [("bottle", .52, 0.0, 66), ("rope", .66, .27, 80), ("coconut", .58, .55, 70), ("bag", .70, .15, 84), ("cloth", .58, .40, 64),
         ("stone_round", .70, .72, 78), ("coconut_cut", .62, .85, 86), ("stone_rock", .72, .33, 72)]
XS = [210, 40, 150, 100, 235, 175, 60, 120]
SPR = {n: half(n) for n, *_ in ITEMS}

def sea(t):
    Y, X = np.mgrid[0:H, 0:W]
    hh = np.sin(TAU * (X / 31.0 + Y / 11.0 - t)) * .5 + np.sin(TAU * (X / 17.0 - Y / 7.0 + t * 2)) * .35
    idx = np.clip(np.floor((hh + 1) / 2 * 2.4 + (BAY[Y % 4, X % 4] - .5) * .6).astype(int) + 2, 2, 4)
    near = np.clip((Y - HOR) / 18.0, 0, 1); idx = np.where(near < .5, np.maximum(1, idx - 1), idx)
    img = np.zeros((H, W, 4), np.uint8)
    for v in (1, 2, 3, 4): img[idx == v, :3] = col('w', v)
    img[..., 3] = 255
    sky = Y < HOR; g = np.clip(2 - (HOR - Y) / 22.0, 0, 2)
    s = np.where(BAY[Y % 4, X % 4] < (g / 2) % 1, np.floor(g) + 1, np.floor(g)).astype(int) + 1
    for v in np.unique(s[sky]): img[sky & (s == v), :3] = col('K', int(v))
    img[(X < 62) & (Y >= 102)] = (*col('D', 4), 255)
    deck = (X < 62) & (Y >= 102); img[deck & (Y == 102), :3] = col('D', 6)
    img[deck & (Y % 5 == 0) & (Y > 102), :3] = col('D', 2)
    return img

def put_sprite(img, spr, x0, y0, wl, wave, t):
    h, w = spr.shape[:2]
    for yy in range(h):
        Y = y0 + yy
        if not (0 <= Y < H): continue
        for xx in range(w):
            if spr[yy, xx, 3] == 0: continue
            X = x0 + xx
            if not (0 <= X < W): continue
            d = Y - (wl + wave(X))
            if d < 0: img[Y, X] = spr[yy, xx]
            elif d < 1: img[Y, X, :3] = col('w', 7)
            elif d < 3 and BAY[Y % 4, X % 4] < .5 - d * .1: img[Y, X, :3] = (spr[yy, xx, :3] * .45 + np.array(col('w', 3)) * .55).astype(np.uint8)

def dot(img, x, y, s):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H: img[y, x, :3] = col('w', s)

def frame(f):
    t = f / NF; img = sea(t)
    wave = lambda X: math.sin(TAU * (X / 13.0 + t * 2)) * .8
    # ちびキャラ（桟橋に立つ。右向き）
    sp = CH.side(0).a
    ch = np.zeros((H, W, 4), np.uint8); ch[102 - 32 - 1:102 - 32 - 1 + 36, 20:44] = sp
    order = sorted(range(len(ITEMS)), key=lambda j: ITEMS[j][3])
    splashes = []
    for j in order:
        n, wlf, ph, wl = ITEMS[j]; spr = SPR[n]; h, w = spr.shape[:2]
        for ff in range(f - 7, f + 1):                                                    # 波しぶき：上下の底のとき
            p = (ff / NF * 3 + ph) % 1.0
            if abs(p - .75) < .5 / NF * 3 * 1.0 and ff >= 0 or (ff < 0):
                pass
        def xpos(fr_): return (XS[j] - SPEED * fr_) % (W + 56) - 28
        def bob(fr_): return math.sin(TAU * (fr_ / NF * 3 + ph)) * 2.4
        x = xpos(f); b = bob(f)
        # ついて来る波紋と、うしろのあわ（右へのびる）
        for k, (rr, sv) in enumerate(((w * .6 + 3, 6), (w * .45, 5))):
            Y, X = np.mgrid[max(0, wl - 8):min(H, wl + 9), 0:W]
            d = np.hypot((X + .5 - x - w / 2) / rr, (Y + .5 - wl - 1) / (rr * .26))
            mk = (np.abs(d - 1) < 1.1 / rr) & (BAY[(Y + 1) % 4, X % 4] < .55)
            img[Y[mk], X[mk], :3] = col('w', sv)
        for k in range(1, 5):
            dot(img, x + w / 2 + w * .5 + k * 3.5, wl + 1 + (k % 2), 6 if k < 3 else 5); dot(img, x + w / 2 + w * .5 + k * 3.5 + 1, wl + 1 + (k % 2), 5)
        put_sprite(img, spr, int(round(x)), int(round(wl - h * wlf + b)), wl, wave, t)
        # しぶき：ゆれが下がりきったあと数コマ、水がはねる
        for ff in range(max(0, f - 6), f + 1) if False else range(f - 6, f + 1):
            p = (ff / NF * 3 + ph) % 1.0
            if 0 <= (p - .72) % 1.0 < (1.0 / NF * 3) * .999 and (p - .72) % 1.0 >= 0:
                age = f - ff; x0 = xpos(ff) + w * .55; 
                for i in range(7):
                    a = (i - 3) * .42; vx = math.sin(a) * 1.8 - 1.0; vy = 3.0 + (i % 3) * .5
                    px_ = x0 + vx * age * 1.0; py_ = wl - vy * age + .55 * age * age
                    if py_ < wl + 1: dot(img, px_, py_, 7 if age < 3 else 6)
    m = ch[..., 3] > 0; img[m] = ch[m]
    return img

fr = [frame(f) for f in range(NF)]
g = [Image.fromarray(a).convert("RGB").resize((W * 4, H * 4), Image.NEAREST) for a in fr]
g[0].save(os.path.join(OUT, "drift_scene.gif"), save_all=True, append_images=g[1:], duration=90, loop=0)
g[10].save(os.path.join(OUT, "drift_scene_frame0.png")); print("ok")
