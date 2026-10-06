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

### 召喚スキルの絵（残り5体）：先に「共通部分」を貼り、魔法使いと狼の絵を添付。動き＝8コマ（4×2の格子）、攻撃＝5コマ（横1列）
- 共通部分：`Dark fantasy pixel art game sprite, 32-bit style, limited muted color palette, 1px dark outline, soft top-left lighting, clean readable silhouette, transparent background, no text, no watermark, no shadow on the ground. Match the art style, outline thickness, and color mood of the attached reference image exactly. Side view facing right. Translucent glowing magic-energy look, same as the attached ghost wolf.`
- 幻影の騎士・動き：`A ghostly knight made of translucent teal magic energy, small and slightly chibi, round helmet with glowing eyes, holding a short sword and a small shield. A smooth walking-running cycle of 8 frames, arranged in 2 rows of 4 frames, evenly spaced in a grid, identical size and design in every frame.`
- 幻影の騎士・切る：`Same knight as the attached image. 5 frames in one horizontal row, evenly spaced, same size: 1 raising the sword, 2 swinging down, 3 slash follow-through, 4 recovering, 5 back to standing.`
- 幻影の射手・動き：`A ghostly archer made of translucent teal magic energy, small and slightly chibi, hooded, holding a glowing bow. A smooth walking cycle of 8 frames, arranged in 2 rows of 4 frames, evenly spaced in a grid, identical size and design in every frame.`
- 幻影の射手・射る：`Same archer as the attached image. 5 frames in one horizontal row, same size: 1 drawing an arrow, 2 aiming, 3 releasing with a glowing arrow, 4 follow-through, 5 back to standing.`
- 火の精霊・動き：`A small fire spirit, a floating flame creature with a round glowing body, two bright eyes, and a trailing flame tail, orange and yellow glow. A floating idle cycle of 8 frames, arranged in 2 rows of 4 frames, evenly spaced in a grid, identical size in every frame.`
- 火の精霊・突進：`Same fire spirit as the attached image. 5 frames in one horizontal row, same size: 1 gathering energy and shrinking, 2 flying forward fast, 3 glowing bright white, 4 swelling just before exploding, 5 a burst of flame.`
- 氷霊の守護像・立つ（4コマ）：`A small guardian statue made of ice and stone, a short stocky knight-like figure holding a big shield, glowing pale-blue cracks, frost mist at the feet. An idle animation of 4 frames in one horizontal row, same size, subtle breathing and glowing motion.`
- 氷霊の守護像・光る（4コマ）：`Same statue as the attached image. 4 frames in one horizontal row, same size: the cracks glow brighter and a ring of frost spreads outward, then fades.`
- 雷の精霊鳥・飛ぶ：`A small thunder spirit bird, a round bird made of yellow-white lightning energy, small wings, bright eyes, crackling sparks around it. A flying cycle with flapping wings, 8 frames, arranged in 2 rows of 4 frames, evenly spaced in a grid, identical size in every frame.`
- 雷の精霊鳥・雷を放つ：`Same thunder bird as the attached image. 5 frames in one horizontal row, same size: 1 gathering sparks, 2 body glowing white, 3 releasing a bolt of lightning downward, 4 sparks scatter, 5 back to flying pose.`
- スライム分身は、ペットのスライムの絵を使う（新しい絵は不要）。
- 頼む順番のおすすめ：騎士 → 火の精霊 → 射手 → 精霊鳥 → 守護像（生成の制限があるため）。

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
