"""
島のパーツ（地形・桟橋・小屋・木・小物）。どれも iso.py の面と箱で描く「部品の関数」。
compose_island.py が、島の地図（island_map.json）を見て、これらを順番に呼ぶ。1つずつ単独でも描ける。
"""
import os, sys, math
import numpy as np
sys.argv = [sys.argv[0]]
import iso as I

FI, np_ = I.FI, np
WZ = -0.35                              # 水面の高さ（陸の上面は z=0）
CELL = .5                               # 地形の1マス（m）

def _t(f, s):
    fi = FI[f]
    return lambda x, y, z, u, v, px, py: (np.full(x.shape, fi, np.int8), np.full(x.shape, s, np.int8))

# ---------------------------------------------------------------- 地形
class Terrain:
    def __init__(self, cfg):
        self.x0, self.y0 = cfg["x0"], cfg["y0"]
        self.nx, self.ny = int(cfg["w"] / CELL), int(cfg["h"] / CELL)
        xs = self.x0 + (np.arange(self.nx) + .5) * CELL; ys = self.y0 + (np.arange(self.ny) + .5) * CELL
        X, Y = np.meshgrid(xs, ys, indexing="ij")
        cx, cy, rx, ry = cfg["cx"], cfg["cy"], cfg["rx"], cfg["ry"]
        r = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2
        r = r + (I.vnoise(X * .45, Y * .45, 61) - .5) * .5 + (I.vnoise(X * 1.3, Y * 1.3, 62) - .5) * .18
        land = r < 1.0
        for (bx0, by0, bx1, by1) in cfg.get("extra_land", []):      # 桟橋の根もとなど、陸を足す
            land |= (X > bx0) & (X < bx1) & (Y > by0) & (Y < by1)
        self.land = land
        d = np.where(land, 99, 0)                                   # 水までの距離（マス）
        wat = ~land; dist = np.where(wat, 0, 9)
        for k in range(1, 9):
            ex = np.zeros_like(wat)
            for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                ex |= np.roll(np.roll(wat, sx, 0), sy, 1)
            dist = np.where((dist == 9) & ex, k, dist); wat = wat | ex
        self.dist = dist
        self.paths = cfg.get("paths", []); self.dirt = cfg.get("dirt", [])
        self.sand_w = cfg.get("sand", 2.0)

    def cell(self, x, y):
        ix = np.clip(np.floor((x - self.x0) / CELL).astype(int), 0, self.nx - 1); iy = np.clip(np.floor((y - self.y0) / CELL).astype(int), 0, self.ny - 1)
        return ix, iy

    def is_land(self, x, y):
        ix, iy = self.cell(x, y)
        inb = (x >= self.x0) & (x < self.x0 + self.nx * CELL) & (y >= self.y0) & (y < self.y0 + self.ny * CELL)
        return self.land[ix, iy] & inb

    def top_tex(self):
        T = self
        def f(x, y, z, u, v, px, py):
            n1 = I.vnoise(x * 1.1, y * 1.1, 21) * .6 + I.vnoise(x * .4, y * .4, 26) * .4; n2 = I.vnoise(x * 3.4, y * 3.4, 22); r = I.h2(px >> 1, py >> 1, 23)
            s = np.where(n1 > .6, 3, np.where(n1 > .28, 2, 1)).astype(np.int16) + (n2 > .88) - (n2 < .08)
            fam = np.full(x.shape, FI['E'], np.int8)
            s = s + (r > .96) - (r < .03)
            # 砂浜：水ぎわから2mほど
            ix, iy = T.cell(x, y)
            dm = T.dist[ix, iy] * CELL + (I.vnoise(x * .9, y * .9, 63) - .5) * 1.1
            sand = dm < T.sand_w
            sd = 4 + (n2 > .6) - (n2 < .25) + (r > .93) - (r < .05) - (dm < .35)
            fam = np.where(sand, FI['B'], fam); s = np.where(sand, sd, s)
            # 道・土
            dirt = np.zeros(x.shape, bool)
            for pl in T.paths:
                pl = np.asarray(pl, float)
                for a, b in zip(pl[:-1], pl[1:]):
                    ab = b - a; t = np.clip(((x - a[0]) * ab[0] + (y - a[1]) * ab[1]) / (ab @ ab), 0, 1)
                    d = np.hypot(x - (a[0] + t * ab[0]), y - (a[1] + t * ab[1]))
                    dirt |= d < .5 + (I.vnoise(x * 1.7, y * 1.7, 64) - .5) * .5
            for (cx, cy, rx, ry) in T.dirt:
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                dirt |= d < (1 + (I.vnoise(x * 1.3, y * 1.3, 24) - .5) * .5)
            sdr = 3 + (n2 > .55) - (n2 < .3) + (r > .93) - (r < .06)
            fam = np.where(dirt, FI['N'], fam); s = np.where(dirt, sdr - 1, s)
            peb = dirt & (I.h2(px >> 1, py >> 1, 25) < .03); fam = np.where(peb, FI['I'], fam); s = np.where(peb, 4, s)
            sh = np.zeros(x.shape, bool)
            for hh in I.SHADOWS: sh |= I.inside(hh, x, y)
            s = np.where(sh, s - 2, s)
            return fam, np.clip(s, 0, 7).astype(np.int8)
        return f

    def skirt_tex(self):
        def f(x, y, z, u, v, px, py):
            lip = z > -.14
            r = I.h2(px >> 1, py >> 1, 65); layer = np.floor((-z) * 4.0)
            s = np.where(lip, 3, 2 + (I.h2(layer.astype(int), (x * 2 + y * 2).astype(int), 66) > .7) - (z < -.55))
            s = s + (r > .9) - (r < .1)
            fam = np.where(lip, FI['E'], FI['J'])
            st = (I.h2((x * 3).astype(int), (y * 3).astype(int) + (z * 5).astype(int), 67) > .86) & ~lip
            fam = np.where(st, FI['I'], fam); s = np.where(st, 3, s)
            return fam.astype(np.int8), np.clip(s, 0, 7).astype(np.int8)
        return f

    def draw(self):
        top = self.top_tex(); sk = self.skirt_tex()
        x1, y1 = self.x0 + self.nx * CELL, self.y0 + self.ny * CELL
        I.face((self.x0, self.y0, 0), (x1 - self.x0, 0, 0), (0, y1 - self.y0, 0), top, 0, 0,
               lambda a, b: self.is_land(self.x0 + a * (x1 - self.x0), self.y0 + b * (y1 - self.y0)))
        zb = WZ - .6
        for i in range(self.nx):
            for j in range(self.ny):
                if not self.land[i, j]: continue
                x, y = self.x0 + i * CELL, self.y0 + j * CELL
                if i + 1 >= self.nx or not self.land[i + 1, j]:
                    I.face((x + CELL, y, zb), (0, CELL, 0), (0, 0, -zb), sk, -1, 1)
                if j - 1 < 0 or not self.land[i, j - 1]:
                    I.face((x, y, zb), (CELL, 0, 0), (0, 0, -zb), sk, 0, 1)

