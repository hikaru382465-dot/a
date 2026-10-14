# 層を重ねた炎の爆発（ドット風）：閃光・火の玉・火花・衝撃の輪・煙。 python3 art/make_boom.py
import math, random
from PIL import Image, ImageDraw, ImageChops, ImageFilter
random.seed(7)
S = 96; UP = 4; N = 14                      # 96px（ドット）で描いて、4倍で見せる
PAL = [(255, 255, 235), (255, 236, 150), (255, 190, 60), (240, 110, 30), (190, 50, 25), (110, 30, 25)]
def ease(t): return 1 - (1 - t) ** 3
sparks = [(random.uniform(0, 6.283), random.uniform(24, 46), random.uniform(0.6, 1.0)) for _ in range(22)]
smoke = [(random.uniform(0, 6.283), random.uniform(6, 20), random.uniform(7, 12)) for _ in range(7)]
def frame(i):
    t = i / (N - 1); c = S // 2
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # 煙（後ろ）：ゆっくり広がって、暗くなって消える
    if t > 0.25:
        k = (t - 0.25) / 0.75
        for a, r, sz in smoke:
            x = c + math.cos(a) * r * (0.5 + k); y = c + math.sin(a) * r * (0.5 + k) - k * 8; s = sz * (0.6 + k * 0.6)
            al = int(150 * (1 - k)); d.ellipse([x - s, y - s, x + s, y + s], fill=(120, 100, 95, al))
    # 衝撃の輪
    if t < 0.55:
        k = t / 0.55; r = 8 + ease(k) * 40; w = max(1, int(5 * (1 - k)))
        d.ellipse([c - r, c - r, c + r, c + r], outline=(255, 210, 120, int(230 * (1 - k))), width=w)
    # 火の玉：大きくなって、色が白→黄→橙→赤へ変わり、縮む
    if t < 0.8:
        k = t / 0.8; r = 6 + math.sin(k * math.pi) ** 0.7 * 22
        blobs = [(math.cos(b * 1.9 + 0.5) * 0.45, math.sin(b * 2.3) * 0.40, 0.55 + 0.25 * ((b * 7) % 3) / 2) for b in range(7)]
        for j in range(5):
            col = PAL[min(5, j + int(k * 3))]; sc = 1 - j * 0.17
            for bx, by, bs in blobs:
                rr = r * bs * sc; x = c + bx * r * (1 + 0.15 * math.sin(i * 0.9 + bx * 5)); y = c + by * r - k * 6
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (255,))
    # 火花
    for a, v, life in sparks:
        if t < life:
            k = t / life; dist = ease(k) * v; x = c + math.cos(a) * dist; y = c + math.sin(a) * dist + k * k * 10
            L = 6 * (1 - k) + 2; col = PAL[min(3, int(k * 4))]
            d.line([x, y, x - math.cos(a) * L, y - math.sin(a) * L], fill=col + (255,), width=2 if k > 0.5 else 3)
    # 閃光（最初の2コマだけ）
    if i < 3:
        a = (1, 0.7, 0.35)[i]; r = (30, 26, 18)[i]
        fl = Image.new('RGBA', (S, S), (0, 0, 0, 0)); ImageDraw.Draw(fl).ellipse([c - r, c - r, c + r, c + r], fill=(255, 255, 255, int(255 * a)))
        im.alpha_composite(fl)
    # ドット風：色を減らして、はっきりさせる
    r_, g_, b_, a_ = im.split(); a_ = a_.point(lambda v: 255 if v > 90 else 0)
    q = Image.merge('RGB', (r_, g_, b_)).quantize(colors=24, dither=Image.NONE).convert('RGB')
    return Image.merge('RGBA', (*q.split(), a_))
frames = [frame(i) for i in range(N)]
import os; os.makedirs('assets/fx/boom', exist_ok=True)
for i, f in enumerate(frames): f.resize((S * UP, S * UP), Image.NEAREST).save('assets/fx/boom/boom_%02d.png' % i)
# 見本：暗い地面に、足し算で重ねて見せる（ブルーム風のにじみつき）
W = 420; bg = Image.new('RGB', (W, W), (22, 34, 28)); out = []
for i in range(N + 4):
    base = bg.copy(); f = frames[min(i, N - 1)] if i < N else None
    if f:
        big = f.resize((S * 3, S * 3), Image.NEAREST); lay = Image.new('RGBA', (W, W), (0, 0, 0, 0)); lay.paste(big, (W // 2 - big.width // 2, W // 2 - big.height // 2), big)
        glow = lay.convert('RGB').filter(ImageFilter.GaussianBlur(14)); base = ImageChops.add(base, glow); base = ImageChops.add(base, glow.point(lambda v: v // 2))
        base.paste(lay.convert('RGB'), (0, 0), lay.split()[3])
    out.append(base)
ox = 0
out[0].save('assets/fx/boom_demo.gif', save_all=True, append_images=out[1:], duration=60, loop=0)
sheet = Image.new('RGB', (W // 2 * 7, W // 2 * 2)); 
for i in range(14): sheet.paste(out[i].resize((W // 2, W // 2)), ((i % 7) * (W // 2), (i // 7) * (W // 2)))
sheet.save('assets/fx/boom_sheet_preview.png'); print('ok')
