"""
武闘家の女の子：シルエット3案の下絵（32×48）。python gen_fighter_sketch.py → assets/character/fighter_sketch.png（塗りつぶし＋色つき＋原寸）
A=高いポニーテール＋ノースリーブ道着＋大きな手甲＋太い帯 / B=おだんご2つ＋チャイナ上着＋バンテージ / C=短い髪＋ハチマキ＋はだけた道着＋素足
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "character"); os.makedirs(OUT, exist_ok=True)
pal, _ = pxl.load_palette()
def c(f, s): return tuple(int(v) for v in pal[f][s]) + (255,)
W, H = 32, 48
SK, SK2 = c('A', 4), c('A', 3)
HAIR, HAIR2, HAIR3 = c('a', 3), c('a', 2), c('a', 5)
GI, GI2 = c('s', 6), c('s', 4)
RED, RED2 = c('G', 4), c('G', 2)
SHOE = c('D', 3)
OUTL = c('K', 1)

def new(): im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)
def finish(im):
    a = np.array(im); al = np.pad(a[..., 3] > 0, 1); e = np.zeros_like(al)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(al, dy, 0), dx, 1)
    e = (e & ~al)[1:-1, 1:-1]; a[e] = OUTL; return Image.fromarray(a)
def head(d, cx=16, cy=10, hair=HAIR):
    d.ellipse((cx - 7, cy - 7, cx + 6, cy + 6), fill=hair)                      # 髪（頭）
    d.ellipse((cx - 5, cy - 3, cx + 4, cy + 6), fill=SK)                        # 顔
    d.rectangle((cx - 4, cy - 3, cx + 3, cy - 1), fill=hair)                    # 前髪
    d.rectangle((cx - 3, cy + 1, cx - 2, cy + 3), fill=c('G', 5)); d.rectangle((cx + 1, cy + 1, cx + 2, cy + 3), fill=c('G', 5))   # 目
def legs(d, wide=False, bandage=False, bare=False, short=False):
    top = 29
    if wide:                                              # ゆるいズボン
        d.polygon([(10, top), (22, top), (24, 44), (17, 44), (16, 36), (15, 44), (8, 44)], fill=GI)
        d.polygon([(10, top), (14, top), (13, 44), (8, 44)], fill=GI2)
    else:
        d.rectangle((11, top, 15, 43), fill=GI); d.rectangle((17, top, 21, 43), fill=GI)
        d.rectangle((11, top, 12, 43), fill=GI2)
    if short:                                             # 七分丈：すねから下ははだ
        d.rectangle((11, 39, 15, 43), fill=SK); d.rectangle((17, 39, 21, 43), fill=SK)
    if bandage:
        for y in (40, 42): d.line((11, y, 15, y), fill=c('s', 7)); d.line((17, y, 21, y), fill=c('s', 7))
    d.rectangle((10, 44, 15, 45), fill=(SK if bare else SHOE)); d.rectangle((17, 44, 22, 45), fill=(SK if bare else SHOE))
    if bare: d.line((10, 45, 15, 45), fill=c('s', 7)); d.line((17, 45, 22, 45), fill=c('s', 7))

def A():
    im, d = new()
    d.polygon([(19, 4), (24, 0), (29, 3), (30, 11), (27, 17), (27, 10), (25, 6)], fill=HAIR2)        # 高いポニーテール
    head(d)
    legs(d)
    d.rectangle((11, 17, 20, 28), fill=GI); d.rectangle((11, 17, 12, 28), fill=GI2)                   # ノースリーブの胴
    d.rectangle((8, 17, 10, 24), fill=SK); d.rectangle((21, 17, 23, 24), fill=SK)                      # むき出しの腕
    d.rectangle((6, 22, 10, 29), fill=RED); d.rectangle((21, 22, 25, 29), fill=RED)                    # 大きな手甲
    d.rectangle((11, 26, 20, 29), fill=RED2)                                                          # 太い帯
    d.polygon([(19, 29), (22, 29), (24, 36), (21, 35)], fill=RED); d.polygon([(13, 29), (16, 29), (14, 37), (11, 35)], fill=RED2)   # たれる帯
    return finish(im)
def B():
    im, d = new()
    d.ellipse((7, 0, 12, 5), fill=HAIR2); d.ellipse((20, 0, 25, 5), fill=HAIR2)                        # おだんご2つ
    head(d, cy=11)
    legs(d, bandage=True, short=True)
    d.rectangle((10, 18, 21, 27), fill=GI); d.rectangle((10, 18, 11, 27), fill=GI2)                    # 短い上着
    d.rectangle((13, 17, 18, 18), fill=RED)                                                           # たて襟
    d.rectangle((7, 18, 10, 27), fill=GI); d.rectangle((21, 18, 24, 27), fill=GI)                      # そで
    for y in (23, 25, 27): d.line((7, y, 10, y), fill=c('s', 7)); d.line((21, y, 24, y), fill=c('s', 7))   # バンテージ
    d.rectangle((7, 28, 10, 29), fill=SK); d.rectangle((21, 28, 24, 29), fill=SK)
    d.rectangle((10, 27, 21, 28), fill=RED)
    return finish(im)
def C():
    im, d = new()
    d.polygon([(8, 7), (6, 3), (10, 5), (12, 1), (15, 4), (18, 0), (21, 4), (25, 2), (24, 8)], fill=HAIR)   # ぼさぼさ短髪
    head(d)
    d.polygon([(8, 6), (24, 6), (24, 8), (8, 8)], fill=RED)                                              # ハチマキ
    d.polygon([(8, 7), (3, 9), (0, 13), (4, 11), (7, 9)], fill=RED2)                                       # なびく端
    legs(d, wide=True, bare=True)
    d.rectangle((10, 17, 21, 28), fill=GI); d.polygon([(13, 17), (18, 17), (16, 25)], fill=SK)           # はだけた胸元
    d.rectangle((7, 17, 10, 27), fill=GI); d.rectangle((21, 17, 24, 27), fill=GI)
    d.rectangle((7, 27, 10, 29), fill=SK); d.rectangle((21, 27, 24, 29), fill=SK)
    d.rectangle((10, 26, 21, 28), fill=RED2)
    return finish(im)

K = 8
sheet = Image.new("RGBA", (W * K * 3 + 40, (H * K) * 2 + 70), (40, 44, 60, 255))
dr = ImageDraw.Draw(sheet)
for i, (name, fn) in enumerate((("A", A), ("B", B), ("C", C))):
    im = fn(); x = i * (W * K + 20) + 10
    a = np.array(im); sil = np.zeros_like(a); sil[a[..., 3] > 0] = (240, 240, 240, 255)
    sheet.alpha_composite(Image.fromarray(sil).resize((W * K, H * K), Image.NEAREST), (x, 30))
    sheet.alpha_composite(im.resize((W * K, H * K), Image.NEAREST), (x, 30 + H * K + 10))
    dr.text((x + W * K // 2 - 4, 10), name, fill=(255, 255, 255, 255))
    Image.fromarray(a).save(os.path.join(OUT, f"fighter_sketch_{name}.png"))
sheet.convert("RGB").save(os.path.join(OUT, "fighter_sketch.png")); print("ok")
