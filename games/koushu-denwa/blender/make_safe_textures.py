"""
手提げ金庫（木目プリントの鉄の箱）の画像を作る。numpy と Pillow だけで動く。
  safe_wood_color.png / safe_wood_normal.png / safe_wood_rough.png … 1024。木目プリント＋ひっかき傷＋塗装のはがれ（ふちに多い）
  safe_plate.png … 銘板（黒いエナメルに銀の文字。HIGH CLASS / MISORA HAND SAFE ＝本物の商標をさけた名前）
使い方：python make_safe_textures.py   出力：assets/tex/game/
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "tex", "game")
N = 1024
rng = np.random.default_rng(1997)


def smooth(sx, sy):
    a = rng.standard_normal((N, N))
    fx = np.fft.fftfreq(N)[None, :]
    fy = np.fft.fftfreq(N)[:, None]
    g = np.exp(-((fx * sx) ** 2 + (fy * sy) ** 2) * 60.0)
    r = np.real(np.fft.ifft2(np.fft.fft2(a) * g))
    return (r - r.min()) / (r.max() - r.min())


# ---- 木目プリント（横方向に流れる、オリーブがかった茶色の杢）----
y = np.arange(N)[:, None] / N
flow = smooth(60.0, 3.0)
fig = np.sin((y * 26.0 + flow * 7.0) * np.pi * 2)            # 杢のうねり
fine = smooth(200.0, 10.0)
cloud = smooth(18.0, 18.0)
grain = np.clip(0.45 + 0.28 * fig + 0.25 * (fine - 0.5) * 2 + 0.2 * (cloud - 0.5), 0, 1)
light = np.array([0.52, 0.42, 0.20])
dark = np.array([0.20, 0.14, 0.06])
col = dark + (light - dark) * grain[..., None]
col[..., 1] *= 0.98 + 0.05 * cloud                           # すこし緑がかった、古い塗装の色
col *= (0.85 + 0.25 * cloud)[..., None]
# 細い白っぽい筋（象嵌のような筋）
rows = (np.abs(np.arange(N) - 40) < 2) | (np.abs(np.arange(N) - (N - 40)) < 2)
col[rows] *= 1.35

# ---- 傷とはがれ ----
img = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8))
d = ImageDraw.Draw(img)
for _ in range(70):                                          # 細いひっかき傷
    x0, y0 = rng.integers(0, N), rng.integers(0, N)
    ang = rng.uniform(-0.25, 0.25) + (np.pi / 2 if rng.random() < 0.15 else 0)
    ln = rng.integers(15, 90)
    d.line((x0, y0, x0 + np.cos(ang) * ln, y0 + np.sin(ang) * ln), fill=(150, 130, 85), width=1)
chip = Image.new("L", (N, N), 0)
cd = ImageDraw.Draw(chip)
for _ in range(90):                                          # 塗装のはがれ（ふちに多い）
    if rng.random() < 0.7:
        side = rng.integers(0, 4)
        t = rng.integers(0, N)
        e = rng.integers(0, 40)
        cx, cy = [(t, e), (t, N - e), (e, t), (N - e, t)][side]
    else:
        cx, cy = rng.integers(0, N), rng.integers(0, N)
    r = rng.integers(3, 14)
    cd.ellipse((cx - r, cy - r * 0.6, cx + r, cy + r * 0.6), fill=255)
chip = chip.filter(ImageFilter.GaussianBlur(1.0))
chipm = np.array(chip).astype(float) / 255.0
a = np.array(img).astype(float) / 255.0
metal = np.array([0.30, 0.27, 0.24])
a = a * (1 - chipm[..., None]) + metal * chipm[..., None]
Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, "safe_wood_color.png"))

# ---- 凹凸（法線）と粗さ ----
h = 0.5 * grain + 0.5 * fine - 0.35 * chipm
dy, dx = np.gradient(h * 5.0)
nx, ny, nz = -dx * 3.0, -dy * 3.0, np.ones_like(h)
l = np.sqrt(nx * nx + ny * ny + nz * nz)
nrm = np.stack([nx / l, ny / l, nz / l], -1) * 0.5 + 0.5
Image.fromarray((nrm * 255).astype(np.uint8)).save(os.path.join(OUT, "safe_wood_normal.png"))
rough = np.clip(0.38 + 0.2 * (1 - grain) * 0.5 + 0.35 * chipm + 0.1 * cloud, 0, 1)         # ニスの光沢。はがれた所は粗い
Image.fromarray((rough * 255).astype(np.uint8)).save(os.path.join(OUT, "safe_wood_rough.png"))

# ---- 銘板 ----
W, H = 640, 256
pl = Image.new("RGB", (W, H), (14, 14, 18))
pd = ImageDraw.Draw(pl)
silver = (205, 205, 210)
f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 54)
f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 34)
pd.rounded_rectangle((6, 6, W - 7, H - 7), radius=26, outline=silver, width=4)
pd.text((40, 38), "HIGH", font=f_big, fill=silver)
pd.text((W - 40 - pd.textlength("CLASS", font=f_big), 38), "CLASS", font=f_big, fill=silver)
cx, cy = W // 2, 78                                           # 中央の紋章（王冠の円）
pd.ellipse((cx - 52, cy - 52, cx + 52, cy + 52), outline=silver, width=4)
pd.ellipse((cx - 38, cy - 38, cx + 38, cy + 38), outline=silver, width=2)
for k in range(5):
    pd.polygon([(cx - 24 + k * 12, cy + 10), (cx - 18 + k * 12, cy - 14), (cx - 12 + k * 12, cy + 10)], fill=silver)
pd.rectangle((cx - 26, cy + 10, cx + 26, cy + 20), fill=silver)
for yy in range(150, 178, 6):                                  # 帯（ななめ線のしま）
    for xx in range(14, W - 14, 12):
        pd.line((xx, yy + 5, xx + 6, yy), fill=(120, 120, 130), width=2)
pd.text((34, 190), "MISORA", font=f_small, fill=silver)
pd.text((W - 34 - pd.textlength("HAND SAFE", font=f_small), 190), "HAND SAFE", font=f_small, fill=silver)
for sx in (24, W - 24):
    pd.ellipse((sx - 8, H // 2 - 8, sx + 8, H // 2 + 8), fill=(150, 150, 155))        # ねじ
arr = np.array(pl).astype(float)
arr += rng.normal(0, 5, arr.shape)                             # ざらつき
pl = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
pd = ImageDraw.Draw(pl)
for _ in range(60):
    x0, y0 = rng.integers(0, W), rng.integers(0, H)
    pd.line((x0, y0, x0 + rng.integers(-40, 40), y0 + rng.integers(-6, 6)), fill=(90, 90, 96), width=1)
pl.save(os.path.join(OUT, "safe_plate.png"))
print("safe_wood_color / safe_wood_normal / safe_wood_rough / safe_plate を作りました")
