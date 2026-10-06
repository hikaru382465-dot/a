"""
ドット絵のキャンバス。文字のマス目(.pxl)を絵にして、拡大した確認用の絵(目盛りつき)と点検の結果を出す。

使い方:  python pxl.py sprites/barrel.pxl        → sprites/barrel.png（原寸）, barrel_zoom.png（拡大+目盛り）
書き方（.pxl）:
  @size 16 20          絵の大きさ（ドット）
  @mirror              左半分だけ書けば、右に折り返す（正面向きの物）
  @sidelight 2 K       左を明るく右を暗く（段数）。K系統（輪郭）には効かない
  @outline sel         外側に輪郭線をつける。sel=となりの色の一番暗い色 / K=夜の黒1色
  @ramp D 8a5430       系統Dの基本色をこの場で変える（パレットの上書き）
  マス目: 1マス=2文字。 ..=すきま、D3=系統D の明るさ3。マスは空白で区切る。 # から行末はメモ
"""
import sys, json, os, colorsys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

def hex2rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def make_ramp(base, n=8):
    """基本色から n 段の明暗を作る。暗いほど青むらさきへ、明るいほど黄色へ寄せる。"""
    r, g, b = base; out = []
    mid = 4
    for i in range(n):
        t = (i - mid) / (mid if i < mid else n - 1 - mid)          # -1 … +1
        if t < 0:
            k = -t; tint = (36, 28, 70)
            c = [v * (1 - .62 * k) + tt * .62 * k for v, tt in zip((r, g, b), tint)]
        else:
            k = t; tint = (255, 238, 190)
            c = [v * (1 - .55 * k) + tt * .55 * k for v, tt in zip((r, g, b), tint)]
        out.append(tuple(int(round(max(0, min(255, x)))) for x in c))
    return out

def load_palette(overrides=None):
    p = json.load(open(os.path.join(HERE, "palette.json")))
    pal = {}
    for f, d in p["families"].items():
        base = hex2rgb((overrides or {}).get(f, d["base"]))
        pal[f] = make_ramp(base, p["shades"])
    return pal, p

def parse(path):
    text = [l.split("#")[0].rstrip() for l in open(path, encoding="utf-8")]
    meta = dict(size=None, mirror=False, side=(0, ""), outline=None, ramps={})
    rows = []
    for ln, l in enumerate(text, 1):
        s = l.strip()
        if not s: continue
        if s.startswith("@"):
            w = s.split()
            if w[0] == "@size": meta["size"] = (int(w[1]), int(w[2]))
            elif w[0] == "@mirror": meta["mirror"] = True
            elif w[0] == "@sidelight": meta["side"] = (int(w[1]), w[2] if len(w) > 2 else "")
            elif w[0] == "@outline": meta["outline"] = w[1] if len(w) > 1 else "sel"
            elif w[0] == "@ramp": meta["ramps"][w[1]] = w[2]
            else: raise SystemExit(f"{path}:{ln}: 知らない指示 {w[0]}")
        else:
            rows.append((ln, s.split()))
    return meta, rows

def build(path):
    meta, rows = parse(path)
    pal, _ = load_palette(meta["ramps"])
    W, H = meta["size"]; half = W // 2 if meta["mirror"] else W
    if len(rows) != H: raise SystemExit(f"{path}: 行が{len(rows)}本。@size では{H}本のはず")
    code = np.full((H, W), "..", dtype="<U2")
    for y, (ln, toks) in enumerate(rows):
        if len(toks) != half: raise SystemExit(f"{path}:{ln}: マスが{len(toks)}個。{half}個のはず")
        for x, t in enumerate(toks):
            if t != ".." and (len(t) != 2 or t[0] not in pal or not t[1].isdigit() or int(t[1]) >= len(pal[t[0]])):
                raise SystemExit(f"{path}:{ln}: マス{x+1}の「{t}」は使えない")
            code[y, x] = t
            if meta["mirror"]: code[y, W - 1 - x] = t
    k, ex = meta["side"]
    if k:  # 左を明るく、右を暗く
        for y in range(H):
            for x in range(W):
                t = code[y, x]
                if t == ".." or t[0] in ex: continue
                off = int(round(-k * (x - (W - 1) / 2) / ((W - 1) / 2)))
                code[y, x] = t[0] + str(max(0, min(len(pal[t[0]]) - 1, int(t[1]) + off)))
    if meta["outline"]:
        opaque = code != ".."; new = code.copy()
        for y in range(H):
            for x in range(W):
                if opaque[y, x]: continue
                best = None
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and opaque[yy, xx]:
                        t = code[yy, xx]
                        if best is None or int(t[1]) < int(best[1]): best = t
                if best: new[y, x] = "K0" if meta["outline"] == "K" else best[0] + "0"
        code = new
    img = np.zeros((H, W, 4), np.uint8)
    for y in range(H):
        for x in range(W):
            t = code[y, x]
            if t != "..": img[y, x] = (*pal[t[0]][int(t[1])], 255)
    return code, img, pal

def inspect(code):
    H, W = code.shape; used = {}
    orphans = []
    for y in range(H):
        for x in range(W):
            t = code[y, x]
            if t == "..": continue
            used[t] = used.get(t, 0) + 1
            nb = [code[yy, xx] for yy, xx in ((y+1, x), (y-1, x), (y, x+1), (y, x-1)) if 0 <= yy < H and 0 <= xx < W]
            if t not in nb and t[1] != "0": orphans.append((x, y, t))
    return used, orphans

def zoom(img, code, pal, z=16):
    H, W = img.shape[:2]; pad = 26
    big = Image.new("RGBA", (W * z + pad, H * z + pad), (22, 26, 34, 255))
    chk = Image.new("RGBA", (W * z, H * z))
    d = ImageDraw.Draw(chk)
    for y in range(H):
        for x in range(W):
            d.rectangle((x*z, y*z, x*z+z-1, y*z+z-1), fill=(46, 52, 62, 255) if (x + y) % 2 else (40, 46, 56, 255))
    chk.alpha_composite(Image.fromarray(img).resize((W * z, H * z), Image.NEAREST))
    d = ImageDraw.Draw(chk)
    for i in range(W + 1): d.line((i*z, 0, i*z, H*z), fill=(255, 255, 255, 90 if i % 4 == 0 else 28))
    for i in range(H + 1): d.line((0, i*z, W*z, i*z), fill=(255, 255, 255, 90 if i % 4 == 0 else 28))
    big.paste(chk, (pad, pad)); d = ImageDraw.Draw(big); f = ImageFont.load_default()
    for i in range(0, W, 2): d.text((pad + i*z + 2, 8), str(i), fill=(200, 210, 230), font=f)
    for i in range(0, H, 2): d.text((2, pad + i*z + 3), str(i), fill=(200, 210, 230), font=f)
    return big

if __name__ == "__main__":
    for path in sys.argv[1:]:
        code, img, pal = build(path)
        base = os.path.splitext(path)[0]
        Image.fromarray(img).save(base + ".png"); zoom(img, code, pal).save(base + "_zoom.png")
        used, orph = inspect(code)
        print(f"{path}: {img.shape[1]}x{img.shape[0]} / 使った色 {len(used)} 色")
        if orph: print("  ぽつんと1ドット（意図したものか確認）:", ", ".join(f"({x},{y}){t}" for x, y, t in orph[:12]))
