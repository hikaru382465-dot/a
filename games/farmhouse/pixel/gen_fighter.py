"""
武闘家の女の子（A案）正面・軽く構えたポーズ 32×48。python gen_fighter.py
→ assets/character/fighter_v2.png / fighter_v2_x8.png / fighter_v2_sil.png
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
    # 髪（紺・3色）
    'D': ('a', 1), 'd': ('a', 1), 'h': ('a', 3), 'H': ('a', 5),
    # 肌（黄みの淡い桃・3色）
    'S': ('A', 6), 's': ('A', 5), 't': ('A', 4),
    # 目：黒目は濃い紺、光は白
    'l': ('a', 0), 'w': ('s', 6), 'm': ('G', 2),
    # 道着（白・3色）
    'V': ('s', 6), 'W': ('s', 6), 'U': ('s', 4), 'Z': ('s', 3),
    # 赤（手甲・帯・3色）
    'P': ('G', 5), 'r': ('G', 4), 'R': ('G', 2),
    # 靴
    'o': ('D', 3), 'O': ('D', 1),
}
G = {}
def row(y, spec): G[y] = G.get(y, "") + " " + spec

# ---- ポニーテール（高い位置から立ちあがって右へたれる。ハイライトは2〜3ドット幅の筋）
row(1,  "24:DhhD")
row(2,  "23:DhHHhD")
row(3,  "22:DhhHHhhD")
row(4,  "12:DhhhhhhhhD 22:rP 24:DhHHhD")
row(5,  "10:DhhHHhhhhhhD 22:Rr 24:DhHHhD")
row(6,  "9:DhhHHHhhhhhhhD 24:DHHhD")
row(7,  "9:DhhhhhhhhhhhhD 24:DHHhD")
row(8,  "9:DhhhhhhhhhhhhD 24:DHHhD")
# ---- 前髪・顔・目（上のまつげ1行、黒目は縦2ドット、上の左に白い光）
row(9,  "9:DhhhshDDhshhhD 24:DHhhD")
row(10, "9:DhsssshDsssshD 24:DHhhD")
row(11, "9:Dh 11:DDDD 15:ss 17:DDDD 21:hD 25:DHhD")
row(12, "9:Dh 11:swll 15:ss 17:wlls 21:hD 25:DHhD")
row(13, "9:Dh 11:slll 15:ss 17:llls 21:hD 25:DHhD")
row(14, "9:Dh 11:ssssssssss 21:hD 26:DHhD")
row(15, "10:DsttssssttsD 26:DhhD")
row(16, "12:sssmmsss 27:DhD")
row(17, "14:ssss 27:DD")
row(18, "14:sstt")
# ---- ノースリーブ道着の胴（V字のえりは濃い線で1ドット太く）
row(19, "11:WW 13:D 14:ssss 18:D 19:UU")
row(20, "11:WWW 14:D 15:ss 17:D 18:UUU")
row(21, "11:WWWW 15:DD 17:UUUU")
row(22, "11:WWWWWUUUUZ")
row(23, "11:WWWWWUUUUZ")
row(24, "11:WWWWWUUUUZ")
row(25, "11:WWWWWUUUUZ")
row(26, "11:WWWWUUUUUZ")
row(27, "11:WWWWUUUUUZ")
# ---- 太い赤い帯
row(28, "10:PPPPPPPPPPr")
row(29, "10:rrrrrrrrrrR")
row(30, "10:rrrrrrrrrrR")
row(31, "10:RRRRRRRRRRR")
# ---- 脚（ゆるいズボン）
row(32, "10:WWWWWUUUUUZZ")
row(33, "9:WWWWWWUUUUUUZZ")
row(34, "9:WWWWWWUUUUUUZZ")
row(35, "9:WWWWWUUUUUUUZZ")
row(36, "9:WWWWWZUUUUUUZZ")
row(37, "9:WWWWWZ 16:WWUUUZZ")
row(38, "9:WWWWWZ 16:WWUUUZZ")
row(39, "9:WWWWUZ 16:WWUUUZZ")
row(40, "10:WWWUZ 16:WUUUUZ")
row(41, "10:WWUUZ 16:WUUUZ")
row(42, "10:UUUUZ 16:UUUUZ")
row(43, "10:ooooO 16:oooooO")
row(44, "8:oooooOO 16:oooooOO")
row(45, "8:OOOOOOO 16:OOOOOOO")
# ---- 帯の結び目とたれ端2本（幅2ドット、少し斜め、暗い赤は外がわの1列だけ）
row(27, "15:rrr")
row(28, "14:Prrrr")
row(29, "14:rrRrr")
row(30, "14:rrrRr")
row(31, "14:RRRRR")
row(32, "14:Rr 17:rR")
row(33, "14:Rr 17:rR")
row(34, "13:Rr 18:rR")
row(35, "13:Rr 18:rR")
row(36, "12:Rr 19:rR")
row(37, "12:Rr 19:rR")
row(38, "12:Rr 20:rR")
row(39, "20:rR")
row(40, "20:R")
# ---- 左うで（あごの近くまで上げた構え）：こぶし→先がせまい手甲→ひじ→上うで
row(15, "3:SSss"); row(16, "3:Ssst")
row(17, "3:PrrrR"); row(18, "3:rrrrR"); row(19, "3:rrrRR 8:sss")
row(20, "4:rrR 8:st"); row(21, "4:rRR 8:st"); row(22, "4:RRR 8:st")
row(23, "4:sst 8:st"); row(24, "4:sssstt")
# ---- 右うで（低い構え）：上うで→ひじ→手首にそう手甲→2×2のこぶし
row(19, "21:sss")
for y in range(20, 26): row(y, "22:st")
row(26, "22:stt")
row(27, "23:PrR"); row(28, "23:rrR"); row(29, "23:PrrrR"); row(30, "23:rrrRR"); row(31, "24:rrRR")
row(32, "25:Ss"); row(33, "25:st")

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
    Image.fromarray(a).save(os.path.join(OUT, "fighter_v2.png"))
    im = Image.fromarray(a)
    bg = Image.new("RGBA", (W, H), (46, 50, 72, 255)); bg.alpha_composite(im)
    bg.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(OUT, "fighter_v2_x8.png"))
    sil = np.zeros_like(a); sil[a[..., 3] > 0] = (240, 240, 240, 255)
    sb = Image.new("RGBA", (W, H), (46, 50, 72, 255)); sb.alpha_composite(Image.fromarray(sil))
    sb.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(OUT, "fighter_v2_sil.png"))
    print("ok", a[..., 3].astype(bool).sum())
