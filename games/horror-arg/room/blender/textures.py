#!/usr/bin/env python3
"""部屋の質感の絵をコードで作る（外部素材なし）。出力：room/textures/*.png
PBRの「色」「法線（凹凸）」「粗さ」を作る。Blenderの glTF 書き出しでそのまま使える。
使い方: python3 textures.py"""
import pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = pathlib.Path(__file__).resolve().parent.parent / "textures"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(42)

def save(arr, name, mode="RGB"):
    a = np.clip(arr, 0, 1)
    Image.fromarray((a * 255).astype(np.uint8), mode if arr.ndim == 3 else "L").save(OUT / name, optimize=True)

def smooth_noise(h, w, cell, octaves=3):
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(2, cell // (2 ** o))
        small = rng.random((h // c + 2, w // c + 2))
        img = Image.fromarray((small * 255).astype(np.uint8)).resize((w + c * 2, h + c * 2), Image.BICUBIC)
        out += amp * np.asarray(img, dtype=float)[:h, :w] / 255.0
        tot += amp; amp *= 0.5
    return out / tot

def normal_from_height(hgt, strength=2.0):
    gy, gx = np.gradient(hgt)
    nx, ny = -gx * strength, gy * strength   # OpenGL向き（Y上）
    nz = np.ones_like(hgt)
    n = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    return np.stack([nx / n * 0.5 + 0.5, ny / n * 0.5 + 0.5, nz / n * 0.5 + 0.5], axis=2)

S = 1024
# ---- フローリング（1m四方に板10枚）----
def floor():
    planks, plank_h = 10, S // 10
    alb = np.zeros((S, S, 3)); hgt = np.zeros((S, S)); rough = np.zeros((S, S))
    base = np.array([0.20, 0.115, 0.065])
    for i in range(planks):
        y0, y1 = i * plank_h, (i + 1) * plank_h
        off = rng.integers(0, S)
        # 板ごとに色を変え、木目を長手方向に
        tint = 0.75 + rng.random() * 0.5
        grain = smooth_noise(plank_h, S, 90, 3)
        streak = np.repeat(smooth_noise(plank_h, 1, 4, 2), S, axis=1) * 0.5 + grain * 0.5
        colr = base[None, None, :] * (tint + (streak[:, :, None] - 0.5) * 0.9)
        colr = np.roll(colr, off, axis=1)
        alb[y0:y1] = colr
        # 継ぎ目（隙間）
        hgt[y0:y0 + 4] = -0.6; hgt[y1 - 2:y1] = -0.3
        j = (off + rng.integers(S // 3, S // 2)) % S
        hgt[y0:y1, j:j + 3] = -0.6
        alb[y0:y0 + 4] *= 0.25; alb[y0:y1, j:j + 3] *= 0.25
        rough[y0:y1] = 0.20 + 0.18 * np.roll(streak, off, axis=1)
    hgt += smooth_noise(S, S, 20, 3) * 0.08
    save(alb, "floor_albedo.png"); save(normal_from_height(hgt, 8.0), "floor_normal.png")
    save(rough, "floor_roughness.png", "L")
floor()

# ---- 壁紙：古びた白、シミ、うすい凹凸 ----
def wall():
    base = np.array([0.46, 0.44, 0.40])
    n1 = smooth_noise(S, S, 200, 4); n2 = smooth_noise(S, S, 30, 3)
    stain = np.clip((n1 - 0.58) * 2.2, 0, 1)
    alb = base[None, None, :] * (0.85 + n2[:, :, None] * 0.25) * (1 - stain[:, :, None] * 0.35)
    alb[:, :, 2] *= 1 - stain * 0.1
    hgt = n2 * 0.5 + smooth_noise(S, S, 6, 2) * 0.5
    save(alb, "wall_albedo.png"); save(normal_from_height(hgt, 3.0), "wall_normal.png")
    save(np.full((S, S), 0.9) - stain * 0.1, "wall_roughness.png", "L")
wall()

# ---- 机の天板：あたたかい茶色の木目 ----
def desk():
    base = np.array([0.33, 0.17, 0.075])
    streak = np.repeat(smooth_noise(S, 1, 3, 3), S, axis=1)
    grain = smooth_noise(S, S, 60, 3)
    v = streak * 0.6 + grain * 0.4
    alb = base[None, None, :] * (0.7 + v[:, :, None] * 0.7)
    wear = smooth_noise(S, S, 120, 3)
    alb *= (1 - np.clip(wear - 0.6, 0, 1)[:, :, None] * 0.4)
    save(alb, "desk_albedo.png"); save(normal_from_height(v * 0.3, 2.0), "desk_normal.png")
    save(0.30 + wear * 0.15, "desk_roughness.png", "L")
desk()

# ---- 掛け布団：灰青のキルト（ひし形）----
def duvet():
    yy, xx = np.mgrid[0:S, 0:S] / S
    cell = 6
    d = np.abs(((xx * cell) % 1) - 0.5) + np.abs(((yy * cell) % 1) - 0.5)
    quilt = np.clip(d * 1.6, 0, 1)
    fine = smooth_noise(S, S, 8, 2)
    base = np.array([0.38, 0.40, 0.46])
    alb = base[None, None, :] * (0.88 + quilt[:, :, None] * 0.10 + fine[:, :, None] * 0.12)
    save(alb, "duvet_albedo.png"); save(normal_from_height(quilt * 0.5 + fine * 0.2, 4.0), "duvet_normal.png")
duvet()

# ---- ラグ：濃いグレーの毛足 ----
def rug():
    f = smooth_noise(S, S, 4, 2); g = smooth_noise(S, S, 60, 2)
    base = np.array([0.13, 0.135, 0.15])
    alb = base[None, None, :] * (0.7 + f[:, :, None] * 0.6) * (0.9 + g[:, :, None] * 0.2)
    save(alb, "rug_albedo.png"); save(normal_from_height(f, 3.0), "rug_normal.png")
rug()

# ---- モニターの壁紙（夜の山と街。光る）----
def screen():
    W, H = 1024, 576
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(8 + 30 * t), int(14 + 40 * t), int(40 + 70 * t)))
    pts = [(0, H)]
    x = 0
    while x <= W:
        pts.append((x, int(H * 0.55 - 120 * abs(np.sin(x / 140.0)) - 60 * abs(np.sin(x / 57.0)))))
        x += 16
    pts.append((W, H)); d.polygon(pts, fill=(10, 20, 45))
    for i in range(160):
        x = int(rng.random() * W); y = int(H * 0.78 + rng.random() * H * 0.2)
        d.rectangle([x, y, x + 2, y + 2], fill=(230, 190, 120))
    d.ellipse([W // 2 - 4, int(H * 0.52), W // 2 + 4, int(H * 0.52) + 8], fill=(255, 235, 190))
    # タスクバー
    d.rectangle([0, H - 26, W, H], fill=(14, 20, 34))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    img.save(OUT / "screen_emissive.png", optimize=True)
screen()

# ---- 置き時計：7セグの「2:17」----
def clock(text="2:17", name="clock_emissive.png"):
    W, H = 512, 256
    img = Image.new("RGB", (W, H), (6, 6, 8)); d = ImageDraw.Draw(img)
    seg = {"0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg", "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg"}
    def digit(x, ch, w=70, h=130, t=12):
        s = seg[ch]; col = (225, 232, 245)
        r = {"a": [x + t, 60, x + w - t, 60 + t], "b": [x + w - t, 60 + t, x + w, 60 + h // 2], "c": [x + w - t, 60 + h // 2, x + w, 60 + h - t],
             "d": [x + t, 60 + h - t, x + w - t, 60 + h], "e": [x, 60 + h // 2, x + t, 60 + h - t], "f": [x, 60 + t, x + t, 60 + h // 2],
             "g": [x + t, 60 + h // 2 - t // 2, x + w - t, 60 + h // 2 + t // 2]}
        for k in s: d.rectangle(r[k], fill=col)
    xs = [90, 180]
    digit(xs[0], text[0]); d.ellipse([170, 95, 182, 107], fill=(225, 232, 245)); d.ellipse([170, 135, 182, 147], fill=(225, 232, 245))
    digit(200, text[2]); digit(290, text[3])
    d.text((395, 70), "AM", fill=(200, 208, 225))
    img = img.filter(ImageFilter.GaussianBlur(0.8)); img.save(OUT / name, optimize=True)
clock()

# ---- 窓の外：街の夜と朝（窓の外の面に貼る。光る）----
def city(kind):
    W, H = 1024, 640
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        if kind == "night": c = (int(4 + 22 * t), int(10 + 38 * t), int(60 + 90 * t))
        else: c = (int(140 + 90 * t), int(170 + 60 * t), int(215 + 25 * t))
        d.line([(0, y), (W, y)], fill=c)
    if kind == "morning": d.ellipse([W * 0.62, H * 0.30, W * 0.62 + 70, H * 0.30 + 70], fill=(255, 245, 215))
    x = 0
    while x < W:
        bw = int(60 + rng.random() * 110); bh = int(120 + rng.random() * 260)
        col = (12, 16, 30) if kind == "night" else (120, 135, 165)
        d.rectangle([x, H - bh, x + bw, H], fill=col)
        for wy in range(H - bh + 14, H - 10, 22):
            for wx in range(x + 8, x + bw - 8, 18):
                if kind == "night" and rng.random() < 0.18: d.rectangle([wx, wy, wx + 7, wy + 10], fill=(240, 205, 130))
                if kind == "morning" and rng.random() < 0.5: d.rectangle([wx, wy, wx + 7, wy + 10], fill=(170, 190, 220))
        x += bw + int(rng.random() * 12)
    img = img.filter(ImageFilter.GaussianBlur(1.0)); img.save(OUT / f"city_{kind}.png", optimize=True)
city("night"); city("morning")

# ---- 壁の写真（白黒の風景）2枚 ----
def photo(name, seed):
    r = np.random.default_rng(seed); W, H = 256, 320
    img = Image.new("L", (W, H)); d = ImageDraw.Draw(img)
    for y in range(H): d.line([(0, y), (W, y)], fill=int(40 + 110 * (1 - y / H)))
    pts = [(0, H)]; x = 0
    while x <= W:
        pts.append((x, int(H * 0.6 - 50 * abs(np.sin(x / (30 + seed % 7 * 4))) - r.random() * 8))); x += 8
    pts.append((W, H)); d.polygon(pts, fill=20)
    img = img.filter(ImageFilter.GaussianBlur(1.2)).convert("RGB")
    canvas = Image.new("RGB", (W + 40, H + 70), (205, 200, 190)); canvas.paste(img, (20, 20)); canvas.save(OUT / name, optimize=True)
photo("photo_a.png", 3); photo("photo_b.png", 11)

# ---- 付箋の絵（黄色。文字は「日ごとに差し替え」するので、ここでは空）----
Image.new("RGB", (128, 128), (235, 215, 120)).save(OUT / "sticky.png", optimize=True)
print("textures:", sorted(p.name for p in OUT.glob("*.png")))
