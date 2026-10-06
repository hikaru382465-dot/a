"""
1枚の絵を、1ドットずつ手で決めて描く（オリジナル：旅の薬草売りの少女、右向き、26×64）。
文字1つ＝1ドット。下の LEGEND で文字をパレットの色に変える。外側の輪郭は自動で足す。
python hand_girl.py → sprites/hand_girl.pxl / .png / _big.png
"""
import os
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 26, 59
LEGEND = {
    'O': 'U1', 'o': 'U4',                                          # 輪郭・中の線（暗いえんじ紫）
    '1': 'a1', '2': 'a2', '3': 'a3', '4': 'a4', '5': 'a5', '6': 'a6',  # 紺の髪
    'z': 'V0', 'r': 'V1', 's': 'V4', 'S': 'V7',                     # 肌（影・ほお・ふつう・明るい）
    'e': 'U1', 'w': 'L7', 'x': 'L4', 'W': 'L6',                     # 目・白
    'g': 'c2', 'G': 'c4', 'h': 'c6',                                # 深い緑のスカーフ
    'm': 'b2', 'n': 'b3', 't': 'b4', 'T': 'b5', 'y': 'b6',          # からし色の服
    'j': 'J2', 'k': 'J3', 'l': 'J4', 'L': 'J6', 'q': 'B6',          # 革（ベルト・かばん）と金具
    'p': 'R1', 'P': 'R3',                                           # 濃い色のタイツ
    'b': 'D1', 'B': 'D3', 'C': 'D5',                                # 茶色のブーツ
    'i': 'L5', 'I': 'L7',                                           # すその白
    'f': 'E4', 'F': 'H5',                                           # かばんの薬草（緑の葉・だいだいの花）
}
g = [['.'] * W for _ in range(H)]
def put(row, col, s):
    for i, ch in enumerate(s):
        if ch != ' ' and 0 <= col + i < W: g[row][col + i] = ch

# ---------------- 頭（髪・顔）
put(0, 10, "OOOOO")
put(1, 8, "O455554432O")
put(2, 7, "O34565565432O")
put(3, 6, "O3456556554321O")
put(4, 5, "O23454554543321O")
put(5, 5, "O234434443433221O")
put(6, 4, "O2234334343332211O")
put(7, 4, "O2233333332211sssO")
put(8, 4, "O22333333221" + "1" + "SsssO")
put(9, 4, "O2233333221sss2ssO")
put(10, 4, "O223333221zsssessO")
put(11, 4, "O22333221zsssseSssO")
put(12, 4, "O22333221zzssrrsssO")
put(13, 4, "O22333221zsssrrszO")
put(14, 4, "O22332211zssszsO")
put(15, 5, "O2232211zzsssszO")
put(16, 5, "O2232211zzzsszO")
put(17, 5, "O223211OzzzzOO")
# ---------------- ポニーテール（後ろにたれる）
for r, (c, s) in enumerate([(4, "O243211O"), (4, "O24321O"), (3, "O234211O"), (3, "O24321O"), (3, "O2421O"), (2, "O24211O"),
                            (2, "O2421O"), (2, "O2321O"), (2, "O241O"), (2, "O231O"), (2, "O21O"), (3, "O1O"), (3, "OO")]):
    put(18 + r, c, s)
put(8, 7, "q"); put(9, 7, "q")                                    # 髪どめ
# ---------------- スカーフ
put(18, 10, "OgGGGhGGgO")
put(19, 9, "OgGGhhGGGgO")
put(20, 9, "OggGGGGGGgO")
put(21, 16, "OGgO"); put(22, 16, "OgO")                            # 結び目のはし
# ---------------- 胴（チュニック）
for r in range(21, 33):
    put(r, 8, "OTTttttnnnmO" if r > 21 else "OyTTtttttnnO")
put(22, 9, "yT"); put(23, 9, "y")
# 肩かけのひも（かばんへ）
for r, c in ((22, 15), (23, 14), (24, 13), (25, 12), (26, 11), (27, 10), (28, 9)): put(r, c, "kj")
# 前の腕（そで）と手
arm = [(21, 13, "oyyTO"), (22, 14, "oyTTO"), (23, 15, "oyTtO"), (24, 16, "oTTtO"), (25, 17, "oTtnO"), (26, 17, "oTtnmO"),
       (27, 17, "oWWxxO"), (28, 17, "oSsszO"), (29, 16, "oSszO"), (30, 15, "oSszO"), (31, 14, "OSsszO"), (32, 14, "OzzO")]
