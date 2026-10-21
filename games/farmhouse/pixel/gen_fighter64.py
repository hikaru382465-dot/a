"""
武闘家の女の子 64×80 V2「羽織がなびく・片腕を高く上げ、もう片腕は前へ構える」立ち絵。python gen_fighter64.py
→ assets/character/fighter64_v1.png / fighter64_v1_x8.png / fighter64_v1_sil.png
やり方：多角形で「明・中・暗」の大きな面を作る（光は左上）→ 顔・拳・帯の結び目は文字の格子で1ドットずつ →
素材ごとの濃い色で縁取り（np.pad→roll）→ ところどころ縁取りを切って明るくする。乱数なし。
色は palette.json の系統×明るさだけ（20色）。
"""
import os
import numpy as np
from PIL import Image, ImageDraw
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "character"); os.makedirs(OUT, exist_ok=True)
pal, _ = pxl.load_palette()
W, H = 64, 80

TOK = {
    'h1': ('a', 1), 'h2': ('a', 2), 'h3': ('a', 3), 'h6': ('a', 6),                     # 髪（紺）
    'b0': ('z', 0), 'b2': ('z', 2), 'b3': ('z', 3), 'b5': ('z', 5), 'b7': ('z', 7),     # 羽織（青）
    'w7': ('s', 7), 'w5': ('s', 5), 'w3': ('S', 4),                                     # 道着（白・灰白・青灰）
    'k3': ('A', 4), 'k5': ('A', 6),                                     # 肌
    'r2': ('G', 2), 'r4': ('G', 4), 'r6': ('G', 6),                                     # 赤（手甲・帯）
    's3': ('D', 3), 's5': ('D', 5), 's6': ('D', 6),                                                     # 靴
}
NAMES = list(TOK); ID = {n: i + 1 for i, n in enumerate(NAMES)}
MATS = ['', 'hair', 'skin', 'gi', 'haori', 'red', 'shoe']
OUTC = {'hair': 'h1', 'skin': 'r2', 'gi': 'b0', 'haori': 'b0', 'red': 'r2', 'shoe': 'h1'}

T = np.zeros((H, W), np.int16); M = np.zeros((H, W), np.int8)
yy, xx = np.mgrid[0:H, 0:W]

def mk(fn):
    im = Image.new("L", (W, H), 0); fn(ImageDraw.Draw(im)); return np.array(im) > 0
def put(mask, tok, mat, clip=None):
    if clip is not None: mask = mask & clip
    T[mask] = ID[tok]; M[mask] = MATS.index(mat)
def polymask(pts): return mk(lambda d: d.polygon(pts, fill=255))
def poly(pts, tok, mat, clip=None): put(polymask(pts), tok, mat, clip)
def shift(m, dx, dy):
    p = np.pad(m, 8); return np.roll(np.roll(p, dy, 0), dx, 1)[8:-8, 8:-8]
def edge_br(m, n): return m & ~shift(m, -n, -n)       # 右下のふち n ドット
def edge_tl(m, n): return m & ~shift(m, n, n)         # 左上のふち n ドット
def limbmask(pts, w):
    def f(d):
        for a, b in zip(pts[:-1], pts[1:]): d.line([a, b], fill=255, width=w)
        for p in pts: d.ellipse((p[0] - w / 2 + .5, p[1] - w / 2 + .5, p[0] + w / 2 - .5, p[1] + w / 2 - .5), fill=255)
    return mk(f)
def line(a, b, tok, mat, clip=None): put(mk(lambda d: d.line([a, b], fill=255, width=1)), tok, mat, clip)
def grid(x0, y0, rows, key, mat):
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == '.': continue
            tok, m = key[ch]
            T[y0 + j, x0 + i] = ID[tok]; M[y0 + j, x0 + i] = MATS.index(m)

FK = {'s': ('k5', 'skin'), 't': ('k3', 'skin'), 'u': ('k3', 'skin'), 'P': ('r6', 'red'), 'r': ('r4', 'red'), 'R': ('r2', 'red')}

