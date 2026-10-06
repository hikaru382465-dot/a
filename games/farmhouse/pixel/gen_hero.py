"""
ゲーム用キャラ（旅の薬草売りの少女、右向き）。
きまり：1m=30ドット（家の絵と同じ）、身長1.6m≒48ドット、1コマ 30×52ドット、基準点＝足もとの下の中央、左向きは反転して使う。
歩きは4コマ（足を開く→そろえて片足を上げる→反対に開く→反対を上げる）。
python gen_hero.py → sprites/hero_walk{0-3}.pxl/.png, assets/character/hero_sheet.png, hero_walk.gif, hero_preview.png
"""
import os, math
import numpy as np
from PIL import Image
import pxl

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 30, 52
F = 0.70                                  # 設計図(69ドットの高さ)を、ゲーム用の大きさに縮める倍率
BASE_Y = 50                               # 足もとの線（ここが地面）
yy, xx = np.mgrid[0:H, 0:W]
code = owner = None

def reset():
    global code, owner
    code = np.full((H, W), "..", dtype="<U2"); owner = np.zeros((H, W), np.int16)
OX, OY = 4.0, 1.0                          # 設計図の原点を、1コマのどこに置くか（左右・上）
def X(x): return OX + x * F
def Y(y): return OY + y * F
def ell(cx, cy, rx, ry): return ((xx + .5 - X(cx)) / (rx * F)) ** 2 + ((yy + .5 - Y(cy)) / (ry * F)) ** 2 <= 1
def poly(pts):
    px, py = xx + .5, yy + .5; inside = np.zeros((H, W), bool); P = [(X(a), Y(b)) for a, b in pts]; j = len(P) - 1
    for i in range(len(P)):
        xi, yi = P[i]; xj, yj = P[j]
        inside ^= ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi); j = i
    return inside
def seg(x0, y0, x1, y1, w):
    x0, y0, x1, y1, w = X(x0), Y(y0), X(x1), Y(y1), w * F
    d = np.abs((x1 - x0) * (y0 - (yy + .5)) - (x0 - (xx + .5)) * (y1 - y0)) / math.hypot(x1 - x0, y1 - y0)
    t = ((xx + .5 - x0) * (x1 - x0) + (yy + .5 - y0) * (y1 - y0)) / ((x1 - x0) ** 2 + (y1 - y0) ** 2)
    return (d <= w / 2) & (t >= -.05) & (t <= 1.05)
nid = [0]
def paint(mask, fam, base, shade=True):
    nid[0] += 1
    hi = mask & ~np.roll(mask, 1, 0); lo = mask & ~np.roll(mask, -1, 0); rt = mask & ~np.roll(mask, -1, 1); lf = mask & ~np.roll(mask, 1, 1)
    for y, x in zip(*np.nonzero(mask)):
        s = base
        if shade:
            if hi[y, x] or lf[y, x]: s += 1
            if lo[y, x] or rt[y, x]: s -= 1
        code[y, x] = f"{fam}{max(0, min(7, s))}"; owner[y, x] = nid[0]
def dot(x, y, t):
    x, y = int(round(X(x))), int(round(Y(y)))
    if 0 <= x < W and 0 <= y < H: code[y, x] = t

