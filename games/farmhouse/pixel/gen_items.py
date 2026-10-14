"""
釣竿と、海から流れてくる漂流物（ロープ・石・布・プラスチック・ヤシの実）。パレットの色だけ、1ドットずつ計算。
python gen_items.py → assets/items/<名前>.png（アイコン）, items_sheet.png（一覧）, items_float.gif（海にうかんで流れる）, items_preview.png
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "items"); os.makedirs(OUT, exist_ok=True)
pal, _ = pxl.load_palette()
BAY = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
def col(f, s): return tuple(int(v) for v in pal[f][int(max(0, min(7, s)))])
def h2(ix, iy, seed=0):
    ix = np.asarray(ix, np.int64); iy = np.asarray(iy, np.int64)
    h = (ix * 73856093) ^ (iy * 19349663) ^ (seed * 83492791); h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return (h % 10007) / 10007.0
LIGHT = np.array([-.5, -.6, .62]); LIGHT /= np.linalg.norm(LIGHT)

class Cv:
    def __init__(self, w, h): self.w, self.h = w, h; self.a = np.zeros((h, w, 4), np.uint8); self.Y, self.X = np.mgrid[0:h, 0:w]
    def p(self, x, y, f, s):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h: self.a[y, x] = (*col(f, s), 255)
    def mask(self, m, f, s):
        s = np.broadcast_to(np.asarray(s), m.shape)
        for v in np.unique(s[m]):
            mm = m & (s == v); self.a[mm, :3] = col(f, int(v)); self.a[mm, 3] = 255
    def outline(self, s=1, f=None):
        al = self.a[..., 3] > 0; e = np.zeros_like(al)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(al, dy, 0), dx, 1)
        o = e & ~al
        for y, x in zip(*np.nonzero(o)):
            self.a[y, x] = (*col(*(f or ('T', 1))), 255)

def sphere_shade(u, v, r):
    z = np.sqrt(np.clip(1 - r * r, 0, 1)); n = np.stack([u, v, z], -1)
    return (n * LIGHT).sum(-1)

# ---------------------------------------------------------------- ロープ（まいたもの）
def rope():
    c = Cv(22, 16); cx, cy = 10.5, 8.0
    for ring_dy, dark in ((1.5, True), (0, False)):
        u = (c.X + .5 - cx) / 9.5; v = (c.Y + .5 - cy - ring_dy) / 6.0; r = np.hypot(u, v); ang = np.arctan2(v, u)
        for (r0, r1) in ((.66, 1.0), (.3, .58)):
            m = (r >= r0) & (r <= r1)
            tw = ((ang / (2 * math.pi) * 24 + r * 5) % 1.0) < .5
            s = np.where(tw, 5, 4) - np.round(v * 1.3) - (r > r1 - .08) * 1 + (r < r0 + .08) * 0
            if dark: s = s - 2
            c.mask(m, 'B', np.clip(s, 1, 7).astype(int))
    for (x, y, s) in ((16, 12, 4), (17, 13, 3), (18, 13, 4), (19, 14, 3), (20, 14, 2)):          # 先っぽ
        c.p(x, y, 'B', s); c.p(x, y + 1, 'B', 2)
    c.p(20, 15, 'B', 5); c.p(21, 14, 'B', 5)
    c.outline(1, ('D', 1)); return c

# ---------------------------------------------------------------- 石（2つ）
def stone(variant=0):
    w, h = (16, 14) if variant == 0 else (19, 13)
    c = Cv(w, h); cx, cy = w / 2, h / 2 + (.3 if variant == 0 else .5); rx, ry = (6.8, 6.2) if variant == 0 else (8.4, 5.6)
    u = (c.X + .5 - cx) / rx; v = (c.Y + .5 - cy) / ry; ang = np.arctan2(v, u)
    bump = 1 + (.14 if variant == 0 else .22) * np.sin(3 * ang + 1.0 + variant * 2) + .08 * np.sin(5 * ang + 2)
    r = np.hypot(u, v) / bump; m = r < 1
    lam = sphere_shade(u, v, np.clip(r, 0, .99)) if variant == 0 else (-u * .5 - v * .8 + .3)
    s = 3 + np.round((lam - .35) * 3.4) + (h2(c.X >> 0, c.Y >> 0, 21 + variant) > .9) - (h2(c.X, c.Y, 22 + variant) < .08)
    c.mask(m, 'I', np.clip(s, 1, 6).astype(int))
    if variant == 0:
        crack = m & (np.abs((c.X - c.Y * .6) - 5.2) < .6) & (c.Y > 5)
        c.mask(crack, 'I', 1)
    else:
        for x0 in (4, 9, 14): c.mask(m & (np.abs(c.Y - (3.5 + (c.X - x0) * .18)) < .5) & (np.abs(c.X - x0) < 3), 'I', 2)   # 地層
    moss = m & (lam > .5) & (h2(c.X >> 1, c.Y >> 1, 25 + variant) > .55) & (c.Y < cy - ry * .2)
    c.mask(moss, 'E', 3 + (h2(c.X, c.Y, 26) > .6).astype(int))
    c.outline(1, ('T', 1)); return c

# ---------------------------------------------------------------- 布（やぶれた切れはし）
def cloth():
    c = Cv(24, 16); cx, cy = 11.5, 8.0
    u = (c.X + .5 - cx) / 10.5; v = (c.Y + .5 - cy) / 6.4; ang = np.arctan2(v, u)
    edge = 1 + .12 * np.sin(3 * ang + 1) + .08 * np.sin(5 * ang + 0.5) + (h2(np.floor(ang * 9).astype(int), 3, 4) - .5) * .16 * (u > .1)
    r = np.hypot(u, v) / edge; m = r < 1
    lam = -u * .4 - v * .7
    fold = np.sin((c.X * .75 + c.Y * .55) * .9) * .5 + np.sin((c.X * .3 - c.Y * .9) * .8) * .35
    s = 4 + np.round(lam * 1.3 + fold * 1.4)
    stripe = ((c.X + c.Y * 1.2) % 8) < 2.3
    c.mask(m, 'C', np.clip(s, 2, 6).astype(int))
    c.mask(m & stripe, 'F', np.clip(s - 1, 2, 5).astype(int))
    hole = m & (np.hypot((c.X - 8) / 1.7, (c.Y - 9) / 1.4) < 1)
    c.a[hole] = 0
    fray = m & (u > .62) & ((c.Y % 2) == 0) & (h2(c.X, c.Y, 8) > .4); c.mask(fray, 'C', 2)
    c.outline(1, ('D', 1)); return c

# ---------------------------------------------------------------- プラスチック（ペットボトルとビニール袋）
def bottle():
    c = Cv(22, 10)
    for x in range(1, 20):
        t = x
        if x <= 12: y0, y1 = 2, 7                       # 本体
        elif x <= 15: y0, y1 = 3, 6                     # 首
        else: y0, y1 = 3, 6                             # キャップ
        if x in (1, 12): y0 += 1; y1 -= 1
        for y in range(y0, y1 + 1):
            if x >= 17: c.p(x, y, 'G', 5 if y < 5 else 3)                      # 赤いキャップ
            elif x >= 15: c.p(x, y, 'S', 5 if y < 5 else 4)
            else:
                inwater = y >= 5 and x < 9
                base = 5 if y <= y0 else 4 if y < y1 else 3
                if y == y0 + 1 and 3 <= x <= 10: base = 7                      # つやのすじ
                c.p(x, y, 'w' if inwater and y > 4 else 'S', (5 if inwater and y == 5 else 4) if inwater else base)
    for x in range(4, 9): 
        for y in (3, 4, 5, 6): c.p(x, y, 'C', 6 if y < 5 else 4) if x in (5, 6, 7) and False else None
    for y in range(3, 7): c.p(10, y, 'S', 3)                                    # ふくらみのすじ
    for x in (4, 5, 6): c.p(x, 2, 'S', 7)
    c.outline(1, ('S', 1)); return c

def bag():
    c = Cv(18, 16); cx, cy = 9, 8
    u = (c.X + .5 - cx) / 7.5; v = (c.Y + .5 - cy) / 6.8; ang = np.arctan2(v, u)
    edge = 1 + .22 * np.sin(4 * ang + .5) + .1 * np.sin(7 * ang)
    r = np.hypot(u, v) / edge; m = r < 1
    cr = np.sin(c.X * .9 + c.Y * .5) * .5 + np.sin(c.X * .4 - c.Y * 1.2) * .5
    s = 5 + np.round(-u * .8 - v * .7 + cr * 1.2)
    c.mask(m, 's', np.clip(s, 2, 7).astype(int))
    hnd = m & (c.Y < 4) & (np.abs(c.X - 9) > 3) & (np.abs(c.X - 9) < 6)
    c.mask(hnd & ((c.X + c.Y) % 3 == 0), 's', 3)
    c.outline(1, ('S', 2)); return c

# ---------------------------------------------------------------- ヤシの実（まるごと／わった）
def coconut(cut=False):
    c = Cv(16, 15); cx, cy = 7.8, 7.4
    u = (c.X + .5 - cx) / 6.6; v = (c.Y + .5 - cy) / 6.4; ang = np.arctan2(v, u)
    r = np.hypot(u, v) / (1 + .08 * np.sin(3 * ang + 1)); m = r < 1
    lam = sphere_shade(u, v, np.clip(r, 0, .99))
    s = 3 + np.round((lam - .35) * 3.2)
    fib = (np.sin((c.X * .5 + c.Y * 1.3) * 1.7) > .55) & m
    c.mask(m, 'D', np.clip(s - fib * 1, 1, 6).astype(int))
    if not cut:
        for (ex, ey) in ((6, 3), (9, 3), (7.5, 5)): c.p(ex, ey, 'D', 1); c.p(ex + (0 if ey == 5 else 0), ey + 1, 'D', 1) if False else None
        for (ex, ey) in ((5, 3), (8, 3), (6.5, 5.5)): c.p(ex, ey, 'D', 0); c.p(ex + 1, ey, 'D', 1)
        c.mask(m & (h2(c.X, c.Y, 33) > .93), 'D', 6)
    else:
        cut_m = m & (c.Y < 8.2 + (c.X - 8) * .0) & (c.Y > 3.2) & (np.abs(u) < .86)
        inner = cut_m & (np.hypot((c.X - 7.8) / 5.2, (c.Y - 5.8) / 2.6) < 1)
        c.mask(cut_m & ~inner, 'D', 2)
        c.mask(inner, 's', np.where(c.Y[inner.nonzero()] if False else 0, 0, 0) if False else 6)
        c.mask(inner & (np.hypot((c.X - 7.8) / 3.2, (c.Y - 6.2) / 1.2) < 1), 'w', 5)          # 中の水
        c.mask(inner & (c.Y < 5.2) & (c.X < 9), 's', 7)
    c.outline(1, ('D', 0)); return c

# ---------------------------------------------------------------- 釣竿（32×32）
def rod():
    c = Cv(32, 32)
    x0, y0, x1, y1 = 3.0, 28.0, 27.0, 3.0
    n = 60
    for k in range(n + 1):
        t = k / n; x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t - math.sin(t * math.pi) * 1.5 * 0 
        thick = 2 if t < .22 else 1
        s = 4 if t > .22 else 3
        for dy in range(thick):
            c.p(x, y + dy, 'D', s + (1 if dy == 0 else -1) + (1 if (k // 6) % 2 == 0 and t > .22 else 0))
        if t < .2: c.p(x, y + 1, 'T', 3)                               # グリップ（黒）
        if t > .22 and k % 9 == 0: c.p(x, y - 1, 'I', 5)               # ガイド（わっか）
    # リール
    for (dx, dy, s) in ((0, 0, 5), (1, 0, 5), (2, 0, 4), (0, 1, 5), (1, 1, 6), (2, 1, 4), (0, 2, 3), (1, 2, 3), (2, 2, 3)):
        c.p(9 + dx, 22 + dy, 'I', s)
    c.p(8, 23, 'I', 4); c.p(8, 22, 'I', 3)                              # ハンドル
    c.p(7, 24, 'b', 5)
    # つり糸 → うき → はり
    lx, ly = 27, 3
    for k in range(0, 15):
        t = k / 14; x = lx + 1.2 * math.sin(t * 2.2) + t * 1.5; y = ly + k * 1.0
        c.p(x, y, 'C', 6)
    fx, fy = 29, 18
    for (dx, dy, f, s) in ((0, 0, 'G', 5), (1, 0, 'G', 5), (-1, 0, 'G', 4), (0, 1, 'G', 4), (1, 1, 'G', 3), (-1, 1, 'G', 3), (0, 2, 's', 6), (1, 2, 's', 5), (0, -1, 's', 7), (1, -1, 's', 6)):
        c.p(fx + dx, fy + dy, f, s)
    for k in range(4): c.p(fx, fy + 3 + k, 'C', 5)
    for (dx, dy) in ((0, 7), (1, 8), (1, 9), (0, 9), (-1, 8)): c.p(fx + dx, fy + dy, 'I', 6)
    c.outline(1, ('T', 1)); return c

ITEMS = {"rod": rod(), "rope": rope(), "stone1": stone(0), "stone2": stone(1), "cloth": cloth(), "bottle": bottle(), "bag": bag(),
         "coconut": coconut(False), "coconut_cut": coconut(True)}
for n, c in ITEMS.items(): Image.fromarray(c.a).save(os.path.join(OUT, n + ".png"))
BG = (24, 54, 78, 255)
def bgimg(w, h): im = Image.new("RGBA", (w, h), BG); return im
# 一覧
cell = 40; cols = 5; rows = 2
sheet = Image.new("RGBA", (cell * cols, cell * rows), BG)
for i, (n, c) in enumerate(ITEMS.items()):
    im = Image.fromarray(c.a); sheet.alpha_composite(im, ((i % cols) * cell + (cell - im.width) // 2, (i // cols) * cell + (cell - im.height) // 2))
sheet.convert("RGB").save(os.path.join(OUT, "items_sheet_small.png"))
sheet.resize((sheet.width * 8, sheet.height * 8), Image.NEAREST).convert("RGB").save(os.path.join(OUT, "items_sheet.png"))

# ---------------------------------------------------------------- 海にうかんで流れる（漂流物のみ）
FLOAT = ["rope", "stone1", "cloth", "bottle", "bag", "coconut", "coconut_cut"]
NF = 8; WW, HH = 200, 44
def water(t):
    cv = Cv(WW, HH)
    h = np.sin(2 * math.pi * (cv.X / 31.0 + cv.Y / 11.0 - t)) * .5 + np.sin(2 * math.pi * (cv.X / 17.0 - cv.Y / 7.0 + t * 2)) * .35
    idx = np.clip(np.floor((h + 1) / 2 * 2.4 + (BAY[cv.Y % 4, cv.X % 4] - .5) * .6).astype(int) + 2, 2, 4)
    cv.mask(np.ones((HH, WW), bool), 'w', idx); return cv
def frame(i):
    t = i / NF; cv = water(t)
    for j, n in enumerate(FLOAT):
        spr = ITEMS[n].a; h, w = spr.shape[:2]
        cx = 14 + j * 28 + int(round(math.sin(math.tau * (t + j * .13)) * 2)); base = 24 + int(round(math.sin(math.tau * (t * 2 + j * .31)) * 1.0))
        # 波紋と影
        for (rad, sv, k) in ((w * .95, 5, .5), (w * .68, 4, .7)):
            d = np.hypot((cv.X + .5 - cx) / rad, (cv.Y + .5 - (base + 1)) / (rad * .42)); mk = (np.abs(d - 1) < 1.4 / rad) & (BAY[(cv.Y + 1) % 4, cv.X % 4] < k)
            cv.mask(mk, 'w', sv)
        # 水にしずむ下がわ：下の2行は水の色とまじる（網点）
        y0 = base - h + 3
        sub = spr.copy(); 
        for yy in range(h - 3, h):
            for xx in range(w):
                if sub[yy, xx, 3] and BAY[(y0 + yy) % 4, (cx + xx) % 4] < (.35 + .3 * (yy - (h - 3))): sub[yy, xx] = 0
        for yy in range(h):
            for xx in range(w):
                if sub[yy, xx, 3]:
                    X, Y = cx - w // 2 + xx, y0 + yy
                    if 0 <= X < WW and 0 <= Y < HH: cv.a[Y, X] = sub[yy, xx]
    return cv.a
fr = [Image.fromarray(frame(i)).resize((WW * 5, HH * 5), Image.NEAREST).convert("RGB") for i in range(NF)]
fr[0].save(os.path.join(OUT, "items_float.gif"), save_all=True, append_images=fr[1:], duration=160, loop=0)
fr[0].save(os.path.join(OUT, "items_preview.png"))
print("ok")
