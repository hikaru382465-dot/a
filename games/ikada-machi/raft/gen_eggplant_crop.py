# ナスの作物（4段階：芽・つぼみ・小さい実・収穫）を、畑のマス（make_crops.py のプランター）に合成する。
# パレットは games/farmhouse/pixel/palette.json（葉=E/O、ナス=q、花の中心=B）。使い道：python3 gen_eggplant_crop.py
import sys, math, pathlib
import numpy as np
from PIL import Image
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'farmhouse' / 'pixel'))
import pxl
import make_crops as mc          # プランターと compose() をそのまま使う
pal, _ = pxl.load_palette()
K = 1.3                         # 作物の大きさのそろえ（トマトなどと同じくらいに）
CW, CH = 104, 125
def col(f, s): return pal[f][int(np.clip(s, 0, 7))]

class Cv:
    def __init__(s): s.rgb = np.zeros((CH, CW, 3), np.uint8); s.a = np.zeros((CH, CW), bool); s.fam = np.full((CH, CW), '', object)
    def put(s, m, f, sh):
        s.rgb[m] = col(f, sh); s.a[m] = True; s.fam[m] = f
Y, X = np.mgrid[0:CH, 0:CW].astype(float)

def leaf(c, cx, cy, ang, ln, wd, droop=0.0):
    """葉：つけ根(cx,cy)から ang(度)の向きに ln、はば wd。上がわが明るく、中ほどに葉脈。"""
    cx, cy, ln, wd = cx * K, cy * K, ln * K, wd * K
    a = math.radians(ang); dx, dy = math.cos(a), -math.sin(a)
    px, py = X - cx, Y - cy
    u = px * dx + py * dy; v = -px * dy + py * dx - droop * (u / ln) ** 2 * ln
    t = u / ln
    half = wd * np.sqrt(np.clip(np.sin(np.clip(t, 0, 1) * math.pi), 0, 1)) ** 1.1 * (1 - .25 * t)
    m = (t >= 0) & (t <= 1) & (np.abs(v) <= half)
    # 光は左上から：葉の向きに対して上がわ（画面の上）を明るく
    up = (-dx * 0 + 1) * (-(v * dx) + 0)            # 向きの法線の、画面上への成分
    lit = (v * (dx) * -1 + 0)
    side = np.where(dy * 0 + (-(v) * dx) > 0, 1, 0)   # v>0 側が画面上かどうか
    s_up = (-(py) > 0)                                 # 画面の上半分
    base = 4 + (1 if t.mean() < 2 else 0)
    sh = np.full(X.shape, 4.0)
    sh += np.where(np.abs(v) > half * .55, -1, 0)      # ふちは暗い
    sh += np.where((-py * 1.0 + (-px) * .5) > 0, 1, 0) * 1   # 左上がわを1段明るく
    sh = np.clip(sh, 2, 6)
    for f_ in (sh,): pass
    yy, xx = np.nonzero(m)
    for y_, x_ in zip(yy, xx):
        s = int(sh[y_, x_]); f = 'E'
        if s >= 6: f, s = 'O', 4
        c.rgb[y_, x_] = col(f, s); c.a[y_, x_] = True; c.fam[y_, x_] = f
    rib = m & (np.abs(v) < .55) & (t > .04) & (t < .92)
    c.rgb[rib] = col('E', 2); 

def stem(c, x0, y0, x1, y1, w=2.2, bend=0.0):
    x0, y0, x1, y1, w, bend = x0 * K, y0 * K, x1 * K, y1 * K, w * K, bend * K
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 3) + 2
    for k in range(n):
        t = k / (n - 1); x = x0 + (x1 - x0) * t + bend * math.sin(t * math.pi); y = y0 + (y1 - y0) * t
        m = (X - x) ** 2 + (Y - y) ** 2 <= (w / 2 + .35) ** 2
        c.put(m, 'E', 3)
        mm = m & (X < x - .3); c.rgb[mm & c.a] = col('O', 3)

def fruit(c, cx, cy, ln, wd, ang=-80, hang=True):
    """ナスの実：のびたしずく形。つや1本。へた（緑のかさ）つき。ang=へたの向き"""
    cx, cy, ln, wd = cx * K, cy * K, ln * K, wd * K
    a = math.radians(ang); dx, dy = math.cos(a), -math.sin(a)       # へた → 先 の向きは逆(dx,dy の反対)
    px, py = X - cx, Y - cy
    u = -(px * dx + py * dy); v = -px * dy + py * dx                 # u: へたから先へ
    t = u / ln
    half = wd * (0.55 + .45 * np.sin(np.clip(t, 0, 1) * math.pi * .62 + .25)) * np.sqrt(np.clip(1 - np.clip(t - .55, 0, 1) ** 2 / .45 ** 2, 0, 1))
    m = (t >= 0) & (t <= 1) & (np.abs(v) <= half)
    d = v / np.maximum(half, 1e-3)
    lam = np.clip(.35 + .6 * (-d * .75 + (1 - np.abs(d)) * .5) , 0, 1)                    # 左がわ（v<0）を明るく
    lam = np.clip(.25 + .55 * (1 - (d + .35) ** 2) + .2 * (1 - t), 0, 1)
    sh = np.clip(np.floor(1 + lam * 4.4), 1, 5)
    yy, xx = np.nonzero(m)
    for y_, x_ in zip(yy, xx):
        c.rgb[y_, x_] = col('q', int(sh[y_, x_])); c.a[y_, x_] = True; c.fam[y_, x_] = 'q'
    hl = m & (np.abs(d + .45) < .12) & (t > .22) & (t < .72)                         # つや（細い帯）
    c.rgb[hl] = col('q', 7)
    cap = (t < .0 + 3.2 / ln) & (np.abs(v) <= wd * .62) & (t > -1.5 / ln)           # へた
    c.put(cap, 'E', 3); c.rgb[cap & (v < 0)] = col('O', 3)

