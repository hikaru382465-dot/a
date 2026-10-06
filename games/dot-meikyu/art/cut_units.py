# 召喚の絵（騎士・射手）の切り出し：動き8コマ（4×2の格子）、攻撃5コマ（横1列）。 python3 art/cut_units.py
import numpy as np, os
from PIL import Image
SC = 0.5
def load(path):
    a = np.array(Image.open(path).convert('RGBA')); a[a[:, :, 3] < 40] = 0; return Image.fromarray(a)
def runs(v, m):
    out = []; s = None
    for i, x in enumerate(v):
        if x and s is None: s = i
        if not x and s is not None: out.append((s, i)); s = None
    if s is not None: out.append((s, len(v)))
    return [r for r in out if r[1] - r[0] > m]
def grid_frames(im, cols, rows):   # 等分の格子（足もとは行の下がわでそろえる）
    W = im.size[0]; out = []
    for (y0, y1) in rows:
        for c in range(cols): out.append(im.crop((int(W * c / cols), y0 - 12, int(W * (c + 1) / cols), y1 + 12)))
    return out
def row_frames(im, n):             # 中身の切れ目で切る（矢や剣がはみ出しても切れない）。足もとの中心でそろえる
    a = np.array(im)[:, :, 3] > 60; cs = runs(a.sum(0) > 2, 40); assert len(cs) == n, (len(cs), n)
    out = []
    for (x0, x1) in cs:
        sub = a[:, x0:x1]; ys = np.where(sub.any(1))[0]; y0, y1 = ys.min(), ys.max() + 1; crop = im.crop((x0, y0, x1, y1))
        low = sub[y1 - max(8, (y1 - y0) // 8):y1]; fx = np.where(low.any(0))[0]; foot = (fx.min() + fx.max()) / 2
        out.append((crop, foot))
    return out
def to_canvas(items, name):
    # items: (画像, 足の中心x) のリスト。足の中心と下がわをそろえて、同じ大きさのキャンバスに置く
    L = max(f for _, f in items); R = max(im.width - f for im, f in items); H = max(im.height for im, _ in items)
    canvas = []
    for im, f in items:
        c = Image.new('RGBA', (int(L + R) + 1, H), (0, 0, 0, 0)); c.paste(im, (int(L - f), H - im.height)); canvas.append(c)
    return finish(canvas, name)
def finish(canvas, name):
    box = None
    for c in canvas:
        b = c.getbbox(); box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    canvas = [c.crop(box).resize((int((box[2] - box[0]) * SC), int((box[3] - box[1]) * SC)), Image.LANCZOS) for c in canvas]
    for i, c in enumerate(canvas): c.save('assets/chars/%s_%d.png' % (name, i))
    sheet = Image.new('RGBA', (canvas[0].width * len(canvas), canvas[0].height), (0, 0, 0, 0))
    for i, c in enumerate(canvas): sheet.paste(c, (i * c.width, 0))
    sheet.save('assets/chars/%s_sheet.png' % name); print(name, len(canvas), canvas[0].size); return canvas
def grid_canvas(frames, name):
    h = max(f.height for f in frames); w = max(f.width for f in frames); canvas = []
    for f in frames:
        c = Image.new('RGBA', (w, h), (0, 0, 0, 0)); c.paste(f, (0, h - f.height)); canvas.append(c)
    return finish(canvas, name)
if __name__ == '__main__':
    os.makedirs('assets/chars', exist_ok=True)
    grid_canvas(grid_frames(load('assets/chatgpt/knight_walk_raw.png'), 4, [(156, 482), (552, 877)]), 'knight_walk')
    to_canvas(row_frames(load('assets/chatgpt/knight_attack_raw.png'), 5), 'knight_attack')
    grid_canvas(grid_frames(load('assets/chatgpt/archer_walk_raw.png'), 4, [(149, 476), (551, 892)]), 'archer_walk')
    to_canvas(row_frames(load('assets/chatgpt/archer_shoot_raw.png'), 5), 'archer_shoot')
