"""
サブマシンガン（ゲーム用の絵・横向き・右向き）100×60ドット。金属＝青灰(S)・鉄(I)、ポリマー＝黒(T)。
形は図形で置き、左上から光（上とひだりのふちが明るい）。滑り止め・通気穴・マガジンのリブは1ドットずつ。
python gen_smg.py → sprites/smg.pxl/.png/_big.png
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 104, 62
yy, xx = np.mgrid[0:H, 0:W]
code = np.full((H, W), "..", dtype="<U2")
def poly(pts):
    px, py = xx + .5, yy + .5; ins = np.zeros((H, W), bool); j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        ins ^= ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi); j = i
    return ins
def bone(a, b, r0, r1=None):
    r1 = r0 if r1 is None else r1; ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    t = np.clip(((xx + .5 - ax) * dx + (yy + .5 - ay) * dy) / L2, 0, 1)
    return np.hypot(xx + .5 - (ax + t * dx), yy + .5 - (ay + t * dy)) <= (r0 + (r1 - r0) * t)
def paint(mask, fam, base, hi=1, lo=1):
    up = mask & ~np.roll(mask, 1, 0); lf = mask & ~np.roll(mask, 1, 1); dn = mask & ~np.roll(mask, -1, 0); rt = mask & ~np.roll(mask, -1, 1)
    for y, x in zip(*np.nonzero(mask)):
        s = base + (hi if (up[y, x] or lf[y, x]) else 0) - (lo if (dn[y, x] or rt[y, x]) else 0)
        code[y, x] = f"{fam}{max(0, min(7, s))}"
def dot(x, y, t):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H: code[y, x] = t
def hline(x0, x1, y, t, only=None):
    for x in range(int(x0), int(x1) + 1):
        if 0 <= x < W and 0 <= y < H and code[y, x] != ".." and (only is None or code[y, x][0] == only): code[y, x] = t
def line(a, b, t, only=None):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
    for k in range(n + 1):
        x = int(round(a[0] + (b[0] - a[0]) * k / max(1, n))); y = int(round(a[1] + (b[1] - a[1]) * k / max(1, n)))
        if 0 <= x < W and 0 <= y < H and code[y, x] != ".." and (only is None or code[y, x][0] == only): code[y, x] = t

# ---- ストック（骨組みタイプ）
paint(bone((34, 24), (8, 26), 1.6), 'T', 3); paint(bone((34, 33), (10, 41), 1.6), 'T', 3)
paint(poly([(4, 23), (9, 22), (11, 44), (6, 45)]), 'T', 3, 1, 1)                                # 肩あて
for y in range(25, 43, 3): dot(7, y, "T5"); dot(8, y, "T4")
paint(bone((9, 27), (11, 41), 1.4), 'T', 2)
# ---- 手前に見えない側（うしろ）のマガジン
paint(poly([(60, 32), (71, 32), (74, 47), (70, 59), (60, 59), (62, 46)]), 'S', 2, 1, 1)
for y in range(36, 58, 4): hline(62, 72, y, "S1", 'S')
for y in range(34, 58, 4): hline(63, 71, y, "S4", 'S')
paint(poly([(59, 57), (71, 57), (71, 60.5), (59, 60.5)]), 'T', 3, 1, 1)
# ---- グリップ（斜め）：滑り止めの格子
paint(poly([(42, 32), (53, 32), (50, 54), (40, 54)]), 'T', 3, 1, 1)
for y in range(35, 52):
    for x in range(41, 52):
        if code[y, x][0] == 'T' and (x + y) % 4 == 0 and (x - y) % 4 != 1: code[y, x] = "T4"
paint(poly([(40, 52), (50, 52), (50, 55), (39.6, 55)]), 'T', 2, 0, 1)
# ---- トリガーガード・トリガー
paint(bone((55, 32), (56, 39), 1.1), 'S', 3); paint(bone((56, 39), (47, 39), 1.1), 'S', 3); paint(bone((47, 39), (47, 33), 1.0), 'S', 3)
paint(bone((51, 33), (52, 37), .9), 'I', 5)
# ---- レシーバー（本体）
paint(poly([(28, 18), (68, 18), (68, 33), (28, 33)]), 'S', 3, 1, 1)
paint(poly([(28, 18), (68, 18), (68, 23), (28, 23)]), 'S', 4, 1, 0)                              # 上のカバー
paint(poly([(28, 29), (68, 29), (68, 33), (28, 33)]), 'S', 2, 0, 1)                              # 下がわ（暗い）
hline(29, 67, 24, "S5", 'S'); hline(29, 67, 29, "S1", 'S')
# 排莢口・ボルトのみぞ
paint(poly([(51, 24.5), (62, 24.5), (62, 28), (51, 28)]), 'T', 0, 0, 0); hline(52, 61, 24, "S6"); dot(62, 26, "T1")
line((34, 26), (48, 26), "S1", 'S'); line((34, 27), (48, 27), "S5", 'S')
# 通気スリット（本体の左がわ）
for x in range(31, 47, 3): paint(poly([(x, 19.2), (x + 1.4, 19.2), (x + 1.4, 22), (x, 22)]), 'T', 1, 0, 0)
# ---- 上のレール（ギザギザ）
paint(poly([(30, 15), (66, 15), (66, 18), (30, 18)]), 'S', 5, 1, 1)
for x in range(31, 66, 3): paint(poly([(x, 15.4), (x + 1.2, 15.4), (x + 1.2, 17.6), (x, 17.6)]), 'S', 2, 0, 0)
# ---- サイト（照準）
paint(poly([(31, 10), (36, 10), (36, 15), (31, 15)]), 'S', 3, 1, 1); paint(poly([(32.5, 10), (34.5, 10), (34.5, 12), (32.5, 12)]), 'T', 0, 0, 0)
paint(poly([(87, 12), (91, 12), (91, 19.5), (87, 19.5)]), 'S', 3, 1, 1); paint(poly([(88.6, 12), (90, 12), (90, 14), (88.6, 14)]), 'T', 0, 0, 0); dot(87, 12, "S6")
# ---- ハンドガード（バレルシュラウド）・通気穴
paint(poly([(68, 19), (91, 19), (91, 31), (68, 31)]), 'S', 3, 1, 1)
paint(poly([(68, 19), (91, 19), (91, 22), (68, 22)]), 'S', 4, 1, 0)
for x in range(71, 90, 4):
    for y in (23, 26.5): paint(poly([(x, y), (x + 2, y), (x + 2, y + 2), (x, y + 2)]), 'T', 0, 0, 0)
hline(68, 91, 30, "S1", 'S')
# ---- バレル・マズルデバイス
paint(poly([(91, 22), (98, 22), (98, 28), (91, 28)]), 'I', 3, 1, 1)
paint(poly([(96, 20), (104, 20), (104, 30), (96, 30)]), 'T', 3, 1, 1)
for x in (98, 100, 102): paint(poly([(x, 21), (x + .9, 21), (x + .9, 29), (x, 29)]), 'T', 1, 0, 0)
dot(103, 25, "T0")
# ---- 装てんハンドル・ねじ・ボルト
paint(poly([(46, 12), (51, 12), (51, 15), (46, 15)]), 'I', 4, 1, 1); dot(47, 12, "I6")
for (x, y) in ((30, 20), (30, 31), (66, 20), (66, 31), (60, 21)): dot(x, y, "I6"); dot(x + 1, y + 1, "S1")
# ---- シリアル刻印（小さな文字風の点）
for x in range(36, 46, 2): dot(x, 31, "S1")
# ---- 外側の輪郭
m = code != ".."; e = np.zeros_like(m)
for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(m, dy, 0), dx, 1)
for y, x in zip(*np.nonzero(e & ~m)): code[y, x] = "T0"
ys, xs = np.nonzero(code != ".."); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
code = code[max(0, y0 - 1):y1 + 2, max(0, x0 - 1):x1 + 2]
p = os.path.join(HERE, "sprites", "smg.pxl")
with open(p, "w") as f:
    f.write(f"# サブマシンガン（横向き）{code.shape[1]}×{code.shape[0]}\n@size {code.shape[1]} {code.shape[0]}\n")
    for r in code: f.write(" ".join(r) + "\n")
c, img, _ = pxl.build(p); Image.fromarray(img).save(p.replace(".pxl", ".png"))
k = 8; big = Image.fromarray(img).resize((img.shape[1] * k, img.shape[0] * k), Image.NEAREST)
bg = Image.new("RGBA", big.size, (60, 66, 82, 255)); bg.alpha_composite(big); bg.convert("RGB").save(p.replace(".pxl", "_big.png")); print("ok", code.shape)
