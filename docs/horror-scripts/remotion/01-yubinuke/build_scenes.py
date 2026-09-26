import json

lines_text = {
1: "これは、私が去年、一人暮らしを始めたときに体験した話です。",
2: "社会人になって、初めて借りたアパート。",
3: "築年数は古いけど、駅から近くて、家賃も安い。",
4: "内見のときは特に何も感じませんでした。",
5: "引っ越して一週間ほど経った頃、郵便受けを開けると、",
6: "見覚えのない名前宛ての手紙が届いていました。",
7: "「佐野様」と書かれています。",
8: "私の苗字ではありません。",
9: "前の住人宛ての誤配だろうと思って、",
10: "郵便受けの横にある「転居先不明」の箱に入れておきました。",
11: "でも、その翌週も、また同じ名前の手紙が届いていました。",
12: "今度は速達で。",
13: "不動産屋に電話をして聞いてみると、",
14: "「あの部屋、前の住人が退去してからもう半年経ってますよ。",
15: "郵便局にも転送届は出してもらってるはずなんですけどね」",
16: "と言われました。",
17: "半年前に退去した人宛ての手紙が、",
18: "なぜ今になって、しかも速達で届くのか。",
19: "少し気味が悪かったですが、その時はまだ、",
20: "「郵便局の手違いだろう」くらいにしか思っていませんでした。",
21: "異変に気づいたのは、それから数日後の深夜でした。",
22: "トイレに起きたとき、玄関の郵便受けのあたりから、",
23: "コトン、と小さな音がしたんです。",
24: "こんな時間に、誰かがポストに何かを入れている。",
25: "怖くなって、ドアスコープからそっと外を覗きました。",
26: "廊下には誰もいません。",
27: "でも、郵便受けの蓋が、まだ小さく揺れていました。",
28: "翌朝、恐る恐る郵便受けを開けると、",
29: "また「佐野様」宛ての手紙が入っていました。",
30: "消印はありません。",
31: "つまり、誰かが直接、手で投函したということです。",
32: "さすがに怖くなって、大家さんに相談しました。",
33: "大家さんは少し言いにくそうにしながら、こう言いました。",
34: "「実はその佐野さんって方、あなたの前にその部屋に住んでた方なんですけど……",
35: "退去の連絡もないまま、ある日突然いなくなってしまって。",
36: "荷物も置いたままだったので、家族の方に連絡して、",
37: "こちらで処分させてもらったんです」",
38: "「もしかして、その手紙を届けに来てるのって……」",
39: "そう聞くと、大家さんは黙ってしまいました。",
40: "その日を境に、私は郵便受けを見るのが怖くなりました。",
41: "それでも生活のために毎日確認しないわけにはいきません。",
42: "一週間後、いつものように郵便受けを開けると、",
43: "今度は「佐野様」ではなく、",
44: "私の名前が書かれた手紙が入っていました。",
45: "差出人の欄には、何も書かれていません。",
46: "中を開けると、一枚の紙にこう書かれていました。",
47: "「次はあなたの番です」",
48: "私はその日のうちに、あの部屋を出ました。",
49: "今でも、夜遅くに郵便受けを覗くたびに、",
50: "あの音を思い出します。",
51: "コトン、という、小さな音を。",
}

with open("/home/user/a/docs/horror-scripts/audio/01-narration-timing.json", encoding="utf-8") as f:
    timing = json.load(f)

emphasis_lines = {7, 29, 43, 47}

# scene image ranges (inclusive start line, exclusive handled by time)
scene_ranges = [
    (0.0, "ext-01-apartment.jpg"),
    (17.867, "mailbox-01-orange.jpg"),
    (45.344, "room-01-interior.jpg"),
    (72.864, "hallway-01-blurred.jpg"),
    (98.645, "mailbox-02-note-mesh.jpg"),
    (113.493, "entrance-01-intercom-note.jpg"),
    (145.419, "mailbox-01-orange.jpg"),
    (172.875, "mailbox-02-note-mesh.jpg"),
    (174.677, "hallway-02-bw-pipes.jpg"),
]

def image_for_time(t):
    img = scene_ranges[0][1]
    for start, name in scene_ranges:
        if t >= start:
            img = name
        else:
            break
    return img

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
    {"time": timing[22]["end"], "label": "koton-1 (line23 end)"},   # index 22 -> line 23 (0-indexed 22)
]
# find exact entries by line number to be safe
by_line = {t["line"]: t for t in timing}
sfx = [
    {"time": by_line[23]["end"] + 0.05, "label": "koton after line23"},
    {"time": by_line[51]["end"] + 0.35, "label": "koton after final line"},
]

scenes = []
for i, (start, name) in enumerate(scene_ranges):
    end = scene_ranges[i+1][0] if i + 1 < len(scene_ranges) else total_duration + 3.0
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
