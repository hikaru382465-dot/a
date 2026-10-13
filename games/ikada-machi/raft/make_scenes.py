# 景色の図鑑の絵を、コードでドット絵ふうに描く。使い方：python3 make_scenes.py → scenes_art.js
import numpy as np, base64, io, json, math
from PIL import Image
W, H = 192, 108
HZ = 60  # 水平線のy
B4 = np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]) / 16.0
def hx(c): c = c.lstrip('#'); return np.array([int(c[i:i+2], 16) for i in (0, 2, 4)], float)
def rng(seed): return np.random.RandomState(seed)
def noise(seed, w, h, sc, sx=1.0):
    r = rng(seed); gw, gh = int(w / sc / sx) + 3, int(h / sc) + 3; g = r.rand(gh, gw)
    ys, xs = np.mgrid[0:h, 0:w]; fx, fy = xs / sc / sx, ys / sc; x0, y0 = fx.astype(int), fy.astype(int); tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    return (g[y0, x0] * (1 - tx) + g[y0, x0 + 1] * tx) * (1 - ty) + (g[y0 + 1, x0] * (1 - tx) + g[y0 + 1, x0 + 1] * tx) * ty
def fbm(seed, w, h, sc): return noise(seed, w, h, sc) * .55 + noise(seed + 1, w, h, sc / 2) * .3 + noise(seed + 2, w, h, sc / 4) * .15
YS, XS = np.mgrid[0:H, 0:W]
def dgrad(top, bot, levels, y0, y1):
    t = np.clip((YS - y0) / max(1, y1 - y0), 0, 1) * (levels - 1); lo = np.floor(t); f = t - lo
    k = lo + (f > B4[YS % 4, XS % 4]); k = np.clip(k, 0, levels - 1) / (levels - 1)
    return hx(top)[None, None, :] * (1 - k[..., None]) + hx(bot)[None, None, :] * k[..., None]
def glow(img, cx, cy, r, col, a):
    d = np.hypot((XS - cx) * 0.8, (YS - cy)) / r; m = np.clip(1 - d, 0, 1) ** 2 * a
    m = np.floor(m * 5 + B4[YS % 4, XS % 4]) / 5; m = np.clip(m, 0, 1)[..., None]; return img * (1 - m) + hx(col) * m
def disc(img, cx, cy, r, col, edge=None):
    d = np.hypot(XS - cx, YS - cy); m = d <= r; img[m] = hx(col)
    if edge: img[(d <= r) & (d > r - 1)] = hx(edge)
    return img
def clouds(img, seed, cover, lit, mid, dark, ytop, ybot, sc=14, stretch=2.6, litdir=(1, -1)):
    n = noise(seed, W, H, sc, stretch) * .5 + noise(seed + 1, W, H, sc / 2, stretch) * .32 + noise(seed + 2, W, H, sc / 4, stretch) * .18
    band = np.clip((YS - ytop) / max(1, ybot - ytop), 0, 1); prof = np.sin(band * math.pi) ** .6
    v = n * (.35 + .65 * prof); th = 1 - cover * .75
    m = v > th * .8
    up = np.roll(v, 2, 0); lo = np.roll(v, -2, 0)
    top_m = m & (up < th * .8 + .0) | (m & (v > th * .8 + .13))
    low_m = m & (v < th * .8 + .05) & (lo < v) 
    img[m] = hx(mid); img[low_m & m] = hx(dark); img[top_m & m] = hx(lit); return img
def stars(img, seed, n, below=HZ - 2, col='#ffffff'):
    r = rng(seed)
    for i in range(n):
        x, y = r.randint(0, W), r.randint(0, below); b = r.rand()
        img[y, x] = hx(col) * (.55 + .45 * b) + hx('#1a2a5a') * (.45 - .45 * b)
        if b > .9 and 0 < x < W - 1 and 0 < y < H - 1:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): img[y + dy, x + dx] = hx(col) * .6 + hx('#1a2a5a') * .4
    return img
def sea(img, top, bot, seed, wave_col, wave_n=70, calm=0.0, white=0.0):
    s = dgrad(top, bot, 7, HZ, H); img[HZ:] = s[HZ:]
    r = rng(seed)
    for i in range(wave_n):
        y = HZ + 1 + int((r.rand() ** 1.6) * (H - HZ - 2)); depth = (y - HZ) / (H - HZ); ln = int(3 + depth * 16 * (1 - .5 * calm)); x = r.randint(-5, W)
        for dx in range(ln):
            if 0 <= x + dx < W: img[y, x + dx] = img[y, x + dx] * (1 - .55) + hx(wave_col) * .55
    if white:
        for i in range(int(wave_n * white)):
            y = HZ + 3 + int((r.rand() ** 1.2) * (H - HZ - 4)); ln = int(4 + (y - HZ) / 4 * r.rand() * 2); x = r.randint(0, W)
            for dx in range(ln):
                if 0 <= x + dx < W: img[y, x + dx] = hx('#e8f0f4') * (.9 - .3 * (dx / ln)) + img[y, x + dx] * (.1 + .3 * (dx / ln))
            if y + 1 < H:
                for dx in range(1, ln - 1):
                    if 0 <= x + dx < W: img[y + 1, x + dx] = img[y + 1, x + dx] * .6 + hx('#9fb3c4') * .4
    return img
