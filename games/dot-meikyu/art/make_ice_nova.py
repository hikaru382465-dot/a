# 氷の範囲攻撃：霜の輪が広がり、氷のトゲが突き出して、砕ける。 python3 art/make_ice_nova.py
import math, random, os
from PIL import Image, ImageDraw, ImageChops, ImageFilter
random.seed(5)
S = 128; UP = 4; N = 18; C = S // 2
PAL = [(255, 255, 255), (215, 245, 255), (150, 215, 250), (90, 160, 235), (50, 100, 200), (30, 55, 130)]
def ease(t): return 1 - (1 - t) ** 3
mage = Image.open('assets/chars/mage_rapid_walk_0.png').convert('RGBA'); mage = mage.resize((int(mage.width * 40 / mage.height), 40), Image.LANCZOS)
spikes = []
for ring, (rad, cnt) in enumerate([(24, 6), (42, 6), (56, 12)]):
    for k in range(cnt):
        a = k / cnt * 6.283 + ring * 0.3 + random.uniform(-0.12, 0.12); spikes.append((a, rad + random.uniform(-3, 3), random.uniform(8, 17), 0.12 + ring * 0.10 + random.uniform(0, 0.05)))
flakes = [(random.uniform(0, 6.283), random.uniform(10, 55), random.uniform(0.3, 1.0)) for _ in range(34)]
def frame(i):
    t = i / (N - 1); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def pt(a, r, h=0): return (C + math.cos(a) * r, C + 6 + math.sin(a) * r * 0.62 - h)
    fade = 1 if t < 0.55 else max(0, 1 - (t - 0.55) / 0.45)
    # 地面：雪の結晶の模様（6方向。枝が分かれる）。広がりながら、ゆっくり回る
    R = ease(min(1, t / 0.4)) * 60
    if R > 2:
        P = 240; flat = Image.new('RGBA', (P, P), (0, 0, 0, 0)); fd = ImageDraw.Draw(flat); c0 = P / 2; rot = t * 0.35
        al = int(255 * fade); sc = P / 2 / 60.0 * R / 60.0 * 60.0 / R * R / 60.0 * 60.0 / 60.0
        k = R / 60.0 * (P / 2 - 6)
        fd.ellipse([c0 - k, c0 - k, c0 + k, c0 + k], fill=PAL[4] + (int(120 * fade),))
        fd.ellipse([c0 - k * 0.7, c0 - k * 0.7, c0 + k * 0.7, c0 + k * 0.7], fill=PAL[3] + (int(110 * fade),))
        def branch(x, y, ang, ln, depth, col, w):
            x2, y2 = x + math.cos(ang) * ln, y + math.sin(ang) * ln
            fd.line([x, y, x2, y2], fill=col + (al,), width=w)
            if depth > 0:
                for fr in (0.45, 0.75):
                    bx, by = x + (x2 - x) * fr, y + (y2 - y) * fr
                    for sg in (-1, 1): branch(bx, by, ang + sg * 0.95, ln * (0.38 if fr < 0.6 else 0.30), depth - 1, col, max(2, w - 2))
        for arm in range(6):
            ang = arm * math.pi / 3 + rot
            branch(c0, c0, ang, k * 0.95, 2, PAL[1], 6); branch(c0, c0, ang, k * 0.95, 0, PAL[0], 2)
        # 内がわの六角形の輪
        for rr, col in ((k * 0.28, PAL[0]), (k * 0.55, PAL[1])):
            fd.polygon([(c0 + math.cos(m * math.pi / 3 + rot + 0.52) * rr, c0 + math.sin(m * math.pi / 3 + rot + 0.52) * rr) for m in range(6)], outline=col + (al,), width=3)
        fd.ellipse([c0 - k, c0 - k, c0 + k, c0 + k], outline=PAL[0] + (al,), width=4)
        fl2 = flat.resize((int(R * 2), max(2, int(R * 2 * 0.62))), Image.LANCZOS)
        im.alpha_composite(fl2.crop((0, 0, fl2.width, fl2.height)), (int(C - fl2.width / 2), int(C + 6 - fl2.height / 2))) if (C - fl2.width / 2 >= 0) else im.alpha_composite(fl2.crop((int(-(C - fl2.width / 2)), 0, fl2.width - int(-(C - fl2.width / 2)), fl2.height)), (0, int(C + 6 - fl2.height / 2)))
    # 氷のトゲ：外へ順番に、速く突き出し、少しのこって、砕けて消える
    for a, r, hgt, t0 in sorted(spikes, key=lambda s: math.sin(s[0])):
        if t < t0: continue
        k = (t - t0) / 0.5
        if k > 1: continue
        grow = ease(min(1, k / 0.35)); h = hgt * grow * (1 if k < 0.7 else 1 - (k - 0.7) / 0.3)
        w = 3.2 * (1 if k < 0.7 else 1 - (k - 0.7) / 0.3) + 0.5
        bx, by = pt(a, r)
        # 3面：左（暗）・右（明）・てっぺん（白）でかたまり感
        d.polygon([(bx - w, by), (bx, by + 1.5), (bx, by - h)], fill=PAL[3] + (255,))
        d.polygon([(bx, by + 1.5), (bx + w, by), (bx, by - h)], fill=PAL[1] + (255,))
        d.polygon([(bx - w * 0.3, by - h * 0.55), (bx + w * 0.3, by - h * 0.55), (bx, by - h)], fill=PAL[0] + (255,))
        if k > 0.7:   # 砕けた欠片
            for q in range(3):
                fx = bx + (q - 1) * 4 * (k - 0.7) * 6; fy = by - h * 0.5 + (k - 0.7) * 30 * (q + 1) * 0.5
                d.rectangle([fx, fy, fx + 1, fy + 1], fill=PAL[0 + q % 2] + (255,))
    # 雪（きらきら）
    for a, r, life in flakes:
        if t < 0.15: continue
        k = (t - 0.15) / 0.85; x, y = pt(a, r * (0.8 + 0.3 * k), 10 + k * 18)
        if 0 <= x < S and 0 <= y < S and k < life: d.rectangle([x, y, x + 1, y + 1], fill=PAL[(int(k * 10) + int(a * 5)) % 2] + (255,))
    # 最初の閃光
    if i < 2:
        r = (22, 15)[i]; fl = Image.new('RGBA', (S, S), (0, 0, 0, 0)); ImageDraw.Draw(fl).ellipse([C - r, C + 6 - r * 0.62, C + r, C + 6 + r * 0.62], fill=(255, 255, 255, 230)); im.alpha_composite(fl)
    r_, g_, b_, a_ = im.split(); a_ = a_.point(lambda v: 255 if v > 60 else 0)
    q = Image.merge('RGB', (r_, g_, b_)).quantize(colors=20, dither=Image.NONE).convert('RGB')
    return Image.merge('RGBA', (*q.split(), a_))
