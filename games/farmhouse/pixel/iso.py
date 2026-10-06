"""
家を「ドット絵として」直接描く小さな描画道具（2:1の斜め上の視点）。
3Dを縮めるのではなく、面ごとに1ドットずつ模様（パレットのコード）を決めて塗る。
色は pixel/palette.json の系統×明るさだけを使うので、農夫とそろう。

python iso.py  →  ../assets/farmhouse_iso.png（480×270）, farmhouse_iso_x4.png
"""
import os, sys, math
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pxl
PAL, _ = pxl.load_palette()
FAM = list(PAL.keys()); FI = {f: i for i, f in enumerate(FAM)}
TABLE = np.array([PAL[f] for f in FAM], np.uint8)              # (系統, 明るさ, rgb)
S = 4                                                           # 細かさ（4で見本と同じくらい）
W, H = 480 * S, 270 * S
A = 15.0 * S                                                    # 1m = 横にAドット
HZ = A * math.sqrt(1.5)                                         # 高さ1mの縦のドット数（仰角30度）
OX, OY = 233.0 * S, 138.0 * S
P = np.array([[A, A, 0.0], [A / 2, -A / 2, -HZ]])
D = np.array([-math.cos(math.radians(30)) / math.sqrt(2), math.cos(math.radians(30)) / math.sqrt(2), -.5])  # カメラの向き
LIGHT = np.array([-.35, -.75, .55]); LIGHT /= np.linalg.norm(LIGHT)
rng = np.random.default_rng(11)

fam = np.full((H, W), -1, np.int8); shd = np.zeros((H, W), np.int8)
zb = np.full((H, W), np.inf); oid = np.zeros((H, W), np.int8)   # oid 0=地面
PX, PY = np.meshgrid(np.arange(W), np.arange(H))

def h2(ix, iy, seed=0):
    ix = np.asarray(ix, np.int64); iy = np.asarray(iy, np.int64)
    h = (ix * 73856093) ^ (iy * 19349663) ^ (seed * 83492791)
    h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return (h % 10007) / 10007.0

