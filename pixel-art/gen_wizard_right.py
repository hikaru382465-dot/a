"""64x64 右向きの魔法使い（STYLE.md のダーク風）を PNG に書き出す。
使い方: python3 gen_wizard_right.py  → out/wizard_right_64.png と 8倍の確認用画像
"""
import math, random
from PIL import Image

W = 64
SEED = 20261004
# 明るい → 暗い。色相ずらし：生成り → 紫茶 → 紫
PAL = ['#FFE2A8', '#E6E0DF', '#D0BDB0', '#F0A050', '#C8B6A8', '#D0A88A', '#A79490', '#A27A6B',
       '#8A7678', '#B8582E', '#955E4F', '#715B62', '#604548', '#71363C', '#57363B', '#483740',
       '#422D37', '#3D2531', '#311926', '#1F1622', '#180E1A', '#130915', '#09040E', '#000000']
R = dict(cloth=[1, 2, 4, 6, 8, 11, 12, 15, 16], skin=[5, 5, 7, 10, 12], hair=[6, 8, 11, 12, 15, 16],
         red=[10, 13, 13, 14, 16, 17], dark=[11, 12, 15, 16, 17, 18, 19], leather=[10, 12, 14, 16, 17, 18],
         wood=[7, 10, 12, 14, 16, 17], orb=[0, 0, 3, 3, 9, 10, 13, 16])

rng = random.Random(SEED)
grid = [[-1] * W for _ in range(W)]


def get(x, y):
    return grid[y][x] if 0 <= x < W and 0 <= y < W else -1


def put(x, y, c):
    if 0 <= x < W and 0 <= y < W:
        grid[y][x] = c


def b_of(nx, ny):          # 光は左上（頭のうしろ側の上空）
    return (-nx - ny) / math.sqrt(2)


class Shape:
    def __init__(self, inside, b=None, v=None):
        self.inside, self.b, self.v = inside, b, v


def ell(cx, cy, rx, ry):
    return Shape(lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1,
                 lambda x, y: b_of((x - cx) / rx, (y - cy) / ry))


def cap(ax, ay, bx, by, r):
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy

    def q(x, y):
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / l2))
        return ax + dx * t, ay + dy * t

    def inside(x, y):
        qx, qy = q(x, y)
        return math.hypot(x - qx, y - qy) <= r

    def b(x, y):
        qx, qy = q(x, y)
        return b_of((x - qx) / r, (y - qy) / r)
    return Shape(inside, b)


def sub(base, fn):
    return Shape(lambda x, y: base.inside(x, y) and fn(x, y), base.b, base.v)


def union(a, b):
    return Shape(lambda x, y: a.inside(x, y) or b.inside(x, y), a.b, a.v)


