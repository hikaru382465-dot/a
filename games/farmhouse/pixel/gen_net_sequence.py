"""
網を、投げる → 着水 → うかぶ → 引き上げる、まで一連で。python gen_net_sequence.py → assets/effects/net_sequence.gif / net_sequence_sheet.png
gen_net.py（投げる・うかぶ）と gen_net_haul.py（引き上げ）のコマを、ひとつの場面にそろえて置く。
"""
import os, math
import numpy as np
from PIL import Image
import gen_net as N
import gen_net_haul as Hl
OUT = N.OUT
W, H = 176, 150
HORIZON = 84
LAND = (128, 110)                      # 網が落ちる場所（水の上）
HAND = (38, 103)                       # 投げる人の手
col = N.col

def background(t):
    cv = N.Canvas(W, H)
    yy = cv.Y
    sky = yy < HORIZON
    g = np.clip(2 - (HORIZON - yy) / 40.0, 0, 2)
    cv.put(sky, 'K', np.where(N.BAY[cv.Y % 4, cv.X % 4] < (g / 2) % 1, np.floor(g) + 1, np.floor(g)).astype(int) + 1)
    h = np.sin(2 * math.pi * (cv.X / 31.0 + cv.Y / 11.0 - t)) * .5 + np.sin(2 * math.pi * (cv.X / 17.0 - cv.Y / 7.0 + t * 2)) * .35
    idx = np.clip(np.floor((h + 1) / 2 * 2.4 + (N.BAY[cv.Y % 4, cv.X % 4] - .5) * .6).astype(int) + 2, 2, 4)
    near = np.clip((cv.Y - HORIZON) / 20.0, 0, 1)
    cv.put(~sky, 'w', np.where(near < .5, np.maximum(1, idx - 1), idx))
    # 桟橋の板（左下）と、手
    cv.put((cv.X < 56) & (cv.Y >= 108), 'D', np.where(cv.Y == 108, 6, 4 - ((cv.Y // 4) % 2)))
    for k in range(8): cv.img[108 + k * 5 // 1 if False else min(H - 1, 108 + k * 5), 20::12, :3] = col('D', 2)
    return cv.img

def stamp(base, f, ox, oy):
    h, w = f.shape[:2]; w = min(w, base.shape[1] - ox); h = min(h, base.shape[0] - oy); f = f[:h, :w]
    sub = base[oy:oy + h, ox:ox + w]; m = f[..., 3] > 0
    sub[m] = f[m]

def rope_line(img, a, b, sag):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 2
    for k in range(n + 1):
        t = k / n; x = int(round(a[0] + (b[0] - a[0]) * t)); y = int(round(a[1] + (b[1] - a[1]) * t + sag * 4 * t * (1 - t)))
        if 0 <= x < W and 0 <= y < H: img[y, x, :3] = col('C', 3); img[y, x, 3] = 255

def hand(img, pull=0):
    x, y = HAND[0] - 3 + pull, HAND[1] - 4
    for yy in range(4):
        for xx in range(6): 
            if 0 <= y + yy < H and 0 <= x + xx < W: img[y + yy, x + xx, :3] = col('A', 4 if yy < 2 else 3); img[y + yy, x + xx, 3] = 255
    for yy in range(3):
        for xx in range(-8, 0):
            if 0 <= y + 1 + yy < H and 0 <= x + xx < W: img[y + 1 + yy, x + xx, :3] = col('b', 4 if yy == 0 else 3); img[y + 1 + yy, x + xx, 3] = 255

seq = []; dur = []; tt = 0
# 1) 投げる＋着水（16コマ）：飛んでいる間のなわは gen_net が手の位置 (22,62)→ 場面の手へ合わせるため、同じ移動量で置く
THO = (LAND[0] - 112, LAND[1] - 70)
for i, f in enumerate(N.frames_throw):
    b = background(tt / 40.0); stamp(b, f, THO[0], THO[1]) if False else None
    img = b.copy(); fr = np.zeros((H, W, 4), np.uint8)
    ox, oy = THO
    sub = f[max(0, -oy):, max(0, -ox):]
    stamp(fr, f, ox, oy)
    # 手もとのなわと手は場面側で描く（飛行中は gen_net のなわを消して、場面の手へつなぎ直す）
    m = fr[..., 3] > 0; img[m] = fr[m]; seq.append(img); dur.append(90 if i < 11 else 130 if i == 11 else 110); tt += 1
# 2) うかぶ（8コマ）：なわが水の上にゆるくのびる
FO = (LAND[0] - 42, LAND[1] - 29)
for i in range(8):
    b = background(tt / 40.0); fr = np.zeros((H, W, 4), np.uint8); stamp(fr, N.frames_float[i % 4], FO[0], FO[1])
    m = fr[..., 3] > 0; b[m] = fr[m]
    rope_line(b, (LAND[0] - 24, LAND[1] + 1), HAND, 6 + math.sin(i * .8)); hand(b); seq.append(b); dur.append(220); tt += 1
# 3) 引き上げ（12コマ）：手のほうへ引っぱる
HO = (LAND[0] - 48, LAND[1] - 96)
for i in range(12):
    f = Hl.frame(i, 12, sway=0, rope=False); ax, ay = Hl.ATT
    b = background(tt / 40.0); fr = np.zeros((H, W, 4), np.uint8); stamp(fr, f, HO[0], HO[1])
    m = fr[..., 3] > 0; b[m] = fr[m]
    t_ = i / 11
    rope_line(b, (HO[0] + ax, HO[1] + ay), HAND, 6 * (1 - t_) + 1); hand(b, pull=int(2 * math.sin(i * 1.2))); seq.append(b); dur.append(110 if i < 10 else 300); tt += 1
dur[-1] = 900
K = 5
g = [Image.fromarray(s).convert("RGB").resize((W * K, H * K), Image.NEAREST) for s in seq]
g[0].save(os.path.join(OUT, "net_sequence.gif"), save_all=True, append_images=g[1:], duration=dur, loop=0)
cols = 9; rows = (len(seq) + cols - 1) // cols
sh = Image.new("RGB", (W * cols, H * rows))
for i, s in enumerate(seq): sh.paste(Image.fromarray(s).convert("RGB"), ((i % cols) * W, (i // cols) * H))
sh.save(os.path.join(OUT, "net_sequence_sheet.png"))
print("ok", len(seq))
