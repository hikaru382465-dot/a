"""
漂流物を海にうかべた絵（8コマの輪）。細かい版（assets/items/hd/*.png）を、水面で切って、波・あわ・波紋をつける。
python gen_items_float.py → assets/items/float/<名前>_float.gif（1つずつ）, items_float_hd.gif（全部ならべ）, items_float_hd_frame0.png
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "assets", "items", "hd"); OUT = os.path.join(HERE, "..", "assets", "items", "float"); os.makedirs(OUT, exist_ok=True)
pal, _ = pxl.load_palette()
def col(f, s): return tuple(int(v) for v in pal[f][int(max(0, min(7, s)))])
BAY = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
TAU = math.tau
NF = 8
# 名前: (水面の位置＝絵の上から何割か, ゆれの大きさ, 波紋のおおきさ)
ITEMS = {"rope": (.66, 1.0, 1.0), "stone_round": (.70, .5, .9), "stone_rock": (.72, .5, .9), "cloth": (.58, 1.2, 1.1), "bottle": (.52, 1.2, 1.0),
         "bag": (.70, 1.0, 1.0), "coconut": (.58, 1.0, .9), "coconut_cut": (.62, 1.0, .9)}

def sea(w, h, t, ox=0):
    Y, X = np.mgrid[0:h, 0:w]; X = X + ox
    hh = np.sin(TAU * (X / 31.0 + Y / 11.0 - t)) * .5 + np.sin(TAU * (X / 17.0 - Y / 7.0 + t * 2)) * .35
    idx = np.clip(np.floor((hh + 1) / 2 * 2.4 + (BAY[Y % 4, X % 4] - .5) * .6).astype(int) + 2, 2, 4)
    img = np.zeros((h, w, 4), np.uint8)
    for v in (2, 3, 4): img[idx == v, :3] = col('w', v)
    img[..., 3] = 255; return img

def frame(spr, spec, t, W, H, ox=0):
    wl_f, bob_a, rip = spec
    h, w = spr.shape[:2]
    img = sea(W, H, t, ox)
    cx = W // 2; wl = int(H * .55)                                  # 画面の水面（絵の水面の位置）
    bob = math.sin(TAU * t) * bob_a; sway = math.sin(TAU * t + 1.0) * 1.0
    Y, X = np.mgrid[0:H, 0:W]
    # 波紋（水面の高さで楕円）
    for k, (rad, sv) in enumerate(((w * .62 * rip + 6 * ((t + .0) % 1), 6), (w * .62 * rip + 6 * ((t + .5) % 1), 5))):
        fade = 1 - ((t + k * .5) % 1)
        d = np.hypot((X + .5 - cx) / rad, (Y + .5 - (wl + 1)) / (rad * .26))
        mk = (np.abs(d - 1) < 1.1 / rad) & (BAY[(Y + 1) % 4, X % 4] < .25 + .7 * fade)
        img[mk, :3] = col('w', sv)
    # スプライトを置く：絵の水面ライン（上から wl_f）を、画面の wl に合わせる
    y0 = int(round(wl - h * wl_f + bob)); x0 = int(round(cx - w / 2 + sway))
    lapx = np.arange(W)
    wave = np.sin(TAU * (lapx / 13.0 + t)) * .9 + np.sin(TAU * (lapx / 6.0 - t * 2)) * .5            # 水面のゆれ（行ごと）
    for yy in range(h):
        Yw = y0 + yy
        if not (0 <= Yw < H): continue
        for xx in range(w):
            if spr[yy, xx, 3] == 0: continue
            Xw = x0 + xx
            if not (0 <= Xw < W): continue
            depth = Yw - (wl + wave[Xw])
            if depth < 0: img[Yw, Xw] = spr[yy, xx]
            elif depth < 1.0: img[Yw, Xw, :3] = col('w', 7); img[Yw, Xw, 3] = 255                                            # あわ（水ぎわの白）
            elif depth < 4.0:                                                                                                 # 水中：うっすら見える
                if BAY[Yw % 4, Xw % 4] < .55 - depth * .1: img[Yw, Xw, :3] = (spr[yy, xx, :3] * .45 + np.array(col('w', 3)) * .55).astype(np.uint8)
    # 水ぎわの小さなあわ（スプライトのふちにそって）
    return img

def run():
    sprs = {n: np.array(Image.open(os.path.join(SRC, n + ".png")).convert("RGBA")) for n in ITEMS}
    allf = [[] for _ in range(NF)]
    cells = []
    for n, spec in ITEMS.items():
        spr = sprs[n]; h, w = spr.shape[:2]
        W = w + 28; H = int(h * (spec[0] + 1.1) * .62) + 26
        H = max(H, int(h * .7) + 28)
        frames = [frame(spr, spec, i / NF, W, H, 7 * 0) for i in range(NF)]
        g = [Image.fromarray(f).resize((W * 6, H * 6), Image.NEAREST).convert("RGB") for f in frames]
        g[0].save(os.path.join(OUT, n + "_float.gif"), save_all=True, append_images=g[1:], duration=150, loop=0)
        Image.fromarray(frames[0]).resize((W * 6, H * 6), Image.NEAREST).convert("RGB").save(os.path.join(OUT, n + "_float.png"))
        cells.append((n, frames, W, H))
    cw = max(c[2] for c in cells); chh = max(c[3] for c in cells)
    cols = 4; rows = 2
    out = []
    for i in range(NF):
        sh = Image.new("RGB", (cw * cols, chh * rows), (24, 54, 78))
        for j, (n, frames, W, H) in enumerate(cells):
            im = Image.fromarray(frames[i]).convert("RGB"); sh.paste(im, ((j % cols) * cw + (cw - W) // 2, (j // cols) * chh + (chh - H) // 2))
        out.append(sh.resize((sh.width * 3, sh.height * 3), Image.NEAREST))
    out[0].save(os.path.join(OUT, "items_float_hd.gif"), save_all=True, append_images=out[1:], duration=150, loop=0)
    out[0].save(os.path.join(OUT, "items_float_hd_frame0.png")); print("ok")
run()
