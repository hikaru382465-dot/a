# 置き物の絵（作業台・貯水槽・ろ過器）を、art/items/catalog.png から切り出して raft/objs_art.js に埋め込む。
#  背景がにじんでいるので、「ふちの黒い線」で囲まれた外側を背景として消す。
# 使い方：python3 make_objs.py
import base64, io, json, pathlib
from collections import deque
import numpy as np
from PIL import Image

here = pathlib.Path(__file__).parent
cat = Image.open(here.parent / 'art' / 'items' / 'catalog.png').convert('RGB')
A_unused = None
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
    img = img.resize((max(1, round(img.width / (shrink or SHRINK))), max(1, round(img.height / (shrink or SHRINK)))), Image.NEAREST)
    al = np.array(img.getchannel('A')); img.putalpha(Image.fromarray(((al > 110) * 255).astype(np.uint8)))
    # 色数をへらして、ドット絵っぽくそろえる
    return img      # 色はへらさない（元の色のまま）

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

def dried_tint(im):     # 銀色の魚を、干物の茶色にぬりかえる
    a = np.array(im).astype(float); L = a[..., :3].mean(axis=2) / 255.0
    lo, hi = np.array([60, 40, 30.0]), np.array([214, 168, 112.0]); t = np.clip((L - 0.1) / 0.75, 0, 1)[..., None]
    a[..., :3] = lo * (1 - t) + hi * t; return Image.fromarray(a.astype(np.uint8), 'RGBA')

def icon(box, shrink=3, tint=None):
    im = cutout(box, shrink=shrink)
    if tint: im = tint(im)
    e = entry(im); e['ppu'] = round(max(im.size) / 0.5); return e
icons = {'wood': [icon((38, 28, 142, 118))], 'floor': [icon((142, 28, 246, 118))], 'cloth': [icon((712, 36, 790, 118))],
         'fish': [icon((26, 136, 136, 208))], 'hammer': [icon((238, 238, 324, 344))], 'net': [icon((1066, 240, 1184, 342))], 'rod': [icon((410, 232, 500, 344), shrink=2)],
         'iron': [icon((628, 30, 700, 112))], 'grilled': [icon((136, 136, 232, 210))], 'campfire': [icon((940, 618, 1028, 702), shrink=3)], 'seat': [icon((1318, 470, 1396, 594), shrink=3)], 'lamp': [icon((1398, 458, 1438, 586), shrink=2)], 'dried': [icon((26, 136, 136, 208), tint=dried_tint)],
         'rack': [icon((364, 476, 482, 596), shrink=3)], 'oven': [icon((152, 474, 252, 572), shrink=3)], 'crate': [icon((832, 492, 912, 570), shrink=3)], 'chest': [icon((726, 492, 820, 570), shrink=3)], 'plot': [icon((26, 618, 134, 700), shrink=3)],  'clay': [icon((438, 32, 524, 118), tint=clay_tint)]}
for n, e in list(icons.items()):
    im = Image.open(io.BytesIO(base64.b64decode(e[0]['src'].split(',')[1]))).convert('RGBA'); print(n, im.size, e[0]['ppu'])
    bg = Image.new('RGBA', (im.width * 5, im.height * 5), (40, 90, 120, 255)); bg.alpha_composite(im.resize((im.width * 5, im.height * 5), Image.NEAREST)); bg.save(f'/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/ic_{n}.png')
def _dil(b, n):
    out = b.copy()
    for _ in range(n):
        p = np.pad(out, 1); out = p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return out
