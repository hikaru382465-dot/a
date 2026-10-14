"""
金髪ボブの女の子（赤い制服・灰色のプリーツスカート・紺のリボン・黒いハイソックス・茶色のローファー）のちびキャラ。
2頭身、イカダ1マスに立てる大きさ（24×36、身長33ドット）。前・後ろ・右・左を歩く（各4コマ）。左向きは右向きの反転。
python gen_blonde_chibi.py → assets/character/blonde_chibi_sheet.png / _walk.gif / _<向き>.gif / _preview.png
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
KEY = {'N': ('n', 5), 'h': ('n', 7), 'n': ('n', 4), 'o': ('n', 2), 'S': ('k', 5), 's': ('k', 4), 'b': ('k', 3), 'M': ('u', 2),
       'E': ('n', 1), 'e': ('u', 5), 'q': ('u', 4), 'W': ('k', 7), 'B': ('u', 5), 'v': ('u', 3)}
FRONT = ["...oonnnnBBBv.", ".onNNhhNNBBvo.", "onNNNhhNNNNnno", "onNNNNNNNNNNno", "onNNSNNNNNSNno", "onNSSSSSSSSNno",
         "onNSEESSEESNno", "onNSWeSSWeSNno", "onNSqqSSqqSNno", "onNbSSSSSSbNno", ".onNSSMMSSNno.", "..onNSSSSNno..", "...oonNNnoo..."]
BACK = ["...oonnnnBBBv.", ".onNNhhNNBBvo.", "onNNNhhNNNNnno", "onNNNNNNNNNNno", "onNNNNNNNNNnnno"[:14], "onNNNNNNNNNnno",
        "onNNNNNNNNnnno", "onNNNNNNNNnnno", "onNNNNNNNNnnno", "onNNNNNNNNnnno", ".onNNNNNNnnno.", "..onNNNNnnno..", "...oonnnnoo..."]
SIDE = ["..oonnnnnBBBv.", ".onNNhhNNNBBvo", "onNNhhhNNNNNno", "onNNNNNNNNNNno", "onNNNNNNNNNSSo", "onNNNNNNNNSSSo",
        "onNNNNNNNSEESo", "onNNNNNNNSWeSo", "onNNNNNNNSqqSo", "onNNNNNNNNbSSo", ".onNNNNNnnSMo.", "..onNNNNnnSso.", "...oonnnnooo.."]
for g in (FRONT, BACK, SIDE):
    for i, r in enumerate(g): g[i] = (r + "." * 14)[:14]
def head(cv, grid, x0, y0):
    for j, row in enumerate(grid):
        for i, ch in enumerate(row):
            if ch in KEY: cv.p(x0 + i, y0 + j, *KEY[ch])
def sh3(x, a, b):
    t = (x - a) / max(1, b - a); return 0 if t < .34 else 1 if t < .7 else 2
def shoe(cv, x, y, w=4, toe=0):
    for i in range(w):
        cv.p(x + i, y, 'D', 1); cv.p(x + i, y - 1, 'D', 3); cv.p(x + i, y - 2, 'D', 4 if i < 2 else 3)
    if toe: cv.p(x + (w - 1 if toe > 0 else 0), y - 2, 'D', 5)
    else: cv.p(x + 1, y - 2, 'D', 5)
def shadow(cv):
    for x in range(6, 18):
        if (x + FOOT) % 2 == 0: cv.p(x, FOOT + 1, 'T', 1)

def legs(cv, top, ph, side_view=False):
    lift = {1: (1, 0), 3: (0, 1)}.get(ph, (0, 0))
    for side, (x0, lf) in enumerate(((8, lift[0]), (13, lift[1]))):
        for y in range(top + 25, FOOT - 2 - lf + 1):
            for x in range(x0, x0 + 3):
                if y < top + 27: cv.p(x, y, 'k', 5 if x == x0 else 4)       # 膝上のはだ
                else: cv.p(x, y, 'T', 3 if x == x0 else 2)                  # 黒いハイソックス
        shoe(cv, x0 - 1 + side, FOOT - lf, 4, 0)
def skirt(cv, top, sway=0, front=True, back=False):
    rows = [(7, 16), (6, 17), (6, 17), (5, 18), (5, 18)]
    for k, (a, b) in enumerate(rows):
        y = top + 20 + k
        sw = sway if k >= 3 else 0
        for x in range(a + sw, b + 1 + sw):
            pleat = (x - a) % 3 == 0
            s = [5, 4, 3][sh3(x, a, b)] - (1 if pleat else 0)
            if front and 10 <= x <= 13: cv.p(x, y, 'u', 4 - (1 if x == 13 else 0))        # 前の赤いパネル
            else: cv.p(x, y, 'g', s)
        cv.p(a + sw, y, 'g', 2); cv.p(b + sw, y, 'g', 3)
def torso(cv, top, front=True, back=False, side=False):
    x0, x1 = (8, 15) if not side else (9, 15)
    for y in range(top + 13, top + 19):
        for x in range(x0, x1 + 1): cv.p(x, y, 'u', [5, 4, 3][sh3(x, x0, x1)])
    cv.rect(x0, top + 19, x1, top + 19, 'u', 2); cv.p(11 if not side else 12, top + 19, 'b', 6)         # ベルト
    if front:
        for x in range(9, 15): cv.p(x, top + 13, 's', 6)                                                  # えり
        cv.rect(11, top + 13, 12, top + 14, 'a', 4); cv.p(10, top + 15, 'a', 3); cv.p(13, top + 15, 'a', 3)  # 紺のリボン
        for y in (top + 16, top + 18): cv.p(12, y, 'b', 6)                                                # ボタン
    elif back:
        for x in range(9, 15): cv.p(x, top + 13, 's', 5)
    else:
        for x in range(10, 15): cv.p(x, top + 13, 's', 6)
        cv.p(15, top + 14, 'a', 4)
def arms(cv, top, ph, front=True):
    sw = {0: 0, 1: 1, 2: 0, 3: -1}[ph]
    for side in (0, 1):
        ax = 7 if side == 0 else 16; dy = sw * (1 if side == 0 else -1) * (1 if front else -1)
        for y in range(top + 14 + dy, top + 20 + dy): cv.p(ax, y, 'u', 5 if side == 0 else 3)
        cv.p(ax, top + 20 + dy, 'k', 5 if side == 0 else 3); cv.p(ax, top + 21 + dy, 'k', 4 if side == 0 else 3)

def front(ph):
    cv = Cv(); bob = 1 if ph in (0, 2) else 0; top = bob
    legs(cv, top, ph); skirt(cv, top, {1: 1, 3: -1}.get(ph, 0), True); torso(cv, top); arms(cv, top, ph, True)
    head(cv, FRONT, 5, top); shadow(cv); return cv
def back(ph):
    cv = Cv(); bob = 1 if ph in (0, 2) else 0; top = bob
    legs(cv, top, ph); skirt(cv, top, {1: -1, 3: 1}.get(ph, 0), False, True); torso(cv, top, False, True); arms(cv, top, ph, False)
    head(cv, BACK, 5, top); shadow(cv); return cv
def side(ph, arms_on=True):
    cv = Cv(); bob = 1 if ph in (0, 2) else 0; top = bob
    spread = {0: (2, -2), 1: (0, 0), 2: (-2, 2), 3: (0, 0)}[ph]; lift = {1: (0, 1), 3: (1, 0)}.get(ph, (0, 0))
    for (off, lf, sh) in ((spread[1], lift[1], 2), (spread[0], lift[0], 4)):
        for y in range(top + 25, FOOT - 2 - lf + 1):
            t = (y - (top + 25)) / max(1, FOOT - 2 - (top + 25)); cx = 10 + int(round(off * t))
            for x in range(cx, cx + 3):
                if y < top + 27: cv.p(x, y, 'k', 5 if sh == 4 else 3)
                else: cv.p(x, y, 'T', 3 if sh == 4 else 2)
        shoe(cv, 9 + off, FOOT - lf, 5, 1)
    for k, (a, b) in enumerate([(8, 16), (7, 17), (7, 17), (6, 18), (6, 18)]):
        y = top + 20 + k
        for x in range(a, b + 1): cv.p(x, y, 'g', [5, 4, 3][sh3(x, a, b)] - (1 if (x - a) % 3 == 0 else 0))
    torso(cv, top, False, False, True)
    if arms_on:
        for armsh, sg in ((2, -1), (4, 1)):
            sw_ = {0: 2, 1: 1, 2: -2, 3: -1}[ph] * sg
            for k in range(7): cv.p(11 + int(round(sw_ * k / 6)), top + 14 + k, 'u', armsh)
            cv.p(11 + sw_, top + 21, 'k', 4 if sg > 0 else 2)
    head(cv, SIDE, 6, top); shadow(cv); return cv

if __name__ == "__main__":
    fr = {"down": [front(i).a for i in range(4)], "up": [back(i).a for i in range(4)], "right": [side(i).a for i in range(4)]}
    fr["left"] = [np.ascontiguousarray(f[:, ::-1]) for f in fr["right"]]
    order = ["down", "left", "right", "up"]
    sheet = np.zeros((H * 4, W * 4, 4), np.uint8)
    for r, d in enumerate(order):
        for c, f in enumerate(fr[d]): sheet[r * H:(r + 1) * H, c * W:(c + 1) * W] = f
    Image.fromarray(sheet).save(os.path.join(OUT, "blonde_chibi_sheet.png"))
    BG = (58, 84, 62, 255); K = 10
    def bg(f, k=K):
        im = Image.new("RGBA", (W, H), BG); im.alpha_composite(Image.fromarray(f)); return im.resize((W * k, H * k), Image.NEAREST).convert("RGB")
    for d in order:
        g = [bg(f) for f in fr[d]]; g[0].save(os.path.join(OUT, f"blonde_chibi_{d}.gif"), save_all=True, append_images=g[1:], duration=150, loop=0)
    g = []
    for i in range(4):
        row = Image.new("RGB", (W * K * 4, H * K))
        for j, d in enumerate(order): row.paste(bg(fr[d][i]), (j * W * K, 0))
        g.append(row)
    g[0].save(os.path.join(OUT, "blonde_chibi_walk.gif"), save_all=True, append_images=g[1:], duration=150, loop=0)
    raft = Image.open(os.path.join(HERE, "sprites", "raft_tile.png")).convert("RGBA")
    sea = Image.new("RGBA", (raft.width + 40, raft.height + 40), (22, 52, 78, 255)); sea.alpha_composite(raft, (20, 30))
    sea.alpha_composite(Image.fromarray(fr["down"][0]), (20 + 33 - W // 2, 30 + 17 - FOOT + 2))
    sea = sea.resize((sea.width * 6, sea.height * 6), Image.NEAREST).convert("RGB")
    pv = Image.new("RGB", (W * K * 4, sea.height + H * K + 10), (40, 60, 44)); pv.paste(sea, (0, 0))
    for j, d in enumerate(order): pv.paste(bg(fr[d][0]), (j * W * K, sea.height + 10))
    pv.save(os.path.join(OUT, "blonde_chibi_preview.png")); print("ok")
