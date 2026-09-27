import json

with open("src/scenes.json", encoding="utf-8") as f:
    full = json.load(f)

SHORT_START = 134.005  # line34開始：「そして、ドアが半分ほど開いたとき、」
SHORT_TITLE = "【実話】おすそ分けをくれる隣人の部屋に、貼られていたもの"
SHORT_OUTRO_PAD = 3.5  # 終わりに「続きは本編で」を出す時間
totalEnd = full["totalDuration"] + full["outroPad"]
SHORT_DUR = totalEnd - SHORT_START

def clip(items, key_start="start", key_end="end"):
    out = []
    for it in items:
        s, e = it[key_start], it[key_end]
        if e <= SHORT_START or s >= totalEnd:
            continue
        ns = max(s, SHORT_START) - SHORT_START
        ne = min(e, totalEnd) - SHORT_START
        new_it = dict(it)
        new_it[key_start] = round(ns, 3)
        new_it[key_end] = round(ne, 3)
        out.append(new_it)
    return out

captions = clip(full["captions"])
scenes = clip(full["scenes"])
if scenes:
    scenes[0]["start"] = 0.0
    scenes[-1]["end"] = round(SHORT_DUR, 3)

sfx = []
for s in full["sfx"]:
    if SHORT_START <= s["time"] < totalEnd:
        sfx.append({"time": round(s["time"] - SHORT_START, 3), "label": s["label"]})

data = {
    "shortStart": SHORT_START,
    "totalDuration": round(SHORT_DUR, 3),
    "outroPad": SHORT_OUTRO_PAD,
    "narrationOffset": SHORT_START,
    "title": SHORT_TITLE,
    "captions": captions,
    "scenes": scenes,
    "sfx": sfx,
}

with open("src/short_scenes.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("short duration:", round(SHORT_DUR, 2), "s")
print("captions:", len(captions))
print("scenes:", len(scenes))
print("sfx:", sfx)