def plane_cut(box, shrink=2, seal=0):
    """背景がぼやけた光の輪になっている絵用：外のふちから背景を平面でフィットして、ちがう所だけを残す。"""
    a = np.array(cat.crop(box)).astype(float); h, w = a.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]; edge = np.zeros((h, w), bool); edge[:6, :] = edge[-6:, :] = True; edge[:, :6] = edge[:, -6:] = True
    X = np.c_[xs[edge], ys[edge], np.ones(edge.sum())]; bgm = np.zeros_like(a)
    for ch in range(3):
        co = np.linalg.lstsq(X, a[..., ch][edge], rcond=None)[0]; bgm[..., ch] = co[0] * xs + co[1] * ys + co[2]
    d = np.sqrt(((a - bgm) ** 2).sum(axis=2)); m = d > 30
    # 光の輪（なめらかで、灰色っぽい）をのぞく
    L = a.mean(axis=2); mx, mn = a.max(axis=2), a.min(axis=2)
    pad = np.pad(L, 1, mode='edge'); stack = np.stack([pad[dy:dy + h, dx:dx + w] for dy in range(3) for dx in range(3)]); sd = stack.std(axis=0)
    halo = (mx - mn < 45) & (L > 60) & (L < 170) & (sd < 7)
    m &= ~halo
    m0 = m; m = _dil(m, seal) if seal else m
    om = np.zeros((h, w), bool); q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not m[y, x]: om[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if not m[y, x] and not om[y, x]: om[y, x] = True; q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X2 = cy + dy, cx + dx
            if 0 <= Y < h and 0 <= X2 < w and not m[Y, X2] and not om[Y, X2]: om[Y, X2] = True; q.append((Y, X2))
    fg = ~om
    if seal: fg &= ~(_dil(om, seal) & ~m0)
    lab = np.zeros((h, w), int); best = (0, 0); n = 0
    for y in range(h):
        for x in range(w):
            if fg[y, x] and not lab[y, x]:
                n += 1; lab[y, x] = n; qq = deque([(y, x)]); cnt = 0
                while qq:
                    cy, cx = qq.popleft(); cnt += 1
                    for dy in (-2, -1, 0, 1, 2):
                        for dx in (-2, -1, 0, 1, 2):
                            Y, X2 = cy + dy, cx + dx
                            if 0 <= Y < h and 0 <= X2 < w and fg[Y, X2] and not lab[Y, X2]: lab[Y, X2] = n; qq.append((Y, X2))
                if cnt > best[0]: best = (cnt, n)
    fg = lab == best[1]
    img = Image.fromarray(np.dstack([a.astype(np.uint8), (fg * 255).astype(np.uint8)]), 'RGBA'); img = img.crop(img.getchannel('A').getbbox())
    img = img.resize((max(1, round(img.width / shrink)), max(1, round(img.height / shrink))), Image.NEAREST)
    al = np.array(img.getchannel('A')); img.putalpha(Image.fromarray(((al > 110) * 255).astype(np.uint8)))
    return img      # 色はへらさない
import cutlib
HI = 1      # 新しいシートの切り出しは、縮めずに元の細かさで（ゲームでは、なめらかに縮めて出す）
C2 = here.parent / 'art' / 'items' / 'catalog2.png'
for _k, _b in (('oven', (448, 704, 552, 812)), ('crate', (558, 700, 662, 808)), ('chest', (18, 700, 138, 806)), ('barrel', (140, 704, 236, 800)), ('bed', (1190, 730, 1292, 820)), ('shelf', (1290, 696, 1388, 822)), ('windmill', (1386, 696, 1462, 830)), ('hut', (20, 816, 190, 968)), ('rack', (668, 700, 790, 820)), ('plot', (488, 590, 596, 672))):      # 新しい絵シート（catalog2）から
    icons[_k] = [entry(cutlib.cut_checker(C2, _b, shrink=HI))]; icons[_k][0]['hi'] = 3 // HI; icons[_k][0]['ppu'] = round(max(icons[_k][0]['w'], icons[_k][0]['h']) / 0.62)
    _im = Image.open(io.BytesIO(base64.b64decode(icons[_k][0]['src'].split(',')[1]))).convert('RGBA'); print(_k, _im.size); _bg = Image.new('RGBA', (_im.width * 5, _im.height * 5), (40, 90, 120, 255)); _bg.alpha_composite(_im.resize((_im.width * 5, _im.height * 5), Image.NEAREST)); _bg.save(f'/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/ic_{_k}.png')
# アイテムの絵（持ち物・漂流物）も、新しいシートから縮めずに切り出す
C3 = here.parent / 'art' / 'items' / 'catalog3.png'
for _k, _b, _bl, _src in (('seed', (26, 744, 94, 822), None, 'C3'), ('veg', (30, 455, 102, 535), None, 'C2'), ('wood', (1024, 324, 1126, 426), (84, 72), 'C2'), ('floor', (1100, 346, 1196, 434), None, 'C2'), ('fish', (22, 56, 134, 126), None, 'C2'), ('grilled', (1392, 370, 1514, 446), None, 'C2'), ('lamp', (1458, 702, 1512, 812), None, 'C2')):
    _im = cutlib.cut_checker(C3 if _src == 'C3' else C2, _b, shrink=1, blank=_bl); icons[_k] = [entry(_im)]; icons[_k][0]['hi'] = 1; icons[_k][0]['ppu'] = round(max(_im.size) / (0.5 if _k not in ('lamp',) else 1.0))
    if _k == 'fish':
        _d = dried_tint(_im); icons['dried'] = [entry(_d)]; icons['dried'][0]['hi'] = 1; icons['dried'][0]['ppu'] = round(max(_d.size) / 0.5)
_boat = plane_cut((398, 712, 648, 866)); icons['boat'] = [entry(_boat)]; icons['boat'][0]['ppu'] = 52
# 作業台・貯水槽・ろ過器（真水器）も、新しい絵シートから縮めずに切る（ほかの置き物と絵のタッチをそろえる）
_CD = here.parent / 'art' / 'items' / 'catalog_dark.png'
bench2 = cutlib.cut_checker(C2, (930, 720, 1050, 830), shrink=1)
tank2 = cutlib.cut_checker(C2, (244, 694, 344, 816), shrink=1, pocket=900, fringe=3, pocket_min=12)
frame2 = cutlib.cut_plane(_CD, (716, 880, 792, 980), shrink=1, thr=46)
def _drip2(img, on):
    a = np.array(img).copy()
    if on:
        h, w = a.shape[:2]
        for dy, c in ((1, (140, 205, 245)), (3, (180, 225, 250))): a[h - 1 - dy, w // 2 + 1] = (*c, 255)
    return Image.fromarray(a, 'RGBA')
def _loopclear(im):      # 投網のロープの輪の中の、白い背景を消す
    a = np.array(im); h, w = a.shape[:2]; sub = a[20:60, 140:w]
    white = (sub[..., :3].min(axis=2) > 205) & ((sub[..., :3].max(axis=2) - sub[..., :3].min(axis=2)) < 28)
    sub[..., 3] = np.where(white, 0, sub[..., 3]); a[20:60, 140:w] = sub; return Image.fromarray(a, 'RGBA')
def _hi(e): e['hi'] = 3; return e
out = {'ppu': 40, 'icons': icons, 'bench': [_hi(entry(bench2))], 'tank': [_hi(entry(tank_level(tank2, l))) for l in range(4)], 'filter': [_hi(entry(_drip2(frame2, 0))), _hi(entry(_drip2(frame2, 1)))]}
_nt = _loopclear(cutlib.cut_checker(here.parent / 'art' / 'items' / 'catalog3.png', (556, 386, 746, 566), shrink=1)); out['icons']['net'] = [_hi(entry(_nt))]; out['icons']['net'][0]['ppu'] = round(max(_nt.size) / 0.62)      # 投網（持ち物・手にもつ絵）
out['campfire'] = out['icons']['campfire']; out['seat'] = out['icons']['seat']; out['lamp'] = out['icons']['lamp']
for _k in ('rack', 'oven', 'crate', 'chest', 'plot', 'barrel', 'bed', 'shelf', 'windmill', 'hut'): out[_k] = out['icons'][_k]
# 小屋の「夜」の絵（窓に明かり）：昼の絵と同じ大きさにそろえる。夜は2コマ目に切りかえる（objects.js）
_hd = Image.open(io.BytesIO(base64.b64decode(out['hut'][0]['src'].split(',')[1]))).convert('RGBA')
_hn = cutlib.cut_checker(here.parent / 'art' / 'hut' / 'night_src.png', (120, 140, 830, 790), shrink=1, pocket=3000, fringe=2, pocket_min=60).resize(_hd.size, Image.BOX)
_en = entry(_hn); _en['hi'] = 3; _en['ppu'] = out['hut'][0].get('ppu'); out['hut'] = [out['hut'][0], _en]
# 小屋の見た目ちがい（ひかるの絵：緑背景。昼と夜が左右に並んだ組を、ならべた絵）。hut の配列は [昼0, 夜0, 昼1, 夜1, …]。見た目の番号は、置いた物の hv
def _hut_pairs(path, W=200, fix=False):
    import make_chars
    A, fg = cutlib.key_green(path); comps = make_chars.components(fg, 3000); items = []
    for pts in comps:
        ys = np.array([p[0] for p in pts]); xs = np.array([p[1] for p in pts]); items.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1, pts))
    items.sort(key=lambda t: (t[1] + t[3]) / 2); rows = []; last = None
    for t in items:
        cy = (t[1] + t[3]) / 2
        if last is None or cy - last > 100: rows.append([])
        rows[-1].append(t); last = cy
    seq = [t for r in rows for t in sorted(r, key=lambda q: q[0])]; assert len(seq) % 2 == 0, len(seq)
    med = float(np.median([t[2] - t[0] for t in seq])); k = W / med      # 1枚の絵の中で、同じ倍率にする（家の高さのちがいは、そのまま）
    def img(t):
        x0, y0, x1, y1, pts = t; m = np.zeros((y1 - y0, x1 - x0), bool)
        for (py, px) in pts: m[py - y0, px - x0] = True
        sub = A[y0:y1, x0:x1].astype(np.uint8).copy(); r_, g_, b_ = sub[..., 0].astype(int), sub[..., 1].astype(int), sub[..., 2].astype(int)
        sub[..., 1] = np.minimum(g_, np.maximum(r_, b_) + 4)      # ふちの緑をなおす
        return Image.fromarray(np.dstack([sub, (m * 255).astype(np.uint8)]), 'RGBA')
    outs = []
    for i in range(0, len(seq), 2):
        d, n = img(seq[i]), img(seq[i + 1]); kk = k
        if fix and d.width < 0.8 * med: kk = k * 0.9 * med / d.width      # 小さく描かれた家は、ほかと同じくらいの大きさに拡大する
        sz = (max(1, round(d.width * kk)), max(1, round(d.height * kk))); pair = []
        for im in (d, n):
            im = im.resize(sz, Image.LANCZOS); al = np.array(im.getchannel('A')); im.putalpha(Image.fromarray(((al > 120) * 255).astype(np.uint8)))
            buf = io.BytesIO(); im.save(buf, 'WEBP', quality=90, method=6)
            pair.append({'src': 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode(), 'w': im.width, 'h': im.height, 'hi': W / 151 * 3})
        outs += pair
    return outs