def reflect_col(img, cx, col, spread=1.0, a=.9, seed=3):
    r = rng(seed)
    for y in range(HZ + 1, H):
        d = (y - HZ) / (H - HZ); half = 1 + d * 16 * spread
        for x in range(int(cx - half), int(cx + half) + 1):
            if not (0 <= x < W): continue
            if r.rand() < .55 - .25 * abs(x - cx) / half and (y % 2 == 0 or r.rand() < .35):
                k = a * (1 - .4 * d) * (1 - .6 * abs(x - cx) / half)
                img[y, x] = img[y, x] * (1 - k) + hx(col) * k
    return img
def mirror(img, k):
    src = img[:HZ][::-1]; n = H - HZ; idx = np.minimum((np.arange(n) * HZ / n).astype(int), HZ - 1)
    ref = src[idx]; wob = (np.sin(np.arange(n) * .9) * 1.2).astype(int)
    for i in range(n):
        ref[i] = np.roll(ref[i], wob[i] * (1 if i % 3 else 0), 0)
    fade = (1 - np.arange(n) / n * .5)[:, None, None]
    img[HZ:] = img[HZ:] * (1 - k) + ref * k * fade * .85 + img[HZ:] * k * (1 - fade) * .0; return img
def rain(img, seed, n, col='#b9cbe0', a=.5, ln=9):
    r = rng(seed)
    for i in range(n):
        x, y = r.randint(0, W + 20), r.randint(-5, H)
        for k in range(ln):
            xx, yy = x - k // 2 - 0, y + k
            if 0 <= xx < W and 0 <= yy < H: img[yy, xx] = img[yy, xx] * (1 - a * (1 - k / ln)) + hx(col) * a * (1 - k / ln)
    return img
def bolt(img, x, col='#f4f2ff'):
    r = rng(int(x)); y = 4
    while y < HZ + 2:
        for k in range(2):
            if 0 <= x < W: img[y, int(x)] = hx(col)
            if 0 <= x + 1 < W and k: img[y, int(x) + 1] = hx(col) * .6 + img[y, int(x) + 1] * .4
            y += 1
        x += r.randint(-3, 4)
    return glow(img, x, HZ - 8, 38, '#c8c4ff', .35)
def raft(img, glowc, lit=True, dark='#150f1c', x0=18):
    d = hx(dark); y = 92
    for x in range(x0, x0 + 60):
        img[y:y + 3, x] = d; 
    for x in range(x0 + 2, x0 + 58): img[y + 3, x] = d * .8
    # 人2人と柱（ランタン）
    for (bx, h) in ((x0 + 14, 9), (x0 + 24, 8)):
        img[y - h:y, bx:bx + 4] = d; img[y - h - 4:y - h, bx:bx + 4] = d; img[y - h - 5, bx + 1:bx + 3] = d
    img[y - 14:y, x0 + 48] = d; img[y - 14, x0 + 46:x0 + 52] = d
    if lit:
        img = glow(img, x0 + 52, y - 12, 14, glowc, .55); img[y - 12:y - 9, x0 + 51:x0 + 54] = hx('#ffd98a'); 
    return img
def vignette(img, a=.28):
    d = np.hypot((XS - W / 2) / (W / 2), (YS - H / 2) / (H / 2)); m = np.clip(d - .55, 0, 1) ** 1.5 * a; return img * (1 - m[..., None])
def horizon(img, col, a=.6):
    for dy, k in ((-1, .35), (0, a), (1, .25)):
        img[HZ + dy] = img[HZ + dy] * (1 - k) + hx(col) * k
    return img

