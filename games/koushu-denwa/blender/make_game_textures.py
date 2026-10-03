"""
ゲーム用の紙もの・看板・液晶の画像を作る（Pillow + numpy。Blender不要）

作るもの（assets/tex/game/）：
  poster_01〜12 … ガラスに貼られる怖い張り紙     poster_hint … 「あの日をおして（4けた）」
  tree_poster … 木の張り紙（金庫ダイヤルの番号）  book_news … 本に挟まった古い新聞
  bulletin_news … 掲示板の新聞切り抜き            gym_card … ジムの会員カード（ドアぶっ壊しのヒント）
  memo_hatch … 電話機の下のふたの中のメモ         phonebook … 電話帳のページ
  missing_news … バッドエンド用の新聞             sign_entrance … 入口の看板
  lcd_board_idle / lcd_board_1〜3 … 警察・消防の欄の液晶
使い方：python make_game_textures.py
"""
import os
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


if __name__ == '__main__':
    make_posters(); make_tree_poster(); make_newspapers(); make_gym_card(); make_memo(); make_phonebook(); make_sign(); make_lcds()
    print('完了')
