# ChatGPTの狼（走り8コマ・かみつき5コマ）を切り出し、大きさと足もとをそろえて assets/chars/ に保存。 python3 art/cut_wolf.py
import numpy as np, os
from PIL import Image
SC = 0.5
def clean(im):
    a = np.array(im); al = a[:, :, 3]; a[al < 40] = 0; return Image.fromarray(a)
def cells(path, cols, rows):
    im = clean(Image.open(path).convert('RGBA')); W, H = im.size; out = []
    for (y0, y1) in rows:
        for c in range(cols):
            x0, x1 = int(W * c / cols), int(W * (c + 1) / cols); out.append((im.crop((x0, y0 - 12, x1, y1 + 12)), y1 + 12 - (y0 - 12)))
    return out
def build(frames, name):
    h = max(f.height for f, _ in frames); w = max(f.width for f, _ in frames)
    canvas = []
    for f, _ in frames:
        c = Image.new('RGBA', (w, h), (0, 0, 0, 0)); c.paste(f, (0, h - f.height)); canvas.append(c)
    # 全コマの合わせた外わく
    box = None
    for c in canvas:
        b = c.getbbox(); box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    canvas = [c.crop(box).resize((int((box[2] - box[0]) * SC), int((box[3] - box[1]) * SC)), Image.LANCZOS) for c in canvas]
    os.makedirs('assets/chars', exist_ok=True)
    for i, c in enumerate(canvas): c.save('assets/chars/%s_%d.png' % (name, i))
    sheet = Image.new('RGBA', (canvas[0].width * len(canvas), canvas[0].height), (0, 0, 0, 0))
    for i, c in enumerate(canvas): sheet.paste(c, (i * c.width, 0))
    sheet.save('assets/chars/%s_sheet.png' % name); print(name, len(canvas), canvas[0].size); return canvas
run = build(cells('assets/chatgpt/wolf_run_raw.png', 4, [(282, 510), (613, 848)]), 'wolf_run')
bite = build(cells('assets/chatgpt/wolf_bite_raw.png', 5, [(217, 545)]), 'wolf_bite')
