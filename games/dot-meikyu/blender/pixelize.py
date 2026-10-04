# Blenderの書き出し絵を、ドット絵ふうに変える（小さくする→色を減らす→ふちを黒くする）
import sys
from PIL import Image
src = sys.argv[1] if len(sys.argv) > 1 else "../assets/hero_side.png"
dst = sys.argv[2] if len(sys.argv) > 2 else "../assets/hero_pixel.png"
H = int(sys.argv[3]) if len(sys.argv) > 3 else 64      # ドットの高さ
COLORS = int(sys.argv[4]) if len(sys.argv) > 4 else 20  # 使う色の数

im = Image.open(src).convert("RGBA")
im = im.crop(im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox())
w = round(im.width * H / im.height)
im = im.resize((w, H), Image.LANCZOS)
a = im.getchannel("A").point(lambda v: 255 if v > 128 else 0)
rgb = im.convert("RGB").quantize(COLORS, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
out = Image.new("RGBA", (w + 2, H + 2), (0, 0, 0, 0))
px = out.load(); ap = a.load(); cp = rgb.load()
for y in range(H + 2):
    for x in range(w + 2):
        sx, sy = x - 1, y - 1
        inside = 0 <= sx < w and 0 <= sy < H and ap[sx, sy]
        if inside:
            px[x, y] = cp[sx, sy] + (255,)
        else:
            near = any(0 <= sx + dx < w and 0 <= sy + dy < H and ap[sx + dx, sy + dy]
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if near:
                px[x, y] = (24, 14, 22, 255)
out.save(dst)
# 左右ならべた確認用（8倍に拡大、黒背景）
S = 8
big = out.resize((out.width * S, out.height * S), Image.NEAREST)
sheet = Image.new("RGBA", (big.width * 2 + 120, big.height + 40), (14, 12, 20, 255))
sheet.alpha_composite(big, (40, 20))
sheet.alpha_composite(big.transpose(Image.FLIP_LEFT_RIGHT), (big.width + 80, 20))
sheet.save(dst.replace(".png", "_preview.png"))
print(out.size)