# ---------------------------------------------------------------- 材料
_PL = None
def plaster_tex():
    global _PL
    if _PL is None: _PL = I.load_tiles("tile_plaster", 3)
    def t(x, y, z, u, v, px, py):
        f, s = I.tile_lookup(_PL, u, v, 31)
        base = .3 + .25 * I.vnoise(u * 5.0, v * 5.0, 33); moss = z < base
        f = np.where(moss, FI['E'], f); s = np.where(moss, 2 + (I.vnoise(u * 12, v * 12, 34) > .6), s)
        return f.astype(np.int8), np.clip(s, 0, 7).astype(np.int8)
    return t

def boards(fam='D', base=4, w=.22, seed=70):
    fi = FI[fam]
    def t(x, y, z, u, v, px, py):
        k = np.floor(u / w).astype(int); fr = u / w - k
        s = base - 1 + (I.h2(k, seed, 1) * 3).astype(int) - (fr < .1) * 2 - (fr > .9)
        gr = (np.abs(((v * 3 + I.h2(k, 0, 2) * 5) % 1) - .5) < .04) & (I.h2(k, (v * 3).astype(int), 3) > .5)
        s = s - gr
        r = I.h2(px >> 1, py >> 1, 71); s = s + (r > .93) - (r < .06)
        return np.full(x.shape, fi, np.int8), np.clip(s, 0, 7).astype(np.int8)
    return t

