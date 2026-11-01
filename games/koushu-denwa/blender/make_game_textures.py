"""
ゲーム用の紙もの・看板・液晶の画像を作る（Pillow + numpy。Blender不要）

作るもの（assets/tex/game/）：
  poster_01〜12 … ガラスに貼られる怖い張り紙     poster_hint … 「あの日をおして（4けた）」
  tree_poster … 木の張り紙（金庫ダイヤルの番号）  book_news … 本に挟まった古い新聞
  bulletin_news … 掲示板の新聞切り抜き            gym_card … ジムの会員カード（ドアぶっ壊しのヒント）
  memo_hatch … 電話機の下のふたの中のメモ         phonebook … 電話帳のページ
  missing_news … バッドエンド用の新聞             sign_entrance … 入口の看板
  lcd_board_idle / lcd_board_1〜3 … 警察・消防の欄の液晶
  glass_glow_0〜9 … 暗い間だけ光る数字（謎7）   glass_hint_c1〜3 … 謎7のヒントの文字
  glass_hand_1〜4 … ガラスに張りついた幽霊の手形・指の筋（python make_game_textures.py hands）
使い方：python make_game_textures.py     （謎7の数字とヒントだけなら: python make_game_textures.py glow）
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import make_textures as M

F, fbm = M.F, M.fbm
OUT = os.path.join(M.OUT, 'game')
os.makedirs(OUT, exist_ok=True)
R = np.random.default_rng(714)
AGE = M.AGE


def save(name, img):
    p = os.path.join(OUT, name)
    img.convert('RGB').save(p, optimize=True)
    print('保存', 'game/' + name, img.size, os.path.getsize(p) // 1024, 'KB')


def paper(w, h, base=(232, 224, 198), stains=1.0):
    """古い紙：色むら・しみ・ふちの焼け・折り目"""
    n = fbm(h, w, 6)
    arr = np.ones((h, w, 3), np.float32) * (np.array(base, np.float32) / 255)
    arr *= (0.86 + 0.22 * n)[..., None]
    st = np.clip(fbm(h, w, 5) - 0.52, 0, 1) * 2.2 * stains * AGE
    arr *= (1 - 0.55 * st)[..., None] * np.array([1.0, 0.93, 0.80])
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy]) / (0.08 * min(w, h))
    arr *= (0.55 + 0.45 * np.clip(edge, 0, 1))[..., None] ** (0.6 + 0.4 * AGE)
    if AGE > 0.3:
        for fx in (0.5,):
            x = int(w * fx)
            arr[:, max(0, x - 2):x + 2] *= 0.88
        y = int(h * 0.5)
        arr[max(0, y - 2):y + 2, :] *= 0.9
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))


def tape(img, x, y, ang=0, w=90, h=34):
    layer = Image.new('RGBA', (w, h), (222, 218, 190, 190))
    layer = layer.rotate(ang, expand=True)
    img.paste(layer, (int(x), int(y)), layer)


def vertical(d, x, y, s, font, fill, gap=4):
    for ch in s:
        d.text((x, y), ch, font=font, fill=fill, anchor='mt')
        y += font.size + gap
    return y


def finish(img, blur=0.6):
    return img.filter(ImageFilter.GaussianBlur(blur))


def poster(idx, text, kind='text'):
    W, H = 512, 704
    img = paper(W, H, [(232, 224, 198), (214, 204, 168), (238, 238, 228), (201, 191, 156)][idx % 4])
    d = ImageDraw.Draw(img)
    red = (122, 12, 12) if idx % 10 < 7 else (20, 20, 20)
    if kind == 'eyes':
        for _ in range(26):
            x, y, s = R.integers(30, W - 30), R.integers(30, H - 30), R.integers(14, 36)
            d.ellipse([x - s, y - s * .55, x + s, y + s * .55], fill=(8, 8, 8))
            d.ellipse([x - s * .28, y - s * .28, x + s * .28, y + s * .28], fill=(232, 224, 198))
    elif kind == 'missing':
        d.text((W // 2, 70), '探しています', font=F(62), fill=(17, 17, 17), anchor='mm')
        d.rectangle([150, 130, 362, 380], fill=(60, 60, 60))
        d.ellipse([196, 160, 316, 320], fill=(176, 176, 176))
        d.text((W // 2, 450), '1998年7月14日', font=F(40), fill=(17, 17, 17), anchor='mm')
        d.text((W // 2, 520), 'この電話から', font=F(40), fill=(17, 17, 17), anchor='mm')
        d.text((W // 2, 580), '帰ってきません', font=F(40), fill=(17, 17, 17), anchor='mm')
    else:
        lines = text.split('\n')
        size = 120 if len(lines) == 1 else 96
        f = F(size)
        for li, ln in enumerate(lines):
            cx = W // 2 + (len(lines) - 1) * (size // 2 + 6) - li * (size + 18)
            vertical(d, cx + int(R.integers(-6, 7)), 70 + int(R.integers(-10, 10)), ln.replace(' ', ''), f, red)
    tape(img, 20, -6, 4)
    tape(img, W - 110, -6, -5)
    return finish(img)


POSTER_TEXTS = ['かえして', 'みてる', 'でられない', 'うしろ', 'たすけて', 'あけて', 'まってた', 'ずっと\nここに', 'なんで\nきたの', 'みぃつけた', 'いっしょに', 'こっちを\nみて']


def _glass_font(size):
    """ガラスの文字のフォント。assets/fonts/ に好きなフォント（.ttf/.otf）を入れると、それを使う（名前に glass が入っていれば優先）"""
    fd = os.path.join(os.path.dirname(M.OUT), 'fonts')
    cands = []
    if os.path.isdir(fd):
        cands = sorted(f for f in os.listdir(fd) if f.lower().endswith(('.ttf', '.otf')))
        cands.sort(key=lambda f: 0 if 'glass' in f.lower() else 1)
    from PIL import ImageFont
    if cands:
        return ImageFont.truetype(os.path.join(fd, cands[0]), size), True
    return F(size), False


def _noise(h, w, cell, amp):
    """なめらかなノイズ（-amp〜amp）"""
    gh, gw = max(2, h // cell + 2), max(2, w // cell + 2)
    g = (R.random((gh, gw)) * 2 - 1).astype(np.float32)
    im = Image.fromarray(((g * 0.5 + 0.5) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return (np.asarray(im, np.float32) / 255.0 * 2 - 1) * amp


def _layer(text, size, angle, W, H, f, cx, cy):
    """1つの言葉を、たて書きで、中心 (cx,cy) のまわりに、角度 angle で書いた L 画像（0〜255）"""
    lines = text.split('\n')
    n_max = max(len(l.replace(' ', '')) for l in lines)
    wid = int(len(lines) * (size + 20) + size)
    hei = int(n_max * (size + 8) + size)
    can = Image.new('L', (wid, hei), 0)
    for li, ln in enumerate(lines):
        x = wid // 2 + (len(lines) - 1) * (size // 2 + 10) - li * (size + 20)
        y = size // 2 + int(R.integers(-8, 9))
        for ch in ln.replace(' ', ''):
            cell = Image.new('L', (size * 2, size * 2), 0)
            ImageDraw.Draw(cell).text((size, size), ch, font=f, fill=255, anchor='mm')
            cell = cell.rotate(float(R.uniform(-9, 9)), resample=Image.BICUBIC)
            k = float(R.uniform(0.9, 1.1))
            cell = cell.resize((int(cell.width * k), int(cell.height * k)), Image.BICUBIC)
            can.paste(255, (int(x + R.integers(-7, 8) - cell.width // 2), int(y - cell.height // 2 + size // 2)), cell)
            y += size + 6 + int(R.integers(-6, 7))
    can = can.rotate(angle, resample=Image.BICUBIC, expand=True)
    out = Image.new('L', (W, H), 0)
    out.paste(can, (int(cx - can.width // 2), int(cy - can.height // 2)), can)
    return np.asarray(out, np.float32) / 255.0


def _glass_finish(m, custom, amp=4.0, drips=7):
    """文字のマスク m（0〜1）に、手書きのゆがみ・太さのむら・かすれ・垂れ・光を付けて、透明な背景の画像にする"""
    H, W = m.shape
    dx, dy = _noise(H, W, 60, amp), _noise(H, W, 60, amp)
    yy, xx_ = np.mgrid[0:H, 0:W]
    sx = np.clip((xx_ + dx).astype(int), 0, W - 1)
    sy = np.clip((yy + dy).astype(int), 0, H - 1)
    m = m[sy, sx]
    mi_ = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))          # 線を少し太く（細い筆でも、ガラスで見えるように）
    mb = np.asarray(mi_.filter(ImageFilter.GaussianBlur(2.0)), np.float32) / 255.0
    rough = mb + _noise(H, W, 5, 0.22) * (1 - np.abs(mb * 2 - 1)) + _noise(H, W, 90, 0.12)
    m = np.clip((rough - 0.28) * 4.0, 0, 1)
    mi = (m > 0.5)
    below = mi[:-1] & ~mi[1:]
    ys, xs = np.nonzero(below)
    if len(ys) and drips > 0:
        for j in R.choice(len(ys), size=min(len(ys), drips), replace=False):
            y0, x0 = ys[j], xs[j]
            ln = int(R.integers(22, 78))
            w = int(R.integers(1, 3))
            for t in range(ln):
                a_ = 1.0 - t / ln
                yy0 = y0 + t
                if yy0 >= H:
                    break
                m[yy0, max(0, x0 - w):x0 + w + 1] = np.maximum(m[yy0, max(0, x0 - w):x0 + w + 1], a_ ** 0.6)
    soft = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9)), np.float32) / 255.0
    glow = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(13)), np.float32) / 255.0
    rgb = np.zeros((H, W, 3), np.float32)
    rgb[...] = np.array([150, 20, 20], np.float32)
    rgb = rgb * (1 - soft[..., None]) + np.array([240, 232, 226], np.float32) * soft[..., None]
    alpha = np.clip(soft * 0.92 + glow * 0.55, 0, 1)
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = rgb.clip(0, 255).astype(np.uint8)
    img[..., 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


def glass_text(idx, text):
    """ガラスに浮かぶ文字だけ（紙なし・透明な背景）。ほかの言葉と交差して、板いっぱいに、ぐちゃぐちゃに散らばって重なる（なぐり書き）"""
    W, H = 512, 704
    lines = text.split('\n')
    size = 130 if len(lines) == 1 else 104
    size = min(size, (704 - 150) // max(len(l.replace(' ', '')) for l in lines) - 6)       # 下にはみ出さない
    f, custom = _glass_font(size)
    m = np.zeros((H, W), np.float32)
    # ほかの言葉を、板いっぱいに散らす：板を 3列×5行 に分け、そのうちのいくつかの区画の中に、ばらばらの大きさ・角度で置く
    others = [t for j, t in enumerate(POSTER_TEXTS) if j != idx]
    cells = [(c, r) for c in range(3) for r in range(5)]
    R.shuffle(cells)
    for (c, r) in cells[:int(R.integers(9, 12))]:
        t = others[int(R.integers(0, len(others)))]
        sz = int(R.integers(58, 120))
        fo, _c = _glass_font(sz)
        cx = int((c + 0.5) * W / 3 + R.integers(-45, 46))
        cy = int((r + 0.5) * H / 5 + R.integers(-50, 51))
        cx, cy = max(40, min(W - 40, cx)), max(70, min(H - 70, cy))
        ang = float(R.uniform(-60, 60)) if R.random() < 0.7 else float(R.choice([90, -90, 180]))
        lay = _layer(t, sz, ang, W, H, fo, cx, cy) * float(R.uniform(0.5, 0.9))
        m = np.maximum(m, lay)
    # 主役の言葉：板のどこかに、いちばん濃く（読める）
    main = _layer(text, size, float(R.uniform(-8, 8)), W, H, f, W // 2 + int(R.integers(-90, 91)), H // 2 + int(R.integers(-110, 111)))
    m = np.maximum(m, main)
    return _glass_finish(m, custom)


def glass_hint():
    """電話機の上の、手がかり（「あの日をおして（4けた）」）。ここだけは、ぐちゃぐちゃにせず、読める。ガラスに浮かぶ文字"""
    W, H = 512, 704
    f, custom = _glass_font(104)
    m = np.zeros((H, W), np.float32)
    m = np.maximum(m, _layer('あの日を', 104, 0.0, W, H, f, W // 2 + 85, 250))
    m = np.maximum(m, _layer('おして', 104, 0.0, W, H, f, W // 2 - 85, 290))
    small, _c = _glass_font(52)
    t = Image.new('L', (W, H), 0)
    ImageDraw.Draw(t).text((W // 2, 590), '（4けた）', font=small, fill=255, anchor='mm')
    m = np.maximum(m, np.asarray(t, np.float32) / 255.0)
    return _glass_finish(m, custom, amp=2.0, drips=3)


def make_glass_texts():
    for i, t in enumerate(POSTER_TEXTS):
        im = glass_text(i, t)
        p = os.path.join(OUT, 'glass_%02d.png' % (i + 1))
        im.save(p, optimize=True)
        print('保存', 'game/glass_%02d.png' % (i + 1), im.size, os.path.getsize(p) // 1024, 'KB')
    im = glass_hint()
    p = os.path.join(OUT, 'glass_hint.png')
    im.save(p, optimize=True)
    print('保存', 'game/glass_hint.png', im.size, os.path.getsize(p) // 1024, 'KB')


CODE_HINT_TEXTS = ['そとの\nきを みて', 'ひかった\nじゅんに', 'もういちど\n0714']       # 謎7のヒント（電話機の上の文字が90秒ごとに変わる。数字は外の木に光る）


def glass_glow_digit(d):
    """暗い間だけ光る数字（蛍光の黄緑）。透明な背景・高さ約6割・外側に大きくぼかした光。_glass_finish は使わず専用に"""
    W, H = 512, 704
    f, _c = _glass_font(400)
    can = Image.new('L', (W, H), 0)
    if d == 1:                                                # 「1」は「7」と見まちがえないよう、専用に描く：たて棒＋足の横棒＋短くて斜めの旗（上の横棒はなし）
        dr = ImageDraw.Draw(can)
        cx, top, bot, sw = W // 2, 110, 594, 66
        dr.rectangle([cx - sw // 2, top, cx + sw // 2, bot], fill=255)                          # たて棒
        dr.polygon([(cx - sw // 2, top + 10), (cx + sw // 2, top), (cx + sw // 2, top + 70), (cx - 130, top + 190), (cx - 160, top + 140)], fill=255)   # 短い旗（左下に斜め）
        dr.rectangle([cx - 135, bot - 48, cx + 135, bot], fill=255)                             # 足（台）
    else:
        ImageDraw.Draw(can).text((W // 2, H // 2), str(d), font=f, fill=255, anchor='mm')
    bb = can.getbbox()
    target = int(H * 0.60)                                    # 高さ約60%に合わせる（フォントごとの差を吸収）
    if bb and (bb[3] - bb[1]) > 0:
        k = target / float(bb[3] - bb[1])
        crop = can.crop(bb)
        crop = crop.resize((max(1, int(crop.width * k)), target), Image.BICUBIC)
        can = Image.new('L', (W, H), 0)
        can.paste(crop, ((W - crop.width) // 2, (H - crop.height) // 2))
    m = np.asarray(can, np.float32) / 255.0
    dx, dy = _noise(H, W, 70, 3.0), _noise(H, W, 70, 3.0)         # 少しゆがませる
    yy, xx_ = np.mgrid[0:H, 0:W]
    m = m[np.clip((yy + dy).astype(int), 0, H - 1), np.clip((xx_ + dx).astype(int), 0, W - 1)]
    soft = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255.0
    glow = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)), np.float32) / 255.0
    col = np.array([190, 255, 140], np.float32)
    core = np.array([215, 255, 160], np.float32)                  # 文字の芯は少し白く
    rgb = col[None, None, :] * (1 - soft[..., None]) + core[None, None, :] * soft[..., None]
    alpha = np.clip(soft * 0.95 + glow * 0.7, 0, 1)
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = rgb.clip(0, 255).astype(np.uint8)
    img[..., 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


def make_glow_digits():
    for d in range(10):
        im = glass_glow_digit(d)
        p = os.path.join(OUT, 'glass_glow_%d.png' % d)
        im.save(p, optimize=True)
        print('保存', 'game/glass_glow_%d.png' % d, im.size, os.path.getsize(p) // 1024, 'KB')


def code_hint(text):
    """謎7のヒントの文字（glass_hint() と同じ、たて書き2列・読める）"""
    W, H = 512, 704
    f, custom = _glass_font(104)
    a, b = text.split('\n')
    m = np.zeros((H, W), np.float32)
    m = np.maximum(m, _layer(a, 104, 0.0, W, H, f, W // 2 + 85, 330))
    m = np.maximum(m, _layer(b, 104, 0.0, W, H, f, W // 2 - 85, 370))
    return _glass_finish(m, custom, amp=2.0, drips=3)


def make_code_hints():
    for i, t in enumerate(CODE_HINT_TEXTS):
        im = code_hint(t)
        p = os.path.join(OUT, 'glass_hint_c%d.png' % (i + 1))
        im.save(p, optimize=True)
        print('保存', 'game/glass_hint_c%d.png' % (i + 1), im.size, os.path.getsize(p) // 1024, 'KB')


def make_posters():
    for i, t in enumerate(POSTER_TEXTS):
        kind = 'eyes' if i == 1 else ('missing' if i == 6 else 'text')
        save('poster_%02d.png' % (i + 1), poster(i, t, kind))
    img = paper(512, 704, (238, 230, 204))
    d = ImageDraw.Draw(img)
    f = F(84)
    vertical(d, 340, 70, 'あの日を', f, (122, 12, 12))
    vertical(d, 180, 150, 'おして', f, (122, 12, 12))
    d.text((256, 650), '（4けた）', font=F(40), fill=(34, 34, 34), anchor='mm')
    tape(img, 20, -6, 4); tape(img, 400, -6, -5)
    save('poster_hint.png', finish(img))


def make_tree_poster():
    img = paper(640, 448, (226, 216, 186))
    d = ImageDraw.Draw(img)
    d.text((320, 70), 'わすれるな', font=F(64), fill=(122, 12, 12), anchor='mm')
    for i, (arrow, n) in enumerate([('←', '3'), ('→', '7'), ('←', '1')]):
        x = 130 + i * 190
        d.text((x, 200), arrow, font=F(90), fill=(40, 20, 20), anchor='mm')
        d.text((x, 310), n, font=F(120), fill=(122, 12, 12), anchor='mm')
    d.text((320, 410), 'ここで まわせ', font=F(32), fill=(60, 40, 40), anchor='mm')
    tape(img, 10, 4, -6); tape(img, 530, 6, 7)
    save('tree_poster.png', finish(img))


def newspaper(w, h, head, date, body, caption=None, redact=None):
    img = paper(w, h, (214, 204, 172), stains=1.2)
    d = ImageDraw.Draw(img)
    d.text((w // 2, 56), '北  峰  新  聞', font=F(60), fill=(30, 30, 30), anchor='mm')
    d.line([30, 100, w - 30, 100], fill=(30, 30, 30), width=3)
    d.text((w - 40, 122), date, font=F(26), fill=(40, 40, 40), anchor='rm')
    y = 160
    for ln in head:
        d.text((40, y), ln, font=F(54), fill=(15, 15, 15), anchor='lt')
        y += 66
    y += 16
    d.line([40, y, w - 40, y], fill=(60, 60, 60), width=2)
    y += 20
    for ln in body:
        d.text((40, y), ln, font=F(30), fill=(40, 40, 40), anchor='lt')
        y += 42
    if redact:
        for (x0, y0, x1, y1) in redact:
            d.rectangle([x0, y0, x1, y1], fill=(12, 12, 12))
    return img


def make_newspapers():
    img = newspaper(
        800, 1000,
        ['公衆電話ボックスで', '女子学生が行方不明'], '1998年（平成10年）7月15日',
        ['14日夜、北峰林道そばの公衆電話ボックスで、',
         '市内の女子学生（19）が行方不明になった。',
         '友人によると、学生は「電話をかけてくる」と',
         'ボックスに入ったまま戻らなかった。',
         '',
         '警察が捜索したが、ボックスの扉は内側から',
         '開かない状態だったという。',
         '',
         '電話機の受話器は外れたままで、',
         '通話記録には ████ への発信が残っていた。',
         '', '', '※この電話に、もう誰もかけてはいけない。'])
    save('book_news.png', finish(img, 0.5))
    img = newspaper(
        640, 520, ['またあの電話で…'], '2005年8月',
        ['北峰林道の公衆電話で', '行方不明の相談が相次いでいる。', '町は撤去を検討中。'])
    save('bulletin_news.png', finish(img, 0.5))
    img = newspaper(
        800, 700, ['大学生が行方不明', '心霊スポットに向かう'], '本日付',
        ['○○大学の男子学生（21）が3日夜から',
         '連絡が取れなくなっている。',
         '', '学生は筋トレと心霊スポット巡りが趣味で、',
         '友人に「森の公衆電話に行く」と話していた。',
         '現場の電話ボックスの扉は閉まったままだった。'])
    save('missing_news.png', finish(img, 0.5))


def make_gym_card():
    W, H = 856, 540
    img = Image.new('RGB', (W, H), (24, 24, 28))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 110], fill=(190, 20, 20))
    d.text((40, 56), '鉄人ジム  会員証', font=F(54), fill=(250, 250, 250), anchor='lm')
    d.text((W - 40, 56), 'MEMBER', font=F(40), fill=(250, 220, 220), anchor='rm')
    d.text((50, 190), '会員名：', font=F(40), fill=(220, 220, 220), anchor='lm')
    d.text((50, 270), '俺最強2929', font=F(100), fill=(255, 215, 60), anchor='lm')
    d.text((50, 380), '会員No. 0029-2929', font=F(34), fill=(190, 190, 190), anchor='lm')
    d.text((50, 440), 'プロテイン割引  ★ 肉の日（29日）はポイント2倍！', font=F(30), fill=(190, 190, 190), anchor='lm')
    d.rectangle([W - 210, 150, W - 50, 330], outline=(120, 120, 120), width=3)
    d.text((W - 130, 240), '写真', font=F(34), fill=(120, 120, 120), anchor='mm')
    arr = np.asarray(img).astype(np.float32) / 255
    arr *= (0.8 + 0.3 * fbm(H, W, 6))[..., None] * (1 - 0.2 * AGE)
    save('gym_card.png', Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)))


def make_memo():
    img = paper(560, 420, (236, 232, 214))
    d = ImageDraw.Draw(img)
    d.text((40, 60), 'この番号に', font=F(48), fill=(30, 30, 90), anchor='lm')
    d.text((40, 150), 'かけて', font=F(48), fill=(30, 30, 90), anchor='lm')
    d.text((300, 270), '0 1 1 5', font=F(110), fill=(122, 12, 12), anchor='mm')
    d.text((40, 370), '（十円をわすれずに）', font=F(30), fill=(60, 60, 60), anchor='lm')
    save('memo_hatch.png', finish(img))


def make_phonebook():
    img = paper(720, 960, (226, 220, 196))
    d = ImageDraw.Draw(img)
    d.text((360, 60), '電話帳  よく使う番号', font=F(50), fill=(30, 30, 30), anchor='mm')
    rows = [('117', '時報'), ('177', '天気予報'), ('104', '番号案内'), ('110', '警察'), ('119', '消防・救急'),
            ('0115', '（書きなぐった跡）'), ('自宅', '（かすれて読めない）')]
    for i, (n, name) in enumerate(rows):
        y = 150 + i * 100
        d.line([40, y + 70, 680, y + 70], fill=(80, 80, 80), width=2)
        d.text((60, y + 35), n, font=F(52), fill=(20, 20, 20), anchor='lm')
        d.text((300, y + 35), name, font=F(40), fill=(40, 40, 40), anchor='lm')
    save('phonebook.png', finish(img))


def make_sign():
    W, H = 1024, 640
    arr = np.ones((H, W, 3), np.float32) * np.array([0.30, 0.20, 0.12])
    arr *= (0.7 + 0.5 * fbm(H, W, 6))[..., None]
    streak = fbm(H, W // 8, 5)
    streak = np.asarray(Image.fromarray((streak * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
    arr *= (0.8 + 0.4 * streak)[..., None]
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.text((W // 2, 130), '北峰林道', font=F(120), fill=(225, 215, 190), anchor='mm')
    d.text((W // 2, 300), '→ 公衆電話  300m', font=F(80), fill=(225, 215, 190), anchor='mm')
    d.text((W // 2, 450), '※ 夜間の立入りは ご遠慮ください', font=F(48), fill=(200, 60, 50), anchor='mm')
    d.text((W // 2, 540), '北峰町', font=F(36), fill=(180, 170, 150), anchor='mm')
    save('sign_entrance.png', finish(img, 0.8))


def lcd(text, name, sub=None, bad=False):
    W, H = 512, 256
    base = np.array([0.62, 0.74, 0.55]) if not bad else np.array([0.55, 0.62, 0.50])
    arr = np.ones((H, W, 3), np.float32) * base
    arr *= (0.85 + 0.2 * fbm(H, W, 5))[..., None]
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    ink = (20, 36, 20)
    if sub:
        d.text((W // 2, 60), sub, font=F(34), fill=ink, anchor='mm')
    d.text((W // 2, 140 if sub else 128), text, font=F(78 if len(text) < 6 else 56), fill=ink, anchor='mm')
    for y in range(0, H, 4):
        d.line([0, y, W, y], fill=(0, 20, 0), width=1)
    save(name, img)


def make_lcds():
    lcd('警察  110', 'lcd_board_idle.png', sub='緊急通報')
    lcd('消防  119', 'lcd_board_idle2.png', sub='緊急通報')
    lcd('でられない', 'lcd_board_1.png', bad=True)
    lcd('うしろ', 'lcd_board_2.png', bad=True)
    lcd('みてる', 'lcd_board_3.png', bad=True)


# ---------------- ガラスの手形（glass_hand_1〜4）：幽霊がガラスに張りついた跡 ----------------
HW, HH = 512, 640
HAND_ALPHA_MAX = 0.55                                         # 手形ぜんたいの透け具合の上限（材質が光らせても、うっすらにする）


def _hand_noise(rg, h, w, cell, amp):
    """手形用のなめらかなノイズ（-amp〜amp）。共有乱数 R を使わない（ほかの画像を変えないため）"""
    gh, gw = max(2, h // cell + 2), max(2, w // cell + 2)
    g = (rg.random((gh, gw)) * 2 - 1).astype(np.float32)
    im = Image.fromarray(((g * 0.5 + 0.5) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return (np.asarray(im, np.float32) / 255.0 * 2 - 1) * amp


def _hand_mask(rg, spread=1.0, close=False, mirror=False, scale=1.0, angle=0.0):
    """手のひら＋指5本（親指つき）の強さ 0〜1（HH x HW）。指先と関節の腹が強く、手のひらの中ほど（くぼみ）は弱い"""
    S = 2
    can = Image.new('L', (HW * S, HH * S), 0)
    d = ImageDraw.Draw(can)
    cx, py0, py1 = HW // 2, 285, 480                           # 手のひらの上・下
    pw = 88
    d.rounded_rectangle([(cx - pw) * S, py0 * S, (cx + pw) * S, py1 * S], radius=60 * S, fill=150)
    d.rectangle([(cx - 62) * S, (py1 - 20) * S, (cx + 62) * S, (HH + 10) * S], fill=110)           # 手首（下に消える）
    fingers = [(-64, 150, -9, 38), (-22, 172, -3, 41), (21, 160, 3, 39), (60, 124, 10, 33)]
    k = 0.45 if close else 1.0
    for ox, ln, ang, w in fingers:
        a = math.radians(ang * spread * k)
        bx, by = cx + ox, py0 + 22
        ln = ln * (0.97 + 0.06 * rg.random())
        tx, ty = bx + ln * math.sin(a), by - ln * math.cos(a)
        d.line([bx * S, by * S, tx * S, ty * S], fill=165, width=int(w * S))
        for (px, py) in ((bx, by), (tx, ty)):
            d.ellipse([(px - w / 2) * S, (py - w / 2) * S, (px + w / 2) * S, (py + w / 2) * S], fill=165)
        for f in (0.0, 0.36, 0.72, 1.0):                         # 関節ごとの腹（強い）
            px, py = bx + (tx - bx) * f, by + (ty - by) * f
            r = w * (0.5 if f < 1.0 else 0.56)
            d.ellipse([(px - r) * S, (py - r * 0.8) * S, (px + r) * S, (py + r * 0.8) * S], fill=235 if f == 1.0 else 205)
    a = math.radians(-58 * (0.6 if close else 1.0) * spread)             # 親指
    bx, by = cx - 80, py0 + 120
    ln, w = 112, 46
    tx, ty = bx + ln * math.sin(a), by - ln * math.cos(a)
    d.line([bx * S, by * S, tx * S, ty * S], fill=165, width=int(w * S))
    d.ellipse([(bx - w / 2) * S, (by - w / 2) * S, (bx + w / 2) * S, (by + w / 2) * S], fill=165)
    d.ellipse([(tx - w / 2) * S, (ty - w / 2) * S, (tx + w / 2) * S, (ty + w / 2) * S], fill=235)
    m = np.asarray(can.resize((HW, HH), Image.LANCZOS), np.float32) / 255.0
    yy = np.arange(HH, dtype=np.float32)[:, None]
    prof = np.where(yy < py0 + 30, 1.0, np.where(yy < py0 + 75, 0.95, np.where(yy < py1 - 85, 0.55, 0.9)))        # 手のひらの縦の強さ
    palm = ((yy >= py0 + 20) & (yy <= py1 + 40))
    m = np.where(palm, m * prof, m)
    m *= (1.0 - 0.9 * np.clip((yy - 495) / 120.0, 0, 1))          # 手首は下へ消える
    m *= 0.82 + 0.5 * (_hand_noise(rg, HH, HW, 7, 0.3) + _hand_noise(rg, HH, HW, 26, 0.35))        # 皮ふのむら
    m = np.clip(m, 0, 1)
    im = Image.fromarray((m * 255).astype(np.uint8))
    if mirror:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if scale != 1.0 or angle:
        im = im.resize((int(HW * scale), int(HH * scale)), Image.BICUBIC)
        can2 = Image.new('L', (HW, HH), 0)
        can2.paste(im, ((HW - im.width) // 2, (HH - im.height) // 2 + 20))
        im = can2.rotate(angle, resample=Image.BICUBIC, center=(HW // 2, int(HH * 0.72)))
    return np.asarray(im, np.float32) / 255.0


def _hand_smear(rg, m, length=190, strength=0.75):
    """指先やふちから下へ、なぞれた筋：列ごとに長さをかえて、下へいくほどうすくなる"""
    H, W = m.shape
    Lc = (length * (0.35 + 0.9 * np.clip(_hand_noise(rg, 1, W, 9, 0.5) + 0.5, 0, 1)))[0][None, :]
    out = m.copy()
    for k in range(2, int(length * 1.3), 3):
        wgt = np.clip(1.0 - k / np.maximum(Lc, 1.0), 0, 1) ** 1.4 * strength
        sh = np.zeros_like(m)
        sh[k:] = m[:-k]
        out = np.maximum(out, sh * wgt)
    return out


def _hand_finish(rg, m, smear, drips=7):
    """強さ m とかすれ smear から、霧のかかったガラスの手形の RGBA 画像を作る：白っぽい灰色・ふちに赤茶・やわらかい端・透け具合は HAND_ALPHA_MAX まで"""
    H, W = m.shape

    def g(a, r):
        return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255.0
    body = g(m, 1.6)
    sm = g(smear, 2.2)
    streak = np.clip(sm - body, 0, 1)                             # 筋だけの部分
    drip = np.zeros_like(m)                                       # 指先から垂れる細い筋
    ys, xs = np.nonzero((body[:-1] > 0.55) & (body[1:] <= 0.55))
    if len(ys):
        for j in rg.choice(len(ys), size=min(len(ys), drips), replace=False):
            y0, x0 = ys[j], xs[j]
            ln = int(rg.integers(60, 230))
            wd = int(rg.integers(1, 3))
            for t in range(ln):
                if y0 + t >= H:
                    break
                xo = int(x0 + 5 * math.sin(t / 23.0 + j))
                xo = min(W - 4, max(3, xo))
                drip[y0 + t, xo - wd:xo + wd + 1] = np.maximum(drip[y0 + t, xo - wd:xo + wd + 1], (1 - t / ln) ** 0.8 * 0.4)
    drip = g(drip, 1.6)
    fog = g(np.maximum(m, smear * 0.6), 28) * 0.16                # 手のまわりの、霧がにじんだ広いもや
    a = np.clip(body * 0.50 + streak * 0.42 + drip * 0.6 + fog, 0, HAND_ALPHA_MAX)
    inner = g(m, 7)
    rim = np.clip(1.0 - inner * 1.5, 0, 1) * np.clip(body * 4, 0, 1)         # ふち（中が薄いところ）
    rim = g(np.maximum(rim, np.clip(streak * 1.5, 0, 1) * 0.5), 3.0)
    base = np.array([214, 214, 220], np.float32)
    red = np.array([140, 52, 40], np.float32)
    rgb = base[None, None, :] * (1 - 0.75 * rim[..., None]) + red[None, None, :] * (0.75 * rim[..., None])
    rgb *= (0.92 + 0.12 * _hand_noise(rg, H, W, 12, 1.0))[..., None]
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = rgb.clip(0, 255).astype(np.uint8)
    img[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


def _hand_streaks(rg):
    """5本の指を、上から下へ引きずった筋（手のひらなし）：頭にだけ指先の丸い跡"""
    m = np.zeros((HH, HW), np.float32)
    xs = [128, 200, 272, 340, 396]
    yy, xx_ = np.mgrid[0:HH, 0:HW]
    for i, x0 in enumerate(xs):
        top = 70 + int(rg.integers(0, 40)) + (30 if i in (0, 4) else 0)
        w = int(rg.integers(15, 22))
        x = x0 + 14 * np.sin((yy - top) / 90.0 + i) + (yy - top) * 0.06 * (i - 2)
        L = int(rg.integers(360, 520))
        t = (yy - top)
        prof = np.exp(-((xx_ - x) / (w * (0.6 + 0.4 * np.clip(1 - t / L, 0, 1)))) ** 2) * ((t >= 0) & (t < L)) * np.clip(1 - t / L, 0, 1) ** 0.7
        stp = np.exp(-(((xx_ - x0) / (w * 1.15)) ** 2 + ((yy - top) / (w * 1.4)) ** 2))
        m = np.maximum(m, np.maximum(prof * 0.8, stp))
    m *= 0.8 + 0.4 * np.clip(_hand_noise(rg, HH, HW, 10, 0.5) + 0.5, 0, 1)
    return np.clip(m, 0, 1)


def make_hand_prints():
    """glass_hand_1〜4.png（512x640 の透明PNG）。1=右手・2=左手(指をひらく)・3=指をとじて強く押す(手のひらが下へ流れる)・4=5本の指を引きずった筋。
    共有乱数 R は使わない（ほかの画像は変えない）"""
    specs = [
        dict(kind='hand', seed=1, spread=1.0, mirror=False, scale=0.92, angle=-7, smear=170),
        dict(kind='hand', seed=2, spread=1.35, mirror=True, scale=0.82, angle=11, smear=120),
        dict(kind='hand', seed=3, spread=0.8, close=True, mirror=False, scale=0.88, angle=22, smear=260, palm_drag=True),
        dict(kind='streak', seed=4),
    ]
    for i, sp in enumerate(specs, 1):
        rg = np.random.default_rng(7140 + sp['seed'])
        if sp['kind'] == 'streak':
            m = _hand_streaks(rg)
            sm = _hand_smear(rg, m, length=90, strength=0.5)
        else:
            m = _hand_mask(rg, sp['spread'], sp.get('close', False), sp['mirror'], sp['scale'], sp['angle'])
            sm = _hand_smear(rg, m, length=sp['smear'], strength=0.8)
            if sp.get('palm_drag'):                               # 手のひらをずらして押しつけた：全体が下へ引きずられる
                sm = np.maximum(sm, _hand_smear(rg, np.clip(m * 0.9, 0, 1), length=330, strength=0.7))
        im = _hand_finish(rg, m, sm)
        p = os.path.join(OUT, 'glass_hand_%d.png' % i)
        im.save(p, optimize=True)
        print('保存', 'game/glass_hand_%d.png' % i, im.size, os.path.getsize(p) // 1024, 'KB')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'hands':         # ガラスの手形だけ作る（ほかの画像は触らない）
        make_hand_prints()
    elif len(sys.argv) > 1 and sys.argv[1] == 'glow':          # 謎7の数字・ヒントだけ作る（ほかの画像は触らない）
        make_glow_digits(); make_code_hints()
    else:
        make_posters(); make_glass_texts(); make_tree_poster(); make_newspapers(); make_gym_card(); make_memo(); make_phonebook(); make_sign(); make_lcds()
        make_glow_digits(); make_code_hints()                  # 共有乱数 R の順番を変えないよう、必ず最後
        make_hand_prints()                                     # 手形は専用の乱数を使う（順番は関係ない）
    print('完了')
