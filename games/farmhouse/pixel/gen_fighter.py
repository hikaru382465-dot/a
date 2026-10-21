"""
武闘家の女の子（A案）正面・軽く構えたポーズ 32×48。python gen_fighter.py
→ assets/character/fighter_v1.png / fighter_v1_x8.png / fighter_v1_sil.png
全体を文字の格子で1ドットずつ手描き（式・乱数なし）。外がわの1ドット輪郭だけ自動（np.pad→roll）。
行の書き方：「開始列:文字列」を空白でつなぐ。光は左上。色は palette.json の系統×明るさだけ（約13色）。
"""
import os
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "character"); os.makedirs(OUT, exist_ok=True)
pal, _ = pxl.load_palette()
W, H = 32, 48
KEY = {
    # 髪（紺）
    'D': ('a', 1), 'd': ('a', 2), 'h': ('a', 3), 'H': ('a', 5),
    # 肌
    'S': ('k', 5), 's': ('k', 4), 't': ('k', 3), 'T': ('k', 2),
    # 目・口
    'l': ('a', 0), 'i': ('a', 2), 'I': ('a', 4), 'j': ('a', 5), 'w': ('s', 7), 'm': ('G', 3),
    # 道着（白）
    'V': ('s', 7), 'W': ('s', 6), 'M': ('s', 5), 'U': ('s', 4), 'Z': ('s', 3),
    # 赤（手甲・帯）
    'P': ('G', 5), 'r': ('G', 4), 'R': ('G', 3), 'Q': ('G', 1), 'q': ('G', 2),
    # 靴
    'p': ('D', 5), 'o': ('D', 3), 'O': ('D', 1),
}
G = {}
def row(y, spec): G[y] = G.get(y, "") + " " + spec

