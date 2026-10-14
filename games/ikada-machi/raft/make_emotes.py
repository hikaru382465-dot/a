# 吹き出し（ハート・！・汗・怒り・zzz・？・音符 など）を、art/buddy/emotes.png（相棒のしぐさシート）から切り出して raft/emotes_art.js に埋め込む。
# 使い方：python3 make_emotes.py
import base64, io, json, pathlib
from collections import deque
import numpy as np
from PIL import Image

here = pathlib.Path(__file__).parent
A = np.array(Image.open(here.parent / 'art' / 'buddy' / 'emotes.png').convert('RGB')).astype(int)
A2 = np.array(Image.open(here.parent / 'art' / 'buddy' / 'loops.png').convert('RGB')).astype(int)
SC = 1.0      # 元の絵の大きさのまま（前の2倍の細かさ）。ゲームでは、画面での大きさがかわらないように k=0.5 をかける

def tidy(im):      # 半透明をなくして、色数をへらす（ドット絵っぽくそろえる）
    al = np.array(im.getchannel('A')); im.putalpha(Image.fromarray(((al > 100) * 255).astype(np.uint8)))
    q = im.convert('RGB').quantize(14, dither=Image.NONE).convert('RGB'); q.putalpha(im.getchannel('A')); return q

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
USE_AI_SHEETS = False      # ひかるの方針：ゲームに出すのは、ひかるが持ってきた『権利OKと確認できた』吹き出しだけ
out = {'ppu': 46, 'k': 0.5, 'emotes': {}}; tiles = []
for k, b in (BOXES.items() if USE_AI_SHEETS else []):
    im = cut(b)
    if im is None: print('なし', k); continue
    im = im.resize((max(1, round(im.width * SC)), max(1, round(im.height * SC))), Image.BOX)
    im = tidy(im)
    tiles.append((k, im)); out['emotes'][k] = {'src': png(im), 'w': im.width, 'h': im.height}; print(k, im.size)
for k, b in (BOXES2.items() if USE_AI_SHEETS else []):
    im = cut(b, 8, A2)
    if im is None: print('なし', k); continue
    im = im.resize((max(1, round(im.width * SC)), max(1, round(im.height * SC))), Image.BOX)
    im = tidy(im)
    tiles.append((k, im)); out['emotes'][k] = {'src': png(im), 'w': im.width, 'h': im.height}; print(k, im.size)
# ---- ひかるが見つけてきた、くっきりした吹き出し（art/buddy/emote_src/）。ドット絵の大きさに縮めて使う ----
# ※ ネットで見つけた絵：商用（Steam販売）で使えるか、配布元の利用規約を確認してから公開すること
def clean(path, name, h, ncol, crop=None, bgmin=226):
    im = Image.open(path); im = im.convert('RGBA')
    if crop: im = im.crop(crop)
    a = np.array(im); H, W = a.shape[:2]
    if a[..., 3].min() < 250:       # もともと透明な背景
        fg = a[..., 3] > 128
    else:                            # 白い背景：外側から白をけずる
        mx, mn = a[..., :3].max(axis=2), a[..., :3].min(axis=2); bg = (mn >= bgmin) & (mx - mn <= 22)
        om = np.zeros((H, W), bool); q = deque()
        for x in range(W):
            for y in (0, H - 1):
                if bg[y, x]: om[y, x] = True; q.append((y, x))
        for y in range(H):
            for x in (0, W - 1):
                if bg[y, x] and not om[y, x]: om[y, x] = True; q.append((y, x))
        while q:
            cy, cx = q.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                Y, X = cy + dy, cx + dx
                if 0 <= Y < H and 0 <= X < W and bg[Y, X] and not om[Y, X]: om[Y, X] = True; q.append((Y, X))
        fg = ~om
    a[..., 3] = fg * 255; im = Image.fromarray(a, 'RGBA'); im = im.crop(im.getchannel('A').getbbox())
    w = max(1, round(im.width * h / im.height)); im = im.resize((w, h), Image.BOX)
    al = np.array(im.getchannel('A')); im.putalpha(Image.fromarray(((al > 120) * 255).astype(np.uint8)))
    q = im.convert('RGB').quantize(ncol, dither=Image.NONE).convert('RGB'); q.putalpha(im.getchannel('A'))
    tiles.append((name, q)); out['emotes'][name] = {'src': png(q), 'w': q.width, 'h': q.height}; print(name, q.size)