def vnoise(x, y, seed=0):
    x0, y0 = np.floor(x), np.floor(y); fx, fy = x - x0, y - y0
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    a, b = h2(x0, y0, seed), h2(x0 + 1, y0, seed); c, d = h2(x0, y0 + 1, seed), h2(x0 + 1, y0 + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def sc(px, py): return A * (px) , 0
def proj(p):
    p = np.asarray(p, float); s = P @ p
    return s[0] + OX, s[1] + OY

# ---------------------------------------------------------------- 面を塗る
def face(o, U, V, tex, off=0, oi=1, mask=None):
    o, U, V = map(lambda v: np.asarray(v, float), (o, U, V))
    PU, PV = P @ U, P @ V
    M = np.array([PU, PV]).T
    det = np.linalg.det(M)
    if abs(det) < 1e-6: return
    s0 = P @ o + (OX, OY)
    cs = np.array([s0, s0 + PU, s0 + PV, s0 + PU + PV])
    x0, x1 = max(0, int(cs[:, 0].min()) - 1), min(W, int(cs[:, 0].max()) + 2)
    y0, y1 = max(0, int(cs[:, 1].min()) - 1), min(H, int(cs[:, 1].max()) + 2)
    if x0 >= x1 or y0 >= y1: return
    gx, gy = PX[y0:y1, x0:x1] + .5 - s0[0], PY[y0:y1, x0:x1] + .5 - s0[1]
    Mi = np.linalg.inv(M)
    a = Mi[0, 0] * gx + Mi[0, 1] * gy; b = Mi[1, 0] * gx + Mi[1, 1] * gy
    e = .02
    ins = (a >= -e) & (a < 1 + e) & (b >= -e) & (b < 1 + e)
    if mask is not None: ins &= mask(a, b)
    wx = o[0] + a * U[0] + b * V[0]; wy = o[1] + a * U[1] + b * V[1]; wz = o[2] + a * U[2] + b * V[2]
    key = wx * D[0] + wy * D[1] + wz * D[2]
    sub = zb[y0:y1, x0:x1]
    ok = ins & (key < sub)
    if not ok.any(): return
    lu, lv = np.linalg.norm(U), np.linalg.norm(V)
    f, s = tex(wx[ok], wy[ok], wz[ok], (a * lu)[ok], (b * lv)[ok], PX[y0:y1, x0:x1][ok], PY[y0:y1, x0:x1][ok])
    s = np.clip(s + off, 0, 7)
    sub[ok] = key[ok]
    fam[y0:y1, x0:x1][ok] = f; shd[y0:y1, x0:x1][ok] = s; oid[y0:y1, x0:x1][ok] = oi

def shade_off(n):
    lam = float(np.dot(n, LIGHT)); return int(round(np.clip((lam - .7) * 2.5, -1.5, 1.5)))

def solid(o, A_, B_, C_, mats, oi=1):
    """平行六面体。mats: 全面共通のテクスチャ関数、または {'+A':f,'-B':f,...}"""
    o, A_, B_, C_ = map(lambda v: np.asarray(v, float), (o, A_, B_, C_))
    ctr = o + (A_ + B_ + C_) / 2
    sides = {'A': (B_, C_, A_), 'B': (C_, A_, B_), 'C': (A_, B_, C_)}
    for ax, (X, Y, Z) in sides.items():
        for sign in (-1, 1):
            org = o + (Z if sign > 0 else 0)
            fc = org + (X + Y) / 2
            n = np.cross(X, Y); n /= np.linalg.norm(n)
            if np.dot(n, fc - ctr) < 0: n = -n
            if np.dot(n, D) >= 0: continue
            name = ('+' if sign > 0 else '-') + ax
            t = mats[name] if isinstance(mats, dict) and name in mats else (mats.get('all') if isinstance(mats, dict) else mats)
            if t is None: continue
            face(org, X, Y, t, shade_off(n), oi)

def box(x0, y0, z0, x1, y1, z1, mats, oi=1):
    solid((x0, y0, z0), (x1 - x0, 0, 0), (0, y1 - y0, 0), (0, 0, z1 - z0), mats, oi)

# ---------------------------------------------------------------- テクスチャ（1ドットずつ決める）
def T(f, base, spk=None):
    fi = FI[f]
    def t(x, y, z, u, v, px, py):
        r = h2(px, py, 3); s = np.full(x.shape, base, np.int8)
        if spk: s = s + (r < spk).astype(np.int8) * -1 + (r > 1 - spk).astype(np.int8)
        return np.full(x.shape, fi, np.int8), s
    return t


# ---- 手描きの模様タイル（tiles.py）を読んで、面に並べる
def load_tiles(prefix, n):
    arrs = []
    for i in range(n):
        code = pxl.build(os.path.join(HERE, "sprites", f"{prefix}{i}.pxl"))[0]
        f = np.vectorize(lambda t: FI[t[0]])(code).astype(np.int8); s_ = np.vectorize(lambda t: int(t[1]))(code).astype(np.int8)
        arrs.append((f, s_))
    return arrs
ART = A / max(1, S // 2) / 1.0                                    # 1mあたりの絵のドット数（1ドット=S//2 のドット）

def tile_lookup(tiles, u, v, seed):
    th, tw = tiles[0][0].shape
    ix = np.floor(u * ART).astype(np.int64); iy = np.floor(v * ART).astype(np.int64)
    cx, cy = ix // tw, iy // th
    var = (h2(cx, cy, seed) * len(tiles)).astype(np.int64) % len(tiles)
    flip = h2(cx, cy, seed + 7) > .5
    lx = np.where(flip, tw - 1 - (ix % tw), ix % tw); ly = iy % th
    F = np.stack([t[0] for t in tiles]); Sh = np.stack([t[1] for t in tiles])
    return F[var, ly, lx], Sh[var, ly, lx].astype(np.int16)

PLASTER_T = THATCH_T = None

def plaster_old(x, y, z, u, v, px, py):
    s = np.full(x.shape, 4, np.int8); r = h2(px >> 1, py >> 1, 1)
    s = s + (r > .94).astype(np.int8) - (r < .07).astype(np.int8)
    bl = vnoise(u * 1.3, v * 1.3, 5); s = s - (bl > .72).astype(np.int8)
    f = np.full(x.shape, FI['L'], np.int8)
    gr = (z < .75) & (h2(px >> 1, py >> 1, 2) < (1 - z / .75) * .7)           # 足もとの苔と泥
    f = np.where(gr, FI['E'], f); s = np.where(gr, 2 + (h2(px >> 1, py >> 1, 6) > .6), s)
    return f, s.astype(np.int8)

def plaster(x, y, z, u, v, px, py):
    global PLASTER_T
    if PLASTER_T is None: PLASTER_T = load_tiles("tile_plaster", 3)
    f, s = tile_lookup(PLASTER_T, u, v, 31)
    # 足もとの苔：ぼかした模様の形で（点ではなく、かたまりで）
    base = .32 + .28 * vnoise(u * 5.0, v * 5.0, 33)
    moss = z < base
    f = np.where(moss, FI['E'], f); s = np.where(moss, 2 + (z < base - .12) * 0 + (vnoise(u * 12, v * 12, 34) > .6), s)
    return f.astype(np.int8), np.clip(s, 0, 7).astype(np.int8)

def beam(x, y, z, u, v, px, py):
    r = h2(px, py, 4); s = np.full(x.shape, 3, np.int8) + (r > .8) - (r < .12)
    return np.full(x.shape, FI['D'], np.int8), s.astype(np.int8)

def doorwood(x, y, z, u, v, px, py):
    s = np.full(x.shape, 4, np.int8); r = h2(px >> 1, py >> 1, 8)
    seam = (np.abs(((u / .3) % 1) - 0) < .06) | (((u / .3) % 1) > .94)
    s = np.where(seam, 2, s + (r > .85) - (r < .15))
    return np.full(x.shape, FI['D'], np.int8), s.astype(np.int8)

def thatch(dark=False):
    def t(x, y, z, u, v, px, py):
        global THATCH_T
        if THATCH_T is None: THATCH_T = load_tiles("tile_thatch", 3)
        f, s = tile_lookup(THATCH_T, u, v, 41)
        h = .62; k = np.floor(v / h); fr = v - k * h
        tooth = (np.abs(((u / .55) % 1) - .5) * 2 * .30 + (vnoise(u * 3.2, k, 31) - .5) * .22)
        band = (k % 2 == 1) & (fr > tooth + .02) & (fr < tooth + .30 + (vnoise(u * 2.1, k + 9, 32) - .5) * .12)
        s = np.where(band, s - 2, s)
        s = np.where(fr < .04, s - 2, s)                                   # 段のさかい目の線
        if dark: s = s - 2
        return f.astype(np.int8), np.clip(s, 0, 7).astype(np.int8)
    return t

def stone(x, y, z, u, v, px, py):
    bh, bw = .27, .42; row = np.floor(v / bh); uo = u + (row % 2) * bw / 2
    col = np.floor(uo / bw)
    mortar = (((v / bh) % 1) < .12) | (((uo / bw) % 1) < .08)
    base = 1 + (h2(col, row, 12) * 3).astype(np.int16)
    s = np.where(mortar, 1, base); r = h2(px >> 1, py >> 1, 13); s = s + (r > .9) - (r < .1)
    f = np.full(x.shape, FI['I'], np.int8)
    mo = (h2(col, row, 14) > .62) & (~mortar); f = np.where(mo, FI['E'], f); s = np.where(mo, 3, s)
    return f, np.clip(s, 0, 7).astype(np.int8)

def dark(x, y, z, u, v, px, py):
    s = np.where(h2(px >> 1, py >> 1, 15) < .1, 1, 0); shelf = ((z * 3) % 1) < .06
    f = np.where(shelf & (z > .5), FI['D'], FI['K']); s = np.where(shelf & (z > .5), 1, s)
    return f.astype(np.int8), s.astype(np.int8)

def glass(x, y, z, u, v, px, py):
    cu, cv = np.abs(u - np.max(u) / 2 if u.size else u), 0
    bar = (np.abs(u - u.max() / 2) < .04) | (np.abs(v - v.max() / 2) < .04) if u.size else u > 9
    s = np.where(bar, 1, 5 + (h2(px, py, 16) > .7)); f = np.where(bar, FI['D'], FI['H'])
    return f.astype(np.int8), s.astype(np.int8)

def soil(x, y, z, u, v, px, py):
    r = h2(px >> 1, py >> 1, 17); s = 2 + (r > .8) - (r < .1) + ((np.floor(u * 4) % 2 == 0) * 0)
    return np.full(x.shape, FI['J'], np.int8), s.astype(np.int8)

def plank(x, y, z, u, v, px, py):
    r = h2(px >> 1, py >> 1, 18); return np.full(x.shape, FI['D'], np.int8), (4 + (r > .8) - (r < .15)).astype(np.int8)

# --- 地面（草・土・影）
DIRT = [(-2.0, -3.6, 1.9, 1.3), (1.4, -3.6, 1.5, 1.2), (-4.5, -1.0, 1.3, 1.0), (-6.5, -4.3, 1.5, 1.2),
        (6.5, -5.2, 1.7, 1.3), (-0.2, -2.7, 3.0, .8)]
SHADOWS = []   # [(凸包の頂点(x,y)の配列)]
def hull(pts):
    pts = sorted(set(map(tuple, pts)))
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])
def cast(points3, k=(.5, .33)):
    SHADOWS.append(hull([(x + z * k[0], y + z * k[1]) for x, y, z in points3] + [(x, y) for x, y, z in points3]))
