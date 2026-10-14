# 雷の球＋稲妻の連鎖：球が着いた所から、近くの敵へ走り、そこから敵→敵へ連鎖する。 python3 art/make_lightning_combo.py
import math, random, os
from PIL import Image, ImageDraw, ImageChops, ImageFilter
S = 128; UP = 3; N = 44; W = 512; K = W / S
PAL = [(255, 255, 255), (235, 225, 255), (180, 160, 255), (120, 90, 235), (70, 50, 170)]
mage = Image.open('assets/chars/mage_rapid_walk_0.png').convert('RGBA'); mage = mage.resize((int(mage.width * 40 / mage.height), 40), Image.LANCZOS)
slime = Image.open('assets/chars/pet_slime_0.png').convert('RGBA'); slime = slime.resize((int(slime.width * 22 / slime.height), 22), Image.LANCZOS)
r_, g_, b_, a_ = slime.split(); gray = Image.merge('RGB', (r_, g_, b_)).convert('L')
enemy = Image.merge('RGBA', (*ImageChops.multiply(Image.merge('RGB', (gray,) * 3), Image.new('RGB', slime.size, (255, 130, 130))).split(), a_))
me = (18, 82); land = (74, 66)
targets = [(50, 38), (100, 40), (104, 78), (82, 104), (46, 94), (60, 66)]
def bolt(rng, p0, p1, spread, depth=5):
    pts = [p0, p1]
    for _ in range(depth):
        new = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
            off = rng.uniform(-1, 1) * spread * L * 0.5; new += [(mx - dy / L * off, my + dx / L * off), b]
        pts = new; spread *= 0.85
    return pts
def draw_bolt(d, pts, w, alpha):
    for ww, col in ((w * 3, PAL[3]), (w * 2, PAL[2]), (w, PAL[0])): d.line(pts, fill=col + (alpha,), width=max(1, int(ww)), joint='curve')
def orb(d, c, r, rng, spark):
    d.ellipse([c[0] - r * 1.7, c[1] - r * 1.7, c[0] + r * 1.7, c[1] + r * 1.7], fill=PAL[4] + (160,))
    d.ellipse([c[0] - r * 1.3, c[1] - r * 1.3, c[0] + r * 1.3, c[1] + r * 1.3], fill=PAL[3] + (255,))
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=PAL[1] + (255,))
    d.ellipse([c[0] - r * 0.55, c[1] - r * 0.55, c[0] + r * 0.55, c[1] + r * 0.55], fill=PAL[0] + (255,))
    for _ in range(spark):                                     # 球のまわりの、ぱちぱち
        a = rng.uniform(0, 6.283); p1 = (c[0] + math.cos(a) * r * 2.6, c[1] + math.sin(a) * r * 2.6); draw_bolt(d, bolt(rng, (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r), p1, 0.5, 3), 1, 255)