def beam_tex(base=3):
    def t(x, y, z, u, v, px, py):
        r = I.h2(px, py, 4); return np.full(x.shape, FI['D'], np.int8), (np.full(x.shape, base) + (r > .8) - (r < .12)).astype(np.int8)
    return t

def shaded_top(tex, zline, by=2):
    """軒の下（上の方）を暗くする"""
    def t(x, y, z, u, v, px, py):
        f, s = tex(x, y, z, u, v, px, py)
        return f, np.where(z > zline, np.maximum(0, s.astype(np.int16) - by), s).astype(np.int8)
    return t

DECK = None
def deck_tex(x, y, z, u, v, px, py):
    k = np.floor(y / .34).astype(int); fr = y / .34 - k
    s = 4 + (I.h2(k, 5, 8) * 3).astype(int) - 1 - (fr < .1) * 2 + (fr > .85)
    gr = (np.abs(((x * 2 + I.h2(k, 0, 9) * 3) % 1) - .5) < .05) & (I.h2(k, (x * 2).astype(int), 10) > .55)
    s = s - gr; r = I.h2(px >> 1, py >> 1, 11); s = s + (r > .94) - (r < .05)
    return np.full(x.shape, FI['D'], np.int8), np.clip(s, 0, 7).astype(np.int8)

