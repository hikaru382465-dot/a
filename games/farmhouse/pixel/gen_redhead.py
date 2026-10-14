"""
赤髪の女性（白シャツ・黒ネクタイ・黒い細身のズボン・茶色の革靴）の、小さなドット絵キャラ。前・後ろ・右・左を歩く（各4コマ）。
1コマ 32×52、身長約48ドット、足もとの基準＝下から2行目。左向きは右向きの左右反転。光は左上。
python gen_redhead.py → assets/character/redhead_sheet.png（4行×4列：下・左・右・上）, redhead_walk.gif（4方向ならべ）, redhead_<dir>.gif, redhead_preview.png（8倍）
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "character"); os.makedirs(OUT, exist_ok=True)
pal, _ = pxl.load_palette()
W, H = 32, 52
FOOT = 49                                              # 足の裏の行
def C(f, s): return tuple(int(v) for v in pal[f][int(max(0, min(7, s)))])

class Cv:
    def __init__(self): self.a = np.zeros((H, W, 4), np.uint8)
    def p(self, x, y, f, s):
        x, y = int(x), int(y)
        if 0 <= x < W and 0 <= y < H: self.a[y, x] = (*C(f, s), 255)
    def get(self, x, y): return self.a[y, x, 3] > 0
    def rect(self, x0, y0, x1, y1, f, s):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): self.p(x, y, f, s)

LEG = ('T', 3)

# ---------------------------------------------------------------- 頭（手で描く）  R=髪 h=ハイライト r=影 o=ふち S=肌 s=肌かげ e=目 E=まぶた m=口
FRONT_HEAD = [
 "...oorrrroo...",
 ".orRRhhhhRRro.",
 "orRRRhhhhRRRro",
 "orRRRRRRRRRRro",
 "orRRRRRRRRRRro",
 "orRSsRRrRRsSRro"[:14],
 "orRSSsRRsSSRro",
 "orRSEESSEESRro",
 "orRSeeSSeeSRro",
 "orRSSSSSSSSsro",
 ".orRSSSSSSsRo.",
 ".orRSSmmSSsRo.",
 "..orRsSSssRo..",
 "...orRssRro...",
]
BACK_HEAD = [
 "...oorrrroo...",
 ".orRRhhhhRRro.",
 "orRRRhhhhRRRro",
 "orRRRRRRRRRRro",
 "orRRRhRRRRRRro",
 "orRRRRRRRRRRro",
 "orRRRRRRRRRrro",
 "orRRRRRRRRRrro",
 "orRRRRRRRRrrro",
 "orRRRRRRRRrrro",
 ".orRRRRRRrrro.",
 ".orRRRRRrrrro.",
 "..orRRRrrrro..",
 "...oorrrroo...",
]
SIDE_HEAD = [
 "..oorrrrrroo..",
 ".orRRhhhhRRRo.",
 "orRRRhhhRRRRRo",
 "orRRRRRRRRRRRo",
 "orRRRRRRRRRRRo",
 "orRRRRRRRRRRSo",
 "orRRRRRRRRSSSo",
 "orRRRRRRRSSEeo",
 "orRRRRRRRSSSSo",
 "orRRRRRRRRSSSo",
 ".orRRRRRrsSsSo",
 ".orRRRRRrrSmo.",
 "..orRRRrrrsso.",
 "...oorrrrooo..",
]
KEY = {'R': ('r', 4), 'h': ('r', 5), 'r': ('r', 3), 'o': ('r', 1), 'S': ('k', 5), 's': ('k', 4), 'e': ('H', 5), 'E': ('r', 1), 'm': ('k', 2)}
def head(cv, grid, x0, y0, flip=False):
    for j, row in enumerate(grid):
        row = row[::-1] if flip else row
        for i, ch in enumerate(row):
            if ch in KEY: cv.p(x0 + i, y0 + j, *KEY[ch])

def shade_lr(x, x0, x1):                 # 左が明るい（0=明, 1=中, 2=暗）
    t = (x - x0) / max(1, x1 - x0); return 0 if t < .3 else 1 if t < .72 else 2

def shoe(cv, x, y, w=5, toe=0):
    """靴：くつ底1行・本体・つま先のかわ。toe=+1 右向き, -1 左向き, 0 正面"""
    for i in range(w):
        cv.p(x + i, y, 'D', 1)
        cv.p(x + i, y - 1, 'D', 3 if i < w - 1 else 4); cv.p(x + i, y - 2, 'D', 4 if i < 2 else 3)
    if toe:
        tx = x + w - 1 if toe > 0 else x
        cv.p(tx, y - 1, 'D', 5); cv.p(tx, y - 2, 'D', 5)
    else:
        cv.p(x + 1, y - 2, 'D', 5); cv.p(x + w - 2, y - 2, 'D', 4)
    cv.p(x + (w // 2), y - 3, 'D', 2)                       # くつひも

# ---------------------------------------------------------------- 正面
def front(ph):
    cv = Cv(); bob = 1 if ph in (0, 2) else 0
    lift = {1: (2, 0), 3: (0, 2)}.get(ph, (0, 0))          # 片足を持ち上げる（左脚, 右脚）
    sw = {0: 0, 1: 1, 2: 0, 3: -1}[ph]                      # 腕のふり
    top = 2 + bob
    # 足（細い黒ズボン）：左脚 x=11..15、右脚 x=16..20 → 足首は3ドット
    for side, (x0, lf) in enumerate(((11, lift[0]), (17, lift[1]))):
        for y in range(top + 25, FOOT - 3 - lf + 1):
            t = (y - (top + 25)) / max(1, (FOOT - 3 - (top + 25)))
            wd = 4 - int(t * 1.3)
            xs = x0 + (0 if side == 1 else 5 - wd) if side == 0 else x0
            xl = (x0 + 4 - wd) if side == 0 else x0
            for x in range(xl, xl + wd):
                s = 3 if (side == 0 and x == xl) else 2 if (side == 1 and x == xl + wd - 1) else 3
                if side == 0 and x == xl: s = 4
                if side == 1 and x == xl + wd - 1: s = 2
                cv.p(x, y, 'T', s)
        yb = FOOT - lf
        sx = 10 if side == 0 else 16
        shoe(cv, sx, yb, 6, 0)
        for yy in range(top + 25, yb - 3): cv.p(x0 + (1 if side == 0 else 1), yy, 'T', 4 if yy % 5 else 3)
        cv.p(x0 + (2 if side == 0 else 2), top + 26, 'T', 2)                # ズボンの折り目
    # 腰（ベルト帯）と股
    cv.rect(11, top + 23, 20, top + 25, 'T', 3)
    for x in range(11, 21): cv.p(x, top + 23, 'T', 4);
    cv.rect(15, top + 25, 16, top + 25, 'T', 1)
    # シャツ
    for y in range(top + 12, top + 24):
        x0, x1 = (10, 21) if y < top + 15 else (11, 20)
        for x in range(x0, x1 + 1): cv.p(x, y, 's', [6, 5, 4][shade_lr(x, x0, x1)] - (1 if y > top + 20 else 0))
    for x in range(11, 21): cv.p(x, top + 23, 's', 3)       # ズボンへ入れた口
    cv.rect(11, top + 23, 20, top + 23, 'T', 4)
    # 首・えり・ネクタイ
    cv.rect(14, top + 11, 17, top + 12, 'k', 4); cv.p(14, top + 12, 'k', 3)
    for dx in (-2, -1, 0, 1):
        cv.p(15 + dx, top + 12, 's', 7 if dx < 0 else 6)
    cv.p(13, top + 12, 's', 5); cv.p(18, top + 12, 's', 4)
    cv.rect(15, top + 13, 16, top + 14, 'T', 3)             # 結び目
    for y in range(top + 15, top + 23): cv.rect(15, y, 16, y, 'T', 3 if y < top + 22 else 2); cv.p(16, y, 'T', 2)
    cv.p(15, top + 22, 'T', 2); cv.p(15, top + 23, 'T', 1)
    # 腕（ながそで）：体の外がわ
    for side in (0, 1):
        ax = 8 if side == 0 else 22; dy = sw * (1 if side == 0 else -1)
        for y in range(top + 13 + dy, top + 25 + dy):
            for x in (ax, ax + 1):
                cv.p(x, y, 's', 5 if x == ax and side == 0 else 4 if side == 0 else 3 if x == ax + 1 else 4)
        cv.p(ax, top + 25 + dy, 's', 4); cv.p(ax + 1, top + 25 + dy, 's', 3)
        cv.rect(ax, top + 26 + dy, ax + 1, top + 27 + dy, 'k', 5 if side == 0 else 3)         # 手
    # 頭
    head(cv, FRONT_HEAD, 9, 0 + bob)
    # 横髪（さがる）：顔のそばから肩へ
    for y in range(top + 12, top + 17):
        for x, s in ((9, 3), (10, 4), (21, 3), (22, 2)):
            if not cv.get(x, y) or y > top + 12: cv.p(x, y, 'r', s)
    # おさげ：右肩（画面の右）にたれる
    braid(cv, 23, top + 10, ph, side=1)
    shadow(cv)
    return cv

def braid(cv, x, y, ph, side=1, length=12, back=False):
    """編み込み：2行ごとに明・暗が左右にずれる。先にゴム（黒）と毛先"""
    for k in range(length):
        seg = (k // 2) % 2; sh = 4 if (k % 2 == 0) else 3
        xs = (x, x + 1) if seg == 0 else (x + 1, x + 2) if side > 0 else (x - 1, x)
        for i, xx in enumerate(xs):
            cv.p(xx, y + k, 'r', sh + (1 if i == 0 and seg == 0 else -1 if i == 1 else 0))
    cv.rect(x, y + length, x + 1, y + length, 'T', 2)
    for dx in (0, 1): cv.p(x + dx, y + length + 1, 'r', 3); 
    cv.p(x, y + length + 2, 'r', 2)

def shadow(cv):
    for x in range(9, 24):
        if (x % 2 == 0): cv.p(x, FOOT + 1, 'T', 1)
        if 11 <= x <= 21 and (x % 2 == 1): cv.p(x, FOOT + 2, 'T', 1)

# ---------------------------------------------------------------- 背面
def back(ph):
    cv = Cv(); bob = 1 if ph in (0, 2) else 0
    lift = {1: (2, 0), 3: (0, 2)}.get(ph, (0, 0)); sw = {0: 0, 1: 1, 2: 0, 3: -1}[ph]
    top = 2 + bob
    for side, (x0, lf) in enumerate(((11, lift[0]), (17, lift[1]))):
        for y in range(top + 25, FOOT - 3 - lf + 1):
            t = (y - (top + 25)) / max(1, (FOOT - 3 - (top + 25))); wd = 4 - int(t * 1.3)
            xl = (x0 + 4 - wd) if side == 0 else x0
            for x in range(xl, xl + wd): cv.p(x, y, 'T', 4 if (side == 0 and x == xl) else 2 if (side == 1 and x == xl + wd - 1) else 3)
        shoe(cv, 10 if side == 0 else 16, FOOT - lf, 6, 0)
    cv.rect(11, top + 22, 20, top + 25, 'T', 3); cv.p(15, top + 25, 'T', 1); cv.p(16, top + 25, 'T', 1)
    for x in range(11, 21): cv.p(x, top + 22, 'T', 4)
    for y in range(top + 12, top + 22):
        x0, x1 = (10, 21) if y < top + 15 else (11, 20)
        for x in range(x0, x1 + 1): cv.p(x, y, 's', [5, 4, 3][shade_lr(x, x0, x1)])
    for y in range(top + 14, top + 19): cv.p(15, y, 's', 3); cv.p(16, y, 's', 3)          # 背中のぬい目
    for x in (12, 13, 18, 19): cv.p(x, top + 15, 's', 3)                                     # 肩甲骨のかげ
    cv.rect(14, top + 11, 17, top + 12, 's', 5)
    for side in (0, 1):
        ax = 8 if side == 0 else 22; dy = sw * (-1 if side == 0 else 1)
        for y in range(top + 13 + dy, top + 25 + dy):
            for x in (ax, ax + 1): cv.p(x, y, 's', 5 if (x == ax and side == 0) else 3 if side == 1 else 4)
        cv.rect(ax, top + 25 + dy, ax + 1, top + 26 + dy, 'k', 5 if side == 0 else 3)
    head(cv, BACK_HEAD, 9, 0 + bob)
    for y in range(top + 11, top + 14):                                                    # 髪の毛先
        for x in range(12, 20):
            if y == top + 11 or (x in (13, 14, 17, 18)): cv.p(x, y, 'r', 3 if x < 16 else 2)
    braid(cv, 8, top + 10, ph, side=-1, back=True)                                          # おさげ（背中側から見える）
    shadow(cv)
    return cv

# ---------------------------------------------------------------- 横向き（右向き）
def side(ph):
    cv = Cv(); bob = 1 if ph in (0, 2) else 0; top = 2 + bob
    # 脚：4コマ  0=ひろげて接地(前=右脚が前) 1=すれちがい 2=ひろげて接地(逆) 3=すれちがい
    spread = {0: (3, -3), 1: (0, 0), 2: (-3, 3), 3: (0, 0)}[ph]; lift = {1: (0, 2), 3: (2, 0)}.get(ph, (0, 0))
    legs = [(spread[1], lift[1], 2), (spread[0], lift[0], 4)]                              # 奥の脚（かげ）→手前の脚
    for off, lf, sh in legs:
        hip_x = 14;
        for y in range(top + 24, FOOT - 3 - lf + 1):
            t = (y - (top + 24)) / max(1, (FOOT - 3 - (top + 24)))
            cx = hip_x + int(round(off * t))
            for x in range(cx, cx + 4 - (1 if t > .5 else 0)): cv.p(x, y, 'T', 3 if sh == 4 else 1 if x == cx else 2)
        shoe(cv, 14 + off - 1, FOOT - lf, 6, 1)
    cv.rect(13, top + 22, 19, top + 25, 'T', 3)
    for x in range(13, 20): cv.p(x, top + 22, 'T', 4)
    for y in range(top + 12, top + 22):
        x0, x1 = 12, 19
        for x in range(x0, x1 + 1): cv.p(x, y, 's', [6, 5, 4][shade_lr(x, x0, x1)])
    cv.p(19, top + 14, 's', 3); cv.p(19, top + 15, 's', 3)
    cv.rect(15, top + 11, 17, top + 12, 'k', 4)                                            # 首
    cv.p(15, top + 12, 's', 6); cv.p(16, top + 12, 's', 6); cv.p(17, top + 12, 's', 5)
    cv.rect(18, top + 14, 18, top + 21, 'T', 3); cv.p(18, top + 21, 'T', 2)                 # ネクタイ（胸の1列）
    # 奥の腕・手前の腕
    for armx, sh, sgn in ((15, 2, -1), (15, 5, 1)):
        swing = {0: 3, 1: 1, 2: -3, 3: -1}[ph] * sgn
        for k in range(12):
            yy = top + 13 + k; xx = armx + int(round(swing * k / 11))
            for dx in (0, 1): cv.p(xx + dx, yy, 's', sh if dx == 0 else sh - 1)
        xx = armx + swing
        cv.rect(xx, top + 25, xx + 1, top + 26, 'k', 4 if sgn > 0 else 2)
    head(cv, SIDE_HEAD, 10, 0 + bob)
    # 奥の横髪と、おさげ（背中側にたれる）
    braid(cv, 9, top + 9, ph, side=-1, back=True)
    # 前髪の先
    cv.p(21, top + 3, 'r', 4); cv.p(22, top + 3, 'r', 3)
    shadow(cv)
    return cv

def flip(cv):
    c = Cv(); c.a = cv.a[:, ::-1].copy(); return c

DIRS = {"down": front, "up": back, "right": side}
frames = {}
for d, fn in DIRS.items(): frames[d] = [fn(i).a for i in range(4)]
frames["left"] = [np.ascontiguousarray(f[:, ::-1]) for f in frames["right"]]
order = ["down", "left", "right", "up"]
sheet = np.zeros((H * 4, W * 4, 4), np.uint8)
for r, d in enumerate(order):
    for c, f in enumerate(frames[d]): sheet[r * H:(r + 1) * H, c * W:(c + 1) * W] = f
Image.fromarray(sheet).save(os.path.join(OUT, "redhead_sheet.png"))
BG = (58, 84, 62, 255)
def on_bg(f, k=8, bg=BG):
    im = Image.new("RGBA", (W, H), bg); im.alpha_composite(Image.fromarray(f)); return im.resize((W * k, H * k), Image.NEAREST).convert("RGB")
for d in order:
    g = [on_bg(f) for f in frames[d]]
    g[0].save(os.path.join(OUT, f"redhead_{d}.gif"), save_all=True, append_images=g[1:], duration=150, loop=0)
g = []
for i in range(4):
    row = Image.new("RGB", (W * 8 * 4, H * 8))
    for j, d in enumerate(order): row.paste(on_bg(frames[d][i]), (j * W * 8, 0))
    g.append(row)
g[0].save(os.path.join(OUT, "redhead_walk.gif"), save_all=True, append_images=g[1:], duration=150, loop=0)
pv = Image.new("RGB", (W * 8 * 4, H * 8 * 2))
for j, d in enumerate(order):
    pv.paste(on_bg(frames[d][0]), (j * W * 8, 0)); pv.paste(on_bg(frames[d][1]), (j * W * 8, H * 8))
pv.save(os.path.join(OUT, "redhead_preview.png"))
print("ok")
