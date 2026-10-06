"""
参考の絵から、色の系統（8段の明るさ）を作ってパレットに足す。
python palette_from_ref.py  → palette.json に系統 U〜Z（輪郭・肌・スカート・上着・髪や靴・脚）を追加し、読み取った絵を作り直す
"""
import json, os, colorsys
import numpy as np
from PIL import Image
import pxl

HERE = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(HERE, "ref", "source_sheet.png")
a = np.asarray(Image.open(src).convert("RGB")).astype(float)
box, p, phx, phy = (150, 265, 105, 380), 4.25, 1.5, 4.0
x0, x1, y0, y1 = box; bg = a[5, 5]
cols = int((x1 - x0) / p) + 1; rows = int((y1 - y0) / p) + 1
cell = np.zeros((rows, cols, 3)); alpha = np.zeros((rows, cols), bool)
for r in range(rows):
    for c in range(cols):
        cx = x0 + phx + c * p; cy = y0 + phy + r * p
        blk = a[int(cy - p * .25):int(cy + p * .25) + 1, int(cx - p * .25):int(cx + p * .25) + 1].reshape(-1, 3)
        if len(blk): m = np.median(blk, 0); cell[r, c] = m; alpha[r, c] = np.abs(m - bg).sum() > 45
ys, xs = np.nonzero(alpha); r0, r1, c0, c1 = ys.min(), ys.max(), xs.min(), xs.max()
cell, alpha = cell[r0:r1 + 1, c0:c1 + 1], alpha[r0:r1 + 1, c0:c1 + 1]
# 色をまとめる（細かく：36色）
q = Image.fromarray(cell.astype(np.uint8)).quantize(36, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
pal = np.array(q.getpalette()[:108]).reshape(-1, 3); idx = np.asarray(q)
used = np.unique(idx[alpha])
def hls(c): h, l, s = colorsys.rgb_to_hls(*(np.array(c) / 255)); return h * 360, l, s
FAMS = {"U": "輪郭の暗いえんじ紫", "V": "肌", "W": "青緑のスカート", "X": "赤い上着", "Y": "髪・靴・かばんの茶色", "Z": "脚のくすんだ紫茶"}
groups = {k: [] for k in FAMS}
for i in used:
    c = pal[i]; h, l, s = hls(c)
    if l < .2 and 290 < h < 350: g = "U"
    elif 170 < h < 235: g = "W"
    elif 12 < h < 40 and l > .62: g = "V"
    elif (h < 12 or h > 350) and l > .44 and s > .45: g = "X"
    elif 335 <= h < 360 and l < .36 and s < .35: g = "Z"
    elif l < .2: g = "U"
    else: g = "Y"
    groups[g].append(c)
def ramp8(cs):
    cs = sorted(cs, key=lambda c: hls(c)[1])
    if len(cs) == 1: cs = [cs[0] * .5, cs[0], np.minimum(255, cs[0] * 1.3 + 20)]
    xs = np.linspace(0, 1, len(cs)); xi = np.linspace(0, 1, 8)
    return ["#%02x%02x%02x" % tuple(int(round(np.interp(t, xs, [c[k] for c in cs]))) for k in range(3)) for t in xi]
path = os.path.join(HERE, "palette.json"); P = json.load(open(path))
print({k: len(v) for k, v in groups.items()})
for k in [k for k in FAMS if not groups[k]]: FAMS.pop(k)
for k, nm in FAMS.items(): P["families"][k] = {"name": "参考キャラ：" + nm, "ramp": ramp8(groups[k])}
json.dump(P, open(path, "w"), ensure_ascii=False, indent=1)
for k in FAMS: print(k, FAMS[k], len(groups[k]), "色 →", P["families"][k]["ramp"])
# 読み取り直し：新しい系統だけから一番近い色を選ぶ
pl, _ = pxl.load_palette(); names = [(f, i) for f in FAMS for i in range(8)]
cl = np.array([pl[f][i] for f, i in names], float)
H, W = alpha.shape; rowsx = []
for y in range(H):
    r = []
    for x in range(W):
        if not alpha[y, x]: r.append(".."); continue
        d = ((cl - cell[y, x]) ** 2).sum(1); f, i = names[d.argmin()]; r.append(f"{f}{i}")
    rowsx.append(r)
pp = os.path.join(HERE, "sprites", "girl_src01.pxl")
open(pp, "w").write(f"# 参考のキャラ（左端）を1ドットずつ読み取って、参考キャラ用の系統（U〜Z）で置きかえたもの\n@size {W} {H}\n" + "\n".join(" ".join(r) for r in rowsx) + "\n")
code, img, _ = pxl.build(pp); Image.fromarray(img).save(os.path.join(HERE, "sprites", "girl_src01.png"))
orig = Image.open(src).convert("RGB").crop((140, 95, 275, 390)); k = 8
def up(im):
    bgc = Image.new("RGBA", (im.width * k, im.height * k), (236, 234, 225, 255)); bgc.alpha_composite(im.convert("RGBA").resize((im.width * k, im.height * k), Image.NEAREST)); return bgc
A_ = orig.resize((orig.width * 2, orig.height * 2), Image.LANCZOS).convert("RGBA")
B_ = up(Image.fromarray(np.dstack([cell.astype(np.uint8), (alpha * 255).astype(np.uint8)])))
C_ = up(Image.fromarray(img))
out = Image.new("RGBA", (A_.width + B_.width + C_.width + 40, max(A_.height, B_.height, C_.height)), (236, 234, 225, 255))
out.paste(A_, (0, 0)); out.paste(B_, (A_.width + 20, 0)); out.paste(C_, (A_.width + B_.width + 40, 0)); out.convert("RGB").save(os.path.join(HERE, "ref", "compare_girl2.png"))
