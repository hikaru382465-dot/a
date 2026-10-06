"""
関節（骨）の位置からキャラを作る：腕・足・体は「骨に沿った太さのある棒」として描く。
ポーズは POSE（関節の座標）だけで決まるので、歩きのコマも同じ絵で作れる。
python gen_rig.py [pose名] → sprites/rig_<pose>.pxl/.png/_big.png と ref/compare_rig.png
"""
import os, sys, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 30, 64
yy, xx = np.mgrid[0:H, 0:W]
P_ = lambda mask: mask
def poly(pts):
    px, py = xx + .5, yy + .5; ins = np.zeros((H, W), bool); j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        ins ^= ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi); j = i
    return ins
def bone(a, b, r0, r1=None):
    """aからbへの、太さが r0→r1 と変わる棒"""
    r1 = r0 if r1 is None else r1
    ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    t = np.clip(((xx + .5 - ax) * dx + (yy + .5 - ay) * dy) / L2, 0, 1)
    d = np.hypot(xx + .5 - (ax + t * dx), yy + .5 - (ay + t * dy))
    return d <= (r0 + (r1 - r0) * t)
code = None
def reset():
    global code; code = np.full((H, W), "..", dtype="<U2")
def paint(mask, fam, base, hi=1, lo=1):
    up = mask & ~np.roll(mask, 1, 0); lf = mask & ~np.roll(mask, 1, 1); dn = mask & ~np.roll(mask, -1, 0); rt = mask & ~np.roll(mask, -1, 1)
    for y, x in zip(*np.nonzero(mask)):
        s = base + (hi if (up[y, x] or lf[y, x]) else 0) - (lo if (dn[y, x] or rt[y, x]) else 0)
        code[y, x] = f"{fam}{max(0, min(7, s))}"
def dot(x, y, t):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H: code[y, x] = t
def line(a, b, t, only=None):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
    for k in range(n + 1):
        x = int(round(a[0] + (b[0] - a[0]) * k / max(1, n))); y = int(round(a[1] + (b[1] - a[1]) * k / max(1, n)))
        if 0 <= x < W and 0 <= y < H and code[y, x] != ".." and (only is None or code[y, x][0] == only): code[y, x] = t
def inner_edge(mask, color="U2", only=None):
    """このパーツのふちのうち、すでにある絵（他のパーツ）に接する部分を暗い線にして、パーツの境目をはっきりさせる"""
    out = ~mask; nb = np.zeros_like(mask)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): nb |= np.roll(np.roll(out & (code != '..'), dy, 0), dx, 1)
    for y, x in zip(*np.nonzero(mask & nb)): code[y, x] = color

def outline_between(mask_new, color="U2"):
    """新しく重ねるパーツのふちのうち、すでに絵がある所の1ドットを暗くして、パーツの境目をはっきりさせる"""
    e = np.zeros_like(mask_new)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(mask_new, dy, 0), dx, 1)
    return e & ~mask_new & (code != "..")

