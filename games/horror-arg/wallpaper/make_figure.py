# 壁紙の家の窓に立つ人影を作る（PILで高解像度に描いて縮小する）。
# 使い方: python3 make_figure.py <Blender描画の入力フォルダ> <出力フォルダ>
#   入力フォルダに final2_dusk/night/red/lit.png（1600x900）が必要。出力は wallpaper_b_{mood}_fig0/fig1/fig.jpg
import sys, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np
SRC, OUT = sys.argv[1], sys.argv[2]
S = 12                                   # 窓の中を、12倍の大きさで描いてから縮める
PX0, PY0, PX1, PY1 = 916, 374, 968, 456   # 窓ガラスの範囲（枠は残す）
W, H = (PX1 - PX0) * S, (PY1 - PY0) * S
random.seed(3)

def interior():
    """部屋の中：あたたかい明かり。上は少し暗く、床に近いほど明るい。まんなかが明るい"""
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(-1, 1, W)[None, :]
    r = 255 - 22 * (1 - y) - 18 * np.abs(x); g = 196 - 40 * (1 - y) - 26 * np.abs(x) + 10 * y; b = 120 - 38 * (1 - y) - 28 * np.abs(x)
    a = np.stack([r * np.ones_like(x), g * np.ones_like(x), b * np.ones_like(x)], -1).clip(0, 255).astype("uint8")
    return Image.fromarray(a, "RGB")

def curtains(alpha_edge=0.55, alpha_mid=0.10):
    """薄いカーテン：左右にひだ。真ん中はうっすら"""
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = c.load()
    for xx in range(W):
        u = xx / W; edge = max(0, 0.30 - min(u, 1 - u)) / 0.30        # 端ほど濃い
        pleat = 0.5 + 0.5 * math.sin(xx / W * 2 * math.pi * 7 + 0.6 * math.sin(xx / 40))
        al = alpha_mid + (alpha_edge - alpha_mid) * edge
        col = int(205 + 30 * pleat - 40 * edge); a = int(255 * al * (0.75 + 0.25 * pleat))
        for yy in range(0, H, 1): px[xx, yy] = (col, int(col * .93), int(col * .78), a)
    return c

def human(d, cx, base_y, h_px, tilt=0.0, hand=False):
    """人の形（正面。逆光で黒い）。h_px は頭のてっぺんから足元までの高さ。比率は、頭が全体の1/7.5ほど"""
    u = h_px / 7.6                                    # 頭1つ分の高さ
    hx, hy = cx + tilt * u * 0.35, base_y - h_px + u * 0.55
    d.ellipse((hx - u * .40, hy - u * .55, hx + u * .40, hy + u * .55), fill=255)                      # 頭
    d.polygon([(hx - u * .17, hy + u * .35), (hx + u * .17, hy + u * .35), (cx + u * .20, hy + u * 1.05), (cx - u * .20, hy + u * 1.05)], fill=255)   # 首
    sy = hy + u * 0.95                                                                                   # 肩の高さ
    sh = u * 1.05                                                                                        # 肩幅（半分）
    d.polygon([(cx - u * .2, sy - u * .1), (cx + u * .2, sy - u * .1), (cx + sh, sy + u * .35), (cx + sh * 1.06, base_y), (cx - sh * 1.06, base_y), (cx - sh, sy + u * .35)], fill=255)   # 肩〜胴
    # 腕：胴との間に細い隙間（明かりがすける）
    gap = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(gap)
    for sgn in (-1, 1):
        gd.polygon([(cx + sgn * sh * .72, sy + u * 1.5), (cx + sgn * sh * .78, sy + u * 1.5), (cx + sgn * sh * .80, base_y), (cx + sgn * sh * .72, base_y)], fill=255)
    return gap