def scene(key):
    t, w = key.split('_'); sd = sum(map(ord, key)); img = np.zeros((H, W, 3))
    P = {
     'dawn': dict(sky=('#2c3f7a', '#f6b57c'), sun=(120, HZ - 3, '#fff0c0', '#ffd08a'), cl=('#ffe2b8', '#e49a8a', '#7a5a86'), sea=('#d98f7a', '#2a4a78'), gl='#ffc890', wave='#f2b090', refl='#ffe0a0'),
     'day': dict(sky=('#2a78c8', '#a8e0f4'), sun=(140, 16, '#fffbe0', '#fff2a0'), cl=('#ffffff', '#d8ecf6', '#9cc0dc'), sea=('#3e9cc8', '#134a82'), gl='#fff2b0', wave='#bfe8f8', refl='#fff6c0'),
     'dusk': dict(sky=('#3a2a6e', '#ff9a5a'), sun=(72, HZ - 5, '#fff0b0', '#ffb060'), cl=('#ffc08a', '#d4607a', '#4a2a62'), sea=('#c06a7a', '#241a4a'), gl='#ff9a60', wave='#ff9a8a', refl='#ffc070'),
     'night': dict(sky=('#050a1e', '#1c2c62'), sun=(130, 20, '#f6f4e0', '#dcdcc8'), cl=('#4a5c92', '#2a3866', '#141c3c'), sea=('#16285a', '#050a1e'), gl='#ffd98a', wave='#4a68b0', refl='#e8e8d0')}[t]
    sky = dgrad(P['sky'][0], P['sky'][1], 9, 0, HZ); img[:] = sky
    st = w == 'storm'; ca = w == 'calm'
    if t == 'night' and not st: img = stars(img, sd, 140 if ca else 110)
    # 天体
    cx, cy, c1, c2 = P['sun']
    if not st:
        img = glow(img, cx, cy, 46 if t != 'day' else 34, c2, .75)
        if t == 'night':
            img = disc(img, cx, cy, 6, c1, '#ffffff'); img = disc(img, cx + 2, cy - 1, 5, c2); img = disc(img, cx - 2, cy + 1, 1, '#b8b8a0'); 
        else:
            img = disc(img, cx, cy, 7 if t != 'day' else 6, c1, c2)
    # 雲
    if st:
        dark = {'dawn': ('#8a8a9a', '#58607a', '#2a3048'), 'day': ('#98a4b6', '#58667e', '#2a3448'), 'dusk': ('#9a6a6a', '#5a3a4e', '#241830'), 'night': ('#3a4058', '#202638', '#0c0e18')}[t]
        bs = {'dawn': ('#3a4058', '#9a8a90'), 'day': ('#3c4a60', '#9aaabc'), 'dusk': ('#1e1830', '#a0605a'), 'night': ('#04060e', '#1c2236')}[t]
        img[:] = dgrad(bs[0], bs[1], 10, 0, HZ)
        img = clouds(img, sd, .8, *dark, 4, HZ - 2, 18, 2.6)
        img = clouds(img, sd + 7, .6, *dark, 0, 30, 12, 2.6)
        if t == 'dusk': img = glow(img, 70, HZ, 30, '#ff7a4a', .5)
    else:
        cov = .28 if ca else .4
        if t == 'day' and not ca: cov = .38
        img = clouds(img, sd, cov, *P['cl'], 4 if not ca else 14, HZ - 16 if t != 'day' else HZ - 18, 16, 3.4)
        if not ca: img = clouds(img, sd + 5, cov * .7, *P['cl'], 26, HZ - 10, 11, 3.0)
    # 海
    img = sea(img, P['sea'][0], P['sea'][1], sd, P['wave'], 40 if ca else 80 if not st else 120, 1.0 if ca else 0, 0 if not st else .45)
    if st:
        g = img[HZ:].mean(2, keepdims=True); img[HZ:] = (img[HZ:] * .5 + g * .5) * .72
    if ca:
        img = mirror(img, .62 if t != 'night' else .55)
    if not st:
        img = reflect_col(img, cx, P['refl'], 1.2 if not ca else .6, .9 if t != 'night' else .6, sd)
        img = glow(img, cx, HZ, 30, c2, .25)
    else:
        img = rain(img, sd, 140 if t != 'night' else 110, '#b4c4da' if t != 'night' else '#6c7ca0', .4, 11)
        if t in ('night', 'dusk', 'dawn') and (sd % 2 == 0 or t == 'night'): img = bolt(img, 70 + (sd % 50), '#f4f2ff')
        if t == 'day': img = glow(img, 40, 12, 40, '#ffffff', .2)
    img = horizon(img, '#fff4d0' if t in ('dusk', 'dawn') and not st else '#cfe0f0' if not st else '#8a98ac', .5 if not st else .3)
    if ca and t != 'night': img = glow(img, cx, HZ - 1, 60, P['gl'], .12)
    img = raft(img, '#ffb060', True, {'dawn': '#241624', 'day': '#1e2230', 'dusk': '#180f20', 'night': '#06060e'}[t] if True else '')
    img = vignette(img, .3 if t == 'night' or st else .22)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

keys = [f'{t}_{w}' for t in ('dawn', 'day', 'dusk', 'night') for w in ('sunny', 'calm', 'storm')]
out = {}
for k in keys:
    im = scene(k); buf = io.BytesIO(); im.save(buf, 'PNG', optimize=True); out[k] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    im.resize((W * 4, H * 4), Image.NEAREST).save(f'/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/sc_{k}.png')
open('scenes_art.js', 'w').write('window.RAFT = window.RAFT || {}; window.RAFT.scenes = ' + json.dumps(out) + ';\n')
print('ok', len(open('scenes_art.js').read()))
