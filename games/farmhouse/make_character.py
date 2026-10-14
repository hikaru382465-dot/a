"""
ドット絵の農夫（32×40）を Blender の画像として描いて、スプライトシートにする。

使い方:  python make_character.py
出力:    assets/character/farmer_sheet.png  （3行×4列：正面・横・うしろ、歩き4コマ）
         assets/character/farmer_front.png  （正面1コマ。make_farmhouse.py が家の絵に立たせる）
         assets/character/farmer_walk.gif   （横向きの歩き。8倍）
"""
import bpy, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "character"); os.makedirs(OUT, exist_ok=True)
W, H = 32, 40

def C(*v): return (*v, 255)
OUTLINE = C(26, 14, 14)
SKIN = (C(244, 198, 156), C(224, 164, 122), C(182, 118, 92))
STRAW = (C(244, 208, 120), C(216, 158, 62), C(160, 104, 40))
SHIRT = (C(240, 228, 198), C(208, 192, 154), C(160, 140, 112))
VEST = (C(168, 104, 60), C(120, 70, 42), C(80, 46, 32))
PANTS = (C(104, 134, 100), C(70, 98, 76), C(46, 68, 56))
BOOT = (C(104, 68, 46), C(66, 42, 30), C(40, 26, 22))
SCARF = (C(118, 150, 214), C(78, 108, 172), C(50, 72, 126))
HAIR = (C(120, 78, 50), C(92, 58, 40), C(60, 38, 30))
EYE = C(32, 22, 28)

class Canvas:
    def __init__(self): self.a = np.zeros((H, W, 4), np.uint8)
    def px(self, x, y, c):
        if 0 <= x < W and 0 <= y < H: self.a[y, x] = c
    def rect(self, x0, y0, x1, y1, pal, lit=True):
        """3色（明・中・暗）で塗る。左と上が明るく、右と下が暗い。"""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                c = pal[1]
                if x1 - x0 >= 2:
                    if x == x0 and lit: c = pal[0]
                    if x == x1: c = pal[2]
                if y1 - y0 >= 2 and y == y1: c = pal[2]
                if y == y0 and y1 - y0 >= 3 and lit and x != x1: c = pal[0]
                self.px(x, y, c)
    def outline(self):
        m = self.a[..., 3] > 0; o = np.zeros_like(m)
        o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        for y, x in zip(*np.nonzero(o & ~m)): self.a[y, x] = OUTLINE

