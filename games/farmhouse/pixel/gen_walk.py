"""農夫の歩き（正面・横向き 各4コマ）の .pxl を作り、絵にしてスプライトシートにまとめる。
横向きの上半身は下の文字で描き、腕と脚はコマごとに位置を変えて組み立てる。
"""
import os, sys
import numpy as np
from PIL import Image
import pxl

HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, "sprites")
W, H = 32, 41

def row(s, indent=8):
    t = s.split(); return [".."] * indent + t + [".."] * (W - indent - len(t))

# 横向き（右向き）の上半身。1行目=画面の2行目(y=1)。頭と胴、腕なし。
SIDE = [
 "..  ..  ..  B3  B5  B5  B5  B5  B5  B5  B4",
 "..  ..  ..  B3  B4  B5  B5  B5  B5  B5  B4",
 "..  ..  ..  B3  B4  B4  B4  B4  B4  B4  B3",
 "..  ..  ..  D2  D3  D3  D3  D3  D3  D3  D2",
 "..  B4  B5  B6  B5  B6  B6  B5  B6  B6  B6  B6  B5  B6  B5  B4",
 "..  ..  B3  B4  B4  B3  B4  B4  B3  B4  B4  B4  B4  B3  B3  B2",
 "..  ..  ..  ..  J2  J3  A2  A2  A2  A2  A2  A2",
 "..  ..  ..  ..  J3  J3  J3  A4  A4  A5  J2  A5",
 "..  ..  ..  ..  J3  J3  A3  A4  A4  A5  K1  A5  A4",
 "..  ..  ..  ..  J3  J3  A3  A3  A4  A4  A4  A4  A3",
 "..  ..  ..  ..  ..  J3  A3  A4  A4  A4  A4  A2",
 "..  ..  ..  ..  ..  ..  A3  A3  A3  A3  A2",
 "..  ..  ..  ..  ..  F3  F4  F4  F5  F4  F4  F3",
 "..  ..  ..  F2  F3  F3  F4  F5  F4  F4  F4  F3",
 "..  ..  ..  F2  D4  D4  C5  C5  C5  C5  C5  C4",
 "..  ..  ..  ..  D4  D3  C5  C5  C5  C5  C5  C4",
 "..  ..  ..  ..  D4  D3  C5  C5  C5  C4  D4  D3",
 "..  ..  ..  ..  D4  D3  C5  C5  C5  C4  D4  D3",
 "..  ..  ..  ..  D4  D3  C5  C5  C5  C4  D3  D3",
 "..  ..  ..  ..  D4  D3  C5  C5  C5  C4  D3  D3",
 "..  ..  ..  ..  D3  D3  C4  C5  C5  C4  D3  D3",
 "..  ..  ..  ..  D3  D3  C4  C4  C4  C4  D3  D2",
 "..  ..  ..  ..  D3  D3  C4  C5  C5  C4  D3  D3",
 "..  ..  ..  ..  D3  D3  C4  C5  C4  C4  D3  D3",
 "..  ..  ..  ..  D3  D3  C4  C4  C4  C4  D3  D2",
 "..  ..  ..  ..  D4  D4  D4  D4  D4  D4  D4  B6",
 "..  ..  ..  ..  D2  D2  D2  D2  D2  D2  D2  B4",
]
# 腕（4幅×11行）。2つの明るさで、手前の腕。
ARM = [
 "C5 C5 C4 C3", "C5 C5 C4 C3", "C5 C4 C4 C3", "C5 C4 C4 C3", "C4 C4 C3 C3", "C4 C4 C3 C3",
 "C4 C3 C3 C2", "C3 C3 C2 C2", "A5 A4 A3 A2", "A4 A4 A3 A2", ".. A3 A3 A2",
]

def put(g, x, y, tok):
    if 0 <= x < W and 0 <= y < H: g[y][x] = tok

def leg(g, x0, y0, dx, length, pal, w=4):
    """腰(x0,y0)から足もとへ、横に dx ずらしながらズボンを描く"""
    for i in range(length):
        sh = int(round(dx * i / max(1, length - 1)))
        for j in range(w):
            c = pal[0] if j == 0 else pal[2] if j == w - 1 else pal[1]
            put(g, x0 + sh + j, y0 + i, c)
    return x0 + int(round(dx))

