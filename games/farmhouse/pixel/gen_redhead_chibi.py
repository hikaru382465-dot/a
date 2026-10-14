"""
赤髪の女性（白シャツ・黒ネクタイ・黒いズボン・茶色の靴）のちびキャラ版。2頭身ぐらい、イカダ1マス（64×32のひし形）に立てる大きさ。
1コマ 24×36（身長33ドット）、足もとの基準＝下から4行目。前・後ろ・右・左を歩く（各4コマ）。左向きは右向きの反転。
python gen_redhead_chibi.py → assets/character/redhead_chibi_sheet.png / _walk.gif / _<向き>.gif / _preview.png（イカダに立てた大きさ比べ）
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "character")
pal, _ = pxl.load_palette()
W, H = 24, 36
FOOT = 32
def C(f, s): return tuple(int(v) for v in pal[f][int(max(0, min(7, s)))])
class Cv:
    def __init__(self): self.a = np.zeros((H, W, 4), np.uint8)
    def p(self, x, y, f, s):
        x, y = int(x), int(y)
        if 0 <= x < W and 0 <= y < H: self.a[y, x] = (*C(f, s), 255)
    def rect(self, x0, y0, x1, y1, f, s):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): self.p(x, y, f, s)

KEY = {'R': ('r', 4), 'h': ('r', 5), 'r': ('r', 3), 'o': ('r', 1), 'S': ('k', 5), 's': ('k', 4), 'b': ('k', 3), 'm': ('k', 2),
       'E': ('r', 0), 'e': ('H', 5), 'q': ('H', 3), 'W': ('k', 7), 'N': ('k', 3)}
FRONT = [
 "...oorrrroo...",
 ".orRRhhhhRRro.",
 "orRRhhhhhhRRro",
 "orRRRRRRRRRRro",
 "orRRSRRRRSRRro",
 "orRSSSSSSSSRro",
 "orRSEESSEESRro",
 "orRSWeSSWeSRro",
 "orRSqqSSqqSRro",
 "orRbSSSSSSbRro",
 ".orRSSmmSSRro.",
 "..orRSSSSRro..",
 "...ooRssRoo...",
]
BACK = [
 "...oorrrroo...",
 ".orRRhhhhRRro.",
 "orRRhhhhhhRRro",
 "orRRRRhhRRRRro",
 "orRRRRRRRRRRro",
 "orRRRRRRRRRrro",
 "orRRRRRRRRrrro",
 "orRRRRRRRRrrro",
 "orRRRRRRRRrrro",
 "orRRRRRRRRrrro",
 ".orRRRRRRrrro.",
 "..orRRRRrrro..",
 "...oorrrroo...",
]
SIDE = [
 "..oorrrrrroo..",
 ".orRRhhhhRRRo.",
 "orRRhhhhRRRRRo",
 "orRRRRRRRRRRRo",
 "orRRRRRRRRRSSo",
 "orRRRRRRRRSSSo",
 "orRRRRRRRSEESo",
 "orRRRRRRRSWeSo",
 "orRRRRRRRSqqSo",
 "orRRRRRRRRbSSo",
 ".orRRRRRrrSmo.",
 "..orRRRrrsSo..",
 "...oorrrrooo..",
]
def head(cv, grid, x0, y0):
    for j, row in enumerate(grid):
        for i, ch in enumerate(row):
            if ch in KEY: cv.p(x0 + i, y0 + j, *KEY[ch])
def shade3(x, a, b):
    t = (x - a) / max(1, b - a); return 0 if t < .34 else 1 if t < .7 else 2
def shoe(cv, x, y, w=5, toe=0):
    for i in range(w):
        cv.p(x + i, y, 'D', 1); cv.p(x + i, y - 1, 'D', 3); cv.p(x + i, y - 2, 'D', 4 if i < 2 else 3)
    if toe: cv.p(x + (w - 1 if toe > 0 else 0), y - 2, 'D', 5)
    else: cv.p(x + 1, y - 2, 'D', 5)
def shadow(cv, cx=12, w=6):
    for x in range(cx - w, cx + w):
        if (x + FOOT) % 2 == 0: cv.p(x, FOOT + 1, 'T', 1)

def braid(cv, x, y, n=8, side=1):
    for k in range(n):
        seg = (k // 2) % 2; sh = 4 if k % 2 == 0 else 3
        for i, xx in enumerate((x, x + 1) if seg == 0 else ((x + 1, x + 2) if side > 0 else (x - 1, x))):
            cv.p(xx, y + k, 'r', sh + (1 if i == 0 and seg == 0 else -1 if i == 1 else 0))
    cv.rect(x, y + n, x + 1, y + n, 'T', 2); cv.p(x, y + n + 1, 'r', 3); cv.p(x + 1, y + n + 1, 'r', 2)

def legs(cv, top, ph, front=True):
    lift = {1: (1, 0), 3: (0, 1)}.get(ph, (0, 0))
    for side, (x0, lf) in enumerate(((8, lift[0]), (13, lift[1]))):
        for y in range(top + 22, FOOT - 2 - lf + 1):
            for x in range(x0, x0 + 3):
                s = 4 if (side == 0 and x == x0) else 2 if (side == 1 and x == x0 + 2) else 3
                cv.p(x, y, 'T', s)
        shoe(cv, x0 - 1 + side * 1, FOOT - lf, 4, 0)
    cv.p(11, top + 22, 'T', 1); cv.p(12, top + 22, 'T', 1)

def front(ph):
    cv = Cv(); bob = 1 if ph in (0, 2) else 0; top = bob; sw = {0: 0, 1: 1, 2: 0, 3: -1}[ph]
    legs(cv, top, ph)
    cv.rect(8, top + 21, 15, top + 21, 'T', 3); cv.rect(8, top + 21, 15, top + 21, 'T', 4)
    for y in range(top + 13, top + 21):
        for x in range(8, 16): cv.p(x, y, 's', [6, 5, 4][shade3(x, 8, 15)] - (1 if y > top + 18 else 0))
    cv.rect(11, top + 14, 12, top + 14, 'T', 3)
    for y in range(top + 15, top + 20): cv.rect(11, y, 12, y, 'T', 3); cv.p(12, y, 'T', 2)
    cv.p(11, top + 20, 'T', 2); cv.p(11, top + 13, 's', 7); cv.p(12, top + 13, 's', 6)
    for side in (0, 1):
        ax = 6 if side == 0 else 16; dy = sw * (1 if side == 0 else -1)
        for y in range(top + 14 + dy, top + 21 + dy): cv.p(ax, y, 's', 5 if side == 0 else 3); cv.p(ax + 1, y, 's', 4 if side == 0 else 3) if False else None
        cv.p(ax, top + 21 + dy, 'k', 5 if side == 0 else 3); cv.p(ax, top + 22 + dy, 'k', 4 if side == 0 else 3)
    head(cv, FRONT, 5, top - 0)
    for y in range(top + 12, top + 15):
        for x, s in ((5, 3), (6, 4), (17, 3), (18, 2)): cv.p(x, y, 'r', s)
    braid(cv, 19, top + 10, 7, 1)
    shadow(cv); return cv

def back(ph):
    cv = Cv(); bob = 1 if ph in (0, 2) else 0; top = bob; sw = {0: 0, 1: 1, 2: 0, 3: -1}[ph]
    legs(cv, top, ph, False)
    cv.rect(8, top + 21, 15, top + 21, 'T', 4)
    for y in range(top + 13, top + 21):
        for x in range(8, 16): cv.p(x, y, 's', [5, 4, 3][shade3(x, 8, 15)])
    for y in range(top + 14, top + 19): cv.p(11, y, 's', 3)
    for side in (0, 1):
        ax = 6 if side == 0 else 16; dy = sw * (-1 if side == 0 else 1)
        for y in range(top + 14 + dy, top + 21 + dy): cv.p(ax, y, 's', 5 if side == 0 else 3)
        cv.p(ax, top + 21 + dy, 'k', 5 if side == 0 else 3); cv.p(ax, top + 22 + dy, 'k', 4 if side == 0 else 3)
    head(cv, BACK, 5, top)
    for x in (9, 10, 13, 14): cv.p(x, top + 13, 'r', 3 if x < 12 else 2)
    braid(cv, 3, top + 10, 7, -1)
    shadow(cv); return cv

def side(ph, arms=True):
    cv = Cv(); bob = 1 if ph in (0, 2) else 0; top = bob
    spread = {0: (2, -2), 1: (0, 0), 2: (-2, 2), 3: (0, 0)}[ph]; lift = {1: (0, 1), 3: (1, 0)}.get(ph, (0, 0))
    for (off, lf, sh) in ((spread[1], lift[1], 2), (spread[0], lift[0], 4)):
        for y in range(top + 22, FOOT - 2 - lf + 1):
            t = (y - (top + 22)) / max(1, FOOT - 2 - (top + 22)); cx = 9 + int(round(off * t))
            for x in range(cx, cx + 4): cv.p(x, y, 'T', 3 if sh == 4 else 2 if x > cx else 1)
        shoe(cv, 8 + off, FOOT - lf, 6, 1)
    cv.rect(9, top + 21, 15, top + 21, 'T', 4)
    for y in range(top + 13, top + 21):
        for x in range(9, 16): cv.p(x, y, 's', [6, 5, 4][shade3(x, 9, 15)])
    cv.p(15, top + 14, 's', 7)
    cv.rect(15, top + 14, 15, top + 19, 'T', 3)
    for armsh, sg in (((2, -1), (5, 1)) if arms else ()):
        sw_ = {0: 2, 1: 1, 2: -2, 3: -1}[ph] * sg
        for k in range(7):
            xx = 11 + int(round(sw_ * k / 6)); cv.p(xx, top + 14 + k, 's', armsh)
        cv.p(11 + sw_, top + 21, 'k', 4 if sg > 0 else 2)
    head(cv, SIDE, 6, top)
    braid(cv, 5, top + 10, 7, -1)
    shadow(cv); return cv

fr = {"down": [front(i).a for i in range(4)], "up": [back(i).a for i in range(4)], "right": [side(i).a for i in range(4)]}
fr["left"] = [np.ascontiguousarray(f[:, ::-1]) for f in fr["right"]]
order = ["down", "left", "right", "up"]
sheet = np.zeros((H * 4, W * 4, 4), np.uint8)
for r, d in enumerate(order):
    for c, f in enumerate(fr[d]): sheet[r * H:(r + 1) * H, c * W:(c + 1) * W] = f
Image.fromarray(sheet).save(os.path.join(OUT, "redhead_chibi_sheet.png"))
BG = (58, 84, 62, 255); K = 10
def bg(f, k=K):
    im = Image.new("RGBA", (W, H), BG); im.alpha_composite(Image.fromarray(f)); return im.resize((W * k, H * k), Image.NEAREST).convert("RGB")
for d in order:
    g = [bg(f) for f in fr[d]]; g[0].save(os.path.join(OUT, f"redhead_chibi_{d}.gif"), save_all=True, append_images=g[1:], duration=150, loop=0)
g = []
for i in range(4):
    row = Image.new("RGB", (W * K * 4, H * K))
    for j, d in enumerate(order): row.paste(bg(fr[d][i]), (j * W * K, 0))
    g.append(row)
g[0].save(os.path.join(OUT, "redhead_chibi_walk.gif"), save_all=True, append_images=g[1:], duration=150, loop=0)
# 大きさ比べ：イカダ1マスに立つ（原寸の4倍）と、4方向×2コマ
raft = Image.open(os.path.join(HERE, "sprites", "raft_tile.png")).convert("RGBA")
sea = Image.new("RGBA", (raft.width + 40, raft.height + 40), (22, 52, 78, 255)); sea.alpha_composite(raft, (20, 30))
cx, cy = 20 + 33, 30 + 17                                         # 上面のひし形の中心
for j, d in enumerate(("down",)):
    sp = Image.fromarray(fr[d][0]); sea.alpha_composite(sp, (cx - W // 2, cy - FOOT + 2))
sea = sea.resize((sea.width * 6, sea.height * 6), Image.NEAREST).convert("RGB")
pv = Image.new("RGB", (max(sea.width, W * K * 4), sea.height + H * K * 2 + 10), (40, 60, 44))
pv.paste(sea, (0, 0))
for j, d in enumerate(order):
    pv.paste(bg(fr[d][0]), (j * W * K, sea.height + 10)); pv.paste(bg(fr[d][1]), (j * W * K, sea.height + 10 + H * K)) if False else None
pv.save(os.path.join(OUT, "redhead_chibi_preview.png"))
print("ok")
