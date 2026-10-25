# 作物ごとの種袋12個（ひかるの絵 art/items/seeds_new.png：緑背景、4×3）→ seeds_art.js。持ち物・流れてくる物の絵になる
import base64, io, json, pathlib, sys
import numpy as np
from PIL import Image
here = pathlib.Path(__file__).parent; sys.path.insert(0, str(here))
import cutlib, make_chars
IDS = ['tomato', 'carrot', 'potato', 'corn', 'berry', 'melon', 'eggplant', 'cabbage', 'pepper', 'pumpkin', 'grape', 'pineapple']      # 絵の並び（左→右、上→下）
A, fg = cutlib.key_green(here.parent / 'art' / 'items' / 'seeds_new.png'); comps = make_chars.components(fg, 1500); items = []
for pts in comps:
    ys = np.array([p[0] for p in pts]); xs = np.array([p[1] for p in pts]); items.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1, pts))
assert len(items) == 12, len(items)
items.sort(key=lambda t: (t[1] + t[3]) / 2); rows = [sorted(items[i * 4:(i + 1) * 4], key=lambda t: t[0]) for i in range(3)]; seq = [t for r in rows for t in r]
art = {}; W = 96
for id, (x0, y0, x1, y1, pts) in zip(IDS, seq):
    m = np.zeros((y1 - y0, x1 - x0), bool)
    for (py, px) in pts: m[py - y0, px - x0] = True
    sub = A[y0:y1, x0:x1].astype(np.uint8).copy(); sub[..., 1] = np.minimum(sub[..., 1].astype(int), np.maximum(sub[..., 0].astype(int), sub[..., 2].astype(int)) + 12).astype(np.uint8)
    im = Image.fromarray(np.dstack([sub, (m * 255).astype(np.uint8)]), 'RGBA'); k = W / im.width
    im = im.resize((W, max(1, round(im.height * k))), Image.LANCZOS); al = np.array(im.getchannel('A')); im.putalpha(Image.fromarray(((al > 120) * 255).astype(np.uint8)))
    buf = io.BytesIO(); im.save(buf, 'WEBP', quality=90, method=6)
    art['sd_' + id] = [{'src': 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode(), 'w': im.width, 'h': im.height, 'hi': 2, 'ppu': 190}]
(here / 'seeds_art.js').write_text('window.RAFT.seedArt = ' + json.dumps({'art': art}) + ';\n')
print('seeds_art.js', (here / 'seeds_art.js').stat().st_size, [(k, v[0]['w'], v[0]['h']) for k, v in list(art.items())[:3]])
