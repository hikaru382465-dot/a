import json

with open("src/scenes.json", encoding="utf-8") as f:
    full = json.load(f)

SHORT_START = 127.456  # line 35 start: "退去の連絡もないまま、ある日突然いなくなってしまって。"
SHORT_TITLE = "【実話】引っ越し先の郵便受けに届いた、知らない名前の手紙"
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
# extend first scene back to 0 and last scene forward to end (avoid gaps at boundaries)
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
    "outroPad": 0.0,
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
