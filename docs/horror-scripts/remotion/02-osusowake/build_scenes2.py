import json

lines_text = {
1: "これは、私が大学を卒業して、一人暮らしを始めた年の話です。",
2: "住んでいたのは、二階建ての小さなアパート。",
3: "隣の部屋には、五十代くらいの奥さんが一人で住んでいました。",
4: "引っ越しの挨拶に行ったとき、その奥さんはとても嬉しそうに、",
5: "「若い人が来てくれて安心だわ。何かあったら、いつでも言ってね」",
6: "と笑ってくれました。",
7: "それから、奥さんはよく「おすそ分け」をくれるようになりました。",
8: "筑前煮、きんぴらごぼう、炊き込みご飯。",
9: "どれも丁寧に作られていて、タッパーに入れて、",
10: "ドアノブに袋ごと掛けておいてくれるんです。",
11: "実家を出たばかりだった私には、それが本当にありがたかった。",
12: "タッパーを返すときには、お菓子を添えてお礼を言っていました。",
13: "最初に「あれ？」と思ったのは、ひと月ほど経った頃です。",
14: "タッパーを返しに行ったとき、奥さんがこう言いました。",
15: "「昨日はカレーだったのね。辛口が好きなの？",
16: "私は甘口派だから、今度甘口も食べてみて」",
17: "確かに、前の晩はカレーを作っていました。",
18: "匂いが廊下に出ていたのかな。",
19: "そう思って、そのときは笑って流しました。",
20: "でも、辛口だということまで、どうして分かったんだろう。",
21: "市販のルーの箱は、ゴミに出す前でした。",
22: "それから、奥さんの言葉が少しずつ気になるようになりました。",
23: "「最近、帰りが遅いのね。昨日は十一時四十二分だったでしょう」",
24: "「日曜日はずっと家にいたのね。電気、つけっぱなしだったから」",
25: "「あのピンクのカーディガン、似合ってたわよ」",
26: "ピンクのカーディガンを着たのは、一度だけ。",
27: "それも、近所のコンビニに行った五分くらいの間です。",
28: "十一時四十二分。",
29: "分単位で、帰宅の時間を覚えている。",
30: "私は、奥さんの前で、笑顔をつくるのが苦しくなっていきました。",
31: "決定的だったのは、ある土曜日の午後です。",
32: "いつものようにタッパーを返しに行くと、",
33: "その日は奥さんが出てくるまでに、少し時間がかかりました。",
34: "そして、ドアが半分ほど開いたとき、",
35: "奥さんの肩ごしに、部屋の中が見えてしまったんです。",
36: "玄関から続く廊下の壁一面に、",
37: "メモ用紙が、びっしりと貼られていました。",
38: "遠くて全部は読めませんでした。",
39: "でも、一番手前の一枚だけは、はっきり見えました。",
40: "「二〇二号室　帰宅　二十三時四十二分　ピンクのカーディガン」",
41: "二〇二号室。",
42: "私の部屋です。",
43: "奥さんは、私の視線に気づいたのか、",
44: "すっとドアを細くして、いつもと同じ笑顔で言いました。",
45: "「いつもありがとうね。また作ったら、持っていくから」",
46: "私は、その日のうちに実家に電話をして、",
47: "一週間後には、そのアパートを出ました。",
48: "奥さんには、何も言いませんでした。",
49: "引っ越し先も、もちろん教えていません。",
50: "新しい部屋での生活にも慣れた、ひと月後のことです。",
51: "仕事から帰ると、玄関のドアノブに、",
52: "見覚えのある袋が掛かっていました。",
53: "中には、タッパーがひとつ。",
54: "甘口のカレーが入っていました。",
55: "そして、ふたの上に、一枚のメモが貼られていました。",
56: "「お引っ越し先でも、お元気でね」",
}

with open("/home/user/a/docs/horror-scripts/audio/02-narration-timing.json", encoding="utf-8") as f:
    timing = json.load(f)

by_line = {t["line"]: t for t in timing}

# 奥さんが具体的な行動を言い当てる場面（じわじわ怖い）＋壁のメモの文面＋最後のメモ
emphasis_lines = {23, 24, 25, 40, 56}

scene_ranges = [
    (0.0, "ext-02-rusty-2story.jpg"),          # 導入：アパート外観
    (14.507, "ext-01-apartment-vending.jpg"),  # 引っ越しの挨拶
    (31.435, "food-02-osusowake.jpg"),         # おすそ分けが始まる
    (61.195, "food-01-curry.jpg"),             # カレーの一件
    (90.581, "hallway-01-dark-door.jpg"),      # 具体的すぎる発言が続く
    (126.72, "door-01-peek-inside.jpg"),       # 土曜日、ドアが半分開く
    (137.195, "wall-01-notes.jpg"),            # 壁一面のメモ
    (166.923, "door-01-peek-inside.jpg"),      # ドアが細くなる
    (175.456, "hallway-02-stairs.jpg"),        # 引っ越しを決意
    (193.024, "ext-01-apartment-vending.jpg"), # 新しい部屋
    (198.955, "food-01-curry.jpg"),            # タッパーが届く
    (203.797, "wall-01-notes.jpg"),            # 最後のメモ
]

captions = []
for t in timing:
    ln = t["line"]
    captions.append({
        "line": ln,
        "text": lines_text[ln],
        "start": t["start"],
        "end": t["end"],
        "emphasis": ln in emphasis_lines,
    })

total_duration = timing[-1]["end"]

sfx = [
    {"time": round(by_line[37]["start"] - 0.1, 3), "label": "paper-turn (wall of notes reveal, before line37)"},
    {"time": round(by_line[55]["end"] - 0.1, 3), "label": "paper-turn (final note reveal, before line56)"},
]

scenes = []
for i, (start, name) in enumerate(scene_ranges):
    end = scene_ranges[i + 1][0] if i + 1 < len(scene_ranges) else total_duration + 3.0
    scenes.append({"start": start, "end": end, "image": name})

data = {
    "totalDuration": total_duration,
    "outroPad": 3.0,
    "captions": captions,
    "scenes": scenes,
    "sfx": sfx,
}

with open("src/scenes.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("total duration", total_duration)
print("num captions", len(captions))
print("num scenes", len(scenes))
print("sfx", sfx)
