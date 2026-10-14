# 氷霊の守護像の見本：立つ→光る→まわりの敵が遅くなる。 python3 art/make_golem_demo.py
import math, random
from PIL import Image, ImageDraw, ImageChops, ImageFilter
W = H = 512; N = 64; random.seed(6)
def ld(n, k, sc): return [Image.open('assets/chars/%s_%d.png' % (n, i)).convert('RGBA').resize((int(Image.open('assets/chars/%s_%d.png' % (n, i)).width * sc), int(Image.open('assets/chars/%s_%d.png' % (n, i)).height * sc)), Image.LANCZOS) for i in range(k)]
idle = ld('golem_idle', 4, 0.8); glow = ld('golem_glow', 4, 0.8)
sl = Image.open('assets/chars/pet_slime_0.png').convert('RGBA'); sl = sl.resize((int(sl.width * 60 / sl.height), 60), Image.LANCZOS)
r_, g_, b_, a_ = sl.split(); gr = Image.merge('RGB', (r_, g_, b_)).convert('L')
red = Image.merge('RGBA', (*ImageChops.multiply(Image.merge('RGB', (gr,) * 3), Image.new('RGB', sl.size, (255, 130, 130))).split(), a_))
blue = Image.merge('RGBA', (*ImageChops.multiply(Image.merge('RGB', (gr,) * 3), Image.new('RGB', sl.size, (150, 200, 255))).split(), a_))
bg = Image.new('RGB', (W, H), (22, 34, 28)); bd = ImageDraw.Draw(bg)
for _ in range(700): x, y = random.randrange(W), random.randrange(H); bd.rectangle([x, y, x + 3, y + 3], fill=random.choice([(28, 44, 34), (18, 28, 24), (32, 50, 38)]))
gx, gy = 256, 330
mobs = [[random.uniform(0, 6.283), random.uniform(230, 300)] for _ in range(7)]
frames = []
for f in range(N):
    base = bg.copy().convert('RGBA'); fx = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(fx)
    pulse = (f % 32) - 12   # 12コマ目から光る
    ring_k = pulse / 14 if 0 <= pulse < 14 else None
    if ring_k is not None:
        R = 40 + ring_k * 150; al = int(255 * (1 - ring_k) ** 0.7); d.ellipse([gx - R, gy - 12 - R * 0.5, gx + R, gy - 12 + R * 0.5], outline=(190, 235, 255, al), width=4)
    slow_r = 160 if (f % 32) >= 12 or f >= 32 else 0
    items = []
    for m in mobs:
        dist = m[1]; inr = dist < 200
        step = 2.0 if not inr else 0.7   # 範囲の中では、のろい
        m[1] = max(60, m[1] - step); x = gx + math.cos(m[0]) * m[1] * 1.15; y = gy - 20 + math.sin(m[0]) * m[1] * 0.55
        items.append((y, blue if (inr and f > 12) else red, x, y))
    gi = glow[min(3, (f % 32 - 12) // 2)] if (f % 32) >= 12 and (f % 32) < 20 else idle[(f // 5) % 4]
    items.append((gy, gi, gx, gy))
    for y, im, x, yy in sorted(items, key=lambda i: i[0]): base.alpha_composite(im, (int(x - im.width / 2), int(yy - im.height + (0 if im is gi else 30))))
    base.alpha_composite(fx)
    glowl = fx.convert('RGB').filter(ImageFilter.GaussianBlur(8)); rgb = ImageChops.add(base.convert('RGB'), glowl.point(lambda v: v * 5 // 10))
    frames.append(rgb)
    if f % 32 == 31: mobs = [[random.uniform(0, 6.283), random.uniform(230, 300)] for _ in range(7)]
frames[0].save('assets/fx/golem_demo.gif', save_all=True, append_images=frames[1:], duration=70, loop=0); frames[18].save('/tmp/gd18.png'); print('ok')