frames = [frame(i) for i in range(N)]
os.makedirs('assets/fx/icenova', exist_ok=True)
for i, f in enumerate(frames): f.resize((S * UP, S * UP), Image.NEAREST).save('assets/fx/icenova/icenova_%02d.png' % i)
W = 512; rng = random.Random(3); bg = Image.new('RGB', (W, W), (22, 34, 28)); bd = ImageDraw.Draw(bg)
for _ in range(700):
    x, y = rng.randrange(W), rng.randrange(W); bd.rectangle([x, y, x + 3, y + 3], fill=rng.choice([(28, 44, 34), (18, 28, 24), (32, 50, 38)]))
out = []
for i in range(N + 6):
    base = bg.copy(); k = min(i, N - 1)
    big = frames[k].resize((W, W), Image.NEAREST); lay = Image.new('RGBA', (W, W), (0, 0, 0, 0)); lay.paste(big, (0, 0), big)
    base.paste(lay.convert('RGB'), (0, 0), lay.split()[3]) if False else None
    if i < N:
        glow = lay.convert('RGB').filter(ImageFilter.GaussianBlur(14)); base = ImageChops.add(base, glow.point(lambda v: v * 6 // 10))
        base.paste(lay.convert('RGB'), (0, 0), lay.split()[3])
    m = mage.resize((mage.width * 4, mage.height * 4), Image.LANCZOS); base.paste(m, (W // 2 - m.width // 2, W // 2 + 24 - m.height // 2 + 20), m)
    out.append(base)
out[0].save('assets/fx/icenova_demo.gif', save_all=True, append_images=out[1:], duration=55, loop=0)
sheet = Image.new('RGB', (256 * 6, 256 * 2))
for i in range(12): sheet.paste(out[i + 1].resize((256, 256)), ((i % 6) * 256, (i // 6) * 256))
sheet.save('assets/fx/icenova_sheet_preview.png'); print('ok')
