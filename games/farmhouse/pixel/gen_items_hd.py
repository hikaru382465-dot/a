"""
釣竿と漂流物を、1つずつ細かく（約2倍）作り込んだ版。python gen_items_hd.py [名前...] → assets/items/hd/<名前>.png と hd_sheet.png
ロープ＝3本よりの縄（うず巻き3周・先をまいた糸）, 石＝割れ面ごとのかげ・地層・こけ・ふじつぼ, 布＝ひだの高さからかげを出す・織り目・ほつれ・ぬい目・穴,
ボトル＝リブ・ラベル・キャップ・水位, ビニール袋＝しわ・赤い印字・持ち手, ヤシの実＝繊維・3つの目・割った断面, 釣竿＝節・コルク・リール・ガイド・うき・はり。
"""
import os, sys, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "items", "hd"); os.makedirs(OUT, exist_ok=True)
pal, _ = pxl.load_palette()
def col(f, s): return tuple(int(v) for v in pal[f][int(max(0, min(7, s)))])
def h2(ix, iy, seed=0):
    ix = np.asarray(ix, np.int64); iy = np.asarray(iy, np.int64)
    h = (ix * 73856093) ^ (iy * 19349663) ^ (seed * 83492791); h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return (h % 10007) / 10007.0
def vn(x, y, seed=0):
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int); fx, fy = x - x0, y - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c_, d = h2(x0, y0, seed), h2(x0 + 1, y0, seed), h2(x0, y0 + 1, seed), h2(x0 + 1, y0 + 1, seed)
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c_ * (1 - fx) * fy + d * fx * fy
BAY = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
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
    def alpha(self): return self.a[..., 3] > 0
    def outline(self, f=('T', 1), diag=False):
        al = np.pad(self.alpha(), 1); e = np.zeros_like(al)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(al, dy, 0), dx, 1)
        e = (e & ~al)[1:-1, 1:-1]
        for y, x in zip(*np.nonzero(e)): self.a[y, x] = (*col(*f), 255)
    def disc(self, x, y, r, f, s):
        m = (self.X + .5 - x) ** 2 + (self.Y + .5 - y) ** 2 <= r * r; self.mask(m, f, s)
    def line(self, p, q, f, s, wd=1):
        n = int(max(abs(q[0] - p[0]), abs(q[1] - p[1])) * 2) + 1
        for k in range(n + 1):
            t = k / n; x = p[0] + (q[0] - p[0]) * t; y = p[1] + (q[1] - p[1]) * t
            for i in range(wd):
                for j in range(wd): self.p(x + i - (wd - 1) / 2, y + j - (wd - 1) / 2, f, s)
