# 引き継ぎ（クラウドの会話 → ひかるのPCのClaude Code）

2026-10-17 時点。PCで新しく始める会話に、最初にこれを読ませる。

## 最初に貼るメッセージ（そのままコピー）
```
games/horror-arg/HANDOFF.md と games/horror-arg/STATUS.md と games/horror-arg/room/README.md を読んで、続きから進めて。
BlenderMCP はつないである（Blenderで開始ずみ）。
まず、いま Blender に何が開いているか確認して。
やることは「3D部屋の細部」から。大枠から細部へ、段階を分けて。毎回、画面を見て確認して。
```

## PCでの準備（最初の1回）
1. リポジトリを手元に取る（ブランチ名に注意。まだmainに入っていない）
   ```
   git clone https://github.com/hikaru382465-dot/a.git
   cd a
   git checkout claude/horror-arg-game-steam-dbsss9
   ```
2. uv を入れる（公式のインストーラ。pipではなく）。
3. `claude mcp add blender uvx blender-mcp`
4. Blender 4.x にアドオンを入れる：`uvx blender-mcp install-addon` → Blender の Edit → Preferences → Add-ons で「Interface: Blender MCP」を有効に。
5. Blenderを開き、3D画面で [N] → 「BlenderMCP」タブ → 開始（Start MCP Server / Connect to Claude）。
6. `a` のフォルダでClaude Codeを起動し、上の「最初に貼るメッセージ」を貼る。
- 確認：`claude mcp list` に `blender` が出る。

## いまの状態（ここまでにできたこと）
- ゲーム本体（ブラウザ版）：`web/`。5日・16本・謎6つ・エンディング3つ・ギミック・メール/SNS/検索（ヨルサガシ）。公開ページ（ひかるだけ）：ゲーム https://claude.ai/artifact/T2mtEGgsqjTrFQWki9wYd6 ／外のサイト https://claude.ai/artifact/KS4JomkiykW6ebpH7qTMae
- 3D部屋：`room/`。Blenderスクリプト `room/blender/build_room.py`（部屋・家具・小物）、汚しの共通ノードグループ `room/blender/wear_group.py`、材質ごとの強さ `room/blender/materials_proc.py`。参考絵 `room/reference/`。
- `room/export/room_proc.blend`：プロシージャルの質感版のBlenderファイル。`room/export/room_night.glb`：Godot用（画像の質感版）。

## 次にやること（順番）
1. **細部（形）**：本の背表紙の細かさ、キーボードのキーのくぼみ、ベッド・棚の木の色（薄いオレンジのまだらを、濃い茶に）、椅子・布団・カーテンの丸み・しわ、観葉植物の葉。参考絵（`room/reference/`）と比べながら。
2. **焼き込み**：プロシージャルの質感を、Godot用の画像（色・粗さ・凹凸）にする。PCのGPUで速く焼ける。焼いたものを `room_night.glb` に入れ直す。
3. Godotで見て、光を付け直す（表は `room/README.md`）。
4. 朝・夜の切りかえ（窓の外の絵と光の色）。
5. ゲームの「寝て起きる」場面とつなぐ（`DESIGN.md` に案）。

## 守ること（このリポジトリのルール）
- ひかるへの返事は、やさしい日本語。最小の返事（挨拶・前置きなし）。
- 作業は大枠から徐々に細部へ、段階に分けて、毎回ひかるに見せる。
- 道具のアドバイスを一言（今すぐ／あとで）。
- 作業の終わりに、`STATUS.md` の「最終更新」と「進行中・次にやること」を直して、コミットする。
- 画像は使わず、すべてプロシージャルで質感を作る（光る画面の中身・写真だけは絵）。
