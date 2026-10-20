# 住人の歩く絵（art/res/<id>_walk.png：緑背景、4行＝前・左・後ろ・右 × 4コマ）→ res_art.js
# 絵が届いたら、RES に id を足して、もう一度実行する。顔の絵 art/res/<id>_face.png があれば、face も入れる
import base64, io, json, pathlib, sys
here = pathlib.Path(__file__).parent; sys.path.insert(0, str(here))
import make_chars
RES = ['toto', 'mina', 'kuro', 'pipi']
import numpy as np
from PIL import Image
import cutlib
def cut_faces(path):
    A, fg = cutlib.key_green(path); comps = make_chars.components(fg, 2000)
    assert len(comps) == 2, len(comps)
    boxes = []
    for pts in comps:
        ys = [p[0] for p in pts]; xs = [p[1] for p in pts]; boxes.append((min(xs), min(ys), max(xs), max(ys), pts))
    boxes.sort(key=lambda t: t[0]); res = []
    for (x0, y0, x1, y1, pts) in boxes:
        cell = np.zeros((y1 - y0 + 1, x1 - x0 + 1, 4), np.uint8)
        for (py, px) in pts:
            r, g, b = A[py, px]; cell[py - y0, px - x0] = (r, min(g, max(r, b) + 4), b, 255)      # ふちの緑をなおす
        im = Image.fromarray(cell, 'RGBA'); im = im.resize((round(im.width * 0.4), round(im.height * 0.4)), Image.LANCZOS)
        al = np.array(im.getchannel('A')); im.putalpha(Image.fromarray(((al > 120) * 255).astype(np.uint8)))
        b = io.BytesIO(); im.save(b, 'WEBP', quality=90, method=6); res.append('data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode())
    return res
out = {}
for id in RES:
    p = here.parent / 'art' / 'res' / f'{id}_walk.png'
    if not p.exists(): continue
    out[id] = make_chars.build_green(p, ['down', 'left', 'up', 'right'], tone=False)
    f = here.parent / 'art' / 'res' / f'{id}_face.png'
    if f.exists(): out[id]['faces'] = cut_faces(f)      # 顔の絵：左＝ふつう、右＝にっこり
(here / 'res_art.js').write_text('window.RAFT.resArt = ' + json.dumps(out) + ';\n', encoding='utf-8')
print('res_art.js', list(out), (here / 'res_art.js').stat().st_size)
