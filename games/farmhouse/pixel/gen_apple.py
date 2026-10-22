"""
りんごの絵。python gen_apple.py → assets/items/apple.png（32×32）, apple_x8.png, apple_16.png（16×16の小さい版）, apple_bitten.png（かじったあと）
形＝2つの円（くぼみあり）→球のかげ（面で4段）→大きなつや→下の反射光→茎・葉→暗い赤のふち。パレットの色だけ。
"""
import os, math
import numpy as np
from PIL import Image
import pxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "items"); os.makedirs(OUT, exist_ok=True)
pal, _ = pxl.load_palette()
def col(f, s): return tuple(int(v) for v in pal[f][int(max(0, min(7, s)))])
LIGHT = np.array([-.5, -.6, .62]); LIGHT /= np.linalg.norm(LIGHT)

def apple(S=32, bitten=False):
    k = S / 32.0
    a = np.zeros((S, S, 4), np.uint8); Y, X = np.mgrid[0:S, 0:S]; x = (X + .5) / k; y = (Y + .5) / k
    # 形：2つの円＋下をすぼめる。上の真ん中にくぼみ
    c1 = ((x - 12.2) / 10.6) ** 2 + ((y - 18.5) / 10.8) ** 2 <= 1
    c2 = ((x - 19.8) / 10.6) ** 2 + ((y - 18.5) / 10.8) ** 2 <= 1
    low = ((x - 16) / 9.8) ** 2 + ((y - 23.5) / 8.5) ** 2 <= 1
    body = c1 | c2 | low
    body &= ~(((x - 16) / 3.0) ** 2 + ((y - 7.2) / 2.4) ** 2 <= 1)                 # 上のくぼみ
    body0 = body.copy()
    bite = (body0 & (((x - 26.0) / 6.2) ** 2 + ((y - 19) / 5.6) ** 2 <= 1)) if bitten else np.zeros_like(body)
    body = body0 & ~bite
    # 球のかげ
    u = (x - 16) / 14.0; v = (y - 18.5) / 12.5; r2 = u * u + v * v
    z = np.sqrt(np.clip(1 - r2, 0, 1)); lam = (np.stack([u, v, z], -1) * LIGHT).sum(-1)
    s = 3 + np.round((lam - .3) * 3.6)
    s = np.clip(s, 1, 6)
    # 面を大きく：段を3つにまとめる（暗・中・明）
    lev = np.where(lam > .62, 5, np.where(lam > .28, 4, np.where(lam > -.05, 3, 2)))
    fam = np.full((S, S), 'G')
    col_idx = lev.astype(int)
    # 下の反射光（ふちの近く）
    refl = body & (lam < .0) & (v > .15) & (u > -.1) & (r2 > .38)
    col_idx = np.where(refl, 4, col_idx)
    # 黄色がかった部分（上のくぼみのまわり）：色ずらし
    yel = body & (np.hypot((x - 16) / 6.5, (y - 9.5) / 4.5) < 1) & (lam > .1)
    for ci, f in ((2, 'G'),):
        pass
    for yy, xx in zip(*np.nonzero(body)):
        f = 'H' if yel[yy, xx] else 'G'; sh = col_idx[yy, xx]
        if f == 'H': sh = min(7, sh + 1)
        a[yy, xx, :3] = col(f, sh); a[yy, xx, 3] = 255
    # 大きなつや（左上）と、小さなつや
    g1 = body & (((x - 10.5) / 2.2) ** 2 + ((y - 14.0) / 4.0 + (x - 10.5) * .06) ** 2 <= 1)
    a[g1, :3] = col('G', 7); a[g1, 3] = 255
    g2 = body & (((x - 9.0) / 1.2) ** 2 + ((y - 21.0) / 1.0) ** 2 <= 1)
    a[g2, :3] = col('G', 7); a[g2, 3] = 255
    # 茎
    st = (np.abs(x - (16 + (y - 7) * -.18)) < 1.2) & (y > 1.6) & (y < 8.5)
    a[st, :3] = col('D', 3); a[st, 3] = 255
    st2 = (np.abs(x - (16 + (y - 7) * -.18) + .6) < .5) & (y > 2) & (y < 7)
    a[st2, :3] = col('D', 5); a[st2, 3] = 255
    # 葉
    lf = (((x - 22.6) / 5.4) ** 2 + ((y - 4.4 - (x - 22.6) * .35) / 2.4) ** 2 <= 1) & (x > 17.5)
    for yy, xx in zip(*np.nonzero(lf)):
        top = (y[yy, xx] - 4.4 - (x[yy, xx] - 22.6) * .35) < 0
        a[yy, xx, :3] = col('O', 5 if top else 3); a[yy, xx, 3] = 255
    rib = lf & (np.abs(y - 4.4 - (x - 22.6) * .35) < .5); a[rib, :3] = col('O', 2); a[rib, 3] = 255
    # 断面（かじったあと）：白い果肉と、ふちの黄色い皮ぎわ
    if bitten:
        for yy, xx in zip(*np.nonzero(bite)):
            d = ((x[yy, xx] - 26.0) / 6.2) ** 2 + ((y[yy, xx] - 19) / 5.6) ** 2
            a[yy, xx, :3] = col('n', 7 if d < .55 else 6 if d < .85 else 5); a[yy, xx, 3] = 255
        seed = bite & (np.abs(x - 24.8) < 1.0) & (np.abs(y - 19) < 1.7); a[seed, :3] = col('D', 3); a[seed, 3] = 255
    # 輪郭（赤の一番濃い色）
    al = np.pad(a[..., 3] > 0, 1); e = np.zeros_like(al)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): e |= np.roll(np.roll(al, dy, 0), dx, 1)
    e = (e & ~al)[1:-1, 1:-1]
    a[e, :3] = col('R', 1); a[e, 3] = 255
    return a

for name, im in (("apple", apple(32)), ("apple_bitten", apple(32, True)), ("apple_16", apple(16))):
    Image.fromarray(im).save(os.path.join(OUT, name + ".png"))
bg = Image.new("RGBA", (32, 32), (40, 52, 70, 255)); bg.alpha_composite(Image.fromarray(apple(32)))
bg.resize((32 * 10, 32 * 10), Image.NEAREST).convert("RGB").save(os.path.join(OUT, "apple_x8.png"))
sheet = Image.new("RGBA", (32 * 3 + 40, 40), (40, 52, 70, 255))
for i, im in enumerate((apple(32), apple(32, True), apple(16))): sheet.alpha_composite(Image.fromarray(im), (6 + i * 40, 4))
sheet.resize((sheet.width * 8, sheet.height * 8), Image.NEAREST).convert("RGB").save(os.path.join(OUT, "apple_sheet.png")); print("ok")
