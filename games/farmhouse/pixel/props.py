"""
小物を1つずつドット絵として作る。 python props.py → sprites/{barrel,bucket,crate,logs}.pxl と .png, _zoom.png
樽とバケツ：文字のマス目（この下のコードで書き出す）。木箱：iso の描画道具で小さく描いてから花を足す。丸太：円柱を専用に塗る。
1マス = 家の絵の2ドット（S=4のとき）。
"""
import os, sys, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.join(HERE, "sprites")
sys.path.insert(0, HERE)
import pxl, iso
rng = np.random.default_rng(5)

def h(ix, iy, seed=0): return float(iso.h2(ix, iy, seed))

def write(name, rows, header, w=None):
    p = os.path.join(SP, name + ".pxl")
    with open(p, "w", encoding="utf-8") as f:
        f.write(header + "\n")
        for r in rows: f.write(" ".join(r) + "\n")
    return p

# ---------------------------------------------------------------- 樽（水がはいっている）
def barrel():
    rows = []
    # ふたの楕円（7行）。木のふち D、水 F
    top = [
        "D5 D6 D6 D6 D6 D5",
        "D4 D5 F3 F3 F4 F4 F4 F4 F5",
        "D3 D4 F2 F3 F3 F4 F4 F5 F4 F4 F4",
        "D3 D4 F2 F2 F3 F3 F4 F4 F4 F5 F5 F4",
        "D3 D4 F2 F3 F3 F3 F4 F4 F4 F4 F4",
        "D4 D4 D3 F2 F2 F3 F3 F3 F3",
        "D3 D4 D4 D4 D4 D4",
    ]
    rows += [r.split() for r in top]
    widths = [11, 11, 11] + [12] * 3 + [12] * 9 + [12] * 3 + [11, 11, 11, 10, 9, 7]
    hoops = {0: 'hi', 1: 'h', 2: 'hl', 15: 'hi', 16: 'h', 17: 'hl'}
    for i, w in enumerate(widths):
        row = []
        for j in range(w):
            c = w - 1 - j                                     # 中心からの距離
            if i in hoops:
                t = hoops[i]; s = 5 if t == 'hi' else 2 if t == 'hl' else 4
                tok = f"I{s - (1 if c % 5 == 4 else 0)}"
                if h(c, i, 1) > .93: tok = "I3"
            else:
                seam = (c + 2) % 4 == 0
                s = 2 if seam else 4 + (1 if h(c, i, 2) > .86 else 0) - (1 if h(c, i, 3) < .12 else 0)
                tok = f"D{s}"
                if i > 17 and h(c, i, 4) < .22: tok = f"E{2 + int(h(c, i, 5) * 2)}"      # 足もとの苔
                if 4 < i < 14 and 3 <= c <= 4 and h(c, i // 3, 6) > .55: tok = "D5"     # つやのすじ
            row.append(tok)
        rows.append(row)
    rows = [[".."]] + rows + [[".."]]
    return write("barrel", rows, "# 樽。水入り。右は自動で折り返し\n@size 24 %d\n@mirror\n@align right\n@sidelight 2 K\n@outline sel" % len(rows))

# ---------------------------------------------------------------- バケツ
def bucket():
    top = ["C3 C4 C4", "C3 .. .. ..", "C3 .. .. ..",
           "D5 D5 D5 D5 D5",
           "D4 D5 F3 F4 F4 F4 F5",
           "D3 F2 F3 F4 F4 F4 F5",
           "D3 D4 D4 D4 D4 D4"]
    body = ["D3 D4 D4 D3 D4 D4 D4", "D3 D4 D4 D4 D3 D4 D4", "I3 I4 I4 I4 I4 I4 I5", "D3 D4 D3 D4 D4 D4 D4",
            "D2 D3 D4 D3 D4 D4 D4", "I2 I3 I3 I3 I4 I3 I4", "D2 D3 D3 D4 D3 D4 D4", "D2 D2 D3 D3 D3 D3 D3"]
    rows = [[".."]] + [r.split() for r in top + body] + [[".."]]
    return write("bucket", rows, "# バケツ（縄の取っ手つき）\n@size 16 %d\n@mirror\n@align right\n@sidelight 2 K\n@outline sel" % len(rows))

# ---------------------------------------------------------------- 木箱（すき間のある板と、だいだいの花）
def crate():
    A_ = 30.0                                        # 1m = 30ドット（家の絵の2ドット = 1マス）
    sv = (iso.W, iso.H, iso.A, iso.HZ, iso.P, iso.OX, iso.OY, iso.PX, iso.PY, iso.fam, iso.shd, iso.zb, iso.oid)
    iso.W, iso.H = 48, 44; iso.A = A_; iso.HZ = A_ * math.sqrt(1.5)
    iso.P = np.array([[iso.A, iso.A, 0.0], [iso.A / 2, -iso.A / 2, -iso.HZ]]); iso.OX, iso.OY = 24.0, 30.0
    iso.PX, iso.PY = np.meshgrid(np.arange(iso.W), np.arange(iso.H))
    iso.fam = np.full((iso.H, iso.W), -1, np.int8); iso.shd = np.zeros((iso.H, iso.W), np.int8)
    iso.zb = np.full((iso.H, iso.W), np.inf); iso.oid = np.zeros((iso.H, iso.W), np.int8)
    FI = iso.FI
    def slats(x, y, z, u, v, px, py):
        k = np.floor(v / .15); fr = v - k * .15
        gap = fr > .125
        s = 4 + (iso.h2(k, 0, 7) > .6) - (iso.h2(k, 0, 8) > .8) * 1
        s = np.where(gap, 1, s + (iso.h2(px, py, 9) > .9) - (iso.h2(px, py, 10) < .1))
        post = (u < .06) | (u > .5)
        f = np.where(gap, FI['K'], FI['D']); s = np.where(post & ~gap, 3, s)
        return f.astype(np.int8), np.clip(s, 0, 7).astype(np.int8)
    def soil(x, y, z, u, v, px, py):
        return np.full(x.shape, FI['J'], np.int8), (2 + (iso.h2(px, py, 11) > .8)).astype(np.int8)
    iso.box(-.28, -.28, 0, .28, .28, .5, {'+z': soil, 'all': slats}, 1)
    f, s = iso.fam.copy(), iso.shd.copy()
    code = np.full(f.shape, "..", dtype="<U2")
    for y in range(f.shape[0]):
        for x in range(f.shape[1]):
            if f[y, x] >= 0: code[y, x] = iso.FAM[f[y, x]] + str(s[y, x])
    ys, xs = np.nonzero(code != ".."); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    code = code[y0 - 8 if y0 >= 8 else 0: y1 + 3, x0 - 1: x1 + 2]
    # 花を足す（上の面の上に）
    H_, W_ = code.shape; top = np.nonzero((code != "..").any(1))[0].min()
    def put(x, y, t):
        if 0 <= x < W_ and 0 <= y < H_: code[y, x] = t
    cx = W_ // 2
    for (dx, base) in ((-4, top + 5), (0, top + 7), (4, top + 5), (-2, top + 9), (2, top + 9)):
        put(cx + dx, base, "E3")
        for ly in range(1, 5): put(cx + dx + (ly % 2 and -1 or 0) * (0), base - ly, "E3" if ly < 3 else "E4")
        for ax in (-2, -1, 1, 2): put(cx + dx + ax, base - 1 - (abs(ax) == 2), "E4" if ax < 0 else "E3")
    for (dx, hy) in ((-4, top + 0), (4, top + 0), (0, top + 2), (-2, top + 4), (2, top + 4)):
        for ox, oy, t in ((0, 0, "H5"), (-1, 0, "H4"), (1, 0, "H6"), (0, -1, "H6"), (0, 1, "H3"), (0, 0, "B6")):
            put(cx + dx + ox, hy + oy, t)
    (iso.W, iso.H, iso.A, iso.HZ, iso.P, iso.OX, iso.OY, iso.PX, iso.PY, iso.fam, iso.shd, iso.zb, iso.oid) = sv
    return write("crate", code.tolist(), "# 木箱と花（isoの描画道具で描いた板に、花を足した）\n@size %d %d\n@outline sel" % (code.shape[1], code.shape[0]))

# ---------------------------------------------------------------- 丸太の山（端の年輪が見える）
def logs():
    Wd, Ht = 64, 62
    code = np.full((Ht, Wd), "..", dtype="<U2")
    A_ = 30.0; HZ = A_ * math.sqrt(1.5)
    P = np.array([[A_, A_, 0.0], [A_ / 2, -A_ / 2, -HZ]])
    ox, oy = 6.0, 46.0
    R = .16
    def inv2(sx, sy, ax, ay):      # 画面の点 → (軸方向以外の2成分 Y,Z)。x軸方向の長さは別に決める
        M = np.array([[P[0, 1], P[0, 2]], [P[1, 1], P[1, 2]]]); return np.linalg.solve(M, np.array([sx, sy]))
    logs_ = [(0, 0), (.33, 0), (.66, 0), (.165, .29), (.495, .29), (.33, .58)]      # (y, z) 断面の中心
    LEN = 1.05
    order = sorted(range(len(logs_)), key=lambda i: (logs_[i][1], -logs_[i][0]))
    zbuf = np.full((Ht, Wd), np.inf)
    for i in order:
        cy, cz = logs_[i][0], logs_[i][1] + R
        for py in range(Ht):
            for px in range(Wd):
                sx, sy = px + .5 - ox, py + .5 - oy
                # 画面の点を通る視線が、円柱(軸=x)の断面円と交わるか：x=t を動かして調べる
                best = None
                for t in np.linspace(0, LEN, 90):
                    Yc, Zc = inv2(sx - P[0, 0] * t, sy - P[1, 0] * t, 0, 0)
                    d = math.hypot(Yc - cy, Zc - cz)
                    if d <= R:
                        key = (-t) * 0.612 * -1 + 0  # 手前ほど小さい値（x大=手前）
                        key = -(t * .612) + (Yc * .612) - Zc * .5
                        if best is None or key < best[0]: best = (key, t, Yc, Zc, d)
                if best is None: continue
                key, t, Yc, Zc, d = best
                if key >= zbuf[py, px]: continue
                zbuf[py, px] = key
                if t > LEN - .06:                                   # 端の面：年輪
                    rr = d / R
                    ring = int(rr * 5.2) % 2
                    tok = f"B{4 + ring}" if rr > .12 else "B6"
                    if rr > .88: tok = "D3"
                    if h(px // 1, py // 1, 21) < .06: tok = "B3"
                else:                                               # 側面：まるみの陰影と皮のすじ
                    ang = math.atan2(Zc - cz, Yc - cy)                # 上=pi/2
                    lit = math.cos(ang - math.radians(125))         # 左上が明るい
                    s = 3 + int(round(lit * 1.6)) + (1 if h(int(t * 14), int(d * 20), 22) > .8 else 0) - (1 if h(int(t * 14), int(d * 20), 23) < .12 else 0)
                    tok = f"D{max(1, min(6, s))}"
                    if h(int(t * 9), i, 24) > .93 and lit > 0: tok = "E3"     # 苔
                code[py, px] = tok
    return write("logs", code.tolist(), "# 丸太の山（6本）\n@size %d %d\n@outline sel" % (Wd, Ht))

if __name__ == "__main__":
    for fn in (barrel, bucket, crate, logs):
        p = fn(); code, img, pal = pxl.build(p)
        from PIL import Image
        base = os.path.splitext(p)[0]; Image.fromarray(img).save(base + ".png"); pxl.zoom(img, code, pal, 12).save(base + "_zoom.png")
        print(fn.__name__, img.shape[1], "x", img.shape[0])
