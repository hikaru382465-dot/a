"""
パーツ1（頭）の作り直し：髪を「毛束のかたまり」を重ねて作る（ヘルメットのような一枚の丸にしない）。
python gen_head2.py → sprites/part_head.pxl/.png/_big.png と、参考との比べ（ref/compare_head.png）
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 24, 20
code = np.full((H, W), "..", dtype="<U2")
yy, xx = np.mgrid[0:H, 0:W]
def poly(pts):
    px, py = xx + .5, yy + .5; ins = np.zeros((H, W), bool); j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        ins ^= ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi); j = i
    return ins
def paint(mask, fam, base, hi=1, lo=1, over=True):
    """上と左のふちを明るく、下と右のふちを暗く。mask の外には出さない"""
    up = mask & ~np.roll(mask, 1, 0); lf = mask & ~np.roll(mask, 1, 1)
    dn = mask & ~np.roll(mask, -1, 0); rt = mask & ~np.roll(mask, -1, 1)
    for y, x in zip(*np.nonzero(mask)):
        s = base + (hi if (up[y, x] or lf[y, x]) else 0) - (lo if (dn[y, x] or rt[y, x]) else 0)
        code[y, x] = f"{fam}{max(0, min(7, s))}"
def dot(x, y, t):
    if 0 <= x < W and 0 <= y < H: code[y, x] = t

# ---- 後ろの髪のかたまり（暗い）
paint(poly([(2, 8), (1, 12), (3, 16.5), (8, 18), (12, 16), (12.5, 9), (8, 3), (4, 5)]), 'a', 3, 0, 1)
# ---- 首
paint(poly([(12, 15), (17, 15), (17, 20), (12, 20)]), 'V', 3, 0, 0)
# ---- 顔（肌）：行ごとの（左, 右）。右がわの出っぱり＝おでこ・鼻・くちびる・あご
SPANS = {8: (17, 20), 9: (15, 20), 10: (13, 20), 11: (12, 21), 12: (12, 21), 13: (12, 20), 14: (13, 20), 15: (14, 19), 16: (15, 18), 17: (16, 17)}
fm = np.zeros((H, W), bool)
for y, (a_, b_) in SPANS.items(): fm[y, a_:b_ + 1] = True
paint(fm, 'V', 4, 1, 1)
# ---- 髪：頭の上のかたまり
paint(poly([(5, 2.5), (9, 0.8), (14, 0.8), (18, 3.5), (19.5, 7), (16, 7), (13, 5), (9, 6.5), (5, 9.5), (3, 6)]), 'a', 4, 1, 1)
# ---- 毛束（左上から右下へ流れる）
paint(poly([(4, 5), (8, 2.2), (12, 2.5), (10, 5.5), (6, 8.5), (3, 9)]), 'a', 5, 1, 1)
paint(poly([(9, 3.5), (14, 2), (17, 4.5), (15.5, 7.5), (11.5, 8.5), (9, 7)]), 'a', 5, 1, 1)
# ---- 前髪の毛先（顔にかかる、とがらせる）
paint(poly([(13.5, 6.5), (19, 5.5), (20.8, 8.2), (18.8, 9.2), (16, 8.7), (14, 9)]), 'a', 4, 1, 1)
paint(poly([(11, 8), (15.6, 8.2), (15.2, 12.2), (14, 14.2), (12, 12), (10.5, 10)]), 'a', 3, 1, 1)
# ---- 耳のうしろから下がる髪
paint(poly([(8, 11), (12, 10.5), (12.5, 17), (10, 18.5), (7, 16)]), 'a', 3, 1, 1)
# ---- 毛先のギザギザ（ふちに小さな束）
paint(poly([(1.5, 9), (-0.5, 11), (2, 11.2)]), 'a', 3, 0, 1)
paint(poly([(2, 14), (0.3, 16.5), (3.5, 16)]), 'a', 3, 0, 1)
paint(poly([(5, 17), (4, 19.6), (7.2, 18.2)]), 'a', 3, 0, 1)
paint(poly([(9, 17.5), (9.5, 20), (11.8, 18)]), 'a', 3, 0, 1)
paint(poly([(8.5, 1.5), (7, -0.2), (11, 0.5)]), 'a', 5, 1, 1)
paint(poly([(16, 2.5), (18.5, 1.2), (19, 4.2)]), 'a', 5, 1, 1)
paint(poly([(18.5, 6.5), (21.4, 6.8), (20.6, 8.6)]), 'a', 4, 1, 1)
paint(poly([(14, 8.5), (15.5, 11.5), (13.2, 10)]), 'a', 3, 1, 1)
# ---- 髪の毛束のすじ（暗い線）
for (x0, y0, x1, y1) in ((6, 4, 11, 8), (11, 3, 15, 7), (4, 10, 7, 15), (9, 11, 10, 16)):
    n = int(max(abs(x1 - x0), abs(y1 - y0)))
    for k in range(n + 1):
        x = int(round(x0 + (x1 - x0) * k / max(1, n))); y = int(round(y0 + (y1 - y0) * k / max(1, n)))
        if code[y, x][0] == 'a': code[y, x] = "a2"
for (x, y) in ((7, 3), (8, 3), (9, 3), (6, 4), (13, 3), (14, 3), (5, 6), (6, 6), (12, 4)): dot(x, y, "a7")      # つや
for (x, y) in ((8, 2), (10, 2), (7, 4), (15, 4)): dot(x, y, "a6")
# ---- 顔の前にもかかる髪（前髪がまゆにかぶさる／頬にたれる細い束／あごの横にたれる束）
paint(poly([(15, 8.2), (19.5, 8.6), (20.4, 10.4), (18.2, 9.9), (16.3, 10.4)]), 'a', 3, 1, 1)
for (x0, y0, x1, y1) in ((14, 10, 15, 15), (13, 11, 14, 16)):
    n = int(max(abs(x1 - x0), abs(y1 - y0)))
    for k in range(n + 1):
        x = int(round(x0 + (x1 - x0) * k / max(1, n))); y = int(round(y0 + (y1 - y0) * k / max(1, n)))
        code[y, x] = "a3" if k % 3 else "a2"
paint(poly([(19.4, 13), (21.2, 13.4), (20.6, 17.2), (19, 16.2)]), 'a', 3, 1, 1)
dot(20, 17, "a2"); dot(20, 16, "a2")
# ---- 顔のなか：まゆ・目・ほお・口
dot(16, 9, "a2")
for x in (15, 16, 17, 18): dot(x, 10, "U1")                      # まつ毛
dot(15, 11, "L7"); dot(16, 11, "b4"); dot(17, 11, "b3"); dot(18, 11, "b2")  # 白目と大きな黒目
dot(16, 12, "b2"); dot(17, 12, "b2"); dot(15, 12, "V1"); dot(18, 12, "V1")
dot(15, 13, "V2"); dot(16, 13, "V2"); dot(17, 16, "V6")           # ほお・あごのつや
dot(18, 14, "V0"); dot(19, 14, "V0")                              # 口
dot(21, 12, "V6"); dot(20, 13, "V1")                              # 鼻先のつや・鼻の下の影
dot(6, 6, "B6"); dot(6, 7, "B4")                                  # 髪どめ
# ---- 外側の輪郭
m = code != ".."; e = np.zeros_like(m)
for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(m, dy, 0), dx, 1)
for y, x in zip(*np.nonzero(e & ~m)): code[y, x] = "U1"
p = os.path.join(HERE, "sprites", "part_head.pxl")
with open(p, "w") as f:
    f.write(f"# 部品：頭（右向き3/4）。体につなぐ位置＝下の中央 x=16\n@size {W} {H}\n")
    for r in code: f.write(" ".join(r) + "\n")
c, img, pal = pxl.build(p); Image.fromarray(img).save(p.replace(".pxl", ".png"))
k = 16
def up(arr):
    im = Image.fromarray(arr); bg = Image.new("RGBA", (im.width * k, im.height * k), (236, 234, 225, 255)); bg.alpha_composite(im.resize((im.width * k, im.height * k), Image.NEAREST)); return bg.convert("RGB")
ref = np.asarray(Image.open(os.path.join(HERE, "ref", "girl_src01_traced.png")))[:20]
A_, B_ = up(ref), up(img)
out = Image.new("RGB", (A_.width + B_.width + 30, max(A_.height, B_.height)), (236, 234, 225)); out.paste(A_, (0, 0)); out.paste(B_, (A_.width + 30, 0))
out.save(os.path.join(HERE, "ref", "compare_head.png")); B_.save(p.replace(".pxl", "_big.png")); print("ok")
