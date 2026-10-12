# 相棒のしぐさ（art/buddy/poses.png）から、使うポーズを切り出して raft/poses_art.js に埋め込む。
# 使い方：python3 make_poses.py
import base64, io, json, pathlib
from collections import deque
import numpy as np
from PIL import Image

here = pathlib.Path(__file__).parent
src = Image.open(here.parent / 'art' / 'buddy' / 'poses.png').convert('RGB'); A = np.array(src).astype(int)
SC = 0.40      # 縮小の割合（どのポーズも同じ割合。歩く絵の高さ約110px→約44px）

def cut(box, name):
    x0, y0, x1, y1 = box; sub = A[y0:y1, x0:x1]; h, w = sub.shape[:2]
    mx, mn = sub.max(axis=2), sub.min(axis=2)
    bg = (mx - mn <= 14) & (mn >= 212)
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
    lab = np.zeros((h, w), int); best = (0, 0); n = 0
    for y in range(h):
        for x in range(w):
            if fg[y, x] and not lab[y, x]:
                n += 1; lab[y, x] = n; qq = deque([(y, x)]); cnt = 0
                while qq:
                    cy, cx = qq.popleft(); cnt += 1
                    for dy in (-2, -1, 0, 1, 2):
                        for dx in (-2, -1, 0, 1, 2):
                            Y, X = cy + dy, cx + dx
                            if 0 <= Y < h and 0 <= X < w and fg[Y, X] and not lab[Y, X]: lab[Y, X] = n; qq.append((Y, X))
                if cnt > best[0]: best = (cnt, n)
    m = lab == best[1]
    rgba = np.dstack([sub.astype(np.uint8), (m * 255).astype(np.uint8)]); img = Image.fromarray(rgba, 'RGBA'); img = img.crop(img.getchannel('A').getbbox())
    return img

def fin(img):
    img = img.resize((max(1, round(img.width * SC)), max(1, round(img.height * SC))), Image.BOX)
    al = np.array(img.getchannel('A')); img.putalpha(Image.fromarray(((al > 110) * 255).astype(np.uint8)))
    q = img.convert('RGB').quantize(32, dither=Image.NONE).convert('RGB'); q.putalpha(img.getchannel('A')); return q

def png(img):
    buf = io.BytesIO(); img.save(buf, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

BOXES = {'fish': (840, 485, 965, 630), 'fish2': (250, 885, 370, 990), 'sit': (1085, 295, 1185, 425), 'drink': (1195, 295, 1300, 425),
         'sleep': (1295, 300, 1415, 425), 'relax': (1418, 300, 1525, 425), 'cheer': (18, 278, 142, 425), 'carry': (990, 515, 1090, 635),
         'walk': (135, 515, 220, 630)}
out = {'ppu': 46, 'poses': {}}
tiles = []
for k, b in BOXES.items():
    im = fin(cut(b, k))
    if k == 'fish':      # 絵に描いてある、ぶら下がった糸と魚は消す（ゲームの糸を、ざおの先から出すため）
        px = np.array(im); px[10:, 34:, 3] = 0; im = Image.fromarray(px, 'RGBA')
    tiles.append((k, im))
    e = {'src': png(im), 'w': im.width, 'h': im.height}
    if k.startswith('fish'):      # ざおの先＝いちばん上の点
        al = np.array(im.getchannel('A')); ys, xs = np.nonzero(al); top = ys.min(); e['tip'] = [int(xs[ys <= top + 1].mean()) + 0.5, int(top)]
    out['poses'][k] = e
    print(k, im.size, e.get('tip'))
(here / 'poses_art.js').write_text('window.RAFT.poseArt = ' + json.dumps(out) + ';\n')
W = sum(i.width * 4 + 10 for _, i in tiles); H = max(i.height * 4 for _, i in tiles)
sheet = Image.new('RGBA', (W, H), (40, 90, 120, 255)); x = 0
for _, i in tiles:
    sheet.alpha_composite(i.resize((i.width * 4, i.height * 4), Image.NEAREST), (x, 0)); x += i.width * 4 + 10
sheet.save('/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/poses_sheet.png')