# ---- ポニーテール（右上の高い所から立ちあがって、右へたれる）
row(1, "24:dhhd")
row(2, "23:dhHhhd")
row(3, "22:dhhHhhhd")
row(4, "12:dhhhhhhhhd 22:rP 24:dhhhhd")
row(5, "10:dhhHHhhhhhhd 22:Rr 24:dhhhhd")
row(6, "9:dhhHHHhhhhhhhd 24:dhhhd")
row(7, "9:dhhhhhhhhhhhhd 24:dhHhd")
row(8, "9:dhhhhhhhhhhhhd 24:dhhhd")
# ---- 前髪・顔・目（目は幅3×高さ4。上はまつげ、外へ1ドットはね、ひとみ、光の点）
row(9, "9:dhhhshddhshhhd 24:dhhhd")
row(10, "9:dhsssshdsssshd 24:dhhhd")
row(11, "9:dh 11:lll 14:s 15:ss 17:s 18:lll 21:hd 25:dhhd")
row(12, "9:dh 11:swil 15:ss 17:lwis 21:hd 25:dhhd")
row(13, "9:dh 11:sIII 15:ss 17:IIIs 21:hd 25:dhhd")
row(14, "9:dh 11:sjjj 15:ss 17:jjjs 21:hd 26:dhhd")
row(15, "10:dsttssssttsd 26:dhhd")
row(16, "12:sssmmsss 27:dhd")
row(17, "14:ssss 27:dd")
row(18, "14:sstt")
# ---- ノースリーブ道着の胴（V字のえり）
row(19, "11:VWW 14:ssss 18:UUZ")
row(20, "11:VWWZ 15:ss 17:ZUUU")
row(21, "11:VWWWZ 16:s 17:ZUUU")
row(22, "11:VWWWWZMUUU")
row(23, "11:VWWWWMMUUZ")
row(24, "11:VWWWWMMUUZ")
row(25, "11:WWWWWMMUUZ")
row(26, "11:WWWWMMUUUZ")
row(27, "11:WWWWMMUUUZ")
# ---- 太い赤い帯
row(28, "10:PrrrrrrrrRQ")
row(29, "10:rrrrrrrrrRQ")
row(30, "10:rrrrrrrrRRQ")
row(31, "10:RRRRRRRRRRQ")
# ---- 脚（ゆるいズボン）
row(32, "10:VWWWWUUUUUZZ")
row(33, "9:VWWWWWUUUUUUZZ")
row(34, "9:VWWWWWUUUUUUZZ")
row(35, "9:WWWWWUUUUUUUZZ")
row(36, "9:WWWWWZUUUUUUZZ")
row(37, "9:WWWWWZ 16:WWUUUZZ")
row(38, "9:WWWWWZ 16:WWUUUZZ")
row(39, "9:WWWWUZ 16:WWUUUZZ")
row(40, "10:WWWUZ 16:WUUUUZ")
row(41, "10:WWUUZ 16:WUUUZ")
row(42, "10:UUUUZ 16:UUUUZ")
row(43, "10:ooooO 16:oooooO")
row(44, "8:pooooOO 16:poooooOO")
row(45, "8:OOOOOOO 16:OOOOOOO")
# ---- 帯の結び目とたれ端2本（ズボンの上）
row(27, "15:rPr")
row(28, "14:PPrrR")
row(29, "14:PrQrR")
row(30, "14:rrQRR")
row(31, "14:rRRRR")
row(32, "14:rR 17:rR")
row(33, "13:rrR 17:rRR")
row(34, "13:rrR 18:rRR")
row(35, "12:rrR 18:rRR")
row(36, "12:rrR 19:rRR")
row(37, "12:rR 19:RR")
row(38, "19:rRR")
row(39, "20:RR")
# ---- 左うで（高い構え）：上うで、こぶし、大きな赤い手甲
for y in range(19, 28): row(y, "9:st")
row(19, "9:ss 4:SSss"); row(20, "3:SSsstt"); row(21, "3:StsstT")
row(22, "3:PPrrrR"); row(23, "3:PrrrrR"); row(24, "3:rqqqqR"); row(25, "3:rrrrRR"); row(26, "3:rrrRRq")
row(27, "5:ssstt"); row(28, "7:stt")
# ---- 右うで（低い構え）
for y in range(19, 30): row(y, "21:st")
row(20, "24:SSss"); row(21, "23:SSsstt"); row(22, "23:StsstT")
row(23, "23:PPrrrR"); row(24, "23:PrrrrR"); row(25, "23:rqqqqR"); row(26, "23:rrrrRR"); row(27, "23:rrrRRq"); row(28, "24:rrRRq")
row(29, "22:sstt"); row(30, "22:stt")

def build():
    a = np.zeros((H, W, 4), np.uint8)
    for y, spec in G.items():
        for item in spec.split():
            c0, txt = item.split(':')
            for i, ch in enumerate(txt):
                if ch == '.': continue
                f, s = KEY[ch]
                x = int(c0) + i
                assert 0 <= x < W, (y, item)
                a[y, x] = (*[int(v) for v in pal[f][s]], 255)
    return a

def outline(a):
    al = np.pad(a[..., 3] > 0, 1)
    e = np.zeros_like(al)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(al, dy, 0), dx, 1)
    e = e & ~al
    big = np.pad(a, ((1, 1), (1, 1), (0, 0)))
    big[e] = (*[int(v) for v in pal['K'][1]], 255)
    return big[1:-1, 1:-1] if (big[0].any() == 0 and big[-1].any() == 0 and big[:, 0].any() == 0 and big[:, -1].any() == 0) else big[1:-1, 1:-1]

if __name__ == "__main__":
    a = outline(build())
    Image.fromarray(a).save(os.path.join(OUT, "fighter_v1.png"))
    im = Image.fromarray(a)
    bg = Image.new("RGBA", (W, H), (46, 50, 72, 255)); bg.alpha_composite(im)
    bg.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(OUT, "fighter_v1_x8.png"))
    sil = np.zeros_like(a); sil[a[..., 3] > 0] = (240, 240, 240, 255)
    sb = Image.new("RGBA", (W, H), (46, 50, 72, 255)); sb.alpha_composite(Image.fromarray(sil))
    sb.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(OUT, "fighter_v1_sil.png"))
    print("ok", a[..., 3].astype(bool).sum())
