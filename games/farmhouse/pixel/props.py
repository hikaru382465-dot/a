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


# ---------------------------------------------------------------- トマトの株（見本：葉は暗い緑・青緑・黄緑、実は赤）
def tomato(seed, Wd=46, Ht=54):
    r = np.random.default_rng(seed)
    code = np.full((Ht, Wd), "..", dtype="<U2"); zb_ = np.full((Ht, Wd), -9.0)
    cx0, base = Wd // 2, Ht - 6
    def put(x, y, t, d):
        if 0 <= x < Wd and 0 <= y < Ht and d >= zb_[y, x]: code[y, x] = t; zb_[y, x] = d
    # 支柱と茎
    for y in range(8, base + 1):
        put(cx0, y, "D3", -1); put(cx0 + 1, y, "D4", -1)
    items = []
    for _ in range(58):                                           # 葉
        z = r.uniform(.12, 1.0); a = r.uniform(0, 2 * math.pi)
        rad = r.uniform(.25, 1.0) * (6 + 12 * math.sin(math.pi * min(1, z * .9 + .1)))
        x = cx0 + rad * math.cos(a); y = base - 4 - z * 32 + math.sin(a) * rad * .32
        d = math.sin(a) + z * .5
        ang = math.atan2(y - (base - 4 - z * 32), x - cx0) + r.normal(0, .5) - .25
        items.append(("leaf", d, x, y, ang, r.uniform(3.4, 5.6), r.uniform(1.7, 2.7), z))
    for _ in range(15):                                           # 実
        z = r.uniform(.1, .62); a = r.uniform(0, 2 * math.pi); rad = r.uniform(.4, 1.0) * (8 + 7 * z)
        x = cx0 + rad * math.cos(a); y = base - 4 - z * 30 + math.sin(a) * rad * .32 + 3
        items.append(("fruit", math.sin(a) + z * .5 + .35, x, y, r.choice(["ripe"] * 12 + ["orange"]), r.uniform(2.1, 2.9), 0, z))
    items.sort(key=lambda t: t[1])
    for it in items:
        kind, d, x, y = it[:4]
        if kind == "leaf":
            ang, a_, b_, z = it[4:8]; ca, sa = math.cos(ang), math.sin(ang)
            for py in range(int(y - a_ - 2), int(y + a_ + 3)):
                for px in range(int(x - a_ - 2), int(x + a_ + 3)):
                    dx, dy = px + .5 - x, py + .5 - y
                    u, v = dx * ca + dy * sa, -dx * sa + dy * ca
                    if abs(u) >= a_: continue
                    w = b_ * math.sqrt(max(0, 1 - (u / a_) ** 2)) * (1 - .3 * (u / a_))
                    if abs(v) > w: continue
                    lit = (-dx * .7 - dy * .7) / (a_ + 1)                # 左上が明るい
                    if z > .72 and lit > -.05: fam_, s = "O", 3 + (lit > .2) + (h(px, py, 41) > .8) - (h(int(x), int(y), 44) > .6)
                    elif z > .3: fam_, s = "P", 3 + (lit > 0) + (h(px, py, 42) > .85)
                    else: fam_, s = "E", 2 + (lit > .1) + (h(px, py, 43) > .85)
                    if abs(v) < .55 and u > -a_ * .6: s += 1                  # 葉脈
                    if abs(v) > w * .8 and lit < 0: s -= 1
                    put(px, py, f"{fam_}{max(0, min(7, s))}", d)
        else:
            kindc, rr = it[4], it[5]
            for py in range(int(y - rr - 1), int(y + rr + 2)):
                for px in range(int(x - rr - 1), int(x + rr + 2)):
                    dx, dy = px + .5 - x, py + .5 - y; q = (dx * dx + dy * dy) / (rr * rr)
                    if q > 1: continue
                    lit = (-dx - dy) / rr
                    f_ = "G" if kindc == "ripe" else "H"; s = 4 + (lit > .5) + (lit > .9) - (lit < -.5) - (q > .75)
                    if lit > .85 and kindc == "ripe": f_, s = "G", 6
                    put(px, py, f"{f_}{max(0, min(7, s))}", d + .01)
            put(int(x), int(y - rr), "E4", d + .02); put(int(x) - 1, int(y - rr + 1), "E3", d + .02)   # へた
    ys, xs = np.nonzero(code != ".."); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    code = code[y0 - 1: y1 + 2, x0 - 1: x1 + 2]
    return write(f"tomato{seed}", code.tolist(), "# トマトの株（葉は暗緑・青緑・黄緑、実は赤とだいだい）\n@size %d %d\n@outline sel" % (code.shape[1], code.shape[0]))

if __name__ == "__main__":
    for fn in (barrel, bucket, crate, logs, lambda: tomato(1), lambda: tomato(2), lambda: tomato(3)):
        p = fn(); code, img, pal = pxl.build(p)
        from PIL import Image
        base = os.path.splitext(p)[0]; Image.fromarray(img).save(base + ".png"); pxl.zoom(img, code, pal, 12).save(base + "_zoom.png")
        print(os.path.basename(p), img.shape[1], "x", img.shape[0])