def paint(shape, ramp, bias=0.0, dith=0.15, noise=0.5, speck=0.025, seam=0.6):
    n = len(ramp)
    m = [[shape.inside(x + .5, y + .5) for x in range(W)] for y in range(W)]
    if seam:   # 部品のさかい目を暗くして、とぎれとぎれの線にする
        for y in range(W):
            for x in range(W):
                if m[y][x] or grid[y][x] < 0:
                    continue
                if any(0 <= x + i < W and 0 <= y + j < W and m[y + j][x + i] for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    if rng.random() < seam:
                        grid[y][x] = min(22, grid[y][x] + 3)
    for y in range(W):
        for x in range(W):
            if not m[y][x]:
                continue
            px, py = x + .5, y + .5
            v = shape.v(px, py) if shape.v else 0.5 - 0.5 * shape.b(px, py)
            k = (v + bias) * (n - 1) + (dith if (x + y) & 1 else -dith) + (rng.random() - .5) * noise
            if rng.random() < speck:
                k += 2 if rng.random() < .5 else -2
            grid[y][x] = ramp[max(0, min(n - 1, round(k)))]
    return m


# ================= パーツ =================
OX, OY = 52, 14       # 宝珠の中心

# 宝珠の光のにじみ（背景）
for y in range(W):
    for x in range(W):
        d = math.hypot(x + .5 - OX, y + .5 - OY)
        if 5 < d < 10 and rng.random() < (1 - (d - 5) / 5) ** 1.5 * .6:
            grid[y][x] = 14 if d < 7 else 17 if d < 8.5 else 19
# 地面のかげ
paint(ell(29, 62, 17, 1.6), [19, 20, 21], bias=.3, noise=1, seam=0)

# ブーツ（つま先は右）
paint(ell(25, 59.5, 4, 2.1), R['leather'], bias=.2)
paint(ell(35, 59, 4.8, 2.3), R['leather'], bias=.15)

# ローブ：前（右）はまっすぐ、うしろ（左）は風でなびく。すそはやぶれ
jag = [rng.choice([0, 0, 0, 1, 2, 3]) for _ in range(33)]
rowj = [rng.choice([0, 0, -1, 1]) for _ in range(W)]
front = lambda y: 37 + (y - 28) * .12
back = lambda y: 24 - ((y - 28) / 28) ** 1.5 * 13
hem = lambda x: 57 - jag[int(x) // 2]
robe = Shape(lambda x, y: 28 <= y <= hem(x) and back(y) + rowj[int(y)] * .7 <= x <= front(y),
             lambda x, y: -((x - (front(y) + back(y)) / 2) / ((front(y) - back(y)) / 2)) * .85
             - ((y - 28) / 30 - .3) * .2 + .1 * math.sin(x * .7 - y * .25))
paint(robe, R['cloth'], bias=.1, noise=.6, dith=.2)
paint(sub(robe, lambda x, y: 40 <= y <= 42), R['leather'], seam=.3, bias=.1)          # 帯
for x, y in ((35, 40), (36, 40), (35, 41), (36, 41), (35, 42), (36, 42)):              # バックル
    put(x, y, 2 if y == 40 else 6)

# 杖（手前に斜めに構える）
paint(cap(33, 51, 50.5, 20.5, 1.5), R['wood'], bias=.05, seam=.3)
paint(ell(51, 19.5, 2.4, 1.6), R['wood'], bias=.15)      # 宝珠の受け
paint(Shape(lambda x, y: math.hypot(x - OX, y - OY) <= 4.3, None,
            lambda x, y: math.hypot(x - OX + .7, y - OY + .7) / 4.6 * .9),
      R['orb'], noise=.4, dith=.1, speck=0, seam=.9)

# まえに出した腕と手
paint(cap(33, 32.5, 39.5, 35.5, 2.5), R['cloth'], bias=.36, noise=.45, seam=.95)
paint(ell(41.5, 36, 2.2, 2.3), R['skin'], noise=.4, speck=0)

# 頭：うしろ髪 → 顔＋尖った鼻 → マフラー
paint(ell(27.5, 23.5, 5, 6.5), R['hair'], bias=.1, noise=.5)
paint(union(ell(32.5, 23, 5.4, 6), ell(38.4, 24.3, 2.0, 1.3)), R['skin'], bias=-.12, noise=.15, dith=.05, speck=0, seam=0)
paint(ell(31.5, 29, 6.5, 2.6), R['red'], noise=.9, seam=.8)                              # 首まわり
paint(union(cap(26, 29.5, 21.5, 33, 2.1), cap(21.5, 33, 18.5, 38.5, 1.4)), R['red'], noise=.6, seam=.6)                              # なびく端
put(35, 21, 19); put(36, 21, 19)                                                          # 片目
put(35, 22, 0); put(36, 22, 3); put(35, 23, 9); put(36, 23, 10)

# つばの落ち影：顔の上2段を1段暗く
skin = R['skin']
for x in range(30, 41):
    for y in (20, 21):
        c = get(x, y)
        if c in skin:
            put(x, y, skin[min(len(skin) - 1, skin.index(c) + 2)])
# 帽子：つば（前が長く、うしろは三角に流れる） → とんがり（先はうしろへ）
brim_y = lambda x: 19.5 - (x - 14) * .065
brim_h = lambda x: 2.9 * (x - 12) / 14 if x < 26 else 2.9 if x < 40 else 2.9 - 2.4 * (x - 40) / 7
paint(Shape(lambda x, y: 12 <= x <= 47 and abs(y - brim_y(x)) <= brim_h(x),
            lambda x, y: -((y - brim_y(x)) / max(brim_h(x), 1)) * .9 - (x - 30) / 45 * .4),
      R['cloth'], bias=.05, noise=.5, seam=.8)
cT = lambda y: (18 - y) / 17
cC = lambda y: 32 - 12 * max(0, cT(y)) ** 1.8
cHW = lambda y: (1 - cT(y)) ** .85 * 8.5 + .9
cone = Shape(lambda x, y: 1 <= y <= 18 and abs(x - cC(y)) <= cHW(y) + rowj[int(y)] * .6,
             lambda x, y: -((x - cC(y)) / cHW(y)) * .9 + .1 * math.sin(x * .8 + y * .3))
paint(cone, R['cloth'], noise=.6, dith=.2)
paint(sub(cone, lambda x, y: 15 <= y <= 16), R['red'], seam=.3, noise=.7)

# 継ぎ当て（茶色の十字）・しみ・すその汚れ
def cross(x, y):
    for k, (i, j) in enumerate(((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))):
        if get(x + i, y + j) >= 0:
            put(x + i, y + j, 10 if k else 12)

cross(30, 10); cross(22, 48)
cloth = R['cloth']
for _ in range(25):
    x, y = rng.randint(10, 50), rng.randint(2, 58)
    c = get(x, y)
    if c in cloth:
        to = cloth[min(len(cloth) - 1, cloth.index(c) + rng.randint(2, 3))]
        put(x, y, to)
        if rng.random() < .4 and get(x + 1, y) in cloth:
            put(x + 1, y, to)
for _ in range(5):
    x, top = rng.randint(14, 36), rng.randint(51, 54)
    for j in range(rng.randint(2, 4)):
        if get(x, top + j) in cloth:
            put(x, top + j, 10 if j < 1 else 12)

# ふちどり：左上は明るい光、ほかは暗い紫をとぎれとぎれに
snap = [row[:] for row in grid]
filled = lambda x, y: 0 <= x < W and 0 <= y < W and snap[y][x] >= 0
for y in range(W):
    for x in range(W):
        c = snap[y][x]
        if c < 0:
            continue
        tl = not filled(x - 1, y) or not filled(x, y - 1)
        ot = not filled(x + 1, y) or not filled(x, y + 1)
        if tl and c <= 8 and rng.random() < .7:
            grid[y][x] = 1
        elif ot and not tl and rng.random() < .35:
            grid[y][x] = rng.choice([18, 19, 19, 20, 21])

# ================= 書き出し =================
def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
for y in range(W):
    for x in range(W):
        if grid[y][x] >= 0:
            img.putpixel((x, y), rgb(PAL[grid[y][x]]) + (255,))
img.save('out/wizard_right_64.png')
prev = Image.new('RGBA', (W, W), (12, 7, 16, 255))
prev.alpha_composite(img)
prev.resize((W * 8, W * 8), Image.NEAREST).save('out/wizard_right_64_x8.png')

op = [(x, y) for y in range(W) for x in range(W) if grid[y][x] >= 0]
single = sum(all(get(x + i, y + j) != grid[y][x] for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))) for x, y in op)
print(f'{len({grid[y][x] for x, y in op})}色 / 1マス点 {single * 100 // len(op)}% / 暗い色 {sum(grid[y][x] >= 15 for x, y in op) * 100 // len(op)}%')
