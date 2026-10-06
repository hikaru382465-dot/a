# 絵の指示文セット（ChatGPTなど画像AI用）

使い方：毎回、**①共通の指示文**を先頭に貼り、**②作りたいもの**を足す。最初の1枚（戦士：`assets/chatgpt/hero_a.png`）を、毎回「参考画像」として添付すると、絵柄がそろいやすい。1回に頼む数は、絵柄がぶれるので少なめ（1枚、多くて4枚）にする。

## ① 共通の指示文（そのまま貼る）
```
Dark fantasy pixel art game sprite, 32-bit style, limited muted color palette, 1px dark outline,
soft top-left lighting, slightly chibi proportions (big head), clean readable silhouette,
transparent background, no text, no watermark, no shadow on the ground.
Match the art style, outline thickness, and color mood of the attached reference image exactly.
```

## ② 作りたいもの（足す文）

### キャラ（横向き・右向き、全身、手足が重ならないポーズ）
- 魔法使い・連射：`A young mage in a short hooded cloak, holding a small wand, quick and agile look, accent color yellow. Side view facing right.`
- 魔法使い・範囲：`A mage in a long robe with wide sleeves, holding a large staff with a glowing orb, accent color orange. Side view facing right.`
- 魔法使い・召喚：`A mage with a book and floating small spirit lights, calm look, accent color teal. Side view facing right.`
- ペット（スライム）：`A cute round green slime pet, big eyes, small and friendly, 3 poses in one row: idle, hopping, happy. Side view.`
- ペットの進化：`The same slime, evolved: version with small horns / version with tiny wings / version with glowing eyes.`

### 召喚スキルの絵
- 幻影の狼・走り（8コマ・4×2の格子。ずれたら4コマ×2回に分け、2回目に1回目を添付）：`A ghostly wolf made of translucent blue magic energy, glowing white eyes, sleek and fast body, misty tail that fades out. A smooth running cycle of 8 frames, arranged in 2 rows of 4 frames, evenly spaced in a grid, identical size and identical wolf design in every frame, side view facing right, legs clearly separated, the last frame loops back to the first.`
- 幻影の狼・かみつき（5コマ）：`Same style and exactly the same ghost wolf as the attached image. 5 frames in one horizontal row, evenly spaced, same size: 1 crouching to jump, 2 leaping forward, 3 biting with open jaws and sharp teeth, 4 landing, 5 returning to a standing pose. Side view facing right, transparent background.`
- コマ数の目安：走り8・かみつき5。ゲーム側で、上下のゆれ・伸び縮み・残像を足して、なめらかに見せる。

### 敵（森）※ それぞれ右向き。向きを変えるときはコードで左右を反転する
- スライム、コウモリ、ゴブリンの弓兵、毒キノコ、コボルトのひろい屋（背中に袋）、ボス：スライム王（大きい、王冠）

### 宝石（小さなアイコン、8種類を1枚に並べる）
- `8 small gem icons in one row, each a different color: fire red, ice cyan, lightning yellow, blood dark red, speed green, critical white, greedy pink, charge indigo. Simple faceted shapes, 16x16 pixel look.`

### ホーム・小物（斜め45度の見下ろし、地面に置く物）
- 建物：`Isometric 45-degree view pixel art of a small [farmhouse / shop with striped awning / blacksmith with stone walls and glowing forge], dark fantasy village mood, same style as the attached reference.`
- 小物：井戸、荷車、たき火、立て札、池、ベンチ など

## ③ 絵ができたら（Claudeがやること）
1. 切り出し（背景を透明に）、大きさを統一、`assets/` に整理。
2. 左右反転、歩きは上下のゆれ＋傾きで代用（またはAIで4コマを頼む）。
3. Unity に入れる形（スプライトシート）にまとめる。

## 注意（公開の前にひかるが確認）
- 使う画像AIの規約で、商用利用してよいか。
- AppleとGoogleの、AI生成素材のルール（表示のしかた）。
- AIが作った絵は、著作権で守られにくいと言われる。まねされにくくするため、キャラの名前や設定を自分で作り込む。
