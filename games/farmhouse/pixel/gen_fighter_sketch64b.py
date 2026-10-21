"""
武闘家：塊（かたまり）のあるシルエット3案（64×80）。見本（75×78、約3400ドット）と並べて、大きさと塊を比べる。
V1=広袖 / V2=羽織（はおり）がなびく / V3=はかま（ベル形のすそ）
python gen_fighter_sketch64b.py → assets/character/fighter_sketch64b.png
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "character")
pal, _ = pxl.load_palette()
def c(f, s): return tuple(int(v) for v in pal[f][s]) + (255,)
W, H = 64, 80
SK, HAIR, HAIR2, GI, GI2, RED, RED2, SHOE, NAVY = c('A', 4), c('a', 3), c('a', 2), c('s', 6), c('s', 4), c('G', 4), c('G', 2), c('D', 3), c('F', 3)
def new(): im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)
def limb(d, pts, w, fill):
    for a, b in zip(pts[:-1], pts[1:]): d.line([a, b], fill=fill, width=w)
    for p in pts: d.ellipse((p[0] - w / 2 + .5, p[1] - w / 2 + .5, p[0] + w / 2 - .5, p[1] + w / 2 - .5), fill=fill)
def head(d, x, y):
    d.ellipse((x - 10, y - 10, x + 9, y + 9), fill=HAIR)
    d.ellipse((x - 6, y - 3, x + 7, y + 8), fill=SK); d.rectangle((x - 5, y - 4, x + 6, y - 1), fill=HAIR)
    d.rectangle((x - 3, y + 1, x - 1, y + 3), fill=c('G', 5)); d.rectangle((x + 2, y + 1, x + 4, y + 3), fill=c('G', 5))
def fist(d, p, r=4): d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=SK); d.ellipse((p[0] - r - 2, p[1] - 1, p[0] + 2, p[1] + 5), fill=RED)
def pony(d, pts, col=HAIR2): d.polygon(pts, fill=col)

def V1():          # 広袖：両そでが大きく広がる
    im, d = new()
    pony(d, [(34, 4), (50, 0), (62, 8), (63, 24), (58, 40), (56, 24), (48, 14), (38, 12)])
    d.polygon([(22, 50), (42, 50), (56, 77), (8, 77)], fill=GI)                                    # 広がるズボン
    d.polygon([(22, 50), (32, 50), (26, 77), (8, 77)], fill=GI2)
    d.polygon([(22, 28), (42, 28), (40, 52), (24, 52)], fill=GI)                                    # 胴
    d.polygon([(24, 46), (40, 46), (40, 53), (24, 53)], fill=RED2)
    d.polygon([(38, 50), (60, 56), (62, 68), (44, 58)], fill=RED)
    d.polygon([(22, 30), (6, 36), (0, 54), (4, 62), (16, 46), (24, 44)], fill=NAVY)               # 左の大きな広袖
    d.polygon([(42, 30), (56, 28), (63, 40), (62, 52), (52, 44), (42, 44)], fill=NAVY)            # 右の広袖
    fist(d, (8, 62), 3); fist(d, (58, 54), 3)
    head(d, 31, 17)
    return im
def V2():          # 羽織：大きな上着が後ろへなびく
    im, d = new()
    pony(d, [(30, 6), (44, 2), (56, 10), (58, 22), (50, 16), (40, 14)])
    d.polygon([(22, 20), (40, 20), (62, 30), (63, 60), (50, 70), (30, 52), (20, 46)], fill=NAVY)  # なびく羽織（右後ろへ大きく）
    d.polygon([(24, 50), (38, 50), (34, 77), (14, 77)], fill=GI); d.polygon([(24, 50), (30, 50), (22, 77), (8, 77)], fill=GI2)
    d.polygon([(30, 50), (42, 52), (54, 77), (36, 77)], fill=GI)
    d.polygon([(22, 28), (38, 28), (36, 52), (24, 52)], fill=GI); d.polygon([(24, 46), (38, 46), (38, 53), (24, 53)], fill=RED2)
    limb(d, [(24, 32), (12, 38), (6, 50)], 8, SK); fist(d, (5, 52), 4)
    limb(d, [(36, 30), (20, 22), (8, 14)], 7, SK); fist(d, (7, 12), 4)
    head(d, 30, 17)
    return im
def V3():          # はかま：ベル形の大きなすそ（見本に近い塊）
    im, d = new()
    pony(d, [(34, 6), (52, 2), (63, 10), (63, 28), (58, 46), (56, 28), (48, 16), (38, 14)])
    d.polygon([(22, 44), (42, 44), (62, 77), (2, 77)], fill=NAVY); d.polygon([(22, 44), (32, 44), (30, 77), (2, 77)], fill=c('F', 2))
    d.polygon([(20, 26), (44, 26), (42, 46), (22, 46)], fill=GI)
    d.polygon([(20, 40), (44, 40), (44, 47), (20, 47)], fill=RED2)
    d.polygon([(32, 47), (46, 54), (48, 68), (36, 56)], fill=RED)
    d.polygon([(20, 28), (4, 34), (0, 46), (8, 48), (20, 42)], fill=GI2); d.polygon([(44, 28), (56, 32), (62, 40), (56, 46), (44, 40)], fill=GI)   # ゆったりそで
    fist(d, (4, 47), 3); fist(d, (58, 44), 3)
    head(d, 32, 16)
    return im
def finish(im):
    a = np.array(im); al = np.pad(a[..., 3] > 0, 1); e = np.zeros_like(al)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(al, dy, 0), dx, 1)
    e = (e & ~al)[1:-1, 1:-1]; a[e] = c('K', 1); return Image.fromarray(a)
K = 7; ref = Image.open(os.path.join(OUT, "ref_sil_dots.png")).convert("RGB")
rw, rh = ref.width // 10, ref.height // 10
cells = []
for n, fn in (("V1", V1), ("V2", V2), ("V3", V3)):
    im = finish(fn()); a = np.array(im); cnt = int((a[..., 3] > 0).sum())
    sil = np.zeros_like(a); sil[a[..., 3] > 0] = (245, 245, 245, 255)
    cells.append((n, im, Image.fromarray(sil), cnt))
    im.save(os.path.join(OUT, f"fighter_sketch64b_{n}.png"))
sheet = Image.new("RGB", (rw * K + 20 + (W * K + 20) * 3, max(rh, H * 2 + 6) * K + 20), (30, 34, 48))
sheet.paste(ref.resize((rw * K, rh * K), Image.NEAREST), (10, 10))
for i, (n, im, sil, cnt) in enumerate(cells):
    x = rw * K + 20 + i * (W * K + 20)
    bg = Image.new("RGBA", (W * K, H * K), (30, 34, 48, 255)); bg.alpha_composite(sil.resize((W * K, H * K), Image.NEAREST)); sheet.paste(bg.convert("RGB"), (x, 10))
    bg2 = Image.new("RGBA", (W * K, H * K), (30, 34, 48, 255)); bg2.alpha_composite(im.resize((W * K, H * K), Image.NEAREST)); sheet.paste(bg2.convert("RGB"), (x, 10 + H * K + 6))
    print(n, "ドット数", cnt)
sheet.save(os.path.join(OUT, "fighter_sketch64b.png")); print("ref", rw, rh)