# ---------------------------------------------------------------- 小屋
def hut(x0, y0, w, d, wh=2.3, rise=2.4, kind='plaster', door=.35, windows=(.7,), dark_roof=False, name=""):
    """x0,y0=かどの位置、w=横(x)、d=奥行き(y)。正面は手前（-y）、右の壁（+x）に三角の妻。"""
    x1, y1 = x0 + w, y0 + d; ym = (y0 + y1) / 2; hs = d / 2
    pts = [(xx, yy, z) for xx in (x0, x1) for yy in (y0, y1) for z in (0, wh)] + [(x0 - .5, ym, wh + rise), (x1 + .5, ym, wh + rise)]
    I.cast(pts)
    wall = {'plaster': plaster_tex(), 'plank': boards('D', 4), 'darkplank': boards('D', 3, .26, 75)}[kind]
    wall = shaded_top(wall, wh - .45)
    beam = beam_tex(3)
    I.box(x0 - .12, y0 - .12, 0, x1 + .12, y1 + .12, .28, I.stone)
    I.box(x0, y0, .28, x1, y1, wh, {'all': wall})
    # 柱と梁（正面）
    for xx in np.linspace(x0, x1, max(2, int(w // 1.6) + 1)):
        I.box(xx - .09, y0 - .1, .28, xx + .09, y0, wh, beam)
    I.box(x0 - .1, y0 - .1, wh - .16, x1 + .1, y0, wh + .02, beam)
    I.box(x0 - .1, y0 - .1, .28, x1 + .1, y0, .42, beam)
    # 戸口（戸は半分あいて暗い）
    dx = x0 + door * w
    I.box(dx - .55, y0 - .09, .28, dx + .55, y0 - .01, 1.95, beam)
    I.box(dx - .42, y0 - .1, .28, dx + .42, y0 - .02, 1.85, I.dark)
    hg = np.array([dx - .42, y0 - .12, .28]); an = math.radians(-108); dv = np.array([math.cos(an), math.sin(an), 0])
    I.solid(hg, dv * .84, (0, 0, 1.57), np.array([-dv[1], dv[0], 0]) * .07, I.doorwood)
    # 窓（正面）
    for wf in windows:
        xc = x0 + wf * w
        I.box(xc - .42, y0 - .1, 1.1, xc + .42, y0 - .01, 1.82, beam)
        I.box(xc - .33, y0 - .13, 1.18, xc + .33, y0 - .09, 1.74, I.glass)
        for sg in (-1, 1):
            hx = xc + sg * .42; ang = math.radians(-72 if sg < 0 else -108); d_ = np.array([math.cos(ang), math.sin(ang), 0]) * .34
            I.solid((hx, y0 - .1, 1.15), d_, (0, 0, .62), np.array([-d_[1], d_[0], 0]) / .34 * .05, beam)
    # 右の壁：小窓＋柱
    for yy in (y0, y1): I.box(x1 - .02, yy - .09, .28, x1 + .1, yy + .09, wh, beam)
    I.box(x1 - .02, y0, wh - .16, x1 + .1, y1, wh + .02, beam)
    I.box(x1 - .02, ym - .36, 1.2, x1 + .08, ym + .36, 1.84, beam); I.box(x1 + .08, ym - .27, 1.28, x1 + .11, ym + .27, 1.76, I.glass)
    I.face((x1, y0, wh), (0, d, 0), (0, 0, rise * .96), wall, I.shade_off(np.array([1, 0, 0])), 1, lambda a, b: b < 1 - np.abs(a - .5) * 2)
    I.solid((x1 - .02, ym - .09, wh), (.14, 0, 0), (0, .18, 0), (0, 0, rise * .95), beam)
    # 屋根
    OV = hs + .65; EZ = wh; RZ = wh + rise
    dy, dz = OV, RZ - EZ; L = math.hypot(dy, dz); ny_ = np.array([0, -dz, dy]) / L * .3
    o = np.array([x0 - .55, ym - OV, EZ - .1]); up = np.array([0, dy, dz])
    I.solid(o, (w + 1.1, 0, 0), up * 1.02, ny_, {'+C': I.thatch(dark_roof), '+A': beam, '-A': beam, '-B': I.thatch(True), 'all': None}, 2)
    I.solid((x0 - .6, ym - .12, RZ - .05), (w + 1.2, 0, 0), (0, .28, 0), (0, 0, .28), beam, 2)

# ---------------------------------------------------------------- 桟橋
def pier(x, y_from, y_to, width=1.5, z=.22):
    """y_from（岸）から y_to（沖、小さい値）へのびる桟橋。板・杭・横木・あかり"""
    ya, yb = min(y_from, y_to), max(y_from, y_to); xa, xb = x - width / 2, x + width / 2
    post = beam_tex(2)
    ys = list(np.arange(yb - .6, ya, -1.7)) + [ya + .15]
    for yy in ys:
        for xx in (xa + .08, xb - .08):
            I.box(xx - .1, yy - .1, WZ - 1.0, xx + .1, yy + .1, z + .02, post, 2)
        I.box(xa - .02, yy - .07, z - .22, xb + .02, yy + .07, z - .06, post, 2)             # 横木
    for xx in (xa + .1, xb - .1): I.box(xx - .06, ya, z - .26, xx + .06, yb, z - .1, post, 2)  # けた
    I.box(xa, ya, z - .05, xb, yb, z + .02, deck_tex, 2); I.box(xa, ya, z, xb, yb, z + .05, {'+C': deck_tex, 'all': beam_tex(3)}, 2)
    # 手前（沖の端）の係留杭とあかり
    for sg in (-1, 1):
        px = x + sg * (width / 2 - .02)
        I.box(px - .1, ya + .1, z, px + .1, ya + .3, z + .85, post, 2)
    I.box(xa + .05, ya + .1, z + .85, xa + .27, ya + .3, z + 1.07, I.glass, 2)
    I.blob(np.array([xa + .16, ya + .2, z + .96]), 5, 5, 'H', 6, 3)

def boat(x, y, L=2.6, Wd=1.0, z=-.3):
    hull = boards('D', 3, .2, 80)
    I.box(x - Wd / 2, y - L / 2, z - .25, x + Wd / 2, y + L / 2, z + .42, {'all': hull, '+C': None}, 2)
    I.box(x - Wd / 2 + .12, y - L / 2 + .1, z + .1, x + Wd / 2 - .12, y + L / 2 - .1, z + .4, {'all': beam_tex(1), '+C': beam_tex(1)}, 2)
    I.face((x - Wd / 2 + .12, y - L / 2 + .12, z + .405), (Wd - .24, 0, 0), (0, L - .24, 0), _t('D', 2), 0, 2)
    for yy in (-.5, .5): I.box(x - Wd / 2 + .1, y + yy - .08, z + .3, x + Wd / 2 - .1, y + yy + .08, z + .4, beam_tex(4), 2)

# ---------------------------------------------------------------- 木・石（球を1ドットずつ計算）
_PINV = I.P.T @ np.linalg.inv(I.P @ I.P.T)
def ball(c, R, tex_f, oi=3):
    c = np.asarray(c, float); sc = I.P @ c + (I.OX, I.OY)
    x0, x1 = int(sc[0] - R * I.A) - 2, int(sc[0] + R * I.A) + 3; y0, y1 = int(sc[1] - R * I.A * 1.3) - 2, int(sc[1] + R * I.A * 1.3) + 3
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(I.W, x1), min(I.H, y1)
    if x0 >= x1 or y0 >= y1: return
    gx, gy = I.PX[y0:y1, x0:x1] + .5 - sc[0], I.PY[y0:y1, x0:x1] + .5 - sc[1]
    lat = _PINV[:, 0][:, None, None] * gx + _PINV[:, 1][:, None, None] * gy         # 画面の点に対応する世界のずれ（視線と直角）
    r2 = (lat ** 2).sum(0); ins = r2 < R * R
    t = np.sqrt(np.maximum(R * R - r2, 0))
    p = c[:, None, None] + lat - t * I.D[:, None, None]
    key = (p * I.D[:, None, None]).sum(0)
    sub = I.zb[y0:y1, x0:x1]; ok = ins & (key < sub)
    if not ok.any(): return
    n = (p - c[:, None, None]) / R
    lam = (n * I.LIGHT[:, None, None]).sum(0)
    f, s = tex_f(p[0][ok], p[1][ok], p[2][ok], lam[ok], I.PX[y0:y1, x0:x1][ok], I.PY[y0:y1, x0:x1][ok])
    sub[ok] = key[ok]; I.fam[y0:y1, x0:x1][ok] = f; I.shd[y0:y1, x0:x1][ok] = np.clip(s, 0, 7); I.oid[y0:y1, x0:x1][ok] = oi

def leaf(fam='O', base=3):
    fi = FI[fam]
    def f(x, y, z, lam, px, py):
        cl = I.vnoise(x * 2.6 + z * 1.3, y * 2.6 - z * 1.1, 91)
        s = base + np.round((lam - .1) * 3.2) + (cl > .66) - (cl < .3) * 1
        r = I.h2(px >> 1, py >> 1, 92); s = s + (r > .96) - (r < .05)
        return np.full(x.shape, fi, np.int8), np.clip(s, 0, 7).astype(np.int8)
    return f

def rockf(x, y, z, lam, px, py):
    r = I.h2(px >> 1, py >> 1, 93); s = 3 + np.round((lam - .1) * 3) + (r > .9) - (r < .1)
    return np.full(x.shape, FI['I'], np.int8), np.clip(s, 0, 7).astype(np.int8)

def tree(x, y, h=3.4, r=1.25, fam='O'):
    I.cast([(x + dx, y + dy, 0) for dx in (-.9, .9) for dy in (-.9, .9)] + [(x, y, h + r)], k=(.45, .3))
    I.box(x - .16, y - .16, 0, x + .16, y + .16, h - .3, {'all': boards('D', 3, .16, 94)}, 3)
    for (dx, dy, dz, rr, b) in ((0, 0, h + .1, r, 3), (-.6, -.4, h - .35, r * .78, 3), (.55, .45, h - .25, r * .8, 4), (.15, -.3, h + r * .8, r * .62, 4)):
        ball((x + dx, y + dy, dz), rr, leaf(fam, b))

def bush(x, y, r=.6, fam='c'):
    I.cast([(x + dx, y + dy, 0) for dx in (-r, r) for dy in (-r, r)], k=(.3, .2))
    ball((x, y, r * .7), r, leaf(fam, 3)); ball((x + r * .7, y - r * .3, r * .55), r * .7, leaf(fam, 3))

def rock(x, y, r=.5):
    ball((x, y, r * .6), r, rockf)

# ---------------------------------------------------------------- 小物（手描きの絵）
def props_at(items):
    k = max(1, I.S // 2)
    spr = {}
    for kind, x, y, z in items:
        if kind not in spr: spr[kind] = I.load_sprite(kind)
        I.drop((x, y), .9 if kind in ('barrel', 'crate', 'logs') else .5)
    for kind, x, y, z in items:
        I.stamp(spr[kind], np.array([x + .1, y - .1, z]), k)
