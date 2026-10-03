# ゲームのしくみ 実装計画（Opus 5.5 が設計 / 2026-10-04）

UE 5.8.0・Blueprint中心（C++は使わない）。ノードは「Pythonで骨組み＋貼り付け用テキスト＋手でつなぐ手順書」の3点セットで配る。

## 作るもの（/Game/KoushuDenwa/Game/）
- BP_KD_GameMode / BP_KD_Player（歩く・見回す・Eで調べる・Fで懐中電灯）
- BP_KD_Director（レベルに1個。状態管理の本体）、BP_KD_EventTrigger（再利用部品）
- BP_KD_Ghost（最初は仮の姿）、BP_KD_Newspaper / BP_KD_PhoneInteract、BPI_KD_Interact
- WBP_KD_HUD / WBP_KD_Paper / WBP_KD_Dial（テンキー）/ WBP_KD_End
- 画像：張り紙12枚＋ヒント張り紙＋新聞（PILで作る）。音：Freesound(CC0)
- 決まり：Tickを使わない。毎フレームのFind/GetAllActors禁止。参照はPythonが入れるか BeginPlay で1回だけ。

## 状態
Explore →(BoothEnter) Trapped[Idle→Flicker→Dark, Stage1〜4] →(0714) Opened →(BoothExit) Escaped
Stage5 または 70秒 → Dead → 失敗画面。番号まちがいはNG表示＋待ち時間を短縮。

## 段階
1. 歩く→ボックスに入る→ドアが閉まる→ライト点滅（setup_game.py、貼り付けテスト）
2. 張り紙・幽霊（仮）・字幕・失敗画面
3. 掲示板と新聞・ダイヤル・脱出
4. 仕上げ（幽霊をBlender/Mixamoに、音、3Dキー、調整）

## 注意
GameModeを設定しないと空飛ぶカメラになる／ボックスは Use Complex as Simple／Lumenの遅れと自動露出で暗転が弱まる／軽さ：TREE_COUNT 40、仮想メモリ32〜64GB。
