"""
水がはねるアニメーション（斜め上45度から見下ろす）。水面は縦に0.707つぶれた楕円、高さも0.707倍。
しくみ：しぶきを3Dの点で計算 → 45度で画面に投影。王冠（まるい水のかべ）・中央の水柱・とびちる水玉・広がる波紋・あわ。
python gen_splash.py → assets/effects/splash45_sheet.png（透明）, splash45.gif（海の上）, splash45_big.png（大きく並べた確認）
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "effects")
pal, _ = pxl.load_palette()
def col(f, s): return tuple(int(v) for v in pal[f][int(max(0, min(7, s)))])
BAY = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
TAU = math.tau
def h2(a, b, seed=0):
    h = (int(a) * 73856093) ^ (int(b) * 19349663) ^ (seed * 83492791); h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return (h % 10007) / 10007.0
W, H = 112, 84; CX, CY = 56.0, 52.0
S45 = math.sin(math.radians(45)); C45 = math.cos(math.radians(45))      # ふかん45度：地面の奥ゆき＝sin、高さ＝cos
NF = 20
def proj(x, y, z): return CX + x, CY + y * S45 - z * C45

class Cv:
    def __init__(self): self.a = np.zeros((H, W, 4), np.uint8); self.Y, self.X = np.mgrid[0:H, 0:W]
    def p(self, x, y, f, s):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H: self.a[y, x] = (*col(f, s), 255)

def ripple(cv, rad, sv, k):
    """水面の波紋：45度の楕円（縦0.707）。とぎれとぎれ"""
    d = np.hypot((cv.X + .5 - CX) / rad, (cv.Y + .5 - CY) / (rad * S45))
    m = (np.abs(d - 1) < 1.05 / rad) & (BAY[(cv.Y + 1) % 4, cv.X % 4] < k) & (cv.a[..., 3] == 0)
    for y, x in zip(*np.nonzero(m)): cv.a[y, x] = (*col('w', sv), 255)

def draw_crown(cv, tau, half):
    """王冠。half=-1：奥の半分（内がわが見える）、+1：手前の半分（外がわ）"""
    if tau > .82: return
    rise = math.sin(math.pi * min(1, tau / .62)) ** .75
    Hm = 21.0 * rise * (1 - smooth(.55, .82, tau))
    if Hm < .6: return
    r = 4.5 + 13.5 * (1 - math.exp(-tau * 4.2))
    thick = 2.0 - 1.0 * smooth(.2, .75, tau)
    ths = np.linspace(0, TAU, 220, endpoint=False)
    order = sorted(ths, key=lambda t: math.sin(t))
    for th in order:
        sn = math.sin(th)
        if (half < 0 and sn >= 0) or (half > 0 and sn < 0): continue
        n = .75 + .25 * math.sin(th * 7 + 1.3) + .15 * math.sin(th * 13 + .4); spike = 4.0 * (h2(int(th * 11), 3) > .82) * rise
        ht = Hm * n + spike
        rr = r + (1 - rise) * 1.2
        gx, gy = rr * math.cos(th), rr * sn
        for z in np.arange(0, ht + .01, .5):
            x, y = proj(gx, gy, z)
            fz = z / max(ht, 1)
            s = 4 + (2 if fz > .8 else 1 if fz > .55 else 0) - (1 if fz < .2 else 0)
            s += round(-math.cos(th) * 1.0) * (1 if half > 0 else 0)
            if half < 0: s = max(3, s - 1)                                             # 奥のかべは少し暗い
            f = 'w'; sv = int(max(2, min(7, s)))
            for tx in (0, 1) if thick > 1.4 else (0,):
                cv.p(x + tx, y, f, sv)
        xt, yt = proj(gx, gy, ht); cv.p(xt, yt, 'w', 7); cv.p(xt + 1, yt, 'w', 7)         # 縁の白
        if half > 0 and z > 2:
            xb, yb = proj(gx, gy, 0); cv.p(xb, yb + 1, 'w', 7) if h2(int(th * 20), 4) > .6 else None   # 根もとのあわ

def smooth(a, b, x): t = max(0, min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t)

def draw_jet(cv, tau):
    if tau < .12 or tau > .85: return
    u = (tau - .12) / .73
    top = 27.0 * math.sin(math.pi * min(1, u * 1.05)) ** .8 * (1 - smooth(.7, 1.0, u) * .6)
    if top < 1: return
    base_r = 2.6 - smooth(0, .8, u) * .6
    for z in np.arange(0, top + .01, .5):
        fz = z / top; rho = base_r * (1 - .25 * fz) + (1.5 if fz > .86 else 0)                 # 先にふくらみ
        for dx in np.arange(-rho, rho + .01, .5):
            x, y = proj(dx, 0, z); k = dx / max(rho, 1)
            s = 5 - round(k * 1.6) + (1 if fz > .9 else 0) - (1 if fz < .1 else 0)
            cv.p(x, y, 'w', max(2, min(7, int(s))))
    xt, yt = proj(0, 0, top + 1); cv.p(xt - 1, yt, 'w', 7); cv.p(xt, yt - 1, 'w', 7)

# 水玉（3D）：たん生フレーム・初速・位置
rng = np.random.default_rng(7)
DROPS = []
for i in range(46):
    th = rng.uniform(0, TAU); sp = rng.uniform(.8, 3.2); vz = rng.uniform(3.4, 6.4)
    t0 = int(rng.integers(1, 7)); r0 = rng.uniform(2, 10)
    DROPS.append(dict(th=th, vx=math.cos(th) * sp, vy=math.sin(th) * sp, vz=vz, t0=t0, x0=math.cos(th) * r0, y0=math.sin(th) * r0, big=rng.random() > .5))
G = .30

def frame(i):
    cv = Cv(); tau = i / (NF - 1) * 1.0
    # 波紋（外へ広がる）と、いまの衝撃のあわの輪
    for k in range(3):
        a = tau * 1.0 - k * .14
        if a <= 0: continue
        rad = 4 + 44 * (1 - math.exp(-a * 2.4)); fade = max(0, 1 - a * 1.0)
        if rad > 5: ripple(cv, rad, 6 if k == 0 else 5 if k == 1 else 4, .2 + .8 * fade)
    if tau < .55: ripple(cv, 3.5 + 20 * tau, 7, .9 * (1 - tau / .55))
    draw_crown(cv, tau, -1); draw_jet(cv, tau)
    # 水玉と、おちた先の小さな輪
    for d in DROPS:
        age = i - d['t0']
        if age < 0: continue
        x = d['x0'] + d['vx'] * age; y = d['y0'] + d['vy'] * age; z = d['vz'] * age - .5 * G * age * age
        if z < 0:
            la = age - (2 * d['vz'] / G)               # 着水してからのコマ
            tl = i - (d['t0'] + 2 * d['vz'] / G)
            if 0 <= tl < 4:
                lx = d['x0'] + d['vx'] * (2 * d['vz'] / G); ly = d['y0'] + d['vy'] * (2 * d['vz'] / G)
                rr = 1.2 + tl * 1.6
                for ang in np.linspace(0, TAU, 9, endpoint=False):
                    px_, py_ = proj(lx + math.cos(ang) * rr, ly + math.sin(ang) * rr * 1.0, 0); cv.p(px_, py_, 'w', 6 if tl < 2 else 5)
            continue
        px_, py_ = proj(x, y, z)
        f_s = 7 if z > 4 else 6
        cv.p(px_, py_, 'w', f_s)
        if d['big']: cv.p(px_ + 1, py_, 'w', 6); cv.p(px_, py_ + 1, 'w', 5)
    draw_crown(cv, tau, +1)
    return cv.a

frames = [frame(i) for i in range(NF)]
sheet = np.zeros((H * 4, W * 5, 4), np.uint8)
for i, f in enumerate(frames): sheet[(i // 5) * H:(i // 5 + 1) * H, (i % 5) * W:(i % 5 + 1) * W] = f
Image.fromarray(sheet).save(os.path.join(OUT, "splash45_sheet.png"))
def sea_bg(t):
    Y, X = np.mgrid[0:H, 0:W]
    hh = np.sin(TAU * (X / 31.0 + Y / 11.0 - t)) * .5 + np.sin(TAU * (X / 17.0 - Y / 7.0 + t * 2)) * .35
    idx = np.clip(np.floor((hh + 1) / 2 * 2.4 + (BAY[Y % 4, X % 4] - .5) * .6).astype(int) + 2, 2, 4)
    img = np.zeros((H, W, 4), np.uint8)
    for v in (2, 3, 4): img[idx == v, :3] = col('w', v)
    img[..., 3] = 255; return img
K = 6
g = []
for i, f in enumerate(frames):
    bg = Image.fromarray(sea_bg(i / NF)); bg.alpha_composite(Image.fromarray(f)); g.append(bg.resize((W * K, H * K), Image.NEAREST).convert("RGB"))
g[0].save(os.path.join(OUT, "splash45.gif"), save_all=True, append_images=g[1:], duration=[70] * (NF - 1) + [300], loop=0)
big = Image.new("RGB", (W * 5, H * 2))
for k, i in enumerate((1, 3, 5, 7, 9, 11, 13, 15, 17, 19)):
    bg = Image.fromarray(sea_bg(i / NF)); bg.alpha_composite(Image.fromarray(frames[i])); big.paste(bg.convert("RGB"), ((k % 5) * W, (k // 5) * H))
big.resize((big.width * 2, big.height * 2), Image.NEAREST).save(os.path.join(OUT, "splash45_big.png")); print("ok")
