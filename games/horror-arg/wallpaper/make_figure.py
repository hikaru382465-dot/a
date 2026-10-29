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

# 人影の段階：x=横の位置(0-1)、base=足元の高さ、h=背の高さ、tilt=頭のかたむき、body=濃さ、cur=カーテンの濃さ(端,中)
STAGES = {
    "fig0": None,                                                                             # 明かりだけ（人はいない）
    "fig1": dict(x=0.42, base=1.02, h=0.74, tilt=-0.4, body=0.72, cur=(0.62, 0.16)),         # 奥・カーテンのうしろ（一瞬の演出用）
    "fig":  dict(x=0.52, base=1.14, h=1.04, tilt=-0.9, body=0.97, cur=(0.22, 0.0), face=True),  # 窓ぎわ（一瞬の演出用）
    # 窓を閉じるたびに近づいてくる（4段階）。壁紙にそのまま残る
    "st1": dict(x=0.36, base=1.02, h=0.50, tilt=-0.3, body=0.58, cur=(0.64, 0.18)),
    "st2": dict(x=0.42, base=1.03, h=0.66, tilt=-0.4, body=0.70, cur=(0.58, 0.14)),
    "st3": dict(x=0.47, base=1.07, h=0.86, tilt=-0.6, body=0.86, cur=(0.40, 0.06)),
    "st4": dict(x=0.52, base=1.14, h=1.04, tilt=-0.9, body=0.97, cur=(0.22, 0.0), face=True),
}

