"""
資材をあつめるときに海へ投げる網（ネット）。パレットの色だけ、1ドットずつ計算。
  ・投げる：手もとのまるめた網 → ひろがりながら弧をえがいて飛ぶ → 着水（しぶき・波紋）  16コマ
  ・海にうかぶ：ひらいた網（うき・おもり・ふちのなわ・水にしずむ中心）がゆらゆら  4コマ
python gen_net.py → assets/effects/net_throw_sheet.png/.gif, net_float_sheet.png/.gif, net_still.png, net_preview.png
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "effects"); os.makedirs(OUT, exist_ok=True)
pal, _ = pxl.load_palette()
def col(f, s): return np.array(pal[f][s], np.uint8)
BAY = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
def h2(ix, iy, seed=0):
    ix = np.asarray(ix, np.int64); iy = np.asarray(iy, np.int64)
    h = (ix * 73856093) ^ (iy * 19349663) ^ (seed * 83492791); h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return (h % 10007) / 10007.0
def smooth(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

class Canvas:
    def __init__(self, W, H):
        self.W, self.H = W, H; self.img = np.zeros((H, W, 4), np.uint8)
        self.Y, self.X = np.mgrid[0:H, 0:W]
    def put(self, mask, f, s):
        s = np.clip(s, 0, 7) if np.ndim(s) else min(7, max(0, s))
        c = np.zeros((self.H, self.W, 3), np.uint8)
        if np.ndim(s):
            for v in np.unique(s[mask]): c[mask & (s == v)] = col(f, int(v))
        else: c[:] = col(f, s)
        self.img[mask, :3] = c[mask]; self.img[mask, 3] = 255
    def line(self, p, q, sag, f, s):
        n = int(max(abs(q[0] - p[0]), abs(q[1] - p[1])) * 2) + 2
        for k in range(n + 1):
            t = k / n; x = p[0] + (q[0] - p[0]) * t; y = p[1] + (q[1] - p[1]) * t + sag * 4 * t * (1 - t)
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < self.W and 0 <= yi < self.H: self.img[yi, xi, :3] = col(f, s); self.img[yi, xi, 3] = 255

def draw_net(cv, cx, cy, a, asp, spin, P=9, haze=0.0, sink=False):
    """網1枚。a=半径(px)、asp=たて/よこ（1=まっすぐ向き、.5=水面にふせた形）、spin=回転、P=あみ目のよこ幅(px)"""
    X, Y = cv.X + .5 - cx, cv.Y + .5 - cy
    u, v = X / a, Y / (a * asp); r = np.hypot(u, v)
    inside = r <= 1.0
    c, s_ = math.cos(spin), math.sin(spin)
    uu, vv = u * c - v * s_, u * s_ + v * c
    kk = 2 * a / P
    grad = (kk / 2) * math.hypot(1 / a, 1 / (a * asp))
    g1, g2 = (uu + vv) * kk / 2, (uu - vv) * kk / 2
    d1 = np.abs(g1 - np.round(g1)) / grad; d2 = np.abs(g2 - np.round(g2)) / grad
    th = .62
    mesh = inside & ((d1 < th) | (d2 < th))
    knot = inside & (d1 < th * 1.1) & (d2 < th * 1.1)
    rim = inside & (r > 1 - max(2.0, 2.4) / a)
    # 色：上（奥）は明るく、手前は影。しずむ網は中心ほど暗く青い
    base = np.round(4 - v * 1.3 + (np.where(knot, 1, 0))).astype(int)
    rope = mesh | rim
    if sink:
        deep = np.clip(1 - r / .95, 0, 1)
        lost = (deep > .55)
        base = base - np.round(deep * 2.0).astype(int)
        pass
    rimshade = np.where(rim, base + 0, base)
    cv.put(rope, 'C', np.clip(np.where(rim, base - (v > .3) * 1, base) - 0, 1, 6))
    # ふちのなわは太く見えるよう、内がわにも1ドット（明るい線）
    inner = inside & (r > 1 - 4.0 / a) & (r <= 1 - 2.4 / a) & (v < .2) & (BAY[cv.Y % 4, cv.X % 4] < .6)
    cv.put(inner & ~rope, 'C', np.clip(base - 1, 1, 6))
    # おもり（ふちに8こ）とうき（あいだに4こ）
    for j in range(8):
        th_ = spin + j * math.tau / 8
        px, py = cx + math.cos(th_) * a * .985, cy + math.sin(th_) * a * asp * .985
        m = (cv.X + .5 - px) ** 2 + ((cv.Y + .5 - py) / max(.6, asp * 1.25)) ** 2 <= (1.9 if a > 12 else 1.2) ** 2
        cv.put(m & inside | (m & rim), 'I', np.where(cv.Y + .5 < py - .3, 4, 2) if m.any() else 2)
    for j in range(4):
        th_ = spin + (j * 2 + 1) * math.tau / 8 + math.tau / 16
        px, py = cx + math.cos(th_) * a * .985, cy + math.sin(th_) * a * asp * .985
        m = (cv.X + .5 - px) ** 2 + ((cv.Y + .5 - py) / max(.6, asp * 1.25)) ** 2 <= (1.6 if a > 12 else 1.0) ** 2
        cv.put(m, 'H', np.where(cv.Y + .5 < py - .3, 5, 3) if m.any() else 3)
    return inside

def water_bg(W, H, t=0.0):
    cv = Canvas(W, H)
    h = np.sin(2 * math.pi * (cv.X / 31.0 + cv.Y / 11.0 - t)) * .5 + np.sin(2 * math.pi * (cv.X / 17.0 - cv.Y / 7.0 + t * 2)) * .35
    q = (h + 1) / 2
    idx = np.clip(np.floor(q * 2.4 + (BAY[cv.Y % 4, cv.X % 4] - .5) * .6).astype(int) + 2, 2, 4)
    cv.put(np.ones((H, W), bool), 'w', idx)
    return cv

def ripple(cv, cx, cy, rad, asp=.5, phase=0.0, strength=1.0, f='w', s=6):
    """水の波紋（だ円）。とぎれとぎれの1ドットの輪"""
    d = np.hypot((cv.X + .5 - cx) / rad, (cv.Y + .5 - cy) / (rad * asp))
    m = (np.abs(d - 1) < 1.1 / rad) & (BAY[(cv.Y + 1) % 4, cv.X % 4] < .35 + .6 * strength) & (h2(cv.X // 3, cv.Y // 2, 3) > .22)
    cv.put(m, f, s)

def shadow(cv, cx, cy, a, asp=.5, k=.5):
    m = (((cv.X + .5 - cx) / a) ** 2 + ((cv.Y + .5 - cy) / (a * asp)) ** 2 <= 1) & (BAY[cv.Y % 4, cv.X % 4] < k)
    cv.put(m & (cv.img[:, :, 3] == 0), 'w', 1)

# ---------------------------------------------------------------- 投げる 16コマ
W1, H1 = 144, 104
NFLY, NSPL = 12, 4
p0 = np.array([22.0, 62.0]); p3 = np.array([112.0, 70.0]); APEX = 46.0
frames_throw = []
for i in range(NFLY + NSPL):
    cv = Canvas(W1, H1)
    if i < NFLY:
        t = i / (NFLY - 1); te = t ** .9
        gx = p0[0] + (p3[0] - p0[0]) * te; gy = p0[1] + (p3[1] - p0[1]) * te
        cy_ = gy - APEX * 4 * te * (1 - te) - 4 * (1 - te)
        a = (3.5 + (25 - 3.5) * smooth(.12, .86, t)) * (1 + .09 * math.sin(t * 9.4) * (1 - t)); asp = (1.0 - .5 * smooth(.25, 1.0, t)) * (1 + .16 * math.sin(t * 11) * (1 - t))
        spin = (1 - smooth(0, 1, t)) * math.pi * 1.7
        P = 4 + 5 * smooth(.1, .8, t)
        shadow(cv, gx, gy + 3, a * .9, .5, .45 * smooth(0, .4, t))
        # 手もとへのなわ（たるむ）：網のふちの近い所 → 手
        att = np.array([gx - a * .9, cy_ + 1])
        if t < .97: cv.line(p0 + np.array([2, 2]), att, 7 * (1 - t) + 2, 'C', 3)
        if t < .5:
            cv.put((cv.X >= p0[0] - 3) & (cv.X <= p0[0] + 1) & (cv.Y >= p0[1] - 1) & (cv.Y <= p0[1] + 4), 'D', 2)
        draw_net(cv, gx, cy_, a, asp, spin, P=P)
        if t < .25:                                   # まるめた網のかたまり：球の陰影
            m = ((cv.X + .5 - gx) / a) ** 2 + ((cv.Y + .5 - cy_) / (a * asp)) ** 2 <= 1
            sh = ((cv.X + .5 - gx) + (cv.Y + .5 - cy_)) / (2 * a)
            cv.put(m & (cv.img[:, :, 3] == 0), 'C', np.where(sh > .35, 2, 3))
    else:
        k = i - NFLY; gx, gy = p3
        a, asp = 25, .5; cy_ = gy - 4 * (1 - k / 3.0) ** 2 * 3 + 0
        ripple(cv, gx, gy + 1, 26 + k * 6 + 4, .5, 0, 1.0 - k * .22)
        if k >= 1: ripple(cv, gx, gy + 1, 22 + k * 3, .5, 0, .8 - k * .15, 'w', 5)
        draw_net(cv, gx, gy, a, asp, 0.0, P=9, sink=True, haze=.2 * k)
        # しぶき：上へとんで落ちる水のつぶ
        for j in range(14):
            ang = j * math.tau / 14 + .3; sp = [13, 19, 21, 17][k] * (.6 + .5 * h2(j, 1, 2))
            dx = math.cos(ang) * sp * (1.0 + k * .35); dy = -abs(math.sin(ang)) * sp * 1.1 * [1.2, 1.0, .5, -.2][k] + 6 * k * k * .3
            xx, yy = int(gx + dx * 1.6 + math.cos(ang) * a * .7), int(gy + dy - 4 + math.sin(ang) * a * .3)
            if k < 3 or j % 2 == 0:
                for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)) if k < 2 else ((0, 0), (1, 0)):
                    if 0 <= xx + ox < W1 and 0 <= yy + oy < H1:
                        cv.img[yy + oy, xx + ox, :3] = col('w', 7 if k < 2 else 6); cv.img[yy + oy, xx + ox, 3] = 255
    frames_throw.append(cv.img.copy())

# ---------------------------------------------------------------- 海にうかぶ 4コマ
W2, H2 = 84, 56
frames_float = []
for i in range(4):
    cv = Canvas(W2, H2); ph = i / 4.0
    cx, cy = W2 / 2, H2 / 2 + 1
    bob = [0, 0, 1, 1][i] if False else int(round(math.sin(math.tau * ph) * .8))
    ripple(cv, cx, cy + 1, 32 + 3 * ph, .5, 0, .9 - .5 * ph, 'w', 5 if ph < .5 else 4)
    ripple(cv, cx, cy + 1, 29 + 3 * ph, .5, 0, .5, 'w', 4)
    draw_net(cv, cx + (1 if i in (1, 2) else 0) * 0, cy + bob, 25, .5, math.sin(math.tau * ph) * .035, P=10, sink=True)
    # 水が網のふちを洗う、白いあわ（ふち手前）
    for j in range(7):
        th_ = (.12 + j * .13 + ph * .08) * math.pi + math.pi * .0
        xx, yy = int(cx + math.cos(th_) * 25.5), int(cy + bob + math.sin(th_) * 12.9)
        if h2(j, i, 5) > .35 and 0 <= xx < W2 and 0 <= yy < H2: cv.img[yy, xx, :3] = col('w', 7); cv.img[yy, xx, 3] = 255
    frames_float.append(cv.img.copy())

# ---------------------------------------------------------------- 出力
def sheet(frames, cols):
    h, w = frames[0].shape[:2]; rows = (len(frames) + cols - 1) // cols
    s = np.zeros((h * rows, w * cols, 4), np.uint8)
    for i, f in enumerate(frames): s[(i // cols) * h:(i // cols + 1) * h, (i % cols) * w:(i % cols + 1) * w] = f
    return s
Image.fromarray(sheet(frames_throw, 8)).save(os.path.join(OUT, "net_throw_sheet.png"))
Image.fromarray(sheet(frames_float, 4)).save(os.path.join(OUT, "net_float_sheet.png"))
Image.fromarray(frames_float[0]).save(os.path.join(OUT, "net_still.png"))
K = 5
def over_sea(f, t, k=K):
    bg = water_bg(f.shape[1], f.shape[0], t); im = Image.fromarray(bg.img); im.alpha_composite(Image.fromarray(f))
    return im.resize((im.width * k, im.height * k), Image.NEAREST).convert("RGB")
gt = [over_sea(f, i / 16.0) for i, f in enumerate(frames_throw)]
gt[0].save(os.path.join(OUT, "net_throw.gif"), save_all=True, append_images=gt[1:], duration=[90] * 11 + [140] + [110, 110, 110, 160], loop=0)
gf = [over_sea(f, i / 4.0, 8) for i, f in enumerate(frames_float)]
gf[0].save(os.path.join(OUT, "net_float.gif"), save_all=True, append_images=gf[1:], duration=240, loop=0)
# 一枚の確認画像：飛んでいくコマを重ねて見る＋うかぶ絵
strip = Image.new("RGBA", (W1, H1)); bg = water_bg(W1, H1); strip.alpha_composite(Image.fromarray(bg.img))
for i in (0, 2, 4, 6, 8, 10, 12, 14): strip.alpha_composite(Image.fromarray(frames_throw[i]))
strip.resize((W1 * 6, H1 * 6), Image.NEAREST).convert("RGB").save(os.path.join(OUT, "net_preview.png"))
print("ok")
