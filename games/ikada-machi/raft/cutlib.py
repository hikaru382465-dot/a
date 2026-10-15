# 白い市松もようの背景の絵（art/items/catalog2.png）から、置き物・アイテムを切り出す道具
import numpy as np
from collections import deque
from PIL import Image
LAST_TOUCH = False
def components(mask, minpx=50, reach=2):
    h, w = mask.shape; lab = np.zeros((h, w), int); n = 0; out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not lab[y, x]:
                n += 1; q = deque([(y, x)]); lab[y, x] = n; pts = [(y, x)]
                while q:
                    cy, cx = q.popleft()
                    for dy in range(-reach, reach + 1):
                        for dx in range(-reach, reach + 1):
                            Y, X = cy + dy, cx + dx
                            if 0 <= Y < h and 0 <= X < w and mask[Y, X] and not lab[Y, X]: lab[Y, X] = n; q.append((Y, X)); pts.append((Y, X))
                if len(pts) >= minpx: out.append(pts)
    return out
def cut_checker(path, box, shrink=2, blank=None, colors=28, pocket=0, fringe=0, pocket_min=80, trim=True):
    """外のふちとつながった白っぽい所だけを消して切り出す（絵の中の白は残る）。いちばん大きいかたまりだけ残す。"""
    im = Image.open(path).convert('RGB').crop(box); a = np.array(im).astype(int); h, w = a.shape[:2]
    bgl = (a.min(axis=2) > 205) & ((a.max(axis=2) - a.min(axis=2)) < 28)
    if blank: bgl[blank[1]:, blank[0]:] = True
    om = np.zeros((h, w), bool); q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bgl[y, x] and not om[y, x]: om[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if bgl[y, x] and not om[y, x]: om[y, x] = True; q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X = cy + dy, cx + dx
            if 0 <= Y < h and 0 <= X < w and bgl[Y, X] and not om[Y, X]: om[Y, X] = True; q.append((Y, X))
    if pocket:      # 絵の中にとり残された、小さい背景（足のすきま・ひげの輪の中）も消す
        inner = bgl & ~om; labp = np.zeros((h, w), bool)
        for pts in components(inner, minpx=1, reach=1):
            if pocket_min <= len(pts) < pocket:
                for (yy, xx) in pts: om[yy, xx] = True
    if fringe:      # 背景ととなりあう、白っぽいふち（にじみ）も消す
        lite = (a.min(axis=2) > 165) & ((a.max(axis=2) - a.min(axis=2)) < 40)
        for _ in range(fringe):
            p = np.pad(om, 1); near = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]; om = om | (near & lite)
    fg = ~om
    cs = components(fg, minpx=50, reach=2)
    if cs:
        big = max(cs, key=len); fg = np.zeros((h, w), bool)
        for (yy, xx) in big: fg[yy, xx] = True
    global LAST_TOUCH; LAST_TOUCH = bool(fg[0, :].any() or fg[-1, :].any() or fg[:, 0].any() or fg[:, -1].any())      # 切り出し範囲のふちにふれていたら、絵が見切れているかもしれない
    img = Image.fromarray(np.dstack([a.astype(np.uint8), (fg * 255).astype(np.uint8)]), 'RGBA'); img = img.crop(img.getchannel('A').getbbox()) if trim else img
    img = img.resize((max(1, round(img.width / shrink)), max(1, round(img.height / shrink))), Image.NEAREST)
    al = np.array(img.getchannel('A')); img.putalpha(Image.fromarray(((al > 110) * 255).astype(np.uint8)))
    return img      # 元の色のまま（色数はへらさない）

def cut_plane(path, box, shrink=1, thr=34):
    """暗いなめらかな背景の絵用：ふちの色から背景を平面でフィットして、ちがう所だけ残す。いちばん大きいかたまりだけ。"""
    im = Image.open(path).convert('RGB').crop(box); a = np.array(im).astype(float); h, w = a.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]; edge = np.zeros((h, w), bool); edge[:4, :] = edge[-4:, :] = True; edge[:, :4] = edge[:, -4:] = True
    X = np.c_[xs[edge], ys[edge], np.ones(edge.sum())]; bgm = np.zeros_like(a)
    for ch in range(3):
        co = np.linalg.lstsq(X, a[..., ch][edge], rcond=None)[0]; bgm[..., ch] = co[0] * xs + co[1] * ys + co[2]
    fg = np.sqrt(((a - bgm) ** 2).sum(axis=2)) > thr
    cs = components(fg, minpx=50, reach=2)
    if cs:
        big = max(cs, key=len); fg = np.zeros((h, w), bool)
        for (yy, xx) in big: fg[yy, xx] = True
    global LAST_TOUCH; LAST_TOUCH = bool(fg[0, :].any() or fg[-1, :].any() or fg[:, 0].any() or fg[:, -1].any())
    img = Image.fromarray(np.dstack([a.astype(np.uint8), (fg * 255).astype(np.uint8)]), 'RGBA'); img = img.crop(img.getchannel('A').getbbox())
    if shrink != 1: img = img.resize((max(1, round(img.width / shrink)), max(1, round(img.height / shrink))), Image.NEAREST)
    al = np.array(img.getchannel('A')); img.putalpha(Image.fromarray(((al > 110) * 255).astype(np.uint8)))
    return img
