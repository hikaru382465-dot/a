# 吹き出し（ハート・！・汗・怒り・zzz・？・音符 など）を、art/buddy/emotes.png（相棒のしぐさシート）から切り出して raft/emotes_art.js に埋め込む。
# 使い方：python3 make_emotes.py
import base64, io, json, pathlib
from collections import deque
import numpy as np
from PIL import Image

here = pathlib.Path(__file__).parent
A = np.array(Image.open(here.parent / 'art' / 'buddy' / 'emotes.png').convert('RGB')).astype(int)
SC = 0.5

def png(img):
    buf = io.BytesIO(); img.save(buf, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

def cut(box, minpx=7):
    x0, y0, x1, y1 = box; sub = A[y0:y1, x0:x1]; h, w = sub.shape[:2]
    mx, mn = sub.max(axis=2), sub.min(axis=2)
    bg = (mx - mn <= 14) & (mn >= 205)
    out = np.zeros((h, w), bool); q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bg[y, x]: out[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if bg[y, x] and not out[y, x]: out[y, x] = True; q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X = cy + dy, cx + dx
            if 0 <= Y < h and 0 <= X < w and bg[Y, X] and not out[Y, X]: out[Y, X] = True; q.append((Y, X))
    fg = ~out
    lab = np.zeros((h, w), int); keep = np.zeros((h, w), bool); n = 0
    for y in range(h):
        for x in range(w):
            if fg[y, x] and not lab[y, x]:
                n += 1; lab[y, x] = n; qq = deque([(y, x)]); pts = []
                while qq:
                    cy, cx = qq.popleft(); pts.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            Y, X = cy + dy, cx + dx
                            if 0 <= Y < h and 0 <= X < w and fg[Y, X] and not lab[Y, X]: lab[Y, X] = n; qq.append((Y, X))
                edge = any(py in (0, h - 1) or px in (0, w - 1) for (py, px) in pts)
                if minpx <= len(pts) <= 900 and not edge:
                    for (py, px) in pts: keep[py, px] = True
    rgba = np.dstack([sub.astype(np.uint8), (keep * 255).astype(np.uint8)]); img = Image.fromarray(rgba, 'RGBA')
    bb = img.getchannel('A').getbbox()
    return img.crop(bb) if bb else None

BOXES = {'heart': (258, 48, 310, 122), 'exclaim': (548, 56, 596, 106), 'sweat': (698, 80, 730, 128), 'anger': (826, 58, 878, 108),
         'zz': (984, 54, 1028, 120), 'question': (1136, 50, 1172, 92), 'sweat2': (1290, 80, 1312, 122), 'music': (358, 292, 388, 320),
         'zzz': (1366, 302, 1398, 340), 'think': (1036, 722, 1068, 756)}
out = {'ppu': 46, 'emotes': {}}; tiles = []
for k, b in BOXES.items():
    im = cut(b)
    if im is None: print('なし', k); continue
    im = im.resize((max(1, round(im.width * SC)), max(1, round(im.height * SC))), Image.BOX)
    al = np.array(im.getchannel('A')); im.putalpha(Image.fromarray(((al > 90) * 255).astype(np.uint8)))
    tiles.append((k, im)); out['emotes'][k] = {'src': png(im), 'w': im.width, 'h': im.height}; print(k, im.size)
(here / 'emotes_art.js').write_text('window.RAFT.emoteArt = ' + json.dumps(out) + ';\n')
W = sum(i.width * 6 + 10 for _, i in tiles); H = max(i.height * 6 for _, i in tiles)
sheet = Image.new('RGBA', (W, H), (40, 90, 120, 255)); x = 0
for _, i in tiles:
    sheet.alpha_composite(i.resize((i.width * 6, i.height * 6), Image.NEAREST), (x, 0)); x += i.width * 6 + 10
sheet.save('/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/emotes_sheet.png')