# =====================================================================
# 1) 羽織：後ろへなびく大きな青い面（肩から放射する斜めのひだ）
# =====================================================================
cape = polymask([(38, 27), (44, 24), (52, 24), (58, 28), (61, 34), (61, 50), (59, 62), (55, 60), (53, 70), (48, 64), (45, 68),
                 (41, 58), (38, 50)])
put(cape, 'b3', 'haori')
O = (37, 28)
def sector(p, q, tok, bp=(0, 0), bq=(0, 0)):
    mid = lambda a, b: ((O[0] + a[0]) / 2 + b[0], (O[1] + a[1]) / 2 + b[1])
    poly([O, mid(p, bp), p, q, mid(q, bq)], tok, 'haori', cape)
sector((58, 28), (61, 36), 'b5', (0, 0), (0, 1))
sector((61, 36), (61, 46), 'b2', (0, 1), (0, 2))
sector((61, 46), (61, 56), 'b3', (0, 2), (0, 2))
sector((61, 56), (58, 63), 'b5', (0, 2), (1, 2))
sector((58, 63), (53, 71), 'b2', (1, 2), (2, 2))
sector((53, 71), (46, 69), 'b3', (2, 2), (1, 3))
sector((46, 69), (40, 56), 'b2', (1, 3), (0, 2))
poly([(46, 29), (61, 35), (61, 37), (46, 31)], 'b7', 'haori', cape)          # 暗い面のすぐ隣に最も明るい細い面
poly([(48, 44), (58, 62), (60, 61), (50, 43)], 'b7', 'haori', cape)
poly([(44, 24), (52, 24), (58, 28), (56, 28), (51, 25), (45, 25)], 'b5', 'haori', cape)
poly([(41, 58), (45, 68), (49, 64), (46, 58)], 'b0', 'haori', cape)           # すその折り返し（暗）
poly([(37, 40), (44, 38), (47, 52), (40, 54)], 'b2', 'haori', cape)           # 体の後ろの影

# =====================================================================
# 2) 脚・靴
# =====================================================================
mL = polymask([(23, 50), (33, 50), (31, 60), (27, 72), (10, 72), (16, 60)])
mR = polymask([(32, 50), (41, 50), (47, 60), (53, 72), (35, 72), (32, 60)])
put(mL, 'w7', 'gi'); put(mR, 'w5', 'gi')
poly([(28, 50), (34, 50), (31, 60), (27, 72), (19, 72), (24, 60)], 'w5', 'gi', mL)
poly([(31, 53), (34, 50), (31, 60), (27, 72), (24, 72), (28, 62)], 'w3', 'gi', mL)
poly([(32, 50), (41, 50), (45, 57), (38, 61), (34, 62)], 'w7', 'gi', mR)
poly([(41, 56), (47, 60), (53, 72), (45, 72), (43, 64)], 'w3', 'gi', mR)
poly([(36, 66), (43, 66), (45, 72), (35, 72)], 'w5', 'gi', mR)
put(polymask([(10, 69), (27, 69), (27, 72), (10, 72)]), 'w5', 'gi', mL)       # すそ（足首）
put(polymask([(10, 71), (27, 71), (27, 72), (10, 72)]), 'w3', 'gi', mL)
put(polymask([(35, 70), (53, 70), (53, 72), (35, 72)]), 'w3', 'gi', mR)
poly([(11, 72), (26, 72), (26, 77), (8, 77), (5, 75), (7, 73)], 's5', 'shoe')
poly([(11, 72), (26, 72), (26, 73), (9, 73), (7, 74), (7, 73)], 's6', 'shoe')
poly([(6, 76), (26, 76), (26, 77), (8, 77), (6, 76)], 's3', 'shoe')
poly([(36, 72), (52, 72), (58, 74), (58, 76), (55, 77), (36, 77)], 's5', 'shoe')
poly([(36, 72), (52, 72), (55, 73), (56, 74), (36, 73)], 's6', 'shoe')
poly([(36, 76), (54, 76), (54, 77), (36, 77)], 's3', 'shoe')

