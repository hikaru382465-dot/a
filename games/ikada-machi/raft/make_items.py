# 漂流物の絵を、ゲーム用に切り出して raft/items.js に埋め込む。
#  ・art/items/sheet.png（ひかるが作った3×3の絵）から、石・布・瓶・袋・ヤシの実・割ったヤシの実
#  ・ロープと釣りざおだけは、art/chars/sheet.png（キャラの絵）の装備のところから（ひかるが「こっちのほうがいい」と選んだ）
# 使い方：python3 make_items.py    （絵を差し替えたら、もう一度実行する）
import base64, io, json, pathlib
from collections import deque
from math import gcd
import numpy as np
from PIL import Image

here = pathlib.Path(__file__).parent
art = here.parent / 'art'

def png(img):
    buf = io.BytesIO(); img.save(buf, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

def components(mask, minpx=300, reach=2):
    h, w = mask.shape; lab = np.zeros((h, w), int); n = 0; out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not lab[y, x]:
                n += 1; q = deque([(y, x)]); lab[y, x] = n; pts = [(y, x)]
                while q:
                    cy, cx = q.popleft()
                    for dy in range(-reach, reach + 1):
                        for dx in range(-reach, reach + 1):
                            Y, X = cy + dy, cx + dx
                            if 0 <= Y < h and 0 <= X < w and mask[Y, X] and not lab[Y, X]: lab[Y, X] = n; q.append((Y, X)); pts.append((Y, X))
                if len(pts) >= minpx: out.append(pts)
    return out

def cut(src, pts, off=(0, 0)):
    ys = [p[0] for p in pts]; xs = [p[1] for p in pts]; x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    cell = Image.new('RGBA', (x1 - x0 + 1, y1 - y0 + 1), (0, 0, 0, 0)); px = cell.load()
    for (y, x) in pts: px[x - x0, y - y0] = tuple(src[off[1] + y, off[0] + x]) + (255,)
    return cell

def entry(img):
    return {'src': png(img), 'w': img.width, 'h': img.height}

# ---- ひかるの新しい絵（5倍に拡大された絵）----
sheet = Image.open(art / 'items' / 'sheet.png').convert('RGB'); SC = 5
small = sheet.resize((sheet.width // SC, sheet.height // SC), Image.NEAREST); A = np.array(small)
bg = A[1, 1]; mask = np.abs(A.astype(int) - bg).sum(axis=2) > 12
comps = components(mask, minpx=60, reach=1)
boxes = []
for pts in comps:
    ys = [p[0] for p in pts]; xs = [p[1] for p in pts]; boxes.append(((min(ys) + max(ys)) / 2, (min(xs) + max(xs)) / 2, pts))
boxes.sort(key=lambda b: (round(b[0] / 70), b[1]))     # 上の段から、左から
names = ['rope_new', 'stoneA', 'stoneB', 'cloth', 'glass', 'bag', 'coconut', 'coconutOpen', 'rod_new']
items = {}
for n, b in zip(names, boxes): items[n] = cut(A, b[2])
print('new sheet items', len(boxes), {k: v.size for k, v in items.items()})

# ---- キャラの絵の、装備のところから：ロープと釣りざお ----
C = np.array(Image.open(art / 'chars' / 'sheet.png').convert('RGB')).astype(int)
x0, y0, x1, y1 = 895, 205, 1105, 405
sub = C[y0:y1, x0:x1]
REFS = [np.array([241, 235, 227]), np.array([236, 229, 219])]      # 外の背景と、カードの背景（2つの色）
near = np.minimum(np.abs(sub - REFS[0]).sum(axis=2), np.abs(sub - REFS[1]).sum(axis=2)) <= 24
fg = ~near
cc = components(fg, minpx=400, reach=2)
cb = []
for pts in cc:
    ys = [p[0] for p in pts]; xs = [p[1] for p in pts]; cb.append((min(xs), min(ys), max(xs), max(ys), len(pts), pts))
cb.sort(key=lambda b: b[1])
print('char-sheet parts', [(b[0], b[1], b[2], b[3], b[4]) for b in cb])
def pick_rope():   # 左のカードの、上のロープ（巻いたロープ）
    return min((b for b in cb if b[0] < 100 and b[4] > 1500), key=lambda b: b[1])
def pick_rod():    # 右のカードの、細長い釣りざお
    return max((b for b in cb if b[0] > 100), key=lambda b: b[3] - b[1])
def fit(cell, long_side, by='w'):
    s = long_side / (cell.width if by == 'w' else cell.height)
    big = Image.new('RGBA', cell.size, (0, 0, 0, 0))
    from PIL import ImageFilter
    cell.putalpha(cell.getchannel('A').filter(ImageFilter.MinFilter(3)))
    nw, nh = max(1, round(cell.width * s)), max(1, round(cell.height * s))
    sm = cell.resize((nw, nh), Image.LANCZOS); al = sm.getchannel('A').point(lambda v: 255 if v > 110 else 0)
    sm = sm.convert('RGBA'); sm.putalpha(al); return sm
def cut_checker(path, box, shrink=2, blank=None):
    """白い市松もようの背景の絵から、外のふちとつながった白っぽい所だけを消して切り出す（絵の中の白は残る）。"""
    from collections import deque
    im = Image.open(path).convert('RGB').crop(box); a = np.array(im).astype(int); h, w = a.shape[:2]
    bgl = (a.min(axis=2) > 205) & ((a.max(axis=2) - a.min(axis=2)) < 28)
    if blank: bgl[blank[1]:, blank[0]:] = True      # となりの絵（ミミズなど）が入る所を、背景あつかいにする
    om = np.zeros((h, w), bool); q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bgl[y, x] and not om[y, x]: om[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if bgl[y, x] and not om[y, x]: om[y, x] = True; q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X = cy + dy, cx + dx
            if 0 <= Y < h and 0 <= X < w and bgl[Y, X] and not om[Y, X]: om[Y, X] = True; q.append((Y, X))
    fg = ~om
    cs = components(fg, minpx=50, reach=2)
    if cs:
        big = max(cs, key=len); fg = np.zeros((h, w), bool)
        for (yy, xx) in big: fg[yy, xx] = True      # いちばん大きいかたまりだけ残す
    img = Image.fromarray(np.dstack([a.astype(np.uint8), (fg * 255).astype(np.uint8)]), 'RGBA'); img = img.crop(img.getchannel('A').getbbox())
    img = img.resize((max(1, round(img.width / shrink)), max(1, round(img.height / shrink))), Image.NEAREST)
    al = np.array(img.getchannel('A')); img.putalpha(Image.fromarray(((al > 110) * 255).astype(np.uint8)))
    return img
rope = cut_checker(art / 'items' / 'catalog2.png', (1248, 252, 1346, 338), shrink=2)       # 新しい絵シート（catalog2）の巻いたロープ
rope_old = fit(cut(C, pick_rope()[5], (x0, y0)), 44, 'w')
rod = fit(cut(C, pick_rod()[5], (x0, y0)), 62, 'h')
print('rope', rope.size, 'rod', rod.size)

out = {
    'ppu': 64,      # 1マス＝64ピクセル分の大きさで、ゲームの中に出す（絵の大きさのまま）
    'art': {
        'rope': [entry(rope)], 'stone': [entry(items['stoneA']), entry(items['stoneB'])], 'cloth': [entry(items['cloth'])],
        'glass': [entry(items['glass'])], 'coconut': [entry(items['coconut'])],
        'coconutOpen': [entry(items['coconutOpen'])], 'bag': [entry(items['bag'])], 'rod': [entry(rod)]
    }
}
(here / 'items.js').write_text('window.RAFT.itemArt = ' + json.dumps(out) + ';\n', encoding='utf-8')
print('items.js', (here / 'items.js').stat().st_size, 'bytes')
