# 第1話「引っ越し先の郵便受け」動画組み立て（Remotion）

第1話の動画を組み立てたときのRemotionプロジェクト一式。次回セッションで作り直したり、演出を調整するときに使う。

## 使う素材（このリポジトリ内）

- ナレーション：`docs/horror-scripts/audio/01-narration-draft.wav`
- 「コトン」効果音：`docs/horror-scripts/sfx/01-koton.wav`
- 背景写真：`docs/horror-scripts/images/01-yubinuke/*.jpg`
- 台本の文字起こし・タイミング・シーン割り当て：`src/scenes.json`（`build_scenes.py`で`01-narration-timing.json`から生成）

## 作り直す手順（クラウドの箱は毎回作り直されるので、そのたびに以下を行う）

```bash
mkdir -p work && cd work
npm init -y
npm install remotion @remotion/cli @remotion/renderer react react-dom

mkdir -p public/images src
cp <このフォルダ>/src/*.jsx <このフォルダ>/src/scenes.json src/
cp docs/horror-scripts/audio/01-narration-draft.wav public/narration.wav
cp docs/horror-scripts/sfx/01-koton.wav public/koton.wav
cp docs/horror-scripts/images/01-yubinuke/*.jpg public/images/

npx remotion render src/index.jsx Yubinuke01 out/01-yubinuke.mp4 \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
```

普通のChromeだと描画に失敗するので、必ず`--browser-executable`で headless_shell を指定すること。

## 演出のメモ

- 背景写真はシーンごとに切り替え、ゆっくり拡大・縮小するKen Burns風の動きを付けている（`Video.jsx`の`SceneImage`）
- テロップは普段白、「佐野様」が出る行と「次はあなたの番です」の行だけ赤字＋拡大＋小さく揺れる演出（`emphasis`フラグ）
- 「コトン」の効果音は、23行目「コトン、と小さな音がしたんです」の直後と、最後の51行目の直後の2か所（`scenes.json`の`sfx`）
- BGMは`docs/horror-scripts/bgm/01-wind-night.mp3`（効果音ラボの「wind2」、夜の風の音、83秒をループ）を低音量（16%）で全編に敷き、「次はあなたの番です」の場面の前後だけ一瞬無音にしている（`Video.jsx`の`bgmVolumeAt`）
  - 効果音ラボは商用利用・YouTube収益化もOK、クレジット表記は任意（それでも概要欄に記載済み）

## シーン割り当て（写真の使用順）

`build_scenes.py`の`scene_ranges`を参照。台本の場面に合わせて7枚の写真を時間軸に割り当てている。写真や順番を変えたいときはここを編集して`python3 build_scenes.py`を実行すると`scenes.json`が更新される。
