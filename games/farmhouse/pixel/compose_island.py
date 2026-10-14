"""
島のマップを、パーツを組み合わせて作る。python compose_island.py [parts]
  island_map.json（地形・桟橋・小屋・木・小物の位置）を読み、island_parts.py の部品を奥から手前へ置く。
  parts を付けると、パーツ1つずつの絵も assets/island/parts/ に出す。
出力：assets/island/island.png（絵）, island_water.gif（海と反射 8コマ）, island_depth.png/island_mask.png（エンジン用の奥行き・水のマスク）
"""
import os, sys, json, math
import numpy as np
from PIL import Image
want_parts = "parts" in sys.argv
import island_parts as P
import iso_reflect as R
I = P.I
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "assets", "island"); os.makedirs(os.path.join(OUT, "parts"), exist_ok=True)
M = json.load(open(os.path.join(HERE, "island_map.json")))
I.OX, I.OY = 960.0, 650.0
NF = 8

def reset():
    I.fam[:] = -1; I.shd[:] = 0; I.zb[:] = np.inf; I.oid[:] = 0; I.SHADOWS.clear()

def land_part():
    global TER
    for h in M["huts"]: P.hut_cast = None
    TER = P.Terrain(M["terrain"])
def shadows():                      # 影は地面を描く前に決める
    for h in M["huts"]:
        x0, y0, w, d = h["x0"], h["y0"], h["w"], h["d"]; wh = h.get("wh", 2.3); rise = h.get("rise", 2.4)
        I.cast([(xx, yy, z) for xx in (x0, x0 + w) for yy in (y0, y0 + d) for z in (0, wh)] + [(x0 - .5, y0 + d / 2, wh + rise), (x0 + w + .5, y0 + d / 2, wh + rise)])
    for (x, y) in M["trees"]:
        I.cast([(x + dx, y + dy, 0) for dx in (-.9, .9) for dy in (-.9, .9)] + [(x, y, 4.5)], k=(.45, .3))
def draw_hut(h):
    h = dict(h); P.hut(h.pop("x0"), h.pop("y0"), h.pop("w"), h.pop("d"), **{k: v for k, v in h.items()})
def draw_pier():
    p = M["pier"]; P.pier(p["x"], p["y_from"], p["y_to"], p["width"]); P.boat(M["boat"]["x"], M["boat"]["y"])
def draw_props():
    P.props_at([tuple(p) for p in M["props"]])
def draw_nature():
    for (x, y) in M["trees"]: P.tree(x, y, 2.6, .95, 'c')
    for (x, y) in M["bushes"]: P.bush(x, y)
    for (x, y, r) in M["rocks"]: P.rock(x, y, r)