def render(frame):
    base = interior().convert("RGBA")
    mask = Image.new("L", (W, H), 0); d = ImageDraw.Draw(mask)
    if frame == 1:      # 奥・小さい・カーテンのうしろ
        gap = human(d, W * 0.42, H * 1.02, H * 0.74, tilt=-0.4)
    elif frame == 2:    # 窓ぎわ・大きい・顔を少しかしげる
        gap = human(d, W * 0.52, H * 1.14, H * 1.04, tilt=-0.9)
    if frame:
        m = mask.filter(ImageFilter.GaussianBlur(S * (0.55 if frame == 2 else 1.1)))
        if frame == 2:
            gm = gap.filter(ImageFilter.GaussianBlur(S * 0.5)).point(lambda v: int(v * 0.75)); m = ImageChops.subtract(m, gm)
        # 逆光のふち：人影のまわりが、ほんの少し明るくにじむ
        halo = ImageChops.subtract(mask.filter(ImageFilter.GaussianBlur(S * 1.8)), mask.filter(ImageFilter.GaussianBlur(S * 0.4))).point(lambda v: min(255, v * 2))
        base = Image.composite(Image.new("RGBA", (W, H), (255, 214, 150, 255)), base, halo.point(lambda v: int(v * 0.35)))
        body = (20, 12, 9, 255) if frame == 2 else (46, 30, 20, 255)
        alpha = m.point(lambda v: int(v * (0.97 if frame == 2 else 0.72)))
        base = Image.composite(Image.new("RGBA", (W, H), body), base, alpha)
        if frame == 2:   # 顔：ごくうすい明るみ（見えるか見えないか）
            fy = int(H * 0.10); ImageDraw.Draw(base).ellipse((W * 0.50 - 26, fy + 20, W * 0.50 + 26, fy + 100), fill=(70, 52, 42, 70))
    if frame in (0, 1):
        base = Image.alpha_composite(base, curtains(0.62, 0.16))
    elif frame == 2:
        base = Image.alpha_composite(base, curtains(0.22, 0.0))
    # 窓の桟（人影の前を横切る）
    dd = ImageDraw.Draw(base); bw = int(S * 1.1)
    dd.rectangle((W // 2 - bw // 2, 0, W // 2 + bw // 2, H), fill=(52, 36, 26, 255)); yb = int(H * 0.50); dd.rectangle((0, yb - bw // 2, W, yb + bw // 2), fill=(52, 36, 26, 255))
    # ガラスのよごれ・うっすらした反射（斜めの帯）
    ref = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(ref)
    rd.polygon([(W * .05, 0), (W * .30, 0), (W * .08, H), (-W * .17, H)], fill=(255, 255, 255, 22))
    base = Image.alpha_composite(base, ref.filter(ImageFilter.GaussianBlur(S * 1.5)))
    return base.convert("RGB").filter(ImageFilter.GaussianBlur(S * 0.28)).resize((PX1 - PX0, PY1 - PY0), Image.LANCZOS)

def glow(base):
    g = Image.new("L", base.size, 0); ImageDraw.Draw(g).rectangle((914, 372, 970, 457), fill=255)
    g = g.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.5))
    return ImageChops.screen(base, Image.composite(Image.new("RGB", base.size, (255, 170, 70)), Image.new("RGB", base.size, (0, 0, 0)), g))

if __name__ == "__main__":
    lit = Image.open(f"{SRC}/final2_lit.png").convert("RGB")
    frames = [render(0), render(1), render(2)]
    for m in ("dusk", "night", "red", "lit"):
        base = Image.open(f"{SRC}/final2_{m}.png").convert("RGB")
        base.paste(lit.crop((906, 366, 978, 462)), (906, 366))       # 窓の枠まわり（明るい状態）
        base = glow(base)
        for name, fr in (("fig0", frames[0]), ("fig1", frames[1]), ("fig", frames[2])):
            im = base.copy(); im.paste(fr, (PX0, PY0)); im.save(f"{OUT}/wallpaper_b_{m}_{name}.jpg", quality=84, optimize=True)
    # 確認用：拡大
    n = Image.open(f"{OUT}/wallpaper_b_night_fig.jpg"); n0 = Image.open(f"{OUT}/wallpaper_b_night_fig0.jpg"); n1 = Image.open(f"{OUT}/wallpaper_b_night_fig1.jpg")
    box = (820, 300, 1080, 520); strip = Image.new("RGB", (260 * 3, 220))
    for i, im in enumerate((n0, n1, n)): strip.paste(im.crop(box), (i * 260, 0))
    strip.resize((260 * 3 * 2, 440), Image.LANCZOS).save("/tmp/claude-0/fig_real.png")
    print("ok")