def frame(step):
    reset()
    bob = [1.6, 0, 1.6, 0][step]                                  # 足を開く時は体が低い
    far = [-4, 0, 4, 0][step] ; near = [4, 1, -4, 0][step]
    lf_far = 4 if step == 3 else 0; lf_near = 4 if step == 1 else 0
    arm = [-2, 0, 2, 0][step]
    # 足は地面（BASE_Y）にそろえる。設計図では y=67 が足の底
    def leg(dx, lift, fam_leg, base_leg, fam_boot, base_boot):
        top = 53 + bob
        paint(poly([(13 + dx * .3, top), (18 + dx * .3, top), (17 + dx, 64 - lift), (12 + dx, 64 - lift)]), fam_leg, base_leg)
        paint(poly([(10 + dx, 63 - lift), (18 + dx, 63 - lift), (19 + dx, 67 - lift), (9 + dx, 67 - lift)]), fam_boot, base_boot)
    # 後ろ髪・後ろ足
    paint(poly([(9, 9 + bob), (6, 14 + bob), (4, 22 + bob), (3, 32 + bob), (6, 36 + bob), (9, 34 + bob), (9, 26 + bob), (11, 18 + bob)]), 'a', 3)
    leg(far, lf_far, 'J', 2, 'R', 2)
    leg(near, lf_near, 'J', 3, 'R', 4)
    # チュニック（スカート）・すそ・胴・ベルト
    b = bob
    paint(poly([(11, 38 + b), (23, 38 + b), (28, 53 + b), (8, 54 + b)]), 'b', 4)
    paint(poly([(8, 51 + b), (28, 50 + b), (28, 54 + b), (8, 55 + b)]), 'L', 5, shade=False)
    paint(poly([(12, 26 + b), (22, 26 + b), (24, 38 + b), (11, 39 + b)]), 'b', 4)
    paint(poly([(11, 37 + b), (24, 36 + b), (24, 40 + b), (11, 41 + b)]), 'J', 3)
    dot(23, 38 + b, "B6")
    # かばん・ひも
    paint(seg(19, 26 + b, 11, 40 + b, 2.2), 'J', 3, shade=False)
    paint(poly([(6, 40 + b), (15, 40 + b), (15, 49 + b), (6, 49 + b)]), 'J', 3)
    paint(poly([(6, 40 + b), (15, 40 + b), (15, 43 + b), (6, 43 + b)]), 'J', 4); dot(11, 45 + b, "B6")
    # スカーフ
    paint(poly([(12, 22 + b), (22, 22 + b), (23, 27 + b), (12, 28 + b)]), 'c', 4)
    paint(poly([(10, 26 + b), (13, 26 + b), (11, 36 + b + (arm > 0)), (8, 35 + b)]), 'c', 3)
    # 首・顔
    paint(poly([(15, 19 + b), (21, 19 + b), (21, 24 + b), (15, 24 + b)]), 'V', 3, shade=False)
    paint(ell(18.5, 14.5 + b, 7.6, 8.6), 'V', 4)
    paint(poly([(17, 9 + b), (24, 12 + b), (25, 17 + b), (24, 20 + b), (22, 22 + b), (17, 22 + b)]), 'V', 4, shade=False)
    # 腕（ふり）
    paint(seg(17, 28 + b, 22 + arm, 38 + b, 4.6), 'b', 3)
    paint(poly([(19 + arm, 36 + b), (24 + arm, 38 + b), (24 + arm, 40 + b), (19 + arm, 39 + b)]), 'L', 5, shade=False)
    paint(poly([(20 + arm, 39 + b), (24 + arm, 40 + b), (24 + arm, 45 + b), (20 + arm, 44 + b)]), 'V', 4)
    # 髪
    paint(ell(16, 9.5 + b, 9.4, 8.6) & ~poly([(19, 13 + b), (30, 13 + b), (30, 24 + b), (19, 24 + b)]) & ~ell(22.5, 17.5 + b, 4.5, 6.5), 'a', 3)
    paint(poly([(15, 3 + b), (24, 6 + b), (26, 12 + b), (22, 12 + b), (19, 9 + b), (13, 9 + b)]), 'a', 4)
    paint(poly([(12, 10 + b), (18, 11 + b), (14, 16 + b), (10, 17 + b)]), 'a', 2, shade=False)
    # 顔のなか
    dot(22, 15 + b, "U2"); dot(22, 14 + b, "U2"); dot(23, 14.5 + b, "U2"); dot(21, 12 + b, "a2"); dot(22.5, 12 + b, "a2")
    dot(22.5, 19 + b, "V2"); dot(20, 17 + b, "H3"); dot(25, 16.5 + b, "V3")
    dot(8, 14 + b, "B5")
    # 輪郭
    m = code != ".."; e = np.zeros_like(m)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(m, dy, 0), dx, 1)
    for y, x in zip(*np.nonzero(e & ~m)): code[y, x] = "U1"
    # 足もとを地面の線（BASE_Y）にそろえる
    ys = np.nonzero((code != "..").any(1))[0]; shift = BASE_Y - ys.max()
    code2 = np.full_like(code, ".."); 
    for y in range(H):
        if 0 <= y + shift < H: code2[y + shift] = code[y]
    return code2

import sys
out = os.path.join(HERE, "..", "assets", "character"); os.makedirs(out, exist_ok=True)
sheet = np.zeros((H, W * 4, 4), np.uint8)
for s in range(4):
    c = frame(s); p = os.path.join(HERE, "sprites", f"hero_walk{s}.pxl")
    with open(p, "w") as f:
        f.write(f"# ゲーム用キャラ 歩き{s}（1コマ {W}×{H}、基準点=下の中央）\n@size {W} {H}\n")
        for r in c: f.write(" ".join(r) + "\n")
    _, img, _ = pxl.build(p); Image.fromarray(img).save(p.replace(".pxl", ".png")); sheet[:, s * W:(s + 1) * W] = img
Image.fromarray(sheet).save(os.path.join(out, "hero_sheet.png"))
k = 10; frames = []
for s in range(4):
    im = Image.fromarray(sheet[:, s * W:(s + 1) * W]).resize((W * k, H * k), Image.NEAREST)
    bg = Image.new("RGBA", im.size, (236, 234, 225, 255)); bg.alpha_composite(im); frames.append(bg)
frames[0].convert("P").save(os.path.join(out, "hero_walk.gif"), save_all=True, append_images=[f.convert("P") for f in frames[1:]], duration=140, loop=0)
prev = Image.new("RGB", (W * k * 4 + 30, H * k), (236, 234, 225))
for s, f in enumerate(frames): prev.paste(f.convert("RGB"), (s * (W * k + 10), 0))
prev.save(os.path.join(out, "hero_preview.png")); print("done", W, H)