# =====================================================================
# 2.5) 高く上げたうで（胴より先に描き、肩を道着でおおう）
# =====================================================================
# 高く上げた腕：上うで→手甲→拳
rup = limbmask([(23, 32), (15, 26)], 7); put(rup, 'k3', 'skin'); put(rup & ~edge_br(rup, 2), 'k5', 'skin')
rfo = limbmask([(15, 26), (11, 15)], 7)
put(rfo, 'k3', 'skin'); put(rfo & ~edge_br(rfo, 2), 'k5', 'skin')
glove = rfo & (yy <= 21)
put(glove, 'r4', 'red'); put(edge_br(rfo, 2), 'r2', 'red', glove); put(edge_tl(rfo, 1), 'r6', 'red', glove)
put(polymask([(5, 20), (17, 22), (17, 23), (5, 21)]), 'r2', 'red', rfo); put(polymask([(5, 21), (17, 23), (17, 24), (5, 22)]), 'r6', 'red', rfo & ~glove | polymask([(5,21),(17,23),(17,24),(5,22)]) & rfo)
grid(6, 6, [
    "..ssssss.",
    ".sssssstt",
    "sssstsstt",
    "sssstsstt",
    "ssssssstt",
    ".tsssstt.",
    "..PPPPPr.",
    "..rrrrrR.",
], FK, 'skin')

# ひだ（面の中の大きな折れ目）
line((21, 56), (15, 68), 'w5', 'gi', T == ID['w7'])
line((37, 62), (41, 69), 'w7', 'gi', T == ID['w5'])

# =====================================================================
# 3) 胴（道着）・えり・帯・羽織の見返し
# =====================================================================
torso = polymask([(23, 31), (27, 28), (36, 28), (40, 32), (39, 47), (23, 47)])
put(torso, 'w7', 'gi')
poly([(31, 36), (40, 32), (39, 47), (30, 47)], 'w5', 'gi', torso)
poly([(35, 40), (40, 36), (39, 47), (34, 47)], 'w3', 'gi', torso)
poly([(23, 44), (39, 44), (39, 47), (23, 47)], 'w5', 'gi', torso)
poly([(24, 41), (30, 38), (30, 41), (24, 45)], 'w5', 'gi', torso)
poly([(28, 28), (34, 28), (31, 37)], 'k5', 'skin')
poly([(32, 28), (34, 28), (31, 37)], 'k3', 'skin')
line((27, 28), (31, 38), 'b0', 'gi'); line((36, 28), (31, 38), 'b0', 'gi')
poly([(22, 46), (41, 46), (41, 53), (22, 53)], 'r4', 'red')
poly([(22, 46), (41, 46), (41, 47), (22, 47)], 'r6', 'red')
poly([(22, 51), (41, 51), (41, 53), (22, 53)], 'r2', 'red')
poly([(38, 31), (41, 33), (42, 45), (40, 46)], 'b3', 'haori')
poly([(38, 31), (39, 31), (40, 46), (39, 46)], 'b5', 'haori')

# =====================================================================
# 4) うで
# =====================================================================
# 前に構えた腕：上うで→前腕(肌)→手甲(赤)→拳
up = limbmask([(38, 31), (40, 40)], 6); put(up, 'k3', 'skin'); put(up & ~edge_br(up, 2), 'k5', 'skin')
fo = limbmask([(39, 41), (30, 41)], 6); put(fo, 'k3', 'skin'); put(fo & shift(fo, 0, -2), 'k5', 'skin')
poly([(20, 37), (30, 38), (30, 45), (20, 46)], 'r4', 'red')
poly([(20, 37), (30, 38), (30, 39), (20, 38)], 'r6', 'red')
poly([(20, 44), (30, 44), (30, 45), (20, 46)], 'r2', 'red')
grid(12, 37, [
    ".ssssss.",
    "ssssssst",
    "sttsssst",
    "ssssssst",
    "sttsssst",
    ".tsssstt",
    "..tttuu.",
], FK, 'skin')