_vh = []
for _f in ('hut_wood.png', 'hut_stone.png'):      # 1枚に昼と夜の1組だけ
    _p = _hut_pairs(here.parent / 'art' / 'hut' / _f); _vh += _p
for _f in ('huts_sheet1.png', 'huts_sheet2.png', 'huts_sheet3_wood.png', 'huts_sheet4_sea.png'): _vh += _hut_pairs(here.parent / 'art' / 'hut' / _f)
_vh += _hut_pairs(here.parent / 'art' / 'hut' / 'huts_sheet5_snow.png', fix=True)
out['hut'] = out['hut'] + _vh
# 回収ネット（ひかるの絵：緑背景。左から、空・物入り・やぶれ）。3枚を同じ大きさの枠にそろえて、下はしを合わせる
def _catchnet(path, W=120):
    A, fg = cutlib.key_green(path); H0, W0 = fg.shape; ims = []
    for i in range(3):
        x0, x1 = i * W0 // 3, (i + 1) * W0 // 3; m = fg[:, x0:x1].copy()
        ys, xs = np.where(m); keep = np.zeros_like(m)
        big = np.zeros_like(m); lab = None
        keep = m      # やぶれの小さなかけらも残す
        ys, xs = np.where(keep); b = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        sub = A[:, x0:x1].astype(np.uint8).copy(); sub[..., 1] = np.minimum(sub[..., 1].astype(int), np.maximum(sub[..., 0].astype(int), sub[..., 2].astype(int)) + 12).astype(np.uint8)
        ims.append((Image.fromarray(np.dstack([sub, (keep * 255).astype(np.uint8)]), 'RGBA'), b))
    L = min(b[0] for _, b in ims); T = min(b[1] for _, b in ims); R_ = max(b[2] for _, b in ims); B = max(b[3] for _, b in ims)
    k = W / (R_ - L); outs = []
    for im, b in ims:
        im = im.crop((L, T, R_, B)); im = im.resize((W, max(1, round(im.height * k))), Image.LANCZOS); al = np.array(im.getchannel('A')); im.putalpha(Image.fromarray(((al > 120) * 255).astype(np.uint8)))
        buf = io.BytesIO(); im.save(buf, 'WEBP', quality=90, method=6); outs.append({'src': 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode(), 'w': im.width, 'h': im.height, 'hi': 3})
    return outs
