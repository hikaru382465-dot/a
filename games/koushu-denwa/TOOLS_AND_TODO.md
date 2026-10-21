# 道具の導入と、これからの作業まとめ（2026-10-14）

## A. 道具：導入する・あとで考える・要らない

### 導入する（優先順）
| 順 | 道具 | 何のため | 状態・注意 |
|---|---|---|---|
| 1 | **Fab / BlenderKit の無料素材** | 本・電話帳・小物・材質を、ゼロから作らず、ライブラリから持ってくる。私（Claude）は「選ぶ・大きさをそろえる・置く・当たり判定」の係 | すぐ使える。ライセンス（商用利用・表記）は素材ごとに確かめる |
| 2 | **EngineWire（ChiR24/Unreal_mcp）** | Claude が、ひかるの Unreal を直接見て動かす（画面の写真・ログの往復を減らす） | UE 5.8 対応と書いてある（β版）。5.8 用の zip が無ければ自分で作る必要あり。先にプロジェクトをバックアップ。手順は下の「導入手順」 |
| 3 | **Blender MCP（公式）＋BlenderKit** | 画面を見ながらモデルを作る・素材を並べる | 2 が動いてから。配布元とバージョンを確かめる |

### あとで考える
- **Meshy**（有料のネットのサービス）：幽霊の人型を、リグ・歩き付きで作るとき
- **CHORD**（1枚の画像から凹凸・粗さの画像を作る）：材質をさらに良くしたいとき。8GBのグラボで動くか要確認
- **ACE-Step / Freesound**：環境音・BGM。手軽さは Freesound の無料素材（safe dial click、phone cord など）
- **stable-fast-3d**：本や小物を写真から3D化したいとき（8GBで動くか要確認）

### 要らない（今のゲームには）
Unity / Godot 系、世界生成AI（Hunyuan-GameCraft・Matrix-Game・HY-World）、スプラット、Omniverse、three.js 系、ゲーム内AI（幽霊は喋らない）、口の動き（Audio2Face）、49人エージェント、C++スキル集、Hunyuan3D / TRELLIS.2（グラボのメモリが足りない見込み）

### EngineWire 導入手順（ひかるのパソコン）
1. プロジェクトを丸ごとコピーして残す（バックアップ）
2. GitHub `ChiR24/Unreal_mcp` の Releases から、`EngineWire-plugin-…zip`（v0.6）を取る
3. 解凍して `EngineWire` フォルダを `プロジェクト\Plugins\` に入れる
4. Unreal を開く（右下「MCP off」）。「Engine modules cannot be compiled at runtime」が出たら Visual Studio で1回ビルド
5. 編集 → プロジェクト設定 → プラグイン → EngineWire →「Enable Native MCP Server」にチェック → 再起動（右下「MCP :3000 (0)」）
6. `プロジェクト\Saved\MCP\capability-token` を開き、中身をコピー（パスワード扱い）
7. Claude Code なら：`claude mcp add --transport http unreal-engine http://127.0.0.1:3000/mcp --header "X-MCP-Capability-Token: <token>"`
   Claude Desktop なら：Node.js 20.19以上を入れ、設定ファイルに `npx -y unreal-engine-mcp-server@beta`（`UE_PROJECT_PATH` を設定。`@beta` は消さない）
8. 「いまのレベルのアクターの一覧を出して」と頼んで確かめる（右下 `MCP :3000 (1)`）

## B. ゲーム：これからの作業

### すぐ（今の流れ）
1. 謎の鎖の続き（`unreal/GAME_PLAN.md` 末尾の「決定版」。謎は8つ・約20分）
   - 段階2：電話（0〜9で番号、10円3枚・117/177/104/110/119/0115、0714）
   - 段階3：金庫の中の箱（1〜16のボタンを 2→15→4→9）と、赤い封筒の4けた
   - 段階4：液晶の謎（110/119で「ソト ヒダリ ミギ ヒダリ」）、暗い間だけ見える蛍光の文字
   - 段階5：張り紙の貼られる順番、ヒント3段階、エンド3つ（脱出／行方不明／プロテイン＋2929）
2. 追加の仕掛け：ガラスの指跡、受話器のゆれ（受話器を別の部品にする）、足元のメモ、会員カード
3. 本と電話帳など小物の見た目を、ライブラリの素材に置き換える（ひかるが選んだ名前を教えてもらう）

### 直しておきたい・未解決
- ふつうの歩き（W A S D）が効かなかった根本原因（いまは「自分で動かす歩き」で歩ける）。候補：キー割り当て（IMC_Default / IA_Move）、歩く処理の壊れ
- 木・岩の当たり判定（`kd_trees_collision.py`。実行して確認）
- `kd_settings.json`：`PUZZLE_COUNT` を8にする、`FLASH_OUTSIDE=0.03` のとき中は暗すぎないか（`FLASH_INSIDE` を上げる）

### あとで（作り込み）
- 幽霊のキャラ（Meshy、または Blender＋Mixamo）
- 効果音・環境音の入れ替え（Freesound）
- ポストプロセス（色収差・うすいフォグ・ボリュメトリックライト）、3点照明（Key/Fill/Rim）
- タイトル画面の「スタート」→ `L_Main`
- Python の試作 → Blueprint へ移す
- 公開（Steam など）の準備：素材のライセンス確認、買った素材（Unity Asset Store の街の小物）は GitHub に上げない

## C. ルール（確認用）
- 買った素材・ひかるの個人データは、GitHub に上げない
- 変えた数字は `Saved\kd_settings.json` に。手で動かした位置は、レベルを保存（Ctrl+S）
- 作業の前に、レベルのバックアップ（コピー）
