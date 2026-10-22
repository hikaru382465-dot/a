"""
りんごの高解像度版（96×96）。python gen_apple_hd.py → assets/items/apple_hd.png / apple_hd_bitten.png / apple_hd_x6.png
形＝くぼみのある丸い高さ場 → 法線で、光・つや（ブリン）・下からの反射光・くぼみのかげ → 縦しまの色むら（赤・だいだい・深い赤）→ 皮の小さな点（決まった位置） → 茎（曲線）・葉（葉脈）。
段は7段で、網点なし。パレットの色だけ。
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "items"); os.makedirs(OUT, exist_ok=True)
pal, _ = pxl.load_palette()
def col(f, s): return tuple(int(v) for v in pal[f][int(max(0, min(7, s)))])
def h2(ix, iy, seed=0):
    ix = np.asarray(ix, np.int64); iy = np.asarray(iy, np.int64)
    h = (ix * 73856093) ^ (iy * 19349663) ^ (seed * 83492791); h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return (h % 10007) / 10007.0
def vn(x, y, seed=0):
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int); fx, fy = x - x0, y - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    return (h2(x0, y0, seed) * (1 - fx) * (1 - fy) + h2(x0 + 1, y0, seed) * fx * (1 - fy) + h2(x0, y0 + 1, seed) * (1 - fx) * fy + h2(x0 + 1, y0 + 1, seed) * fx * fy)
LIGHT = np.array([-.52, -.62, .58]); LIGHT /= np.linalg.norm(LIGHT)
def bez(p0, p1, p2, p3, n=120):
    t = np.linspace(0, 1, n)[:, None]; P = [np.array(p, float) for p in (p0, p1, p2, p3)]
    return (1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t ** 2 * P[2] + t ** 3 * P[3]

def apple(S=96, bitten=False, clean=False):
    k = S / 32.0
    A = np.zeros((S, S, 4), np.uint8); Y, X = np.mgrid[0:S, 0:S]; x = (X + .5) / k; y = (Y + .5) / k      # 32×32 の座標
    # ---- 形
    c1 = ((x - 12.8) / 9.6) ** 2 + ((y - 18.6) / 10.0) ** 2 <= 1
    c2 = ((x - 19.2) / 9.6) ** 2 + ((y - 18.6) / 10.0) ** 2 <= 1
    low = ((x - 16) / 8.6) ** 2 + ((y - 23.6) / 7.6) ** 2 <= 1
    wob = 1 + .02 * np.sin(x * .9 + 1.0) + .015 * np.sin(y * 1.3)
    sh1 = ((x - 10.2) / 5.6) ** 2 + ((y - 14.6) / 5.0) ** 2 <= 1
    sh2 = ((x - 21.8) / 5.6) ** 2 + ((y - 14.6) / 5.0) ** 2 <= 1
    body0 = (c1 | c2 | low | sh1 | sh2) & ~(((x - 16) / 3.2) ** 2 + ((y - 7.0) / 2.6) ** 2 <= 1)
    bite = (body0 & (((x - 26.2) / 6.4) ** 2 + ((y - 19.4) / 5.8) ** 2 <= 1)) if bitten else np.zeros_like(body0)
    body = body0 & ~bite
    # ---- 高さ場（球＋上下のくぼみ）→ 法線
    u = (x - 16) / 14.2; v = (y - 18.6) / 12.6; r2 = u * u + v * v
    h = np.sqrt(np.clip(1 - r2, 0, 1)) * 12.0
    h -= 5.5 * np.exp(-(((x - 16) / 3.4) ** 2 + ((y - 7.6) / 2.6) ** 2))                     # 上のくぼみ
    h += 1.1 * np.exp(-(((x - 16) / 6.0) ** 2 + ((y - 27.5) / 2.0) ** 2))                    # 底のふくらみ
    hs = h * k
    gx = np.gradient(hs, axis=1); gy = np.gradient(hs, axis=0)
    nz = np.ones_like(gx); nx, ny = -gx, -gy; nn = np.sqrt(nx * nx + ny * ny + nz * nz); nx, ny, nz = nx / nn, ny / nn, nz / nn
    lam = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    hv = LIGHT + np.array([0, 0, 1.0]); hv /= np.linalg.norm(hv)
    spec = np.clip(nx * hv[0] + ny * hv[1] + nz * hv[2], 0, 1) ** 40                                # つや
    bounce = np.clip(-(nx * -.45 + ny * -.7) * .5, 0, 1) * (1 - nz) * 1.3                            # 右下からの反射光
    ao = 1 - .55 * np.exp(-(((x - 16) / 4.6) ** 2 + ((y - 8.8) / 3.8) ** 2))                         # くぼみのまわりの暗がり
    I = np.clip((.26 + .74 * lam) * ao + bounce * .22, 0, 1)
    # ---- 色むら：縦しま（赤・だいだい）
    ang = np.arctan2(x - 16, 20)
    st = vn(ang * 9 + 3, y * .05, 5) * .65 + vn(ang * 21, y * .09, 6) * .35
    orange = np.clip((st - .56) * 3.2, 0, 1) * np.clip(1.15 - (y - 4) / 22, 0, 1)                    # 上ほどだいだい
    deep = np.zeros_like(st)
    # ---- 7段にまとめる（網点なし）。clean=True は、ドット絵の見本（OpenGameArtのりんご）の作り方：少ない色・赤の中に暖色の段・細い弧のつや・三日月のかげ
    band = np.clip(np.floor(I * 7.0 + .15), 0, 6).astype(int)
    if clean:
        rr_ = np.hypot(u, v)
        core = body & (lam < .30) & (rr_ > .55) & (u + v > .1)                                   # 右下の三日月のかげ
        warm = body & (lam > .80) & (x < 20)                                                    # 明るい側は暖色（だいだい赤）へ色ずらし
        for yy, xx in zip(*np.nonzero(body)):
            if core[yy, xx]: f, sh = 'u', 3 if lam[yy, xx] < .12 else 4
            elif warm[yy, xx]: f, sh = 'H', 4
            elif lam[yy, xx] > .55: f, sh = 'G', 5
            else: f, sh = 'G', 4
            A[yy, xx, :3] = col(f, sh); A[yy, xx, 3] = 255
        # つや：左上のふちにそう、細い弧（太さは中ほどが太く、両はしが細い）
        for tt_ in np.linspace(0, 1, 90):
            ang_ = math.radians(198 + tt_ * 62); rad_ = .66
            cx_, cy_ = 16 + 14.2 * rad_ * math.cos(ang_), 18.6 + 12.6 * rad_ * math.sin(ang_)
            wd_ = .45 + 1.35 * math.sin(math.pi * tt_)
            m_ = body & ((x - cx_) ** 2 + (y - cy_) ** 2 <= wd_ ** 2)
            A[m_, :3] = col('H', 7); A[m_, 3] = 255
        dotm = body & ((x - 8.2) ** 2 + (y - 22.4) ** 2 <= 1.0); A[dotm, :3] = col('H', 7); A[dotm, 3] = 255
    else:
        for yy, xx in zip(*np.nonzero(body)):
            b = band[yy, xx]; o = orange[yy, xx]; d = deep[yy, xx]
            sv_ = st[yy, xx]
            if sv_ > .72 and 3 <= b <= 5 and y[yy, xx] < 21: f, sh = 'H', [1, 2, 3, 3, 4, 5, 6][b] - (1 if b >= 4 else 0)
            elif sv_ < .27 and b <= 4: f, sh = 'u', min(6, [1, 2, 3, 4, 4, 5, 6][b] + 0)
            else: f, sh = 'G', [1, 2, 3, 4, 4, 5, 6][b]
            A[yy, xx, :3] = col(f, sh); A[yy, xx, 3] = 255
    if not clean:
        sp1 = body & (spec > .42); A[sp1, :3] = col('G', 7); A[sp1, 3] = 255
        sp2 = body & (spec > .80); A[sp2, :3] = col('n', 7); A[sp2, 3] = 255
    # 皮の小さな点（決まった位置に14個、上のほうに多い）
    rng = np.random.default_rng(3)
    placed = 0
    while placed < (0 if clean else 14):
        px, py = rng.uniform(7, 26), rng.uniform(10, 28)
        ix, iy = int(px * k), int(py * k)
        if 0 <= ix < S and 0 <= iy < S and body[iy, ix] and lam[iy, ix] > .15:
            A[iy, ix, :3] = col('n', 6); A[iy, ix, 3] = 255
            if h2(ix, iy, 1) > .6: A[iy, min(S - 1, ix + 1), :3] = col('n', 5); A[iy, min(S - 1, ix + 1), 3] = 255
            placed += 1
    # ---- 茎（曲線）
    stem = bez((16.4, 8.8), (16.2, 5.5), (15.6, 3.6), (16.6, 1.4))
    for i, (sx, sy) in enumerate(stem):
        for dx in np.arange(-.75, .76, .25 / k * 2):
            xx, yy = int((sx + dx) * k), int(sy * k)
            if 0 <= xx < S and 0 <= yy < S and (sy < 8.6):
                t = (dx + .75) / 1.5; A[yy, xx, :3] = col('D', 5 if t < .3 else 4 if t < .65 else 2); A[yy, xx, 3] = 255
    # ---- 葉：茎のつけ根から右上へ反って先がとがる。中央の葉脈、左右で明暗、ふちのぎざぎざ
    path = bez((17.2, 7.4), (20.0, 2.8), (25.0, 2.2), (29.0, 5.2), 160)
    px_all = (X + .5) / k; py_all = (Y + .5) / k
    best = np.full((S, S), 1e9); tt = np.zeros((S, S)); sg = np.zeros((S, S))
    for i, (cx_, cy_) in enumerate(path):
        d = np.hypot(px_all - cx_, py_all - cy_)
        upd = d < best
        tang = path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]; tang = tang / (np.hypot(*tang) + 1e-9)
        side = np.sign(-(px_all - cx_) * tang[1] + (py_all - cy_) * tang[0] * -1 * -1)
        best = np.where(upd, d, best); tt = np.where(upd, i / (len(path) - 1), tt); sg = np.where(upd, np.sign((px_all - cx_) * (-tang[1]) + (py_all - cy_) * tang[0]), sg)
    wdt = 2.7 * np.sin(np.pi * np.clip(tt * 1.0, 0, 1)) ** .75 * (1 + .06 * np.sin(tt * 55))
    leafm = (best <= wdt) & (tt > .02)
    for yy, xx in zip(*np.nonzero(leafm)):
        t_ = tt[yy, xx]; d_ = best[yy, xx]; w_ = wdt[yy, xx]
        if d_ < .32: sh = 2                                                  # 葉脈
        elif sg[yy, xx] > 0: sh = 6 if t_ < .6 else 5                        # 明るい側
        else: sh = 4 if t_ < .6 else 3                                       # 暗い側
        if w_ - d_ < .45: sh = max(1, sh - 1)                                # ふちはやや暗く
        if abs(d_ - w_ * .55) < .2 and .2 < t_ < .85 and int(t_ * 14) % 2 == 0: sh = max(1, sh - 1)    # 側脈
        A[yy, xx, :3] = col('O', sh); A[yy, xx, 3] = 255
    # ---- かじったあと
    if bitten:
        for yy, xx in zip(*np.nonzero(bite)):
            d = ((x[yy, xx] - 26.2) / 6.4) ** 2 + ((y[yy, xx] - 19.4) / 5.8) ** 2
            A[yy, xx, :3] = col('n', 7 if d < .5 else 6 if d < .78 else 5 if d < .92 else 4); A[yy, xx, 3] = 255
        core = bite & (((x - 25.2) / 2.1) ** 2 + ((y - 19.4) / 3.0) ** 2 <= 1)
        A[core, :3] = col('n', 3); A[core, 3] = 255
        for sx, sy in ((25.0, 18.2), (25.0, 20.6)):
            seed = bite & (((x - sx) / .8) ** 2 + ((y - sy) / 1.0) ** 2 <= 1); A[seed, :3] = col('D', 2); A[seed, 3] = 255
    # ---- 縁取り（左上は明るい赤、右下は暗い赤）
    al = np.pad(A[..., 3] > 0, 1); e = np.zeros_like(al)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(al, dy, 0), dx, 1)
    e = (e & ~al)[1:-1, 1:-1]
    for yy, xx in zip(*np.nonzero(e)):
        a_ = (xx + yy) / (2.0 * S); A[yy, xx, :3] = col('R', 2) if a_ < .45 else col('R', 1); A[yy, xx, 3] = 255
    return A

if __name__ == "__main__":
    for nm, im in (("apple_hd", apple(96)), ("apple_hd_bitten", apple(96, True)), ("apple_hd_clean", apple(96, False, True)), ("apple_hd_clean_bitten", apple(96, True, True))):
        Image.fromarray(im).save(os.path.join(OUT, nm + ".png"))
    bg = Image.new("RGBA", (96 * 4 + 20, 96 + 8), (40, 52, 70, 255))
    for i_, im_ in enumerate((apple(96), apple(96, True), apple(96, False, True), apple(96, True, True))): bg.alpha_composite(Image.fromarray(im_), (4 + i_ * 100, 4))
    bg.resize((bg.width * 5, bg.height * 5), Image.NEAREST).convert("RGB").save(os.path.join(OUT, "apple_hd_x6.png")); print("ok")
