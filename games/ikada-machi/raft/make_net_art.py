# 網の絵（art/net/*.png）を、ゲーム用に切り分けて raft/net_art.js に埋め込む。
# 使い方：python3 make_net_art.py   （絵を差し替えたら、もう一度実行する）
import base64, io, json, pathlib
from collections import Counter
from math import gcd
from PIL import Image

here = pathlib.Path(__file__).parent
art = here.parent / 'art' / 'net'

def true_scale(im):
    px, (w, h) = im.load(), im.size; g = 0
    for y in range(0, h, 5):
        run, prev = 1, px[0, y]
        for x in range(1, w):
            if px[x, y] == prev: run += 1
            else: g = gcd(g, run); run, prev = 1, px[x, y]
        g = gcd(g, run)
    for x in range(0, w, 5):
        run, prev = 1, px[x, 0]
        for y in range(1, h):
            if px[x, y] == prev: run += 1
            else: g = gcd(g, run); run, prev = 1, px[x, y]
        g = gcd(g, run)
    return max(1, g)

def load(name):
    im = Image.open(art / name).convert('RGB'); s = true_scale(im)
    if s > 1: im = im.resize((im.width // s, im.height // s), Image.NEAREST)
    return im, s

def isnet(c): return c[0] > c[2] + 25 and c[0] > 100

def longest(counts, th):
    best, cur, start, bs = (0, -1), 0, 0, -1
    for i, v in enumerate(counts + [0]):
        if v >= th:
            if cur == 0: start = i
            cur += 1
        else:
            if cur > best[0]: best = (cur, start)
            cur = 0
    return best[1], best[1] + best[0] - 1

def frame(im, box, bg, near, rope):
    cell = im.crop(box); w, h = cell.size; px = cell.load()
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0)); po = out.load()
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if c == bg: continue
            if c in near: po[x, y] = (6, 14, 28, 90); continue
            po[x, y] = c + (255,)
    cols = [sum(1 for y in range(h) if po[x, y][3] == 255 and isnet(po[x, y][:3])) for x in range(w)]
    rows = [sum(1 for x in range(w) if po[x, y][3] == 255 and isnet(po[x, y][:3])) for y in range(h)]
    x0, x1 = longest(cols, 4); y0, y1 = longest(rows, 4)
    if rope:                                   # ロープ（細い線）は、プログラムで引くので消す
        for y in range(h):
            for x in range(w):
                if (x < x0 - 1 or x > x1 + 1) and po[x, y][3] == 255 and isnet(po[x, y][:3]): po[x, y] = (0, 0, 0, 0)
    bb = out.getbbox(); cx, cy = (x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2
    out = out.crop(bb); buf = io.BytesIO(); out.save(buf, 'PNG')
    return {'src': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(), 'w': out.width, 'h': out.height,
            'ax': round(cx - bb[0], 1), 'ay': round(cy - bb[1], 1), 'discW': x1 - x0 + 1}

def sheet(name, cols, rows, rope_rows=(), up=1):
    im, s = load(name)
    if up > 1: im = im.resize((im.width * up, im.height * up), Image.NEAREST)   # 別の絵より細かさが小さいときは、整数倍に拡大して合わせる
    c = Counter(im.getdata()); bg = c.most_common(1)[0][0]
    near = {k for k in c if k != bg and sum(abs(a - b) for a, b in zip(k, bg)) <= 12}
    fw, fh = im.width // cols, im.height // rows; frames = []
    for r in range(rows):
        for q in range(cols):
            frames.append(frame(im, (q * fw, r * fh, (q + 1) * fw, (r + 1) * fh), bg, near, r in rope_rows))
    print(name, 'scale', s, 'size', im.size, 'frame', (fw, fh), 'discW', [f['discW'] for f in frames])
    return frames

t = sheet('throw_splash.png', 4, 2, rope_rows=(0,))
idle = sheet('idle.png', 4, 1, up=2)
data = {'fly': t[:4], 'splash': t[4:], 'idle': idle, 'flyDiscW': t[3]['discW'], 'idleDiscW': idle[0]['discW']}
(here / 'net_art.js').write_text('window.RAFT.netArt = ' + json.dumps(data, ensure_ascii=False) + ';\n', encoding='utf-8')
print('net_art.js', (here / 'net_art.js').stat().st_size, 'bytes')