# =====================================================================
# 5) 頭：髪のかたまり → 首 → 顔（文字の格子）→ ポニーテール
# =====================================================================
put(polymask([(28, 25), (33, 25), (33, 31), (28, 31)]), 'k3', 'skin')
cap = (((xx - 29.5) / 12.7) ** 2 + ((yy - 15.5) / 11.8) ** 2 <= 1.0) & (yy <= 22)
put(cap, 'h3', 'hair')
put(edge_br(cap, 3), 'h2', 'hair', cap); put(edge_br(cap, 1), 'h1', 'hair', cap)
put(edge_tl(cap, 3) & (xx < 31) & (yy < 15), 'h6', 'hair', cap)
line((26, 4), (21, 12), 'h3', 'hair', T == ID['h6']); line((27, 4), (22, 12), 'h3', 'hair', T == ID['h6'])
line((30, 5), (27, 11), 'h2', 'hair', T == ID['h3']); line((35, 5), (34, 12), 'h2', 'hair', T == ID['h3'])
poly([(18, 19), (22, 19), (22, 27), (20, 30), (18, 25)], 'h2', 'hair')
poly([(37, 19), (41, 19), (41, 25), (39, 30), (37, 27)], 'h1', 'hair')
poly([(18, 19), (19, 19), (19, 24), (18, 23)], 'h3', 'hair')

FACE_KEY = {'h': ('h3', 'hair'), 'g': ('h2', 'hair'), 'o': ('h1', 'hair'), 'H': ('h6', 'hair'),
            's': ('k5', 'skin'), 't': ('k3', 'skin'),
            'e': ('h1', 'hair'), 'w': ('w7', 'gi'), 'W': ('w7', 'gi'), 'i': ('b3', 'haori'), 'I': ('b5', 'haori'),
            'b': ('h2', 'hair'), 'n': ('h3', 'hair'), 'm': ('r2', 'red'), 'c': ('r4', 'red')}
def R(*parts):
    r = "".join(parts); assert len(r) == 18, (len(r), r); return r
FACE = [
    R('hhh', 'HHH', 'h' * 10, 'gg'),
    R('hh', 'HH', 'h' * 12, 'gg'),
    R('h' * 8, 'ss', 'h' * 6, 'gg'),
    R('h' * 7, 'ssss', 'h' * 5, 'gg'),
    R('h' * 6, 'ssssss', 'h' * 4, 'gg'),
    R('h' * 5, 'bbb', 'ss', 'bbb', 'h' * 3, 'gg'),
    R('hh', 'ss', 'bb', 's' * 6, 'bb', 'ss', 'hg'),
    R('hh', 's', 'e', 'ssss', 'ss', 'ssss', 'e', 's', 'hg'),
    R('hh', 's', 'eeeee', 'ss', 'eeeee', 's', 'hg'),
    R('hh', 's', 'eWnne', 'ss', 'eWnne', 's', 'hg'),
    R('hh', 's', 'eiiIe', 'ss', 'eiiIe', 's', 'hg'),
    R('hh', 's', 'siiis', 'st', 'siiis', 's', 'hg'),
    R('ggg', 's' * 10, 'tt', 'ggg'),
    R('.ggg', 'sss', 'mmmm', 'sst', 'ggg.'),
    R('..ggg', 's' * 6, 'tt', 'ggg..'),
    R('...ggg', 'sssstt', 'ggg...'),
]
grid(21, 12, FACE, FACE_KEY, 'skin')

# ---- ポニーテール（高い位置から右へ大きくなびく）。面：明るい筋・ふつう・暗い下がわ
pony = polymask([(38, 7), (43, 2), (51, 1), (58, 4), (60, 10), (60, 20), (59, 29), (57, 22), (55, 15), (50, 10), (44, 12), (40, 13)])
put(pony, 'h3', 'hair')
put(edge_br(pony, 4), 'h2', 'hair', pony); put(edge_br(pony, 2), 'h1', 'hair', pony)
put(edge_tl(pony, 2) & (xx < 58), 'h6', 'hair', pony)
poly([(46, 5), (52, 4), (58, 9), (59, 18), (56, 12), (50, 8)], 'h6', 'hair', pony & ~edge_br(pony, 3))
line((50, 3), (55, 13), 'h3', 'hair', T == ID['h6']); line((55, 3), (58, 15), 'h3', 'hair', T == ID['h6'])
line((52, 12), (56, 20), 'h6', 'hair', T == ID['h3'])
# 髪どめ（赤）
FR = {'P': ('r6', 'red'), 'r': ('r4', 'red'), 'R': ('r2', 'red')}
grid(38, 7, ["PPr.", "PrrR", ".rRR"], FR, 'red')