def bez(p0, p1, p2, p3, n=80):
    t = np.linspace(0, 1, n)[:, None]; P = [np.array(p, float) for p in (p0, p1, p2, p3)]
    return (1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t ** 2 * P[2] + t ** 3 * P[3]
def contact_shadow(c, cx, cy, rx, ry, k=.55):
    m = (((c.X + .5 - cx) / rx) ** 2 + ((c.Y + .5 - cy) / ry) ** 2 < 1) & (BAY[c.Y % 4, c.X % 4] < k) & ~c.alpha(); c.mask(m, 'T', 1)

# ================================================================ ロープ
def rope():
    c = Cv(52, 38); cx, cy, RX, RY = 22.0, 18.0, 20.0, 11.0
    for dy, dark in ((2.6, True), (0.0, False)):
        u = (c.X + .5 - cx) / RX; v = (c.Y + .5 - cy - dy) / RY; r = np.hypot(u, v); ang = np.arctan2(v, u)
        for k, (rc, hw) in enumerate(((.82, .15), (.52, .14), (.25, .11))):
            w = (r - rc) / hw; m = np.abs(w) < 1
            ph = (ang / (2 * math.pi) * 44 + w * 1.7 + k * .41) % 1
            s = np.where(ph < .30, 6, np.where(ph < .68, 5, 3)).astype(float)
            s = s + np.round(-v * 1.2) - (np.abs(w) > .72) * 1 - (np.abs(w) > .9) * 1
            if dark: s = s - 3
            c.mask(m, 'B', np.clip(s, 1, 7).astype(int))
            gap = (np.abs(np.abs(w) - 1) < .12) & (np.abs(w) >= .9); 
    # 先っぽ（外がわの輪からのびて、くるんと曲がる）
    path = bez((33, 26), (40, 31), (48, 27), (47, 18), 120)
    for i, (x, y) in enumerate(path):
        t = i / (len(path) - 1)
        ph = (t * 34) % 1
        for rr, dark in ((2.0, True), (1.8, False)):
            yy = y + (1.8 if dark else 0)
            m = (c.X + .5 - x) ** 2 + (c.Y + .5 - yy) ** 2 <= rr * rr
            c.mask(m, 'B', 3 if dark else (6 if ph < .3 else 5 if ph < .65 else 4))
    ex, ey = path[-1]
    for k in range(4): c.p(ex + (k % 2) * .6 - .3, ey - 2 - k * .5, 'B', 6 if k % 2 == 0 else 4)            # ほつれ
    for dx, dy in ((-1, -2), (1, -2), (0, -3), (2, -1), (-2, -1)): c.p(ex + dx, ey + dy, 'B', 6 if (dx + dy) % 2 else 4)
    for yy in range(int(path[-9][1]), int(path[-5][1]) + 1): c.disc(path[-8][0], path[-8][1], 2.0, 'C', 5); c.disc(path[-7][0], path[-7][1], 2.0, 'C', 4)   # 巻いた糸（止め）
    c.outline(('D', 1)); return c

# ================================================================ 石
def stone(kind):
    if kind == 'round':
        c = Cv(38, 30); cx, cy, rx, ry = 19.0, 15.5, 16.5, 12.5
        u = (c.X + .5 - cx) / rx; v = (c.Y + .5 - cy) / ry; ang = np.arctan2(v, u)
        edge = 1 + .09 * np.sin(2 * ang + .6) + .05 * np.sin(5 * ang + 1.2); r = np.hypot(u, v) / edge; m = r < 1
        z = np.sqrt(np.clip(1 - r * r, 0, 1)); lam = (np.stack([u, v, z], -1) * LIGHT).sum(-1)
        s = 3 + np.round((lam - .4) * 3.6)
        n = vn(c.X * .33, c.Y * .33, 41); s = s + (n > .62) - (n < .3)
        sp = h2(c.X, c.Y, 42); s = s + (sp > .94) - (sp < .06)
        c.mask(m, 'I', np.clip(s, 1, 7).astype(int))
        band = m & (np.abs((c.X * .5 - c.Y * 1.0) - (-9 + 3 * vn(c.X * .15, 0, 43))) < 1.2); c.mask(band, 'I', np.clip(s + 2, 1, 7).astype(int))     # 白いすじ
        sh = m & (np.hypot((c.X - 12) / 3.6, (c.Y - 9) / 2.4) < 1) & (lam > .55); c.mask(sh, 'I', 7)                                            # 水のつや
        moss = m & (lam > .3) & (v < -.15) & (vn(c.X * .22, c.Y * .3, 44) > .52 + (v + .8) * .6); c.mask(moss, 'E', np.clip(2 + np.round(lam * 2), 1, 5).astype(int))
        for (bx, by) in ((26, 21), (28, 19), (25, 23), (13, 24)): c.disc(bx, by, 1.1, 'L', 6); c.p(bx, by, 'L', 3)                              # ふじつぼ
        c.outline(('T', 1)); return c
    c = Cv(44, 30); cx, cy = 22.0, 16.0
    u = (c.X + .5 - cx) / 20.0; v = (c.Y + .5 - cy) / 12.0; ang = np.arctan2(v, u)
    edge = 1 + .17 * np.sin(3 * ang + 2.0) + .09 * np.sin(5 * ang + .4) + .05 * np.sin(9 * ang); r = np.hypot(u, v) / edge; m = r < 1
    # 割れ面（ボロノイ）：面ごとに向きがちがう
    seeds = [(14, 9), (26, 8), (34, 14), (10, 17), (21, 17), (30, 21), (17, 24), (38, 19)]
    d = np.stack([np.hypot(c.X - sx, (c.Y - sy) * 1.3) for sx, sy in seeds], 0); fid = d.argmin(0)
    tilt = np.array([(h2(i, 1, 9) - .5, h2(i, 2, 9) - .5) for i in range(len(seeds))])
    nx, ny = tilt[fid, 0] * 1.4 + u * .5, tilt[fid, 1] * 1.2 + v * .5
    lam = (np.stack([nx, ny, np.sqrt(np.clip(1 - nx * nx - ny * ny, .1, 1))], -1) * LIGHT).sum(-1)
    s = 3 + np.round((lam - .45) * 4.0)
    d2 = np.sort(d, 0); edge_l = (d2[1] - d2[0]) < .9; s = np.where(edge_l, s - 1, s)
    n = vn(c.X * .5, c.Y * .5, 51); s = s + (n > .66) - (n < .28)
    c.mask(m, 'I', np.clip(s, 1, 7).astype(int))
    for k, y0 in enumerate((12, 18, 23)):                                                               # 地層
        c.mask(m & (np.abs(c.Y - (y0 + (c.X - 22) * .13 * (1 if k % 2 else -1))) < .6) & (h2(c.X >> 1, k, 52) > .25), 'I', np.clip(s - 2, 1, 7).astype(int))
    moss = m & (v < -.1) & (vn(c.X * .25, c.Y * .35, 53) > .5 + (v + .8) * .55) & (lam > .25); c.mask(moss, 'E', np.clip(2 + np.round(lam * 2.2) + (h2(c.X, c.Y, 54) > .8), 1, 6).astype(int))
    c.mask(m & (np.abs(c.X - (30 + (c.Y - 12) * .4)) < .6) & (c.Y > 11) & (c.Y < 23), 'I', 1)           # ひび
    for (bx, by) in ((9, 22), (11, 24), (33, 24), (36, 21)): c.disc(bx, by, 1.2, 'L', 5); c.p(bx, by, 'L', 2)
    c.outline(('T', 1)); return c

# ================================================================ 布（波うつ1枚の布：青い縞・ぬい目・やぶれた右はし）
def cloth():
    c = Cv(56, 34); X = c.X + .5; Y = c.Y + .5
    xs = np.arange(c.w) + .5
    top = 8 + 2.6 * np.sin(xs * .20 + .6) + 1.2 * np.sin(xs * .47 + 1.5)                 # 上のふちの波
    bot = top + 16 + 2.0 * np.sin(xs * .16 + 2.2)                                         # 下のふち
    # 右はしをやぶく：ななめにのこぎり状
    tear = 49 + 3.0 * np.sin(Y * .9) + (h2((Y * 1).astype(int), 5, 6) - .5) * 4.5 + (Y - 16) * .22
    T = top[None, :].repeat(c.h, 0); B = bot[None, :].repeat(c.h, 0)
    m = (Y > T) & (Y < B) & (X > 3) & (X < tear)
    v = (Y - T) / (B - T)                                                                # 0（上）〜1（下）
    slope = np.gradient(top)[None, :].repeat(c.h, 0) * .5 + np.gradient(bot)[None, :].repeat(c.h, 0) * .5
    fold = np.cos(X * .20 + .6) * .9 + np.cos(X * .47 + 1.5) * .35
    lam = -slope * 1.1 + fold * .35 - (v - .5) * .5
    s = 4 + np.round(lam * 2.2)
    stripe = ((v > .22) & (v < .36)) | ((v > .60) & (v < .74))                           # 長さ方向の青い縞
    c.mask(m, 'C', np.clip(s, 2, 6).astype(int))
    c.mask(m & stripe, 'F', np.clip(s - 1, 2, 5).astype(int))
    c.mask(m & stripe & (((c.X // 2 + (v * 20).astype(int)) % 2) == 0) & (np.abs(v - .29) < .02), 'F', 2)
    wv = m & (((c.X + c.Y) % 4) == 0) & (h2(c.X, c.Y, 61) > .5); c.mask(wv, 'C', np.clip(s - 1, 2, 6).astype(int))               # 織り目（まばら）
    stitch = m & (np.abs(v - .91) < .04) & (c.X % 3 != 0); c.mask(stitch, 'D', 3)                                               # ぬい目（下のはし）
    stitch2 = m & (np.abs(v - .07) < .04) & (c.X % 3 != 0); c.mask(stitch2, 'D', 3)
    hole = np.hypot((X - 20) / 2.8, (Y - 17) / 2.2) < 1; c.a[hole & m] = 0                                                       # 小さな穴
    rim = (np.hypot((X - 20) / 3.8, (Y - 17) / 3.2) < 1) & ~hole & m; c.mask(rim, 'C', np.clip(s - 2, 2, 4).astype(int))
    for k in range(9):                                                                  # やぶれ口から出る糸
        yy = 11 + k * 1.9; xx = tear[int(min(c.h - 1, yy))] if False else 49 + (k % 3) - 1
        for i in range(3 + k % 3): c.p(xx + i + (1 if k % 2 else 0), yy + (i // 2) * (1 if k % 2 else -1), 'C', 5 if i == 0 else 4)
    c.outline(('D', 1)); return c

# ================================================================ ビニール袋（スーパーの袋：持ち手2つ・赤い印字・底のまち）
def bag():
    c = Cv(48, 40); X = c.X + .5; Y = c.Y + .5
    xs = np.arange(c.w) + .5
    topE = 16 + 1.6 * np.sin(xs * .35 + .4)                                              # 口のふち（波）
    botE = 35 + 1.4 * np.sin(xs * .30 + 1.7)
    L = 6 + (Y - 24) * .06 + 1.2 * np.sin(Y * .5); R = 41 - (Y - 24) * .05 + 1.2 * np.sin(Y * .45 + 1)
    m = (Y > topE[None, :].repeat(c.h, 0)) & (Y < botE[None, :].repeat(c.h, 0)) & (X > L) & (X < R)
    u = (X - 6) / 35.0; v = (Y - 16) / 19.0
    fold = np.sin(u * 17.0 + .4) * .8 + np.sin(u * 7.0 + v * 3 + 1) * .9 + np.cos(v * 9 - u * 3) * .35
    gx = np.gradient(fold, axis=1)
    s = 5 + np.round(-gx * 7.0) + np.round((.5 - v) * .8)                                  # 大きなしわのかげ
    c.mask(m, 's', np.clip(s, 3, 7).astype(int))
    thin = m & (np.sin(u * 17.0 + .4) > .72); c.mask(thin, 'S', 5)                         # うすい所は青白く
    c.mask(m & (v > .86), 's', np.clip(s - 2, 2, 5).astype(int))                             # 底のかげ
    c.mask(m & (np.abs(v - .93) < .03), 's', 3)                                              # 底のまちの線
    c.mask(m & (np.abs(u - .5) < .02) & (v > .2) & (v < .86) & (np.arange(c.h)[:, None] % 4 != 0), 's', 4)   # 中央の折り目
    # 赤い印字（帯と文字ブロック）
    band = m & (v > .40) & (v < .66) & (u > .12) & (u < .88)
    c.mask(band, 'G', np.clip(4 - np.round(gx * 5), 3, 5).astype(int))
    txt = band & (((np.floor(X) + 1) % 4) < 2) & (np.abs(v - .53) < .07) & (h2(np.floor(X / 2).astype(int), 9, 3) > .25); c.mask(txt, 's', 7)
    # 持ち手（左右の輪）と、そこから口へのつけ根
    for sx in (-1, 1):
        cx_ = 24 + sx * 8.5
        pts = bez((cx_ - sx * 4.2, 16.5), (cx_ - sx * 4, 3), (cx_ + sx * 4, 3), (cx_ + sx * 4.2, 16.5), 60)
        for (x, y) in pts: c.disc(x, y, 1.1, 's', 7 if sx < 0 else 5); c.p(x + 1, y + 1, 'S', 3)
    c.mask(m & (v < .12), 's', np.clip(s + 1, 4, 7).astype(int))
    c.outline(('S', 2)); return c

# ================================================================ ペットボトル
def bottle():
    c = Cv(64, 26); cy = 12.5
    def body_h(x):   # よこ向きの太さ（半分）
        if x < 2: return 0
        if x < 42: return 9.0 - (1.2 if x < 5 else 0) - .8 * (x > 38)
        if x < 50: return 9.0 - (x - 42) * .8
        return 2.6
    Y = c.Y + .5 - cy
    for x in range(1, 59):
        hh = body_h(x)
        if x < 4: hh = [0, 4.6, 7.0, 8.2][x]
        for y in range(c.h):
            dy = Y[y, 0]
            if abs(dy) > hh: continue
            t = dy / max(hh, 1)
            if x >= 54: f, s = 'u', 5 - round(t * 2) - 1                                             # 赤いキャップ
            elif x >= 50: f, s = 'S', 5 - round(t * 2)                                               # 首
            else:
                f = 'S'; s = 5 - round(t * 2.6) + (1 if t < -.55 else 0)
                if 6 <= x <= 40 and abs(dy) > hh - 1.3: s += 1 if dy < 0 else -1
            c.p(x, y, f, s)
    # 水（下から 45%）と水面・泡
    for x in range(3, 42):
        hh = body_h(x)
        for y in range(c.h):
            dy = Y[y, 0]
            if abs(dy) > hh - .8: continue
            if dy > -hh * .1:
                c.p(x, y, 'w', 4 if dy < hh * .45 else 3)
                if dy < -hh * .1 + 1.2: c.p(x, y, 'w', 6)                                              # 水面のきわ
    for (bx, by) in ((12, 15), (20, 16), (28, 14), (33, 16)): c.p(bx, by, 'w', 7)                      # 泡
    # リブ（くびれ）
    for x in (8, 16, 24, 32, 40):
        hh = body_h(x)
        for y in range(c.h):
            if abs(Y[y, 0]) <= hh - .5 and h2(x, y, 3) > -1: c.a[y, x, :3] = [int(v * .86) for v in c.a[y, x, :3]] if c.a[y, x, 3] else c.a[y, x, :3]
    # ラベル（青い帯＋白い印字）
    for x in range(13, 31):
        hh = body_h(x)
        for y in range(c.h):
            dy = Y[y, 0]
            if abs(dy) <= hh - 1.4:
                f, s = 'F', 4 - round(dy / hh * 1.6)
                if abs(dy) < hh * .45 and (x * 7 + 3) % 5 not in (0,) and (x % 2 == 0 or h2(x, 1, 7) > .5): f, s = 's', 7                   # 白い文字ぽい模様
                c.p(x, y, f, s)
    for x in (13, 30):
        for y in range(c.h):
            if abs(Y[y, 0]) <= body_h(x) - 1.4: c.p(x, y, 'F', 2)
    # キャップのみぞ・首のリング
    for x in (55, 57): 
        for y in range(c.h):
            if c.a[y, x, 3] and abs(Y[y, 0]) < 2.6: c.p(x, y, 'u', 2)
    for y in range(c.h):
        if c.a[y, 50, 3] and abs(Y[y, 0]) < 4: c.p(50, y, 'S', 7)
    # つや（上のすじ）と、下のかげ
    for x in range(6, 40): c.p(x, cy - body_h(x) + 2, 'S', 7) if x % 6 != 5 else None
    c.outline(('S', 1)); return c

# ================================================================ ヤシの実
def coconut(cut=False):
    c = Cv(36, 34); cx, cy = 18.0, 19.0
    u = (c.X + .5 - cx) / 15.0; v = (c.Y + .5 - cy) / 13.5; ang = np.arctan2(v, u)
    r = np.hypot(u, v) / (1 + .05 * np.sin(3 * ang + .8)); m = r < 1
    z = np.sqrt(np.clip(1 - r * r, 0, 1)); lam = (np.stack([u, v, z], -1) * LIGHT).sum(-1)
    s = 3 + np.round((lam - .35) * 3.4)
    # 繊維：上の頂点から下へ流れるすじ
    fiber = np.sin((np.arctan2(u, -v) * 7.0 + (r * 5) ) * 1.0) > .35
    fib2 = (h2((c.X * .8).astype(int), (c.Y * .5).astype(int), 81) > .62)
    s = s - (fiber & (r > .35)) * 1 + (fib2 & (lam > .3)) * 1
    # 3本の縦の稜（ぬい目）
    for a0 in (-2.1, .0, 2.1):
        rid = m & (np.abs(np.arctan2(u, -v) - a0) < .045 + .04 * r) & (r > .2); s = np.where(rid, s - 1, s)
    c.mask(m, 'D', np.clip(s, 1, 7).astype(int))
    if not cut:
        for (ex, ey, rr) in ((12.3, 9.2, 1.9), (17.6, 8.2, 1.9), (14.6, 13.0, 1.9)):                    # 3つの目
            c.disc(ex, ey, rr, 'D', 0); c.disc(ex - .3, ey - .3, rr * .6, 'D', 1); c.p(ex - 1, ey - 1, 'D', 4)
        c.mask(m & (np.hypot((c.X - 11.5) / 3.2, (c.Y - 14) / 2.1) < 1) & (lam > .55), 'D', 6)           # つや
        c.outline(('D', 0)); return c
    # わった：うえ半分を切って、断面（楕円）を見せる
    cut_y = 12.0
    m2 = m & (c.Y > cut_y + (c.X - cx) * .0); c.a[:] = 0
    c.mask(m2, 'D', np.clip(s, 1, 7).astype(int))
    rimU = (c.X + .5 - cx) / 14.2; rimV = (c.Y + .5 - cut_y - 2.5) / 5.6
    rr_ = np.hypot(rimU, rimV)
    c.mask(rr_ < 1.0, 'D', 2)                                   # 殻の外がわ（繊維の厚み）
    c.mask(rr_ < .86, 'D', 1)                                   # かたい殻（こげ茶）
    c.mask(rr_ < .74, 's', 7)                                   # 白い果肉
    c.mask(rr_ < .74, 's', np.clip(6 + np.round(-rimV * 1.0), 5, 7).astype(int))
    c.mask(rr_ < .55, 'w', 5); c.mask((rr_ < .55) & (rimV > .05), 'w', 4)
    c.mask((rr_ < .55) & (rimV < -.2) & (rimU < .2), 'w', 6); c.p(cx - 3, cut_y + 1.6, 's', 7); c.p(cx - 2, cut_y + 1.2, 's', 7)
    c.mask((rr_ < .74) & (rr_ > .62) & (h2(c.X, c.Y, 83) > .5), 's', 5)
    c.outline(('D', 0)); return c

# ================================================================ 釣竿
def rod():
    c = Cv(72, 72)
    x0, y0, x1, y1 = 6.0, 64.0, 62.0, 6.0                       # 持ち手のおしり → 竿先
    n = 200
    P = lambda t: (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t - math.sin(t * math.pi) * 0)
    # 竿（先ほど細く、節ごとに色がちがう）
    for k in range(n + 1):
        t = k / n; x, y = P(t); wd = 3.6 - 2.4 * t if t > .27 else 5.0
        if t < .08: f, s = 'T', 3                                                     # おしりのゴム
        elif t < .27: f, s = ('B', 5) if (int(t * 120) % 5) else ('B', 3)             # コルクのグリップ（リング）
        else: f, s = 'D', 4
        seg = int((t - .27) / .12) if t > .27 else 0
        node = t > .27 and abs(((t - .27) % .12) - .0) < .006
        for dy in np.arange(-wd / 2, wd / 2 + .01, .5):
            yy = y + dy; xx = x - dy * .3
            top = dy < -wd * .15
            ss = s + (1 if top else 0) - (1 if dy > wd * .25 else 0) - (2 if node else 0) + (1 if (f == 'D' and seg % 2) else 0)
            c.p(xx, yy, f, ss)
    # リールシート（金属の輪）とリール
    for t in (.27, .285):
        x, y = P(t)
        for dy in range(-3, 4): c.p(x, y + dy, 'I', 5 - abs(dy) // 2)
    rx_, ry_ = 22.0, 52.0
    c.disc(rx_, ry_ + 3, 6.0, 'I', 3); c.disc(rx_, ry_ + 3, 4.6, 'I', 5)                             # スプール（糸巻き）
    c.disc(rx_, ry_ + 3, 3.2, 'C', 6); c.disc(rx_ - .6, ry_ + 2.4, 1.6, 'C', 7)                      # 糸
    for k in range(10): c.p(rx_ + math.cos(k * .63) * 4.3, ry_ + 3 + math.sin(k * .63) * 4.3, 'I', 6 if k % 3 else 3)
    
    for yy in range(int(ry_) + 6, int(ry_) + 12):
        for xx in range(int(rx_ - 3), int(rx_ + 4)): c.p(xx, yy, "I", 4 - (yy - int(ry_) - 6) // 3)     # ボディ
    c.line((rx_ + 4, ry_ + 8), (rx_ + 10, ry_ + 15), 'I', 3, 2); c.disc(rx_ + 11, ry_ + 17, 2.0, 'D', 4); c.p(rx_ + 10, ry_ + 16, 'D', 6)   # ハンドルと握り
    c.line((rx_ - 4, ry_ + 5), (rx_ - 9, ry_ + 9), 'I', 6, 1)                                         # ベイル（糸まわし）
    # ガイド（輪）：根もとほど大きい
    gpos = [.34, .44, .55, .66, .77, .88, 1.0]
    gx = []
    for i, t in enumerate(gpos):
        x, y = P(t); rr = 2.6 - i * .28
        for a in np.linspace(0, 2 * math.pi, 18, endpoint=False): c.p(x + math.cos(a) * rr - 1, y - 2.6 + math.sin(a) * rr - .4, 'I', 6 if a < math.pi else 3)
        c.p(x, y - 1, 'I', 4); gx.append((x - 1, y - 2.6 - 0))
    # つり糸：リール → ガイドをとおって → 竿先 → たれる
    pts = [(rx_ + 1, ry_ + 3)] + [(gx[i][0], gx[i][1] - 1.6) for i in range(len(gx))]
    for a, b in zip(pts[:-1], pts[1:]): c.line(a, b, 'C', 7, 1)
    tip = pts[-1]
    drop = bez(tip, (tip[0] + 5, tip[1] + 12), (tip[0] + 9, tip[1] + 22), (tip[0] + 8, tip[1] + 34), 90)
    for (x, y) in drop: c.p(x, y, 'C', 7)
    fx, fy = drop[-1][0], drop[-1][1]
    # うき（赤白）・おもり・はり・えさ
    for yy in range(-6, 7):
        wdt = 3.4 * math.sqrt(max(0, 1 - (yy / 6.8) ** 2))
        for xx in np.arange(-wdt, wdt + .1, .5):
            top = yy < 0
            f, s = ('G', 5 - int(abs(xx) > wdt - .8) * 2) if top else ('s', 6 - int(xx > wdt * .3) * 2)
            if top and xx < -wdt * .35 and yy < -2: s = 6
            c.p(fx + xx, fy + 2 + yy, f, s)
    for k in range(5): c.p(fx, fy + 2 - 7 - k, 'T', 3)                                               # 先のアンテナ
    c.p(fx, fy - 12, 'G', 5)
    for k in range(10): c.p(fx, fy + 9 + k, 'C', 6)
    c.disc(fx, fy + 12, 1.4, 'I', 4); c.p(fx - 1, fy + 11, 'I', 7)                                    # 小さなおもり
    hx, hy = fx, fy + 19
    for (dx, dy) in ((0, 0), (0, 1), (0, 2), (0, 3), (1, 4), (2, 4), (3, 3), (3, 2), (2, 2)): c.p(hx + dx, hy + dy, 'I', 7 if dx == 0 else 5)   # はり
    c.p(hx + 2, hy + 1, 'I', 6)
    for k in range(5): c.p(hx - 1 + (k % 2), hy + 4 + k, 'G', 4 if k % 2 else 5)                      # えさ（ミミズ）
    c.outline(('T', 1)); return c

ITEMS = {"rope": rope, "stone_round": lambda: stone('round'), "stone_rock": lambda: stone('rock'), "cloth": cloth, "bottle": bottle,
         "bag": bag, "coconut": lambda: coconut(False), "coconut_cut": lambda: coconut(True), "rod": rod}
want = [a for a in sys.argv[1:]] or list(ITEMS)
BG = (24, 54, 78, 255); K = 8
sheet_items = []
for n in want:
    c = ITEMS[n](); Image.fromarray(c.a).save(os.path.join(OUT, n + ".png"))
    im = Image.new("RGBA", c.a.shape[1::-1], BG); im.alpha_composite(Image.fromarray(c.a))
    im.resize((im.width * K, im.height * K), Image.NEAREST).convert("RGB").save(os.path.join(OUT, n + "_x8.png")); sheet_items.append((n, c))
cw = max(c.w for _, c in sheet_items) + 8; ch = max(c.h for _, c in sheet_items) + 8; cols = 3; rows = (len(sheet_items) + cols - 1) // cols
sh = Image.new("RGBA", (cw * cols, ch * rows), BG)
for i, (n, c) in enumerate(sheet_items): sh.alpha_composite(Image.fromarray(c.a), ((i % cols) * cw + (cw - c.w) // 2, (i // cols) * ch + (ch - c.h) // 2))
sh.resize((sh.width * 5, sh.height * 5), Image.NEAREST).convert("RGB").save(os.path.join(OUT, "hd_sheet.png")); print("ok", [n for n, _ in sheet_items])
