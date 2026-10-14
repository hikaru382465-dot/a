# 歩きの絵がほぼ同じポーズだったので、足の動きをコードで足した8コマを作る（騎士・射手）。 python3 art/make_walk_frames.py
import math
import numpy as np
from PIL import Image
def swing(src, n=8, leg=0.30, amp=0.075, lift=0.05, bob=0.02, lean=0.015):
    im = Image.open(src).convert('RGBA'); W, H = im.size; a = np.array(im); frames = []
    PAD = int(W * 0.15)
    for k in range(n):
        ph = 2 * math.pi * k / n; s = math.sin(ph); c = math.cos(ph)
        out = np.zeros((H + int(H * lift) + 4, W + 2 * PAD, 4), np.uint8); y0 = int(H * (1 - leg)); base = int(H * lift) + 2
        # 上半身：ぜんたいが少し上下・かたむく
        for y in range(H):
            t = (H - y) / H; dx = int(round(lean * W * s * t * 1.0)); dy = -int(round(abs(c) * bob * H)); 
            row = a[y]
            if y < y0:
                yy = base + y + dy
                if 0 <= yy < out.shape[0]: xs = PAD + dx; out[yy, xs:xs + W] = np.where(row[:, 3:4] > 0, row, out[yy, xs:xs + W])
        # 足：左右の半分を、反対向きにふる（片方は持ち上げる）
        half = W // 2
        for y in range(y0, H):
            u = (y - y0) / (H - y0)
            for side, (xa, xb) in enumerate(((0, half), (half, W))):
                sg = 1 if side == 0 else -1
                dx = int(round(sg * s * amp * W * (0.35 + 0.65 * u)))
                up = int(round(max(0.0, sg * c) * lift * H))
                yy = base + y - up + -int(round(abs(c) * bob * H)); xs = PAD + dx + xa
                seg = a[y, xa:xb]
                if 0 <= yy < out.shape[0]: out[yy, xs:xs + (xb - xa)] = np.where(seg[:, 3:4] > 0, seg, out[yy, xs:xs + (xb - xa)])
        im2 = Image.fromarray(out); bb = im2.getbbox(); frames.append(im2)
    box = None
    for f in frames:
        b = f.getbbox(); box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    # 足もと（下）はそろえる：下がわの余白は共通で切る
    return [f.crop(box) for f in frames]
for name, kw in (('knight_walk', dict(leg=0.30, amp=0.08)), ('archer_walk', dict(leg=0.34, amp=0.07))):
    fr = swing('assets/chars/%s_0.png' % name, **kw)
    for i, f in enumerate(fr): f.save('assets/chars/%s2_%d.png' % (name, i))
    sheet = Image.new('RGBA', (fr[0].width * 8, fr[0].height), (22, 34, 28, 255))
    for i, f in enumerate(fr): sheet.alpha_composite(f, (i * f.width, 0))
    sheet.convert('RGB').save('/tmp/%s2_sheet.png' % name); print(name, fr[0].size)