# ---------------------------------------------------------------- ポーズ（関節）
POSES = {
 "akimbo": dict(  # 手を腰に当てて、歩き出すところ
    neck=(16.5, 19), sh=(16, 22), hip=(14.5, 35),
    f_hip=(15.5, 35), f_knee=(18.5, 46.5), f_ankle=(19.5, 56.5), f_toe=(25.5, 60.5),
    b_hip=(13.5, 35), b_knee=(12, 46.5), b_ankle=(8.5, 56), b_toe=(6, 60.5),
    f_el=(21, 28.5), f_wr=(17.5, 33.5), b_el=(10.5, 28), b_wr=(12.5, 34),
    hem_f=(24.5, 47), hem_b=(5.8, 46.5)),
}
def build(pose):
    J = POSES[pose]; reset()
    head = pxl.build(os.path.join(HERE, "sprites", "part_head.pxl"))[0]
    # 1) 後ろの腕
    m1 = bone(J["sh"], J["b_el"], 2.0, 1.7); m2 = bone(J["b_el"], J["b_wr"], 1.7, 1.5)
    paint(m1, 'L', 3, 0, 1); paint(m2 & ~m1, 'V', 2, 0, 1); paint(bone(J["b_wr"], (J["b_wr"][0] + .5, J["b_wr"][1] + 1.2), 1.6), 'V', 2, 0, 1)
    # 2) かばん（腰の後ろ）と薬草
    bx, by = J["hip"][0] - 11, J["hip"][1] - 2
    bm = poly([(bx, by), (bx + 8.5, by), (bx + 9, by + 10.5), (bx + .5, by + 10.5)])
    paint(bm, 'J', 3, 1, 1); paint(poly([(bx, by), (bx + 8.5, by), (bx + 8.7, by + 4), (bx + .2, by + 4)]), 'J', 4, 1, 1)
    dot(bx + 4, by + 4.5, "B6"); dot(bx + 5, by + 4.5, "B6"); dot(bx + 4, by + 5.5, "B4")
    for (x, y, t) in ((1, -1, "E4"), (2, -2, "E4"), (2, -3, "E3"), (3, -4, "E4"), (5, -1, "E3"), (5, -2, "E4"), (6, -3, "E4"), (4, -1, "E5"),
                      (2, -5, "H5"), (3, -6, "H4"), (2, -6, "H6"), (6, -4, "H5"), (7, -5, "H4"), (6, -5, "H6")): dot(bx + x, by + y, t)
    # 3) 後ろの足と靴
    paint(bone(J["b_hip"], J["b_knee"], 2.2, 1.7) | bone(J["b_knee"], J["b_ankle"], 1.7, 1.5), 'R', 1, 1, 0)
    ax, ay = J["b_ankle"]; tx, ty = J["b_toe"]
    paint(poly([(ax - 1.9, ay - 2.5), (ax + 1.9, ay - 2.5), (ax + 2.4, ay + .5), (tx - 1.4, ty + 1), (tx - 1.8, ty - 1.6), (ax - 1.9, ay)]), 'D', 2, 1, 1)
    paint(poly([(tx - 1.8, ty), (ax + 2.4, ay + 3), (ax + 2.4, ty + 1.2), (tx - 1.9, ty + 1.2)]), 'D', 0, 0, 0)
    # 4) 前の足と靴
    paint(bone(J["f_hip"], J["f_knee"], 2.3, 1.8) | bone(J["f_knee"], J["f_ankle"], 1.8, 1.6), 'R', 3, 1, 1)
    line((J["f_knee"][0] + .5, J["f_knee"][1] + 1), (J["f_ankle"][0] + .8, J["f_ankle"][1] - 1), "R2", 'R')
    dot(J["f_knee"][0] - 1, J["f_knee"][1] - 1, "R5"); dot(J["f_knee"][0] - 1, J["f_knee"][1], "R4")
    ax, ay = J["f_ankle"]; tx, ty = J["f_toe"]
    paint(poly([(ax - 1.9, ay - 3), (ax + 2, ay - 3), (ax + 2, ay + .5), (tx + .6, ty - 1.4), (tx + .8, ty + 1.3), (ax - 2, ty + 1.3)]), 'D', 3, 1, 1)
    paint(poly([(ax - 1.9, ay - 3), (ax + 2, ay - 3), (ax + 2, ay - 1), (ax - 1.9, ay - 1)]), 'D', 5, 1, 0)       # 折り返し
    paint(poly([(ax - 2, ty + .2), (tx + .8, ty + .2), (tx + .8, ty + 1.4), (ax - 2, ty + 1.4)]), 'D', 0, 0, 0)
    dot(ax + .5, ay - .5, "B6"); dot(ax + 1.2, ay - .5, "B4")
    # 5) スカート（腰から、ひだが流れて、すそが広がる）
    hx, hy = J["hip"]; waistL, waistR = hx - 3.6, hx + 4.2
    sk = poly([(waistL, hy - 3.5), (waistR, hy - 3.5), (waistR + .6, hy - .5), (J["hem_f"][0], J["hem_f"][1] - .4), (hx + 10, J["hem_f"][1] + 1.0), (hx + 8, J["hem_f"][1] + 2.4), (hx + 5.5, J["hem_f"][1] + 1.2),
               (hx + 3, J["hem_f"][1] + 2.6), (hx, J["hem_f"][1] + 1.4), (hx - 3, J["hem_f"][1] + 2.4), (J["hem_b"][0] + 1, J["hem_b"][1] + 1.6), (J["hem_b"][0] - .5, J["hem_b"][1] + 1.2), (J["hem_b"][0], J["hem_b"][1] - .5), (waistL - .6, hy - .5)])
    paint(sk, 'b', 4, 1, 1)
    for k, f in enumerate((.25, .5, .75)):
        a = (waistL + (waistR - waistL) * f, hy - 2.0); b_ = (J["hem_b"][0] + (J["hem_f"][0] - J["hem_b"][0]) * (f + .04), J["hem_f"][1] - 2)
        line(a, b_, "b2" if k != 1 else "b3", 'b'); line((a[0] + 1, a[1] + .5), (b_[0] + 1.2, b_[1] - .5), "b6", 'b')
    paint(poly([(J["hem_b"][0] - .5, J["hem_b"][1] - 1.2), (J["hem_f"][0] + .5, J["hem_f"][1] - 2.2), (hx + 10, J["hem_f"][1] + 1.2), (hx, J["hem_f"][1] + 2.4), (J["hem_b"][0] - .5, J["hem_b"][1] + 1.6)]) & sk, 'L', 5, 1, 1)
    # 6) 胴（肩幅→ウエスト→腰）、ベルト、えり
    sx, sy = J["sh"]
    tm = poly([(sx - 4.6, sy - 1), (sx + 3.4, sy - 1.2), (sx + 3.7, sy + 4.5), (hx + 3.2, hy - 4), (hx + 3.8, hy - 1), (hx - 4, hy - .5), (hx - 3.4, hy - 5), (sx - 5.2, sy + 4.5)])
    paint(tm, 'b', 4, 1, 1)
    paint(poly([(sx - 4.6, sy - 1), (sx - 1.5, sy - 1.2), (sx - 1.8, sy + 5), (hx - 3.4, hy - 5), (sx - 5.2, sy + 4.5)]) & tm, 'b', 2, 0, 1)
    paint(poly([(sx + .2, sy - 1.1), (sx + 3.4, sy - 1.2), (sx + 2.4, sy + 4), (sx + 1, sy + 4)]) & tm, 'L', 5, 1, 1)
    line((sx - 1.5, sy + 3), (hx - 3.2, hy - 6), "b2", 'b'); line((sx - .5, sy + 1.8), (sx - 1, sy + 4.5), "b6", 'b')
    paint(poly([(hx - 3.9, hy - 4.6), (hx + 3.9, hy - 4.8), (hx + 4, hy - 1.6), (hx - 3.8, hy - 1.4)]), 'J', 3, 1, 1)
    dot(hx + 1.5, hy - 3.6, "B6"); dot(hx + 2.5, hy - 3.6, "B6"); dot(hx + 1.5, hy - 2.6, "B4"); dot(hx + 2.5, hy - 2.6, "B4")
    # 7) かばんのひも
    line((sx + 2.5, sy - .5), (hx - 4, hy - 3), "J3"); line((sx + 3.5, sy - .5), (hx - 3, hy - 3), "J2")
    # 8) スカーフ（首にまいて、結び目が後ろにたれる）
    nx, ny = J["neck"]
    paint(poly([(nx - 4.8, ny - 1.2), (nx + 2.8, ny - 1.2), (nx + 3.6, ny + 2.6), (nx - 4.6, ny + 3.6)]), 'c', 4, 1, 1)
    paint(poly([(nx - 5.6, ny + .5), (nx - 2.5, ny + .5), (nx - 3.5, ny + 11), (nx - 6.8, ny + 9.5)]), 'c', 3, 1, 1)
    line((nx - 3.5, ny + 1), (nx + 3, ny + .6), "c2"); line((nx - 4, ny + 4), (nx - 5.5, ny + 9), "c2"); dot(nx - 1, ny - 1, "c6"); dot(nx, ny - 1, "c6")
    # 9) 前の腕（肩→ひじ→手首→手）
    up_ = bone(J["sh"], J["f_el"], 2.3, 2.0); fo_ = bone(J["f_el"], J["f_wr"], 1.9, 1.6)
    for msk in (up_, fo_ & ~up_):
        ring = msk & ~(np.roll(msk, 1, 0) & np.roll(msk, -1, 0) & np.roll(msk, 1, 1) & np.roll(msk, -1, 1))
        for y, x in zip(*np.nonzero(ring)): code[y, x] = 'U2' if code[y, x] != '..' else code[y, x]
    paint(up_, 'L', 5, 1, 1)
    wx, wy = J["f_wr"]
    paint(fo_ & ~up_, 'V', 4, 1, 1)
    paint(bone((wx, wy + .2), (wx - 1.2, wy + 3.2), 1.7, 1.4), 'V', 4, 1, 1)
    ex, ey = J["f_el"]
    paint(poly([(ex - 2.4, ey - .4), (ex + 2.4, ey - 1.0), (ex + 2.2, ey + 1.6), (ex - 2.2, ey + 1.8)]) & fo_ | (poly([(ex - 2.4, ey - 1.2), (ex + 2.4, ey - 1.6), (ex + 2.3, ey + .6), (ex - 2.3, ey + 1)]) & up_), 'L', 7, 1, 1)   # まくった折り返し
    line(J["sh"], J["f_el"], "L7", 'L'); line((ex - .5, ey - 2), (J["sh"][0] + 1, J["sh"][1] + 1), "L3", 'L')
    # 10) 頭（ネックの位置を、首の中央にあわせる）
    ox, oy = int(round(nx - 14.5)) + 0, 0
    for y in range(head.shape[0]):
        for x in range(head.shape[1]):
            if head[y, x] != ".." and 0 <= x + ox < W and 0 <= y + oy < H: code[y + oy, x + ox] = head[y, x]
    # 11) パーツの境目の線と、外側の輪郭
    m = code != ".."; e = np.zeros_like(m)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(m, dy, 0), dx, 1)
    for y, x in zip(*np.nonzero(e & ~m)): code[y, x] = "U1"
    return code.copy()

