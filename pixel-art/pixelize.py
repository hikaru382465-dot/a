#!/usr/bin/env python3
"""絵（画像生成AIの絵など）→ ドット絵に変換する道具。

使い方（例）:
  python3 pixelize.py 入力.png -o out/name --height 64 --colors 16
  python3 pixelize.py 入力.png -o out/name --height 64 --colors 20 --palette reference/mage_128x128_color_array.json
  python3 pixelize.py すでにドット絵の画像.png -o out/name --cell 4.3      # すでにドット絵の画像を、1マス=4.3pxとして元の大きさに戻す

流れ: 背景を消す → 余白を切る → 色を減らす → マス目にそろえる(各マスで多数決) → 孤立点を消す → 輪郭を足す → 保存
出力: name.png（透明）/ name_x8.png（8倍の確認用）/ name.json（見本と同じ形式）
"""
import argparse, json, math, os, sys
from collections import Counter, deque
from PIL import Image

PREV_BG = (236, 234, 225)


def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(c):
    return '#%02X%02X%02X' % tuple(c)


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


# ---------- 背景を消す ----------
def remove_bg(img, tol):
    """すでに透明があればそれを使う。なければ、ふちの色から塗りつぶしで背景を消す。"""
    img = img.convert('RGBA')
    a = img.getchannel('A')
    if a.getextrema()[0] < 250:
        return img
    w, h = img.size
    px = img.load()
    border = [px[x, 0][:3] for x in range(w)] + [px[x, h - 1][:3] for x in range(w)] + \
             [px[0, y][:3] for y in range(h)] + [px[w - 1, y][:3] for y in range(h)]
    bg = Counter(tuple(c // 8 * 8 for c in p) for p in border).most_common(1)[0][0]
    bg = tuple(c + 4 for c in bg)
    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or seen[y * w + x]:
            continue
        if dist(px[x, y][:3], bg) > tol:
            continue
        seen[y * w + x] = 1
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    out = img.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            if seen[y * w + x]:
                op[x, y] = (0, 0, 0, 0)
    return out


# ---------- 見つける：すでにドット絵のとき、マス目の大きさを探す ----------
def _edge_profile(img, axis):
    img = img.convert('RGB')
    w, h = img.size
    px = img.load()
    n = w if axis == 0 else h
    P = [0.0] * n
    step = 2
    for t in range(1, n):
        tot = 0
        for u in range(0, (h if axis == 0 else w), step):
            p = px[t, u] if axis == 0 else px[u, t]
            q = px[t - 1, u] if axis == 0 else px[u, t - 1]
            tot += abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2])
        P[t] = tot
    return P


def _grid_score(P, s, steps=10):
    n = len(P)
    mean = sum(P) / n or 1
    best = (0, 0)
    for oi in range(steps):
        o = s * oi / steps
        vals, k = [], 0
        while o + k * s < n - 1:
            x = int(round(o + k * s))
            vals.append(max(P[max(0, x - 1):x + 2]) if 0 <= x < n else 0)
            k += 1
        sc = (sum(vals) / len(vals)) / mean
        if sc > best[0]:
            best = (sc, o)
    return best


def find_offset(img, cell):
    """マス目の大きさ(cell px)がわかっているとき、ずれ(位置)を探す。"""
    img = img.convert('RGB')
    w, h = img.size
    px = img.load()
    pts = [(x, y) for y in range(0, h, 3) for x in range(0, w, 3)]
    best = None
    steps = 8
    for oxi in range(steps):
        for oyi in range(steps):
            ox, oy = cell * oxi / steps, cell * oyi / steps
            err = 0
            for x, y in pts:
                cx = int((math.floor((x - ox) / cell) + .5) * cell + ox)
                cy = int((math.floor((y - oy) / cell) + .5) * cell + oy)
                if 0 <= cx < w and 0 <= cy < h:
                    err += dist(px[x, y], px[cx, cy])
            if best is None or err < best[0]:
                best = (err, ox, oy)
    return best[1], best[2]


def from_pixelart(img, s, ox, oy):
    img = img.convert('RGBA')
    w, h = img.size
    nw, nh = int((w - ox) / s), int((h - oy) / s)
    out = Image.new('RGBA', (nw, nh))
    px, op = img.load(), out.load()
    for y in range(nh):
        for x in range(nw):
            op[x, y] = px[min(w - 1, int(ox + (x + .5) * s)), min(h - 1, int(oy + (y + .5) * s))]
    return out


