"""
パーツで作る：服・スカート・かばん・足・靴を別々に作って、頭と組み合わせる。
全部おなじ座標（26×64の枠）で描くので、重ねるだけでつながる。
python gen_body.py → sprites/part_*.pxl/.png（パーツ）、sprites/girl_parts.pxl/.png/_big.png（組み合わせ）、ref/compare_full.png
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 26, 64
yy, xx = np.mgrid[0:H, 0:W]
TX = lambda x: 12.5 + (x - 16) * 0.8          # 体は参考のように、頭のうしろ寄りで、すこし細くする
def poly(pts):
    pts = [(TX(a), b) for a, b in pts]
    px, py = xx + .5, yy + .5; ins = np.zeros((H, W), bool); j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        ins ^= ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi); j = i
    return ins
class Part:
    def __init__(self, name): self.name = name; self.code = np.full((H, W), "..", dtype="<U2")
    def paint(self, mask, fam, base, hi=1, lo=1, keep=None):
        up = mask & ~np.roll(mask, 1, 0); lf = mask & ~np.roll(mask, 1, 1); dn = mask & ~np.roll(mask, -1, 0); rt = mask & ~np.roll(mask, -1, 1)
        for y, x in zip(*np.nonzero(mask)):
            s = base + (hi if (up[y, x] or lf[y, x]) else 0) - (lo if (dn[y, x] or rt[y, x]) else 0)
            self.code[y, x] = f"{fam}{max(0, min(7, s))}"
    def dot(self, x, y, t):
        x = int(round(TX(x)))
        if 0 <= x < W and 0 <= y < H: self.code[y, x] = t
    def line(self, x0, y0, x1, y1, t, only=None):
        x0, x1 = TX(x0), TX(x1)
        n = int(max(abs(x1 - x0), abs(y1 - y0)))
        for k in range(n + 1):
            x = int(round(x0 + (x1 - x0) * k / max(1, n))); y = int(round(y0 + (y1 - y0) * k / max(1, n)))
            if 0 <= x < W and 0 <= y < H and self.code[y, x] != ".." and (only is None or self.code[y, x][0] == only): self.code[y, x] = t

parts = []
# ---- かばん（腰のうしろ）と薬草
bag = Part("bag"); parts.append(bag)
bag.paint(poly([(3, 33), (10.5, 33), (10.5, 44), (3, 44)]), 'J', 3, 1, 1)
bag.paint(poly([(3, 33), (10.5, 33), (10.5, 37), (3, 37)]), 'J', 4, 1, 1)
bag.paint(poly([(3.5, 44), (10, 44), (9, 46), (4.5, 46)]), 'J', 2, 0, 1)
for (x, y) in ((6, 38), (7, 38)): bag.dot(x, y, "B6")
bag.dot(6, 39, "B4"); bag.dot(7, 39, "B4")
for (x, y, t) in ((4, 32, "E4"), (5, 31, "E4"), (5, 30, "E3"), (6, 29, "E4"), (8, 32, "E3"), (8, 31, "E4"), (9, 30, "E4"), (7, 32, "E5"),
                  (5, 28, "H5"), (6, 27, "H4"), (5, 27, "H6"), (9, 29, "H5"), (10, 28, "H4"), (9, 28, "H6")): bag.dot(x, y, t)
# ---- 後ろの足・前の足
legs = Part("legs"); parts.append(legs)
legs.paint(poly([(11, 47), (15.5, 47), (13, 57.5), (9.5, 57.5)]), 'R', 1, 1, 0)
legs.paint(poly([(16, 47), (20.5, 47), (22.5, 57.5), (19, 57.5)]), 'R', 3, 1, 1)
legs.line(18, 49, 20, 56, "R2", 'R')
# ---- 靴
boots = Part("boots"); parts.append(boots)
boots.paint(poly([(7, 56), (13.5, 56), (14.5, 61.5), (5.5, 62), (5.5, 59)]), 'D', 2, 1, 1)
boots.paint(poly([(17, 56), (23, 56), (24, 59.5), (26, 61), (25.5, 62.5), (17, 62.5)]), 'D', 3, 1, 1)
boots.paint(poly([(17.5, 56), (22.5, 56), (22.5, 58), (17.5, 58)]), 'D', 5, 0, 0)     # 折り返し
boots.paint(poly([(5, 61.3), (14.5, 61.3), (14.5, 62.5), (5, 62.8)]), 'D', 0, 0, 0); boots.paint(poly([(17, 61.3), (25.8, 61.3), (25.5, 62.5), (17, 62.5)]), 'D', 0, 0, 0)
boots.dot(20, 59, "B6"); boots.dot(21, 59, "B4"); boots.dot(9, 58, "B4")
# ---- スカート（ひだ）
skirt = Part("skirt"); parts.append(skirt)
skirt.paint(poly([(9.5, 33), (22.5, 33), (27.5, 46), (4.5, 47.5)]), 'b', 4, 1, 1)
for (x0, y0, x1, y1, t) in ((12, 35, 9.5, 46, "b2"), (15, 35, 14.5, 47, "b2"), (18, 35, 20.5, 46.5, "b2"), (21, 35, 25.5, 46, "b1")): skirt.line(x0, y0, x1, y1, t, 'b')
for (x0, y0, x1, y1) in ((13, 35, 11.5, 45), (16.5, 35, 17.5, 46), (19.5, 35, 23, 45)): skirt.line(x0, y0, x1, y1, "b6", 'b')
skirt.paint(poly([(4.5, 45), (27.4, 44), (27.6, 47), (4.5, 48)]), 'L', 5, 1, 1)                    # すその白いふち
for x in (8, 12, 16, 20, 24): skirt.dot(x, 46, "L3")
# ---- 胴（チュニック）と白いえり
torso = Part("torso"); parts.append(torso)
torso.paint(poly([(10, 21), (22, 21), (22.8, 34), (9.6, 34.5)]), 'b', 4, 1, 1)
torso.paint(poly([(10, 21), (13.5, 21), (13, 34.5), (9.6, 34.5)]), 'b', 2, 0, 1)                    # うしろがわは暗い
torso.paint(poly([(15.5, 21), (21.5, 21), (19.5, 27), (17.5, 27)]), 'L', 5, 1, 1)                    # えり
torso.line(14, 25, 13, 33, "b2", 'b'); torso.line(14.5, 23, 15, 27, "b6", 'b')
torso.paint(poly([(9.6, 31.5), (22.8, 31), (22.9, 34.5), (9.6, 35)]), 'J', 3, 1, 1)                 # ベルト
torso.dot(18, 32, "B6"); torso.dot(19, 32, "B6"); torso.dot(18, 33, "B4"); torso.dot(19, 33, "B4")
# ---- かばんのひも
strap = Part("strap"); parts.append(strap)
strap.line(19, 21, 11, 33, "J3"); strap.line(20, 21, 12, 33, "J2"); strap.line(18, 21, 10, 33, "J4")
# ---- スカーフ
scarf = Part("scarf"); parts.append(scarf)
scarf.paint(poly([(11, 18), (21.5, 18), (22.5, 22.5), (12, 23.5)]), 'c', 4, 1, 1)
scarf.paint(poly([(10.5, 20), (13.5, 20), (12, 31), (8, 29)]), 'c', 3, 1, 1)
scarf.line(12, 21, 21, 21, "c2"); scarf.line(11, 24, 9, 29, "c2")
for (x, y) in ((13, 19), (14, 19), (15, 19)): scarf.dot(x, y, "c6")
# ---- 前の腕と手
arm = Part("arm"); parts.append(arm)
arm.paint(poly([(16.5, 22), (21, 22), (23.3, 28.5), (20, 30)]), 'b', 5, 1, 1)
arm.paint(poly([(19.5, 28), (23.5, 28.5), (21.5, 33.5), (17.5, 33)]), 'b', 5, 1, 1)
arm.paint(poly([(17.8, 31.5), (21.8, 32.2), (21.6, 34), (17.6, 33.4)]), 'L', 5, 1, 1)                # そでぐち
arm.paint(poly([(17.5, 33.3), (21.5, 33.8), (21.2, 36.5), (17.6, 36)]), 'V', 4, 1, 1)                # 手
arm.line(21, 24, 22, 29, "b2", 'b'); arm.line(19, 29, 20, 31, "b2", 'b'); arm.dot(18, 25, "b6"); arm.dot(19, 26, "b6")
# ---- 頭
head = Part("head"); hc = pxl.build(os.path.join(HERE, "sprites", "part_head.pxl"))[0]
for y in range(hc.shape[0]):
    for x in range(hc.shape[1]):
        if hc[y, x] != "..": head.code[y, x] = hc[y, x]
parts.append(head)

def save(part, name, outline=True):
    code = part.code.copy()
    if outline:
        m = code != ".."; e = np.zeros_like(m)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(m, dy, 0), dx, 1)
        for y, x in zip(*np.nonzero(e & ~m)): code[y, x] = "U1"
    p = os.path.join(HERE, "sprites", name + ".pxl")
    with open(p, "w") as f:
        f.write(f"# {name}（{W}×{H}の枠のなかの位置は全パーツ共通）\n@size {W} {H}\n")
        for r in code: f.write(" ".join(r) + "\n")
    c, img, _ = pxl.build(p); Image.fromarray(img).save(p.replace(".pxl", ".png")); return img
for pt in parts:
    save(pt, "part_" + pt.name if pt.name != "head" else "part_head_in_frame")
# ---- 組み合わせ（うしろ→まえ）
order = ["bag", "legs", "boots", "skirt", "torso", "strap", "arm", "scarf", "head"]
full = Part("full")
for n in order:
    pt = next(p for p in parts if p.name == n)
    m = pt.code != ".."
    # 部品どうしのさかいに暗い線（ふちの内側から1ドット）を入れる：すでに前にあるパーツのうえに重なる所
    if n not in ("bag", "legs"):
        e = np.zeros_like(m)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(m, dy, 0), dx, 1)
        edge = e & ~m & (full.code != "..")
        for y, x in zip(*np.nonzero(edge)): full.code[y, x] = "U2" if n in ("arm", "skirt", "scarf", "torso") else full.code[y, x]
    full.code[m] = pt.code[m]
img = save(full, "girl_parts")
k = 10
def up(arr):
    im = Image.fromarray(arr); bg = Image.new("RGBA", (im.width * k, im.height * k), (236, 234, 225, 255)); bg.alpha_composite(im.resize((im.width * k, im.height * k), Image.NEAREST)); return bg.convert("RGB")
B_ = up(img); B_.save(os.path.join(HERE, "sprites", "girl_parts_big.png"))
ref = Image.open(os.path.join(HERE, "ref", "source_sheet.png")).convert("RGB").crop((140, 95, 275, 390)); k2 = B_.height / ref.height
A_ = ref.resize((int(ref.width * k2), B_.height), Image.NEAREST)
out = Image.new("RGB", (A_.width + B_.width + 30, B_.height), (236, 234, 225)); out.paste(A_, (0, 0)); out.paste(B_, (A_.width + 30, 0)); out.save(os.path.join(HERE, "ref", "compare_full.png")); print("ok")
