"""
家を水辺に立たせて、海に映す。python iso_reflect.py → assets/effects/house_reflect_frame0.png, house_reflect.gif（8コマ）
反射のしくみ：家の面ごとに、画面の点から高さ z を逆算（ななめ上の視点の式）→ 水面(z=WZ)で折り返した位置へ点を移す
  → 水の色へ寄せる（暗く・青く）→ 行ごとに波でゆがめる → 水面から遠いほど網点でうすく → 水のマスの上だけに重ねる。
"""
import os, sys, math
import numpy as np
from PIL import Image
sys.argv = [sys.argv[0]]
import iso as I

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "assets", "effects")
TAU = 2 * math.pi
WZ = -0.35                                  # 水面の高さ（陸は z=0）
NF = 8
pal, _ = I.pxl.load_palette(); WAT = I.TABLE[I.FI['w']]
BAY = I.PX * 0 + I.np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])[np.mgrid[0:I.H, 0:I.W][0] % 4, np.mgrid[0:I.H, 0:I.W][1] % 4] / 16.0

def sea_tex(t):
    wi = I.FI['w']
    def f(x, y, z, u, v, px, py):
        uu = np.mod(x / 3.0, 1.0); vv = np.mod(y / 3.0, 1.0)
        warp = .13 * np.sin(TAU * (3 * vv) + TAU * t) + .06 * np.sin(TAU * (5 * vv + uu) - TAU * 2 * t)
        h = (.62 * np.sin(TAU * (2 * uu + warp) - TAU * t) + .30 * np.sin(TAU * (3 * uu + vv + .5 * warp) - TAU * 2 * t + 1.1)
             + .22 * np.sin(TAU * (2 * vv + .08 * np.sin(TAU * 2 * uu)) + TAU * t + .4) + .12 * np.sin(TAU * (6 * uu - 5 * vv) + TAU * 3 * t))
        q = np.clip((h + 1.0) / 2.0, 0, 1)
        B = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
        qx, qy = px >> 1, py >> 1                                                              # 絵のドット（2×2）の単位で、網点を打つ
        idx = np.clip(np.floor(q * 2.6 + (B[qy % 4, qx % 4] - .5) * .5).astype(int) + 2, 2, 4)
        idx = np.where((h > .9) & (B[(qy + 1) % 4, qx % 4] < .5), 5, idx)
        idx = np.where(h < -.8, 2, idx)
        return np.full(x.shape, wi, np.int8), idx.astype(np.int8)
    return f

cache = {}
def to_water(f, s):
    """色を水の色へ寄せる（暗く・青く）→ パレットの一番近い色に"""
    key = (int(f), int(s))
    if key not in cache:
        rgb = I.TABLE[f, s].astype(float); wc = WAT[2].astype(float)
        c = (rgb * .4 + wc * .6) * .8
        allc = I.TABLE.reshape(-1, 3).astype(float); j = int(((allc - c) ** 2).sum(1).argmin())
        cache[key] = (j // 8, j % 8)
    return cache[key]

def render(i):
    t = i / NF
    I.fam[:] = -1; I.shd[:] = 0; I.zb[:] = np.inf; I.oid[:] = 0; I.SHADOWS.clear()
    I.face((-30, -30, WZ), (60, 0, 0), (0, 60, 0), sea_tex(t), 0, 9)                        # 海
    I.box(-8, -2.0, WZ, 11, 8, 0, {'+C': I.ground, 'all': I.stone}, 1)                      # 陸（島）
    I.build(ground_plane=False, extras=False)                                                   # 家
    # ---- 反射
    H, W = I.H, I.W
    ys, xs = np.nonzero((I.oid > 0) & (I.oid != 9) & (I.fam >= 0))
    sy = ys + .5
    z = (-I.zb[ys, xs] - 1.2247 * (sy - I.OY) / I.A) / 2
    keep = z > 0.1                                                                              # 陸の面（z=0）や、岸のかべ（z<0）は映さない
    ys, xs, z = ys[keep], xs[keep], z[keep]
    dz = z - WZ
    ny = ys + np.round(2 * I.HZ * dz).astype(int)
    wave = np.sin(TAU * (ny / 17.0 + t)) * (1.0 + 3.2 * np.clip(dz / 6.0, 0, 1)) + np.sin(TAU * (ny / 7.0 - 2 * t)) * 1.2
    nx = xs + np.round(wave).astype(int)
    ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
    ys, xs, ny, nx, dz = ys[ok], xs[ok], ny[ok], nx[ok], dz[ok]
    fadep = 1 - .8 * np.clip(dz / 5.0, 0, 1)                                                   # 水面から遠いほど薄い
    vis = (BAY[(ny >> 1) << 1, (nx >> 1) << 1] < fadep * .8) & (I.oid[ny, nx] == 9)
    # 近いもの（元の depth が小さい）が勝つ：遠いほうから先に書き、近いほうが後から上書き
    sy_, sx_, dy_, dx_ = ys[vis], xs[vis], ny[vis], nx[vis]
    order = np.argsort(-I.zb[sy_, sx_])
    sy_, sx_, dy_, dx_ = sy_[order], sx_[order], dy_[order], dx_[order]
    lut = np.zeros((I.TABLE.shape[0], 8, 2), np.int8)
    for f_ in range(I.TABLE.shape[0]):
        for s_ in range(8): lut[f_, s_] = to_water(f_, s_)
    srcf, srcs = I.fam[sy_, sx_], I.shd[sy_, sx_]
    I.fam[dy_, dx_] = lut[srcf, srcs, 0]; I.shd[dy_, dx_] = lut[srcf, srcs, 1]
    rgb = np.zeros((H, W, 3), np.uint8); okp = I.fam >= 0; rgb[okp] = I.TABLE[I.fam[okp], I.shd[okp]]
    return Image.fromarray(rgb)

if __name__ == "__main__":
    fr = [render(i) for i in range(NF)]
    box = (300, 0, 1700, 1080)
    fr[0].crop(box).save(os.path.join(OUT, "house_reflect_frame0.png"))
    g = [f.crop(box).resize((700, 540), Image.NEAREST) for f in fr]
    g[0].save(os.path.join(OUT, "house_reflect.gif"), save_all=True, append_images=g[1:], duration=140, loop=0); print("ok")
