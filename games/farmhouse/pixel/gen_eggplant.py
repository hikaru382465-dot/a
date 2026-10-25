# ナス（64×96）：曲がった軸に沿った太さ（高さ場）→ 法線 → 光・つや・下からの反射光 → 段にまとめる。パレットは q(紫)・E(へた)・D(茎)
import numpy as np, math, os
from PIL import Image
import pxl
pal, _ = pxl.load_palette()
W, H = 64, 100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "items")
def col(f, s): return pal[f][int(np.clip(s, 0, 7))]

def eggplant(bitten=False):
    y, x = np.mgrid[0:H, 0:W].astype(float)
    t = np.clip((y - 16) / 78.0, 0, 1)                         # 0=上(へた) 1=下(先)
    cx = 30 + 9 * np.sin(t * 2.4) - 4 * t                       # 軸のカーブ（すこし右へ曲がる）
    # 太さ：首は細く、下がふくらみ、先は丸い
    wd = 8 + 10 * np.clip(t / .55, 0, 1) ** 1.2 * (1 - 0.0 * t)
    wd = np.where(t > .6, 18 * np.sqrt(np.clip(1 - ((t - .6) / .4) ** 2.2, 0, 1)) + 0 * t, wd)
    wd = np.where(t <= .6, 8 + 10 * np.sin(np.clip(t / .6, 0, 1) * math.pi / 2) ** 1.4, wd)
    d = (x - cx) / np.maximum(wd, 1e-3)
    body = (np.abs(d) < 1) & (y >= 16) & (t < 1)
    zz = np.sqrt(np.clip(1 - d ** 2, 0, 1)) * wd
    # 法線（高さ場の傾き）
    gy, gx = np.gradient(zz)
    nx, ny, nz = -gx, -gy, np.ones_like(zz)
    n = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2); nx, ny, nz = nx / n, ny / n, nz / n
    L = np.array([-.55, -.6, .58]); L /= np.linalg.norm(L)
    lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    Hh = L + np.array([0, 0, 1.0]); Hh /= np.linalg.norm(Hh)
    spec = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1) ** 38
    bounce = np.clip(-(nx * .4 + ny * .8) , 0, 1) * (np.abs(d) > .55) * .22
    I = .16 + .74 * lam + bounce
    band = np.clip(np.floor(I * 6.2), 0, 6).astype(int)
    A = np.zeros((H, W, 4), np.uint8)
    for yy, xx in zip(*np.nonzero(body)):
        sh = 1 + min(band[yy, xx], 4)
        f = 'q'
        if spec[yy, xx] > .8 and abs(d[yy, xx]) < .8: f, sh = 'q', 6
        A[yy, xx, :3] = col(f, min(sh, 7)); A[yy, xx, 3] = 255
    # つや：左がわに細い縦の帯（太さは中ほどで太い）
    for yy in range(26, 84):
        tt = (yy - 26) / 58.0
        gx0 = cx[yy, 0] - wd[yy, 0] * .52
        ln = int(round(5 + 18 * math.sin(math.pi * min(1, tt * 1.15)) ** .8 * (1 if tt < .85 else 0.4)))
        if tt > .83: continue
        xs = int(round(gx0))
        wdt = 2 if .15 < tt < .6 else 1
        A[yy, xs:xs + wdt, :3] = col('q', 7); A[yy, xs:xs + wdt, 3] = 255
    # へた：しわのような葉4まい＋茎
    cxt = cx[16, 0]
    cal = np.zeros((H, W), bool)
    for k, ang in enumerate((-70, -25, 25, 70)):
        for s_ in np.linspace(0, 1, 40):
            a_ = math.radians(ang)
            px_ = cxt + math.sin(a_) * 16 * s_; py_ = 14 + 9 * s_ * (1 - 0.4 * abs(math.sin(a_))) + 3 * s_ ** 2
            r_ = 4.4 * (1 - s_) ** .8 + .6
            cal |= (x - px_) ** 2 + (y - py_) ** 2 <= r_ ** 2
    cal |= (np.abs(x - cxt) < 12) & (y >= 10) & (y < 17) & (((x - cxt) / 12) ** 2 + ((y - 16) / 8) ** 2 < 1)
    yy2, xx2 = np.nonzero(cal)
    for yy, xx in zip(yy2, xx2):
        sh = 2 + (1 if yy < 14 else 0) + (1 if xx < cxt else 0)
        A[yy, xx, :3] = col('E', sh); A[yy, xx, 3] = 255
    for yy in range(2, 13):                                   # 茎
        for xx in range(int(cxt) - 2 + (yy < 7), int(cxt) + 3):
            A[yy, xx - (1 if yy < 6 else 0), :3] = col('D', 3 if xx > cxt else 4); A[yy, xx - (1 if yy < 6 else 0), 3] = 255
    # 輪郭
    al = A[..., 3] > 0
    pad = np.pad(al, 1); edge = ~al & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
    A[edge, :3] = col('q', 0); A[edge, 3] = 255
    return A

imgs = [eggplant()]
big = []
for im in imgs:
    Image.fromarray(im).save(os.path.join(OUT, "eggplant.png"))
    b = Image.fromarray(im).resize((W * 8, H * 8), Image.NEAREST); big.append(b)
sheet = Image.new("RGBA", (W * 8 + 40, H * 8 + 40), (40, 44, 58, 255)); sheet.alpha_composite(big[0], (20, 20))
sheet.save(os.path.join(OUT, "eggplant_x8.png"))
print("ok", len({tuple(p) for p in imgs[0].reshape(-1, 4) if p[3]}))