for r, c, s in arm: put(r, c, s)
# ベルト
put(31, 8, "Ojkkkkkk"); put(32, 8, "Ojjjjjjj"); put(31, 15, "q")
# ---------------- かばん（後ろの腰）と薬草
put(27, 3, "  f F")
put(28, 2, " ffFf")
put(29, 2, "OfFffO")
put(30, 1, "OLLLLLLO")
put(31, 1, "OlLLLLlkO")
put(32, 1, "OkllqllkO")
put(33, 1, "OkkkkkkjO")
put(34, 1, "OkkkkkkjO")
put(35, 1, "OkkkkkjjO")
put(36, 2, "OjjjjjO")
put(37, 3, "OOOOO")
# ---------------- スカート（すそが広がる・ひだ）
cols = [8, 8, 7, 7, 6, 6, 5, 5, 4, 4, 4]
rights = [19, 20, 20, 21, 21, 22, 22, 23, 23, 24, 24]
folds = [((11, 8), "n", "y"), ((14, 14), "n", "T"), ((17, 20), "m", "T")]   # （上のx, 下のx）：ひだの線は上から下へ広がる
for i, (c0, c1) in enumerate(zip(cols, rights)):
    row = {x: "t" for x in range(c0 + 1, c1)}
    row[c0 + 1] = "T"; row[c1 - 1] = "m"; row[c1 - 2] = "n"
    for (xt, xb), dk, lt in folds:
        x = int(round(xt + (xb - xt) * i / 10))
        if x in row: row[x] = dk
        if x - 1 in row and i > 1: row[x - 1] = lt
    put(33 + i, c0, "O" + "".join(row[x] for x in range(c0 + 1, c1)) + "O")
put(44, 4, "OiiIIIiiiiiiiiiiixO")
put(45, 4, "OxiiiiiixxiiiixxxxO")
put(46, 5, "OOOOOOOOOOOOOOOOO")
# ---------------- 足（後ろの足は暗く後ろへ、前の足は明るく前へ＝歩いているところ）
for i, r in enumerate(range(47, 52)):
    put(r, 8 - i // 2, "OppO"); put(r, 13 + (i + 1) // 2, "OPPpO")
# ---------------- ブーツ（後ろ：かかとが少し上がる、前：つま先が前）
put(52, 4, "OBBBBO");   put(52, 15, "OCBBBO")
put(53, 3, "OBBBBBO");  put(53, 15, "OCBBBBO")
put(54, 3, "OBBBBBBO"); put(54, 15, "OCCBBBBBO")
put(55, 2, "OBBBBBBO"); put(55, 15, "OBBBBBBBBO")
put(56, 2, "ObbbbbbO"); put(56, 15, "ObbbbbbbbO")
put(57, 2, "OOOOOOOO"); put(57, 15, "OOOOOOOOOO")

# ---------------- 外側の輪郭を自動で足す → .pxl
code = np.array([[LEGEND.get(ch, '..') for ch in row] for row in g], dtype="<U2")
m = code != '..'; e = np.zeros_like(m)
for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(m, dy, 0), dx, 1)
for y, x in zip(*np.nonzero(e & ~m)): code[y, x] = 'U1'
p = os.path.join(HERE, "sprites", "hand_girl.pxl")
with open(p, "w") as f:
    f.write(f"# 手描き：旅の薬草売りの少女（右向き）\n@size {W} {H}\n")
    for r in code: f.write(" ".join(r) + "\n")
c, img, pal = pxl.build(p); Image.fromarray(img).save(p.replace(".pxl", ".png"))
k = 10; big = Image.fromarray(img).resize((W * k, H * k), Image.NEAREST)
bg = Image.new("RGBA", big.size, (236, 234, 225, 255)); bg.alpha_composite(big); bg.convert("RGB").save(p.replace(".pxl", "_big.png"))
print("ok")
