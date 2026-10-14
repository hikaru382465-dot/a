# 炎の粒（メラメラ）を、ドット絵の8コマ（つなぎ目なしのループ）で作る
import math, os
from PIL import Image
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fx"); os.makedirs(OUT, exist_ok=True)
N, W, H, UP = 8, 32, 48, 6
BANDS = [(0.80, (255, 246, 190)), (0.56, (255, 208, 64)), (0.35, (255, 132, 30)), (0.17, (222, 58, 28)), (0.05, (128, 34, 30))]

def frame(k):
    t = k / N * 2 * math.pi
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = im.load()
    for y in range(H):
        u = (H - 1 - y) / (H - 1)                      # 下=0、上=1
        c = W / 2 + 3.2 * u * math.sin(t - u * 3.0) + 1.6 * u * math.sin(2 * t + u * 5.0)   # 先がゆれる
        hw = W * 0.36 * (1 - u ** 1.25) ** 0.85 * (1 + 0.12 * math.sin(3 * t + u * 9))        # 太さがうねる
        for x in range(W):
            d = abs(x - c) / max(hw, 0.01)
            val = ((1 - d ** 1.5) * (1 - u * 0.5) + 0.07 * math.sin(x * 1.7 + t + u * 8)) if d <= 1 else 0
            for sd in (-1, 1):                              # 横に小さな炎の舌（ちらちら）
                lim = 0.58 + 0.08 * math.sin(2 * t + sd)
                if u < lim:
                    cs = c + sd * hw * 0.62 + 1.4 * math.sin(t * 2 + sd * 2 + u * 6)
                    hs = hw * 0.42 * (1 - u / lim) ** 0.8
                    ds = abs(x - cs) / max(hs, 0.01)
                    if ds <= 1: val = max(val, (1 - ds ** 1.5) * (1 - u * 0.9) * 0.9)
            if val <= 0: continue
            for th, col in BANDS:
                if val > th: px[x, y] = (*col, 255); break
    for i in range(3):                                   # ひのこ（上へのぼって消える）
        ph = (k / N + i / 3) % 1; sy = int(H * 0.8 - ph * H * 0.85); sx = int(W / 2 + 6 * math.sin(2 * math.pi * (ph + i / 3)))
        if 0 <= sx < W and 0 <= sy < H:
            a = int(255 * (1 - ph)); px[sx, sy] = (255, 200, 80, a)
    return im

frames = [frame(k) for k in range(N)]
big = [f.resize((W * UP, H * UP), Image.NEAREST) for f in frames]
for i, f in enumerate(big): f.save(os.path.join(OUT, f"fire_{i}.png"))
sheet = Image.new("RGBA", (big[0].width * N, big[0].height), (0, 0, 0, 0))
for i, f in enumerate(big): sheet.alpha_composite(f, (i * big[0].width, 0))
sheet.save(os.path.join(OUT, "fire_sheet.png"))
# 動きの確認用：暗い背景のアニメGIF（炎を3つ並べて、ずらして再生）
pv = []
for k in range(N):
    bg = Image.new("RGBA", (big[0].width * 3 + 40, big[0].height + 20), (26, 22, 40, 255))
    for j in range(3): bg.alpha_composite(big[(k + j * 3) % N], (10 + j * (big[0].width + 10), 10))
    pv.append(bg.convert("RGB"))
pv[0].save(os.path.join(OUT, "fire_preview.gif"), save_all=True, append_images=pv[1:], duration=90, loop=0)
st = Image.new("RGBA", (big[0].width * N // 2 + 20, big[0].height // 2 * 2 + 20), (26, 22, 40, 255))
for i, f in enumerate(big): st.alpha_composite(f.resize((f.width // 2, f.height // 2), Image.NEAREST), (10 + i * f.width // 2, 10))
st.save(os.path.join(OUT, "fire_preview.png")); print("ok", st.size)