def inside(h, x, y):
    ok = np.ones(x.shape, bool)
    for i in range(len(h)):
        a, b = h[i], h[(i + 1) % len(h)]
        ok &= ((b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])) >= 0
    return ok

def ground(x, y, z, u, v, px, py):
    n1 = vnoise(x * 1.1, y * 1.1, 21) * .6 + vnoise(x * .4, y * .4, 26) * .4; n2 = vnoise(x * 3.4, y * 3.4, 22); r = h2(px >> 1, py >> 1, 23)
    s = np.where(n1 > .6, 3, np.where(n1 > .28, 2, 1)).astype(np.int16) + (n2 > .88) - (n2 < .08)
    f = np.full(x.shape, FI['E'], np.int8)
    dirt = np.zeros(x.shape, bool)
    for (cx, cy, rx, ry) in DIRT:
        d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        dirt |= d < (1 + (vnoise(x * 1.3, y * 1.3, 24) - .5) * .5)
    f = np.where(dirt, FI['N'], f); sd = 3 + (n2 > .55) - (n2 < .3) + (r > .93) - (r < .06)
    s = np.where(dirt, sd - 1, s + (r > .96) - (r < .03))
    peb = dirt & (h2(px >> 1, py >> 1, 25) < .03); f = np.where(peb, FI['I'], f); s = np.where(peb, 4, s)
    # 家の足もとの影と、まわりの暗がり
    sh = np.zeros(x.shape, bool)
    for hh in SHADOWS: sh |= inside(hh, x, y)
    s = np.where(sh, s - 2, s)
    ao = (x > -4.9) & (x < 4.9) & (y > -2.3) & (y < 4.3) & ~((x > -4) & (x < 4) & (y > -1.5) & (y < 3.5))
    s = np.where(ao & ~sh, s - 1, s)
    return f, np.clip(s, 0, 7).astype(np.int8)

