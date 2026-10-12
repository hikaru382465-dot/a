"""
音符マーク（♪ ♫ ♩ ♬）。ドット絵のアイコン（16×20）と、ふわっと上がって消えるアニメ。
python gen_notes.py → assets/ui/note_<形>_<色>.png, notes_sheet.png（一覧）, notes_float.gif（ちびキャラの頭から上がる）
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "ui"); os.makedirs(OUT, exist_ok=True)
pal, _ = pxl.load_palette()
def col(f, s): return tuple(int(v) for v in pal[f][int(max(0, min(7, s)))])
BAY = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
W, H = 16, 20
COL = {"white": ('s', 7, 5, 3), "pink": ('u', 6, 5, 3), "gold": ('n', 6, 5, 3), "aqua": ('w', 7, 6, 4)}   # 系統, 明, 中, 暗

class Cv:
    def __init__(self, w=W, h=H): self.w, self.h = w, h; self.a = np.zeros((h, w, 4), np.uint8); self.Y, self.X = np.mgrid[0:h, 0:w]
    def alpha(self): return self.a[..., 3] > 0

def head(c, cx, cy, rx=3.3, ry=2.5, tilt=-.35):
    X, Y = c.X + .5 - cx, c.Y + .5 - cy
    u = X * math.cos(tilt) - Y * math.sin(tilt); v = X * math.sin(tilt) + Y * math.cos(tilt)
    return (u / rx) ** 2 + (v / ry) ** 2 <= 1
def stem(c, x, y0, y1, w=2): return (c.X >= x - w / 2 + .5 - .5) & (c.X < x + w / 2 + .0) & (c.Y >= y0) & (c.Y <= y1)
def band(c, p, q, th):
    """p→q の太い線（ビーム・はた）"""
    px, py = p; qx, qy = q; dx, dy = qx - px, qy - py; L2 = dx * dx + dy * dy
    t = np.clip(((c.X + .5 - px) * dx + (c.Y + .5 - py) * dy) / L2, 0, 1)
    d = np.hypot(c.X + .5 - (px + t * dx), c.Y + .5 - (py + t * dy)); return d <= th / 2

def paint(shape, color, k=1.0):
    f, lo, mid, dk = COL[color]
    Wk, Hk = int(round(W * k)) + (1 if k < 1 else 0), int(round(H * k)) + (1 if k < 1 else 0)
    c = Cv(Wk, Hk); m = np.zeros((Hk, Wk), bool)
    K = lambda v: v * k
    def hd(cx, cy, rx=3.3, ry=2.5): return head(c, K(cx), K(cy), max(1.6, K(rx)), max(1.3, K(ry)))
    def st(x0, x1, y0, y1): return (c.X >= K(x0)) & (c.X < max(K(x1), K(x0) + 1.0)) & (c.Y >= K(y0)) & (c.Y <= K(y1))
    def bd(p, q, th): return band(c, (K(p[0]), K(p[1])), (K(q[0]), K(q[1])), max(1.3, K(th)))
    if shape == "eighth":
        m |= hd(5.0, 15.0); m |= st(6.5, 8.7, 3, 15)
        for t in np.linspace(0, 1, 30):
            x = 8.2 + 4.2 * math.sin(t * 1.5); y = 3.2 + 7.0 * t * (1 - .15 * t)
            m |= (c.X + .5 - K(x)) ** 2 + (c.Y + .5 - K(y)) ** 2 <= max(.5, K(1.25 - .5 * t)) ** 2
    elif shape == "beamed":
        m |= hd(4.0, 16.0, 3.0, 2.3) | hd(11.4, 14.0, 3.0, 2.3)
        m |= st(5.6, 7.4, 4, 16) | st(13.0, 14.8, 2, 14); m |= bd((6.5, 4.5), (13.9, 2.5), 2.6)
    elif shape == "quarter":
        m |= hd(5.0, 15.5, 3.4, 2.6); m |= st(6.8, 8.9, 2, 15.5)
    else:
        m |= hd(4.0, 16.5, 3.0, 2.3) | hd(11.4, 14.5, 3.0, 2.3)
        m |= st(5.6, 7.4, 4, 16.5) | st(13.0, 14.8, 2, 14.5); m |= bd((6.5, 4.2), (13.9, 2.2), 2.0) | bd((6.5, 8.0), (13.9, 6.0), 2.0)
    X, Y = c.X + .5, c.Y + .5
    lam = -(X - Wk / 2) * .10 / k - (Y - Hk / 2) * .07 / k
    s_ = np.where(lam > .28, lo, np.where(lam > -.2, mid, dk))
    for v in (lo, mid, dk):
        mm = m & (s_ == v); c.a[mm, :3] = col(f, v); c.a[mm, 3] = 255
    if k >= 1.8:
        # 面取り（ふちの明るさ）：左上のふちは明るく、右下のふちは暗い
        d = max(1, int(round(k * .7)))
        def sh(a_, dx, dy): return np.roll(np.roll(np.pad(a_, d + 1), dy, 0), dx, 1)[d + 1:-d - 1, d + 1:-d - 1]
        hi = m & ~sh(m, d, d); lw = m & ~sh(m, -d, -d)
        for mm, v in ((lw, max(1, dk - 1)), (hi, min(7, lo + 1))):
            c.a[mm, :3] = col(f, v); c.a[mm, 3] = 255
        # 頭のつや
        centers = {"eighth": [(5.0, 15.0)], "beamed": [(4.0, 16.0), (11.4, 14.0)], "quarter": [(5.0, 15.5)], "double": [(4.0, 16.5), (11.4, 14.5)]}[shape]
        for (cx, cy) in centers:
            g = (((c.X + .5 - K(cx - 1.0)) / max(1.0, K(1.2))) ** 2 + ((c.Y + .5 - K(cy - 1.0)) / max(.8, K(.7))) ** 2) <= 1
            c.a[g & m, :3] = col(f, 7); c.a[g & m, 3] = 255
        # 軸のハイライト（細い線）
        st_x = {"eighth": [7.0], "beamed": [6.1, 13.5], "quarter": [7.3], "double": [6.1, 13.5]}[shape]
        for x_ in st_x:
            hl = (np.abs(c.X + .5 - K(x_)) < .5) & (c.Y > K(6)) & (c.Y < K(13)) & m
            c.a[hl, :3] = col(f, min(7, lo + 1)); c.a[hl, 3] = 255
    th = max(1, int(round(k * .6)))
    al = c.alpha()
    for _ in range(th):
        pa = np.pad(al, 1); e = np.zeros_like(pa)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(pa, dy, 0), dx, 1)
        e = (e & ~pa)[1:-1, 1:-1]
        c.a[e, :3] = col('K', 1) if color != "white" else col('K', 2); c.a[e, 3] = 255
        al = al | e
    return c

SHAPES = ["eighth", "beamed", "quarter", "double"]
items = {}
for sh in SHAPES:
    for co in COL:
        c = paint(sh, co); items[(sh, co)] = c; Image.fromarray(c.a).save(os.path.join(OUT, f"note_{sh}_{co}.png"))
BG = (36, 40, 66, 255)
cell = 24
sheet = Image.new("RGBA", (cell * len(COL), cell * len(SHAPES)), BG)
for r, sh in enumerate(SHAPES):
    for k, co in enumerate(COL): sheet.alpha_composite(Image.fromarray(items[(sh, co)].a), (k * cell + 4, r * cell + 2))
sheet.resize((sheet.width * 8, sheet.height * 8), Image.NEAREST).convert("RGB").save(os.path.join(OUT, "notes_sheet.png"))

# 高解像度版（2倍・3倍）
for kk in (2, 3):
    HR = os.path.join(OUT, f"x{kk}"); os.makedirs(HR, exist_ok=True)
    cs = int(24 * kk); sh_ = Image.new("RGBA", (cs * len(COL), cs * len(SHAPES)), BG)
    for r, shp in enumerate(SHAPES):
        for q, co in enumerate(COL):
            cc = paint(shp, co, kk); Image.fromarray(cc.a).save(os.path.join(HR, f"note_{shp}_{co}.png"))
            sh_.alpha_composite(Image.fromarray(cc.a), (q * cs + 4 * kk, r * cs + 2 * kk))
    sh_.resize((sh_.width * (8 // kk if kk <= 4 else 2), sh_.height * (8 // kk if kk <= 4 else 2)), Image.NEAREST).convert("RGB").save(os.path.join(OUT, f"notes_sheet_x{kk}.png"))
# ふわっと上がるアニメ：ちびキャラの頭のうえから、3つの音符が順番に上がる（音符は半分の大きさ）
import gen_blonde_chibi as CH
ALLC = np.array([pal[f][k] for f in pal for k in range(8)], float)
def halve(a):
    h, w = a.shape[0] // 2, a.shape[1] // 2; o = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            blk = a[y * 2:y * 2 + 2, x * 2:x * 2 + 2].reshape(-1, 4).astype(float); m = blk[:, 3] > 0
            if m.sum() < 2: continue
            c = blk[m, :3].mean(0); j = ((ALLC - c) ** 2).sum(1).argmin(); o[y, x, :3] = ALLC[j]; o[y, x, 3] = 255
    return o
SM = {key: paint(key[0], key[1], .6).a for key in items}
NF = 24; CW, CH_ = 56, 84
chib = Image.fromarray(CH.front(0).a)
def frame(i):
    im = Image.new("RGBA", (CW, CH_), BG)
    im.alpha_composite(chib, ((CW - 24) // 2, CH_ - 36 - 4))
    for k, (sh, co, x0, delay) in enumerate((("eighth", "white", 6, 0), ("beamed", "pink", 36, 7), ("double", "gold", 22, 14))):
        age = i - delay
        if age < 0: continue
        T = age / 14.0
        if T > 1: continue
        y = 40 - 36 * T; x = x0 + math.sin(T * math.tau * 1.3 + k) * 3.0
        a = SM[(sh, co)].copy()
        if T > .65:
            keep = BAY[np.arange(a.shape[0])[:, None] % 4, np.arange(a.shape[1])[None, :] % 4] < (1 - T) / .35
            a[..., 3] = np.where(keep, a[..., 3], 0)
        im.alpha_composite(Image.fromarray(a), (int(round(x)), int(round(y))))
    return im
g = [frame(i).resize((CW * 8, CH_ * 8), Image.NEAREST).convert("RGB") for i in range(NF)]
g[0].save(os.path.join(OUT, "notes_float.gif"), save_all=True, append_images=g[1:], duration=90, loop=0)
g[12].save(os.path.join(OUT, "notes_float_frame.png")); print("ok")