def run(pose):
    c = build(pose); p = os.path.join(HERE, "sprites", f"rig_{pose}.pxl")
    with open(p, "w") as f:
        f.write(f"# 関節から作ったキャラ ポーズ={pose}（{W}×{H}）\n@size {W} {H}\n")
        for r in c: f.write(" ".join(r) + "\n")
    _, img, _ = pxl.build(p); Image.fromarray(img).save(p.replace(".pxl", ".png"))
    k = 10
    def up(arr):
        im = Image.fromarray(arr); bg = Image.new("RGBA", (im.width * k, im.height * k), (236, 234, 225, 255)); bg.alpha_composite(im.resize((im.width * k, im.height * k), Image.NEAREST)); return bg.convert("RGB")
    B_ = up(img); B_.save(p.replace(".pxl", "_big.png"))
    ref = Image.open(os.path.join(HERE, "ref", "source_sheet.png")).convert("RGB").crop((140, 95, 275, 390)); k2 = B_.height / ref.height
    A_ = ref.resize((int(ref.width * k2), B_.height), Image.NEAREST)
    out = Image.new("RGB", (A_.width + B_.width + 30, B_.height), (236, 234, 225)); out.paste(A_, (0, 0)); out.paste(B_, (A_.width + 30, 0)); out.save(os.path.join(HERE, "ref", "compare_rig.png"))
if __name__ == "__main__": run(sys.argv[1] if len(sys.argv) > 1 else "akimbo"); print("ok")