# ---- 帯の結び目（左腰）とたれ端2本
grid(17, 45, [
    "..PPPPP..",
    ".PPrrrrR.",
    "PPrrRRrrR",
    "PrrRRRRrR",
    ".rrrRRrR.",
    "..RrrrR..",
    ".rrR..rrR",
    ".rrR..rrR",
    "rrR....rR",
    "rrR....rR",
    "rR.....RR",
    "rR......R",
    "R........",
], FR, 'red')

# =====================================================================
# 6) 縁取り（素材ごとの一番濃い色で1ドット。np.pad→roll）
# =====================================================================
def outline():
    al = np.pad(T > 0, 1); mp = np.pad(M, 1); tp = np.pad(T, 1)
    best = np.zeros(al.shape, np.int8)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sh = np.roll(np.roll(mp, dy, 0), dx, 1)
        take = (~al) & (best == 0) & (sh > 0); best[take] = sh[take]
    for i in range(1, len(MATS)):
        tp[best == i] = ID[OUTC[MATS[i]]]
    return tp[1:-1, 1:-1], (best[1:-1, 1:-1])

T2, ring = outline()
# ふちを切って明るくする：光の当たる左上の縁取りを、ところどころ明るい色に（プロの描き方）
def cut_rim(x0, x1, y0, y1, tok, mat_name):
    sel = (ring == MATS.index(mat_name)) & (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)
    T2[sel] = ID[tok]
RIM = [   # (x0,x1,y0,y1,tok,mat)：左上の縁取りを、ところどころ明るい色に
    (17, 25, 5, 13, 'h3', 'hair'), (30, 34, 2, 4, 'h6', 'hair'),
    (47, 57, 0, 2, 'h6', 'hair'), (60, 63, 6, 10, 'h3', 'hair'),
    (46, 56, 22, 24, 'b5', 'haori'),
    (8, 13, 4, 5, 'k5', 'skin'),
]
for r in RIM: cut_rim(*r)

KEEP = {(25, 21), (32, 21), (27, 22), (34, 22), (30, 23), (7, 11)}   # 光・鼻・ハイライトなど、わざと残す1ドット
DARK = ('h1', 'r2', 'b0')
def smooth(t):
    for _ in range(3):
        for y in range(H):
            for x in range(W):
                v = t[y, x]
                if v == 0 or (x, y) in KEEP or ring[y, x] > 0 or NAMES[v - 1] in DARK: continue
                nb = [t[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= y + dy < H and 0 <= x + dx < W]
                if v in nb: continue
                nb = [n for n in nb if n > 0 and NAMES[n - 1] not in DARK] or [n for n in nb if n > 0]
                if nb: t[y, x] = max(set(nb), key=nb.count)
smooth(T2)

def render(t):
    a = np.zeros((H, W, 4), np.uint8)
    for n, i in ID.items():
        f, s = TOK[n]; a[t == i] = (*[int(v) for v in pal[f][s]], 255)
    return a

def save(a):
    im = Image.fromarray(a); im.save(os.path.join(OUT, "fighter64_v1.png"))
    bg = Image.new("RGBA", (W, H), (46, 50, 72, 255)); bg.alpha_composite(im)
    bg.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(OUT, "fighter64_v1_x8.png"))
    sil = np.zeros_like(a); sil[a[..., 3] > 0] = (240, 240, 240, 255)
    sb = Image.new("RGBA", (W, H), (46, 50, 72, 255)); sb.alpha_composite(Image.fromarray(sil))
    sb.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(OUT, "fighter64_v1_sil.png"))

def lonely(t):
    out = []
    for y in range(H):
        for x in range(W):
            if t[y, x] == 0: continue
            nb = [t[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= y + dy < H and 0 <= x + dx < W]
            if t[y, x] not in nb: out.append((x, y, NAMES[t[y, x] - 1]))
    return out

if __name__ == "__main__":
    a = render(T2); save(a)
    print("dots", int((a[..., 3] > 0).sum()), "colors", len(set(map(tuple, a[a[..., 3] > 0][:, :3]))))
    print("lonely", [p for p in lonely(T2) if p[2] not in ('h1', 'r2', 'b0')])
