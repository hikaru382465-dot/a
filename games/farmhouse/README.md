# 農家の家（Blender）

見本の絵（夕方のドット絵の農家）を Blender で3Dにしたもの。

- 作り方：`pip install bpy pillow numpy` のあと `python make_farmhouse.py`（`--norender` で形だけ）
- Blenderの画面で見るなら、Scripting タブでこのファイルを開いて ▶（その場合は最後の「色づけ」部分は不要）
- 出力：`assets/farmhouse.glb`（Unreal / Unity / Godot に入れられる）、`farmhouse.png`、`farmhouse_pixel.png`（ドット絵風）
- まだ違うところ：見本より窓・草が少ない／霧は未設定（つるは壁にはわせ済み）
- 道具のアドバイス：今すぐ → Poly Haven の木・漆喰の質感を貼ると一気に本物っぽくなる。あとで → 草・つるは Blender の Geometry Nodes で散らすと楽。
