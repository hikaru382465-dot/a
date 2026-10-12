# 置き物の絵（作業台・貯水槽・ろ過器）を、art/items/catalog.png から切り出して raft/objs_art.js に埋め込む。
#  背景がにじんでいるので、「ふちの黒い線」で囲まれた外側を背景として消す。
# 使い方：python3 make_objs.py
import base64, io, json, pathlib
from collections import deque
import numpy as np
from PIL import Image

here = pathlib.Path(__file__).parent
cat = Image.open(here.parent / 'art' / 'items' / 'catalog.png').convert('RGB')
SHRINK = 4

def png(img):
    buf = io.BytesIO(); img.save(buf, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

def cutout(box, dark=48, shrink=None):
    x0, y0, x1, y1 = box; sub = cat.crop(box); a = np.array(sub).astype(int); h, w = a.shape[:2]
    luma = a.sum(axis=2) / 3
    wall0 = luma < dark                     # 黒い線
    wall = wall0.copy()
    for _ in range(2):                      # 線のすきまをふさぐ（2ドットぶん太らせる）
        wall = wall | np.roll(wall, 1, 0) | np.roll(wall, -1, 0) | np.roll(wall, 1, 1) | np.roll(wall, -1, 1)
    seen = np.zeros((h, w), bool); q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not wall[y, x]: seen[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if not wall[y, x] and not seen[y, x]: seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X = y + dy, x + dx
            if 0 <= Y < h and 0 <= X < w and not seen[Y, X] and not wall[Y, X]: seen[Y, X] = True; q.append((Y, X))
    inside = ~seen
    core = inside.copy()
    for _ in range(2):                      # 太らせたぶんを、元にもどす
        core = core & np.roll(core, 1, 0) & np.roll(core, -1, 0) & np.roll(core, 1, 1) & np.roll(core, -1, 1)
    inside = core | (wall0 & inside)
    wall = wall0
    lab = np.zeros((h, w), int); n = 0; best = (0, 0)       # いちばん大きい1つだけ残す（となりの絵を消す）
    for y0_ in range(h):
        for x0_ in range(w):
            if inside[y0_, x0_] and not lab[y0_, x0_]:
                n += 1; lab[y0_, x0_] = n; qq = deque([(y0_, x0_)]); cnt = 0
                while qq:
                    cy, cx = qq.popleft(); cnt += 1
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                        Y, X = cy + dy, cx + dx
                        if 0 <= Y < h and 0 <= X < w and inside[Y, X] and not lab[Y, X]: lab[Y, X] = n; qq.append((Y, X))
                if cnt > best[0]: best = (cnt, n)
    inside = lab == best[1]
    # 線のすぐ外側の1ぶんも、物のふちとして残す（線の色をそのまま使う）
    grown = inside.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        grown |= np.roll(np.roll(inside, dy, 0), dx, 1) & wall
    rgba = np.dstack([a.astype(np.uint8), (grown * 255).astype(np.uint8)])
    img = Image.fromarray(rgba, 'RGBA'); bb = img.getchannel('A').getbbox(); img = img.crop(bb)
    img = img.resize((max(1, round(img.width / (shrink or SHRINK))), max(1, round(img.height / (shrink or SHRINK)))), Image.BOX)
    al = np.array(img.getchannel('A')); img.putalpha(Image.fromarray(((al > 110) * 255).astype(np.uint8)))
    # 色数をへらして、ドット絵っぽくそろえる
    rgb = img.convert('RGB').quantize(28, dither=Image.NONE).convert('RGB'); rgb.putalpha(img.getchannel('A'))
    return rgb

def entry(img): return {'src': png(img), 'w': img.width, 'h': img.height}

bench = cutout((15, 476, 150, 585))
tank = cutout((552, 482, 632, 588))
frame = cutout((486, 494, 548, 574))
print('sizes', bench.size, tank.size, frame.size)

def tank_level(img, lv):                    # 水の青を、へった分だけ灰色にする
    a = np.array(img).astype(float); f = (3 - lv) / 3
    blue = (a[..., 2] > a[..., 0] + 22) & (a[..., 3] > 0)
    grey = np.array([58, 60, 66.0])
    a[blue, :3] = a[blue, :3] * (1 - f) + grey * f
    return Image.fromarray(a.astype(np.uint8), 'RGBA')

def drip(img, on):
    a = np.array(img).copy()
    if on:
        h, w = a.shape[:2]; x = w - 6
        for dy, c in ((1, (120, 190, 240)), (3, (160, 215, 250))): a[h - 1 - dy, x] = (*c, 255)
    return Image.fromarray(a, 'RGBA')

# インベントリ・漂流物に使う小さな絵（3分の1の大きさ）。ppu＝ゲームの中での大きさ（いちばん長い辺が0.5マスぶん）
def clay_tint(im):     # 灰色の石の絵を、粘土色（赤茶）にぬりかえる
    a = np.array(im).astype(float); L = a[..., :3].mean(axis=2) / 255.0
    lo, hi = np.array([70, 36, 24.0]), np.array([226, 140, 92.0]); t = np.clip((L - 0.12) / 0.7, 0, 1)[..., None]
    a[..., :3] = lo * (1 - t) + hi * t; return Image.fromarray(a.astype(np.uint8), 'RGBA')

def icon(box, shrink=3, tint=None):
    im = cutout(box, shrink=shrink)
    if tint: im = tint(im)
    e = entry(im); e['ppu'] = round(max(im.size) / 0.5); return e
icons = {'wood': [icon((38, 28, 142, 118))], 'floor': [icon((142, 28, 246, 118))], 'cloth': [icon((712, 36, 790, 118))],
         'fish': [icon((26, 136, 136, 208))], 'hammer': [icon((238, 238, 324, 344))], 'net': [icon((1066, 240, 1184, 342))], 'rod': [icon((410, 232, 500, 344), shrink=2)],
         'iron': [icon((628, 30, 700, 112))], 'grilled': [icon((136, 136, 232, 210))], 'campfire': [icon((940, 618, 1028, 702), shrink=3)], 'clay': [icon((438, 32, 524, 118), tint=clay_tint)]}
for n, e in list(icons.items()):
    im = Image.open(io.BytesIO(base64.b64decode(e[0]['src'].split(',')[1]))).convert('RGBA'); print(n, im.size, e[0]['ppu'])
    bg = Image.new('RGBA', (im.width * 5, im.height * 5), (40, 90, 120, 255)); bg.alpha_composite(im.resize((im.width * 5, im.height * 5), Image.NEAREST)); bg.save(f'/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/ic_{n}.png')
out = {'ppu': 40, 'icons': icons, 'bench': [entry(bench)], 'tank': [entry(tank_level(tank, l)) for l in range(4)], 'filter': [entry(drip(frame, 0)), entry(drip(frame, 1))]}
out['campfire'] = out['icons']['campfire']
(here / 'objs_art.js').write_text('window.RAFT.objArt = ' + json.dumps(out) + ';\n')
for n, im in (('bench', bench), ('tank', tank), ('frame', frame)):
    bg = Image.new('RGBA', (im.width * 6, im.height * 6), (40, 90, 120, 255)); bg.alpha_composite(im.resize((im.width * 6, im.height * 6), Image.NEAREST)); bg.save(f'/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/o_{n}.png')

# ---- 新しい釣りざお（ひかるの絵：糸とウキつき）。art/items/rod2.png から切り出す ----
def make_rod():
    src = here.parent / 'art' / 'items' / 'rod2.png'
    if not src.exists(): return
    im = Image.open(src).convert('RGB'); a = np.array(im).astype(int); luma = a.sum(axis=2) / 3
    X0, Y0, X1, Y1 = 365, 80, 605, 430
    fg = (luma < 205)[Y0:Y1, X0:X1]; h, w = fg.shape
    def grow(m, n=1):
        for _ in range(n): m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
        return m
    def shrink_(m, n=1):
        for _ in range(n): m = m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
        return m
    d = grow(fg, 2); lab = np.zeros((h, w), int); best = (0, 0); n = 0
    for y in range(h):
        for x in range(w):
            if d[y, x] and not lab[y, x] and y < 330 - 0:
                n += 1; lab[y, x] = n; q = deque([(y, x)]); cnt = 0
                while q:
                    cy, cx = q.popleft(); cnt += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            Y, X = cy + dy, cx + dx
                            if 0 <= Y < h and 0 <= X < w and d[Y, X] and not lab[Y, X]: lab[Y, X] = n; q.append((Y, X))
                if cnt > best[0]: best = (cnt, n)
    full = fg & (lab == best[1]); full = shrink_(grow(full, 3), 3)        # すきまをうめる
    full = grow(full & grow(full, 0), 0)
    body = full.copy()
    rgb = np.array(im)[Y0:Y1, X0:X1]
    def pack(mask, th):
        rgba = np.dstack([rgb, (mask * 255).astype(np.uint8)]); img = Image.fromarray(rgba, 'RGBA'); bb = img.getchannel('A').getbbox()
        return img, bb
    imf, bb = pack(full, 0); imb, _ = pack(body, 0)
    imf = imf.crop(bb); imb = imb.crop(bb)
    H = 52; sc = H / imf.height
    def fin(img):
        img = img.resize((max(1, round(img.width * sc)), H), Image.BOX); al = np.array(img.getchannel('A')); px = np.array(img.convert('RGB')).astype(int); white = (px.min(axis=2) > 175)      # 背景の白っぽい色を消す
        img.putalpha(Image.fromarray((((al > 90) & ~white) * 255).astype(np.uint8)))
        q = img.convert('RGB').quantize(28, dither=Image.NONE).convert('RGB'); q.putalpha(img.getchannel('A')); return q
    ff, fb = fin(imf), fin(imb)
    ab = np.array(fb); ab[14:, 21:, 3] = 0; ab[9:14, 29:, 3] = 0; fb = Image.fromarray(ab, 'RGBA')      # ウキと糸だけ消す（投げたあとは、水の中のウキを使う）
    # ざおの先（いちばん上の、いちばん右）を、絵の中の位置で出す
    aa = np.array(fb.getchannel('A')); ys, xs = np.nonzero(aa); top = int(ys.min()); tx = int(xs[ys <= top + 1].max())
    for nme, img in (('rod', ff), ('rodBody', fb)):
        bg = Image.new('RGBA', (img.width * 6, img.height * 6), (40, 90, 120, 255)); bg.alpha_composite(img.resize((img.width * 6, img.height * 6), Image.NEAREST)); bg.save(f'/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/rod_{nme}.png')
    ea, eb = entry(ff), entry(fb); ea['ppu'] = eb['ppu'] = 72; eb['tip'] = [tx + 0.5, top]
    return {'rod': [ea], 'rodBody': [eb]}, (ff.size, fb.size, tx, top)
r = make_rod()
if r:
    out['icons'].update(r[0]); print('rod', r[1])
    (here / 'objs_art.js').write_text('window.RAFT.objArt = ' + json.dumps(out) + ';\n')
