"""
写真（背景が白い物）を、ドット絵にする：形（シルエット）と明暗を写真から取り、パレットの段階に切る。
python photo_to_pixel.py ref/smg_photo.jpg 幅 名前 → sprites/名前.png/_big.png と比べの絵
"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))

def run(path, W, name, black_fam='S', accent_fam='G'):
    im = Image.open(path).convert("RGB")
    H = int(round(im.height * W / im.width))
    a = np.asarray(im.resize((W * 4, H * 4), Image.LANCZOS)).astype(float)
    # 背景（白）をはずす
    dist_bg = (255 - a).sum(2)
    mask4 = dist_bg > 60
    mask4 = np.asarray(Image.fromarray((mask4 * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))) > 127
    small = np.asarray(im.resize((W, H), Image.LANCZOS)).astype(float)
    m = np.asarray(Image.fromarray((mask4 * 255).astype(np.uint8)).resize((W, H), Image.BOX)).astype(float) / 255 > .5
    lum = small @ np.array([.3, .59, .11])
    # 明暗を引きのばす（ほぼ黒の物なので、内側の範囲を広げる）
    v = lum[m]; lo, hi = np.percentile(v, 2), np.percentile(v, 99.5)
    t = np.clip((lum - lo) / (hi - lo + 1e-6), 0, 1) ** .8
    # 局所コントラスト：まわりとの差をつよめて、部品の境目を出す
    blur = np.asarray(Image.fromarray((t * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(float) / 255
    t = np.clip(t + (t - blur) * 1.8, 0, 1)
    pal, _ = pxl.load_palette()
    B = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    yy_, xx_ = np.mgrid[0:H, 0:W]
    idx = np.clip(np.floor(t * 6.3 + (B[yy_ % 4, xx_ % 4] - .5) * .55).astype(int), 0, 6)   # 青灰の鋼（S0〜S6）。網点で、なめらかな明暗を出す
    red = (small[..., 0] > small[..., 1] + 45) & (small[..., 0] > small[..., 2] + 45) & m
    code = np.full((H, W), "..", dtype="<U2")
    for y in range(H):
        for x in range(W):
            if not m[y, x]: continue
            code[y, x] = f"{accent_fam}{3 + int(t[y, x] * 3)}" if red[y, x] else f"{black_fam}{idx[y, x]}"
    # ふちの光：上と左が空いているふちは明るく、下と右は暗く。シルエットを読みやすくする
    up = m & ~np.roll(m, 1, 0); lf = m & ~np.roll(m, 1, 1); dn = m & ~np.roll(m, -1, 0); rt = m & ~np.roll(m, -1, 1)
    for y, x in zip(*np.nonzero(m)):
        c = code[y, x]
        if c[0] == accent_fam: continue
        s_ = int(c[1])
        if up[y, x] or lf[y, x]: s_ = min(7, s_ + 1)
        elif dn[y, x] or rt[y, x]: s_ = max(0, s_ - 0)
        code[y, x] = f"{c[0]}{s_}"
    # ぽつんと浮いた1ドットを、まわりの色にならす
    out = code.copy()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            c = code[y, x]
            if c == "..": continue
            nb = [code[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if c not in nb and c[0] != accent_fam:
                cand = [n for n in nb if n != ".."]
                if len(cand) >= 3: out[y, x] = max(set(cand), key=cand.count)
    code = out
    return code, im

if __name__ == "__main__":
    path, W, name = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    code, im = run(path, W, name); H = code.shape[0]
    p = os.path.join(HERE, "sprites", name + ".pxl")
    with open(p, "w") as f:
        f.write(f"# 写真から作ったドット絵 {W}×{H}\n@size {W} {H}\n")
        for r in code: f.write(" ".join(r) + "\n")
    c, img, _ = pxl.build(p); Image.fromarray(img).save(p.replace(".pxl", ".png"))
    k = 6; big = Image.fromarray(img).resize((W * k, H * k), Image.NEAREST)
    bg = Image.new("RGBA", big.size, (84, 92, 110, 255)); bg.alpha_composite(big)
    ph = im.resize(big.size, Image.LANCZOS)
    out = Image.new("RGB", (big.width * 2 + 20, big.height), (84, 92, 110)); out.paste(ph, (0, 0)); out.paste(bg.convert("RGB"), (big.width + 20, 0)); out.save(p.replace(".pxl", "_compare.png")); print("ok", W, H)
