"""
武闘家：見本（約65×77ドット）に合わせた大きさ 64×80 のシルエット3案。動きのある形（流れる髪・帯・ゆるいズボン）。
python gen_fighter_sketch64.py → assets/character/fighter_sketch64.png（塗りつぶし＋色つき）
P=正拳づき / K=とび蹴り / G=構え（半身）
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "character")
pal, _ = pxl.load_palette()
def c(f, s): return tuple(int(v) for v in pal[f][s]) + (255,)
W, H = 64, 80
SK, HAIR, GI, GI2, RED, RED2, SHOE = c('A', 4), c('a', 3), c('s', 6), c('s', 4), c('G', 4), c('G', 2), c('D', 3)
def new(): im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)
def limb(d, pts, w, fill):
    for a, b in zip(pts[:-1], pts[1:]): d.line([a, b], fill=fill, width=w)
    for p in pts: d.ellipse((p[0] - w / 2 + .5, p[1] - w / 2 + .5, p[0] + w / 2 - .5, p[1] + w / 2 - .5), fill=fill)
def head(d, x, y, face_dir=1):
    d.ellipse((x - 9, y - 9, x + 8, y + 8), fill=HAIR)
    d.ellipse((x - 6 + 2 * face_dir, y - 3, x + 6 + 2 * face_dir, y + 8), fill=SK)
    d.rectangle((x - 5 + 2 * face_dir, y - 4, x + 5 + 2 * face_dir, y - 1), fill=HAIR)
    d.rectangle((x + (1 if face_dir > 0 else -5), y + 1, x + (4 if face_dir > 0 else -2), y + 3), fill=c('G', 5))
def fist(d, p, r=4): d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=SK); d.ellipse((p[0] - r - 1, p[1] - 1, p[0] + 2, p[1] + 4), fill=RED)
def shoe(d, p, dirx=1): d.polygon([(p[0] - 4, p[1] - 2), (p[0] + 4 * dirx + 2 * dirx, p[1] - 1), (p[0] + 6 * dirx, p[1] + 3), (p[0] - 4, p[1] + 3)], fill=SHOE)

def P():
    im, d = new()
    d.polygon([(26, 10), (14, 6), (6, 12), (2, 24), (5, 38), (7, 22), (14, 14), (24, 14)], fill=c('a', 2))        # 流れるポニーテール
    limb(d, [(30, 46), (45, 55), (47, 70)], 9, GI); shoe(d, (48, 72)); limb(d, [(26, 46), (14, 58), (9, 71)], 9, GI2); shoe(d, (9, 73), -1)
    d.polygon([(22, 26), (38, 26), (36, 48), (24, 48)], fill=GI)                                   # 胴
    d.polygon([(24, 44), (36, 44), (36, 50), (24, 50)], fill=RED2)                                  # 帯
    d.polygon([(24, 47), (4, 52), (2, 62), (14, 54), (26, 52)], fill=RED); d.polygon([(26, 48), (10, 58), (8, 68), (20, 58)], fill=RED2)   # 流れる帯
    limb(d, [(36, 30), (47, 29), (58, 28)], 6, SK); d.rectangle((46, 24, 54, 34), fill=RED); fist(d, (60, 28))     # 突き出す拳
    limb(d, [(24, 30), (18, 36), (20, 44)], 6, SK); fist(d, (20, 45), 3)
    head(d, 31, 15)
    return d, im
def K():
    im, d = new()
    d.polygon([(18, 18), (8, 10), (0, 12), (4, 20), (0, 30), (10, 24), (18, 24)], fill=c('a', 2))
    limb(d, [(38, 46), (52, 40), (62, 30)], 9, GI); shoe(d, (62, 28)); limb(d, [(34, 50), (26, 62), (14, 58)], 9, GI2); shoe(d, (12, 58), -1)
    d.polygon([(22, 28), (36, 32), (40, 50), (28, 52)], fill=GI)
    d.polygon([(28, 46), (40, 48), (40, 53), (28, 51)], fill=RED2)
    d.polygon([(28, 50), (14, 54), (10, 66), (22, 56)], fill=RED)
    limb(d, [(24, 32), (14, 28), (8, 20)], 6, SK); fist(d, (7, 18), 3)
    limb(d, [(34, 34), (46, 28), (56, 22)], 6, SK); d.rectangle((44, 24, 50, 32), fill=RED); fist(d, (57, 20), 3)
    head(d, 26, 22)
    return d, im
def G():
    im, d = new()
    d.polygon([(26, 8), (12, 2), (4, 10), (10, 20), (6, 34), (16, 24), (24, 16)], fill=c('a', 2))
    limb(d, [(33, 50), (42, 62), (43, 72)], 9, GI); shoe(d, (45, 74)); limb(d, [(28, 50), (19, 60), (13, 72)], 9, GI2); shoe(d, (12, 74), -1)
    d.polygon([(24, 28), (38, 28), (36, 50), (26, 50)], fill=GI)
    d.polygon([(26, 46), (37, 46), (37, 52), (26, 52)], fill=RED2)
    d.polygon([(26, 50), (12, 56), (8, 66), (20, 58)], fill=RED); d.polygon([(30, 52), (22, 64), (22, 72), (32, 60)], fill=RED2)
    limb(d, [(36, 32), (44, 36), (42, 24)], 6, SK); d.rectangle((40, 26, 46, 34), fill=RED); fist(d, (42, 22), 3)
    limb(d, [(26, 32), (32, 38), (34, 28)], 6, SK); fist(d, (34, 26), 3)
    head(d, 31, 17)
    return d, im
def finish(im):
    a = np.array(im); al = np.pad(a[..., 3] > 0, 1); e = np.zeros_like(al)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(al, dy, 0), dx, 1)
    e = (e & ~al)[1:-1, 1:-1]; a[e] = c('K', 1); return Image.fromarray(a)
K_ = 8; sheet = Image.new("RGBA", (W * K_ * 3 + 40, H * K_ * 2 + 60), (40, 44, 60, 255))
for i, (n, fn) in enumerate((("P", P), ("K", K), ("G", G))):
    d, im = fn(); im = finish(im); x = i * (W * K_ + 20) + 10
    a = np.array(im); sil = np.zeros_like(a); sil[a[..., 3] > 0] = (240, 240, 240, 255)
    sheet.alpha_composite(Image.fromarray(sil).resize((W * K_, H * K_), Image.NEAREST), (x, 20))
    sheet.alpha_composite(im.resize((W * K_, H * K_), Image.NEAREST), (x, 30 + H * K_))
    im.save(os.path.join(OUT, f"fighter_sketch64_{n}.png"))
sheet.convert("RGB").save(os.path.join(OUT, "fighter_sketch64.png")); print("ok")