SRC = here.parent / 'art' / 'buddy' / 'emote_src'
clean(SRC / 'exclaim.png', 'exclaim2', 48, 6, (320, 470, 845, 1220))
clean(SRC / 'zzz2.png', 'zzzClean', 48, 5)
# zzz を、小さいZ→2つ→3つ に分ける（同じ大きさの台紙に、位置をそろえて）
_z = np.array(out_img := Image.open(io.BytesIO(base64.b64decode(out['emotes']['zzzClean']['src'].split(',')[1]))).convert('RGBA'))
_al = _z[..., 3] > 0; _lab = np.zeros(_al.shape, int); _n = 0
for _y in range(_al.shape[0]):
    for _x in range(_al.shape[1]):
        if _al[_y, _x] and not _lab[_y, _x]:
            _n += 1; _q = deque([(_y, _x)]); _lab[_y, _x] = _n
            while _q:
                _cy, _cx = _q.popleft()
                for _dy in (-1, 0, 1):
                    for _dx in (-1, 0, 1):
                        _Y, _X = _cy + _dy, _cx + _dx
                        if 0 <= _Y < _al.shape[0] and 0 <= _X < _al.shape[1] and _al[_Y, _X] and not _lab[_Y, _X]: _lab[_Y, _X] = _n; _q.append((_Y, _X))
_areas = sorted(range(1, _n + 1), key=lambda i: (_lab == i).sum())
print('Zの数', _n)
for _k in range(1, min(3, _n) + 1):
    _m = np.isin(_lab, _areas[:_k]); _im = _z.copy(); _im[..., 3] = _m * 255
    _img = Image.fromarray(_im, 'RGBA'); out['emotes'][f'zz{_k}'] = {'src': png(_img), 'w': _img.width, 'h': _img.height}; tiles.append((f'zz{_k}', _img))
clean(SRC / 'sweat.jpg', 'sweatClean', 36, 6)
clean(SRC / 'heart.png', 'heartClean', 32, 6)
clean(SRC / 'anger.jpg', 'angerClean', 36, 5)
clean(SRC / 'gloom.jpg', 'gloom', 44, 5, None, 140)       # 市松もようの背景つきの絵
clean(SRC / 'burst.jpg', 'burst', 40, 4, None, 140)
# ---- 音符（ひかる提供のドット絵：4色×4種。もとの大きさのまま）----
NS = np.array(Image.open(SRC / 'notes.png').convert('RGBA')); NH, NW = NS.shape[0] // 4, NS.shape[1] // 4
for r_ in range(4):
    for c_ in range(4):
        cell = Image.fromarray(NS[r_ * NH:(r_ + 1) * NH, c_ * NW:(c_ + 1) * NW], 'RGBA'); bb = cell.getchannel('A').getbbox()
        if not bb: continue
        cell = cell.crop(bb); nm = f'note{r_}{c_}'
        tiles.append((nm, cell)); out['emotes'][nm] = {'src': png(cell), 'w': cell.width, 'h': cell.height}
print('音符 16種')
(here / 'emotes_art.js').write_text('window.RAFT.emoteArt = ' + json.dumps(out) + ';\n')
W = sum(i.width * 6 + 10 for _, i in tiles); H = max(i.height * 6 for _, i in tiles)
sheet = Image.new('RGBA', (W, H), (40, 90, 120, 255)); x = 0
for _, i in tiles:
    sheet.alpha_composite(i.resize((i.width * 6, i.height * 6), Image.NEAREST), (x, 0)); x += i.width * 6 + 10
sheet.save('/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/emotes_sheet.png')
