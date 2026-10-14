"""
オリジナルのキャラ（横向き・右向き）：旅の薬草売りの少女。26×66ドット前後。
形を塗りつぶしの図形で置き、パレットの系統（明るさ段階）で色をつけ、ふちの明暗は自動でつける。
python gen_char.py → sprites/herbgirl.pxl / .png / _zoom.png
"""
import os, math
import numpy as np
from PIL import Image
import pxl

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 34, 70
code = np.full((H, W), "..", dtype="<U2"); owner = np.zeros((H, W), np.int16)
yy, xx = np.mgrid[0:H, 0:W]

def ell(cx, cy, rx, ry): return ((xx + .5 - cx) / rx) ** 2 + ((yy + .5 - cy) / ry) ** 2 <= 1
def poly(pts):
    m = np.zeros((H, W), bool); n = len(pts)
    px, py = xx + .5, yy + .5; inside = np.zeros((H, W), bool)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]; xj, yj = pts[j]
        c = ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi)
        inside ^= c; j = i
    return inside
def seg(x0, y0, x1, y1, w):
    d = np.abs((x1 - x0) * (y0 - (yy + .5)) - (x0 - (xx + .5)) * (y1 - y0)) / math.hypot(x1 - x0, y1 - y0)
    t = ((xx + .5 - x0) * (x1 - x0) + (yy + .5 - y0) * (y1 - y0)) / ((x1 - x0) ** 2 + (y1 - y0) ** 2)
    return (d <= w / 2) & (t >= -.05) & (t <= 1.05)

nid = [0]
def paint(mask, fam, base, shade=True, edge=None):
    """マスクを塗る。左上のふちは1段明るく、右下のふちは1段暗くして、立体にする"""
    nid[0] += 1; mask = mask.copy()
    up = np.roll(mask, 1, 0) & np.roll(mask, 1, 1); hi = mask & ~np.roll(mask, 1, 0)      # 上が空いている＝明るいふち
    lo = mask & ~np.roll(mask, -1, 0); rt = mask & ~np.roll(mask, -1, 1)
    for y, x in zip(*np.nonzero(mask)):
        s = base
        if shade:
            if hi[y, x] or (x > 0 and not mask[y, x - 1]): s += 1
            if lo[y, x] or rt[y, x]: s -= 1
        code[y, x] = f"{fam}{max(0, min(7, s))}"; owner[y, x] = nid[0]
    if edge:                                       # 部品のふち（となりの部品との境目）に暗い線
        e = mask & ~(np.roll(mask, -1, 0) & np.roll(mask, 1, 0) & np.roll(mask, -1, 1) & np.roll(mask, 1, 1))
        for y, x in zip(*np.nonzero(e)):
            if code[y, x] != "..": code[y, x] = edge
def dot(x, y, t):
    if 0 <= x < W and 0 <= y < H: code[y, x] = t

