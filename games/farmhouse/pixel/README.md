# ドット絵キャンバス（Claude用）

文字のマス目でドット絵を描いて、絵にして、拡大して見直すための道具。

- `palette.json`：色の系統（A〜Z・a〜z）×明るさ0〜7。コードは2文字（例 `D3`）。暗い側は青むらさき、明るい側は黄色へずれる
- `pxl.py`：`python pxl.py sprites/barrel.pxl` → 原寸の絵と、目盛りつき拡大の絵（`_zoom.png`）。点検（使った色の数、ぽつんと1ドット）も出す
- 書き方は `pxl.py` の先頭に書いてある（@mirror=左右折り返し、@sidelight=左明るく右暗く、@outline sel=となりの色で輪郭）
- 描き方：絵を書く → 拡大を見る → マスの文字だけ直す、をくり返す

## 農夫の歩き（v2）
- `python gen_walk.py`：正面と横向き（右向き）の歩き4コマずつを `sprites/farmer_*_walk0〜3.pxl` に作り、絵にしてまとめる
- 出力（`assets/character/`）：`farmer_sheet_v2.png`（2行×4列、1コマ32×41）、`farmer_walk_v2.gif`（横向き）、`farmer_preview_v2.png`（拡大）
- 左向きは、横向きを左右反転して使う。うしろ向きはまだ

## 家を「ドット絵として」描く（iso.py）
- `python iso.py` → `../assets/farmhouse_iso.png`（480×270）と `farmhouse_iso_x4.png`
- 3Dを縮めるのではなく、2:1の斜め上の視点で、面ごとに1ドットずつ模様（パレットのコード）を決めて塗る。色は `palette.json` だけ（農夫と同じ）
- 屋根のわらの段とギザギザ、しっくいの汚れ、石の目地、木目、窓のあかり、影、足もとの暗がりは `iso.py` の「テクスチャ」の関数で決まる
- 物の置き場所は `build()` と `props()`。数字を変えれば動く
