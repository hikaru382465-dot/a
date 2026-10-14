# ドット絵スクリプト早見表（別のセッション・別のリポジトリへ持っていくとき）

最小セット（これだけコピーすれば動く）：
- `palette.json`, `pxl.py`（パレット読み込みと文字グリッド→絵）
- 作るものに近い `gen_*.py` 1本（例：キャラなら `gen_blonde_chibi.py`、音符なら `gen_notes.py`、水しぶきなら `gen_splash.py`）
- 実行：`python gen_xxx.py`（Python 3 + numpy + Pillow）。出力先は `../assets/...`（なければ自動で作る）

別リポジトリに持っていく場合は、このフォルダの `pixel/` と `.claude/skills/pixel-art/` をそのままコピーする。
同じリポジトリの新しいセッションは、スキル `pixel-art` が自動で見つかるので何もしなくてよい。
