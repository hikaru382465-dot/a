#!/usr/bin/env python3
"""外のサイト「夜ばなし投稿館」（ARGの本物の公開側）を、1枚のHTMLに書き出す。
使い方: python3 site/build_site.py 出力先.html
投稿の文章は web/data.js と web/data2.js から読む（ゲームと同じものを公開サイトに載せる）。"""
import base64, io, json, pathlib, random, subprocess, sys, unicodedata

here = pathlib.Path(__file__).parent
web = here.parent / "web"
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "yobanashi-site.html")

# --- ゲームの文章を取り出す ---
js = """
global.window={};require('%s/data.js');require('%s/data2.js');
const D=window.GAME_DATA,E=window.GAME_EXTRA;
const posts=D.posts.filter(p=>typeof p.body!=='function'&&p.day<=4).map(p=>({id:p.id,title:p.title,author:p.author,time:p.time,body:p.body,comments:(E.comments[p.id]||[])}));
console.log(JSON.stringify({posts,pass:D.passphrase,site:D.siteName.replace('（仮）','')}));
""" % (web, web)
data = json.loads(subprocess.check_output(["node", "-e", js]).decode())

# --- ブログの暗号：ひとつ後ろの文字にずらす（あ→い）。濁点は残す ---
ROWS = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
def shift(text, n=1):
    r = []
    for ch in unicodedata.normalize("NFD", text):
        i = ROWS.find(ch)
        r.append(ROWS[(i + n) % len(ROWS)] if i >= 0 else ch)
    return unicodedata.normalize("NFC", "".join(r))
secret = shift("あたまのもじを ならべて")

# --- 隠し文字つきの写真（コントラストを上げると読める。ほとんど見えない） ---
def hidden_photo():
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    W, H = 720, 480
    rnd = random.Random(11)
    img = Image.new("RGB", (W, H), (9, 11, 16))
    d = ImageDraw.Draw(img)
    for y in range(H):
        c = int(9 + 10 * y / H); d.line([(0, y), (W, y)], fill=(c, c + 2, c + 6))
    d.rectangle([0, 330, W, H], fill=(20, 26, 38))
    d.rectangle([180, 120, 360, 250], fill=(120, 150, 205))      # モニター
    d.rectangle([190, 130, 350, 142], fill=(60, 100, 190))
    d.ellipse([430, 210, 490, 280], fill=(4, 6, 10))              # 後ろ姿
    d.polygon([(380, 400), (400, 300), (520, 300), (545, 400)], fill=(4, 6, 10))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    # 隠し文字：背景との差は 3 だけ
    font = None
    for p in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "/usr/share/fonts/opentype/unifont/unifont_jp.otf"]:
        try: font = ImageFont.truetype(p, 44); break
        except Exception: pass
    layer = Image.new("L", (W, H), 0); ld = ImageDraw.Draw(layer)
    ld.text((60, 60), "十六人目は あなた", fill=255, font=font)
    px = img.load(); lp = layer.load()
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            n = rnd.randint(-2, 2)
            k = 3 if lp[x, y] > 128 else 0
            px[x, y] = (max(0, r + n + k), max(0, g + n + k), max(0, b + n + k))
    buf = io.BytesIO(); img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
photo = hidden_photo()

blog = [
  {"title": "今日から、管理人です", "date": "4年前", "body": ["前の管理人さんから、引き継ぎを受けました。", "毎晩、届いた怪談を読んで、承認か却下を選ぶだけの仕事です。簡単そうです。", "ただ、「数えなおしたら、ひとつ多かった」というメモだけが、ずっと気になっています。"]},
  {"title": "却下について", "date": "3年前", "body": ["却下した投稿が、次の日に戻ってきます。何度却下しても、戻ってきます。", "今日で十一回目です。どの投稿者も、同じ言い回しで書いてくる。", "明日、十二回目を押すか、承認するか、決めます。"]},
  {"title": "（下書き）最後の更新", "date": "3年前", "body": ["これが最後の更新です。写真を一枚だけ載せます。", "明るくして、見てみてください。", "それから、メモを一行だけ。ひとつ前の文字にもどして読んでください。"], "photo": True, "secret": secret},
]
hidden = [
  "最初に、このサイトに投稿したのは、私です。",
  "十年前、眠れない夜に、ひとつだけ、怖い話を書きました。誰にも読まれなくていい、と思っていました。",
  "ところが、翌朝には、別の名前で、同じ書き方の投稿が、もうひとつ届いていました。それから毎晩、ひとつずつ、増えました。",
  "管理人を何度か替えましたが、替えるたびに、私の投稿者の数も、増えました。数えなおしたら、ひとつ多かった。",
  "あなたが来る前から、見ていたのよ。",
  "十六人目の投稿者は、いま、この画面を見ているあなたです。承認も、却下も、もう、必要ありません。",
]

html = open(here / "site_template.html", encoding="utf-8").read()
html = html.replace("/*DATA*/null", json.dumps({"posts": data["posts"], "blog": blog, "hidden": hidden, "pass": data["pass"], "site": data["site"], "photo": photo, "accept": [data["pass"], "あなたが来る前から見ていたのよ"]}, ensure_ascii=False))
out.write_text(html, encoding="utf-8")
print("書き出しました:", out, f"({len(html)//1024} KB)", "| 暗号:", secret)