def flower(c, cx, cy, r=5, bud=False):
    cx, cy, r = cx * K, cy * K, r * K
    if bud:
        m = ((X - cx) / (r * .55)) ** 2 + ((Y - cy) / r) ** 2 <= 1
        c.put(m, 'q', 5); c.rgb[m & (X < cx - .5)] = col('q', 6)
        cap = (np.abs(X - cx) <= r * .6) & (Y >= cy + r * .35) & (Y <= cy + r * 1.05) & (np.abs(X - cx) <= (1.05 - (Y - cy) / r * .35) * r * .6)
        c.put(cap, 'E', 3); return
    for k in range(5):
        a = math.radians(90 + k * 72)
        px, py = cx + math.cos(a) * r * .55, cy - math.sin(a) * r * .55
        m = ((X - px) ** 2 + (Y - py) ** 2) <= (r * .62) ** 2
        c.put(m, 'q', 5 if k not in (0, 1) else 6)
    c.put((X - cx) ** 2 + (Y - cy) ** 2 <= (r * .32) ** 2, 'B', 5)

def outline(c):
    al = c.a; pad = np.pad(al, 1)
    edge = ~al & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
    for y_, x_ in zip(*np.nonzero(edge)):
        f = 'E'
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y_ + dy, x_ + dx
            if 0 <= yy < CH and 0 <= xx < CW and al[yy, xx]: f = c.fam[yy, xx] if c.fam[yy, xx] in ('q',) else 'E'; break
        c.rgb[y_, x_] = col(f, 0)
    c.a = c.a | edge

def img(c):
    out = np.zeros((CH, CW, 4), np.uint8); out[..., :3] = c.rgb; out[..., 3] = np.where(c.a, 255, 0)
    im = Image.fromarray(out, 'RGBA'); return im.crop(im.getchannel('A').getbbox())

B = (40, 90)      # 根もと
def s1():     # 芽：ふたばと小さい本葉
    c = Cv(); stem(c, 40, 90, 40, 76, 2.4)
    leaf(c, 40, 78, 160, 13, 4.2, .3); leaf(c, 40, 78, 20, 13, 4.2, .3)
    leaf(c, 40, 76, 85, 9, 3.0); outline(c); return img(c)
def s2():     # つぼみ：枝がのび、葉がふえ、先に紫のつぼみ
    c = Cv(); stem(c, 40, 90, 41, 54, 3.0, 1.2)
    leaf(c, 40, 80, 155, 19, 6.0, .4); leaf(c, 40, 80, 25, 19, 6.0, .4)
    leaf(c, 40, 68, 135, 18, 6.0, .3); leaf(c, 40, 66, 48, 18, 6.0, .3)
    leaf(c, 41, 58, 105, 12, 4.4); leaf(c, 41, 58, 78, 12, 4.4)
    flower(c, 41, 49, 5.5, bud=True); outline(c); return img(c)
def s3():     # 小さい実：花がさき、小さな実がぶらさがる
    c = Cv(); stem(c, 40, 90, 41, 44, 3.4, 1.5)
    leaf(c, 40, 82, 160, 24, 7.5, .5); leaf(c, 40, 82, 20, 24, 7.5, .5)
    leaf(c, 40, 68, 145, 22, 7.0, .4); leaf(c, 40, 64, 38, 22, 7.0, .4)
    leaf(c, 41, 54, 150, 16, 5.6, .3); leaf(c, 41, 52, 32, 16, 5.6, .3)
    stem(c, 42, 56, 51, 60, 1.6); fruit(c, 51, 60, 15, 5.0, ang=100)
    flower(c, 41, 40, 5.0); outline(c); return img(c)
def s4():     # 収穫：大きな実が2つ、つやのある濃い紫
    c = Cv(); stem(c, 40, 90, 41, 34, 3.8, 1.5)
    leaf(c, 40, 84, 162, 27, 8.5, .5); leaf(c, 40, 84, 18, 27, 8.5, .5)
    leaf(c, 40, 70, 148, 25, 8.0, .4); leaf(c, 40, 66, 34, 25, 8.0, .4)
    leaf(c, 41, 48, 120, 20, 6.5, .3); leaf(c, 41, 44, 66, 20, 6.5)
    stem(c, 38, 58, 28, 60, 1.8); fruit(c, 28, 60, 30, 9.0, ang=95)
    stem(c, 43, 52, 55, 56, 1.8); fruit(c, 55, 56, 26, 8.0, ang=88)
    outline(c); return img(c)

stages = [s1(), s2(), s3(), s4()]
frames = [mc.compose(s, 0.9 if i == 3 else 1.0) for i, s in enumerate(stages)]
out = pathlib.Path(__file__).resolve().parents[2] / 'farmhouse' / 'assets' / 'items'
sheet = Image.new('RGBA', (sum(f.width + 12 for f in frames) + 12, frames[0].height + 12), (40, 120, 170, 255)); x = 12
for i, f in enumerate(frames): sheet.alpha_composite(f, (x, 6)); f.save(out / f'eggplant_crop{i + 1}.png'); x += f.width + 12
sheet = sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST); sheet.save(out / 'eggplant_crop_sheet.png')
print([s.size for s in stages])
