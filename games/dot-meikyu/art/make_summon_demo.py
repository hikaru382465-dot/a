# 召喚の見本：騎士が走って切る／射手が矢を射る／狼が噛む。 python3 art/make_summon_demo.py
import math, random
from PIL import Image, ImageDraw, ImageChops, ImageFilter
W = 640; H = 480; N = 72; random.seed(2)
def ld(n, k, sc): return [Image.open('assets/chars/%s_%d.png' % (n, i)).convert('RGBA') for i in range(k)]
def S(ims, sc): return [i.resize((int(i.width * sc), int(i.height * sc)), Image.LANCZOS) for i in ims]
kw, ka = S(ld('knight_walk', 8, 0), 0.62), S(ld('knight_attack', 5, 0), 0.62)
aw, ash = S(ld('archer_walk', 8, 0), 0.62), S(ld('archer_shoot', 5, 0), 0.62)
wr, wb = S(ld('wolf_run', 8, 0), 0.6), S(ld('wolf_bite', 5, 0), 0.6)
mage = Image.open('assets/chars/mage_summon_walk_0.png').convert('RGBA'); mage = mage.resize((int(mage.width * 140 / mage.height), 140), Image.LANCZOS)
sl = Image.open('assets/chars/pet_slime_0.png').convert('RGBA'); sl = sl.resize((int(sl.width * 56 / sl.height), 56), Image.LANCZOS)
r_, g_, b_, a_ = sl.split(); gr = Image.merge('RGB', (r_, g_, b_)).convert('L')
enemy = Image.merge('RGBA', (*ImageChops.multiply(Image.merge('RGB', (gr,) * 3), Image.new('RGB', sl.size, (255, 130, 130))).split(), a_))
bg = Image.new('RGB', (W, H), (22, 34, 28)); bd = ImageDraw.Draw(bg)
for _ in range(900): x, y = random.randrange(W), random.randrange(H); bd.rectangle([x, y, x + 3, y + 3], fill=random.choice([(28, 44, 34), (18, 28, 24), (32, 50, 38)]))
def put(base, im, x, y): base.alpha_composite(im, (int(x - im.width / 2), int(y - im.height)))   # (x,y)＝足もと
me = (70, 300); ek = (330, 250); ea = (560, 390); ew = (470, 300)
frames = []
for f in range(N):
    base = bg.copy().convert('RGBA'); items = []
    items.append((me[1], mage, me))
    # 騎士：歩く8コマ → 切る5コマ をくりかえす
    cyc = f % 28
    if cyc < 14: kimg = kw[(cyc // 2) % 8]; kx = 150 + cyc * 8
    else: kimg = ka[min(4, (cyc - 14) // 2)]; kx = 262
    items.append((300, kimg, (kx, 300)))
    # 射手：矢を射る
    acyc = f % 24
    aimg = ash[min(4, acyc // 5)] if acyc < 24 else aw[0]
    items.append((420, aimg, (130, 420)))
    # 狼
    wcyc = f % 30
    if wcyc < 18: wimg = wr[wcyc % 8]; wx = 200 + wcyc * 12
    else: wimg = wb[min(4, (wcyc - 18) // 2)]; wx = 416
    items.append((360, wimg, (wx, 360)))
    for y, im, p in sorted(items, key=lambda i: i[0]): put(base, im, p[0], p[1])
    for p in (ek, ew, ea): base.alpha_composite(enemy, (int(p[0] - enemy.width / 2), int(p[1] - enemy.height)))
    d = ImageDraw.Draw(base)
    if 10 <= acyc < 16:    # 矢
        k = (acyc - 10) / 5; x = 200 + k * 360; d.line([x - 30, 372, x, 372], fill=(210, 250, 255, 255), width=3)
    glow = base.convert('RGB').filter(ImageFilter.GaussianBlur(8)); rgb = ImageChops.add(base.convert('RGB'), glow.point(lambda v: v // 6))
    frames.append(rgb)
frames[0].save('assets/fx/summon_demo.gif', save_all=True, append_images=frames[1:], duration=60, loop=0)
frames[16].save('/tmp/sd16.png'); print('ok')
