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

def apple(S=96, bitten=False):
    k = S / 32.0
    A = np.zeros((S, S, 4), np.uint8); Y, X = np.mgrid[0:S, 0:S]; x = (X + .5) / k; y = (Y + .5) / k      # 32×32 の座標
    # ---- 形
    c1 = ((x - 12.8) / 9.6) ** 2 + ((y - 18.6) / 10.0) ** 2 <= 1
    c2 = ((x - 19.2) / 9.6) ** 2 + ((y - 18.6) / 10.0) ** 2 <= 1
    low = ((x - 16) / 8.6) ** 2 + ((y - 23.6) / 7.6) ** 2 <= 1
    wob = 1 + .02 * np.sin(x * .9 + 1.0) + .015 * np.sin(y * 1.3)
    body0 = (c1 | c2 | low) & ~(((x - 16) / 3.2) ** 2 + ((y - 7.0) / 2.6) ** 2 <= 1)
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
    st = vn(ang * 7 + 3, y * .08, 5) * .7 + vn(ang * 16, y * .15, 6) * .3
    orange = np.clip((st - .56) * 3.2, 0, 1) * np.clip(1.15 - (y - 4) / 22, 0, 1)                    # 上ほどだいだい
    deep = np.zeros_like(st)
    # ---- 7段にまとめる（網点なし）
    band = np.clip(np.floor(I * 7.0 + .15), 0, 6).astype(int)
    for yy, xx in zip(*np.nonzero(body)):
        b = band[yy, xx]; o = orange[yy, xx]; d = deep[yy, xx]
        if o > .85 and b >= 2: f, sh = 'H', min(7, b + 1)                                              # だいだいのしま
        elif d > .72 and b <= 4: f, sh = 'u', max(1, b + 1)                                                # 深い赤のしま（暗い）
        else: f, sh = 'G', [1, 2, 3, 4, 4, 5, 6][b]
        A[yy, xx, :3] = col(f, sh); A[yy, xx, 3] = 255
    # つや（2段：やわらかいふち＋まぶしい芯）
    sp1 = body & (spec > .42); A[sp1, :3] = col('G', 7); A[sp1, 3] = 255
    sp2 = body & (spec > .80); A[sp2, :3] = col('n', 7); A[sp2, 3] = 255
    # 皮の小さな点（決まった位置に14個、上のほうに多い）
    rng = np.random.default_rng(3)
    placed = 0
    while placed < 14:
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
    # ---- 葉（曲がった形、葉脈、ぎざぎざ）
    lx0, ly0 = 17.4, 6.4
    for yy in range(S):
        for xx in range(S):
            px_, py_ = (xx + .5) / k, (yy + .5) / k
            t = (px_ - lx0) / 9.0
            if not (0 <= t <= 1): continue
            cy_ = ly0 - 2.6 * math.sin(t * math.pi * .9) + 1.8 * t * t                          # 中心線（上へ反って先が下がる）
            wd = 2.1 * math.sin(math.pi * min(1, t * 1.05)) ** .8
            wd *= 1 + .08 * math.sin(t * 40)                                                  # ぎざぎざ
            dy = py_ - cy_
            if abs(dy) <= wd:
                up = dy < 0; vein = abs(dy) < .35 or (abs(dy - (-1 if up else 1) * (t * 4 % 1.5)) < .2 and abs(dy) > .6 and False)
                side = vn(px_ * 2, py_ * 2, 9)
                sh = 2 if vein else (6 if up and t < .75 else 5 if up else 4 if t < .5 else 3)
                if abs(abs(dy) - wd) < .45: sh = max(1, sh - 1)
                A[yy, xx, :3] = col('O', sh); A[yy, xx, 3] = 255
                if abs(abs(dy) - wd * .55) < .22 and t > .15 and t < .85 and h2(int(t * 12), 0, 2) > .3: A[yy, xx, :3] = col('O', 2)
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
    for nm, im in (("apple_hd", apple(96)), ("apple_hd_bitten", apple(96, True))):
        Image.fromarray(im).save(os.path.join(OUT, nm + ".png"))
    bg = Image.new("RGBA", (96 * 2 + 12, 96 + 8), (40, 52, 70, 255))
    bg.alpha_composite(Image.fromarray(apple(96)), (4, 4)); bg.alpha_composite(Image.fromarray(apple(96, True)), (104, 4))
    bg.resize((bg.width * 5, bg.height * 5), Image.NEAREST).convert("RGB").save(os.path.join(OUT, "apple_hd_x6.png")); print("ok")
