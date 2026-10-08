"""
網を、投げる → 着水 → うかぶ → 引き上げる、まで一連で。赤髪のちびキャラが桟橋に立って、投げて、引き上げる。
python gen_net_sequence.py → assets/effects/net_sequence.gif / net_sequence_sheet.png
gen_net.py（投げる・うかぶ）と gen_net_haul.py（引き上げ）のコマを、ひとつの場面にそろえて置く。なわは場面側で、手から網へ描く。
"""
import os, math
os.environ["NET_NOROPE"] = "1"
import numpy as np
from PIL import Image
import gen_net as N
import gen_net_haul as Hl
import gen_redhead_chibi as RC
OUT = N.OUT
W, H = 176, 150
HORIZON = 84
LAND = (128, 110)
col = N.col
CH_X, CH_Y = 26, 75                       # ちびキャラ（24×36）を置く左上。足の裏＝桟橋の上
SHOULDER = (CH_X + 13, CH_Y + 14)

def background(t):
    cv = N.Canvas(W, H); yy = cv.Y; sky = yy < HORIZON
    g = np.clip(2 - (HORIZON - yy) / 40.0, 0, 2)
    cv.put(sky, 'K', np.where(N.BAY[cv.Y % 4, cv.X % 4] < (g / 2) % 1, np.floor(g) + 1, np.floor(g)).astype(int) + 1)
    h = np.sin(2 * math.pi * (cv.X / 31.0 + cv.Y / 11.0 - t)) * .5 + np.sin(2 * math.pi * (cv.X / 17.0 - cv.Y / 7.0 + t * 2)) * .35
    idx = np.clip(np.floor((h + 1) / 2 * 2.4 + (N.BAY[cv.Y % 4, cv.X % 4] - .5) * .6).astype(int) + 2, 2, 4)
    near = np.clip((cv.Y - HORIZON) / 20.0, 0, 1)
    cv.put(~sky, 'w', np.where(near < .5, np.maximum(1, idx - 1), idx))
    cv.put((cv.X < 56) & (cv.Y >= 108), 'D', np.where(cv.Y == 108, 6, 4 - ((cv.Y // 4) % 2)))
    for k in range(8): cv.img[min(H - 1, 108 + k * 5), 20::12, :3] = col('D', 2)
    return cv.img

def stamp(base, f, ox, oy):
    h, w = f.shape[:2]; w = min(w, base.shape[1] - ox); h = min(h, base.shape[0] - oy); f = f[:h, :w]
    sub = base[oy:oy + h, ox:ox + w]; m = f[..., 3] > 0; sub[m] = f[m]

def put(img, x, y, f, s):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H: img[y, x, :3] = col(f, s); img[y, x, 3] = 255

def rope_line(img, a, b, sag):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 2
    for k in range(n + 1):
        t = k / n; put(img, a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + sag * 4 * t * (1 - t), 'C', 3)

def character(img, hand, lean=0, bob=0, ph=1):
    """ちびキャラ（右向き・うでなし）を置き、肩から手まで腕をのばす。手の位置（場面の座標）を返す"""
    spr = RC.side(ph, arms=False).a
    stamp(img, spr, CH_X + lean, CH_Y + bob)
    sx, sy = SHOULDER[0] + lean, SHOULDER[1] + bob
    hx, hy = sx + hand[0], sy + hand[1]
    n = int(max(abs(hx - sx), abs(hy - sy))) + 1
    for k in range(n + 1):
        t = k / max(1, n); x, y = sx + (hx - sx) * t, sy + (hy - sy) * t
        if k >= n - 1: put(img, x, y, 'k', 4)
        else: put(img, x, y, 's', 5); put(img, x, y + 1, 's', 3) if abs(hx - sx) < abs(hy - sy) else put(img, x + 1, y, 's', 3)
    put(img, hx, hy, 'k', 5)
    return (hx + .5, hy + .5)

seq = []; dur = []; tt = 0
THO = (LAND[0] - 112, LAND[1] - 70)
HANDS_THROW = [(-4, -2), (-5, -4), (-5, -6), (-4, -7), (-1, -9), (3, -9), (6, -7), (8, -4), (8, -2), (8, -1), (8, 0), (8, 0)]
# 1) 投げる＋着水
for i, f in enumerate(N.frames_throw):
    img = background(tt / 40.0); fr = np.zeros((H, W, 4), np.uint8); stamp(fr, f, *THO)
    m = fr[..., 3] > 0; img[m] = fr[m]
    hand = HANDS_THROW[i] if i < 12 else (7, 1 + (i - 12))
    lean = -1 if i < 3 else 0
    hp = character(img, hand, lean=lean, ph=1 if i < 8 else 0)
    att = N.ATTS[i]
    if att is not None: rope_line(img, hp, (att[0] + THO[0], att[1] + THO[1]), 7 * (1 - i / 11) + 1)
    elif i >= 12: rope_line(img, hp, (LAND[0] - 24, LAND[1] + 1), 5)
    seq.append(img); dur.append(90 if i < 11 else 130 if i == 11 else 110); tt += 1
# 2) うかぶ（8コマ）：なわを手でゆるく持つ
FO = (LAND[0] - 42, LAND[1] - 29)
for i in range(8):
    b = background(tt / 40.0); fr = np.zeros((H, W, 4), np.uint8); stamp(fr, N.frames_float[i % 4], *FO)
    m = fr[..., 3] > 0; b[m] = fr[m]
    hp = character(b, (7, 2 + (1 if i % 4 in (1, 2) else 0)), ph=0)
    rope_line(b, hp, (LAND[0] - 24, LAND[1] + 1), 6 + math.sin(i * .8)); seq.append(b); dur.append(220); tt += 1
# 3) 引き上げ（12コマ）：手を交互に引く。体をうしろへかたむける
HO = (LAND[0] - 48, LAND[1] - 96)
HANDS_HAUL = [(6, 3), (4, 5), (3, 6), (5, 3), (4, 5), (3, 6), (5, 3), (4, 5), (3, 6), (4, 4), (4, 4), (4, 4)]
for i in range(12):
    f = Hl.frame(i, 12, sway=0, rope=False); ax, ay = Hl.ATT
    b = background(tt / 40.0); fr = np.zeros((H, W, 4), np.uint8); stamp(fr, f, *HO)
    m = fr[..., 3] > 0; b[m] = fr[m]
    hp = character(b, HANDS_HAUL[i], lean=-1 if 1 <= i <= 9 else 0, bob=0, ph=[1, 2, 3, 0][i % 4])
    rope_line(b, hp, (HO[0] + ax, HO[1] + ay), 5 * (1 - i / 11) + 1); seq.append(b); dur.append(110 if i < 10 else 300); tt += 1
dur[-1] = 900
K = 5
g = [Image.fromarray(s).convert("RGB").resize((W * K, H * K), Image.NEAREST) for s in seq]
g[0].save(os.path.join(OUT, "net_sequence.gif"), save_all=True, append_images=g[1:], duration=dur, loop=0)
cols = 9; rows = (len(seq) + cols - 1) // cols
sh = Image.new("RGB", (W * cols, H * rows))
for i, s in enumerate(seq): sh.paste(Image.fromarray(s).convert("RGB"), ((i % cols) * W, (i // cols) * H))
sh.save(os.path.join(OUT, "net_sequence_sheet.png"))
print("ok", len(seq))
