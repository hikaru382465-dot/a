# AIで作った歩き絵（横に4コマ）を、コマごとに切り出して、背景を透明にして、同じ大きさのキャンバスにそろえる
import sys, os
from PIL import Image, ImageDraw

def load_mask(path, white_bg):
    im = Image.open(path).convert("RGBA")
    if white_bg:  # 白い背景：ふちから白をぬる
        rgb = im.convert("RGB")
        marker = (255, 0, 255)
        for pt in [(0, 0), (rgb.width - 1, 0), (0, rgb.height - 1), (rgb.width - 1, rgb.height - 1)]:
            ImageDraw.floodfill(rgb, pt, marker, thresh=28)
        px = rgb.load(); ip = im.load()
        for y in range(im.height):
            for x in range(im.width):
                if px[x, y] == marker:
                    ip[x, y] = (0, 0, 0, 0)
    else:  # 透明PNG：うすいにじみ（光のふち）は消す
        ip = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = ip[x, y]
                if a < 90: ip[x, y] = (0, 0, 0, 0)
                else: ip[x, y] = (r, g, b, 255)
    return im

def split_frames(im, gap=25):
    a = im.getchannel("A").point(lambda v: 255 if v > 0 else 0)
    cols = [any(a.getpixel((x, y)) for y in range(0, im.height, 2)) for x in range(im.width)]
    runs, start, last = [], None, None
    for x, on in enumerate(cols):
        if on:
            if start is None: start = x
            last = x
        elif start is not None and x - last > gap:
            runs.append((start, last)); start = None
    if start is not None: runs.append((start, last))
    out = []
    for (x0, x1) in runs:
        crop = im.crop((x0, 0, x1 + 1, im.height)); bb = crop.getchannel("A").getbbox()
        if bb and (bb[2]-bb[0]) > 30: out.append(crop.crop(bb))
    return out

def pack(frames, name, outdir, margin=6):
    W = max(f.width for f in frames) + margin * 2; H = max(f.height for f in frames) + margin * 2
    files = []
    for i, f in enumerate(frames):
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        c.alpha_composite(f, ((W - f.width) // 2, H - margin - f.height))  # 足もとをそろえる
        p = os.path.join(outdir, f"{name}_{i}.png"); c.save(p); files.append(c)
    strip = Image.new("RGBA", (W * len(files), H), (0, 0, 0, 0))
    for i, c in enumerate(files): strip.alpha_composite(c, (i * W, 0))
    strip.save(os.path.join(outdir, f"{name}_sheet.png"))
    return W, H, len(files), strip

if __name__ == "__main__":
    src, name, white = sys.argv[1], sys.argv[2], sys.argv[3] == "white"
    outdir = sys.argv[4] if len(sys.argv) > 4 else "../assets/chars"
    frames = split_frames(load_mask(src, white))
    W, H, n, _ = pack(frames, name, outdir)
    print(name, "コマ数", n, "キャンバス", W, "x", H, "各コマ", [(f.width, f.height) for f in frames])
