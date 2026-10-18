# 料理のアイコン（ひかるの絵 art/food/dishes.png の4つ）→ dishes_art.js。湯気はコードで動かすので、切りぬかない（箱を湯気の下から始める）
import base64, io, json, pathlib, sys
from PIL import Image
here = pathlib.Path(__file__).parent; sys.path.insert(0, str(here)); import cutlib
SRC = here.parent / 'art' / 'food' / 'dishes_green.png'      # 緑の背景（白いつぶつぶのノイズつき）の絵。湯気（クリーム色）まで切りぬける
import numpy as np
key_green = cutlib.key_green
def drop_small(fg, minpx):
    seen = np.zeros_like(fg); H, W = fg.shape
    for y0, x0 in zip(*np.where(fg)):
        if seen[y0, x0]: continue
        st = [(y0, x0)]; seen[y0, x0] = True; comp = []
        while st:
            y, x = st.pop(); comp.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and fg[ny, nx] and not seen[ny, nx]: seen[ny, nx] = True; st.append((ny, nx))
        if len(comp) < minpx:
            for y, x in comp: fg[y, x] = False
    return fg
BOX = {'yakiyasai': (180, 480, 1000, 1100), 'soup': (1260, 290, 1900, 1100), 'tsukeni': (2160, 460, 3140, 1100), 'nabe': (3280, 290, 4240, 1130)}
art = {}
A, FG = key_green(SRC)
for k, (x0, y0, x1, y1) in BOX.items():
    fg = FG[y0:y1, x0:x1].copy(); fg = drop_small(fg[::2, ::2].copy(), 400)      # 間引いてから、小さいかたまりを消す
    big = np.kron(fg, np.ones((2, 2), bool)); sub = A[y0:y1, x0:x1].astype(np.uint8); big = big[:sub.shape[0], :sub.shape[1]]
    big = np.pad(big, ((0, sub.shape[0] - big.shape[0]), (0, sub.shape[1] - big.shape[1]))) if big.shape != sub.shape[:2] else big
    rgba = np.dstack([sub, (big * 255).astype(np.uint8)]); im = Image.fromarray(rgba, 'RGBA'); im = im.crop(im.getchannel('A').getbbox())
    im = im.resize((max(1, round(im.width / 6)), max(1, round(im.height / 6))), Image.LANCZOS); al = np.array(im.getchannel('A')); im.putalpha(Image.fromarray(((al > 120) * 255).astype(np.uint8)))
    px = np.array(im); e = px[..., 3] > 0; edge = e & ~np.pad(e, 1)[2:, 1:-1] | e & ~np.pad(e, 1)[:-2, 1:-1] | e & ~np.pad(e, 1)[1:-1, 2:] | e & ~np.pad(e, 1)[1:-1, :-2]      # ふちの緑がかった色を、赤と青の間に直す
    px[..., 1] = np.where(edge, np.minimum(px[..., 1], np.maximum(px[..., 0], px[..., 2])), px[..., 1]); im = Image.fromarray(px, 'RGBA')
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
    art[k] = [{'src': 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(), 'w': im.width, 'h': im.height, 'hi': True}]; print(k, im.size)
(here / 'dishes_art.js').write_text('window.RAFT.dishArt = ' + json.dumps({'art': art}) + ';\n')
