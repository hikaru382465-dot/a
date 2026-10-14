# 畑のプランターの絵：空・種・芽・育ち中・実（6種）を、プランターに合成して crops_art.js にする。使い道：python3 make_crops.py
# 絵のもと：art/items/catalog3.png（プランター・成長段階・作物）。objs_art.js のあとに読み込み、objArt.plot をおきかえる
import base64, io, json, pathlib
import numpy as np
from PIL import Image
import cutlib
here = pathlib.Path(__file__).parent
C3 = here.parent / 'art' / 'items' / 'catalog3.png'
def cut(box, shrink=1):
    im = cutlib.cut_checker(C3, box, shrink=shrink)
    for _ in range(8):
        if not cutlib.LAST_TOUCH: break
        box = (box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4); im = cutlib.cut_checker(C3, box, shrink=shrink)
    return im
def soil(im):      # プランターの草（緑）を、土の色にぬりかえて「空」にする
    a = np.array(im).astype(float); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = (g > r * 1.02) & (g > b * 1.05) & (g > 60) & (a[..., 3] > 0)
    n = (np.sin(np.arange(a.shape[0])[:, None] * 12.9 + np.arange(a.shape[1])[None, :] * 78.2) * 43758.5 % 1.0)
    base = np.array([78, 52, 34.0]); k = (0.78 + 0.35 * n)[..., None]
    a[..., :3] = np.where(green[..., None], base * k, a[..., :3]); return Image.fromarray(a.astype(np.uint8), 'RGBA')
planter = soil(cut((1138, 730, 1250, 792)))
STAGES = [cut((598, 752, 628, 784)), cut((662, 752, 700, 792)), cut((732, 728, 794, 792))]      # 種・芽・育ち中（みんな共通）
FINAL = {      # 実のなった姿（作物ごと）
    'tomato': (798, 402, 896, 492), 'potato': (930, 402, 1034, 492), 'carrot': (1050, 402, 1156, 492),
    'corn': (1048, 540, 1150, 634), 'melon': (932, 540, 1034, 634), 'berry': (1408, 540, 1504, 632),
}
fin = {k: cut(b) for k, b in FINAL.items()}
PW, PH = planter.size; pad = 8; TOPH = 96
def compose(plant, scale=1.0):
    W = PW + pad * 2; H = PH + TOPH; cv = Image.new('RGBA', (W, H), (0, 0, 0, 0)); cv.alpha_composite(planter, (pad, H - PH))
    if plant is not None:
        p = plant if scale == 1.0 else plant.resize((max(1, round(plant.width * scale)), max(1, round(plant.height * scale))), Image.NEAREST)
        surf = H - PH + int(PH * 0.50)      # 土の面の、まん中あたり
        cv.alpha_composite(p, ((W - p.width) // 2, surf - p.height + int(p.height * 0.10)))
    return cv
frames = [compose(None)] + [compose(s) for s in STAGES] + [compose(fin[k], 0.9) for k in FINAL]
def entry(im):
    buf = io.BytesIO(); im.save(buf, 'PNG', optimize=True)
    return {'src': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(), 'w': im.width, 'h': im.height, 'hi': 3, 'ppu': 100}
out = [entry(f) for f in frames]
(here / 'crops_art.js').write_text('window.RAFT.objArt.plot = ' + json.dumps(out) + ';\nwindow.RAFT.cropIds = ' + json.dumps(list(FINAL)) + ';\n', encoding='utf-8')
print('crops_art.js', (here / 'crops_art.js').stat().st_size, 'bytes', [f.size for f in frames][:2])
bgc = Image.new('RGBA', (frames[0].width * len(frames) + 10 * len(frames), frames[0].height), (40, 120, 170, 255)); x = 0
for f in frames: bgc.alpha_composite(f, (x, 0)); x += f.width + 10
bgc.convert('RGB').save('/tmp/claude-0/-home-user-a/3a8914da-c12e-5acb-b76e-3d39cc2e80dd/scratchpad/crops_sheet.png')
