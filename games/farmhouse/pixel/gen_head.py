"""
パーツ1：頭（髪＋顔＋首のはじ）。24ドット幅×20行。右向き（3/4）。
参考の絵を数えた大きさに合わせる：髪をふくむ頭 約22×18、顔（肌の部分）約8×10、目は1〜3ドット。
python gen_head.py → sprites/part_head.pxl/.png/_big.png と、参考との比べ
"""
import os
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 24, 20
LEG = {'O': 'U1', 'o': 'U4', '1': 'a1', '2': 'a2', '3': 'a3', '4': 'a4', '5': 'a5', '6': 'a6', '7': 'a7',
       'z': 'V1', 'n': 'V2', 'c': 'V3', 's': 'V4', 'S': 'V6', 'T': 'V7', 'I': 'b3', 'i': 'b2', 'w': 'L7', 'e': 'a2', 'm': 'V0', 'q': 'B6', 'Q': 'B4'}
g = [['.'] * W for _ in range(H)]
def put(r, c, s):
    for i, ch in enumerate(s):
        if ch != ' ' and 0 <= c + i < W and 0 <= r < H: g[r][c + i] = ch
def fit(r, c0, c1, pat):
    """c0〜c1 の幅に、パターンを引きのばして入れる（両はしは輪郭）"""
    n = c1 - c0 + 1; inner = n - 2
    s = "".join(pat[min(len(pat) - 1, int(i * len(pat) / inner))] for i in range(inner))
    put(r, c0, "O" + s + "O")

# ---- 髪（上から）：左ほど暗く、左上に明るい帯、右は前髪（目の上までかかる）
put(0, 8, "OOOOO")
fit(1, 6, 16, "3455555544")
fit(2, 5, 17, "34566766554433")
fit(3, 4, 18, "3456677766655433")
fit(4, 3, 18, "23456666666655433")
fit(5, 3, 19, "2345566665555443 33".replace(" ", ""))
fit(6, 2, 20, "234455555544454433")
fit(7, 2, 20, "2334455444445544 3".replace(" ", ""))
fit(8, 1, 21, "2334444443444455433")
fit(9, 1, 14, "233444433433")
fit(10, 0, 13, "23344443334")
fit(11, 0, 11, "23344333")
fit(12, 0, 11, "233443323")
fit(13, 1, 11, "2334432")
fit(14, 1, 11, "2334332")
fit(15, 2, 10, "233332")
fit(16, 3, 9, "22332")

# 毛束のすじ（暗い線を斜めに、明るい線を左上に）
for (r, c) in ((3, 8), (4, 9), (5, 10), (6, 11), (7, 12), (8, 13), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 8), (11, 7), (12, 6), (13, 5)):
    if g[r][c] not in ('O', '.'): g[r][c] = '2'
for (r, c) in ((2, 8), (2, 9), (3, 9), (3, 10), (4, 11), (5, 12), (4, 6), (5, 7), (6, 8), (7, 9), (8, 10), (9, 11)):
    if g[r][c] not in ('O', '.'): g[r][c] = '7' if (r + c) % 2 == 0 else '6'
# 前髪のとがった先（顔にかかる）
put(8, 14, "O4"); put(9, 14, "O4"); put(7, 17, "O3"); put(8, 18, "3O")
# ---- 顔（肌）：左はさかい目が髪にかかる。右は鼻先まで
face = {
    8: (17, "sSsS"), 9: (15, "zzsssS"), 10: (13, "zsssssss"), 11: (12, "zzsssssss"), 12: (12, "zzsssssss"),
    13: (12, "zcsssssss"), 14: (13, "zsssssss"), 15: (14, "zsssss"), 16: (15, "zzss"),
}
for r, (c, s_) in face.items(): put(r, c, s_)
put(11, 21, "s"); put(12, 21, "s"); put(13, 21, "z")                        # 鼻先
put(9, 16, "ee"); put(9, 18, "e")                                           # まゆ
put(10, 15, "OOOO"); put(11, 15, "iwII"); put(12, 16, "zz")                 # 目
put(13, 15, "cc")                                                            # ほお
put(14, 19, "mm")                                                            # 口
put(15, 16, "zz")                                                            # あごの影
# ---- 首のはじ（体につなぐ目印：下の中央が x=16）
put(17, 14, "nnnnn"); put(18, 14, "nnnnn"); put(19, 14, "nnnnn")
# ---- 髪どめ
put(5, 6, "q"); put(6, 6, "Q")

code = np.array([[LEG.get(ch, '..') for ch in row] for row in g], dtype="<U2")
m_ = code != '..'; e_ = np.zeros_like(m_)
for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e_ |= np.roll(np.roll(m_, dy, 0), dx, 1)
for y, x in zip(*np.nonzero(e_ & ~m_)): code[y, x] = 'U1'
p = os.path.join(HERE, "sprites", "part_head.pxl")
with open(p, "w") as f:
    f.write(f"# 部品：頭（右向き3/4）。体につなぐ位置＝下の中央 x=15\n@size {W} {H}\n")
    for r in code: f.write(" ".join(r) + "\n")
c, img, pal = pxl.build(p); Image.fromarray(img).save(p.replace(".pxl", ".png"))
k = 16
def up(arr):
    im = Image.fromarray(arr); bg = Image.new("RGBA", (im.width * k, im.height * k), (236, 234, 225, 255)); bg.alpha_composite(im.resize((im.width * k, im.height * k), Image.NEAREST)); return bg.convert("RGB")
ref = np.asarray(Image.open(os.path.join(HERE, "ref", "girl_src01_traced.png")))[:20]
A_, B_ = up(ref), up(img)
out = Image.new("RGB", (A_.width + B_.width + 30, max(A_.height, B_.height)), (236, 234, 225)); out.paste(A_, (0, 0)); out.paste(B_, (A_.width + 30, 0))
out.save(os.path.join(HERE, "ref", "compare_head.png")); B_.save(p.replace(".pxl", "_big.png")); print("ok")
