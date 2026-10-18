# 相棒の表情（ひかるの絵 art/face/faces.png の6つ）→ faces_art.js。まばたきは、眠い顔の目を、ふつう・さびしい・おどろきの顔に合成して作る
import base64, io, json, pathlib, sys
from PIL import Image, ImageFilter
here = pathlib.Path(__file__).parent; sys.path.insert(0, str(here)); import cutlib
fr = [cutlib.cut_checker(here.parent / 'art' / 'face' / 'faces.png', (10 + 360 * i - 5, 150, 10 + 360 * i + 345, 560), shrink=1, fringe=1, trim=False, bgthr=(238, 14), seam=True) for i in range(6)]
BOX = (148, 188, 282, 230)
def clean(f):      # 右の髪のすきまに残った、白い背景の切れはし（まわりが暗い線で囲まれて、つながらず残る）を消す
    import numpy as np
    a = np.array(f); rgb = a[..., :3].astype(int); lt = (rgb.min(2) >= 195) & (rgb.max(2) - rgb.min(2) <= 55); reg = np.zeros(lt.shape, bool); reg[165:305, 262:] = True
    a[..., 3] = np.where(lt & reg, 0, a[..., 3]); return Image.fromarray(a, 'RGBA')
fr = [clean(f) for f in fr]
def blink(base, src):
    m = Image.new('L', base.size, 0); m.paste(255, BOX); m = m.filter(ImageFilter.GaussianBlur(2)); o = base.copy(); o.paste(src, (0, 0), m); return o
names = ['normal', 'smile', 'happy', 'sad', 'surprise', 'sleepy']
imgs = {n: f for n, f in zip(names, fr)}
for n in ('normal', 'sad', 'surprise'): imgs[n + '_blink'] = blink(imgs[n], imgs['sleepy'])
bb = None
for f in imgs.values():
    b = f.getchannel('A').getbbox(); bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
out = {}
for n, f in imgs.items():
    g = f.crop(bb); g = g.resize((g.width // 2, g.height // 2), Image.LANCZOS); b = io.BytesIO(); g.save(b, 'WEBP', quality=88, method=6); out[n] = 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()
(here / 'faces_art.js').write_text('window.RAFT.faces = ' + json.dumps({'w': (bb[2] - bb[0]) // 2, 'h': (bb[3] - bb[1]) // 2, 'img': out}) + ';\n')
print('faces', len(out), bb)
