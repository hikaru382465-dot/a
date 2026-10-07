"""
海の1マス（ななめ上の視点 2:1、1m×1m、菱形 64×32）。波が流れる8コマの輪（ループ）。
隣のマスと、ぴったりつながる（波の式を、マスの中で繰り返す整数の周期にしているから）。
python gen_sea_tile.py → assets/effects/sea_tile_sheet.png（4列×2行）, sea_tile.gif, sea_raft_demo.gif（イカダを浮かべた確認）
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "effects"); os.makedirs(OUT, exist_ok=True)
HW, HH = 32, 16
TW, TH = HW * 2, HH * 2
N = 8
pal, _ = pxl.load_palette(); WAT = np.array(pal["w"], np.uint8)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
def h2(ix, iy, seed=0):
    ix = np.asarray(ix, np.int64); iy = np.asarray(iy, np.int64)
    h = (ix * 73856093) ^ (iy * 19349663) ^ (seed * 83492791); h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return (h % 10007) / 10007.0
yy, xx = np.mgrid[0:TH, 0:TW]
X, Y = xx + .5, yy + .5
U = (X / HW + (Y - HH) / HH) / 2; V = (X / HW - (Y - HH) / HH) / 2
MASK = (U >= 0) & (U < 1) & (V >= 0) & (V < 1)
TAU = 2 * math.pi

def height(u, v, t):
    """波の高さ。u,v は 0〜1 でくり返す（整数の周期）、t は 0〜1（1で1周）。
    おもな波＝u の方向へ流れる長いうねり（筋は v の辺と平行）。筋をゆらして、くねらせる。細かいさざ波を少し重ねる"""
    warp = .13 * np.sin(TAU * (3 * v) + TAU * t) + .06 * np.sin(TAU * (5 * v + 1 * u) - TAU * 2 * t)
    swell = .62 * np.sin(TAU * (2 * u + warp) - TAU * t)
    swell2 = .30 * np.sin(TAU * (3 * u + 1 * v + .5 * warp) - TAU * 2 * t + 1.1)
    cross = .22 * np.sin(TAU * (2 * v + .08 * np.sin(TAU * 2 * u)) + TAU * t + .4)
    ripple = .12 * np.sin(TAU * (6 * u - 5 * v) + TAU * 3 * t)
    return swell + swell2 + cross + ripple

def frame(i):
    t = i / N
    h = height(U, V, t)
    # ふかさ：マス全体のゆるいむら（右下ほど少し深い）
    depth = .25 * np.sin(TAU * (U - V) * 1) * 0 + 0
    q = (h + 1.0) / 2.0                                            # 0〜1
    q = np.clip(q, 0, 1)
    lev = q * 5.0 + (BAYER[yy % 4, xx % 4] - .5) * .55
    idx = np.clip(np.floor(lev).astype(int) + 1, 1, 5)             # w1〜w5
    # 白いあわ（波がしら）：高い所を、線の形に
    crest = (h > .78) & (BAYER[(yy + 1) % 4, xx % 4] < .8)
    idx = np.where(crest, 6, idx)
    # きらめき：高い所の、ときどき1ドット
    sp = (h > .5) & (h2(xx, yy, 5 + i) > .985)
    idx = np.where(sp, 7, idx)
    # 暗いかげ（谷）
    trough = (h < -.62)
    idx = np.where(trough, 1, idx)
    img = np.zeros((TH, TW, 4), np.uint8)
    img[MASK, :3] = WAT[idx[MASK]]; img[MASK, 3] = 255
    return img

frames = [frame(i) for i in range(N)]
sheet = np.zeros((TH * 2, TW * 4, 4), np.uint8)
for i, f in enumerate(frames): sheet[(i // 4) * TH:(i // 4 + 1) * TH, (i % 4) * TW:(i % 4 + 1) * TW] = f
Image.fromarray(sheet).save(os.path.join(OUT, "sea_tile_sheet.png"))

# ---- つなげた確認：6×6のマスの海（アニメ）
def sea_field(cols, rows, i):
    tile = Image.fromarray(frames[i % N])
    W = (cols + rows) * HW + 2; H = (cols + rows) * HH + 2
    c = Image.new("RGBA", (W, H), (8, 20, 36, 255))
    for a in range(cols):
        for b in range(rows):
            c.alpha_composite(tile, ((a + b) * HW, (rows - 1) * HH + (a - b) * HH))
    return c
frames_big = []
raft = Image.open(os.path.join(HERE, "sprites", "raft_tile.png")).convert("RGBA")
cols = rows = 6
for i in range(N):
    base = sea_field(cols, rows, i)
    # イカダ（3×2）を中央に。ゆらゆら上下に1ドット
    bob = [0, 0, 1, 1, 1, 0, 0, -1][i] if False else int(round(math.sin(TAU * i / N) * 1.0))
    order = sorted([(a, b) for a in range(3) for b in range(2)], key=lambda t: (t[0] - t[1], t[0] + t[1]))
    for a, b in order:
        ga, gb = a + 2, b + 2                                       # 海の中の位置
        ox = (ga + gb) * HW - 1; oy = (rows - 1) * HH + (ga - gb) * HH - 12 + bob
        base.alpha_composite(raft, (ox, oy))
    frames_big.append(base)
k = 4
gif = [f.resize((f.width * k, f.height * k), Image.NEAREST).convert("RGB") for f in frames_big]
gif[0].save(os.path.join(OUT, "sea_raft_demo.gif"), save_all=True, append_images=gif[1:], duration=140, loop=0)
gif[0].save(os.path.join(OUT, "sea_raft_demo_frame0.png"))
tiles = [Image.fromarray(f).resize((TW * 6, TH * 6), Image.NEAREST) for f in frames]
tg = []
for t_ in tiles:
    bg = Image.new("RGBA", t_.size, (8, 20, 36, 255)); bg.alpha_composite(t_); tg.append(bg.convert("RGB"))
tg[0].save(os.path.join(OUT, "sea_tile.gif"), save_all=True, append_images=tg[1:], duration=140, loop=0)
print("ok")
