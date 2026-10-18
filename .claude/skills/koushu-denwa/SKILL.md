---
name: koushu-denwa
description: ひかるの3Dホラーゲーム「公衆電話」（Unreal Engine 5.8）の作業手順。ゲーム、公衆電話、幽霊、金庫、ダイヤル、ガラスの文字、Unreal、Blender、setup_game_fp、kd_game、EngineWire などの話が出たら必ず使う。games/koushu-denwa/ の STATUS.md と ROADMAP.md が本体。
---

# 公衆電話ゲームの作業手順（games/koushu-denwa/）

ひかるはUnrealをPCで動かして試し、画面とログを送ってくる。クラウドのClaudeはUnrealを動かせない。**書く→ひかるが試す→結果で直す**の繰り返し。

## 作業の前に
1. `STATUS.md` の「進行中・次にやること」を読む。決まったことは会話ではなくメモに残す。
2. 返事は最小。前置き・結びなし。直しは Before / After の差分だけ。やさしい日本語。
3. ゲームの返事には「今すぐ／あとで」の道具のアドバイス（Blender・エンジン・無料素材・ブラウザ版の線引き）を一言つける。
4. 新しく作り始める・設計が大きく変わるときだけ Opus で計画。小さな直しは計画を省く。

## ファイルの役割（unreal/ と blender/）
| ファイル | 役割 |
|---|---|
| `unreal/setup_game_fp.py` | 世界を組み立てる（取り込み・配置・材質・光）。`step()/setp()/spawn()/tag_actor()` の流れ。設定値は先頭の定数と `Saved/kd_settings.json` |
| `unreal/kd_game.py` | 遊んでいる間の動き（tick）。歩き、ダイヤル、電話、金庫、幽霊、フラグ |
| `blender/*.py` | 3Dと絵を作る。bpy で書き出す（FBX・PNG）。`ghost_face.py`（幽霊）、`make_dial_safe.py`（金庫）、`make_game_textures.py`（ガラス文字）、`make_sounds.py`（音） |
| `assets/` | 出来上がりの素材。買った素材はGitHubに置かない |

## ひかるが決めたこと（変えない）
- 金庫は電話ボックスの中に1つだけ。外側ダイヤル L19→R3→L8、中の16ボタン箱 2→15→4→9
- 本は電話ボックスの中。幽霊はしゃべらない。エンディングは3つ
- 謎解きのイベントは「フラグ」で進める
- ブランチは `claude/earning-with-claude-code-opsfwg`

## ひかるのPCで動かす手順
1. GitHub Desktop で Pull origin。
2. Unreal のコマンド欄で、**フルパスで** `py "C:/…/unreal/setup_game_fp.py"`（`…/` の相対パスは失敗する）。
3. 続けて `kd_game.py` を実行して遊ぶ。
4. 出力ログと画面を送ってもらう。見るログ：「ガラスの面の位置:」「ダイヤル専用カメラに切りかえました」。

## 作り方の決まり
- **Unreal Python**：`unreal` の API は5.8で変わる。`HitResult` は `to_tuple()`（point=5, normal=7, actor=9）。ハーネスの属性は `getattr` で守る。
- **毎フレーム検索しない**：tickの中で `Find`/`GetComponent` 相当を呼ばず、最初に取って保存する。
- **しかけは部品化**：イベントはフラグ＋再利用できる部品で。
- **壁抜け対策**：歩きは `clamp_in_booth` で内側に収める（`KD_BoothInner`、`PAWN_RADIUS=22`）。
- **調整値は定数にする**：`PHONE_KEY_*`、`GHOST_YAW/GHOST_Z`、`SAFE_LID_SIGN`、`GLASS_GAP` など。実機の結果を見て1つずつ直す。
- **Blender**：非破壊（モディファイア）優先。操作の説明にはショートカットを添える（例：[G] > [Z]）。ヘッドレスは venv の bpy、確認画像は Cycles CPU。
- **見た目**：ホラー向け低照度3点照明（Key/Fill/Rim）、ポストプロセス、PBRの Normal / Roughness の具体値を手順に入れる。
- **ドライテスト**：クラウドでは `unreal` を偽物（mock）にして流れだけ確認する。本物の確認はひかるのPCで。

## よくある失敗と直し方
| 症状 | 直し方 |
|---|---|
| 壁ぎわでガタガタ | `booth_limits` / `clamp_in_booth`、カプセルの半径を小さく |
| ガラスの文字が浮く | ガラスの実測の面（`glass_halves()`）＋ `GLASS_GAP`、古い位置を消す `RESET_POSTERS=True` |
| ダイヤルが見えない | 手で回した金庫に向けず、専用カメラ `KD_DialCam` を使う |
| 電話のボタンがずれる | `PHONE_KEY_DEBUG=True` で枠を見て `PHONE_KEY_U0/Z0/W/H` を直す |
| 金庫のフタが逆に開く | `SAFE_LID_SIGN` の符号を反転 |
| 幽霊の向き・高さ | `GHOST_YAW` / `GHOST_Z` |
| バイナリ素材が時刻だけ違う | 作り直さず `git checkout` で戻す |
| 25MB超でブラウザ投稿できない | GitHub Desktop で push |

## 作業の終わりに
`STATUS.md` の「最終更新」と「進行中・次にやること」を書き換え、工程が進んだら `ROADMAP.md` も更新してコミット。
