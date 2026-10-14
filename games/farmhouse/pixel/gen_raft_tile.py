"""
木のイカダの床 1マス（ななめ上の視点 2:1、1m×1m）。上面は5枚の板（水が見えるすき間つき）、両はしに縄のしばり、くぎ、節、木目。
手前の2辺は厚み（側面：左は板の横、右は板の端の年輪）。左上から光。
python gen_raft_tile.py → sprites/raft_tile.pxl/.png/_big.png、sprites/raft_tile_3x2.png（つなげた確認）
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
HW, HH, T = 32, 16, 9                 # 上面ひし形の半幅・半高、厚み
W, H = HW * 2 + 2, HH * 2 + T + 3
OX, OY = 1, 1
def h2(ix, iy, seed=0):
    ix = np.asarray(ix, np.int64); iy = np.asarray(iy, np.int64)
    h = (ix * 73856093) ^ (iy * 19349663) ^ (seed * 83492791); h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return (h % 10007) / 10007.0
code = np.full((H, W), "..", dtype="<U2")
NP = 5
PLK = [4, 5, 4, 5, 4]                 # 板ごとの基本の明るさ（ばらつき）
def top(px, py):
    """画面の点 → 上面の座標 (u: 右下へ, v: 右上へ)"""
    x = px - OX; y = py - OY
    u = (x / HW + (y - HH) / HH) / 2; v = (x / HW - (y - HH) / HH) / 2
    return u, v
for py in range(H):
    for px in range(W):
        u, v = top(px + .5, py + .5)
        if not (0 <= u < 1 and 0 <= v < 1): continue
        k = int(v * NP); fr = v * NP - k; ix = int(u * 64); iy = int(v * 32)
        if fr < .07:                                                       # 板のすき間：水
            tok = "S0" if h2(ix // 2, k, 1) > .25 else "S1"
        else:
            base = PLK[k] + (1 if h2(k, 0, 5) > .7 else 0) - (1 if h2(k, 0, 6) < .2 else 0)
            s = base
            if fr > .8: s += 1                                            # 上（左上がわ）のふちは明るい
            if fr < .22: s -= 2                                             # 下のふちは影
            for gi, gf in enumerate((.33, .62)):                           # 木目：板ごとに2本、ところどころ切れる
                gj = gf + (h2(k, gi, 7) - .5) * .12
                if abs(fr - gj) < .045 and h2(int(u * 9) + gi * 13, k, 8) > .32: s -= 1
            jx = .35 + h2(k, 0, 9) * .4                                    # 板の途中のつなぎ目（横のすじ）
            if abs(u - jx) < .012 and fr > .1: s -= 2
            if h2(ix // 3, iy // 3, 11) > .965: s -= 1                      # 傷・色むら
            if h2(ix // 3, iy // 3, 12) > .95: s += 1
            tok = f"D{max(2, min(7, s))}"
            for (kk, ku, kv) in ((1, .66, .5), (3, .28, .5)):              # 節
                r = ((u - ku) / .045) ** 2 + ((fr - kv) / .2) ** 2
                if k == kk and r < 1: tok = "D1" if r < .35 else "D2"
            if (u < .08 or v < .05) and h2(ix // 2, iy // 2, 13) > .8: tok = "E2" if h2(ix, iy, 14) > .5 else "S2"   # 水しみ・苔
        for uc in (.1, .9):                                                # 縄のしばり（両はし）
            if abs(u - uc) < .045 and fr >= .07:
                tw = (int(v * 90) % 2 == 0)
                tok = "C4" if tw else "C2"
                if abs(u - uc) > .03: tok = "C5" if (u < uc) else "C1"
            elif abs(u - uc - .06) < .016 and fr >= .07 and tok[0] == "D":
                tok = "D1"                                                  # 縄の影
        for ku in (.035, .965):                                            # くぎ
            if abs(u - ku) < .014 and abs(fr - .5) < .06: tok = "I5"
        code[py, px] = tok
# ---- 側面（手前の2辺）
for px in range(OX, OX + HW):                                              # 左：板の横がわ
    topy = OY + HH + (px - OX) / 2
    for y in range(int(topy), int(topy) + T):
        d = y - int(topy)
        if y < H:
            code[y, px] = ("D4" if d == 0 else "D3" if d < 2 else "D2" if d < T - 2 else "D1")
            if d in (3, 6) and h2(px // 3, d, 21) > .35: code[y, px] = "D1"
for px in range(OX + HW, OX + 2 * HW):                                      # 右：板の端（年輪）
    topy = OY + 2 * HH - (px - OX - HW) / 2
    v = (px - OX - HW) / HW; k = min(NP - 1, int(v * NP)); fr = v * NP - k
    for y in range(int(topy), int(topy) + T):
        d = y - int(topy)
        if y >= H: continue
        if fr < .07: code[y, px] = "S0"; continue
        c = "D2" if d < T - 2 else "D1"
        if ((fr - .5) * 2) ** 2 + ((d - 4) / 4.2) ** 2 < 1:
            r = math.hypot((fr - .5) * 2 * 1.2, (d - 4) / 3.6)
            c = "D4" if int(r * 3) % 2 == 0 else "D2"
            if r < .35: c = "D3"
        if d == 0: c = "D3"
        code[y, px] = c
# ---- 外側の輪郭
m = code != ".."; e = np.zeros_like(m)
for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(m, dy, 0), dx, 1)
for y, x in zip(*np.nonzero(e & ~m)): code[y, x] = "U1"
p = os.path.join(HERE, "sprites", "raft_tile.pxl")
with open(p, "w") as f:
    f.write(f"# 木のイカダの床 1マス（{W}×{H}）。上面のひし形の中心＝({OX + HW},{OY + HH})\n@size {W} {H}\n")
    for r in code: f.write(" ".join(r) + "\n")
c_, img, _ = pxl.build(p); Image.fromarray(img).save(p.replace(".pxl", ".png"))
k = 8; big = Image.fromarray(img).resize((W * k, H * k), Image.NEAREST); bg = Image.new("RGBA", big.size, (34, 52, 70, 255)); bg.alpha_composite(big); bg.convert("RGB").save(p.replace(".pxl", "_big.png"))
tile = Image.fromarray(img); cols, rows = 3, 2                              # つなげた確認（3×2）
canvas = Image.new("RGBA", ((cols + rows) * HW + 10, (cols + rows) * HH + T + 12), (34, 52, 70, 255))
order = sorted([(i, j) for i in range(cols) for j in range(rows)], key=lambda t: (t[0] - t[1], t[0] + t[1]))
for i, j in order:
    ox = (i + j) * HW; oy = (rows - 1) * HH + (i - j) * HH
    canvas.alpha_composite(tile, (ox - OX + 4, oy + 4))
canvas.resize((canvas.width * 4, canvas.height * 4), Image.NEAREST).convert("RGB").save(os.path.join(HERE, "sprites", "raft_tile_3x2.png")); print("ok", W, H)
