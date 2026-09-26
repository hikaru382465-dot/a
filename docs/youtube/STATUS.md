# YouTube「実話怪談ラジオ」 状況メモ

セッションの最初に読み、作業が終わったら「最終更新」と「進行中・次にやること」を書き換える。

最終更新：2026-09-26

## 現状

- チャンネル「実話怪談ラジオ」開設済み。アイコンはChatGPTで作ったものを使用
- 投稿済み動画：まだなし
- 企画・方針：`docs/horror-channel-plan.md`（ジャンルは人怖、役割分担もここ）
- 台本：
  - 第1話「引っ越し先の郵便受け」約4分 → `docs/horror-channel-plan.md` 内
  - 第2話「おすそ分けをくれる隣の奥さん」約4〜5分 → `docs/horror-scripts/02-osusowake.md`
  - VOICEVOXに読み込ませる1行1文のテキスト → `docs/horror-scripts/voicevox/`
- 作り方の手順書（ひかる向け）：`docs/horror-scripts/HOW-TO-MAKE.md`
- 第1話の投稿準備物（新規）：`docs/horror-scripts/01-yubinuke-upload-package.md`（タイトル案・概要欄コピペ文・タグ）、サムネイル下案 `docs/horror-scripts/thumbnails/01-yubinuke.svg`（プレビュー：同フォルダの`01-yubinuke-preview.png`）
- 第1話の「コトン」効果音：確定 → `docs/horror-scripts/sfx/01-koton.wav`（ひかるが実際の郵便受けを撮った動画から切り出した本物の音。台本の途中とラストの2か所で使う）
- 第1話のナレーション：**51行すべて完成** → `docs/horror-scripts/audio/01-narration-draft.wav`（3分7秒）、行ごとの開始・終了時間は`01-narration-timing.json`（テロップをぴったり合わせるのに使う）。抜けていた47番のセリフも録り直してもらい、組み込み済み
- 第1話の背景写真：**完成** → `docs/horror-scripts/images/01-yubinuke/`（ぱくたそ・Pixabayからひかるが厳選。外観・廊下2種・玄関・部屋の中・郵便受け2種の7枚）
  - 素材だけ届いて未採用のものは`/tmp`の一時フォルダに残っている（廃墟すぎる外観、繁華街の夜景、脅迫状風の貼り紙など）。今回は使わないが、別の話で使えそうなものもある

**第1話に必要な素材（ナレーション・効果音・背景写真）がすべて揃った。次はClaudeが動画を組み立てる番。**

## 進行中・次にやること

1. Claudeが動画に組み立てる（横長の本編、Remotion）← 今ここ
2. 本編の一番怖い場面を60秒に切り出して、縦長のショートを作る
3. 1本目の手順が固まったら、`skill-creator` で「怪談動画を作る」スキルにする

## 決めたこと

- 第1話のナレーションは**VOICEVOX「青山龍星」のしっとりスタイル**に決定。概要欄クレジットは`VOICEVOX:青山龍星`（`01-yubinuke-upload-package.md`に反映済み）
- 動画の組み立てはCapCut（ひかるの手作業）ではなく、**Remotion（Claudeが自動でやる）**で進める。理由：ひかるの編集時間をゼロに近づけたいため。トレードオフとして、テロップのタイミングはCapCutの自動字幕ほど精密には合わせられない可能性がある → 1本目を作ってみて、ズレが気になるようならCapCutに戻すことも検討する（`HOW-TO-MAKE.md`のCapCut手順は保険として残してある）
- 本編（横長・4〜5分）を先に作り、そこからショートを切り出す
- 声は必ずVOICEVOX（ひかるのPC）。Open JTalkは機械的すぎて不採用
- 画像はPixabayの実写をひかるが保存する。Claudeが描いた背景は「弱い」ので、写真が見つからない場面の補完だけ
- 人物のイラストは使わない
- テロップ：普段は白、決め台詞だけ赤字＋拡大＋揺れ。場面に合わせてGoogle Fontsの明朝体なども使う
- VOICEVOXを使ったら、概要欄に `VOICEVOX:キャラ名` のクレジットが必須

## Claude側の作業環境（クラウドの箱は毎回作り直されるので、そのたびに入れ直す）

- ffmpeg：`apt-get update && apt-get install -y ffmpeg`
- Remotion：作業用フォルダで `npm install remotion @remotion/cli @remotion/renderer react react-dom`
  - 描画は `--browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell` を付ける（普通のchromeは失敗する）
  - 入口のファイルで `registerRoot()` を呼ぶ
- Google Fontsは使える。音声合成サービスには、この環境からはつながらない
- ひかるが環境の「ネットワークアクセス」設定に`soundeffect-lab.info`と`pixabay.com`を追加済み（2026-09-26）
  - `soundeffect-lab.info`：つながるようになった。ただしmp3への直リンクだけだと403で弾かれるので、`curl -A "Mozilla/5.0" -e "https://soundeffect-lab.info/sound/various/"`のようにUser-AgentとRefererを付ける必要がある
  - `pixabay.com`：最初`pixabay.co`と打ち間違えていたのが原因で403だった。ひかるが`pixabay.com`に修正済み（2026-09-26）。ただし環境の設定変更は「新しいセッションから適用」なので、このセッションではまだ403のまま → 次の新しいセッションで`curl`で確認する
  - この設定は環境（クラウドの箱）ではなく別の場所にあるようで、箱を作り直しても消えない可能性がある
