# 幻影の狼の見本（ChatGPTの絵）：魔法陣→2匹が走って噛む→消える。 python3 art/make_wolf_demo.py
import math, random
from PIL import Image, ImageDraw, ImageChops, ImageFilter
W = 512; N = 64; random.seed(8)
run = [Image.open('assets/chars/wolf_run_%d.png' % i).convert('RGBA') for i in range(8)]
bite = [Image.open('assets/chars/wolf_bite_%d.png' % i).convert('RGBA') for i in range(5)]
SC = 0.7
def sc(im): return im.resize((int(im.width * SC), int(im.height * SC)), Image.LANCZOS)
run = [sc(i) for i in run]; bite = [sc(i) for i in bite]
mage = Image.open('assets/chars/mage_summon_walk_0.png').convert('RGBA'); mage = mage.resize((int(mage.width * 160 / mage.height), 160), Image.LANCZOS)
sl = Image.open('assets/chars/pet_slime_0.png').convert('RGBA'); sl = sl.resize((int(sl.width * 60 / sl.height), 60), Image.LANCZOS)
r_, g_, b_, a_ = sl.split(); gr = Image.merge('RGB', (r_, g_, b_)).convert('L')
enemy = Image.merge('RGBA', (*ImageChops.multiply(Image.merge('RGB', (gr,) * 3), Image.new('RGB', sl.size, (255, 130, 130))).split(), a_))
bg = Image.new('RGB', (W, W), (22, 34, 28)); bd = ImageDraw.Draw(bg)
for _ in range(700): x, y = random.randrange(W), random.randrange(W); bd.rectangle([x, y, x + 3, y + 3], fill=random.choice([(28, 44, 34), (18, 28, 24), (32, 50, 38)]))
me = (88, 340); tg = [(280, 220), (390, 330), (270, 420)]
hp = [100, 100, 100]
wolves = [{'tg': 0, 'pos': [me[0] + 30, me[1] - 10], 'spawn': 6, 'state': 'run', 'bt': 0}, {'tg': 1, 'pos': [me[0] + 30, me[1] + 10], 'spawn': 10, 'state': 'run', 'bt': 0}]
frames = []; flash = {}
for f in range(N):
    base = bg.copy().convert('RGBA'); fx = Image.new('RGBA', (W, W), (0, 0, 0, 0)); d = ImageDraw.Draw(fx)
    if f < 16:   # 魔法陣
        k = f / 16; R = 70 * min(1, k * 2); al = int(255 * (1 - k) ** 0.6); cx, cy = me[0] + 50, me[1] + 24
        d.ellipse([cx - R, cy - R * 0.55, cx + R, cy + R * 0.55], outline=(200, 245, 255, al), width=3)
        for q in range(6): a = q * 1.05 + f * 0.2; d.ellipse([cx + math.cos(a) * R * 0.9 - 3, cy + math.sin(a) * R * 0.5 - 3, cx + math.cos(a) * R * 0.9 + 3, cy + math.sin(a) * R * 0.5 + 3], fill=(200, 245, 255, al))
    sprites = []
    for w in wolves:
        if f < w['spawn']: continue
        life = (f - w['spawn']) / 44
        if life >= 1: continue
        alpha = 1.0 if life < 0.85 else 1 - (life - 0.85) / 0.15
        alpha = min(alpha, min(1, (f - w['spawn']) / 4))
        t = tg[w['tg']]; dx, dy = t[0] - w['pos'][0], t[1] - w['pos'][1]; L = math.hypot(dx, dy); face = 1 if dx >= 0 else -1
        if w['state'] == 'run':
            if L > 70: w['pos'][0] += dx / L * 13; w['pos'][1] += dy / L * 13; img = run[(f // 1) % 8]
            else: w['state'] = 'bite'; w['bt'] = 0; img = bite[0]
        if w['state'] == 'bite':
            img = bite[min(4, w['bt'] // 1)]; w['bt'] += 1
            if w['bt'] == 3: hp[w['tg']] -= 35; flash[w['tg']] = f
            if w['bt'] >= 6: w['state'] = 'run'; w['tg'] = (w['tg'] + 1) % 3
        spr = img if face > 0 else img.transpose(Image.FLIP_LEFT_RIGHT)
        if alpha < 1: spr = spr.copy(); spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
        sprites.append((w['pos'][1], spr, w['pos'][0], w['pos'][1]))
        if w['state'] == 'run':   # 残像
            for j in (1, 2, 3):
                gh = spr.copy(); gh.putalpha(gh.split()[3].point(lambda v: int(v * 0.16 / j)))
                fx.alpha_composite(gh, (int(w['pos'][0] - dx / (L or 1) * j * 16 - spr.width / 2), int(w['pos'][1] - dy / (L or 1) * j * 16 - spr.height / 2)))
    # 絵を並べる（奥から手前）
    items = [(me[1], 'm', me)] + [(tg[i][1], 'e', i) for i in range(3) if hp[i] > -20 and not (hp[i] <= 0 and f - flash.get(i, 0) > 6)] + [(s[0], 'w', s) for s in sprites]
    for _, kind, p in sorted(items, key=lambda x: x[0]):
        if kind == 'm': base.alpha_composite(mage, (int(p[0] - mage.width / 2), int(p[1] - mage.height + 20)))
        elif kind == 'e':
            e = enemy
            if f - flash.get(p, -9) < 3: al = enemy.split()[3]; e = Image.merge('RGBA', (*ImageChops.add(enemy.convert('RGB'), Image.new('RGB', enemy.size, (120, 120, 140))).split(), al))
            base.alpha_composite(e, (int(tg[p][0] - e.width / 2), int(tg[p][1] - e.height / 2)))
        else:
            _, spr, x, y = p; base.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height / 2)))
    for i, t0 in flash.items():
        k = f - t0
        if 0 <= k < 4:
            tx, ty = tg[i]
            for q in range(7): a = q * 0.9 + t0; d.line([tx, ty - 20, tx + math.cos(a) * (14 + k * 10), ty - 20 + math.sin(a) * (14 + k * 10)], fill=(255, 255, 255, 255), width=3)
    glow = fx.convert('RGB').filter(ImageFilter.GaussianBlur(10)); rgb = ImageChops.add(base.convert('RGB'), glow.point(lambda v: v * 5 // 10))
    rgb.paste(fx.convert('RGB'), (0, 0), fx.split()[3]); frames.append(rgb)
frames[0].save('assets/fx/wolf_demo.gif', save_all=True, append_images=frames[1:], duration=55, loop=0)
frames[26].save('/tmp/wolf26.png'); print('ok')
