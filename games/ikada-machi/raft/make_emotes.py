# 吹き出し（ハート・！・汗・怒り・zzz・？・音符 など）を、art/buddy/emotes.png（相棒のしぐさシート）から切り出して raft/emotes_art.js に埋め込む。
# 使い方：python3 make_emotes.py
import base64, io, json, pathlib
from collections import deque
import numpy as np
from PIL import Image

here = pathlib.Path(__file__).parent
A = np.array(Image.open(here.parent / 'art' / 'buddy' / 'emotes.png').convert('RGB')).astype(int)
A2 = np.array(Image.open(here.parent / 'art' / 'buddy' / 'loops.png').convert('RGB')).astype(int)
SC = 0.5

def tidy(im):      # 半透明をなくして、色数をへらす（ドット絵っぽくそろえる）
    al = np.array(im.getchannel('A')); im.putalpha(Image.fromarray(((al > 100) * 255).astype(np.uint8)))
    q = im.convert('RGB').quantize(10, dither=Image.NONE).convert('RGB'); q.putalpha(im.getchannel('A')); return q

def png(img):
    buf = io.BytesIO(); img.save(buf, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

def cut(box, minpx=9, src=None):
    """吹き出しの色（青・ピンク・赤・紺）だけを取り出す。キャラの茶色・ベージュは入らない。"""
    AA = A if src is None else src
    x0, y0, x1, y1 = box; sub = AA[y0:y1, x0:x1]; h, w = sub.shape[:2]
    r, g, bl = sub[..., 0], sub[..., 1], sub[..., 2]
    mx, mn = sub.max(axis=2), sub.min(axis=2)
    blue = (bl > r + 22) & (bl > 60) & (mn < 235)             # 青・紺（zz・？・音符・汗・ちょうちん）
    pink = (r > g + 45) & (r > 170)                           # ピンク・赤（ハート・！・怒り）
    core = (blue | pink) & (mn < 238)
    near = core.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)): near |= np.roll(np.roll(core, dy, 0), dx, 1)
    dark = near & (mx < 120)                                  # 吹き出しのすぐそばの、こいふちだけ入れる
    m = core | dark
    # 小さなゴミを消す（つながり 8近傍・minpx 未満）
    lab = np.zeros((h, w), int); keep = np.zeros((h, w), bool); n = 0
    for y in range(h):
        for x in range(w):
            if m[y, x] and not lab[y, x]:
                n += 1; lab[y, x] = n; qq = deque([(y, x)]); pts = []
                while qq:
                    cy, cx = qq.popleft(); pts.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            Y, X = cy + dy, cx + dx
                            if 0 <= Y < h and 0 <= X < w and m[Y, X] and not lab[Y, X]: lab[Y, X] = n; qq.append((Y, X))
                if len(pts) >= minpx:
                    for (py, px) in pts: keep[py, px] = True
    # 穴ふさぎ（すきまを1ドットぶん）
    k2 = keep.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): k2 |= np.roll(np.roll(keep, dy, 0), dx, 1) & m
    rgba = np.dstack([sub.astype(np.uint8), (k2 * 255).astype(np.uint8)]); img = Image.fromarray(rgba, 'RGBA')
    bb = img.getchannel('A').getbbox()
    return img.crop(bb) if bb else None

BOXES = {'heart': (258, 48, 310, 122), 'exclaim': (548, 56, 596, 106), 'sweat': (698, 80, 730, 128), 'anger': (826, 58, 878, 108),
         'zz': (984, 54, 1028, 120), 'question': (1136, 50, 1172, 92), 'sweat2': (1290, 80, 1312, 122), 'music': (358, 292, 388, 320),
         'zzz': (1366, 302, 1398, 340), 'think': (1036, 722, 1068, 756)}
# ループ用の絵（loops.png）にも、zzz・音符・ちょうちんがあった
BOXES2 = {'zzA': (140, 92, 186, 140), 'zzB': (312, 90, 360, 140), 'bubble': (506, 92, 552, 140), 'zzC': (696, 92, 744, 140), 'zzD': (888, 104, 930, 144),
          'zzE': (1084, 100, 1132, 146), 'noteA': (700, 358, 745, 396), 'noteB': (1272, 372, 1308, 404), 'noteC': (1456, 360, 1494, 392), 'noteD': (1074, 624, 1112, 660), 'noteE': (1462, 856, 1496, 886)}
out = {'ppu': 46, 'emotes': {}}; tiles = []
for k, b in BOXES.items():
    im = cut(b)
    if im is None: print('なし', k); continue
    im = im.resize((max(1, round(im.width * SC)), max(1, round(im.height * SC))), Image.BOX)
    im = tidy(im)
    tiles.append((k, im)); out['emotes'][k] = {'src': png(im), 'w': im.width, 'h': im.height}; print(k, im.size)
for k, b in BOXES2.items():
    im = cut(b, 8, A2)
    if im is None: print('なし', k); continue
    im = im.resize((max(1, round(im.width * SC)), max(1, round(im.height * SC))), Image.BOX)
    im = tidy(im)
    tiles.append((k, im)); out['emotes'][k] = {'src': png(im), 'w': im.width, 'h': im.height}; print(k, im.size)
(here / 'emotes_art.js').write_text('window.RAFT.emoteArt = ' + json.dumps(out) + ';\n')
W = sum(i.width * 6 + 10 for _, i in tiles); H = max(i.height * 6 for _, i in tiles)
sheet = Image.new('RGBA', (W, H), (40, 90, 120, 255)); x = 0
for _, i in tiles:
    sheet.alpha_composite(i.resize((i.width * 6, i.height * 6), Image.NEAREST), (x, 0)); x += i.width * 6 + 10
sheet.save('/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/emotes_sheet.png')
