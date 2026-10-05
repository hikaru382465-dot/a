# 農家の家（Blender）

見本の絵（夕方のドット絵の農家）を Blender で3Dにしたもの。

- 作り方：`pip install bpy pillow numpy` のあと `python make_farmhouse.py`（`--norender` で形だけ）
- Blenderの画面で見るなら、Scripting タブでこのファイルを開いて ▶（その場合は最後の「色づけ」部分は不要）
- 出力：`assets/farmhouse.glb`（Unreal / Unity / Godot に入れられる）、`farmhouse.png`、`farmhouse_pixel.png`（ドット絵風）
- 質感は全部ノードで作った（漆喰のひび・汚れ、木目、わらの筋、石の目地と苔、土の小石、草のつぶ）。画像は不要。
- ドット絵版：480×270で描き→32色にしぼり→輪郭線→4倍に拡大（`farmhouse_pixel.png`、1倍は `farmhouse_pixel_1x.png`）。`--pixel-only` で絵だけ作り直せる。
- 細かい作り込み：軒先のわらのふさ、屋根の苔、妻壁の窓、飛び石、小石、小さな花、キノコ、麻袋、柵の頭
- まだ違うところ：見本より草・花が少ない／霧は絵の色づけでかすませているだけ
- 道具のアドバイス：今すぐ → Poly Haven の木・漆喰の質感を貼ると一気に本物っぽくなる。あとで → 草・つるは Blender の Geometry Nodes で散らすと楽。

## Poly Haven の質感を貼る
1. https://polyhaven.com/textures で好きな質感（1k〜2k, JPG）をダウンロードし、`assets/tex/` に次の名前で置く。
   `plaster_diff.jpg`（漆喰）, `wood_diff.jpg`（木）, `stone_diff.jpg`（石）, `thatch_diff.jpg`（わら）。
   それぞれ `_rough.jpg`（粗さ）と `_nor_gl.jpg`（凹凸）も置くと、もっと本物っぽくなる。
2. `python make_farmhouse.py` を実行する。ファイルがあるものだけ自動で貼られる。
- おすすめ：漆喰 `plaster_grey_04`、木 `wood_planks_dirty`、石 `rock_wall_08`、わら `thatch` 系（名前は変わることがあるので検索）
- 注意：貼った質感は絵（PNG）には出るが、`.glb` にはまだ入らない。ゲームに使うときは Blender で「ベイク」するか、エンジン側で貼る。

## Three.js で見る
- `index.html` をブラウザで開く（ダブルクリックでよい。部品はネットから読み込むので、ネットにつながっていること）
- ドラッグ：まわす／ホイール：ズーム／右ドラッグ：ずらす。ボタン：斜め上から・ドット絵風・まわす・夕方/夜
- モデルは `assets/farmhouse.glb.js`（`farmhouse.glb` を文字にしたもの）。`make_farmhouse.py` を実行すると自動で作り直される
- ノードの質感は `.glb` に入らないので、`index.html` の中で平均の色を指定している（`BASE`）

## 質感のベイク
- `python make_farmhouse.py --bake` で、ノードの模様（色と凹凸）を画像に焼いて `assets/farmhouse_baked.glb`（と `.glb.js`）を作る。2分ほど。
- 焼いた画像は .glb の中に入っている（色と凹凸、JPEG）。Unreal / Unity / Godot にそのまま入れて模様が出る。
- `index.html` と スマホ用ページは焼いた版を使う。

## 農夫のキャラクター（ドット絵）
- `python make_character.py`：32×40のドット絵の農夫を、Blenderの画像機能で描いて保存する（正面・横・うしろ × 歩き4コマ）
- 出力：`assets/character/farmer_sheet.png`（スプライトシート）、`farmer_front.png`、`farmer_walk.gif`（歩きの確認）、`farmer_preview.png`
- `make_farmhouse.py` は `farmer_front.png` があれば家の前に立たせる（ドット絵版には原寸のまま貼る）
- ゲームで使うとき：シートは1コマ 32×40。Unity / Godot / Unreal(Paper2D) の「スプライトシート」としてそのまま読める
