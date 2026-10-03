# Unreal Engine 5 に持っていく手順（電話ボックス・電話機）

## 0. 最初に：起動時の警告「Visual C++ redistributable ... is outdated」が出たとき

ひかるのパソコンで出た警告。直さないと不安定になることがあるので、先に直す。

1. 警告の [OK] を押して、Unreal を一度閉じる
2. エクスプローラーで、Unreal のインストール先の次のファイルを探す
   `C:\Program Files\Epic Games\UE_5.x\Engine\Extras\Redist\en-us\vc_redist.x64.exe`
   （`5.x` は入れた版。場所が違えば、Epic Games Launcher の Unreal の「▼ → 管理（Manage）」→ 「Show in Folder」で開ける）
3. `vc_redist.x64.exe` をダブルクリック → 「同意する」にチェック → 「インストール」
4. 終わったら **パソコンを再起動**（求められなくてもしておく）
5. もう一度 Unreal を起動。警告が出なければ成功

## 1. 自動セットアップ（おすすめ・ここから）

`unreal/setup_phonebooth.py` を1回実行すると、取り込み・材質・配置・光・霧・ドアの回転軸までまとめてやる。

1. Unreal を起動 → 新しいプロジェクト：「ゲーム」→「空白（Blank）」→ Blueprint／Desktop／Maximum Quality／スターターコンテンツ オフ／レイトレーシング オフ
2. 上のメニュー「編集 → プラグイン」→ 検索「Python」→ **Python Editor Script Plugin** をオン → 再起動
3. 画面下の「Output Log」を開く → 入力欄の左を「Cmd」にして、次を貼って Enter（パスは自分のリポジトリの場所に。区切りは `/`）
   `py "C:/Users/あなた/…/a/games/koushu-denwa/unreal/setup_phonebooth.py"`
4. 終わると Output Log に `[KD] SUMMARY: …` と出る。全部 OK ならレベル `L_Booth` ができている
5. 失敗があれば、Output Log の検索欄に `KD` と入れて、出た行を全部コピーして Claude に送る（`Saved/Logs/KD_setup.txt` を送ってもよい）

⚠ Claude は Unreal を実行できないため、このスクリプトは疑似の環境でしか試せていない。名前の違いでエラーが出たら、ログを送ってもらえば直す。

ドアの開き：`DoorHinge` を選んで Details の Rotation の Yaw を 100 か -100 にすると、開く向きを確かめられる。

以下は、スクリプトを使わず手作業でやる場合の手順（スクリプトが動かないときの予備）。

ひかるのパソコンに Unreal Engine 5 が入っているので、Blenderで作ったモデルをそのまま持っていける。

⚠ この手順は Claude が Unreal の画面で実際に試せていない（クラウドで動いているため）。
画面の名前や場所が違ったら、画面を写真で送ってほしい。そこから手順を直す。

## 2. 用意するファイル（このリポジトリの中）

| ファイル | 中身 |
|---|---|
| `assets/unreal/PhoneBooth.fbx` | 電話ボックス＋電話機＋料金案内板＋台（画像を中に入れてある） |
| `assets/tex/*.png` | 元の画像（パネルの印刷、液晶、テンキー、本体の緑、注意シール、料金板） |

FBXの中の名前：`Door`（蝶番が原点なので、回すとそのままドアが開く）、`Booth_Frame`、`Booth_Glass`、`Booth_Roof`、
`Booth_Interior`（柱・台・電話帳）、`Phone_Body`、`Phone_Panel`、`Phone_LCD`、`Phone_Keys`、`Phone_Details`、`Phone_Handset`、`Phone_Cord`

## 3. 手作業：プロジェクトを作る

1. Unreal Engine 5 を起動 → 「ゲーム」→ 「空白（Blank）」
2. 設定：Blueprint／Desktop／**Maximum Quality**／スターターコンテンツは **オフ**／レイトレーシングは **オフ**
3. 作れたら、上のメニュー「編集 → プロジェクト設定」で次を確認
   - Rendering → Dynamic Global Illumination Method = **Lumen**
   - Rendering → Reflection Method = **Lumen**
   - Rendering → Shadow Map Method = **Virtual Shadow Maps**
   - Rendering → 「Support Hardware Ray Tracing」= **オフ**（RTX 2070 SUPER では重いので）

## 4. 手作業：モデルを入れる

1. コンテンツブラウザで右クリック → 「Import to /Game/…」→ `PhoneBooth.fbx` を選ぶ
2. 設定画面で：
   - **Combine Meshes**（メッシュの結合）= **オフ**（名前を残すため）
   - Import Materials = オン／Import Textures = オン
   - Generate Missing Collision = オン
   - Build Nanite = オン（細かい形をそのまま出せる。ガラスは後で外す）
3. 入ったら、レベルにドラッグして置く。大きさは1メートル = 100ユニットで合っているはず（電話ボックスの高さ 約230）

## 5. 手作業：材質を直す（ここが見た目の勝負）

FBXから来る材質は簡単なものなので、次の3つだけ手で直す。

- **ガラス（Booth_Glass、Doorの中のガラス）**：材質を開いて Blend Mode = **Translucent**、Lighting Mode = **Surface ForwardShading**、
  Roughness = 0.03、Opacity = 0.12〜0.2、Specular = 0.6。Nanite は外す
- **液晶（Phone_LCD）**：材質の Emissive Color に液晶の画像（`phone_lcd.png`）をつなぎ、倍率を 3〜5 にする
- **蛍光灯（Booth_Frame の中の Tube 材質）**：Emissive Color = 白（倍率 30〜50）。ちらつかせたいときは Material Parameter Collection か、材質のパラメーターを Blueprint から変える

## 6. 手作業：光と空気（写真のようにする）

1. レベルに「**Exponential Height Fog**」を置く（Volumetric Fog = オン、Fog Density = 0.02〜0.05）
2. 「**Post Process Volume**」を置き、Infinite Extent = オン
   - Exposure → Metering Mode = Manual、Exposure Compensation を 1〜3 くらいで調整
   - Bloom、Film Grain、Vignette、Chromatic Aberration を少しずつ足す
3. 電話ボックスの中に **Rect Light** を蛍光灯の位置に2個置く（色は少し緑がかった白）
4. 森：Fab（Epic Games Launcher → Fab）で「Megascans」の松の木・土・草・落ち葉をとる（Nanite対応の無料素材が多い）

## 7. ゲームのしくみを Blueprint に置きかえる（あとで）

いまブラウザ版（`index.html`）に入っているしくみは、Unrealでは次のように作りなおす。

| ブラウザ版 | Unreal では |
|---|---|
| ボックスに入ったら扉が閉まる | Box Trigger → Timeline で `Door` を回す → 効果音 |
| ちらつく・暗転・張り紙がふえる | ボックス内ライトを Timeline で点滅、張り紙（Decal または Plane）を段階ごとに表示 |
| 幽霊が近づく（5段階） | 幽霊のメッシュ（Blender／Mixamo）を各段階の位置に Set Actor Location（暗転中に動かす） |
| 電話で「0714」を押す | UMG（画面のボタン）でテンキーを作り、4けたを比べる |
| 新聞を読む | 掲示板の近くで E キー → UMG に文章を表示 |

作るときは、Claude が Blueprint の作り方を1ノードずつ説明できる（画面を見ながら一緒に進められる）。