def snap(name):
    ok = I.fam >= 0
    if not ok.any(): return
    ys, xs = np.nonzero(ok); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb = np.zeros((I.H, I.W, 4), np.uint8); rgb[ok, :3] = I.TABLE[I.fam[ok], I.shd[ok]]; rgb[ok, 3] = 255
    Image.fromarray(rgb[y0:y1, x0:x1]).resize(((x1 - x0) // 2, (y1 - y0) // 2), Image.NEAREST).save(os.path.join(OUT, "parts", name + ".png"))

if want_parts:                      # パーツ1つずつ（影なし・単独）
    TER = P.Terrain(M["terrain"])
    reset(); TER.draw(); snap("terrain")
    reset(); draw_pier(); snap("pier_boat")
    for h in M["huts"]:
        reset(); draw_hut(h); I.outline(); snap(h["name"])
    reset(); draw_nature(); snap("trees_rocks")
    print("parts ok")

# ---- 全体
reset(); TER = P.Terrain(M["terrain"])
shadows()
TER.draw()
for (x, y) in M["trees"]: I.drop((x, y), 1.4, .7, 2)
draw_pier()
for h in M["huts"]: draw_hut(dict(h))
draw_nature(); draw_props()
SCENE = (I.fam.copy(), I.shd.copy(), I.zb.copy(), I.oid.copy())

def vignette():
    yy, xx = np.mgrid[0:I.H, 0:I.W]; r = np.hypot((xx - I.W / 2) / (I.W / 2), (yy - I.H / 2) / (I.H / 2))
    B = R.BAY
    dk = (r > .72) * (B < (r - .72) * 3.2) + (r > .9) * (B < (r - .9) * 6)
    ok = I.fam >= 0; I.shd[ok] = np.maximum(0, I.shd[ok] - dk[ok].astype(np.int8))

def frame(i):
    t = i / NF
    I.fam[:], I.shd[:], I.zb[:], I.oid[:] = (a.copy() for a in SCENE)
    I.face((-40, -40, P.WZ), (80, 0, 0), (0, 80, 0), R.sea_tex(t), 0, 9)
    # 反射（iso_reflect と同じしくみ）
    H, W = I.H, I.W
    ys, xs = np.nonzero((I.oid > 0) & (I.oid != 9) & (I.fam >= 0)); sy = ys + .5
    z = (-I.zb[ys, xs] - 1.2247 * (sy - I.OY) / I.A) / 2; keep = z > 0.1
    ys, xs, z = ys[keep], xs[keep], z[keep]; dz = z - P.WZ
    ny = ys + np.round(2 * I.HZ * dz).astype(int)
    wave = np.sin(R.TAU * (ny / 17.0 + t)) * (1.0 + 3.2 * np.clip(dz / 6.0, 0, 1)) + np.sin(R.TAU * (ny / 7.0 - 2 * t)) * 1.2
    nx = xs + np.round(wave).astype(int)
    ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W); ys, xs, ny, nx, dz = ys[ok], xs[ok], ny[ok], nx[ok], dz[ok]
    fadep = 1 - .8 * np.clip(dz / 5.0, 0, 1)
    vis = (R.BAY[(ny >> 1) << 1, (nx >> 1) << 1] < fadep * .8) & (I.oid[ny, nx] == 9)
    sy_, sx_, dy_, dx_ = ys[vis], xs[vis], ny[vis], nx[vis]
    o = np.argsort(-I.zb[sy_, sx_]); sy_, sx_, dy_, dx_ = sy_[o], sx_[o], dy_[o], dx_[o]
    lut = np.zeros((I.TABLE.shape[0], 8, 2), np.int8)
    for f_ in range(I.TABLE.shape[0]):
        for s_ in range(8): lut[f_, s_] = R.to_water(f_, s_)
    sf, ss = I.fam[sy_, sx_], I.shd[sy_, sx_]
    I.fam[dy_, dx_] = lut[sf, ss, 0]; I.shd[dy_, dx_] = lut[sf, ss, 1]
    # 岸の水ぎわ：陸のすぐそばの海を少し明るく（あわ）
    vignette()
    rgb = np.zeros((H, W, 3), np.uint8); okp = I.fam >= 0; rgb[okp] = I.TABLE[I.fam[okp], I.shd[okp]]
    return Image.fromarray(rgb)

fr = [frame(i) for i in range(NF)]
fr[0].save(os.path.join(OUT, "island.png"))
fr[0].resize((960, 540), Image.NEAREST).save(os.path.join(OUT, "island_half.png"))
g = [f.resize((960, 540), Image.NEAREST) for f in fr]
g[0].save(os.path.join(OUT, "island_water.gif"), save_all=True, append_images=g[1:], duration=140, loop=0)
# エンジン用：陸と物（水より上）のマスク、奥行き
I.fam[:], I.shd[:], I.zb[:], I.oid[:] = (a.copy() for a in SCENE)
land = (I.fam >= 0); Image.fromarray((land * 255).astype(np.uint8)).save(os.path.join(OUT, "island_mask.png"))
d = np.where(land, I.zb, np.nan); lo, hi = np.nanmin(d), np.nanmax(d)
Image.fromarray(np.where(land, 255 - (d - lo) / (hi - lo) * 255, 0).astype(np.uint8)).save(os.path.join(OUT, "island_depth.png"))
print("ok")
