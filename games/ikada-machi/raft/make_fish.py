# 魚の図鑑の絵：新しい絵シート（art/items/catalog2.png）から、縮めずに切り出して fish_art.js にする。使い方：python3 make_fish.py
import base64, io, json, pathlib
from PIL import Image
import cutlib
here = pathlib.Path(__file__).parent
C2 = here.parent / 'art' / 'items' / 'catalog2.png'
# 魚のid: 切り出し範囲（左, 上, 右, 下）
BOX = {
    'iwashi': (22, 56, 134, 126), 'aji': (134, 60, 254, 130), 'saba': (260, 56, 388, 132), 'tai': (396, 52, 514, 136), 'masu': (518, 52, 642, 128),
    'unagi': (640, 44, 800, 126), 'kurage': (36, 148, 124, 248), 'ei': (140, 152, 250, 222), 'maguro': (258, 154, 434, 240), 'kajiki': (448, 148, 650, 248),
    'hamachi': (650, 172, 780, 242), 'ika': (790, 40, 842, 118), 'tako': (843, 44, 940, 138), 'ebi': (952, 50, 1074, 142), 'kani': (1086, 44, 1234, 146),
    'hirame': (782, 172, 908, 240), 'kasago': (926, 164, 1056, 244), 'iseebi': (1056, 164, 1130, 262), 'fugu': (1136, 166, 1204, 238),
}
SHRINK = 1.5      # 1なら元の細かさ（約510KB）。1.5は約230KB
out = {}; ims = {}
for k, box in BOX.items():
    im = cutlib.cut_checker(C2, box, shrink=SHRINK); ims[k] = im
    buf = io.BytesIO(); im.save(buf, 'PNG', optimize=True)
    out[k] = {'src': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(), 'w': im.width, 'h': im.height}
    print(k, im.size, len(buf.getvalue()))
(here / 'fish_art.js').write_text('window.RAFT.fishArt = ' + json.dumps(out) + ';\n', encoding='utf-8')
print('fish_art.js', (here / 'fish_art.js').stat().st_size, 'bytes')
# 確かめ用の見本（青い背景）
W = 6; cols = 5; cw = max(i.width for i in ims.values()) + 8; ch = max(i.height for i in ims.values()) + 8
rows = (len(ims) + cols - 1) // cols; sheet = Image.new('RGBA', (cw * cols, ch * rows), (40, 120, 170, 255))
for n, (k, im) in enumerate(ims.items()): sheet.alpha_composite(im, ((n % cols) * cw + 4, (n // cols) * ch + 4))
sheet.convert('RGB').save('/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/fish_sheet.png')
