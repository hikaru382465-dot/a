# 日記帳の絵（ひかるの絵：白紙ページ版）→ diary_art.js。そのまま背景に使う（切りぬかない）
import base64, io, json, pathlib
from PIL import Image
here = pathlib.Path(__file__).parent
im = Image.open(here.parent / 'art' / 'diary' / 'book.png').convert('RGB'); b = io.BytesIO(); im.save(b, 'JPEG', quality=86, optimize=True)
(here / 'diary_art.js').write_text('window.RAFT.diaryArt = ' + json.dumps('data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()) + ';\n')
print('diary', len(b.getvalue()))
