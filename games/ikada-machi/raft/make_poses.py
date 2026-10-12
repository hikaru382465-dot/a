# 相棒のしぐさ（art/buddy/poses.png）から、使うポーズを切り出して raft/poses_art.js に埋め込む。
# 使い方：python3 make_poses.py
import base64, io, json, pathlib
from collections import deque
import numpy as np
from PIL import Image

here = pathlib.Path(__file__).parent
src = Image.open(here.parent / 'art' / 'buddy' / 'poses.png').convert('RGB'); A = np.array(src).astype(int)
SC = 0.34 if False else 0.40      # 縮小の割合（どのポーズも同じ割合。歩く絵の高さ約110px→約44px）

def cut(box, name, AA=None, bgmin=212):
    AA = A if AA is None else AA
    x0, y0, x1, y1 = box; sub = AA[y0:y1, x0:x1]; h, w = sub.shape[:2]
    mx, mn = sub.max(axis=2), sub.min(axis=2)
    bg = (mx - mn <= 14) & (mn >= bgmin)
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

def fin(img, sc=None):
    sc = sc or SC
    img = img.resize((max(1, round(img.width * sc)), max(1, round(img.height * sc))), Image.BOX)
    al = np.array(img.getchannel('A')); img.putalpha(Image.fromarray(((al > 110) * 255).astype(np.uint8)))
    q = img.convert('RGB').quantize(32, dither=Image.NONE).convert('RGB'); q.putalpha(img.getchannel('A')); return q

def png(img):
    buf = io.BytesIO(); img.save(buf, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

BOXES = {'fish': (840, 485, 965, 630), 'cheer': (18, 278, 142, 425)}
out = {'ppu': 46, 'poses': {}, 'anims': {}}
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
# ---- アニメ（art/buddy/anims.png：5つ×8コマ）----
AN = np.array(Image.open(here.parent / 'art' / 'buddy' / 'anims.png').convert('RGB')).astype(int)
COLS = [(165, 330), (330, 470), (470, 650), (650, 840), (840, 1000), (1000, 1170), (1170, 1345), (1345, 1525)]
ROWS = {'sleep': (30, 202), 'sit': (235, 408), 'relax': (440, 603), 'drink': (640, 802), 'eat': (830, 982)}
LOOP = {'sleep': 5, 'sit': 5, 'relax': 3, 'drink': None, 'eat': None}      # ここから先をくりかえす（0はじまり）。Noneは1回だけ
FPS = {'sleep': 5, 'sit': 5, 'relax': 5, 'drink': 8, 'eat': 8}
sheet2 = []
for k, (y0, y1) in ROWS.items():
    frames = []
    for (x0, x1) in COLS:
        im = fin(cut((x0, y0, x1, y1), k, AN), 0.29); frames.append(im)
        out['anims'][k] = out['anims'].get(k, {'loop': LOOP[k], 'fps': FPS[k], 'frames': []}); out['anims'][k]['frames'].append({'src': png(im), 'w': im.width, 'h': im.height})
    sheet2.append(frames)
W2 = max(sum(i.width * 3 + 6 for i in fr) for fr in sheet2); H2 = sum(max(i.height for i in fr) * 3 + 6 for fr in sheet2)
sh2 = Image.new('RGBA', (W2, H2), (40, 90, 120, 255)); yy = 0
for fr in sheet2:
    xx = 0; hh = max(i.height for i in fr) * 3
    for i in fr: sh2.alpha_composite(i.resize((i.width * 3, i.height * 3), Image.NEAREST), (xx, yy + hh - i.height * 3)); xx += i.width * 3 + 6
    yy += hh + 6
sh2.save('/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/anims_sheet.png')
# ---- ループ用のアニメ（art/buddy/loops.png：4つ×8コマ）：寝てる・くつろぐ・座る（のんびり＝草の上は、いまは使わない）----
LP = np.array(Image.open(here.parent / 'art' / 'buddy' / 'loops.png').convert('RGB')).astype(int)
LCOLS = [22, 212, 400, 590, 778, 965, 1153, 1341]
OLD_SLEEP = out['anims']['sleep']['frames']      # 前の絵の「寝る」（わすわる・うとうと）
LROWS = {'relax': (358, 506), 'sit': (850, 975)}
sheet3 = []
for k, (y0, y1) in LROWS.items():
    frames = []
    out['anims'][k] = {'loop': 0, 'fps': 4, 'frames': []}
    for x0 in LCOLS:
        im = fin(cut((x0 + 10, y0, x0 + 168, y1), k, LP, 170), 0.32); frames.append(im)
        out['anims'][k]['frames'].append({'src': png(im), 'w': im.width, 'h': im.height})
    sheet3.append(frames)
W3 = max(sum(i.width * 3 + 6 for i in fr) for fr in sheet3); H3 = sum(max(i.height for i in fr) * 3 + 6 for fr in sheet3)
sh3 = Image.new('RGBA', (W3, H3), (40, 90, 120, 255)); yy = 0
for fr in sheet3:
    xx = 0; hh = max(i.height for i in fr) * 3
    for i in fr: sh3.alpha_composite(i.resize((i.width * 3, i.height * 3), Image.NEAREST), (xx, yy + hh - i.height * 3)); xx += i.width * 3 + 6
    yy += hh + 6
# 寝る：座ったまま、こっくりこっくり（わすわる→うとうと）だけ
out['anims']['sleep'] = {'loop': 0, 'fps': 2.2, 'frames': [OLD_SLEEP[0], OLD_SLEEP[0], OLD_SLEEP[0], OLD_SLEEP[1]]}
sh3.save('/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/loops_sheet.png')
# （古い）くつろぐ：座る・もたれる（1,2）で落ち着いたら、そのまま。ときどきだけ「のびる」（4,5コマ目）
(here / 'poses_art.js').write_text('window.RAFT.poseArt = ' + json.dumps(out) + ';\n')
W = sum(i.width * 4 + 10 for _, i in tiles); H = max(i.height * 4 for _, i in tiles)
sheet = Image.new('RGBA', (W, H), (40, 90, 120, 255)); x = 0
for _, i in tiles:
    sheet.alpha_composite(i.resize((i.width * 4, i.height * 4), Image.NEAREST), (x, 0)); x += i.width * 4 + 10
sheet.save('/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/poses_sheet.png')
