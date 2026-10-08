# スマホ用：index.html と部品を1枚にまとめた公開用HTMLを作る。使い方：python3 make_artifact.py 出力先.html
import re, sys, pathlib
here = pathlib.Path(__file__).parent
src = (here / 'index.html').read_text(encoding='utf-8')
style = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
body = re.search(r'<body>(.*?)<script src=', src, re.S).group(1)
files = ['../island/common.js', 'data.js', 'net_art.js', 'chars.js', 'sim.js', 'camera.js', 'water.js', 'light.js', 'floor.js', 'objects.js', 'buddy.js', 'drift.js', 'sound_data.js', 'sound.js', 'hud.js']
js = '\n'.join((here / f).read_text(encoding='utf-8') for f in files)
imap = re.search(r'<script type="importmap">.*?</script>', src, re.S).group(0)
mod = re.search(r'(<script type="module">.*?</script>)', src, re.S).group(1)
out = f'''<title>イカダの海暮らし</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DotGothic16&display=swap">
<style>
:root{{color-scheme:dark}}
{style}
html,body{{height:100%}}
body{{background:#0c1530;color:#e8dcb8}}
</style>
{body}
<script>
{js}
</script>
{imap}
{mod}
'''
pathlib.Path(sys.argv[1]).write_text(out, encoding='utf-8')
print(len(out), 'bytes')