def boot(g, x, y, pal, lift=0):
    for r in range(3):
        for j in range(6):
            t = pal[0] if r == 0 else pal[1] if r == 1 else pal[2]
            if j == 5 and r < 2: t = pal[2]
            put(g, x + j - 1, y + r - lift, t)
    for j in range(6): put(g, x + j - 1, y + 3 - lift, "K3")

def side_frame(step):
    g = [[".."] * W for _ in range(H)]
    oy = 1 if step in (0, 2) else 0                  # 足を開いた時は体が低い
    for i, s in enumerate(SIDE):
        for x, t in enumerate(row(s)):
            if t != "..": put(g, x, 1 + oy + i, t)
    ax = {0: -2, 1: 0, 2: 2, 3: 0}[step]             # 腕のふり
    for i, s in enumerate(ARM):
        for j, t in enumerate(s.split()):
            if t != "..": put(g, 8 + 6 + j + ax, 1 + oy + 14 + i, t)
    hipy = 1 + oy + 27                                # 腰の下
    # 奥の足（暗め）→ 手前の足
    far = {0: -3, 1: 0, 2: 3, 3: -1}[step]; near = {0: 3, 1: 1, 2: -3, 3: 0}[step]
    lift_far = 3 if step == 3 else 0; lift_near = 3 if step == 1 else 0
    FARP = ("M2", "M3", "M2"); NEARP = ("M3", "M4", "M3")
    for (d, pal, bpal, lift) in ((far, FARP, ("D3", "D2", "D2"), lift_far), (near, NEARP, ("D4", "D3", "D3"), lift_near)):
        ln = 38 - hipy - 2 - lift
        fx = leg(g, 13, hipy, d, ln, pal)
        boot(g, fx, 36 - lift if False else hipy + ln, bpal)
    return g

def front_frame(step):
    code, _ = pxl.build(os.path.join(S, "farmer_front.pxl"), pre=True)
    g = [[str(code[y, x]) for x in range(W)] for y in range(H)]
    # 脚をあげる（左脚：コマ1、右脚：コマ3）、手を少し振る
    if step in (1, 3):
        xs = range(0, 16) if step == 1 else range(16, 32)
        for x in xs:
            col = [g[y][x] for y in range(33, 40)]
            for y in range(33, 40): g[y][x] = ".."
            for i, t in enumerate(col): g[33 + i - 2][x] = t
    if step in (0, 2):
        dy = 1 if step == 0 else -1
        for x in list(range(5, 9)) if step == 0 else list(range(23, 27)):
            col = [g[y][x] for y in range(17, 28)]
            for y in range(17, 28): g[y][x] = ".."
            for i, t in enumerate(col): g[17 + i + (1 if step == 0 else 0)][x] = t
    return g

def write(name, g):
    p = os.path.join(S, name + ".pxl")
    with open(p, "w") as f:
        f.write(f"@size {W} {H}\n@sidelight 1 K\n@outline sel\n")
        for r in g: f.write(" ".join(r) + "\n")
    return p

sheet = np.zeros((H * 2, W * 4, 4), np.uint8)
for r, (nm, fn) in enumerate((("front", front_frame), ("side", side_frame))):
    for s in range(4):
        _, img, _ = pxl.build(write(f"farmer_{nm}_walk{s}", fn(s)))
        sheet[r * H:(r + 1) * H, s * W:(s + 1) * W] = img
out = os.path.join(HERE, "..", "assets", "character")
Image.fromarray(sheet).save(os.path.join(out, "farmer_sheet_v2.png"))
frames = []
for s in range(4):
    im = Image.fromarray(sheet[H:2 * H, s * W:(s + 1) * W]).resize((W * 10, H * 10), Image.NEAREST)
    bg = Image.new("RGBA", im.size, (36, 52, 64, 255)); bg.alpha_composite(im); frames.append(bg)
frames[0].convert("P").save(os.path.join(out, "farmer_walk_v2.gif"), save_all=True, append_images=[f.convert("P") for f in frames[1:]], duration=170, loop=0)
big = Image.fromarray(sheet).resize((W * 4 * 8, H * 2 * 8), Image.NEAREST)
bg = Image.new("RGBA", big.size, (36, 52, 64, 255)); bg.alpha_composite(big); bg.save(os.path.join(out, "farmer_preview_v2.png"))
print("done")