# ---- 後ろ髪（ポニーテール）と後ろ側のもの
paint(poly([(9, 9), (6, 14), (4, 22), (3, 32), (6, 36), (9, 34), (9, 26), (11, 18)]), 'a', 3)
paint(seg(8, 16, 4, 31, 4), 'a', 2, shade=False)
# ---- 後ろの足と靴
paint(poly([(13, 53), (18, 53), (17, 64), (12, 64)]), 'J', 2)
paint(poly([(10, 63), (18, 63), (19, 67), (9, 67)]), 'R', 2)
# ---- 前の足と靴
paint(poly([(18, 53), (23, 53), (24, 64), (19, 64)]), 'J', 3)
paint(poly([(18, 63), (26, 62), (28, 66), (18, 67)]), 'R', 4)
# ---- スカートの形のチュニック
paint(poly([(11, 38), (23, 38), (28, 53), (8, 54)]), 'b', 4)
paint(poly([(8, 51), (28, 50), (28, 54), (8, 55)]), 'L', 5, shade=False)          # すその白いふち
# ---- 胴
paint(poly([(12, 26), (22, 26), (24, 38), (11, 39)]), 'b', 4)
paint(poly([(11, 37), (24, 36), (24, 40), (11, 41)]), 'J', 3)                    # ベルト
dot(23, 38, "B6"); dot(23, 39, "B6")
# ---- かばんとひも
paint(seg(19, 26, 11, 40, 2), 'J', 3, shade=False)
paint(poly([(6, 40), (15, 40), (15, 49), (6, 49)]), 'J', 3, edge="U1")
paint(poly([(6, 40), (15, 40), (15, 43), (6, 43)]), 'J', 4); dot(11, 44, "B6"); dot(11, 45, "B5")
# ---- スカーフ
paint(poly([(12, 22), (22, 22), (23, 27), (12, 28)]), 'c', 4)
paint(poly([(10, 26), (13, 26), (11, 36), (8, 35)]), 'c', 3)                     # 後ろにたれる端
# ---- 首と顔
paint(poly([(15, 19), (21, 19), (21, 24), (15, 24)]), 'V', 3, shade=False)
paint(ell(18.5, 14.5, 7.6, 8.6), 'V', 4)
paint(poly([(17, 9), (24, 12), (25, 17), (24, 20), (22, 22), (17, 22)]), 'V', 4, shade=False)
dot(25, 16, "V3"); dot(25, 17, "V2")                                             # 鼻
# ---- 前の腕と手（スカーフの前）
paint(seg(17, 28, 22, 38, 4.6), 'b', 3)
paint(poly([(19, 35), (24, 37), (24, 39), (19, 38)]), 'L', 5, shade=False)
paint(poly([(20, 38), (24, 39), (24, 45), (20, 44)]), 'V', 4)
# ---- 髪（頭の上と前髪、耳の後ろ）
paint(ell(16, 9.5, 9.4, 8.6) & ~poly([(19, 13), (30, 13), (30, 24), (19, 24)]) & ~ell(22.5, 17.5, 4.5, 6.5), 'a', 3)
paint(poly([(15, 3), (24, 6), (26, 12), (22, 12), (19, 9), (13, 9)]), 'a', 4)
paint(poly([(12, 10), (18, 11), (14, 16), (10, 17)]), 'a', 2, shade=False)
# ---- 顔のなか
dot(22, 15, "U2"); dot(22, 14, "U2"); dot(23, 14, "U2"); dot(23, 15, "U2"); dot(22, 14, "V7"); dot(23, 12, "a2"); dot(22, 12, "a2"); dot(21, 12, "a2")
dot(22, 19, "V2"); dot(23, 19, "V2"); dot(20, 17, "H3"); dot(21, 17, "H3")                                         # 口・ほお
# ---- 髪のひも
dot(8, 14, "B5"); dot(7, 14, "B4"); dot(8, 15, "B3")

# ---- ふち（まわりの輪郭）
m = code != ".."; edge = np.zeros_like(m)
for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): edge |= np.roll(np.roll(m, dy, 0), dx, 1)
for y, x in zip(*np.nonzero(edge & ~m)): code[y, x] = "U1"
ys, xs = np.nonzero(code != ".."); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
code = code[max(0, y0 - 1):y1 + 2, max(0, x0 - 1):x1 + 2]
p = os.path.join(HERE, "sprites", "herbgirl.pxl")
with open(p, "w") as f:
    f.write(f"# 旅の薬草売りの少女（オリジナル・横向き）\n@size {code.shape[1]} {code.shape[0]}\n")
    for r in code: f.write(" ".join(r) + "\n")
c, img, pal = pxl.build(p); Image.fromarray(img).save(p.replace(".pxl", ".png"))
k = 10; big = Image.fromarray(img).resize((img.shape[1] * k, img.shape[0] * k), Image.NEAREST)
bg = Image.new("RGBA", big.size, (236, 234, 225, 255)); bg.alpha_composite(big); bg.convert("RGB").save(p.replace(".pxl", "_big.png"))
print(code.shape)
