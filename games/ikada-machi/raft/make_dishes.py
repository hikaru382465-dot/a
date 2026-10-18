# 料理のアイコン（ひかるの絵 art/food/dishes.png の4つ）→ dishes_art.js。湯気はコードで動かすので、切りぬかない（箱を湯気の下から始める）
import base64, io, json, pathlib, sys
from PIL import Image
here = pathlib.Path(__file__).parent; sys.path.insert(0, str(here)); import cutlib
SRC = here.parent / 'art' / 'food' / 'dishes.png'
BOX = {'yakiyasai': (90, 255, 495, 545), 'soup': (640, 272, 945, 548), 'tsukeni': (1085, 240, 1558, 548), 'nabe': (1655, 226, 2108, 565)}
art = {}
for k, box in BOX.items():
    im = cutlib.cut_checker(SRC, box, shrink=3, fringe=1, bgthr=(232, 16)); b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
    art[k] = [{'src': 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(), 'w': im.width, 'h': im.height, 'hi': True}]; print(k, im.size)
(here / 'dishes_art.js').write_text('window.RAFT.dishArt = ' + json.dumps({'art': art}) + ';\n')