# ---------- 大きい絵 → 小さいマス目 ----------
def downscale(img, tw, th, ncolors, k=4, palette=None):
    """色を減らしてから、各マスの中で多数決をとる（色がにごらない）。"""
    big = img.resize((tw * k, th * k), Image.LANCZOS)
    mask = big.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
    rgb = Image.new('RGB', big.size, (128, 128, 128))
    rgb.paste(big.convert('RGB'), (0, 0), mask)
    bgpx = mask.load()
    # 前景の平均色で背景部分をうめる（ふちに変な色がまざらないように）
    fg = [rgb.getpixel((x, y)) for y in range(0, big.height, 2) for x in range(0, big.width, 2) if bgpx[x, y]]
    if fg:
        avg = tuple(sum(c[i] for c in fg) // len(fg) for i in range(3))
        flat = Image.new('RGB', big.size, avg)
        flat.paste(rgb, (0, 0), mask)
        rgb = flat
    q = rgb.quantize(colors=max(2, ncolors - 1), method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()
    cols = [tuple(pal[i * 3:i * 3 + 3]) for i in range(len(pal) // 3) if i < max(2, ncolors - 1)]
    # 細い輪郭線の色を、いちばん暗い3%の平均から作って1色足す（色をへらすと線が消えるため）
    mp = mask.load()
    samples = sorted((rgb.getpixel((x, y)) for y in range(big.height) for x in range(big.width) if mp[x, y]), key=lum)
    dark = samples[:max(1, len(samples) // 33)]
    cols.append(tuple(sum(c[i] for c in dark) // len(dark) for i in range(3)))
    if palette:     # 指定のパレットに寄せる
        cols = [min(palette, key=lambda p: dist(p, c)) for c in cols]
    cache = {}

    dl = lum(cols[-1])

    def nearest(c):
        if c not in cache:
            # 輪郭の色に近い暗い色は、ぜんぶ輪郭の色にまとめる
            cache[c] = len(cols) - 1 if lum(c) <= dl + 35 else min(range(len(cols)), key=lambda i: dist(cols[i], c))
        return cache[c]
    out = [[None] * tw for _ in range(th)]
    for y in range(th):
        for x in range(tw):
            cnt, on = Counter(), 0
            for j in range(k):
                for i in range(k):
                    if mp[x * k + i, y * k + j]:
                        on += 1
                        cnt[nearest(rgb.getpixel((x * k + i, y * k + j)))] += 1
            if on * 2 >= k * k and cnt:
                pick = cnt.most_common(1)[0][0]
                dk = len(cols) - 1                       # 輪郭の色は、マスの3割あれば残す
                if cnt[dk] >= 0.3 * on:
                    pick = dk
                out[y][x] = cols[pick]
    return out


def tight_bbox(img):
    return img.getchannel('A').point(lambda v: 255 if v >= 128 else 0).getbbox()


# ---------- 仕上げ ----------
def despeckle(g, rounds=2):
    h, w = len(g), len(g[0])
    for _ in range(rounds):
        ch = 0
        for y in range(h):
            for x in range(w):
                c = g[y][x]
                if c is None:
                    continue
                nb = [g[y + j][x + i] for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + i < w and 0 <= y + j < h]
                if c in nb:
                    continue
                diag = [g[y + j][x + i] for i in (-1, 1) for j in (-1, 1) if 0 <= x + i < w and 0 <= y + j < h]
                if c in diag:
                    continue
                vals = [v for v in nb if v is not None]
                if len(vals) >= 3:
                    g[y][x] = Counter(vals).most_common(1)[0][0]; ch += 1
                elif len(vals) <= 1:
                    g[y][x] = None; ch += 1
        if not ch:
            break
    return g


def pad(g, n):
    w = len(g[0])
    return [[None] * (w + 2 * n) for _ in range(n)] + [[None] * n + r + [None] * n for r in g] + [[None] * (w + 2 * n) for _ in range(n)]


def outline(g, col):
    h, w = len(g), len(g[0])
    pts = [(x, y) for y in range(h) for x in range(w) if g[y][x] is None and
           any(0 <= x + i < w and 0 <= y + j < h and g[y + j][x + i] is not None for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in pts:
        g[y][x] = col
    return g


def auto_outline_color(g):
    cols = [c for r in g for c in r if c is not None]
    d = min(cols, key=lum)
    return tuple(max(0, int(v * 0.55)) for v in d)


# ---------- 保存 ----------
def save(g, base, scale=8, halo=True):
    h, w = len(g), len(g[0])
    cols = sorted({c for r in g for c in r if c is not None}, key=lambda c: -lum(c))   # 明るい→暗い
    idx = {c: i for i, c in enumerate(cols)}
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            if g[y][x] is not None:
                img.putpixel((x, y), g[y][x] + (255,))
    os.makedirs(os.path.dirname(base) or '.', exist_ok=True)
    img.save(base + '.png')
    prev = Image.new('RGBA', (w, h), PREV_BG + (255,))
    if halo:
        for y in range(h):
            for x in range(w):
                if g[y][x] is None and any(0 <= x + i < w and 0 <= y + j < h and g[y + j][x + i] is not None
                                           for i in (-1, 0, 1) for j in (-1, 0, 1)):
                    prev.putpixel((x, y), (247, 246, 230, 255))
    prev.alpha_composite(img)
    prev.resize((w * scale, h * scale), Image.NEAREST).save(base + '_x8.png')
    with open(base + '.json', 'w') as f:
        json.dump({'width': w, 'height': h, 'transparent': 255,
                   'palette': {str(i): rgb2hex(c) for i, c in enumerate(cols)},
                   'pixels': [255 if g[y][x] is None else idx[g[y][x]] for y in range(h) for x in range(w)]}, f, separators=(',', ':'))
    return len(cols)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input')
    ap.add_argument('-o', '--out', default='out/pixelized', help='出力の名前（拡張子なし）')
    ap.add_argument('--height', type=int, default=64, help='完成の高さ（マス）。--width と同時指定なら大きいほうに合わせる')
    ap.add_argument('--width', type=int)
    ap.add_argument('--colors', type=int, default=16, help='使う色の数')
    ap.add_argument('--palette', help='見本のJSON。その色だけを使う')
    ap.add_argument('--outline', default='auto', help='auto / none / #RRGGBB（外側に1マスの輪郭）')
    ap.add_argument('--bg-tol', type=float, default=40, help='背景を消す色の許す差（0〜255）')
    ap.add_argument('--no-clean', action='store_true', help='孤立点を消さない（ざらつきを残す）')
    ap.add_argument('--cell', type=float, help='すでにドット絵の画像：1マスの大きさ(px)。元の大きさに戻す')
    ap.add_argument('--canvas', type=int, help='正方形のキャンバス（例128）の下そろえ中央に置く')
    a = ap.parse_args()

    img = Image.open(a.input).convert('RGBA')
    if max(img.size) > 900 and not a.cell:
        r = 900 / max(img.size)
        img = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    img = remove_bg(img, a.bg_tol)
    bb = tight_bbox(img)
    if not bb:
        sys.exit('前景が見つかりませんでした（--bg-tol を大きくしてみてください）')
    img = img.crop(bb)
    pal = None
    if a.palette:
        d = json.load(open(a.palette))
        pal = [hex2rgb(v) for v in d['palette'].values()]

    if a.cell:
        s = a.cell
        ox, oy = find_offset(img, s)
        small = from_pixelart(img, s, ox, oy)
        g = [[(small.getpixel((x, y))[:3] if small.getpixel((x, y))[3] >= 128 else None) for x in range(small.width)] for y in range(small.height)]
    else:
        ratio = img.width / img.height
        th = a.height
        tw = max(1, round(th * ratio))
        if a.width and tw > a.width:
            tw = a.width; th = max(1, round(tw / ratio))
        g = downscale(img, tw, th, a.colors, palette=pal)
    if not a.no_clean:
        g = despeckle(g)
    if a.outline != 'none':
        col = auto_outline_color(g) if a.outline == 'auto' else hex2rgb(a.outline)
        g = outline(pad(g, 1), col)
    if a.canvas:
        h, w = len(g), len(g[0])
        if h > a.canvas or w > a.canvas:
            sys.exit(f'キャンバス{a.canvas}より絵が大きいです（{w}×{h}）。--height を小さくしてください')
        left, top = (a.canvas - w) // 2, a.canvas - h - 1
        full = [[None] * a.canvas for _ in range(a.canvas)]
        for y in range(h):
            for x in range(w):
                full[top + y][left + x] = g[y][x]
        g = full
    n = save(g, a.out)
    print(f'{len(g[0])}×{len(g)}マス / {n}色 → {a.out}.png, {a.out}_x8.png, {a.out}.json')


if __name__ == '__main__':
    main()
