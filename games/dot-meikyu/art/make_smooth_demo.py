# 攻撃をなめらかに見せる工夫の見本（左：今のまま／右：直した版）。 python3 art/make_smooth_demo.py
import math, random
from PIL import Image, ImageDraw, ImageChops, ImageFilter
random.seed(3); FPS = 30; W = 400; H = 330
ka = [Image.open('assets/chars/knight_attack_%d.png' % i).convert('RGBA') for i in range(5)]
sc = 0.8; ka = [i.resize((int(i.width * sc), int(i.height * sc)), Image.LANCZOS) for i in ka]
sl = Image.open('assets/chars/pet_slime_0.png').convert('RGBA'); sl = sl.resize((int(sl.width * 54 / sl.height), 54), Image.LANCZOS)
r_, g_, b_, a_ = sl.split(); gr = Image.merge('RGB', (r_, g_, b_)).convert('L')
red = Image.merge('RGBA', (*ImageChops.multiply(Image.merge('RGB', (gr,) * 3), Image.new('RGB', sl.size, (255, 130, 130))).split(), a_))
bg = Image.new('RGB', (W, H), (22, 34, 28)); bd = ImageDraw.Draw(bg)
for _ in range(500): x, y = random.randrange(W), random.randrange(H); bd.rectangle([x, y, x + 3, y + 3], fill=random.choice([(28, 44, 34), (18, 28, 24), (32, 50, 38)]))
FX, FY = 130, 290; EX, EY = 290, 290
def blend(a, b, t):
    w = max(a.width, b.width); h = max(a.height, b.height); A = Image.new('RGBA', (w, h)); B = Image.new('RGBA', (w, h)); A.paste(a, (0, h - a.height)); B.paste(b, (0, h - b.height)); return Image.blend(A, B, t)
def old(f):   # 今のまま：5コマを同じ長さで（3フレームずつ）
    base = bg.copy().convert('RGBA'); i = min(4, f // 4 % 7) if (f // 4) % 7 < 5 else 4
    s = ka[min(4, (f // 4) % 5)]; base.alpha_composite(s, (FX - 40, FY - s.height)); base.alpha_composite(red, (EX - red.width // 2, EY - red.height)); return base
def new(f):
    # 時間割（フレーム数）：1ため 5 / 1→2 ぶれ 1 / 2 すばやく 2 / 3 当たり 4（ヒットストップ）/ 4 戻り 3 / 5 立ち 4
    sched = [(0, 5)] + [('b12', 1)] + [(1, 2)] + [('b23', 1)] + [(2, 5)] + [(3, 3)] + [(4, 5)]
    total = sum(n for _, n in sched); ff = f % total; acc = 0; cur = None; local = 0
    for k, n in sched:
        if ff < acc + n: cur = k; local = ff - acc; break
        acc += n
    base = bg.copy().convert('RGBA'); d = ImageDraw.Draw(base)
    if cur == 'b12': s = blend(ka[0], ka[1], 0.55)
    elif cur == 'b23': s = blend(ka[1], ka[2], 0.5)
    else: s = ka[cur]
    dx = {0: -2, 'b12': 2, 1: 6, 'b23': 8, 2: 10, 3: 6, 4: 2}.get(cur, 0)      # 切るときに、前へ踏みこむ
    ex = 0; shake = (0, 0); flash = False
    hit = (cur == 2)
    if hit:
        shake = (random.randint(-3, 3), random.randint(-2, 2)) if local < 3 else (0, 0); ex = min(10, local * 4); flash = local < 2
    pos = (FX - 40 + dx, FY - s.height)
    # 残像（切るとき）
    if cur in ('b12', 1, 'b23'):
        gh = ka[0].copy(); gh.putalpha(gh.split()[3].point(lambda v: int(v * 0.25))); base.alpha_composite(gh, (FX - 40 - 6, FY - gh.height))
    base.alpha_composite(s, pos)
    e = red
    if flash: al = red.split()[3]; e = Image.merge('RGBA', (*ImageChops.add(red.convert('RGB'), Image.new('RGB', red.size, (150, 150, 150))).split(), al))
    base.alpha_composite(e, (EX - red.width // 2 + ex, EY - red.height))
    if hit and local < 3:   # 火花
        for q in range(8): a = q * 0.8 + random.random() * 0.3; r = 10 + local * 14; d.line([EX - 20, EY - 30, EX - 20 + math.cos(a) * r, EY - 30 + math.sin(a) * r], fill=(255, 255, 255, 255), width=2)
    if shake != (0, 0): base = ImageChops.offset(base.convert('RGB'), *shake).convert('RGBA')
    return base
frames = []
for f in range(75):
    L = old(f); R = new(f); s = Image.new('RGB', (W * 2 + 6, H), (0, 0, 0)); s.paste(L.convert('RGB'), (0, 0)); s.paste(R.convert('RGB'), (W + 6, 0))
    ImageDraw.Draw(s).text((8, 6), 'before', fill=(255, 255, 255)); ImageDraw.Draw(s).text((W + 14, 6), 'after', fill=(255, 255, 255)); frames.append(s)
frames[0].save('assets/fx/smooth_demo.gif', save_all=True, append_images=frames[1:], duration=1000 // FPS, loop=0); print('ok')
