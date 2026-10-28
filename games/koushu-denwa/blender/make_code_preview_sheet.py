"""code_preview_*.png を 2列x3行 の一枚にまとめる（py make_code_preview_sheet.py）"""
import os
from PIL import Image, ImageDraw, ImageFont

A = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets'))
items = [('1', '暗い間1（数字1つ光る）'), ('2', '暗い間2'), ('3', '暗い間3'), ('4', '暗い間4（4つ光る）'), ('lit', '明るい間（張り紙の文字）')]
cw, ch, lab, gap = 800, 450, 44, 10
font = ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc', 26)
sheet = Image.new('RGB', (cw * 2 + gap * 3, 3 * (ch + lab) + gap * 4), (24, 24, 28))
d = ImageDraw.Draw(sheet)
for i, (k, t) in enumerate(items):
    x = gap + (i % 2) * (cw + gap)
    y = gap + (i // 2) * (ch + lab + gap)
    d.text((x + 6, y + 6), t, font=font, fill=(235, 235, 235))
    sheet.paste(Image.open(os.path.join(A, f'code_preview_{k}.png')).convert('RGB').resize((cw, ch), Image.LANCZOS), (x, y + lab))
sheet.save(os.path.join(A, 'code_preview_sheet.png'))
print('ok')
