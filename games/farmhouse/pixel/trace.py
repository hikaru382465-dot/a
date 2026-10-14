"""
ドット絵の画像（拡大されてぼやけたもの）から、1ドットずつ色を読み取って、元のドット絵に戻す。
python trace.py ref/source_sheet.png  x0 x1 y0 y1  ドットの大きさ 横の位相 縦の位相  名前   → sprites/名前.png, 名前.pxl, 重ね合わせの確認
"""
import sys, os
import numpy as np
from PIL import Image
import pxl

def trace(path, box, p, phx, phy, name, ncol=18):
    im = Image.open(path).convert("RGB"); a = np.asarray(im).astype(float)
    x0, x1, y0, y1 = box; bg = a[5, 5]
    cols = int((x1 - x0) / p) + 1; rows = int((y1 - y0) / p) + 1
    cell = np.zeros((rows, cols, 3)); alpha = np.zeros((rows, cols), bool)
    for r in range(rows):
        for c in range(cols):
            cx = x0 + phx + c * p; cy = y0 + phy + r * p
            blk = a[int(cy - p * .25):int(cy + p * .25) + 1, int(cx - p * .25):int(cx + p * .25) + 1].reshape(-1, 3)
            if len(blk) == 0: continue
            m = np.median(blk, 0); cell[r, c] = m; alpha[r, c] = np.abs(m - bg).sum() > 45
    ys, xs = np.nonzero(alpha); r0, r1, c0, c1 = ys.min(), ys.max(), xs.min(), xs.max()
    cell, alpha = cell[r0:r1 + 1, c0:c1 + 1], alpha[r0:r1 + 1, c0:c1 + 1]
    # 色を少ない数にまとめる
    small = Image.fromarray(cell.astype(np.uint8)).quantize(ncol, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = np.asarray(small.convert("RGB"))
    out = np.zeros((*alpha.shape, 4), np.uint8); out[..., :3] = q; out[..., 3] = alpha * 255
    return out

if __name__ == "__main__":
    pass
