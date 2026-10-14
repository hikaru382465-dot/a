# 攻撃エフェクトの見本（上から見る形）：既存の絵を合成して、GIFにする。 python3 art/make_demo.py
import math, random
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageEnhance
A = 'assets/'
W = H = 540; FPS = 20; N = 100
random.seed(4)
def load(p, h=None):
    im = Image.open(A + p).convert('RGBA')
    if h: im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    return im
mage = [load('chars/mage_rapid_walk_%d.png' % i, 110) for i in range(4)]
slime = [load('chars/pet_slime_%d.png' % (i % 3), 56) for i in range(3)]
def tint(im, rgb):
    r, g, b, a = im.split(); gray = ImageEnhance.Brightness(Image.merge('RGB', (r, g, b)).convert('L')).enhance(1.0)
    col = Image.new('RGB', im.size, rgb); out = ImageChops.multiply(Image.merge('RGB', (gray, gray, gray)), col); out = ImageChops.add(out, Image.new('RGB', im.size, (20, 10, 10)))
    return Image.merge('RGBA', (*out.split(), a))
enemy = [tint(s, (255, 120, 120)) for s in slime]
def seq(name, n, size): return [load('fx/%s_%d.png' % (name, i), size) for i in range(n)]
expl = seq('fx_explosion', 8, 170); slash = seq('fx_slash', 6, 160); circ = [load('fx/fx_magic_circle_%d.png' % i, 150) for i in range(3)]
bolt = [Image.open(A + 'fx/fx_lightning_%d.png' % i).convert('RGBA') for i in range(6)]
fire = seq('fire', 8, 120)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
# 地面
ground = Image.new('RGB', (W, H), (22, 34, 28)); gd = ImageDraw.Draw(ground)
for _ in range(900):
    x, y = random.randrange(W), random.randrange(H); c = random.choice([(28, 44, 34), (18, 28, 24), (32, 50, 38)]); gd.rectangle([x, y, x + 3, y + 3], fill=c)
vig = Image.new('L', (W, H), 0); vd = ImageDraw.Draw(vig)
for r in range(0, 300, 6): vd.ellipse([W / 2 - 380 + r, H / 2 - 380 + r, W / 2 + 380 - r, H / 2 + 380 - r], fill=int(255 * min(1, r / 260)))
def add(base, fx, pos, alpha=1.0):
    # 光る合成（足し算）：エフェクトは、明るく
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0)); layer.paste(fx, (int(pos[0] - fx.width / 2), int(pos[1] - fx.height / 2)), fx)
    rgb = layer.convert('RGB'); a = layer.split()[3].point(lambda v: int(255 * (v / 255.0) ** 2.2 * alpha)); rgb = ImageChops.multiply(rgb, Image.merge('RGB', (a, a, a)).point(lambda v: 255 if v > 0 else 0)) if False else rgb
    glow = ImageChops.add(base.convert('RGB'), Image.composite(rgb, Image.new('RGB', base.size), a))
    return glow.convert('RGBA')
def over(base, im, pos):
    base.alpha_composite(im, (int(pos[0] - im.width / 2), int(pos[1] - im.height / 2))); return base
cx, cy = W // 2, H // 2 + 20
E = []
for i in range(7):
    ang = i * 0.9 + 0.3; E.append({'a': ang, 'r': 250 + i * 18, 'dead': None, 'hit': -99, 'kind': ['fire', 'bolt', 'slash'][i % 3]})
nums = []; frames = []
for f in range(N):
    base = ground.convert('RGBA'); t = f / FPS
    # 魔法陣（足もと）
    c = circ[f % 3].copy(); base = add(base, c, (cx, cy + 30), 0.7)
    pos = []
    for e in E:
        if e['dead'] is not None: pos.append(None); continue
        e['r'] = max(60, e['r'] - 3.2); p = (cx + math.cos(e['a']) * e['r'], cy + math.sin(e['a']) * e['r'] * 0.8); pos.append(p)
        if e['r'] <= 130 and e['hit'] < 0 and f % 3 == 0: e['hit'] = f
    # 敵と主人公（奥から手前の順）
    items = [(cy, 'm', None)] + [(p[1], 'e', i) for i, p in enumerate(pos) if p]
    for _, k, i in sorted(items):
        if k == 'm': base = over(base, mage[(f // 4) % 4], (cx, cy))
        else:
            e = E[i]; sp = enemy[(f // 4) % 3]
            if f - e['hit'] < 3 and e['hit'] >= 0:
                al = sp.split()[3]; fl = ImageChops.add(sp.convert('RGB'), Image.new('RGB', sp.size, (140, 140, 140))); sp = Image.merge('RGBA', (*fl.split(), al))
            base = over(base, sp, pos[i])
    # 攻撃
    for i, e in enumerate(E):
        p = pos[i]
        if e['dead'] is not None or p is None or e['hit'] < 0: continue
        k = f - e['hit']
        if e['kind'] == 'fire' and k < 8: base = add(base, expl[k], p); 
        if e['kind'] == 'fire' and k < 8 and k == 0: nums.append([p[0], p[1] - 30, f, str(random.randint(18, 26)), (255, 255, 255)])
        if e['kind'] == 'bolt' and k < 6:
            dx, dy = p[0] - cx, p[1] - cy; L = math.hypot(dx, dy); b = bolt[k].resize((int(L), 110)); b = b.rotate(-math.degrees(math.atan2(dy, dx)), expand=True)
            base = add(base, b, ((cx + p[0]) / 2, (cy + p[1]) / 2)); 
            if k == 0: nums.append([p[0], p[1] - 30, f, str(random.randint(22, 34)), (255, 230, 80)])
        if e['kind'] == 'slash' and k < 6:
            base = add(base, slash[k], p)
            if k == 0: nums.append([p[0], p[1] - 30, f, str(random.randint(15, 22)), (255, 255, 255)])
        if k == 7: e['dead'] = f
    # 数字
    d = ImageDraw.Draw(base)
    for n in nums:
        k = f - n[2]
        if 0 <= k < 14: d.text((n[0] - 14, n[1] - k * 2.2), n[3], font=font, fill=n[4], stroke_width=3, stroke_fill=(0, 0, 0))
    # 軽い色づけと暗い周辺（ホラー向けの雰囲気）
    rgb = base.convert('RGB'); rgb = Image.composite(rgb, ImageEnhance.Brightness(rgb).enhance(0.45), vig)
    frames.append(rgb)
frames[0].save('assets/fx/attack_demo.gif', save_all=True, append_images=frames[1:], duration=1000 // FPS, loop=0, optimize=True)
frames[40].save('assets/fx/attack_demo_still.png')
print('ok', len(frames))
