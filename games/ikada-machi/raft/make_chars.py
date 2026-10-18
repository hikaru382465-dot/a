# art/chars/sheet.png（男の子・女の子の歩く絵：4方向×4コマ）を、ゲーム用に切り出して raft/chars.js に埋め込む。
# 使い方：python3 make_chars.py    （絵を差し替えたら、もう一度実行する）
import base64, io, json, pathlib
from collections import deque
import numpy as np
from PIL import Image, ImageFilter

here = pathlib.Path(__file__).parent
im = Image.open(here.parent / 'art' / 'chars' / 'sheet.png').convert('RGB')
A = np.array(im).astype(int)
BG = np.array([240, 236, 229])
TARGET_H = 44            # ゲーム内の高さ（ピクセル）。床より約3倍細かい
GRID = {'girl': (296, 8, 706, 418), 'boy': (296, 424, 706, 828)}   # 歩く絵の範囲 x0,y0,x1,y1
DIRS = ['down', 'up', 'left', 'right']

def foreground(box):
    x0, y0, x1, y1 = box; sub = A[y0:y1, x0:x1]; h, w, _ = sub.shape
    near = np.abs(sub - BG).sum(axis=2) <= 26
    near |= (sub[:, :, 2] > sub[:, :, 0] + 25) & (sub.sum(axis=2) > 330)      # 下のふちの青い背景も、背景あつかい
    seen = np.zeros((h, w), bool); q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if near[y, x] and not seen[y, x]: seen[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if near[y, x] and not seen[y, x]: seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X = y + dy, x + dx
            if 0 <= Y < h and 0 <= X < w and near[Y, X] and not seen[Y, X]: seen[Y, X] = True; q.append((Y, X))
    return ~seen

def components(fg, minpx=700):
    h, w = fg.shape; lab = np.zeros((h, w), int); n = 0; out = []
    for y in range(h):
        for x in range(w):
            if fg[y, x] and not lab[y, x]:
                n += 1; q = deque([(y, x)]); lab[y, x] = n; pts = []
                while q:
                    cy, cx = q.popleft(); pts.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            Y, X = cy + dy, cx + dx
                            if 0 <= Y < h and 0 <= X < w and fg[Y, X] and not lab[Y, X]: lab[Y, X] = n; q.append((Y, X))
                if len(pts) >= minpx: out.append(pts)
    return out

def tone_light(img):
    import colorsys
    a = np.array(img).astype(float) / 255; rgb = a[..., :3]; v = rgb.max(2); mn = rgb.min(2); s = (v - mn) / np.maximum(v, 1e-6); m = (v > 0.75) & (s < 0.5) & (a[..., 3] > 0.5)
    k = np.where(m, 1.0, 0.0)[..., None]; g = np.repeat(v[..., None], 3, 2)      # 彩度を下げ、明るさを少し下げる
    out = rgb * (1 - k) + (g + (rgb - g) * 0.8) * 0.965 * k; a[..., :3] = np.clip(out, 0, 1); return Image.fromarray((a * 255).astype(np.uint8), 'RGBA')

def build_green(path, dirs):
    """緑背景の歩く絵（4行×4コマ）。行は上から dirs の順。"""
    import sys; sys.path.insert(0, str(here)); import cutlib
    Ag, fg = cutlib.key_green(path); comps = components(fg, 600)
    items = []
    for pts in comps:
        ys = [p[0] for p in pts]; xs = [p[1] for p in pts]; items.append((min(xs), min(ys), max(xs), max(ys), pts))
    print('girl(green) components', len(items)); assert len(items) == 16, len(items)
    items.sort(key=lambda t: (t[1] + t[3]) / 2); rows = [sorted(items[i * 4:(i + 1) * 4], key=lambda t: t[0]) for i in range(4)]
    H = max(t[3] - t[1] + 1 for r in rows for t in r); scale = TARGET_H / H; res = {}
    for d, row in zip(dirs, rows):
        res[d] = []
        for (a, b, c, e, pts) in row:
            w, h = c - a + 1, e - b + 1; cell = Image.new('RGBA', (w, h), (0, 0, 0, 0)); px = cell.load()
            for (py, pxx) in pts:
                r_, g_, b_ = Ag[py, pxx]; px[pxx - a, py - b] = (r_, min(g_, max(r_, b_) + 4), b_, 255)      # ふちの緑がかった色をなおす
            cell = tone_light(cell)      # 明るい色（ずきん・服）だけ、小屋の中の相棒に合わせて、少し白く落ち着かせる
            cell.putalpha(cell.getchannel('A').filter(ImageFilter.MinFilter(3)))
            nw, nh = max(1, round(w * scale)), max(1, round(h * scale)); small = cell.resize((nw, nh), Image.LANCZOS)
            alpha = small.getchannel('A').point(lambda v: 255 if v > 110 else 0); small.putalpha(alpha)
            small = small.quantize(colors=28, method=Image.FASTOCTREE, dither=Image.NONE).convert('RGBA'); small.putalpha(alpha)
            buf = io.BytesIO(); small.save(buf, 'PNG')
            res[d].append({'src': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(), 'w': nw, 'h': nh, 'ax': round(nw / 2, 1), 'ay': nh})
    return res

def build(name):
    box = GRID[name]; fg = foreground(box); comps = components(fg)
    items = []
    for pts in comps:
        ys = [p[0] for p in pts]; xs = [p[1] for p in pts]
        items.append((min(xs), min(ys), max(xs), max(ys), pts))
    print(name, 'components', len(items))
    items.sort(key=lambda t: (t[1] + t[3]) / 2)
    rows = [sorted(items[i * 4:(i + 1) * 4], key=lambda t: t[0]) for i in range(4)]
    x0, y0, _, _ = box
    H = max(t[3] - t[1] + 1 for r in rows for t in r)
    scale = TARGET_H / H; res = {}
    for d, row in zip(DIRS, rows):
        res[d] = []
        for (a, b, c, e, pts) in row:
            w, h = c - a + 1, e - b + 1
            cell = Image.new('RGBA', (w, h), (0, 0, 0, 0)); px = cell.load()
            for (py, pxx) in pts: px[pxx - a, py - b] = tuple(A[y0 + py, x0 + pxx]) + (255,)
            cell.putalpha(cell.getchannel('A').filter(ImageFilter.MinFilter(3)))      # 背景とまざった外側1ピクセルを削る
            nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
            small = cell.resize((nw, nh), Image.LANCZOS)
            alpha = small.getchannel('A').point(lambda v: 255 if v > 110 else 0); small.putalpha(alpha)
            small = small.quantize(colors=28, method=Image.FASTOCTREE, dither=Image.NONE).convert('RGBA'); small.putalpha(alpha)
            buf = io.BytesIO(); small.save(buf, 'PNG')
            res[d].append({'src': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(), 'w': nw, 'h': nh, 'ax': round(nw / 2, 1), 'ay': nh})
    return res

if __name__ == '__main__':
    data = {'boy': build('boy'), 'girl': build_green(here.parent / 'art' / 'chars' / 'girl_walk.png', ['down', 'left', 'up', 'right']), 'ppu': 46}      # 女の子は、新しい絵（小屋の中の相棒と同じ顔）
    (here / 'chars.js').write_text('window.RAFT.charArt = ' + json.dumps(data) + ';\n', encoding='utf-8')
    print('chars.js', (here / 'chars.js').stat().st_size, 'bytes')