# ---------------------------------------------------------------- 単色モード（python iso.py --flat）：見本のようにベタ塗り＋影と形だけ
FLAT = "--flat" in sys.argv
def flat(f, sh):
    fi = FI[f]
    return lambda x, y, z, u, v, px, py: (np.full(x.shape, fi, np.int8), np.full(x.shape, sh, np.int8))
if FLAT:
    plaster = flat('D', 6)                               # 見本の壁 #bb885a に近い
    beam = flat('R', 2)                                  # 見本の梁 #3d1f28 に近いえんじ
    def thatch(dark=False):
        def t(x, y, z, u, v, px, py):
            h = .62; k = np.floor(v / h); fr = v - k * h
            tooth = (np.abs(((u / .55) % 1) - .5) * 2 * .30 + (vnoise(u * 3.2, k, 31) - .5) * .22)
            band = (k % 2 == 1) & (fr > tooth + .02) & (fr < tooth + .30 + (vnoise(u * 2.1, k + 9, 32) - .5) * .12)
            s = np.where(band, 3, 4) - (2 if dark else 0)
            return np.full(x.shape, FI['D'], np.int8), s.astype(np.int8)
        return t

# ---------------------------------------------------------------- 物を置く
def build():
    cast([(x, y, z) for x in (-4.2, 4.2) for y in (-1.6, 3.6) for z in (0, 3)] + [(-4.8, 1, 7.2), (4.8, 1, 7.2), (-4.2, -2.1, 2.9), (4.2, -2.1, 2.9)])
    cast([(-5.4 + dx, -3.4 + dy, z) for dx in (-.9, .9) for dy in (-.7, .7) for z in (0, 2.2)])
    face((-20, -20, 0), (40, 0, 0), (0, 40, 0), ground, 0, 0)
    # 土台と壁
    box(-4.15, -1.65, 0, 4.15, 3.65, .3, stone)
    box(-4, -1.5, .3, 4, 3.5, 3, {'all': plaster})
    # 戸口（真っ黒）と戸の枠
    box(-3.7, -1.52, .3, -1.5, -1.5, 2.4, dark)
    # 正面の梁
    for xx in (-4, -3.7, -1.5, .5, 2.5, 3.8):
        box(xx - .1, -1.62, .3, xx + .1, -1.5, 3, beam)
    box(-4.1, -1.62, 2.82, 4.1, -1.5, 3.02, beam); box(-4.1, -1.62, 1.22, 4.1, -1.5, 1.38, beam)
    box(-4.1, -1.62, .3, 4.1, -1.5, .46, beam); box(-3.8, -1.62, 2.3, -1.4, -1.5, 2.5, beam)
    for sx_ in (-1, 1):
        pass
    # 窓
    for xc in (-.5, 1.5, 3.1):
        box(xc - .48, -1.6, 1.5, xc + .48, -1.5, 2.34, beam)
        box(xc - .38, -1.64, 1.6, xc + .38, -1.6, 2.24, glass)
        # 開いた鎧戸
        for sg in (-1, 1):
            hx = xc + sg * .45; ang = math.radians(-70 if sg < 0 else -110)
            d_ = np.array([math.cos(ang), math.sin(ang), 0]) * .42
            solid((hx, -1.62, 1.55), d_, (0, 0, .75), np.array([-d_[1], d_[0], 0]) / .42 * .05, beam)
    for xc in (-.5, 1.5):
        box(xc + .1, -1.62, .6, xc + .6, -1.5, 1.05, beam); box(xc + .16, -1.64, .66, xc + .54, -1.6, .99, glass)
    # 開いた納屋の戸
    hg = np.array([-3.7, -1.65, .3]); an = math.radians(-105); dv = np.array([math.cos(an), math.sin(an), 0])
    solid(hg, dv * 2.1, (0, 0, 2.2), np.array([-dv[1], dv[0], 0]) * .09, doorwood)
    # 右の壁（妻）：窓と柱、三角壁
    for yy in (-1.5, 3.5): box(3.9, yy - .1, .3, 4.1, yy + .1, 3, beam)
    box(3.95, -1.6, 1.22, 4.1, 3.6, 1.38, beam); box(3.95, -1.6, 2.82, 4.1, 3.6, 3.02, beam)
    for yc, zc in ((1.2, 1.9), (1.0, 4.6)):
        box(4.0, yc - .5, zc - .45, 4.12, yc + .5, zc + .45, beam)
        box(4.12, yc - .4, zc - .35, 4.16, yc + .4, zc + .35, glass)
    for sg in (-1, 1):
        box(4.12, 1.2 + sg * .75 - .22, 1.5, 4.18, 1.2 + sg * .75 + .22, 2.3, doorwood)
    def tri(a, b): return (b <= 1 - a)                                       # 三角のおおい（a=y方向, b=高さ方向）
    face((4.0, -1.5, 3.0), (0, 5, 0), (0, 0, 4.1), plaster, shade_off(np.array([1, 0, 0])), 1,
         lambda a, b: b < 1 - np.abs(a - .5) * 2 * 1.0)
    for sg in (-1, 1):
        solid((4.0, 1 - .1, 3), (.14, 0, 0), (0, .2, 0), (0, 0, 4.0), beam)    # 大黒柱
    # 屋根
    EZ, RZ, RY, OV = 2.9, 7.2, 1.0, 3.15
    dy, dz = OV, RZ - EZ; L = math.hypot(dy, dz); ny = np.array([0, -dz, dy]) / L * .32
    o = np.array([-4.6, RY - OV, EZ - .1]); up = np.array([0, dy, dz])
    solid(o, (9.2, 0, 0), up * 1.02, ny, {'+C': thatch(), '+A': beam, '-A': beam, '-B': thatch(True), 'all': None}, 2)
    solid((-4.8, RY - .12, RZ - .05), (9.6, 0, 0), (0, .28, 0), (0, 0, .3), beam, 2)
    solid((-4.8, RY - .3, RZ - .1), (9.6, 0, 0), (0, .2, 0), (0, 0, .25), beam, 2)
    # 井戸
    wx, wy = -5.4, -3.4
    for k in range(10):
        a_ = k * math.radians(36); cx, cy = wx + .75 * math.cos(a_), wy + .75 * math.sin(a_)
        box(cx - .25, cy - .22, 0, cx + .25, cy + .22, .8, stone)
    for sg in (-1, 1): box(wx + sg * .9 - .08, wy - .08, 0, wx + sg * .9 + .08, wy + .08, 2.0, beam)
    box(wx - 1.0, wy - .06, 1.74, wx + 1.0, wy + .06, 1.86, beam)
    for sg in (-1, 1):
        solid((wx - 1.0, wy + (0 if sg > 0 else 0), 2.0), (2.0, 0, 0), (0, sg * .65, .38 * -1 * 0 + .2), (0, 0, .06), doorwood) if False else None
    box(wx - 1.05, wy - .62, 2.0, wx + 1.05, wy + .62, 2.1, doorwood)
    # 畑・柵
    box(5.0, -3.2, 0, 9.4, 1.2, .14, soil)
    for x in np.arange(5.0, 9.41, .8):
        for y in (-3.2, 1.2): box(x - .05, y - .05, 0, x + .05, y + .05, .9, plank)
    for y in np.arange(-3.2, 1.21, .8): box(9.35, y - .05, 0, 9.45, y + .05, .9, plank)
    for z in (.35, .7):
        box(5, -3.25, z, 9.4, -3.15, z + .07, plank); box(5, 1.15, z, 9.4, 1.25, z + .07, plank); box(9.35, -3.2, z, 9.45, 1.2, z + .07, plank)
    # 切り株・丸太
    box(7.8, -4.8, 0, 8.3, -4.3, .42, plank)

