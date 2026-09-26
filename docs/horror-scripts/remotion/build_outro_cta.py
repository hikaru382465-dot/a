import json

# 全話共通のエンディングCTA（登録・高評価ナレーション＋テロップ）のデータを生成する。
# docs/horror-scripts/audio/outro-cta-timing.json（音声の行タイミング）を元に、
# 各話のRemotionプロジェクトの src/outro_cta.json にコピーして使う。

with open("/home/user/a/docs/horror-scripts/audio/outro-cta-timing.json", encoding="utf-8") as f:
    timing = json.load(f)

TAIL_PAD = 1.0  # 最後の余白（フェードアウト用）
total_duration = timing[-1]["end"]

captions = [
    {"line": t["line"], "text": t["text"], "start": t["start"], "end": t["end"]}
    for t in timing
]

# 3行目「気に入っていただけたら、チャンネル登録と高評価を、お願いします。」の中で
# 「チャンネル登録」「高評価」がズームインするタイミング（文字数比で概算し、多少余裕を持たせた）
zoom_words = [
    {"word": "チャンネル登録", "start": 7.85, "end": 9.15},
    {"word": "高評価", "start": 9.15, "end": 11.2},
]

data = {
    "totalDuration": total_duration,
    "tailPad": TAIL_PAD,
    "captions": captions,
    "zoomWords": zoom_words,
}

with open("src/outro_cta.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("outro cta total duration", total_duration + TAIL_PAD)
print("zoom words", zoom_words)