def render(name):
    cfg = STAGES[name]
    base = interior().convert("RGBA")
    mask = Image.new("L", (W, H), 0); d = ImageDraw.Draw(mask)
    if cfg:
        gap = human(d, W * cfg["x"], H * cfg["base"], H * cfg["h"], tilt=cfg["tilt"])
        blur = S * (0.55 if cfg["h"] > 0.95 else 1.1 - 0.6 * (cfg["h"] - 0.5))
        m = mask.filter(ImageFilter.GaussianBlur(blur))
        if cfg["h"] > 0.95:
            gm = gap.filter(ImageFilter.GaussianBlur(S * 0.5)).point(lambda v: int(v * 0.75)); m = ImageChops.subtract(m, gm)
        halo = ImageChops.subtract(mask.filter(ImageFilter.GaussianBlur(S * 1.8)), mask.filter(ImageFilter.GaussianBlur(S * 0.4))).point(lambda v: min(255, v * 2))
        base = Image.composite(Image.new("RGBA", (W, H), (255, 214, 150, 255)), base, halo.point(lambda v: int(v * 0.35)))
        k = (cfg["h"] - 0.5) / 0.54
        body = (int(46 - 26 * k), int(30 - 18 * k), int(20 - 11 * k), 255)
        base = Image.composite(Image.new("RGBA", (W, H), body), base, m.point(lambda v: int(v * cfg["body"])))
        if cfg.get("face"):
            fy = int(H * 0.10); ImageDraw.Draw(base).ellipse((W * 0.50 - 26, fy + 20, W * 0.50 + 26, fy + 100), fill=(70, 52, 42, 70))
    ce = cfg["cur"] if cfg else (0.62, 0.16)
    base = Image.alpha_composite(base, curtains(*ce))
    dd = ImageDraw.Draw(base); bw = int(S * 1.1)
    dd.rectangle((W // 2 - bw // 2, 0, W // 2 + bw // 2, H), fill=(52, 36, 26, 255)); yb = int(H * 0.50); dd.rectangle((0, yb - bw // 2, W, yb + bw // 2), fill=(52, 36, 26, 255))
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
    frames = {k: render(k) for k in STAGES}
    for m in ("dusk", "night", "red", "lit"):
        base = Image.open(f"{SRC}/final2_{m}.png").convert("RGB")
        base.paste(lit.crop((906, 366, 978, 462)), (906, 366))       # 窓の枠まわり（明るい状態）
        base = glow(base)
        for name, fr in frames.items():
            im = base.copy(); im.paste(fr, (PX0, PY0)); im.save(f"{OUT}/wallpaper_b_{m}_{name}.jpg", quality=84, optimize=True)
    # 確認用：段階を並べる（夜）
    box = (820, 300, 1080, 520); names = ["fig0", "st1", "st2", "st3", "st4"]; strip = Image.new("RGB", (260 * 5, 220))
    for i, n in enumerate(names): strip.paste(Image.open(f"{OUT}/wallpaper_b_night_{n}.jpg").crop(box), (i * 260, 0))
    strip.save("/tmp/claude-0/fig_stages.png"); print("ok")

# ===== 外に立つ人影（家の外・柵のあたり・手前の草の上。だんだん近づく）=====
# 位置は 1600x900 の壁紙の座標。cx=横、feet=足元の高さ、h=背の高さ、blur=ピンボケ（近いほど大きい）、a=濃さ（遠いほどうすい）
OUTDOOR = {
    "o1": dict(cx=1235, feet=602, h=92, blur=1.0, a=0.62),
    "o2": dict(cx=1010, feet=655, h=175, blur=1.5, a=0.80),
    "o3": dict(cx=905, feet=770, h=340, blur=2.8, a=0.90),
    "o4": dict(cx=820, feet=985, h=800, blur=7.5, a=0.95, face=True),
}
BODY = {"dusk": (24, 17, 9), "night": (5, 8, 16), "red": (14, 2, 2), "lit": (5, 8, 16)}
RIM = {"dusk": (255, 215, 150), "night": (140, 165, 235), "red": (255, 90, 60), "lit": (140, 165, 235)}

def outdoor_mask(size, cfg):
    Wf, Hf = size; m = Image.new("L", size, 0); d = ImageDraw.Draw(m)
    cx, feet, h = cfg["cx"], cfg["feet"], cfg["h"]; u = h / 7.6
    top = feet - h; hx, hy = cx + u * 0.18, top + u * 0.55
    d.ellipse((hx - u * .40, hy - u * .55, hx + u * .40, hy + u * .55), fill=255)                                     # 頭（少しかしぐ）
    d.polygon([(hx - u * .17, hy + u * .35), (hx + u * .17, hy + u * .35), (cx + u * .21, hy + u * 1.05), (cx - u * .21, hy + u * 1.05)], fill=255)   # 首
    sy = hy + u * 0.95; sh = u * 0.98; hip = sy + u * 2.9
    d.polygon([(cx - u * .2, sy - u * .1), (cx + u * .2, sy - u * .1), (cx + sh * .86, sy + u * .35), (cx + sh * .62, hip), (cx - sh * .62, hip), (cx - sh * .86, sy + u * .35)], fill=255)   # 肩〜胴
    for sg in (-1, 1):                                                       # 腕：胴との間に細いすきま
        d.polygon([(cx + sg * sh * .90, sy + u * .30), (cx + sg * (sh * .90 + u * .36), sy + u * .55), (cx + sg * (sh * .92 + u * .34), sy + u * 3.15), (cx + sg * (sh * .74), sy + u * 3.10)], fill=255)
        d.polygon([(cx + sg * sh * .60, hip - u * .1), (cx + sg * sh * .04, hip - u * .1), (cx + sg * sh * .10, feet), (cx + sg * sh * .56, feet)], fill=255)   # 脚
    return m

def outdoor(mood, name):
    cfg = OUTDOOR[name]; base = Image.open(f"{SRC}/final2_{mood}.png").convert("RGB")
    m = outdoor_mask(base.size, cfg)
    soft = m.filter(ImageFilter.GaussianBlur(cfg["blur"]))
    # ふち：月などの光で、輪郭がうっすら明るい
    rim = ImageChops.subtract(m.filter(ImageFilter.GaussianBlur(cfg["blur"] + 1.6)), m.filter(ImageFilter.GaussianBlur(cfg["blur"] * 0.4))).point(lambda v: min(255, v * 2))
    base = Image.composite(Image.new("RGB", base.size, RIM[mood]), base, rim.point(lambda v: int(v * 0.16 * cfg["a"])))
    out = Image.composite(Image.new("RGB", base.size, BODY[mood]), base, soft.point(lambda v: int(v * cfg["a"])))
    if cfg.get("face"):   # ごくうすい顔の明るみ（見えるか見えないか）
        u = cfg["h"] / 7.6; hx = cfg["cx"] + u * 0.18; hy = cfg["feet"] - cfg["h"] + u * 0.55
        fl = Image.new("L", base.size, 0); ImageDraw.Draw(fl).ellipse((hx - u * .22, hy - u * .30, hx + u * .22, hy + u * .34), fill=255)
        fl = fl.filter(ImageFilter.GaussianBlur(cfg["blur"] * 0.8)).point(lambda v: int(v * 0.16))
        out = Image.composite(Image.new("RGB", base.size, (190, 184, 170)), out, fl)
    out.save(f"{OUT}/wallpaper_b_{mood}_{name}.jpg", quality=84, optimize=True)

if __name__ == "__main__":
    for mood in ("dusk", "night", "red", "lit"):
        for name in OUTDOOR: outdoor(mood, name)
    box = (500, 150, 1500, 900); strip = Image.new("RGB", (1000 * 2, 750 * 2))
    for i, n in enumerate(("o1", "o2", "o3", "o4")):
        strip.paste(Image.open(f"{OUT}/wallpaper_b_night_{n}.jpg").crop(box), ((i % 2) * 1000, (i // 2) * 750))
    strip.resize((1400, 1050)).save("/tmp/claude-0/fig_outdoor.png"); print("outdoor ok")
