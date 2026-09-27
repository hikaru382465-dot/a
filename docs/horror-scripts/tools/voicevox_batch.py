# -*- coding: utf-8 -*-
"""
VOICEVOXの台本テキストを自動で音声化するスクリプト。

使い方：
  1. VOICEVOXを起動しておく（エンジンが裏で立ち上がるまで少し待つ）
  2. 台本テキストファイルを voicevox_batch.bat にドラッグ＆ドロップする
  3. 同じフォルダに「台本名_audio.zip」ができるので、それをそのままチャットに送る

台本テキストの書き方（1行1セリフ）：
  speaker_key|セリフ
例：
  aoyama|これは、私が去年、一人暮らしを始めたときに体験した話です。
  himari|「若い人が来てくれて安心だわ」

speaker_key の意味は下の SPEAKERS で決める。
「|」を書かずにセリフだけ書いた行は、DEFAULT_SPEAKER が使われる（1人語りの台本ならこれでOK）。
"""

import json
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ENGINE_URL = "http://127.0.0.1:50021"

# キャラクターを増やしたいときはここに追加する。
# (名前, スタイル名) はVOICEVOXの表示とまったく同じ文字列にすること。
SPEAKERS = {
    "aoyama": ("青山龍星", "しっとり"),
    "aoyama_whisper": ("青山龍星", "囁き"),  # ラストの決め台詞など、恐怖を強調したい行に使う
    "himari": ("冥鳴ひまり", "ノーマル"),
}
DEFAULT_SPEAKER = "aoyama"


def get_speaker_id_map():
    with urllib.request.urlopen(f"{ENGINE_URL}/speakers") as res:
        speakers = json.loads(res.read())
    id_map = {}
    for sp in speakers:
        for style in sp["styles"]:
            id_map[(sp["name"], style["name"])] = style["id"]
    return id_map


def synth_one(text, style_id):
    query_url = f"{ENGINE_URL}/audio_query?text={urllib.parse.quote(text)}&speaker={style_id}"
    req = urllib.request.Request(query_url, method="POST")
    with urllib.request.urlopen(req) as res:
        query = res.read()

    synth_url = f"{ENGINE_URL}/synthesis?speaker={style_id}"
    req = urllib.request.Request(
        synth_url, data=query, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        return res.read()


def main():
    if len(sys.argv) < 2:
        print("台本テキストファイルを voicevox_batch.bat にドラッグ＆ドロップして実行してください。")
        input("Enterキーで終了...")
        return

    script_path = Path(sys.argv[1])

    try:
        print("VOICEVOXのキャラクター一覧を取得中...")
        id_map = get_speaker_id_map()
    except Exception:
        print("VOICEVOXに接続できませんでした。VOICEVOXを起動してから、もう一度実行してください。")
        input("Enterキーで終了...")
        return

    lines = [
        line.rstrip("\n")
        for line in script_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    out_dir = script_path.parent / (script_path.stem + "_audio")
    out_dir.mkdir(exist_ok=True)

    manifest = []
    for i, line in enumerate(lines, start=1):
        if "|" in line:
            key, text = line.split("|", 1)
        else:
            key, text = DEFAULT_SPEAKER, line
        key = key.strip()
        text = text.strip()

        if key not in SPEAKERS:
            print(f"[{i}] 不明なspeaker_key『{key}』です。スクリプト内のSPEAKERSに追加してください。スキップします。")
            continue

        name, style = SPEAKERS[key]
        style_id = id_map.get((name, style))
        if style_id is None:
            print(f"[{i}] VOICEVOXに『{name}（{style}）』が見つかりません。名前・スタイル名を確認してください。スキップします。")
            continue

        print(f"[{i}/{len(lines)}] {name}（{style}）: {text[:20]}...")
        wav_bytes = synth_one(text, style_id)

        wav_name = f"{i:03d}.wav"
        (out_dir / wav_name).write_bytes(wav_bytes)
        manifest.append({"line": i, "speaker": key, "text": text, "file": wav_name})

        time.sleep(0.1)  # エンジンへの連続アクセスを少し緩める

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    zip_path = script_path.parent / (script_path.stem + "_audio.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for wav_file in sorted(out_dir.glob("*.wav")):
            zf.write(wav_file, wav_file.name)
        zf.write(out_dir / "manifest.json", "manifest.json")

    print()
    print(f"完了！ {len(manifest)}個の音声ファイルを作りました。")
    print(f"このZIPファイルをそのままチャットに送ってください：")
    print(zip_path)
    input("Enterキーで終了...")


if __name__ == "__main__":
    main()
