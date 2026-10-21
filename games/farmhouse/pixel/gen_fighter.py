"""
武闘家の女の子（A案）正面・軽く構えたポーズ 32×48。python gen_fighter.py
→ assets/character/fighter_v9.png / fighter_v9_x8.png / fighter_v9_sil.png
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
    # 髪（紺：濃い縁・影・ふつう・水色がかった筋）
    'D': ('a', 1), 'd': ('a', 1), 'e': ('a', 2), 'h': ('a', 3), 'H': ('a', 6),
    # 肌（淡い桃・影）
    'S': ('A', 6), 's': ('A', 6), 't': ('A', 4), 'u': ('A', 4),
    # 目・口
    'l': ('a', 1), 'w': ('s', 6), 'm': ('G', 2),
    # 道着：白・灰青・青灰の3段（大きな面で）
    'V': ('s', 6), 'W': ('s', 6), 'U': ('F', 7), 'Z': ('S', 4),
    # 赤（手甲・帯）：明るい・ふつう・暗い
    'P': ('G', 5), 'r': ('G', 4), 'R': ('G', 2),
    # 靴
    'o': ('D', 3), 'p': ('D', 5), 'N': ('F', 7), 'O': ('a', 1),
}
MAT = {}
for ch in 'DdehHN': MAT[ch] = 'hair'
for ch in 'SstulwSm': MAT[ch] = 'skin'
for ch in 'VWUZ': MAT[ch] = 'gi'
for ch in 'PrR': MAT[ch] = 'red'
for ch in 'opO': MAT[ch] = 'shoe'
OUTC = {'hair': ('a', 1), 'skin': ('A', 2), 'gi': ('S', 1), 'red': ('G', 2), 'shoe': ('a', 1)}
G = {}
def row(y, spec): G[y] = G.get(y, "") + " " + spec

# ---- ポニーテール（高い位置から立ちあがって右へたれる。ハイライトは2ドット幅のひと筋）
row(1,  "24:DhhD")
row(2,  "23:DhHHhD")
row(3,  "22:DhhHHhhD")
row(4,  "12:DhhhhhhhhD 22:rP 24:DHHhhD")
row(5,  "10:DhhHHhhhhhhD 22:Rr 24:DHHhhD")
row(6,  "9:DhhHHHhhhhhhhD 24:DHhhD")
row(7,  "9:DhhhhhhhhhhhhD 24:DHhhD")
row(8,  "9:DhhhhhhhhhhhhD 11:sD 19:Ds 24:DHhhD")
# ---- 前髪（3つの房：真ん中が1ドット長く、左右は短くずらす）・目（上のまつげ1行、黒目は縦2ドット、左上に白い光）
row(9,  "9:Dh 11:ss 13:DD 15:hh 17:DD 19:ss 21:hD 24:DHhhD")
row(10, "9:Dh 11:DDD 15:hD 18:DDD 21:hD 24:DHhhD")
row(11, "9:Dh 11:s 12:wl 14:w 15:ss 17:w 18:lw 20:s 21:hD 25:DHhD")
row(12, "9:Dh 11:s 12:ll 14:w 15:ss 17:w 18:ll 20:s 21:hD 25:DHhD")
row(13, "9:Dh 11:s 12:ll 14:s 15:ss 17:s 18:ll 20:s 21:hD 26:DHhD")
row(14, "9:Dh 11:ssssssssss 21:hD 26:DHhD")
row(15, "10:DsttssssttsD 27:DHD")
row(16, "12:sssmmsss 17:s 27:DhD")
row(17, "14:ssss 27:DD")
row(18, "14:sstt")
# ---- ノースリーブ道着の胴（V字のえりは濃い線）
row(19, "11:WW 13:D 14:ssss 18:D 19:UZ")
row(20, "11:WWW 14:D 15:ss 17:D 18:UUZ")
row(21, "11:WWWW 15:DD 17:UUUZ")
row(22, "11:WWWWWWWZZZ")
row(23, "11:WWWWWWZZZZ")
row(24, "11:WWWWWZZZZZ")
row(25, "11:WWWWZZZZZZ")
row(26, "11:WWWZZZZZZZ")
row(27, "11:UUUUUUUZZZ")
# ---- 太い赤い帯
row(28, "10:PPPPPPPPPPr")
row(29, "10:rrrrrrrrrrR")
row(30, "10:rrrrrrrrrrR")
row(31, "10:RRRRRRRRRRR")
# ---- 脚（ゆるいズボン。股の下に幅2ドットのすき間、左足を1列外へ、つま先は少し上げて明るく）
row(32, "10:WWWWWWWUUUZZ")
row(33, "9:WWWWWWWWUUUZZZ")
row(34, "9:WWWWWWWWUUUZZZ")
row(35, "9:WWWWWWWWUUUZZZ")
row(36, "9:WWWWUZ 17:WWWUZZ")
row(37, "9:WWWWUZ 17:WWWUZZ")
row(38, "9:WWWWUZ 17:WWWUZZ")
row(39, "9:WWWWUZ 17:WWUUZZ")
row(40, "9:WWWUZ 18:WWUZZ")
row(41, "9:WWWUZ 18:WWUZ")
row(42, "9:WWWUZ 18:WWUZ")
row(43, "9:ppppp 18:ppppp")
row(44, "7:ooooooo 18:ooooooo")
row(45, "7:ooooooo 18:ooooooo")
# ---- 帯の結び目（左腰）とたれ端2本（腰の高さで短く、片側から）
row(27, "11:PPP")
row(28, "10:Prrrr")
row(29, "10:rrRrr")
row(30, "10:rrrRr")
row(31, "10:RRRRR")
row(32, "9:rrR 11:Rrr")
row(33, "8:rrR 11:Rrr")
row(34, "8:rrR 11:Rrr")
row(35, "7:rrR 12:Rr")
row(36, "7:rrR")
row(37, "7:rR")
# ---- 左うで：肩→上うで→ひじ→斜めの前腕（肌）→手甲（太く：上は明るく下は暗く）→拳（指の線1本）
row(15, "5:SSts"); row(16, "5:SSts"); row(17, "5:sstt")
row(19, "9:ss"); row(20, "8:st"); row(21, "8:st"); row(22, "5:ss 8:st"); row(23, "6:ss 8:st"); row(24, "6:sstt")
row(18, "4:PPPPP"); row(19, "4:rrrrR"); row(20, "4:rrrR"); row(21, "4:RRRR")
# ---- 右うで：上うで→ひじを曲げ、手甲のついた前腕をみぞおちの前へ→2×2の拳
row(19, "21:sss")
for y in range(20, 24): row(y, "22:st")
row(24, "19:PPPPP"); row(25, "19:rrrrr"); row(26, "19:rrrrR"); row(27, "19:RRRRR")
row(23, "17:Ssu"); row(24, "17:stu"); row(25, "17:ZZ"); row(26, "18:Z")

# ---- 髪の影（頭の右がわ・ポニーテールの右半分は一段暗い紺）
row(4, "19:ee"); row(5, "19:ee")
for y in (6, 7, 8): row(y, "20:ee")
for y in range(9, 15): row(y, "21:e")
for y in (4, 5): row(y, "27:e")
for y in range(6, 11): row(y, "27:e")
for y in range(11, 14): row(y, "27:e")
row(2, "27:e"); row(3, "27:e"); row(14, "28:e")

row(5, "13:N"); row(3, "25:N")

def build():
    a = np.zeros((H, W, 4), np.uint8); mat = np.zeros((H, W), np.int8)
    for y, spec in G.items():
        for item in spec.split():
            c0, txt = item.split(':')
            for i, ch in enumerate(txt):
                if ch == '.': continue
                f, s = KEY[ch]
                x = int(c0) + i
                assert 0 <= x < W, (y, item)
                a[y, x] = (*[int(v) for v in pal[f][s]], 255)
                mat[y, x] = ['hair', 'skin', 'gi', 'red', 'shoe'].index(MAT[ch]) + 1
    # 髪のふちの紺(D)は、外がわの縁取りと二重にならないよう一段明るい紺にする
    al = np.pad(a[..., 3] > 0, 1)
    edge = np.zeros_like(al)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): edge |= ~np.roll(np.roll(al, dy, 0), dx, 1)
    edge = edge[1:-1, 1:-1]
    c1 = np.array([int(v) for v in pal['a'][1]], np.uint8)
    rim = (mat == 1) & edge & (a[..., :3] == c1).all(axis=2)
    a[rim] = (*[int(v) for v in pal['a'][2]], 255)
    return a, mat

def outline(a, mat):
    """素材ごとの一番濃い色で縁取る（np.padしてからroll。迷子ドットなし）"""
    al = np.pad(a[..., 3] > 0, 1)
    mp = np.pad(mat, 1)
    out = np.pad(a, ((1, 1), (1, 1), (0, 0)))
    best = np.zeros(al.shape, np.int8)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sh = np.roll(np.roll(mp, dy, 0), dx, 1)
        take = (~al) & (best == 0) & (sh > 0)
        best[take] = sh[take]
    names = ['', 'hair', 'skin', 'gi', 'red', 'shoe']
    for i in range(1, 6):
        f, sd = OUTC[names[i]]
        out[best == i] = (*[int(v) for v in pal[f][sd]], 255)
    return out[1:-1, 1:-1]

if __name__ == "__main__":
    a = outline(*build())
    Image.fromarray(a).save(os.path.join(OUT, "fighter_v9.png"))
    im = Image.fromarray(a)
    bg = Image.new("RGBA", (W, H), (46, 50, 72, 255)); bg.alpha_composite(im)
    bg.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(OUT, "fighter_v9_x8.png"))
    sil = np.zeros_like(a); sil[a[..., 3] > 0] = (240, 240, 240, 255)
    sb = Image.new("RGBA", (W, H), (46, 50, 72, 255)); sb.alpha_composite(Image.fromarray(sil))
    sb.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(OUT, "fighter_v9_sil.png"))
    print("ok", a[..., 3].astype(bool).sum())