_cn = _catchnet(here.parent / 'art' / 'items' / 'catchnet.png')
out['catchnet'] = _cn; out['icons']['catchnet'] = [_cn[1]]
print('小屋の見た目', len(out['hut']) // 2, '種類（わら含む）')
assert len(out['hut']) // 2 == 54, len(out['hut']) // 2      # data.js の HUT_N と同じにする
out['icons']['hutw'] = [_vh[0]]; out['icons']['huts'] = [_vh[2]]; out['hutw'] = out['icons']['hutw']; out['huts'] = out['icons']['huts']
# 小屋の中の絵（入ったときに出す）と、ベッドで足パタパタの8コマ：別ファイル hut_art.js（部屋の絵の上に、%の位置で重ねる）
_ti = cutlib.cut_checker(here.parent / 'art' / 'hut' / 'interior2.png', (0, 0, 1536, 1024), shrink=1, trim=False); _bx = _ti.getchannel('A').getbbox(); _ti = _ti.crop(_bx); IW, IH = _ti.size      # 余白は切りおとす（ベッドの位置は、この切りおとし分をひく）
_ti2 = _ti.resize((IW // 2, IH // 2), Image.BOX); _bf = io.BytesIO(); _ti2.save(_bf, 'PNG', optimize=True)
_runs = [(116, 417), (652, 955), (1180, 1519), (1681, 2021), (2250, 2553), (2786, 3093), (3320, 3621), (3860, 4157)]      # 相棒だけ（ベッドなし）の足パタパタ。ベッドは部屋の絵の1枚のまま
_fr = [cutlib.cut_checker(here.parent / 'art' / 'hut' / 'girl_sheet.png', ((a + b) // 2 - 210, 420, (a + b) // 2 + 210, 1000), shrink=1, fringe=1, trim=False, bgthr=(238, 14), seam=True) for a, b in _runs]
def _peel(f, n=4, lo=200, sat=40):      # ふちに残った白っぽい背景を、外から内へ数ピクセルだけはがす（目のハイライトは中なので残る）
    import numpy as _np
    a = _np.array(f); al = a[..., 3] > 128
    for _ in range(n):
        near = _np.zeros_like(al)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)): near |= ~_np.roll(_np.roll(al, dy, 0), dx, 1)
        rgb = a[..., :3].astype(int); lt = (rgb.min(2) >= lo) & (rgb.max(2) - rgb.min(2) <= sat)
        kill = al & near & lt; al &= ~kill
    a[..., 3] = _np.where(al, a[..., 3], 0); return Image.fromarray(a, 'RGBA')
def _specks(f, r=16, lo=185, minpx=60):      # 外にぽつんと近い白い点と、そのまわりの小さなかけらを消す
    import numpy as _np
    a = _np.array(f); al = a[..., 3] > 128
    out = ~al
    for _ in range(r):
        o2 = out.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1): o2 |= _np.roll(_np.roll(out, dy, 0), dx, 1)
        out = o2
    rgb = a[..., :3].astype(int); lt = (rgb.min(2) >= lo) & (rgb.max(2) - rgb.min(2) <= 45)
    h = a.shape[0]; reg = _np.zeros_like(al); reg[int(h * 0.2):int(h * 0.6), int(a.shape[1] * 0.5):] = True
    al &= ~(out & lt & reg)
    seen = _np.zeros_like(al)
    for y, x in zip(*_np.where(al)):
        if seen[y, x]: continue
        st = [(y, x)]; seen[y, x] = True; comp = []
        while st:
            cy, cx = st.pop(); comp.append((cy, cx))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < al.shape[0] and 0 <= nx < al.shape[1] and al[ny, nx] and not seen[ny, nx]: seen[ny, nx] = True; st.append((ny, nx))
        if len(comp) < minpx:
            for cy, cx in comp: al[cy, cx] = False
    a[..., 3] = _np.where(al, a[..., 3], 0); return Image.fromarray(a, 'RGBA')
_fr = [_specks(_peel(f)) for f in _fr]
def _align(frames, top=0.36):      # コマごとのずれを、頭・体の上の部分の「重さの中心」をそろえて直す（足は動いてよいので、見ない）
    import numpy as _np
    def cen(f):
        a = _np.array(f.getchannel('A')) > 128; h = a.shape[0]; ys, xs = _np.where(a[:int(h * top)]); return xs.mean(), ys.mean()
    cx0, cy0 = cen(frames[0]); out = [frames[0]]
    for f in frames[1:]:
        cx, cy = cen(f); dx, dy = int(round(cx0 - cx)), int(round(cy0 - cy)); a = _np.array(f)
        out.append(Image.fromarray(_np.roll(_np.roll(a, dy, 0), dx, 1), 'RGBA'))
    return out
_fr = _align(_fr)
_bb = None
for _f in _fr:
    _b = _f.getchannel('A').getbbox(); _bb = _b if _bb is None else (min(_bb[0], _b[0]), min(_bb[1], _b[1]), max(_bb[2], _b[2]), max(_bb[3], _b[3]))
_fr = [_f.crop(_bb) for _f in _fr]; _S, _OX, _OY = 0.62, 335 - _bx[0], 306 - _bx[1]       # 部屋のベッドの上にのせる大きさと位置（元の絵の画素）
_frs = []
for _f in _fr:
    _g = _f.resize((int(_f.width * _S / 2), int(_f.height * _S / 2)), Image.NEAREST); _gb = io.BytesIO(); _g.save(_gb, 'PNG', optimize=True)
    _frs.append('data:image/png;base64,' + base64.b64encode(_gb.getvalue()).decode())
_gw, _gh = int(_fr[0].width * _S), int(_fr[0].height * _S)
(here / 'hut_art.js').write_text('window.RAFT.hutArt = ' + json.dumps({'interior': 'data:image/png;base64,' + base64.b64encode(_bf.getvalue()).decode(), 'w': IW // 2, 'h': IH // 2, 'bed': {'frames': _frs, 'x': _OX / IW * 100, 'y': _OY / IH * 100, 'w': _gw / IW * 100, 'h': _gh / IH * 100}}) + ';\n', encoding='utf-8')
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
        return img
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