def draw(view, step):
    c = Canvas()
    sw = [0, 1, 0, -1][step]                 # 腕のふり
    lift = [0, 0, 0, 0][step]
    bob = 1 if step in (1, 3) else 0         # 体が少し上下
    y0 = bob
    if view in ("front", "back"):
        # 脚と靴
        for i, (x0, x1) in enumerate(((11, 15), (16, 20))):
            up = 2 if (step == 1 and i == 0) or (step == 3 and i == 1) else 0
            c.rect(x0, 27, x1, 34 - up, PANTS, lit=False)
            c.rect(x0, 35 - up, x1, 38 - up, BOOT, lit=False)
        # 胴・ベスト・ベルト
        c.rect(10, 17 - y0, 21, 26 - y0, SHIRT)
        c.rect(10, 17 - y0, 12, 26 - y0, VEST); c.rect(19, 17 - y0, 21, 26 - y0, VEST)
        c.rect(10, 25 - y0, 21, 26 - y0, BOOT)
        c.px(15, 25 - y0, C(236, 200, 90)); c.px(16, 25 - y0, C(236, 200, 90))
        # 腕と手
        for (x0, x1, s) in ((7, 9, sw), (22, 24, -sw)):
            c.rect(x0, 17 - y0 + s, x1, 23 - y0 + s, SHIRT)
            c.rect(x0, 24 - y0 + s, x1, 26 - y0 + s, SKIN, lit=False)
        # スカーフと顔
        c.rect(12, 15 - y0, 19, 16 - y0, SCARF)
        c.rect(12, 8 - y0, 19, 14 - y0, SKIN if view == "front" else HAIR)
        if view == "front":
            c.px(13, 11 - y0, EYE); c.px(18, 11 - y0, EYE); c.px(13, 12 - y0, SKIN[2]); c.px(18, 12 - y0, SKIN[2])
            c.px(15, 13 - y0, SKIN[2]); c.px(16, 13 - y0, SKIN[2])
            c.rect(12, 8 - y0, 19, 8 - y0, HAIR)
    else:  # 横向き（右向き）
        far = [3, 0, -3, 0][step]
        # 奥の脚 → 手前の脚
        for (dx, pal_b) in ((-far, True), (far, False)):
            x0 = 13 + dx; c.rect(x0, 27, x0 + 3, 34, PANTS, lit=False)
            c.rect(x0, 35, x0 + 4, 38, BOOT, lit=False)
            if pal_b: pass
        c.rect(12, 17 - y0, 19, 26 - y0, SHIRT)
        c.rect(12, 17 - y0, 14, 26 - y0, VEST)
        c.rect(12, 25 - y0, 19, 26 - y0, BOOT)
        # 奥の腕（暗め）と手前の腕
        c.rect(14 - 2 * sw, 18 - y0, 16 - 2 * sw, 25 - y0, (SHIRT[2], SHIRT[2], SHIRT[2]))
        c.rect(13 + 2 * sw, 18 - y0, 16 + 2 * sw, 23 - y0, SHIRT)
        c.rect(13 + 2 * sw, 24 - y0, 16 + 2 * sw, 26 - y0, SKIN, lit=False)
        c.rect(12, 15 - y0, 19, 16 - y0, SCARF)
        c.rect(12, 8 - y0, 19, 14 - y0, SKIN)
        c.rect(12, 8 - y0, 14, 14 - y0, HAIR)
        c.px(17, 11 - y0, EYE); c.px(20, 11 - y0, SKIN[1]); c.px(20, 12 - y0, SKIN[2])
    # 麦わら帽子
    c.rect(11, 1 - y0, 20, 5 - y0, STRAW)
    for x in range(11, 21, 2): c.px(x, 3 - y0, STRAW[2])               # わらの編み目
    c.rect(11, 4 - y0, 20, 4 - y0, BOOT)                               # 帽子のひも
    bx0, bx1 = (6, 25) if view != "side" else (8, 24)
    c.rect(bx0, 6 - y0, bx1, 8 - y0, STRAW)
    for x in range(bx0 + 1, bx1, 3): c.px(x, 7 - y0, STRAW[2])
    c.outline()
    return c.a

views = ["front", "side", "back"]
sheet = np.zeros((H * 3, W * 4, 4), np.uint8)
for r, v in enumerate(views):
    for s in range(4): sheet[r * H:(r + 1) * H, s * W:(s + 1) * W] = draw(v, s)

# Blender の画像として作って Blender で保存する（上下が逆なので反転して渡す）
def save_with_blender(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=True)
    img.pixels = (arr[::-1].astype(np.float32) / 255).ravel().tolist()
    img.filepath_raw = path; img.file_format = 'PNG'; img.save()
save_with_blender(sheet, os.path.join(OUT, "farmer_sheet.png"))
save_with_blender(sheet[0:H, 0:W], os.path.join(OUT, "farmer_front.png"))

# 確認：歩きの動き（GIF）と8倍拡大
fr = []
for s in (0, 1, 2, 3):
    im = Image.fromarray(sheet[H:2 * H, s * W:(s + 1) * W]).resize((W * 8, H * 8), Image.NEAREST)
    bg = Image.new("RGBA", im.size, (36, 52, 64, 255)); bg.alpha_composite(im); fr.append(bg.convert("P"))
fr[0].save(os.path.join(OUT, "farmer_walk.gif"), save_all=True, append_images=fr[1:], duration=160, loop=0)
big = Image.fromarray(sheet).resize((W * 4 * 6, H * 3 * 6), Image.NEAREST)
bg = Image.new("RGBA", big.size, (36, 52, 64, 255)); bg.alpha_composite(big); bg.save(os.path.join(OUT, "farmer_preview.png"))
print("done")
