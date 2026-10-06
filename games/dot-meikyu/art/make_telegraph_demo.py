# 敵の範囲攻撃の見本：赤い予告→炸裂（地ならし・落石・全周の衝撃波）。 python3 art/make_telegraph_demo.py
import math, random
from PIL import Image, ImageDraw, ImageChops, ImageFilter
random.seed(5); W = 480; H = 480; FPS = 30
bg = Image.new('RGB', (W, H), (22, 34, 28)); bd = ImageDraw.Draw(bg)
for _ in range(800): x, y = random.randrange(W), random.randrange(H); bd.rectangle([x, y, x + 3, y + 3], fill=random.choice([(28, 44, 34), (18, 28, 24), (32, 50, 38)]))
gol = Image.open('assets/chars/golem_idle_0.png').convert('RGBA'); gol = gol.resize((int(gol.width * 0.85), int(gol.height * 0.85)), Image.LANCZOS)
mage = Image.open('assets/chars/mage_summon_walk_0.png').convert('RGBA'); mage = mage.resize((int(mage.width * 100 / mage.height), 100), Image.LANCZOS)
BX, BY = 240, 190; MX, MY = 110, 400
def circle(layer, x, y, r, fill, outline=None, sq=0.55):
    d = ImageDraw.Draw(layer); d.ellipse([x - r, y - r * sq, x + r, y + r * sq], fill=fill, outline=outline, width=3)
def scene(f):
    t = f / FPS; base = bg.copy().convert('RGBA'); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fx = Image.new('RGBA', (W, H), (0, 0, 0, 0)); shake = (0, 0)
    # 0〜1.2秒：地ならし（半径3＝120px）。0.9秒かけて濃くなる → 炸裂
    if t < 2.2:
        k = t / 0.9
        if k < 1: a = int(60 + 140 * k); circle(ov, BX, BY + 70, 130, (255, 40, 30, int(a * 0.55)), (255, 80, 60, a))
        elif k < 1 + 0.25 / 0.9:
            b = (k - 1) / (0.25 / 0.9); circle(fx, BX, BY + 70, 130, (255, 245, 210, int(230 * (1 - b))), (255, 255, 255, int(255 * (1 - b)))); shake = (random.randint(-4, 4), random.randint(-3, 3)) if b < 0.6 else (0, 0)
            for q in range(14): a = q * 0.45; r = 130 * (0.5 + b * 0.6); fx_d = ImageDraw.Draw(fx); fx_d.rectangle([BX + math.cos(a) * r, BY + 70 + math.sin(a) * r * .55 - b * 25, BX + math.cos(a) * r + 4, BY + 70 + math.sin(a) * r * .55 - b * 25 + 4], fill=(230, 210, 170, int(255 * (1 - b))))
    # 2.2〜4.0秒：落石（6か所・1.0秒前に予告）
    if 2.2 <= t < 4.2:
        tt = t - 2.2
        spots = [(300, 380), (160, 330), (360, 300), (210, 420), (90, 300), (330, 430)]
        for i, (sx, sy) in enumerate(spots):
            t0 = i * 0.08; k = (tt - t0) / 1.0
            if 0 <= k < 1: a = int(60 + 140 * k); circle(ov, sx, sy, 44, (255, 40, 30, int(a * 0.55)), (255, 80, 60, a)); 
            elif 1 <= k < 1.3:
                b = (k - 1) / 0.3; circle(fx, sx, sy, 44, (255, 245, 210, int(230 * (1 - b))), (255, 255, 255, int(255 * (1 - b)))); shake = (random.randint(-2, 2), random.randint(-2, 2)) if i == 0 else shake
                d = ImageDraw.Draw(fx); [d.rectangle([sx + math.cos(q) * 40 * b, sy + math.sin(q) * 22 * b - 12 * b, sx + math.cos(q) * 40 * b + 4, sy + math.sin(q) * 22 * b - 12 * b + 4], fill=(190, 170, 140, int(255 * (1 - b)))) for q in [0.5 * z for z in range(12)]]
            if -0.5 < k < 0:   # 落ちる岩（予告の前）
                pass
    # 4.4〜6.2秒：全周の衝撃波（半径5＝210px）
    if 4.4 <= t < 6.4:
        tt = t - 4.4; k = tt / 0.9
        if k < 1: a = int(60 + 140 * k); circle(ov, BX, BY + 70, 215, (255, 40, 30, int(a * 0.4)), (255, 80, 60, a))
        elif k < 1.4:
            b = (k - 1) / 0.4; r = 215 * (0.7 + 0.3 * b); circle(fx, BX, BY + 70, r, (0, 0, 0, 0), (255, 255, 255, int(255 * (1 - b)))); circle(fx, BX, BY + 70, r * 0.92, (255, 230, 190, int(120 * (1 - b))), None); shake = (random.randint(-5, 5), random.randint(-4, 4)) if b < 0.7 else (0, 0)
    base.alpha_composite(ov)
    items = [(BY + 160, 'g'), (MY, 'm')]
    for y, kd in sorted(items):
        if kd == 'g': base.alpha_composite(gol, (BX - gol.width // 2, BY + 80 - gol.height + 40))
        else: base.alpha_composite(mage, (MX - mage.width // 2, MY - mage.height))
    base.alpha_composite(fx)
    glow = fx.convert('RGB').filter(ImageFilter.GaussianBlur(10)); rgb = ImageChops.add(base.convert('RGB'), glow.point(lambda v: v * 5 // 10))
    return ImageChops.offset(rgb, *shake) if shake != (0, 0) else rgb
frames = [scene(f) for f in range(int(6.8 * FPS))]
frames[0].save('assets/fx/telegraph_demo.gif', save_all=True, append_images=frames[1:], duration=1000 // FPS, loop=0); frames[int(0.8 * FPS)].save('/tmp/tg1.png'); frames[int(3.0 * FPS)].save('/tmp/tg2.png'); print('ok')
