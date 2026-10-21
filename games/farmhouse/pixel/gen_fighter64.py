"""
武闘家の女の子 64×80 V2「羽織がなびく・片腕を高く上げ、もう片腕は前へ構える」立ち絵。python gen_fighter64.py
→ assets/character/fighter64_v4.png / fighter64_v4_x8.png / fighter64_v4_sil.png
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
    'b0': ('z', 0), 'b2': ('z', 2), 'b3': ('z', 3), 'b4': ('z', 4), 'b5': ('z', 5),     # 羽織（青）
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
cape = polymask([(38, 28), (45, 28), (51, 34), (57, 42), (62, 52), (62, 62), (62, 69), (61, 74), (58, 68), (56, 75), (54, 69), (53, 73),
                 (54, 64), (50, 56), (46, 48), (42, 40), (40, 34)])
put(cape, 'b3', 'haori')
O = (37, 28)
def sector(p, q, tok):
    poly([O, p, q], tok, 'haori', cape)
sector((45, 28), (51, 34), 'b4'); sector((51, 34), (57, 42), 'b2'); sector((57, 42), (62, 52), 'b3')
sector((62, 52), (62, 62), 'b4'); sector((62, 62), (61, 74), 'b2'); sector((61, 74), (56, 75), 'b3'); sector((56, 75), (53, 73), 'b2')
poly([(46, 28), (51, 33), (52, 35), (47, 29)], 'b5', 'haori', cape)          # 暗い面のすぐ隣に、明るい細い面
poly([(60, 50), (62, 55), (62, 57), (60, 54)], 'b5', 'haori', cape)
# すそのぎざぎざ：切れこみから上へ、暗いひだの折れ目（3段）
line((58, 68), (57, 58), 'b0', 'haori', cape); line((54, 69), (54, 60), 'b0', 'haori', cape); line((60, 66), (61, 60), 'b0', 'haori', cape)
poly([(55, 62), (59, 62), (58, 68), (56, 67)], 'b2', 'haori', cape)
poly([(50, 62), (54, 62), (54, 69), (51, 67)], 'b2', 'haori', cape)
poly([(38, 36), (44, 40), (48, 52), (44, 46), (40, 42)], 'b2', 'haori', cape)  # 体の後ろの影

# =====================================================================
# 2) 脚・靴
# =====================================================================
mL = polymask([(23, 53), (33, 53), (31, 62), (24, 73), (11, 73), (16, 62)])
mR = polymask([(32, 53), (41, 53), (46, 62), (50, 73), (38, 73), (32, 62)])
put(mL, 'w7', 'gi'); put(mR, 'w5', 'gi')
poly([(33, 55), (34, 55), (31, 62), (27, 73), (21, 73), (27, 63)], 'w3', 'gi', mL)         # 左脚：股からひざへ外向きの影（左どなりは最も明るい白）
poly([(33, 55), (34, 55), (33, 62), (30, 73), (27, 73), (31, 62)], 'w5', 'gi', mL)
poly([(33, 56), (36, 56), (46, 66), (50, 73), (44, 73), (36, 65)], 'w3', 'gi', mR)         # 右脚：股からひざへ外向きの影
poly([(32, 56), (34, 56), (41, 66), (43, 73), (40, 73), (35, 65)], 'w7', 'gi', mR)         # 影のすぐ隣は最も明るい白
poly([(32, 53), (41, 53), (43, 57), (36, 58), (34, 62)], 'w7', 'gi', mR)
# 靴：12列×4行（格子）。右向き、つま先は右下が丸い。B=明るい茶 M=中の茶 d=暗い茶の底
SHOE = ["..BBBBBB....",
        ".BMMMMMMMM..",
        ".MMMMMMMMMMM",
        ".ddddddddddd"]
SK_ = {'B': ('s6', 'shoe'), 'M': ('s5', 'shoe'), 'd': ('s3', 'shoe')}
grid(12, 74, SHOE, SK_, 'shoe'); grid(38, 74, SHOE, SK_, 'shoe')

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

# =====================================================================
# 3) 胴（道着）・えり・帯・羽織の見返し
# =====================================================================
torso = polymask([(23, 31), (27, 28), (36, 28), (40, 32), (39, 50), (23, 50)])
put(torso, 'w7', 'gi')
poly([(31, 36), (40, 32), (39, 50), (30, 50)], 'w5', 'gi', torso)
poly([(23, 46), (39, 46), (39, 50), (23, 50)], 'w5', 'gi', torso)
poly([(27, 30), (31, 30), (41, 42), (41, 48), (37, 47)], 'w3', 'gi', torso)                  # 左肩から帯の右へ、灰青の斜めの大きな面
poly([(24, 40), (28, 38), (28, 44), (24, 47)], 'w5', 'gi', torso)
poly([(26, 30), (33, 30), (38, 36), (34, 38), (28, 34)], 'w3', 'gi', torso)
poly([(28, 28), (34, 28), (31, 37)], 'k5', 'skin')
poly([(32, 28), (34, 28), (31, 37)], 'k3', 'skin')
line((27, 28), (31, 38), 'b0', 'gi'); line((36, 28), (31, 38), 'b0', 'gi')
poly([(22, 49), (41, 49), (41, 56), (22, 56)], 'r4', 'red')
poly([(22, 49), (41, 49), (41, 50), (22, 50)], 'r6', 'red')
poly([(22, 54), (41, 54), (41, 56), (22, 56)], 'r2', 'red')
poly([(38, 31), (41, 33), (42, 48), (40, 49)], 'b3', 'haori')
poly([(38, 31), (39, 31), (40, 49), (39, 49)], 'b4', 'haori')

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
put(polymask([(28, 26), (33, 26), (33, 32), (28, 32)]), 'k3', 'skin')
cap = (((xx - 29.5) / 13.7) ** 2 + ((yy - 14.5) / 12.6) ** 2 <= 1.0) & (yy <= 21)
put(cap, 'h3', 'hair')
put(edge_br(cap, 3), 'h2', 'hair', cap); put(edge_br(cap, 1), 'h1', 'hair', cap)
put(edge_tl(cap, 3) & (xx < 31) & (yy < 14), 'h6', 'hair', cap)
line((26, 3), (20, 11), 'h3', 'hair', T == ID['h6']); line((27, 3), (21, 11), 'h3', 'hair', T == ID['h6'])
line((30, 4), (27, 10), 'h2', 'hair', T == ID['h3']); line((36, 4), (35, 11), 'h2', 'hair', T == ID['h3'])
poly([(17, 18), (21, 18), (21, 27), (19, 30), (17, 25)], 'h2', 'hair')
poly([(38, 18), (42, 18), (42, 25), (40, 30), (38, 27)], 'h1', 'hair')
poly([(17, 18), (18, 18), (18, 24), (17, 23)], 'h3', 'hair')

FACE_KEY = {'h': ('h3', 'hair'), 'g': ('h2', 'hair'), 'o': ('h1', 'hair'), 'H': ('h6', 'hair'),
            's': ('k5', 'skin'), 't': ('k3', 'skin'),
            'e': ('h1', 'hair'), 'w': ('w7', 'gi'), 'W': ('w7', 'gi'), 'i': ('b3', 'haori'), 'I': ('b4', 'haori'),
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
def widen(r): return r[:9] + r[8] + r[9] + r[9:]
F2 = list(FACE); F2[3] = F2[3].replace('ssss', 'tttt')
rows = [F2[k] for k in range(10)]
rows += [F2[9].replace('W', 'n').replace('e', 's'), F2[10].replace('e', 's'), F2[10].replace('I', 'i').replace('e', 's')] + F2[11:]
FACE20 = [widen(r) for r in rows]
assert len(FACE20) == 18 and all(len(r) == 20 for r in FACE20)
def R20(*p):
    r = "".join(p); assert len(r) == 20, (len(r), r); return r
for k in (5, 6): FACE20[k] = FACE20[k].replace('b', 'o')                                     # 眉を濃く
# 目の格子（左目7列×6行。右目は左右反転し、光は同じ左上に置き直す）。o=まぶた W=白目 b=暗い青 B=明るい青 w=光 s=肌の影
EYE_L = ["ooooooo", "oWbbbbo", "WbwwbBb", ".WbbBBb", "..bBBBb", "..ssss."]
EYE_R = ["ooooooo", "obbbbWo", "bwwbBbW", "bBBbbW.", "bBBBb..", ".ssss.."]
FACE20[7] = R20('hh', 's' * 16, 'hg')
for k in range(6):
    FACE20[8 + k] = R20('hh', EYE_L[k].replace('.', 's'), 'ss', EYE_R[k].replace('.', 's'), 'hg')
FACE_KEY['b'] = ('b2', 'haori'); FACE_KEY['B'] = ('b3', 'haori'); FACE_KEY['W'] = ('w7', 'gi'); FACE_KEY['w'] = ('w7', 'gi')
grid(20, 11, FACE20, FACE_KEY, 'skin')

# ---- ポニーテール（高い位置から右へ大きくなびく）。面：明るい筋・ふつう・暗い下がわ
CP = [(41, 8, 3), (46, 4.5, 4), (52, 6, 4.5), (56, 12, 4.4), (57, 19, 3.8), (56, 25, 2.6), (55, 29, 1.2), (54.5, 31, 0.5)]
def pony_path(off):
    pts = []
    for (x0, y0, r0), (x1, y1, r1) in zip(CP[:-1], CP[1:]):
        for t in np.linspace(0, 1, 6)[:-1]:
            pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r0 + (r1 - r0) * t))
    out = []
    for k, (x, y, r) in enumerate(pts):
        a = pts[min(k + 1, len(pts) - 1)]; b = pts[max(k - 1, 0)]
        dx, dy = a[0] - b[0], a[1] - b[1]; n = (dx * dx + dy * dy) ** .5 or 1
        nx, ny = dy / n, -dx / n
        if nx + ny > 0: nx, ny = -nx, -ny
        out.append((x + nx * r * off, y + ny * r * off, r))
    return out
pony = np.zeros((H, W), bool)
for x, y, r in pony_path(0):
    pony |= ((xx - x) ** 2 + (yy - y) ** 2 <= (r + .3) ** 2)
put(pony, 'h3', 'hair')
put(edge_br(pony, 2), 'h2', 'hair', pony); put(edge_br(pony, 1), 'h1', 'hair', pony)
for off, tok in ((-.55, 'h6'), (0.0, 'h2'), (.5, 'h2')):            # 曲がりにそった3本の筋（強すぎない色）
    for (x0, y0, r0), (x1, y1, r1) in zip(pony_path(off)[:-1], pony_path(off)[1:]):
        if r0 > 1.5: put(mk(lambda d: d.line([(x0, y0), (x1, y1)], fill=255, width=1)), tok, 'hair', pony & (T != ID['h1']))
# 髪と羽織のあいだに暗い縁を1列
ringp = (shift(pony, 1, 0) | shift(pony, -1, 0) | shift(pony, 0, 1) | shift(pony, 0, -1)) & ~pony & (M == MATS.index('haori'))
put(ringp, 'h1', 'hair')
# 髪どめ（赤）
FR = {'P': ('r6', 'red'), 'r': ('r4', 'red'), 'R': ('r2', 'red')}
grid(39, 7, ["PPr.", "PrrR", ".rRR"], FR, 'red')

# ---- 帯の結び目（左腰）とたれ端2本
grid(17, 48, [
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
    (47, 56, 0, 2, 'h6', 'hair'),
    (44, 52, 24, 27, 'b4', 'haori'),
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
    im = Image.fromarray(a); im.save(os.path.join(OUT, "fighter64_v4.png"))
    bg = Image.new("RGBA", (W, H), (46, 50, 72, 255)); bg.alpha_composite(im)
    bg.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(OUT, "fighter64_v4_x8.png"))
    sil = np.zeros_like(a); sil[a[..., 3] > 0] = (240, 240, 240, 255)
    sb = Image.new("RGBA", (W, H), (46, 50, 72, 255)); sb.alpha_composite(Image.fromarray(sil))
    sb.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(OUT, "fighter64_v4_sil.png"))

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
