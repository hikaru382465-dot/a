import json

with open("/home/user/a/docs/horror-scripts/audio/03-narration-timing.json", encoding="utf-8") as f:
    timing = json.load(f)

by_line = {t["line"]: t for t in timing}

# 決め台詞・恐怖の核心（赤字・拡大・揺れ）
emphasis_lines = {39, 50, 69, 74, 75}

scene_ranges = [
    (0.0, "ext-01-night-lit-windows.jpg"),        # 導入：アパート外観
    (42.400, "moving-01-boxes.jpg"),              # 引っ越し・入居
    (56.021, "entrance-01-shoes.jpg"),            # 玄関の電気（違和感の始まり）
    (76.331, "window-01-night.jpg"),              # 窓が閉まっている
    (82.592, "entrance-01-shoes.jpg"),            # 靴が並べ直されている
    (100.651, "hallway-01-vending-dark.jpg"),     # 廊下の足音
    (112.277, "kitchen-01-fridge-night.png"),     # 冷蔵庫のプリンが消える
    (131.861, "silhouette-01-woman-night.jpg"),   # 夜、外に立つ女性
    (149.536, "entrance-01-shoes.jpg"),           # 防犯カメラ設置
    (172.768, "phone-01-hand.jpg"),               # SNSで前の住人を検索
    (188.885, "hallway-01-vending-dark.jpg"),     # 大家さんに相談・合鍵の話
    (222.720, "entrance-01-shoes.jpg"),           # 鍵を交換
    (234.645, "mirror-01-dirty-atmospheric.jpg"), # 「おかえり」の鏡
    (257.216, "hallway-01-vending-dark.jpg"),     # 友人宅に泊まり、帰宅
    (269.952, "table-01-mug.jpg"),                # テーブルの上のマグカップ
    (285.749, "entrance-01-shoes.jpg"),           # 警察に連絡
    (304.192, "ext-02-eerie-stairwell.jpg"),      # 大家さんの追加調査・真相
    (336.608, "entrance-01-shoes.jpg"),           # 引っ越しを決意
    (343.947, "moving-01-boxes.jpg"),             # 引っ越し当日
    (354.379, "phone-01-hand.jpg"),               # 知らない番号からの電話
    (366.421, "ext-03-night-alt.jpg"),            # 新しい部屋
    (382.027, "conbini-01-night.jpg"),            # 近所のコンビニで見かける
]

captions = []
for t in timing:
    ln = t["line"]
    captions.append({
        "line": ln,
        "text": t["text"],
        "start": t["start"],
        "end": t["end"],
        "emphasis": ln in emphasis_lines,
    })

total_duration = timing[-1]["end"]

scenes = []
for i, (start, name) in enumerate(scene_ranges):
    end = scene_ranges[i + 1][0] if i + 1 < len(scene_ranges) else total_duration + 3.0
    scenes.append({"start": start, "end": end, "image": name})

data = {
    "totalDuration": total_duration,
    "outroPad": 3.0,
    "captions": captions,
    "scenes": scenes,
    "sfx": [],
}

with open("src/scenes.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("total duration", total_duration)
print("num captions", len(captions))
print("num scenes", len(scenes))
