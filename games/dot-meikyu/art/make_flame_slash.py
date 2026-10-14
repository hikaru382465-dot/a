# 炎の斬撃（火の呼吸ふう）：三日月の炎が、横にふり抜く。 python3 art/make_flame_slash.py
import math, random
from PIL import Image, ImageDraw, ImageChops, ImageFilter
random.seed(11)
S = 128; UP = 4; N = 16
PAL = [(255, 255, 240), (255, 240, 160), (255, 200, 70), (245, 130, 35), (205, 65, 25), (120, 30, 25)]
mage = Image.open('assets/chars/mage_rapid_walk_0.png').convert('RGBA'); mage = mage.resize((int(mage.width * 56 / mage.height), 56), Image.LANCZOS)
def frame(i):
    t = i / (N - 1); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); px = im.load()
    cx, cy = 30, 60                                   # 円の中心（主人公のあたり）
    sweep = min(1.0, t / 0.45)                        # 0〜0.45：ふり抜く、そのあと消える
    head = -1.15 + 2.3 * (1 - (1 - sweep) ** 3)       # 先頭の角度（速く出て、ゆっくり止まる）
    fade = 1.0 if t < 0.45 else max(0, 1 - (t - 0.45) / 0.55)
    steps = 140
    for s in range(steps):
        a = head - (s / steps) * 1.9                  # 先頭から、うしろへ
        if a < -1.15: break
        age = s / steps                               # 0＝先頭（白く太い）、1＝しっぽ（赤く細い）
        R = 52 + 12 * math.sin(a * 1.2)               # 半径
        thick = (14 * (1 - age) ** 0.8 + 1.5) * (0.6 + 0.4 * fade)
        for r in range(int(-thick * 0.2), int(thick) + 1):
            # 外がわほど、炎のゆらぎで、ギザギザにする
            wob = math.sin(a * 23 + i * 1.7 + r) * 2.2 * age + random.uniform(-0.8, 0.8)
            rr = R + r * 1.0 + wob
            x = cx + math.cos(a) * rr * 1.25; y = cy + math.sin(a) * rr * 0.8
            u = r / max(1.0, thick)                    # 0＝内がわ、1＝外がわ
            heat = min(5, int((u * 0.5 + age * 0.9 + (1 - fade) * 0.5) * 5.5))
            col = PAL[max(0, min(5, heat))]
            for dx in (0, 1):
                for dy in (0, 1):
                    xx, yy = int(x) + dx, int(y) + dy
                    if 0 <= xx < S and 0 <= yy < S: px[xx, yy] = col + (int(255 * min(1, fade * 1.3)),)
    # 火の舌：外がわから、上へのびる
    d = ImageDraw.Draw(im)
    for k in range(14):
        a = head - random.uniform(0.05, 1.4) * 0.8
        if a < -1.15: continue
        R = 52 + 12 * math.sin(a * 1.2) + 10; x = cx + math.cos(a) * R * 1.25; y = cy + math.sin(a) * R * 0.8
        L = random.uniform(5, 12) * fade; d.polygon([(x - 2, y), (x + 2, y), (x + random.uniform(-3, 3), y - L)], fill=PAL[2 + (k % 2)] + (int(255 * fade),))
    # 火の粉
    for k in range(18):
        a = head - random.uniform(0, 1.7); R = 52 + random.uniform(-6, 24)
        x = cx + math.cos(a) * R * 1.25 + t * 10; y = cy + math.sin(a) * R * 0.8 - t * 22 * random.uniform(0.3, 1)
        if fade > 0.1 and 0 <= x < S and 0 <= y < S: d.rectangle([x, y, x + 1, y + 1], fill=PAL[1 + k % 3] + (255,))
    # 先頭の閃光
    if t < 0.5 and sweep > 0.05:
        hx = cx + math.cos(head) * 52 * 1.25; hy = cy + math.sin(head) * 52 * 0.8; r = 7 * (1 - t / 0.5) + 2
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=(255, 255, 255, 255))
    r_, g_, b_, a_ = im.split(); a_ = a_.point(lambda v: 255 if v > 80 else 0)
    q = Image.merge('RGB', (r_, g_, b_)).quantize(colors=24, dither=Image.NONE).convert('RGB')
    return Image.merge('RGBA', (*q.split(), a_))
frames = [frame(i) for i in range(N)]
import os; os.makedirs('assets/fx/flameslash', exist_ok=True)
for i, f in enumerate(frames): f.resize((S * UP, S * UP), Image.NEAREST).save('assets/fx/flameslash/flameslash_%02d.png' % i)
W = 512; rng = random.Random(3); bg = Image.new('RGB', (W, W), (22, 34, 28)); bd = ImageDraw.Draw(bg)
for _ in range(700):
    x, y = rng.randrange(W), rng.randrange(W); bd.rectangle([x, y, x + 3, y + 3], fill=rng.choice([(28, 44, 34), (18, 28, 24), (32, 50, 38)]))
out = []
for i in range(N + 6):
    base = bg.copy(); k = min(i, N - 1)
    m = mage.resize((mage.width * 2, mage.height * 2), Image.LANCZOS); base.paste(m, (30 * 4 - m.width // 2 + 0, 60 * 4 - m.height // 2), m)
    big = frames[k].resize((W, W), Image.NEAREST); lay = Image.new('RGBA', (W, W), (0, 0, 0, 0)); lay.paste(big, (0, 0), big)
    if i < N:
        glow = lay.convert('RGB').filter(ImageFilter.GaussianBlur(16)); base = ImageChops.add(base, glow); base = ImageChops.add(base, glow.point(lambda v: v // 2))
        base.paste(lay.convert('RGB'), (0, 0), lay.split()[3])
    out.append(base)
out[0].save('assets/fx/flameslash_demo.gif', save_all=True, append_images=out[1:], duration=55, loop=0)
sheet = Image.new('RGB', (256 * 6, 256 * 2))
for i in range(12): sheet.paste(out[i + 1].resize((256, 256)), ((i % 6) * 256, (i // 6) * 256))
sheet.save('assets/fx/flameslash_sheet_preview.png'); print('ok')
