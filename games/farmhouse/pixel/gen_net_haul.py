"""
網を引き上げる。海にひろがった網が、ふちをすぼめながら水から持ち上がり、資材（板・樽・丸太・魚・箱）をつつんだ袋になって、水をしたたらせる。
python gen_net_haul.py → assets/effects/net_haul_sheet.png / net_haul.gif（12コマ）, net_haul_still.png（引き上げた袋 1枚）
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "effects")
pal, _ = pxl.load_palette()
def col(f, s): return np.array(pal[f][int(min(7, max(0, s)))], np.uint8)
BAY = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
def h2(ix, iy, seed=0):
    ix = np.asarray(ix, np.int64); iy = np.asarray(iy, np.int64)
    h = (ix * 73856093) ^ (iy * 19349663) ^ (seed * 83492791); h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return (h % 10007) / 10007.0
def smooth(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

W, H = 96, 112
YW = 92                                     # 水面の高さ（画面の行）
HOOK = (48, 3)
Y, X = np.mgrid[0:H, 0:W]

class C:
    def __init__(self): self.img = np.zeros((H, W, 4), np.uint8)
    def px(self, x, y, f, s):
        if 0 <= x < W and 0 <= y < H: self.img[y, x, :3] = col(f, s); self.img[y, x, 3] = 255
    def mask(self, m, f, s):
        if np.ndim(s) == 0: self.img[m, :3] = col(f, s); self.img[m, 3] = 255
        else:
            for v in np.unique(s[m]): mm = m & (s == v); self.img[mm, :3] = col(f, int(v)); self.img[mm, 3] = 255
    def rect(self, x0, y0, x1, y1, f, s):
        for yy in range(y0, y1):
            for xx in range(x0, x1): self.px(xx, yy, f, s)

# ---- 資材（小さな絵）。袋の中にいれる
def item_plank(c, x, y, ang, L=22, f='D', s=4):
    for k in range(L):
        px_, py_ = x + k * math.cos(ang), y + k * math.sin(ang)
        for o in (0, 1, 2):
            c.px(int(round(px_ - math.sin(ang) * o)), int(round(py_ + math.cos(ang) * o)), f, s + (1 if o == 0 else -1 if o == 2 else 0))
    c.px(int(x + L * math.cos(ang)), int(y + L * math.sin(ang)), 'D', 6)
def item_barrel(c, x, y):
    for yy in range(0, 13):
        w = 6 + int(1.5 * math.sin(math.pi * yy / 12))
        for xx in range(-w, w + 1):
            c.px(x + xx, y + yy, 'D', 4 if xx < -w + 3 else 3 if xx < w - 2 else 2)
    for yy in (3, 9):
        for xx in range(-7, 8): c.px(x + xx, y + yy, 'I', 3)
    for xx in range(-5, 6): c.px(x + xx, y - 1, 'D', 5)
def item_log(c, x, y):
    for yy in range(-5, 6):
        for xx in range(0, 18):
            if xx < 3 and abs(yy) > 4 - xx * .3: continue
            c.px(x + xx, y + yy, 'D', 2 if yy > 2 else 3 if yy > -2 else 4)
    for yy in range(-5, 6):
        for xx in (-1, 0):
            if yy * yy < 26 - 1: c.px(x + xx, y + yy, 'D', 6 if (yy * yy + xx * 3) % 7 > 2 else 5)
def item_fish(c, x, y, dirn=1):
    body = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (8, 0), (2, -1), (3, -1), (4, -1), (5, -1), (6, -1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (9, -1), (10, -2), (10, 1), (9, 0), (9, 1)]
    for dx, dy in body: c.px(x + dx * dirn, y + dy, 'S' if dy <= 0 else 'I', 5 if dy < 0 else 4 if dy == 0 else 3)
    c.px(x + 1 * dirn, y - 1, 'T', 0)
def item_crate(c, x, y):
    c.rect(x, y, x + 12, y + 10, 'D', 4)
    for xx in range(x, x + 12): c.px(xx, y, 'D', 6); c.px(xx, y + 9, 'D', 2)
    for k in range(10): c.px(x + 1 + k, y + 1 + k * 9 // 10, 'D', 2); c.px(x + 10 - k, y + 1 + k * 9 // 10, 'D', 2)
    for xx in (x, x + 11):
        for yy in range(y, y + 10): c.px(xx, yy, 'D', 1)

def contents(c, cx, cy, t):
    """袋のなか（t: 袋のふくらみ）"""
    item_log(c, cx - 11, cy + 14)
    item_barrel(c, cx + 5, cy + 6)
    item_crate(c, cx - 15, cy + 2)
    item_fish(c, cx - 4, cy + 22, 1); item_fish(c, cx + 6, cy + 25, -1)

def bag_mask(cx, top, bot, Wd):
    u = (Y + .5 - top) / (bot - top); uc = .62
    hw = np.where(u >= uc, Wd * np.sqrt(np.clip(1 - ((u - uc) / (1 - uc)) ** 2, 0, 1)), Wd * np.clip(u / uc, 0, 1) ** 1.25 + 1.2)
    return (u >= 0) & (u <= 1) & (np.abs(X + .5 - cx) <= hw), hw, u

def frame(i, N=12, sway=0.0):
    t = i / (N - 1)
    c = C()
    rise = smooth(.12, .95, t)                                       # 引き上げ具合
    close = smooth(.05, .6, t)                                       # すぼまり具合
    cx = 48 + sway
    # 水面のゆれ（背景は透明、水面の波紋だけ描く）
    # ---- 網（袋）の形：ひろがった円盤 → 袋
    cy_disc = YW + 4
    top = YW - 6 - rise * 72                       # 袋の上（すぼめ口）の位置
    bot = (cy_disc + 8) - rise * 40                  # 袋の底
    Wd = 25 - 4 * close
    if close < .15:
        # まだ水に広がった円盤（ちょっと持ち上がり始め）
        a = 25 - 6 * close / .15; asp = .5 + .12 * close / .15; cyy = cy_disc - rise * 8
        r = np.hypot((X + .5 - cx) / a, (Y + .5 - cyy) / (a * asp)); inside = r <= 1
        kk = 2 * a / 10; g1 = ((X + .5 - cx) / a + (Y + .5 - cyy) / (a * asp)) * kk / 2; g2 = ((X + .5 - cx) / a - (Y + .5 - cyy) / (a * asp)) * kk / 2
        grad = (kk / 2) * math.hypot(1 / a, 1 / (a * asp))
        mesh = inside & ((np.abs(g1 - np.round(g1)) / grad < .62) | (np.abs(g2 - np.round(g2)) / grad < .62))
        rim = inside & (r > 1 - 2.4 / a)
        c.mask(mesh | rim, 'C', np.clip(np.round(4 - (Y + .5 - cyy) / (a * asp) * 1.3 - (r < .6) * 1), 1, 6).astype(int))
    else:
        # 袋：中身 → あみ目 → ふち。水の下の部分は水色に
        m, hw, u = bag_mask(cx, top, bot, Wd)
        cb = C(); contents(cb, int(cx), int(bot - 40 + (1 - close) * 6), t)
        # 袋の影（中身のうしろ）：あみ目のすき間から暗い内側が見える
        c.mask(m, 'w', 1 + (BAY[Y % 4, X % 4] < .3).astype(int))
        ci = cb.img[:, :, 3] > 0
        c.img[m & ci] = cb.img[m & ci]
        # あみ目（たて向きのひし形）
        P = 8.0
        g1 = (X + Y * .85) / P; g2 = (X - Y * .85) / P
        # 袋の丸みで線が集まる：口に近いほど細かく
        mesh = m & ((np.abs(g1 - np.round(g1)) < .11) | (np.abs(g2 - np.round(g2)) < .11))
        edge = m & (np.abs(np.abs(X + .5 - cx) - hw) < 1.6)
        lit = np.clip(np.round(4 + ((X + .5 - cx) / np.maximum(hw, 1)) * -1.2 + (u < .3) * .5), 1, 6).astype(int)
        c.mask(mesh, 'C', lit)
        c.mask(edge, 'C', np.clip(lit - 1, 1, 6))
        # 口のすぼめ結び目とロープ
        kx, ky = int(cx), int(top)
        c.rect(kx - 2, ky - 1, kx + 3, ky + 3, 'D', 3); c.rect(kx - 1, ky - 1, kx + 2, ky, 'D', 5)
        for yy in range(HOOK[1], ky - 1):
            xx = int(round(HOOK[0] + (cx - 48) * ((yy - HOOK[1]) / max(1, ky - HOOK[1]))))
            c.px(xx, yy, 'C', 4); c.px(xx + 1, yy, 'C', 2)
        # 口からはみだす板（引き上げたあとの資材）
        if t > .55:
            k = smooth(.55, .9, t)
            for dx, ang in ((-5, -1.95), (2, -1.3), (6, -.95)):
                item_plank(c, int(cx + dx), int(top + 6), ang, int(7 + 7 * k), "D", 4)
        # 水中の部分：水の色にかぶせる（あみ目と中身がにじむ）
        sub = (Y >= YW) & (c.img[:, :, 3] > 0)
        swz = BAY[Y % 4, X % 4] < .62
        c.img[sub & swz, :3] = col('w', 3); c.img[sub & swz, 3] = 255
    # ---- 水面：波紋、しずくの滝
    def ripple(rad, k, f='w', s=6):
        d = np.hypot((X + .5 - cx) / rad, (Y + .5 - (YW + 1)) / (rad * .5))
        mm = (np.abs(d - 1) < 1.1 / rad) & (BAY[(Y + 1) % 4, X % 4] < .35 + .6 * k) & (h2(X // 3, Y // 2, 3) > .22)
        mm &= c.img[:, :, 3] == 0
        c.mask(mm, f, s)
    ripple(30 + 10 * t, 1 - .5 * t); ripple(22 + 8 * t, .8 - .4 * t, 'w', 5)
    if t < .5: ripple(36 + 22 * t, .5, 'w', 4)
    # 袋の底から水がしたたる
    if close >= .15:
        m, hw, u = bag_mask(cx, top, bot, Wd)
        yb = int(bot)
        ndrop = int(round(9 * (1 - smooth(.55, 1.0, t)) + 3))
        for j in range(ndrop):
            fx = (h2(j, 1, 7) - .5) * 1.7 * (Wd * .85); ph = (h2(j, 2, 8) + t * 3.0 + j * .37) % 1
            ys = yb + 1 + int(ph * (YW + 4 - yb)); xs = int(cx + fx)
            if ys < YW + 2 and ys > yb - 1:
                c.px(xs, ys, 'w', 7); c.px(xs, ys + 1, 'w', 6)
        if t > .3:                                                    # 水の筋（袋のふちを伝う）
            for xx in (-1, 1):
                for yy in range(yb - 8, yb):
                    if h2(yy, xx, 4) > .4: c.px(int(cx + xx * (Wd * .6)), yy, 'w', 6)
        # 水面にぽたぽた輪
        if t > .45:
            for j in range(3):
                ph = (t * 3.0 + j * .33) % 1; rr = 2 + ph * 7
                if ph > .1:
                    for ang in np.linspace(0, math.tau, 14, endpoint=False):
                        c.px(int(cx + (j - 1) * 9 + math.cos(ang) * rr), int(YW + 2 + math.sin(ang) * rr * .5), 'w', 6)
    return c.img

N = 12
fr = [frame(i, N, sway=(math.sin(i * .9) * 1.2 * smooth(.6, 1, i / (N - 1)))) for i in range(N)]
h, w = fr[0].shape[:2]
sheet = np.zeros((h * 2, w * 6, 4), np.uint8)
for i, f in enumerate(fr): sheet[(i // 6) * h:(i // 6 + 1) * h, (i % 6) * w:(i % 6 + 1) * w] = f
Image.fromarray(sheet).save(os.path.join(OUT, "net_haul_sheet.png"))
Image.fromarray(fr[-1]).save(os.path.join(OUT, "net_haul_still.png"))
def bgw(t):
    cvx, cvy = np.meshgrid(np.arange(W), np.arange(H))
    hh = np.sin(2 * math.pi * (cvx / 31.0 + cvy / 11.0 - t)) * .5 + np.sin(2 * math.pi * (cvx / 17.0 - cvy / 7.0 + t * 2)) * .35
    idx = np.clip(np.floor((hh + 1) / 2 * 2.4 + (BAY[cvy % 4, cvx % 4] - .5) * .6).astype(int) + 2, 2, 4)
    img = np.zeros((H, W, 4), np.uint8)
    for v in (2, 3, 4): img[idx == v, :3] = col('w', v)
    img[..., 3] = 255
    sky = np.arange(H)[:, None] < YW - 2                              # 水面より上は夜空の色
    img[(cvy < YW - 2)] = [*col('K', 2), 255]
    return img
K = 5
g = []
for i, f in enumerate(fr):
    b = Image.fromarray(bgw(i / 12.0)); b.alpha_composite(Image.fromarray(f)); g.append(b.resize((W * K, H * K), Image.NEAREST).convert("RGB"))
g[0].save(os.path.join(OUT, "net_haul.gif"), save_all=True, append_images=g[1:], duration=[110] * 10 + [200, 260], loop=0)
g[-1].save(os.path.join(OUT, "net_haul_preview.png"))
print("ok")
