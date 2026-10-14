"""
壁と屋根の「手描きの模様タイル」を作る。乱数の点ではなく、かたまりと線を1つずつ置いて描く。
python tiles.py → sprites/tile_plaster{0,1,2}.pxl, tile_thatch{0,1,2}.pxl（と確認用の絵）
タイルは、上下左右につながっても、ふちに模様がかからないように描く。
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.join(HERE, "sprites")
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image
import pxl

def tile(name, w, h, base, feats):
    g = [[base] * w for _ in range(h)]
    for tok, ox, oy, pts in feats:
        for dx, dy in pts:
            x, y = ox + dx, oy + dy
            if 0 <= x < w and 0 <= y < h: g[y][x] = tok
    p = os.path.join(SP, name + ".pxl")
    with open(p, "w") as f:
        f.write(f"# 手描きタイル {name}\n@size {w} {h}\n")
        for r in g: f.write(" ".join(r) + "\n")
    code, img, pal = pxl.build(p)
    big = np.tile(img, (3, 3, 1)); Image.fromarray(big).resize((big.shape[1] * 6, big.shape[0] * 6), Image.NEAREST).save(os.path.join(SP, name + "_x3.png"))
    return p

def line(pts): return pts
B1 = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)]
B2 = [(0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (1, 2), (2, 2)]
B3 = [(0, 0), (1, 0), (2, 0), (1, 1)]
D1 = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]
D2 = [(0, 0), (1, 0), (0, 1), (1, 1), (2, 1)]
D3 = [(0, 0), (1, 0), (0, 1)]
CRACK = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (4, 2), (4, 3), (5, 3), (5, 4), (5, 5)]
STAIN = [(0, i) for i in range(7)]

# ---- しっくい（20×20）：明るいかたまり・暗いかたまり・ひび・しみ
tile("tile_plaster0", 20, 20, "L4", [("L5", 4, 3, B1), ("L5", 13, 11, B2), ("L5", 8, 15, B3), ("L3", 11, 4, D1), ("L3", 3, 12, D2), ("L3", 15, 16, D3),
                                     ("L2", 5, 7, CRACK), ("L3", 6, 8, [(0, 0)])])
tile("tile_plaster1", 20, 20, "L4", [("L5", 12, 3, B2), ("L5", 3, 11, B1), ("L5", 14, 15, B3), ("L3", 4, 4, D2), ("L3", 11, 9, D1), ("L3", 7, 16, D3),
                                     ("L3", 15, 2, STAIN), ("L2", 15, 8, [(0, 0)])])
tile("tile_plaster2", 20, 20, "L4", [("L5", 3, 8, B2), ("L5", 11, 2, B3), ("L5", 12, 14, B1), ("L3", 8, 11, D1), ("L3", 14, 7, D3), ("L3", 3, 16, D2),
                                     ("L2", 10, 5, [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)])])

# ---- わら（16×16）：縦の筋（斜面を下る向き）。暗い筋と、そのとなりの明るい筋
def strokes(spec):
    f = []
    for (x, y0, y1, dark, light) in spec:
        f.append(("H2" if dark else "H3", x, y0, [(0, i) for i in range(y1 - y0 + 1)]))
        if light: f.append(("H5", x + 1, y0 + 1, [(0, i) for i in range(max(1, y1 - y0 - 1))]))
    return f
tile("tile_thatch0", 16, 16, "H4", strokes([(2, 1, 6, 1, 1), (7, 4, 9, 1, 1), (12, 0, 4, 0, 1), (5, 9, 14, 1, 1), (10, 9, 14, 0, 1), (14, 8, 12, 1, 0)]))
tile("tile_thatch1", 16, 16, "H4", strokes([(3, 0, 5, 0, 1), (8, 6, 12, 1, 1), (12, 2, 7, 1, 1), (1, 9, 14, 1, 0), (6, 0, 3, 0, 1), (14, 11, 15, 1, 1)]))
tile("tile_thatch2", 16, 16, "H4", strokes([(1, 3, 8, 1, 1), (6, 0, 4, 1, 1), (11, 5, 10, 0, 1), (4, 10, 15, 1, 1), (9, 11, 15, 1, 0), (14, 1, 5, 1, 1)]))
print("done")
