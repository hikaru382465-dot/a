# 置き物の絵（作業台・貯水槽・ろ過器）を、art/items/catalog.png から切り出して raft/objs_art.js に埋め込む。
#  背景がにじんでいるので、「ふちの黒い線」で囲まれた外側を背景として消す。
# 使い方：python3 make_objs.py
import base64, io, json, pathlib
from collections import deque
import numpy as np
from PIL import Image

here = pathlib.Path(__file__).parent
cat = Image.open(here.parent / 'art' / 'items' / 'catalog.png').convert('RGB')
SHRINK = 4

def png(img):
    buf = io.BytesIO(); img.save(buf, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

def cutout(box, dark=48):
    x0, y0, x1, y1 = box; sub = cat.crop(box); a = np.array(sub).astype(int); h, w = a.shape[:2]
    luma = a.sum(axis=2) / 3
    wall0 = luma < dark                     # 黒い線
    wall = wall0.copy()
    for _ in range(2):                      # 線のすきまをふさぐ（2ドットぶん太らせる）
        wall = wall | np.roll(wall, 1, 0) | np.roll(wall, -1, 0) | np.roll(wall, 1, 1) | np.roll(wall, -1, 1)
    seen = np.zeros((h, w), bool); q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not wall[y, x]: seen[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if not wall[y, x] and not seen[y, x]: seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X = y + dy, x + dx
            if 0 <= Y < h and 0 <= X < w and not seen[Y, X] and not wall[Y, X]: seen[Y, X] = True; q.append((Y, X))
    inside = ~seen
    core = inside.copy()
    for _ in range(2):                      # 太らせたぶんを、元にもどす
        core = core & np.roll(core, 1, 0) & np.roll(core, -1, 0) & np.roll(core, 1, 1) & np.roll(core, -1, 1)
    inside = core | (wall0 & inside)
    wall = wall0
    # 線のすぐ外側の1ぶんも、物のふちとして残す（線の色をそのまま使う）
    grown = inside.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        grown |= np.roll(np.roll(inside, dy, 0), dx, 1) & wall
    rgba = np.dstack([a.astype(np.uint8), (grown * 255).astype(np.uint8)])
    img = Image.fromarray(rgba, 'RGBA'); bb = img.getchannel('A').getbbox(); img = img.crop(bb)
    img = img.resize((max(1, round(img.width / SHRINK)), max(1, round(img.height / SHRINK))), Image.BOX)
    al = np.array(img.getchannel('A')); img.putalpha(Image.fromarray(((al > 110) * 255).astype(np.uint8)))
    # 色数をへらして、ドット絵っぽくそろえる
    rgb = img.convert('RGB').quantize(28, dither=Image.NONE).convert('RGB'); rgb.putalpha(img.getchannel('A'))
    return rgb

def entry(img): return {'src': png(img), 'w': img.width, 'h': img.height}

bench = cutout((15, 476, 150, 585))
tank = cutout((552, 482, 632, 588))
frame = cutout((486, 494, 548, 574))
print('sizes', bench.size, tank.size, frame.size)

def tank_level(img, lv):                    # 水の青を、へった分だけ灰色にする
    a = np.array(img).astype(float); f = (3 - lv) / 3
    blue = (a[..., 2] > a[..., 0] + 22) & (a[..., 3] > 0)
    grey = np.array([58, 60, 66.0])
    a[blue, :3] = a[blue, :3] * (1 - f) + grey * f
    return Image.fromarray(a.astype(np.uint8), 'RGBA')

def drip(img, on):
    a = np.array(img).copy()
    if on:
        h, w = a.shape[:2]; x = w - 6
        for dy, c in ((1, (120, 190, 240)), (3, (160, 215, 250))): a[h - 1 - dy, x] = (*c, 255)
    return Image.fromarray(a, 'RGBA')

out = {'ppu': 40, 'bench': [entry(bench)], 'tank': [entry(tank_level(tank, l)) for l in range(4)], 'filter': [entry(drip(frame, 0)), entry(drip(frame, 1))]}
(here / 'objs_art.js').write_text('window.RAFT.objArt = ' + json.dumps(out) + ';\n')
for n, im in (('bench', bench), ('tank', tank), ('frame', frame)):
    bg = Image.new('RGBA', (im.width * 6, im.height * 6), (40, 90, 120, 255)); bg.alpha_composite(im.resize((im.width * 6, im.height * 6), Image.NEAREST)); bg.save(f'/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/o_{n}.png')
