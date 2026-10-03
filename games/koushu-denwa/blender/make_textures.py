"""
公衆電話機・料金案内板・注意シールの「表面の絵（テクスチャ）」を作るスクリプト
出力先：games/koushu-denwa/assets/tex/

実物の写真（NTTのディジタル公衆電話）を見本に、操作パネルの印刷文字・ボタン・SOS表示などを絵として描く。
ひかるのパソコンでは実行しなくてよい（できあがりのPNGがリポジトリに入っている）。
直したいとき用：  python make_textures.py   （Pillow と numpy が必要。日本語フォントは IPAゴシック）
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'assets', 'tex'))
os.makedirs(OUT, exist_ok=True)
FONT = next((p for p in ['/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf', '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
                         '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'] if os.path.exists(p)), None)
rng = np.random.default_rng(1998)
# 古びの強さ（0=新品 〜 1=ぼろぼろ）。環境変数 KD_AGE でも変えられる。おすすめは 0.8（暗い画面でも見える強さ）
AGE = float(os.environ.get('KD_AGE', '0.9'))
def F(size): return ImageFont.truetype(FONT, size)

def fbm(h, w, octaves=6):
    out = np.zeros((h, w), np.float32); amp = 1.; tot = 0.
    for o in range(octaves):
        g = 2 ** (o + 2)
        small = rng.random((g + 1, g + 1)).astype(np.float32)
        im = Image.fromarray(small).resize((w, h), Image.BICUBIC)
        out += np.asarray(im) * amp; tot += amp; amp *= .5
    return out / tot

def streaks(h, w, strength=1.0):
    """上から下へ流れる汚れの筋（雨だれ）。0〜1"""
    col = np.convolve(rng.random(w).astype(np.float32), np.ones(7, np.float32) / 7, mode='same')
    col = np.clip((col - np.percentile(col, 55)) * 6.0, 0, 1)
    zz = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    length = rng.random(w).astype(np.float32)[None, :] * .8 + .2           # 筋ごとに流れる長さが違う
    prof = np.clip(1.0 - np.abs(zz - .15) / length, 0, 1) * (.4 + .6 * zz)
    return col[None, :] * prof * strength

def save(name, img):
    p = os.path.join(OUT, name); img.save(p, optimize=True); print('保存', name, img.size, os.path.getsize(p) // 1024, 'KB')

def normal_from_height(hm, strength=3.0):
    gy, gx = np.gradient(hm.astype(np.float32))
    nx, ny, nz = -gx * strength, gy * strength, np.ones_like(hm)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / l, ny / l, nz / l], -1) * .5 + .5
    return Image.fromarray((n * 255).astype(np.uint8))

def text_c(d, xy, s, font, fill, anchor='mm'):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)

# ======================================================================
# 1) 操作パネル（幅.215m×高さ.245m を 1290×1470px。6000px/m）
# ======================================================================
def make_panel():
    W, H = 1290, 1470
    S = 2                                    # 2倍で描いて縮めると文字がなめらか
    w, h = W * S, H * S
    def X(v): return int(v * S)
    base = np.zeros((h, w, 3), np.float32)
    grad = np.linspace(1.0, .82, h, dtype=np.float32)[:, None]
    base[:] = np.array([.165, .2, .18], np.float32)[None, None] * grad[..., None]
    base += (fbm(h, w, 5)[..., None] - .5) * .05
    img = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8))
    hm = Image.new('L', (w, h), 128)          # 高さの絵（あとで法線マップにする）
    d = ImageDraw.Draw(img); hd = ImageDraw.Draw(hm)
    WHITE = (222, 226, 220); GOLD = (214, 168, 60); LINE = (120, 132, 124)

    # 外枠の細い線
    d.rounded_rectangle([X(16), X(16), X(W - 16), X(H - 16)], radius=X(26), outline=LINE, width=X(3))
    hd.rounded_rectangle([X(16), X(16), X(W - 16), X(H - 16)], radius=X(26), outline=90, width=X(4))

    # ---- 液晶の窓（枠だけ。中身は別パーツ） ----
    lcd = (86, 108, 742, 352)
    d.rounded_rectangle([X(lcd[0] - 12), X(lcd[1] - 12), X(lcd[2] + 12), X(lcd[3] + 12)], radius=X(14), fill=(14, 18, 16), outline=LINE, width=X(2))
    # ---- 音量ボタン ----
    text_c(d, (X(150), X(414)), '音量／VOL', F(X(30)), WHITE)
    for cx, sym in ((430, '▼'), (540, '▲')):
        d.rounded_rectangle([X(cx - 38), X(384), X(cx + 38), X(446)], radius=X(10), fill=(30, 36, 33), outline=LINE, width=X(2))
        text_c(d, (X(cx), X(415)), sym, F(X(30)), (200, 205, 200))
    text_c(d, (X(430), X(368)), '−', F(X(34)), WHITE); text_c(d, (X(540), X(368)), '＋', F(X(30)), WHITE)
    # ---- スピーカーの溝 ----
    for y in range(492, 764, 24):
        d.rectangle([X(90), X(y), X(742), X(y + 9)], fill=(20, 25, 22)); d.rectangle([X(90), X(y + 9), X(742), X(y + 13)], fill=(70, 80, 74))
        hd.rectangle([X(90), X(y), X(742), X(y + 9)], fill=40); hd.rectangle([X(90), X(y + 13), X(742), X(y + 16)], fill=170)
    # ---- テレホンカード ----
    text_c(d, (X(98), X(816)), 'テレホンカード／TELEPHONE CARD', F(X(30)), WHITE, 'lm')
    plate = (120, 872, 590, 1330)
    grad_img = Image.new('RGB', (w, h)); gd = ImageDraw.Draw(grad_img)
    for i in range(plate[1], plate[3]):     # 金属板のグラデーション
        t = (i - plate[1]) / (plate[3] - plate[1]); c = int(176 - 40 * t)
        gd.line([X(plate[0]), X(i), X(plate[2]), X(i)], fill=(c, c + 4, c))
    pm = Image.new('L', (w, h), 0); ImageDraw.Draw(pm).rounded_rectangle([X(plate[0]), X(plate[1]), X(plate[2]), X(plate[3])], radius=X(16), fill=255)
    img.paste(grad_img, (0, 0), pm)
    d.rounded_rectangle([X(plate[0]), X(plate[1]), X(plate[2]), X(plate[3])], radius=X(16), outline=(70, 76, 72), width=X(4))
    hd.rounded_rectangle([X(plate[0]), X(plate[1]), X(plate[2]), X(plate[3])], radius=X(16), fill=190)
    d.polygon([(X(310), X(842)), (X(390), X(842)), (X(350), X(866))], fill=(150, 156, 150))      # ▽の矢印
    d.polygon([(X(612), X(1084)), (X(612), X(1132)), (X(590), X(1108))], fill=(150, 156, 150))  # ◁
    d.rounded_rectangle([X(44), X(1062), X(92), X(1116)], radius=X(6), outline=WHITE, width=X(3))  # カード挿入の絵
    d.polygon([(X(62), X(1076)), (X(84), X(1088)), (X(62), X(1100))], fill=WHITE)

    # ---- コイン投入口まわり ----
    cx, cy, r = 960, 190, 96
    d.ellipse([X(cx - r), X(cy - r), X(cx + r), X(cy + r)], fill=(176, 180, 174), outline=(60, 66, 62), width=X(4))
    d.ellipse([X(cx - r + 14), X(cy - r + 14), X(cx + r - 14), X(cy + r - 14)], fill=(150, 154, 148))
    hd.ellipse([X(cx - r), X(cy - r), X(cx + r), X(cy + r)], fill=200)
    for (bx, by, label) in ((1198, 80, '10'), (1198, 200, '100')):
        d.ellipse([X(bx - 50), X(by - 50), X(bx + 50), X(by + 50)], fill=(190, 194, 188), outline=(70, 76, 72), width=X(3))
        d.ellipse([X(bx - 38), X(by - 38), X(bx + 38), X(by + 38)], outline=(60, 66, 62), width=X(2))
        text_c(d, (X(bx), X(by)), label, F(X(38 if len(label) == 2 else 32)), (30, 34, 32))
    d.polygon([(X(800), X(160)), (X(800), X(222)), (X(768), X(191))], fill=(230, 150, 40))     # ◀（オレンジの三角）
    d.polygon([(X(800), X(288)), (X(800), X(318)), (X(782), X(303))], fill=(210, 214, 208))
    d.rounded_rectangle([X(832), X(296), X(940), X(324)], radius=X(6), outline=WHITE, width=X(2))  # 小さな表示窓
    text_c(d, (X(1030), X(376)), '100円は、おつりがでません', F(X(29)), WHITE)
    text_c(d, (X(1030), X(414)), 'No partial refunds for 100yen coins.', F(X(20)), (200, 206, 200))

    # ---- テンキー（丸ボタンの絵。実物は別パーツで立体にする） ----
    keys = [['1', '2', '3'], ['4', '5', '6'], ['7', '8', '9'], ['＊', '0', '＃']]
    kx0, kdx, ky0, kdy, kr = 898, 130, 522, 110, 50
    for ri, row in enumerate(keys):
        for ci, k in enumerate(row):
            cx, cy = kx0 + ci * kdx, ky0 + ri * kdy
            d.ellipse([X(cx - kr - 4), X(cy - kr - 4), X(cx + kr + 4), X(cy + kr + 4)], fill=(10, 12, 11))
            hd.ellipse([X(cx - kr - 8), X(cy - kr - 8), X(cx + kr + 8), X(cy + kr + 8)], fill=60)
    # ---- SOS ----
    sos = (806, 960, 1254, 1250)
    d.rounded_rectangle(sos, radius=X(10), outline=LINE, width=X(3), fill=(34, 42, 38)) if False else d.rounded_rectangle([X(v) for v in sos], radius=X(10), outline=LINE, width=X(3), fill=(34, 42, 38))
    text_c(d, (X(852), X(1000)), 'SOS', F(X(38)), WHITE)
    for i, (num, lab) in enumerate((('110', '警察'), ('118', '海上'), ('119', '消防'))):
        bx = 1000 + i * 100
        d.ellipse([X(bx - 34), X(984), X(bx + 34), X(1052)], fill=(20, 24, 22), outline=GOLD, width=X(4))
        text_c(d, (X(bx), X(1018)), num, F(X(24)), GOLD)
        text_c(d, (X(bx), X(1076)), lab, F(X(18)), WHITE)
    text_c(d, (X(1030), X(1140)), 'そのままダイヤルして下さい', F(X(24)), WHITE)
    text_c(d, (X(1030), X(1180)), 'Please dial without coin(card).', F(X(19)), (200, 206, 200))
    text_c(d, (X(1030), X(1222)), '110　118　119　は無料です', F(X(19)), (200, 206, 200))
    text_c(d, (X(660), X(1400)), 'NTT', F(X(32)), (160, 200, 230))

    # 汚れ・ひっかき傷（少しだけ）
    arr = np.asarray(img).astype(np.float32) / 255
    dirt = np.clip(fbm(h, w, 6) - .55, 0, 1) * (.15 + .55 * AGE)
    arr = arr * (1 - dirt[..., None]) + dirt[..., None] * np.array([.28, .27, .22])
    st = streaks(h, w) * AGE * .6                                   # 雨だれの筋
    arr = arr * (1 - st[..., None] * .5) + st[..., None] * .5 * np.array([.20, .18, .12])
    arr = arr * (1 - .10 * AGE) + np.array([.30, .27, .14]) * .10 * AGE   # 黄ばみ（うすいくもり）
    for _ in range(int(30 + 110 * AGE)):
        y = rng.integers(0, h); x = rng.integers(0, w); ln = rng.integers(20, 90) * S; a = rng.random() * math.pi
        for t in range(ln):
            xx, yy = int(x + math.cos(a) * t), int(y + math.sin(a) * t)
            if 0 <= xx < w and 0 <= yy < h: arr[yy, xx] = arr[yy, xx] * .8 + .2
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    hm = hm.filter(ImageFilter.GaussianBlur(S * .8)).resize((W, H), Image.LANCZOS)
    save('phone_panel_albedo.png', img)
    save('phone_panel_normal.png', normal_from_height(np.asarray(hm) / 255., 5.0))
    return dict(lcd=lcd, keys=(kx0, kdx, ky0, kdy, kr), coin=(960, 190, 96), plate=plate, W=W, H=H)

# ======================================================================
# 2) 液晶（オレンジ）
# ======================================================================
def make_lcd():
    W, H = 656, 244
    a = np.zeros((H, W, 3), np.float32)
    grad = np.linspace(1., .82, H, dtype=np.float32)[:, None]
    a[:] = np.array([1., .5, .1], np.float32)[None, None] * grad[..., None]
    a += (fbm(H, W, 4)[..., None] - .5) * .08
    img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 4): d.line([x, 0, x, H], fill=(230, 110, 20), width=1)      # 液晶のこまかい線
    d.text((W // 2, H // 2 - 6), '国際通話がご利用できます', font=F(44), fill=(70, 22, 4), anchor='mm')
    d.text((W - 16, H - 18), 'ﾃﾞｼﾞﾀﾙ', font=F(20), fill=(90, 30, 6), anchor='rm')
    d.rectangle([0, 0, W - 1, H - 1], outline=(120, 50, 10), width=4)
    arr = np.asarray(img).astype(np.float32) / 255
    arr *= (1 - .45 * AGE * fbm(H, W, 4))[..., None]                 # 色むら・焼けつき
    for x in rng.choice(W, int(3 + 10 * AGE), replace=False):        # 死んだ縦線
        arr[:, x:x + 2] *= .15
    arr[int(H * .55):, :] *= (1 - .5 * AGE)                          # 下半分がうすれる
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    save('phone_lcd.png', img)

# ======================================================================
# 3) テンキーのシート（4行×3列。1マス256px）
# ======================================================================
def make_keys():
    C = 256
    img = Image.new('RGB', (C * 3, C * 4), (12, 13, 12)); d = ImageDraw.Draw(img)
    labels = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '＊', '0', '＃']
    for i, s in enumerate(labels):
        cx, cy = (i % 3) * C + C // 2, (i // 3) * C + C // 2
        wear = AGE * (.25 + .5 * rng.random())                     # ボタンごとにすり減りが違う
        gold = tuple(int(c * (1 - wear * .5) + 70 * wear * .5) for c in (222, 178, 68))
        ring = tuple(int(c * (1 - wear * .5) + 60 * wear * .5) for c in (205, 160, 56))
        d.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], fill=(14, 15, 14), outline=ring, width=10)
        d.ellipse([cx - 96, cy - 96, cx + 96, cy + 96], fill=(22, 23, 21))
        d.text((cx, cy - 4), s, font=F(130), fill=gold, anchor='mm')
    save('phone_keys_atlas.png', img)

# ======================================================================
# 4) 電話機の緑の本体（色ムラ・汚れ・こすれ）
# ======================================================================
def make_body():
    N = 1024
    g = np.array([.05, .52, .04], np.float32)              # 明るい黄緑（リニア色）
    n = fbm(N, N, 6)
    a = g[None, None] * (.9 + .25 * n[..., None])
    zz = np.linspace(0, 1, N, dtype=np.float32)[:, None]
    dirt = np.clip(fbm(N, N, 7) - .5, 0, 1) * (.5 + .8 * zz)    # 下ほどよごれる
    a = a * (1 - dirt[..., None] * .8) + dirt[..., None] * np.array([.05, .045, .03]) * .5
    sc = np.zeros((N, N), np.float32)
    for _ in range(60):
        x = rng.integers(0, N); y = rng.integers(0, N); ln = rng.integers(15, 80); ang = rng.random() * math.pi
        for t in range(ln):
            xx, yy = int(x + math.cos(ang) * t), int(y + math.sin(ang) * t)
            if 0 <= xx < N and 0 <= yy < N: sc[yy, xx] = 1
    sc = np.asarray(Image.fromarray((sc * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.8))) / 255.
    a = a * (1 - .5 * sc[..., None]) + sc[..., None] * .18
    # ---- 古び：色あせ・雨だれの筋・上面のほこり ----
    fade = .45 * AGE
    a = a * (1 - fade) + np.array([.16, .30, .10], np.float32)[None, None] * fade
    st = streaks(N, N) * AGE * .9
    a = a * (1 - st[..., None] * .75) + st[..., None] * .75 * np.array([.07, .055, .03])
    dust = np.clip(fbm(N, N, 6) - .5, 0, 1) * 2 * AGE * (.4 + .6 * (1 - zz))
    a = a * (1 - dust[..., None] * .6) + dust[..., None] * .6 * np.array([.34, .30, .22])
    # ---- 廃墟：塗装のはがれ→さび、上のほうのこけ ----
    peel = np.clip((fbm(N, N, 7) - .54) * 5, 0, 1) * AGE
    rust = np.clip(peel * (.25 + .75 * zz) * 1.8, 0, 1)
    rcol = np.array([.20, .075, .03], np.float32)[None, None] * (.6 + .8 * fbm(N, N, 5)[..., None])
    a = a * (1 - rust[..., None]) + rust[..., None] * rcol
    moss = np.clip((fbm(N, N, 6) - .58) * 4, 0, 1) * AGE * (1 - zz) * .9
    a = a * (1 - moss[..., None] * .65) + moss[..., None] * .65 * np.array([.03, .08, .02])
    srgb = np.clip(a, 0, 1) ** (1 / 2.2)
    save('phone_body_albedo.png', Image.fromarray((srgb * 255).astype(np.uint8)))
    rough = np.clip(.26 + AGE * .20 + dirt * .5 + sc * .3 + dust * .3 + st * .2 + rust * .5 + moss * .3 + (n - .5) * .1, 0, 1)
    save('phone_body_rough.png', Image.fromarray((rough * 255).astype(np.uint8)))

# ======================================================================
# 4b) ガラスの汚れ（下ほど濃い・雨だれ・手形の拭き跡）
# ======================================================================
def make_glass():
    N = 512
    zz = np.linspace(0, 1, N, dtype=np.float32)[:, None]
    base = np.clip(fbm(N, N, 6) - .40, 0, 1) * 1.8
    m = base * (.25 + .9 * zz ** 1.5) + streaks(N, N) * .8
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    for (cx, cy, rx, ry) in ((.62, .45, .05, .08), (.66, .40, .025, .04), (.30, .55, .05, .075), (.34, .50, .025, .04)):
        e = ((xx / N - cx) / rx) ** 2 + ((yy / N - cy) / ry) ** 2
        m = m * (1 - np.clip(1.2 - e, 0, 1) * .75)                   # 手の跡は汚れが拭き取られる
    m = np.clip(m * AGE * 1.6, 0, 1)
    if AGE > .35:                                                   # ひび割れ（放射状の線）
        cr = Image.new('L', (N, N), 0); cd = ImageDraw.Draw(cr)
        for (cx, cy) in ((.72, .30), (.25, .62)):
            for k in range(7):
                ang = rng.random() * math.tau; x, y = cx * N, cy * N; pts = [(x, y)]
                for _ in range(int(8 + rng.random() * 8)):
                    ang += (rng.random() - .5) * .7; step = 14 + rng.random() * 26
                    x += math.cos(ang) * step; y += math.sin(ang) * step; pts.append((x, y))
                cd.line(pts, fill=255, width=2)
        cr = np.asarray(cr.filter(ImageFilter.GaussianBlur(.7))).astype(np.float32) / 255
        m = np.clip(np.maximum(m, cr * 1.1), 0, 1)
    save('glass_dirt.png', Image.fromarray((m * 255).astype(np.uint8)))
    save('glass_rough.png', Image.fromarray((np.clip(.04 + m * .66, 0, 1) * 255).astype(np.uint8)))
    rgb = np.stack([.80 - m * .45, .92 - m * .40, .88 - m * .55], -1)
    alpha = np.clip(.12 + m * .55, 0, 1)[..., None]
    rgba = np.concatenate([rgb, alpha], -1)
    save('glass_color.png', Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), 'RGBA'))

# ======================================================================
# 4c) ブロンズ色のアルミ枠（ブラシ目・白い腐食粉・さび）
# ======================================================================
def make_bronze():
    N = 512
    n3 = fbm(N, N, 8)
    streak = rng.random((1, N)).astype(np.float32)
    streak = (streak + np.roll(streak, 1, 1) + np.roll(streak, -1, 1)) / 3
    zz = np.linspace(0, 1, N, dtype=np.float32)[:, None]
    bronze = np.array([.115, .085, .065], np.float32)[None, None] * (.8 + .35 * streak[..., None] + .2 * (n3[..., None] - .5)) * (1 - .35 * (zz ** 2)[..., None])
    powder = np.clip((fbm(N, N, 6) - .50) * 3, 0, 1) * AGE * 1.3 * (.4 + .6 * zz)      # 白い腐食の粉
    rust = np.clip((fbm(N, N, 5) - .55) * 3.5, 0, 1) * AGE * 1.1 * (.2 + .8 * zz)               # さび
    st = streaks(N, N) * AGE * .6
    bronze = bronze * (1 - powder[..., None] * .7) + powder[..., None] * .7 * np.array([.42, .40, .36])
    bronze = bronze * (1 - rust[..., None]) + rust[..., None] * np.array([.22, .085, .03])
    bronze = bronze * (1 - st[..., None] * .4)
    save('bronze_color.png', Image.fromarray((np.clip(bronze, 0, 1) * 255).astype(np.uint8)))
    rough = np.clip(.32 + .25 * streak + .3 * zz ** 2 + powder * .5 + rust * .5, 0, 1)
    save('bronze_rough.png', Image.fromarray((np.clip(rough, 0, 1) * 255).astype(np.uint8)))

# ======================================================================
# 4d) 灰色の塗装（柱・台・台座）：はがれ・さびの染み出し
# ======================================================================
def make_gray():
    N = 512
    zz = np.linspace(0, 1, N, dtype=np.float32)[:, None]
    base = np.array([.55, .56, .57], np.float32)[None, None] * (.85 + .3 * fbm(N, N, 6)[..., None])
    peel = np.clip((fbm(N, N, 7) - .52) * 5, 0, 1) * AGE
    st = streaks(N, N) * AGE
    rustc = np.array([.45, .22, .10], np.float32)[None, None] * (.6 + .7 * fbm(N, N, 5)[..., None])
    rm = np.clip(peel * (.3 + .7 * zz) * 1.6 + st * .7, 0, 1)
    col = base * (1 - rm[..., None]) + rm[..., None] * rustc
    grime = np.clip((fbm(N, N, 6) - .45) * 2, 0, 1) * AGE * (.3 + .7 * zz)
    col = col * (1 - grime[..., None] * .55)
    save('gray_paint_color.png', Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)))
    save('gray_paint_rough.png', Image.fromarray((np.clip(.55 + rm * .3 + grime * .2, 0, 1) * 255).astype(np.uint8)))

# ======================================================================
# 4e) 天井（水のしみ・カビ）と床（よごれたコンクリート・落ち葉・ひび）
# ======================================================================
def make_ceiling():
    N = 512
    col = np.array([.82, .82, .77], np.float32)[None, None] * (.9 + .15 * fbm(N, N, 5)[..., None])
    stain = np.clip((fbm(N, N, 5) - .50) * 4, 0, 1) * AGE
    col = col * (1 - stain[..., None] * .7) + stain[..., None] * .7 * np.array([.42, .30, .15])     # 茶色い水のしみ
    mold = np.clip((fbm(N, N, 8) - .6) * 5, 0, 1) * AGE
    col = col * (1 - mold[..., None] * .8) + mold[..., None] * .8 * np.array([.06, .07, .05])         # 黒カビ
    save('ceiling_color.png', Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)))

def make_floor():
    N = 512
    col = np.array([.42, .42, .40], np.float32)[None, None] * (.8 + .4 * fbm(N, N, 6)[..., None])
    dirt = np.clip((fbm(N, N, 6) - .45) * 2.5, 0, 1) * AGE
    col = col * (1 - dirt[..., None] * .6) + dirt[..., None] * .6 * np.array([.14, .11, .07])           # 泥
    moss = np.clip((fbm(N, N, 7) - .6) * 5, 0, 1) * AGE
    col = col * (1 - moss[..., None] * .7) + moss[..., None] * .7 * np.array([.05, .12, .03])
    im = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for _ in range(int(120 * AGE)):                                                                     # 落ち葉
        x, y = rng.integers(0, N), rng.integers(0, N); r = 3 + rng.random() * 7
        c = (int(70 + rng.random() * 70), int(40 + rng.random() * 40), int(15 + rng.random() * 20))
        d.ellipse([x - r, y - r * .5, x + r, y + r * .5], fill=c)
    for _ in range(3):                                                                                   # ひび
        x, y = rng.random() * N, rng.random() * N; ang = rng.random() * math.tau; pts = [(x, y)]
        for _ in range(14):
            ang += (rng.random() - .5) * .8; x += math.cos(ang) * 22; y += math.sin(ang) * 22; pts.append((x, y))
        d.line(pts, fill=(18, 18, 16), width=2)
    save('floor_color.png', im)
    save('floor_rough.png', Image.fromarray((np.clip(.75 + dirt * .2, 0, 1) * 255).astype(np.uint8)))

# ======================================================================
# 5) 注意シール（「注意」＋3つの禁止マーク）
# ======================================================================
def make_caution():
    W, H = 512, 768
    img = Image.new('RGB', (W, H), (246, 244, 238)); d = ImageDraw.Draw(img)
    d.rectangle([4, 4, W - 5, H - 5], outline=(196, 32, 36), width=10)
    d.rectangle([4, 4, W - 5, 96], fill=(196, 32, 36))
    d.text((W // 2, 52), '注　意', font=F(64), fill=(255, 255, 255), anchor='mm')
    rows = [('電話機の上に座ったり', '乗ったりしないでください'), ('電話ボックス内では', '飲食・喫煙は禁止です'), ('故障・いたずらを見つけたら', 'ご連絡をお願いします')]
    for i, (l1, l2) in enumerate(rows):
        y0 = 120 + i * 210
        d.rectangle([24, y0, 188, y0 + 180], outline=(196, 32, 36), width=4)
        cx, cy = 106, y0 + 90
        d.polygon([(cx, cy - 66), (cx + 66, cy), (cx, cy + 66), (cx - 66, cy)], fill=(196, 32, 36))
        d.ellipse([cx - 42, cy - 42, cx + 42, cy + 42], fill=(250, 250, 250))
        if i == 0: d.rectangle([cx - 26, cy + 4, cx + 26, cy + 22], fill=(20, 20, 20)); d.ellipse([cx - 12, cy - 30, cx + 12, cy - 6], fill=(20, 20, 20))
        if i == 1: d.rectangle([cx - 30, cy - 4, cx + 30, cy + 8], fill=(20, 20, 20)); d.rectangle([cx + 30, cy - 4, cx + 36, cy + 8], fill=(230, 100, 30))
        if i == 2: d.polygon([(cx - 30, cy + 26), (cx, cy - 30), (cx + 30, cy + 26)], fill=(20, 20, 20))
        d.line([cx - 38, cy + 38, cx + 38, cy - 38], fill=(196, 32, 36), width=9)
        d.text((204, y0 + 60), l1, font=F(25), fill=(20, 20, 20), anchor='lm'); d.text((204, y0 + 100), l2, font=F(25), fill=(20, 20, 20), anchor='lm')
    arr = np.asarray(img).astype(np.float32) / 255
    arr *= (.85 + .2 * fbm(H, W, 5)[..., None])
    arr = arr * (1 - .35 * AGE) + np.array([.55, .52, .45]) * .35 * AGE      # 色あせ・黄ばみ
    arr *= (1 - .5 * AGE * np.clip(fbm(H, W, 6) - .5, 0, 1) * 2)[..., None]   # しみ
    save('caution_sticker.png', Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)))

# ======================================================================
# 6) 青い料金案内板
# ======================================================================
def make_info():
    W, H = 1024, 640
    img = Image.new('RGB', (W, H), (24, 74, 156)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 86], fill=(12, 48, 116)); d.text((W // 2, 44), '公衆電話のご利用方法・料金', font=F(46), fill=(255, 255, 255), anchor='mm')
    d.rectangle([0, 86, W, 94], fill=(240, 200, 30))
    rows = [('市内通話', '3分 10円'), ('市外（同一県内）', '1分 10円〜'), ('携帯電話あて', '約30秒 10円'), ('国際通話', 'KDDI・NTTコム等'), ('緊急通報', '110・118・119は無料')]
    for i, (a, b) in enumerate(rows):
        y = 118 + i * 96
        d.rectangle([28, y, W - 28, y + 82], fill=(238, 242, 248))
        d.line([440, y, 440, y + 82], fill=(24, 74, 156), width=4)
        d.text((60, y + 41), a, font=F(38), fill=(12, 48, 116), anchor='lm'); d.text((470, y + 41), b, font=F(38), fill=(12, 48, 116), anchor='lm')
    d.text((W // 2, H - 26), '10円・100円硬貨とテレホンカードがご利用いただけます', font=F(26), fill=(230, 238, 250), anchor='mm')
    arr = np.asarray(img).astype(np.float32) / 255; arr *= (.9 + .15 * fbm(H, W, 5)[..., None])
    arr = arr * (1 - .30 * AGE) + np.array([.50, .52, .48]) * .30 * AGE      # 色あせ
    arr *= (1 - .6 * AGE * np.clip(fbm(H, W, 6) - .5, 0, 1) * 2)[..., None]   # しみ・汚れ
    save('info_panel.png', Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)))

if __name__ == '__main__':
    info = make_panel(); make_lcd(); make_keys(); make_body(); make_glass(); make_bronze(); make_gray(); make_ceiling(); make_floor(); make_caution(); make_info()
    import json
    json.dump({k: (list(v) if isinstance(v, tuple) else v) for k, v in info.items()}, open(os.path.join(OUT, 'panel_layout.json'), 'w'))
    print('完了')