FLY0, FLY1, BURST = 0.05, 0.38, 0.38
def frame(i):
    t = i / (N - 1); rng = random.Random(100 + i // 2); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if t < FLY1:
        k = max(0, (t - FLY0) / (FLY1 - FLY0)); k = k * k * (3 - 2 * k)
        c = (me[0] + (land[0] - me[0]) * k, me[1] + (land[1] - me[1]) * k - math.sin(k * math.pi) * 6)
        for j in range(1, 6):                                      # しっぽ
            kk = max(0, k - j * 0.06); cc = (me[0] + (land[0] - me[0]) * kk, me[1] + (land[1] - me[1]) * kk - math.sin(kk * math.pi) * 6)
            d.ellipse([cc[0] - 3 + j * 0.3, cc[1] - 3 + j * 0.3, cc[0] + 3 - j * 0.3, cc[1] + 3 - j * 0.3], fill=PAL[2 + j % 2] + (int(200 - j * 30),))
        if t > FLY0: orb(d, c, 4.5, rng, 3)
        else: orb(d, me, 2 + (t / FLY0) * 2.5, rng, 2)             # 杖の先で、ふくらむ
    else:
        k = (t - BURST) / (1 - BURST)
        # 着地の地面：焦げた輪
        R = min(1, k / 0.25) * 48
        d.ellipse([land[0] - R, land[1] + 3 - R * 0.6, land[0] + R, land[1] + 3 + R * 0.6], outline=PAL[2] + (int(220 * (1 - k)),), width=2)
        # 球から近くの3体へ（細め）→ そこから、敵→敵へ連鎖（0.12ずつ遅れて走る）
        order = sorted(targets, key=lambda p: math.hypot(p[0] - land[0], p[1] - land[1]))
        links = [(land, order[0]), (land, order[1]), (land, order[2])]
        rest = order[:3]; remaining = order[3:]
        cur = order[2]
        for nxt in remaining:
            links.append((cur, nxt)); cur = nxt
        r2 = random.Random(500 + i // 2)
        for n_, (a0, b0) in enumerate(links):
            t0 = 0.0 if n_ < 3 else 0.10 * (n_ - 2) + 0.05; kk = (k - t0) / 0.30
            if 0 <= kk < 1:
                al = 255 if kk < 0.4 else int(255 * (1 - (kk - 0.4) / 0.6))
                rl = random.Random(900 + n_ * 13 + i // 2); pts = bolt(rl, a0, b0, 0.26)
                draw_bolt(d, pts, 1.4, al)
                if kk < 0.4:
                    j = rl.randrange(len(pts) // 4, len(pts) * 3 // 4); st = pts[j]; draw_bolt(d, bolt(rl, st, (st[0] + rl.uniform(-12, 12), st[1] + rl.uniform(-12, 12)), 0.4, 3), 1, int(al * 0.9))
                    rr = 3.5 * (1 - kk / 0.4) + 1; d.ellipse([b0[0] - rr, b0[1] - rr, b0[0] + rr, b0[1] + rr], fill=PAL[0] + (255,))
        if k < 0.5:
            for _ in range(6):
                a = r2.uniform(0, 6.283); dist = k * 34 * r2.uniform(0.3, 1); x, y = land[0] + math.cos(a) * dist, land[1] + math.sin(a) * dist * 0.7
                d.rectangle([x, y, x + 1, y + 1], fill=PAL[r2.randrange(0, 3)] + (255,))
        # 中心：球が弾ける閃光
        if k < 0.18: rr = 8 * (1 - k / 0.18) + 3; d.ellipse([land[0] - rr, land[1] - rr, land[0] + rr, land[1] + rr], fill=PAL[0] + (255,))
        elif k < 0.5: orb(d, land, max(1, 4 * (1 - (k - 0.18) / 0.32)), rng, 2)
    r_, g_, b_, a_ = im.split(); a_ = a_.point(lambda v: 255 if v > 60 else 0)
    q = Image.merge('RGB', (r_, g_, b_)).quantize(colors=16, dither=Image.NONE).convert('RGB'); return Image.merge('RGBA', (*q.split(), a_))
rng0 = random.Random(3); bg = Image.new('RGB', (W, W), (22, 30, 34)); bd = ImageDraw.Draw(bg)
for _ in range(700): x, y = rng0.randrange(W), rng0.randrange(W); bd.rectangle([x, y, x + 3, y + 3], fill=rng0.choice([(26, 38, 42), (16, 24, 28), (30, 44, 48)]))
frames = [frame(i) for i in range(N)]
os.makedirs('assets/fx/lightning_combo', exist_ok=True)
for i, f in enumerate(frames): f.resize((S * UP, S * UP), Image.NEAREST).save('assets/fx/lightning_combo/combo_%02d.png' % i)
out = []
for i in range(N + 8):
    k = min(i, N - 1); base = bg.copy(); t = k / (N - 1)
    items = [(p[1], 'e', p) for p in targets] + [(me[1], 'm', me)]
    for _, kind, p in sorted(items):
        if kind == 'm': m = mage.resize((mage.width * 4, mage.height * 4), Image.LANCZOS); base.paste(m, (int(p[0] * K - m.width / 2), int(p[1] * K - m.height / 2 + 16)), m)
        else:
            e = enemy.resize((enemy.width * 4, enemy.height * 4), Image.LANCZOS)
            if False: e = ImageChops.add(e.convert('RGB'), Image.new('RGB', e.size, (70, 70, 90))).convert('RGBA'); e.putalpha(enemy.resize(e.size).split()[3])
            base.paste(e, (int(p[0] * K - e.width / 2), int(p[1] * K - e.height / 2 + 8)), e)
    big = frames[k].resize((W, W), Image.NEAREST); lay = Image.new('RGBA', (W, W), (0, 0, 0, 0)); lay.paste(big, (0, 0), big)
    if i < N:
        glow = lay.convert('RGB').filter(ImageFilter.GaussianBlur(12)); base = ImageChops.add(base, glow); base = ImageChops.add(base, glow.point(lambda v: v // 2))
        base.paste(lay.convert('RGB'), (0, 0), lay.split()[3])
    out.append(base)
out[0].save('assets/fx/lightning_combo_demo.gif', save_all=True, append_images=out[1:], duration=60, loop=0)
sheet = Image.new('RGB', (256 * 6, 256 * 2))
for n, i in enumerate((4, 9, 13, 14, 15, 17, 19, 21, 23, 26, 29, 33)): sheet.paste(out[i].resize((256, 256)), ((n % 6) * 256, (n // 6) * 256))
sheet.save('assets/fx/lightning_combo_sheet_preview.png'); print('ok')
