# 住人の歩く絵（art/res/<id>_walk.png：緑背景、4行＝前・左・後ろ・右 × 4コマ）→ res_art.js
# 絵が届いたら、RES に id を足して、もう一度実行する。顔の絵 art/res/<id>_face.png があれば、face も入れる
import base64, io, json, pathlib, sys
here = pathlib.Path(__file__).parent; sys.path.insert(0, str(here))
import make_chars
RES = ['toto', 'mina']
out = {}
for id in RES:
    p = here.parent / 'art' / 'res' / f'{id}_walk.png'
    if not p.exists(): continue
    out[id] = make_chars.build_green(p, ['down', 'left', 'up', 'right'], tone=False)
    f = here.parent / 'art' / 'res' / f'{id}_face.png'
    if f.exists():
        from PIL import Image
        im = Image.open(f).convert('RGBA'); b = io.BytesIO(); im.save(b, 'WEBP', quality=88); out[id]['face'] = 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()
(here / 'res_art.js').write_text('window.RAFT.resArt = ' + json.dumps(out) + ';\n', encoding='utf-8')
print('res_art.js', list(out), (here / 'res_art.js').stat().st_size)
