# 魔法のエフェクト（ドット絵のアニメ）を、コードで描いて、コマごとのPNGとシートに書き出す
import math, random, os
from PIL import Image, ImageDraw
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fx"); os.makedirs(OUT, exist_ok=True)
UP = 4  # 小さく描いて、ドットのまま4倍にする

def save(name, frames):
    big = [f.resize((f.width * UP, f.height * UP), Image.NEAREST) for f in frames]
    for i, f in enumerate(big): f.save(os.path.join(OUT, f"{name}_{i}.png"))
    sheet = Image.new("RGBA", (big[0].width * len(big), big[0].height), (0, 0, 0, 0))
    for i, f in enumerate(big): sheet.alpha_composite(f, (i * big[0].width, 0))
    sheet.save(os.path.join(OUT, f"{name}_sheet.png")); return sheet

def lightning(n=6, w=64, h=24):  # 稲妻：ぎざぎざの線。コマごとに形が変わる
    fr = []
    for i in range(n):
        R = random.Random(100 + i); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        pts = [(1, h // 2)]; x = 1
        while x < w - 3:
            x += R.randint(5, 9); pts.append((min(x, w - 2), h // 2 + R.randint(-8, 8)))
        a = 255 if i < n - 2 else int(255 * (n - i) / 3)
        for width, col in ((5, (120, 80, 255, a // 2)), (3, (255, 160, 40, a)), (1, (255, 255, 230, a))):
            d.line(pts, fill=col, width=width)
        for (px, py) in pts[1:-1:2]:  # 火花
            d.point((px + R.randint(-2, 2), py + R.randint(-3, 3)), fill=(255, 255, 255, a))
        fr.append(im)
    return fr

def slash(n=6, s=48):  # 斬撃：三日月がさっと現れて消える
    fr = []
    for i in range(n):
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); px = im.load(); c = s / 2
        prog = min(1, (i + 1) / 3.0); fade = 1 if i < 3 else (n - i) / 3
        for y in range(s):
            for x in range(s):
                dx, dy = x - c, y - c; r = math.hypot(dx, dy); ang = math.degrees(math.atan2(dy, dx))
                if ang < -80 or ang > 80 - (1 - prog) * 160: continue
                outer = 21 + math.cos(math.radians(ang * 1.1)) * 2; inner = outer - (3 + 5 * math.cos(math.radians(ang * 1.1)))
                if inner < r < outer:
                    t = (r - inner) / max(1, outer - inner); col = (255, 255, 255) if t > .5 else (140, 220, 255)
                    px[x, y] = (*col, int(255 * fade))
        fr.append(im)
    return fr

def explosion(n=8, s=48):  # 爆発：ふくらんで、色がかわって、けむりになる
    fr = []
    for i in range(n):
        R = random.Random(7 + i); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); px = im.load(); c = s / 2
        rad = 6 + i * 2.6; fade = 1 if i < 5 else (n - i) / 3
        for y in range(s):
            for x in range(s):
                dx, dy = x - c, y - c; r = math.hypot(dx, dy) + R.uniform(-2.2, 2.2); k = r / rad
                if k > 1: continue
                if i < 4: col = (255, 250, 200) if k < .35 else (255, 200, 60) if k < .7 else (255, 110, 30)
                else: col = (255, 150, 40) if k < .45 else (200, 60, 30) if k < .75 else (70, 50, 60)
                px[x, y] = (*col, int(255 * fade))
        fr.append(im)
    return fr

def magic_circle(n=8, s=48):  # 魔法陣：まわるルーン
    fr = []
    for i in range(n):
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2; rot = i * 2 * math.pi / (n * 3)
        a = 200 + int(55 * math.sin(i / n * 2 * math.pi)); col = (120, 255, 230, a); dim = (60, 180, 200, a // 2)
        d.ellipse((2, 2, s - 3, s - 3), outline=col); d.ellipse((6, 6, s - 7, s - 7), outline=dim)
        for k in range(6):  # ルーンの印
            ang = rot + k * math.pi / 3; x = c + math.cos(ang) * 19; y = c + math.sin(ang) * 19
            d.rectangle((x - 1, y - 1, x + 1, y + 1), fill=col)
        star = [(c + math.cos(rot + k * 2 * math.pi / 5 * 2 - math.pi / 2) * 15, c + math.sin(rot + k * 2 * math.pi / 5 * 2 - math.pi / 2) * 15) for k in range(6)]
        d.line(star, fill=col, width=1)
        fr.append(im)
    return fr

if __name__ == "__main__":
    sheets = {n: save(n, f()) for n, f in (("fx_lightning", lightning), ("fx_slash", slash), ("fx_explosion", explosion), ("fx_magic_circle", magic_circle))}
    W = max(s.width for s in sheets.values()) + 20; H = sum(s.height for s in sheets.values()) + 20 * (len(sheets) + 1)
    bg = Image.new("RGBA", (W, H), (26, 22, 40, 255)); y = 20
    for s in sheets.values(): bg.alpha_composite(s, (10, y)); y += s.height + 20
    bg.save(os.path.join(OUT, "preview_fx.png")); print(bg.size)
