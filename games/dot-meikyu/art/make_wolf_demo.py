# 幻影の狼の見本（仮の絵：コードで描いた青い狼）。本番はChatGPTの絵に差し替える。 python3 art/make_wolf_demo.py
import math, random
from PIL import Image, ImageDraw, ImageChops, ImageFilter
S = 128; W = 512; K = W / S; N = 56
CY = [(200, 245, 255), (140, 215, 255), (80, 150, 240), (50, 90, 190)]
mage = Image.open('assets/chars/mage_summon_walk_0.png').convert('RGBA'); mage = mage.resize((int(mage.width * 40 / mage.height), 40), Image.LANCZOS)
sl = Image.open('assets/chars/pet_slime_0.png').convert('RGBA'); sl = sl.resize((int(sl.width * 22 / sl.height), 22), Image.LANCZOS)
r_, g_, b_, a_ = sl.split(); gr = Image.merge('RGB', (r_, g_, b_)).convert('L')
enemy = Image.merge('RGBA', (*ImageChops.multiply(Image.merge('RGB', (gr,) * 3), Image.new('RGB', sl.size, (255, 130, 130))).split(), a_))
def wolf(d, x, y, face, phase, alpha):
    # 右向きを基本に、face=-1 で左右反転。4コマの走り（足の動き）
    def P(px, py): return (x + px * face, y + py)
    a = alpha; sw = math.sin(phase) * 3
    body = [P(-7, -4), P(-3, -6), P(4, -6), P(7, -4), P(6, -1), P(-6, -1)]
    d.polygon(body, fill=CY[2] + (a,)); d.polygon([P(-6, -4), P(0, -5.5), P(5, -5), P(5, -3), P(-5, -3)], fill=CY[1] + (a,))
    d.polygon([P(5, -6), P(10, -7), P(12, -4), P(9, -2), P(5, -3)], fill=CY[1] + (a,))                 # 頭
    d.polygon([P(6, -6), P(7, -9), P(8.5, -6.5)], fill=CY[0] + (a,)); d.polygon([P(8.5, -6.5), P(10, -9), P(10.5, -6)], fill=CY[0] + (a,))   # 耳
    d.polygon([P(12, -4), P(14, -3.5), P(12, -2.5)], fill=CY[3] + (a,)); d.rectangle([min(P(9, -5)[0], P(9.8, -4.2)[0]), P(9, -5)[1], max(P(9, -5)[0], P(9.8, -4.2)[0]), P(9, -4.2)[1]], fill=(255, 255, 255, a))  # 鼻・目
    d.polygon([P(-7, -4), P(-12, -7 + sw * 0.4), P(-11, -4), P(-7, -2)], fill=CY[1] + (a,))             # しっぽ
    for lx, ph in ((-5, 0), (-2, 2), (3, 1), (6, 3)):                                                    # 足4本
        o = math.sin(phase + ph) * 3.2; d.line([P(lx, -1), P(lx + o, 3)], fill=CY[2 if ph % 2 else 3] + (a,), width=2)
random.seed(8)
me = (22, 84); tg = [(70, 54), (96, 84), (66, 104)]
bg = Image.new('RGB', (W, W), (22, 34, 28)); bd = ImageDraw.Draw(bg)
for _ in range(700): x, y = random.randrange(W), random.randrange(W); bd.rectangle([x, y, x + 3, y + 3], fill=random.choice([(28, 44, 34), (18, 28, 24), (32, 50, 38)]))
frames = []
hp = [30, 30, 30]
wolves = [{'t': 0.0, 'tg': 0, 'pos': list(me), 'spawn': 6}, {'t': 0.0, 'tg': 1, 'pos': list(me), 'spawn': 8}]
bites = []
for f in range(N):
    base = bg.copy().convert('RGBA'); lay = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # 召喚の魔法陣
    if f < 14:
        k = f / 14; R = 16 * min(1, k * 2); al = int(255 * (1 - k) ** 0.6)
        d.ellipse([me[0] + 12 - R, me[1] + 6 - R * 0.55, me[0] + 12 + R, me[1] + 6 + R * 0.55], outline=CY[0] + (al,), width=1)
        for q in range(6): a = q * 1.05 + f * 0.2; d.rectangle([me[0] + 12 + math.cos(a) * R * 0.9, me[1] + 6 + math.sin(a) * R * 0.5, me[0] + 12 + math.cos(a) * R * 0.9 + 1, me[1] + 6 + math.sin(a) * R * 0.5 + 1], fill=CY[0] + (al,))
    for wi, w in enumerate(wolves):
        if f < w['spawn']: continue
        t = tg[w['tg']]; dx, dy = t[0] - w['pos'][0], t[1] - w['pos'][1]; L = math.hypot(dx, dy)
        if L > 8: w['pos'][0] += dx / L * 3.4; w['pos'][1] += dy / L * 3.4; mode = 'run'
        else:
            mode = 'bite'
            if f % 5 == 0: bites.append((f, t, wi)); hp[w['tg']] -= 7
            if hp[w['tg']] <= 0 or f % 17 == 0: w['tg'] = (w['tg'] + 1) % 3
        life = (f - w['spawn']) / 40; alpha = 255 if life < 0.8 else int(255 * (1 - (life - 0.8) / 0.2))
        if life >= 1: continue
        for tr in range(1, 5):   # かげのしっぽ
            wolf(d, w['pos'][0] - dx / (L or 1) * tr * 3, w['pos'][1] - dy / (L or 1) * tr * 3, 1 if dx >= 0 else -1, f * 1.1, int(alpha * 0.18))
        wolf(d, w['pos'][0], w['pos'][1], 1 if dx >= 0 else -1, f * 1.1 if mode == 'run' else f * 0.5, alpha)
    for bf, t, wi in bites:
        k = f - bf
        if 0 <= k < 4:
            for q in range(5): a = q * 1.26 + bf; d.line([t[0], t[1] - 3, t[0] + math.cos(a) * (3 + k * 2.5), t[1] - 3 + math.sin(a) * (3 + k * 2.5)], fill=CY[0] + (255,), width=1)
    r2, g2, b2, a2 = lay.split(); a2 = a2.point(lambda v: v if v > 60 else 0)
    big = Image.merge('RGBA', (r2, g2, b2, a2)).resize((W, W), Image.NEAREST)
    items = [(me[1], 'm', me)] + [(t[1], 'e', t) for i, t in enumerate(tg) if hp[i] > 0 or f < 50]
    for _, kind, p in sorted(items):
        if kind == 'm': m = mage.resize((mage.width * 4, mage.height * 4), Image.LANCZOS); base.alpha_composite(m, (int(p[0] * K - m.width / 2), int(p[1] * K - m.height / 2 + 16)))
        else:
            e = enemy.resize((enemy.width * 4, enemy.height * 4), Image.LANCZOS); base.alpha_composite(e, (int(p[0] * K - e.width / 2), int(p[1] * K - e.height / 2 + 8)))
    glow = big.convert('RGB').filter(ImageFilter.GaussianBlur(10)); rgb = ImageChops.add(base.convert('RGB'), glow.point(lambda v: v * 6 // 10))
    rgb.paste(big.convert('RGB'), (0, 0), big.split()[3]); frames.append(rgb)
frames[0].save('assets/fx/wolf_demo.gif', save_all=True, append_images=frames[1:], duration=60, loop=0)
frames[24].save('/tmp/wolf24.png'); print('ok')
