#!/usr/bin/env python3
"""web/ の中身を、1枚のHTML（外部ファイルなし）にまとめる。
使い方: python3 build_single.py 出力先.html
claude.ai のページとして公開するとき、またはスマホにファイルで送るときに使う。"""
import re, sys, pathlib

here = pathlib.Path(__file__).parent
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "yobanashi-single.html")
html = (here / "index.html").read_text(encoding="utf-8")

css = (here / "style.css").read_text(encoding="utf-8")
body = re.search(r"<body>(.*)</body>", html, re.S).group(1)
body = re.sub(r"<script src=\"[^\"]+\"></script>\s*", "", body)
scripts = "\n".join((here / n).read_text(encoding="utf-8") for n in
                    ["data.js", "data2.js", "data3.js", "sound.js", "apps.js", "gimmicks.js", "game.js"])
import base64
for _w in ["wallpaper", "wallpaper_night", "wallpaper_red", "wallpaper_lit"]:
    css = css.replace(_w + ".jpg", "data:image/jpeg;base64," + base64.b64encode((here / (_w + ".jpg")).read_bytes()).decode())
scripts = scripts.replace("</script", "<\\/script")

page = f"""<title>投稿受付中</title>
<style>
{css}
html,body{{height:100%}}
</style>
{body.strip()}
<script>
{scripts}
</script>
"""
out.write_text(page, encoding="utf-8")
print("書き出しました:", out, f"({len(page)//1024} KB)")