# 部品（絵）を置く：anchor=足もとの世界の点
def stamp(code, p, k=None):
    k = k or max(1, round(A * .044))
    h, w = code.shape; sx, sy = proj(p); key = float(np.dot(p, D)) - .02
    x0, y0 = int(round(sx)) - w * k // 2, int(round(sy)) - h * k + 1
    for yy in range(h):
        for xx in range(w):
            t = code[yy, xx]
            if t == "..": continue
            X, Y = x0 + xx * k, y0 + yy * k
            ys, xs = slice(max(0, Y), min(H, Y + k)), slice(max(0, X), min(W, X + k))
            sub = zb[ys, xs]
            if sub.size == 0: continue
            ok = key < sub + .6
            fam[ys, xs][ok] = FI[t[0]]; shd[ys, xs][ok] = int(t[1]); zb[ys, xs][ok] = key; oid[ys, xs][ok] = 3

def blob(p, rx, ry, f, s, oi=3):
    sx, sy = proj(p); key = float(np.dot(p, D)) - .02
    rx, ry = rx * S, ry * S
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            d = (dx / (rx + .5)) ** 2 + (dy / (ry + .5)) ** 2
            if d > 1: continue
            X, Y = int(round(sx)) + dx, int(round(sy)) + dy - ry
            if not (0 <= X < W and 0 <= Y < H) or key >= zb[Y, X] + .6: continue
            lit = -dx / (rx + .5) - dy / (ry + .5)
            ss = s + (1 if lit > .6 else 0) - (1 if lit < -.7 else 0) - (1 if d > .72 else 0)
            fam[Y, X] = FI[f]; shd[Y, X] = max(0, min(7, ss)); zb[Y, X] = key; oid[Y, X] = oi

