# 農家の家（Blender）

見本の絵（夕方のドット絵の農家）を Blender で3Dにしたもの。

- 作り方：`pip install bpy pillow numpy` のあと `python make_farmhouse.py`（`--norender` で形だけ）
- Blenderの画面で見るなら、Scripting タブでこのファイルを開いて ▶（その場合は最後の「色づけ」部分は不要）
- 出力：`assets/farmhouse.glb`（Unreal / Unity / Godot に入れられる）、`farmhouse.png`、`farmhouse_pixel.png`（ドット絵風）
- まだ違うところ：見本より窓・草が少ない／霧は未設定（つるは壁にはわせ済み）
- 道具のアドバイス：今すぐ → Poly Haven の木・漆喰の質感を貼ると一気に本物っぽくなる。あとで → 草・つるは Blender の Geometry Nodes で散らすと楽。

## Poly Haven の質感を貼る
1. https://polyhaven.com/textures で好きな質感（1k〜2k, JPG）をダウンロードし、`assets/tex/` に次の名前で置く。
   `plaster_diff.jpg`（漆喰）, `wood_diff.jpg`（木）, `stone_diff.jpg`（石）, `thatch_diff.jpg`（わら）。
   それぞれ `_rough.jpg`（粗さ）と `_nor_gl.jpg`（凹凸）も置くと、もっと本物っぽくなる。
2. `python make_farmhouse.py` を実行する。ファイルがあるものだけ自動で貼られる。
- おすすめ：漆喰 `plaster_grey_04`、木 `wood_planks_dirty`、石 `rock_wall_08`、わら `thatch` 系（名前は変わることがあるので検索）
- 注意：貼った質感は絵（PNG）には出るが、`.glb` にはまだ入らない。ゲームに使うときは Blender で「ベイク」するか、エンジン側で貼る。
