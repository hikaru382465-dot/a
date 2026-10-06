# 稲妻の連鎖：杖から敵へ、敵から敵へ。Lvが上がると太く・枝が増える。 python3 art/make_lightning_chain.py
import math, random, os
from PIL import Image, ImageDraw, ImageChops, ImageFilter, ImageEnhance
S = 128; UP = 3; N = 20
PAL = [(255, 255, 255), (235, 225, 255), (180, 160, 255), (120, 90, 235), (70, 50, 170)]
mage = Image.open('assets/chars/mage_rapid_walk_0.png').convert('RGBA'); mage = mage.resize((int(mage.width * 40 / mage.height), 40), Image.LANCZOS)
slime = Image.open('assets/chars/pet_slime_0.png').convert('RGBA'); slime = slime.resize((int(slime.width * 22 / slime.height), 22), Image.LANCZOS)
def tint(im):
    r, g, b, a = im.split(); gray = Image.merge('RGB', (r, g, b)).convert('L'); col = ImageChops.multiply(Image.merge('RGB', (gray,) * 3), Image.new('RGB', im.size, (255, 130, 130)))
    return Image.merge('RGBA', (*col.split(), a))
enemy = tint(slime)
def bolt(rng, p0, p1, spread, depth=5):
    pts = [p0, p1]
    for _ in range(depth):
        new = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
            off = rng.uniform(-1, 1) * spread * L * 0.5
            new += [(mx - dy / L * off, my + dx / L * off), b]
        pts = new; spread *= 0.85
    return pts
def draw_bolt(d, pts, level, col_w, alpha):
    for w, col in ((col_w * 3, PAL[3]), (col_w * 2, PAL[2]), (col_w, PAL[0])):
        d.line(pts, fill=col + (alpha,), width=max(1, int(w)), joint='curve')
def render(level, seed):
    rng = random.Random(seed); frames = []
    me = (22, 78); targets = [(70, 50), (98, 76), (84, 100)]
    width = 1 + level * 0.5; branches = 1 + level
    for i in range(N):
        t = i / (N - 1); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        chain = [me] + targets[:2 + (1 if level >= 3 else 0)]
        # 1発ごとに、順番に光る（0.0秒、0.25、0.5）
        for seg, (a, b) in enumerate(zip(chain, chain[1:])):
            t0 = seg * 0.22; k = (t - t0) / 0.42
            if 0 <= k < 1:
                alpha = int(255 * (1 - k) ** 0.7 if k > 0.35 else 255)
                r2 = random.Random(seed * 100 + seg * 7 + i // 2)       # 2コマごとに形が変わる（ちかちか）
                pts = bolt(r2, a, b, 0.28)
                draw_bolt(d, pts, level, width, alpha)
                for _ in range(branches):                              # 枝：途中から、まわりへ
                    j = r2.randrange(len(pts) // 4, len(pts) * 3 // 4); st = pts[j]; ang = math.atan2(b[1] - a[1], b[0] - a[0]) + r2.uniform(-1.2, 1.2); ln = r2.uniform(8, 16) * (0.7 + level * 0.15)
                    en = (st[0] + math.cos(ang) * ln, st[1] + math.sin(ang) * ln); draw_bolt(d, bolt(r2, st, en, 0.35, 3), level, max(1, width * 0.5), int(alpha * 0.9))
                if k < 0.15:   # 当たった点の閃光
                    rr = 7 + level
                    d.ellipse([b[0] - rr, b[1] - rr, b[0] + rr, b[1] + rr], fill=PAL[0] + (255,))
                if k < 0.6:    # 火花
                    for _ in range(4 + level * 2):
                        ang = r2.uniform(0, 6.283); dist = k * 22 * r2.uniform(0.4, 1); x, y = b[0] + math.cos(ang) * dist, b[1] + math.sin(ang) * dist
                        d.rectangle([x, y, x + 1, y + 1], fill=PAL[r2.randrange(0, 3)] + (255,))
        r_, g_, b_, a_ = im.split(); a_ = a_.point(lambda v: 255 if v > 60 else 0)
        q = Image.merge('RGB', (r_, g_, b_)).quantize(colors=16, dither=Image.NONE).convert('RGB')
        frames.append(Image.merge('RGBA', (*q.split(), a_)))
    return frames
os.makedirs('assets/fx/lightning_chain', exist_ok=True)
rng0 = random.Random(3); W = 384
def bg_img():
    bg = Image.new('RGB', (W, W), (22, 30, 34)); bd = ImageDraw.Draw(bg)
    for _ in range(420): x, y = rng0.randrange(W), rng0.randrange(W); bd.rectangle([x, y, x + 3, y + 3], fill=rng0.choice([(26, 38, 42), (16, 24, 28), (30, 44, 48)]))
    return bg
bgs = bg_img(); tgs = [(70, 50), (98, 76), (84, 100)]; me = (22, 78); K = W / S
clips = []
for lv, seed in ((1, 1), (5, 2)):
    frames = render(lv, seed)
    for i, f in enumerate(frames): f.resize((S * UP, S * UP), Image.NEAREST).save('assets/fx/lightning_chain/lv%d_%02d.png' % (lv, i))
    clip = []
    for i in range(N + 4):
        base = bgs.copy(); k = min(i, N - 1)
        for p in tgs[:2 + (1 if lv >= 3 else 0)]:
            e = enemy.resize((enemy.width * 3, enemy.height * 3), Image.LANCZOS)
            hit = any(0 <= (k / (N - 1) - j * 0.22) / 0.42 < 0.3 for j in range(3)) and False
            base.paste(e, (int(p[0] * K - e.width / 2), int(p[1] * K - e.height / 2 + 8)), e)
        m = mage.resize((mage.width * 3, mage.height * 3), Image.LANCZOS); base.paste(m, (int(me[0] * K - m.width / 2), int(me[1] * K - m.height / 2 + 14)), m)
        big = frames[k].resize((W, W), Image.NEAREST); lay = Image.new('RGBA', (W, W), (0, 0, 0, 0)); lay.paste(big, (0, 0), big)
        if i < N:
            glow = lay.convert('RGB').filter(ImageFilter.GaussianBlur(10)); base = ImageChops.add(base, glow); base = ImageChops.add(base, glow.point(lambda v: v // 2))
            base.paste(lay.convert('RGB'), (0, 0), lay.split()[3])
        ImageDraw.Draw(base).text((8, 6), 'Lv%d' % lv, fill=(255, 255, 255))
        clip.append(base)
    clips.append(clip)
out = []
for a, b in zip(*clips):
    s = Image.new('RGB', (W * 2 + 6, W), (0, 0, 0)); s.paste(a, (0, 0)); s.paste(b, (W + 6, 0)); out.append(s)
out[0].save('assets/fx/lightning_demo.gif', save_all=True, append_images=out[1:], duration=60, loop=0)
sheet = Image.new('RGB', ((W + 3) * 4, (W // 2 + 3) * 2))
for n, i in enumerate((3, 6, 9, 12)): sheet.paste(out[i].resize(((W * 2 + 6) // 2, W // 2)), ((n % 2) * ((W * 2 + 6) // 2), (n // 2) * (W // 2)))
sheet.save('assets/fx/lightning_sheet_preview.png'); print('ok')
