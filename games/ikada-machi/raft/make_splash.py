# 水しぶきのアニメ（20コマ・5×4）を、art/items/splash.png から切り出して raft/splash_art.js に埋め込む。
#  1〜10コマ：大きなしぶき（釣りの着水・つりあげ）／11〜20コマ：弱いしぶきと波紋（漂流物のさざ波）
# 使い方：python3 make_splash.py
import base64, io, json, pathlib
from PIL import Image
here = pathlib.Path(__file__).parent
im = Image.open(here.parent / 'art' / 'items' / 'splash.png').convert('RGBA')
CW, CH = im.width // 5, im.height // 4
frames = []
for r in range(4):
    for c in range(5):
        cell = im.crop((c * CW, r * CH, (c + 1) * CW, (r + 1) * CH)); buf = io.BytesIO(); cell.save(buf, 'PNG')
        frames.append('data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode())
out = {'w': CW, 'h': CH, 'ax': CW // 2, 'ay': 56, 'ppu': 72, 'frames': frames}
(here / 'splash_art.js').write_text('window.RAFT.splashArt = ' + json.dumps(out) + ';\n')
print(CW, CH, len(frames), sum(len(f) for f in frames) // 1024, 'KB')