def dots(p, f, s, pts):
    sx, sy = proj(p); key = float(np.dot(p, D)) - .03
    b = S // 2
    for dx, dy in pts:
        X, Y = int(round(sx)) + dx * b, int(round(sy)) + dy * b
        ys, xs = slice(max(0, Y), min(H, Y + b)), slice(max(0, X), min(W, X + b))
        if zb[ys, xs].size == 0: continue
        ok = key < zb[ys, xs] + .6
        fam[ys, xs][ok] = FI[f]; shd[ys, xs][ok] = s; zb[ys, xs][ok] = key; oid[ys, xs][ok] = 3

def load_sprite(name): return pxl.build(os.path.join(HERE, "sprites", name + ".pxl"))[0]

def shade_ellipse(p, rx, ry, d=2):
    sx, sy = proj(p); X0, Y0 = int(sx), int(sy)
    for yy in range(Y0 - ry, Y0 + ry + 1):
        for xx in range(X0 - rx, X0 + rx + 1):
            if 0 <= xx < W and 0 <= yy < H and ((xx - X0) / rx) ** 2 + ((yy - Y0) / ry) ** 2 <= 1 and oid[yy, xx] in (0, 1):
                shd[yy, xx] = max(0, shd[yy, xx] - d)

def props():
    k = max(1, S // 2)
    barrel, bucket, crate, logs = (load_sprite(n) for n in ("barrel", "bucket", "crate", "logs"))
    for (x, y) in ((3.2, -3.1), (3.9, -3.5)): stamp(barrel, np.array([x + .1, y - .1, 0.]), k)
    for (x, y) in ((2.5, -3.7), (4.5, -2.8)): stamp(bucket, np.array([x + .1, y - .1, 0.]), k)
    for (cx, cy, cz) in ((-1.0, -2.4, 0), (-.35, -2.55, 0), (-.7, -2.45, .5)): stamp(crate, np.array([cx + .28, cy - .28, cz]), k)
    stamp(logs, np.array([9.0, -3.9, 0.]), k)
    for (x, y) in ((2.5, -3.05), (2.15, -3.4)): blob(np.array([x, y, 0.]), 4, 3, 'C', 4)   # 麻袋
    # トマト（株ごとの小物の絵を置く）
    plants = [load_sprite(f"tomato{i}") for i in (1, 2, 3)]
    for i in range(8):
        px_ = 5.6 + (i % 4) * 1.0 + rng.uniform(-.1, .1); py_ = -2.5 + (i // 4) * 1.5 + rng.uniform(-.15, .15)
        shade_ellipse(np.array([px_ + .1, py_, 0.]), int(.55 * A), int(.28 * A)); stamp(plants[i % 3], np.array([px_, py_, 0.]), k)
    # 背の高い花（小物の絵）
    fl = [load_sprite("flower1"), load_sprite("flower2")]
    for i, (fx, fy) in enumerate(((4.7, -2.2), (5.0, -1.0), (4.65, .3), (4.9, 1.1), (5.6, .7), (4.4, -.4), (9.1, -2.6), (9.2, .6))):
        stamp(fl[i % 2], np.array([fx, fy, 0.]), k)
    # つる（家の壁）
    for (x, top) in ((-3.85, 2.8), (-1.4, 2.2), (-1.7, 1.2), (.6, 2.6), (2.6, 1.8), (3.9, 2.9)):
        u = 0.; z = .3
        while z < top:
            u = max(-.12, min(.12, u + rng.uniform(-.05, .05)))
            dots(np.array([x + u, -1.66, z]), 'E', 3, [(0, 0)])
            if rng.random() < .8: blob(np.array([x + u + rng.uniform(-.1, .1), -1.68, z]), 1, 1, 'E', 4)
            z += .09
    # 屋根の苔
    # 草のたば
    ys, xs = np.nonzero((oid == 0) & (fam == FI['E']) & (shd >= 3))
    b = S // 2
    for i in rng.choice(len(ys), size=min(900 * S * S // 2, len(ys)), replace=False):
        X, Y = xs[i], ys[i]
        pat = ((0, 0, 4), (0, -1, 5), (-1, -1, 3), (1, -1, 3), (0, -2, 5)) if rng.random() < .7 else ((0, 0, 3), (1, -1, 5), (2, -2, 5))
        for dx, dy, s in pat:
            Y2, X2 = Y + dy * b, X + dx * b
            if 0 <= X2 < W - b and 0 <= Y2 < H - b and (oid[Y2:Y2 + b, X2:X2 + b] == 0).all():
                fam[Y2:Y2 + b, X2:X2 + b] = FI['E']; shd[Y2:Y2 + b, X2:X2 + b] = s

def outline():
    """建物・物のふちを、自分の色の一番暗い色にする（地面に接するところだけ）"""
    out = np.zeros_like(oid, bool)
    for k in range(1, S // 2 + 1):
        for dy, dx in ((k, 0), (-k, 0), (0, k), (0, -k)):
            nb = np.roll(np.roll(oid, dy, 0), dx, 1)
            out |= (oid != 0) & (nb == 0)
    shd[out] = np.maximum(0, shd[out] - 3)

def finish(path):
    rgb = np.zeros((H, W, 3), np.uint8)
    ok = fam >= 0
    rgb[ok] = TABLE[fam[ok], shd[ok]]
    img = Image.fromarray(rgb).convert("RGBA")
    spr = os.path.join(HERE, "..", "assets", "character", "farmer_front_v2.png")
    if False and os.path.exists(spr):
        sp = Image.open(spr).convert("RGBA"); fx, fy = proj(np.array([1.0, -4.3, 0.]))
        from PIL import ImageDraw
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((fx - 8, fy - 3, fx + 8, fy + 3), fill=(12, 16, 28, 110))
        img = Image.alpha_composite(img, sh); img.alpha_composite(sp, (int(fx) - 16, int(fy) - 40))
    img = img.convert("RGB"); img.save(path)
    img.resize((W // 2, H // 2), Image.NEAREST).save(path.replace(".png", "_half.png"))

if __name__ == "__main__":
    build(); props(); outline()
    finish(os.path.join(HERE, "..", "assets", "farmhouse_iso_flat.png" if FLAT else "farmhouse_iso.png"))
    print("done")
