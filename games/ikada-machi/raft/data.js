// イカダ暮らし：表（数字はここだけ。あとで Godot の Resource / Dictionary にそのまま移せる）
window.RAFT = { parts: {}, order: ['camera', 'water', 'light', 'floor', 'objects', 'buddy', 'drift', 'boat', 'sound', 'hud'] };
window.RAFT.data = {
  DAY_SEC: 720,                       // 1日の長さ（秒）＝12分。URLの最後に ?fast で10倍
  MAX_SIZE: 8,                        // イカダの最大（8×8マス）
  NEEDS: { hunger: 0.25, thirst: 0.33, low: 30 },   // 1秒に減る量、相棒が自分で食べ始める値
  // lv：この網のレベル以上で取れる。w：流れてくる重み。food/drink：食べる・飲むで戻る量。place：置ける物
  ITEMS: {
    wood:    { name: '木くず',   lv: 1, w: 6, tip: '作る材料' },
    fish:    { name: '小魚',     lv: 1, w: 0, food: 8, tip: '生のまま食べると少ししか戻らない。焚き火で焼こう' },
    seed:    { name: 'おたのしみ種袋', lv: 2, w: 0.15, tip: '畑にまく。何が育つかは、お楽しみ（12種類のどれか）' },
    veg:     { name: '野菜',     lv: 0, w: 0, food: 8, drink: 3, tip: '畑でとれた。そのままだと少し。料理すると、もっと戻る' },
    dried:   { name: '干物',     lv: 0, w: 0, food: 30, tip: '干し魚だなで作る。食べると、おなかが戻る' },
    yakiyasai: { name: '焼き野菜', lv: 0, w: 0, food: 35, tip: 'かまどで作る。おなかがしっかり戻る' },
    soup:    { name: '野菜スープ', lv: 0, w: 0, food: 50, mood: 5, tip: 'かまどで作る。おなかが戻って、ほっとする' },
    tsukeni: { name: '魚の煮つけ', lv: 0, w: 0, food: 65, mood: 10, tip: 'かまどで作る。ごちそう。機嫌もよくなる' },
    nabe:    { name: '海鮮鍋',   lv: 0, w: 0, food: 90, mood: 20, tip: 'かまどで作る。いちばんのごちそう' },
    grilled: { name: '焼き魚',   lv: 0, w: 0, food: 40, tip: '食べると、おなかがしっかり戻る' },
    coconut: { name: 'ヤシの実', lv: 1, w: 2, food: 8, drink: 28, tip: '飲むとのどが戻る（おなかも少し）' },
    rope:    { name: '縄',       lv: 2, w: 3, tip: '作る材料' },
    cloth:   { name: '布',       lv: 2, w: 2, tip: '作る材料' },
    clay:    { name: '粘土',     lv: 3, w: 2, tip: '作る材料' },
    stone:   { name: '石',       lv: 3, w: 2, tip: '作る材料' },
    iron:    { name: '鉄くず',   lv: 4, w: 1, tip: '作る材料' },
    glass:   { name: 'ガラス',   lv: 4, w: 1, tip: '作る材料' },
    floor:   { name: '床板',     lv: 0, w: 0, place: true, tip: '海に面したところに置くと、イカダが広がる' },
    bench:   { name: '作業台',   lv: 0, w: 0, place: true, tip: '置くと、いろいろ作れる（イカダに1つ）' },
    tank:    { name: '貯水槽',   lv: 0, w: 0, place: true, cap: 8, tip: '雨の水をためる。タップで飲む' },
    campfire: { name: '焚き火',  lv: 0, w: 0, place: true, tip: '置いて、タップ。魚と木くずを入れると焼ける' },
    seat:    { name: '見晴らしいす', lv: 0, w: 0, place: true, tip: '置いて、タップで座る。景色を眺めて、ほっとする' },
    rack:    { name: '干し魚だな', lv: 0, w: 0, place: true, tip: '飾り。イカダが漁師の家らしくなる' },
    oven:    { name: 'かまど',   lv: 0, w: 0, place: true, tip: '置いて、タップ。野菜や魚で料理ができる（焼き魚は焚き火で）' },
    crate:   { name: '木箱',     lv: 0, w: 0, place: true, tip: '飾り。荷物を置いた感じになる' },
    chest:   { name: '宝箱',     lv: 0, w: 0, place: true, tip: '飾り。かっこいい箱' },
    plot:    { name: '畑', lv: 0, w: 0, place: true, tip: '置いて、タップ。種袋をまくと、野菜が育つ' },
    barrel:  { name: '樽',       lv: 0, w: 0, place: true, tip: '飾り。水の樽（のちに、水をためられるようにしたい）' },
    bed:     { name: 'ベッド',   lv: 0, w: 0, place: true, tip: '飾り。ふかふかのベッド（のちに、ねて回復できるようにしたい）' },
    shelf:   { name: '本棚',     lv: 0, w: 0, place: true, tip: '飾り。本や瓶をならべた棚' },
    windmill:{ name: '風車',     lv: 0, w: 0, place: true, tip: '飾り。小さな風車' },
    hutw:    { name: '木の板の小屋', lv: 0, w: 0, place: true, size: [2, 3], as: 'hut', hv: 1, tip: '木の板の屋根と、白い壁の小屋。広さも、住める人数も、わらの小屋と同じ（2×3マス）' },
    huts:    { name: '石の小屋', lv: 0, w: 0, place: true, size: [2, 3], as: 'hut', hv: 2, tip: '灰色の石の屋根と、石の壁の小屋。広さも、住める人数も、わらの小屋と同じ（2×3マス）' },
    hut:     { name: '小屋',     lv: 0, w: 0, place: true, size: [2, 3], rnd: true, tip: '自分と相棒の家。タップで中に入って、休める（2×3マス）。見た目は、置くとき、ランダムに決まる' },
    filter:  { name: 'ろ過器',   lv: 0, w: 0, place: true, sec: 40, tip: '海水をろ過して、貯水槽に水を入れる' }
  },
  // 作る：need が 'bench' のものは、イカダに作業台が置かれているときだけ作れる。special:'net' は網の強化（材料は NET_LV の cost）
  RECIPES: [
    { id: 'bench',  out: 'bench',  cost: { wood: 6 },                   need: null,    tip: '最初に作る。これがあれば、ほかの物が作れる' },
    { id: 'floor',  out: 'floor',  cost: { wood: 4 },                   need: null,    tip: 'イカダを広げる' },
    { id: 'tank',   out: 'tank',   cost: { wood: 6 },                   need: 'bench', tip: '雨の水がたまる' },
    { id: 'net',    special: 'net',                                     need: 'bench', tip: '網のレベルを上げる（遠くへ飛ぶ・取れる物が増える）' },
    { id: 'rod',    special: 'rod', cost: { wood: 4, rope: 2 },    need: 'bench', tip: '魚を1匹ずつ釣れる。縄は網でとる' },
    { id: 'fixnet', special: 'fix', tool: 'net', cost: { wood: 2 }, need: 'bench', tip: '網のいたみを直す' },
    { id: 'fixrod', special: 'fix', tool: 'rod', cost: { wood: 2 }, need: 'bench', tip: '釣りざおのいたみを直す' },
    { id: 'campfire', out: 'campfire', cost: { wood: 8 }, need: 'bench', tip: '魚を焼ける' },
    { id: 'seat', out: 'seat', cost: { wood: 8, rope: 2, cloth: 1 }, need: 'bench', tip: '座って景色を眺める。ほっとして、贈り物が見つかることも' },
    { id: 'rack', out: 'rack', cost: { wood: 6, rope: 3 }, need: 'bench', tip: '魚をつるして飾る' },
    { id: 'crate', out: 'crate', cost: { wood: 5 }, need: 'bench', tip: '木の箱を飾る' },
    { id: 'chest', out: 'chest', cost: { wood: 6, iron: 2 }, need: 'bench', tip: '鉄で補強した宝箱' },
    { id: 'plot', out: 'plot', cost: { wood: 5, cloth: 1 }, need: 'bench', tip: '畑を置く。種袋をまくと野菜が育つ' },
    { id: 'oven', out: 'oven', cost: { wood: 2, clay: 6, iron: 1 }, need: 'bench', tip: '粘土で作る石のかまど。料理ができる' },
    { id: 'barrel', out: 'barrel', cost: { wood: 6, iron: 1 }, need: 'bench', tip: '木の樽を作る' },
    { id: 'bed', out: 'bed', cost: { wood: 8, cloth: 3, rope: 2 }, need: 'bench', tip: '布でふかふかのベッド' },
    { id: 'shelf', out: 'shelf', cost: { wood: 10, rope: 2 }, need: 'bench', tip: '本棚を作る' },
    { id: 'windmill', out: 'windmill', cost: { wood: 8, rope: 3, cloth: 2, iron: 1 }, need: 'bench', tip: '風で回る飾りの風車' },
    { id: 'hut', out: 'hut', special: 'hut', cost: { wood: 24, rope: 8, cloth: 6 }, need: 'bench', tip: '家を作る。見た目を54種類から選べる。大きな建物なので、材料は多め。見た目の系統で、材料がちがう（木・石・レンガ・海・緑・雪）' },
    { id: 'filter', out: 'filter', cost: { wood: 6, rope: 2, cloth: 2 }, need: 'bench', tip: '海水から、貯水槽へ水を作る' }
  ],
  // 相棒（女の子）にまかせる仕事。mood＝機嫌（働くと減り、休むと増える。低いほど仕事がおそい）
  BUDDY: {
    JOBS: {
      fish:  { name: '釣り番',     tip: '相棒がざおで魚を釣る（リズムなしなので、ゆっくり）' },
      net:   { name: '網番',       tip: '相棒が網を投げて、引き上げる（網のレベルしだい）' },
      water: { name: '水くみ番',   tip: 'ろ過器・貯水槽のそばで手伝う（ろ過と雨水ためが速くなる）' },
      rest:  { name: 'くつろぐ',   tip: '景色を眺めて、機嫌をもどす' },
      sit:   { name: '座る',       tip: '座って休む（ふつうに機嫌がもどる）' },
      sleep: { name: '寝る',       tip: '眠って休む（いちばん早く機嫌がもどる）' }
    },
    ROD_COST: { wood: 4, rope: 2 },
    MOOD0: 80, DRAIN: 0.12, REST: 0.9, REST_RATE: { rest: 0.9, sit: 0.7, sleep: 1.6 }, IDLE: 0.15, TIRED: 12,
    FISH_WAIT: [5, 12], FISH_REST: [2, 5], NET_REST: 6, NET_POWER: 0.6, VIEW_SEC: 25
  },
  // 道具のいたみ：使うたびに減る。0になると「ぼろぼろ」（使えるが、遠くへ飛ばない・1個しか入らない・ウキの時間が短い）。「作る」で直す（作業台がいる）
  DUR: { net: { use: 3 }, rod: { use: 5 }, fixCost: { wood: 2 }, worn: { range: 0.5, cap: 1, bite: 0.6 }, low: 25 },
  // 日がたつと、きびしくなる：嵐が増える・おなかとのどが速く減る・嵐で網が破れる
  DIFF: { stormBase: 2.5, stormPerDay: 0.8, stormMax: 9, sunnyBase: 5, sunnyMin: 1.5, needPerDay: 0.06, needMax: 0.6, tearBase: 0.08, tearPerDay: 0.015, tearMax: 0.2, tearDmg: 25, weak: 0.6 },
  RACK: { sec: 45, max: 3 },     // 干し魚だな：1匹が干物になる秒数・かけられる数
  DISHES: [      // かまどの料理。need＝材料（木くずは燃料）／sec＝できるまでの秒数
    { id: 'yakiyasai', need: { veg: 1, wood: 1 }, sec: 8 },
    { id: 'soup', need: { veg: 2, wood: 1 }, sec: 10 },
    { id: 'tsukeni', need: { fish: 1, veg: 1, wood: 1 }, sec: 12 },
    { id: 'nabe', need: { fish: 2, veg: 2, wood: 2 }, sec: 16 }
  ],
  OVEN: { maxIn: 8, maxOut: 16 },
  COOK: { sec: 12, perWood: 3, maxFish: 8, maxWood: 8, maxOut: 16 },   // 1匹12秒・木くず1個で3匹ぶん・各枠の上限
  // 船の住人との交渉：夕方に、嵐でなければ、1日に1回まで船が来る。1つの船に2つの取引。1つずつ、1回だけ
  BOAT: {
    FROM: 0.55, TO: 0.85, SPEED: 0.9, STAY: 110, OFFSET: 3.2,
    RES: {
      toto: { ask: 3, base: 'boy', tint: '#e6dcc0', name: 'トトじいさん', hello: 'やあ、海の上でも商売さ。魚と交換しないかい？', thanks: 'まいど！ また来るよ。',
              deals: [{ want: { fish: 4 }, give: { cloth: 2 } }, { want: { grilled: 2 }, give: { rope: 2 } }] },
      mina: { ask: 3, base: 'girl', tint: '#ffa98c', name: 'ミナ（かじ屋の子）', hello: '鉄は重いんだ。ただじゃ渡せないよ。', thanks: 'いい物をありがとう。大切に使うね。',
              deals: [{ want: { grilled: 3 }, give: { iron: 2 } }, { want: { wood: 10 }, give: { iron: 1, stone: 1 } }] },
      kuro: { ask: 3, base: 'girl', tint: '#9fc2ff', name: 'クロさん（焼き物の人）', hello: '雨の日は、土がこねやすいのよ。', thanks: 'また、いい土を持ってくるわ。',
              deals: [{ want: { wood: 8 }, give: { clay: 3 } }, { want: { coconut: 3 }, give: { glass: 2 } }] },
      pipi: { ask: 3, base: 'boy', tint: '#8fd4ff', name: 'ピピ（見習い船乗り）', hello: 'ヤシの実、ちょうだい！ 石ならあるよ！', thanks: 'やったあ！ ありがとう！',
              deals: [{ want: { coconut: 2 }, give: { stone: 2 } }, { want: { fish: 3 }, give: { rope: 1, cloth: 1 } }] }
    }
  },
  // 住人：仲間になって、小屋1つにつき1人、イカダに住む。perk＝住んでいるあいだの能力（stage1 は kuro と pipi）
  HUT_N: 54,      // 小屋の見た目の数（objs_art.js の hut の配列＝昼夜2枚ずつ。make_objs.py が数を確かめる）
  RESIDENT: {
    ask: { toto: 'ここの暮らしは、おもしろそうじゃ。わしも住んでいいかね？', mina: 'ここなら、いい鉄打ちができそう。住んでもいい？', kuro: 'この筏、土がこねやすそうね。しばらく住んでいい？', pipi: 'ねえねえ、ぼくもここに住みたい！ いいでしょ？' },
    join: { toto: 'ほっほ、よろしくの。', mina: 'よろしく！ 腕によりをかけるよ。', kuro: 'ありがとう。いいお茶、いれるわね。', pipi: 'やったー！ よろしくお願いしまーす！' },
    perk: { kuro: { cookMul: 1.25, gift: ['clay', 'glass'] }, pipi: { warn: 20 }, toto: { deals: [{ want: { fish: 2 }, give: { cloth: 1 } }, { want: { grilled: 1 }, give: { rope: 1 } }] }, mina: { off: ['iron', 'stone'] } },
    talk: {
      toto: { cooked: ['いい匂いじゃ。わしにも一口くれんかのう。'], fish: ['今日は、よう釣れたのう。'], farm: ['畑も、ええ具合じゃのう。'], after: ['昨日の嵐は、すごかったのう。'], day: ['今日も、いい風じゃのう。', '魚は焼くより、干すのが好きでな。', '海は広い。急がんでええよ。'], storm: ['こりゃ荒れるのう。小屋に入っておるといい。'], night: ['夜の海は、星が近いのう。', 'もう寝る時間じゃ。'] },
      mina: { cooked: ['いい匂い！ おなかすいてきた。'], fish: ['たくさん釣れたね。針、研いでおこうか？'], farm: ['畑の道具も、直せるよ。'], after: ['昨日の嵐、ひどかったね。道具は無事？'], day: ['金づち、まだ持ってる？ 手入れしとこうか。', '鉄はね、焦っちゃだめなんだ。', 'この筏、木の香りがいいね。'], storm: ['嵐の音って、鉄を打つ音に似てるよね。'], night: ['夜は、火の色がきれいだね。', 'そろそろ休もうか。'] },
      kuro: { cooked: ['あら、いい料理。かまどが喜んでるわ。'], fish: ['お魚、たくさん。つぼに入れておく？'], farm: ['野菜、いい色ね。スープにしましょ。'], after: ['昨日は荒れたわね。土がしっとりしてるわ。'], day: ['土のにおいがする、いい日ね。', 'かまど、いい形ね。何か焼こうかしら。', 'お茶が入ったわ。ひと息つきましょ。'], storm: ['雨の日は、土がしっとりするの。悪くないわ。'], night: ['夜のかまどは、あったかいわね。', '星が、つぼの中にも映ってるわ。'] },
      pipi: { cooked: ['わあ、おいしそう！ ぼくも食べたい！'], fish: ['すごーい、大漁だ！'], farm: ['野菜が育ってる！ すごいや！'], after: ['昨日の嵐、こわかったけど、かっこよかった！'], day: ['今日の海、波が高いかも！', '見張りは、まかせてよ！', '船乗りになるのが夢なんだ！'], storm: ['わあ、大荒れだ！ でも、ちょっとワクワクする！', '嵐が来るよ！ 気をつけて！'], night: ['夜の見張りは、ぼくの番だね。', '星が、いっぱい！'] }
    }
  },
  // 景色を眺める：座っている間、「ほっとした」がふえる。相棒の機嫌ももどる。ときどき贈り物
  LOOK: { gain: 3, decay: 0.08, giftSec: 45, buddyBonus: 0.8, gifts: ['coconut', 'cloth', 'rope', 'glass', 'wood'] },
  TANK_SIP: 30,      // 貯水槽から1回飲んで戻るのどのかわき
  RAIN_SEC: 4,       // 嵐のとき、貯水槽に水が1たまる間隔（秒）
  // 道具（持ち物の先頭に並ぶ。選ぶと手に持つ）
  TOOLS: { net: { name: '網', tip: '海を押し続けて、離すと投げる' }, rod: { name: '釣りざお', tip: '海をタップして、糸をたらす。ウキがしずんだら、輪がちぢんで重なる時にタップ' } },
  // 釣り：range＝糸が届くマス、wait＝魚が来るまでの秒（最小〜最大）、bite＝ウキがしずんでいる秒（この間にタップ）
  ROD: { range: 4.5, min: 1.5, wait: [3, 8], bite: 1.7, fishP: 0.8, great: [0.55, 0.2] },   // great＝タイミングぴったり（しずんでからの割合の前後で2匹）
  // 網（投げる）：range＝ゲージ満タンで飛ぶ距離（マス）、r＝網がとる広さ（半径・マス）、cap＝1回で入る数
  NET_LV: [
    { lv: 1, range: 4,   r: 0.9, cap: 3 },
    { lv: 2, range: 5.5, r: 1.0, cap: 4, cost: { wood: 8 } },
    { lv: 3, range: 7,   r: 1.1, cap: 5, cost: { wood: 12, rope: 4, cloth: 3 } },
    { lv: 4, range: 9,   r: 1.3, cap: 6, cost: { wood: 16, clay: 5, stone: 5 } }
  ],
  NET_MIN: 1.5,      // ゲージが0でも、これだけは飛ぶ
  NET_REST: 4.5,     // 水の上でとっている時間（秒）
  NET_DRAG: 5,       // 網を引きずる速さ（マス/秒）。引き上げの絵（haul）は、いまは使っていない
  NET_HAUL: 0.6,
  NET_FLY: 0.55,     // 飛んでいる時間（秒）
  // speed：流れの速さ（マス/秒）、rate：物の出る多さ、thirst：のどのかわく速さの倍率、w：次に選ばれやすさ
  // 魚の図鑑：lv＝網のレベルがこれ以上で出る／star＝めずらしさ（3は、とれたら魚が3匹）／w＝出やすさ／time＝多い時間（dawn・day・dusk・night）／wx＝多い天気／by＝rod（釣りざおだけ）・net（網だけ）・省略で両方／great＝釣りざおの「ぴったり」のときだけ
  // 畑：畑に種袋をまくと、くじで作物が決まる。水（貯水槽から）があるあいだだけ育つ。嵐の雨は、全部のプランターに水を入れる
  HUT: { needMul: 0.6, calm: 2 },      // 小屋の中：おなか・のどの減りが0.6倍／「ほっとした」が1秒に2ふえる
  PLOT: { water: 240, sunDry: 1.4, calmGrow: 1.5, seedBack: 0.5 },      // water＝水がもつ秒数／sunDry＝晴れの日の乾きの速さ／calmGrow＝凪の日の育ち／seedBack＝収穫で種が戻る確率
  CROPS: {
    tomato: { name: 'トマト',     sec: 360, star: 1, w: 5, tip: '赤くてつやつや。おなかにもいい' },
    carrot: { name: 'ニンジン',   sec: 420, star: 1, w: 5, tip: '土の中でのびる。ぽりぽりおいしい' },
    potato: { name: 'ジャガイモ', sec: 480, star: 1, w: 5, tip: 'ほくほくのいも。焼くとおいしそう' },
    corn:   { name: 'トウモロコシ', sec: 600, star: 2, w: 3, tip: '背が高くなる。きいろい実が自慢' },
    berry:  { name: 'イチゴ',     sec: 600, star: 2, w: 3, tip: 'あまい赤い実。おやつにぴったり' },
    melon:  { name: 'スイカ',     sec: 720, star: 3, w: 1.5, tip: '大きな丸い実。育つのに時間がかかる' },
    eggplant:  { name: 'ナス',       sec: 480, star: 1, w: 4, tip: 'つやつやの紫の実。焼くとおいしい' },
    cabbage:   { name: 'キャベツ',   sec: 540, star: 1, w: 4, tip: 'まるくて、葉っぱがぎっしり' },
    pepper:    { name: 'ピーマン',   sec: 540, star: 1, w: 4, tip: '緑と赤の実がなる。ちょっとにがい' },
    pumpkin:   { name: 'カボチャ',   sec: 780, star: 2, w: 2.5, tip: '大きなオレンジ色の実。スープにぴったり' },
    grape:     { name: 'ブドウ',     sec: 840, star: 3, w: 1.2, tip: 'むらさきのふさ。あまくて、めずらしい' },
    pineapple: { name: 'パイナップル', sec: 900, star: 3, w: 1.0, tip: '南の島の果物。育つのに、とても時間がかかる' }
  },
  FISH: {
    iwashi: { name: 'イワシ',   lv: 1, star: 1, w: 10, tip: '群れでいる小さな魚。どこにでもいる' },
    aji:    { name: 'アジ',     lv: 1, star: 1, w: 8,  tip: '素早い。焼くとおいしい' },
    saba:   { name: 'サバ',     lv: 1, star: 1, w: 7,  tip: '背中のもようがきれい' },
    tai:    { name: 'タイ',     lv: 2, star: 2, w: 4,  wx: 'calm', tip: '赤いお魚。凪の日に見つかりやすい' },
    masu:   { name: 'マス',     lv: 2, star: 1, w: 5,  time: 'dawn', tip: '朝のつめたい水が好き' },
    ika:    { name: 'イカ',     lv: 2, star: 2, w: 4,  time: 'night', tip: '夜になると、あかりに寄ってくる' },
    ebi:    { name: 'エビ',     lv: 2, star: 1, w: 5,  by: 'net', tip: '網にからまって取れる' },
    fugu:   { name: 'フグ',     lv: 2, star: 2, w: 3,  tip: 'ふくらむ。かわいいけど、あぶない' },
    kasago: { name: 'カサゴ',   lv: 2, star: 2, w: 3,  tip: 'とげとげの、岩かげの魚' },
    kani:   { name: 'カニ',     lv: 3, star: 1, w: 5,  by: 'net', tip: '網の底でごそごそしている' },
    tako:   { name: 'タコ',     lv: 3, star: 2, w: 3,  time: 'night', by: 'net', tip: '8本の足。夜に出てくる' },
    hirame: { name: 'ヒラメ',   lv: 3, star: 2, w: 3,  wx: 'calm', tip: '海の底にぺたり。凪の日に会える' },
    unagi:  { name: 'ウナギ',   lv: 3, star: 2, w: 3,  time: 'night', tip: 'にょろにょろ。夜に多い' },
    hamachi:{ name: 'ハマチ',   lv: 3, star: 2, w: 3,  time: 'day', tip: '昼のあかるい海で、よく泳ぐ' },
    ei:     { name: 'エイ',     lv: 3, star: 3, w: 1.5, tip: 'ひらひら泳ぐ、めずらしい魚' },
    iseebi: { name: 'イセエビ', lv: 3, star: 3, w: 1.5, by: 'net', tip: '長いひげ。ごちそうの王様' },
    maguro: { name: 'マグロ',   lv: 4, star: 3, w: 2,  by: 'rod', tip: '大きな魚。釣りざおが重い！' },
    kajiki: { name: 'カジキ',   lv: 4, star: 3, w: 1.5, by: 'rod', great: true, wx: 'storm', tip: '角のある魚。嵐のあとに会えることも' },
    katsuo: { name: 'カツオ',   lv: 2, star: 1, w: 5,  time: 'day', tip: 'すばしこい群れの魚。昼のあかるい海が好き' },
    sake:   { name: 'サーモン', lv: 2, star: 1, w: 4,  time: 'dusk', tip: '夕方、まっすぐ泳いでくる魚' },
    karei:  { name: 'カレイ',   lv: 2, star: 1, w: 3,  wx: 'calm', tip: '海の底にぺたり。ヒラメとは目の向きがちがう' },
    tachiuo:{ name: 'タチウオ', lv: 3, star: 2, w: 3,  time: 'night', tip: '銀色の細長い魚。夜の海でキラリと光る' },
    anago:  { name: 'アナゴ',   lv: 3, star: 2, w: 3,  time: 'night', tip: '岩のあなにひそむ、細長い魚' },
    utsubo: { name: 'ウツボ',   lv: 3, star: 2, w: 2,  time: 'night', tip: '岩かげから、がぶり！ こわい顔だけど、はずかしがり' },
    manbo:  { name: 'マンボウ', lv: 4, star: 3, w: 1.5, wx: 'calm', tip: 'ぷかぷか浮かぶ、まるい魚。凪の日にのんびり' },
    iruka:  { name: 'イルカ',   lv: 4, star: 3, w: 1,  time: 'day', by: 'rod', tip: '人なつこい海の友だち。晴れた昼に会えることも' },
    shirakansu: { name: 'シーラカンス', lv: 4, star: 3, w: 0.7, by: 'rod', great: true, tip: '大昔から生きている、まぼろしの魚' },
    kurage: { name: 'クラゲ',   lv: 4, star: 2, w: 3,  wx: 'calm', by: 'net', tip: 'ふわふわ浮かぶ。凪の日に多い' }
  },
  SCENES: {
    dawn_sunny: ['朝やけの海', '空がうすいオレンジ。水平線がきらきらしている。', '#f2b27a,#5a7fa8'], dawn_calm: ['朝もやの海', '風がない。海がしずかに息をしている。', '#d9c3b0,#7c9aa8'], dawn_storm: ['嵐の朝', '雲が低い。波の音が大きい。', '#6d7080,#2f3a4d'],
    day_sunny: ['青い昼の海', '空が高い。水平線がずっと先まで見える。', '#8fd0f0,#2f78b0'], day_calm: ['鏡のような海', '空がそのまま海にうつっている。', '#bfe6f2,#5aa0c0'], day_storm: ['荒れた昼の海', '白い波がたつ。雨が横からふく。', '#59657a,#27384f'],
    dusk_sunny: ['夕やけの海', '空がだいだい色にそまっていく。', '#f08a5a,#5b3b6e'], dusk_calm: ['ゆうなぎ', '海も空も、ピンク色。', '#f0b8a0,#7a5a8a'], dusk_storm: ['夕方の嵐', '赤黒い雲のすきまから光がもれる。', '#7a4a4a,#2a2038'],
    night_sunny: ['星の海', '星がきれい。波の音だけがする。', '#1a2a5a,#0a1230'], night_calm: ['しずかな夜', '星が海にうつって、二つの空みたい。', '#22336a,#0c1838'], night_storm: ['嵐の夜', '真っ暗。雷のひかりだけが海をてらす。', '#12141f,#05060c']
  },
  WEATHER: {
    sunny: { name: '晴れ', speed: 0.6, rate: 1.0, thirst: 1.4, w: 5 },
    calm:  { name: '凪',   speed: 0.25, rate: 0.5, thirst: 0.9, w: 2.5 },
    storm: { name: '嵐',   speed: 1.2, rate: 1.8, thirst: 0.6, w: 2.5 }
  }
};
// 小屋の見た目20種類（objs_art.js の hut の配列の順）。n＝名前、c＝材料（大きな建物なので多め。系統ごとに材料がちがう）
// 木・わら系＝木と縄と布／石・レンガ系＝石・粘土・（鉄）／海系＝ガラスと縄／緑系＝種・ヤシ／雪＝布と石
window.RAFT.data.HUT_LOOKS = [
  { n: 'わらぶきの小屋', c: { wood: 24, rope: 8, cloth: 6 } }, { n: '木の板の小屋', c: { wood: 28, rope: 8, cloth: 6 } }, { n: '石の小屋', c: { wood: 14, stone: 24, rope: 6, cloth: 4 } },
  { n: '貝がらの屋根の家', c: { wood: 22, glass: 4, rope: 10, cloth: 6 } }, { n: '苔の屋根の家', c: { wood: 22, rope: 8, seed: 4, cloth: 4 } }, { n: '赤い瓦の家', c: { wood: 14, clay: 24, rope: 6, cloth: 4 } },
  { n: '青い板の家', c: { wood: 26, rope: 12, glass: 2, cloth: 6 } }, { n: '竹の家', c: { wood: 26, rope: 12, cloth: 4 } }, { n: 'ヤシの葉の家', c: { wood: 20, coconut: 6, rope: 8, cloth: 4 } },
  { n: '雪の屋根の家', c: { wood: 24, cloth: 12, stone: 10, rope: 8 } }, { n: 'レンガの家（黒い屋根）', c: { wood: 14, clay: 20, stone: 10, rope: 6 } }, { n: '土壁の家', c: { wood: 16, clay: 16, rope: 6 } },
  { n: '紫の屋根の石の家', c: { wood: 16, stone: 26, glass: 4, iron: 2, rope: 6 } }, { n: 'きのこの家', c: { wood: 18, clay: 12, seed: 6, cloth: 8, coconut: 4 } }, { n: 'トタン屋根の家', c: { wood: 24, iron: 6, rope: 6 } },
  { n: '青い屋根のレンガの家', c: { wood: 14, clay: 22, stone: 10, rope: 6 } }, { n: '赤い屋根の商店風の家', c: { wood: 20, clay: 24, rope: 8, cloth: 8 } }, { n: '2階建ての家', c: { wood: 30, clay: 30, stone: 12, rope: 10, cloth: 8, iron: 2 } },
  { n: '屋上カフェの家', c: { wood: 26, clay: 28, stone: 14, rope: 8, cloth: 10 } }, { n: '丸い塔の家', c: { wood: 16, stone: 30, clay: 16, rope: 8 } },
  { n: '丸窓の木の家', c: { wood: 26, rope: 8, cloth: 4 } }, { n: 'とんがり屋根の木の家', c: { wood: 28, rope: 8, cloth: 4 } }, { n: 'ひさしの長い木の家', c: { wood: 34, rope: 10, cloth: 8 } },
  { n: '高床の木の家', c: { wood: 32, rope: 14, cloth: 4 } }, { n: 'かまぼこ屋根の木の家', c: { wood: 28, rope: 8, cloth: 6 } }, { n: 'ログハウス', c: { wood: 36, rope: 8, cloth: 4 } },
  { n: '花壇つきの木の家', c: { wood: 26, rope: 6, cloth: 6 } }, { n: '葉っぱ屋根の木の家', c: { wood: 22, seed: 4, rope: 8, cloth: 4 } }, { n: '浮き輪の木の家', c: { wood: 28, rope: 12 } },
  { n: 'ヒトデ屋根の貝がらの家', c: { wood: 22, glass: 4, rope: 10, cloth: 6 } }, { n: '巻貝かざりの白い家', c: { wood: 22, glass: 4, rope: 10, cloth: 6 } }, { n: '青い貝の屋根と旗の家', c: { wood: 24, glass: 6, rope: 10, cloth: 8 } }, { n: '巻貝のつののある家', c: { wood: 22, glass: 4, rope: 12, cloth: 6 } }, { n: 'カモメと貝の丸い屋根の家', c: { wood: 24, glass: 4, rope: 12, cloth: 6 } }, { n: 'ヒトデかざりの貝の家', c: { wood: 24, glass: 4, rope: 10, cloth: 8 } }, { n: '海辺の市場風の家', c: { wood: 30, glass: 2, rope: 14, cloth: 10 } }, { n: '巻貝の塔の家', c: { wood: 28, glass: 6, rope: 12, cloth: 6 } }, { n: '帆立貝の屋根の家', c: { wood: 22, glass: 4, rope: 10, cloth: 6 } }, { n: '貝がらのドームの家', c: { wood: 26, glass: 6, rope: 10, cloth: 6 } }, { n: '灯台つきの貝の家', c: { wood: 30, glass: 8, rope: 12, cloth: 8, stone: 6 } }, { n: 'うろこ屋根の貝の家', c: { wood: 22, glass: 4, rope: 10, cloth: 6 } },
  { n: 'ゆきだるまの雪の家', c: { wood: 24, cloth: 12, stone: 8, rope: 8 } }, { n: '雪のログ小屋', c: { wood: 30, cloth: 10, stone: 6, rope: 8 } }, { n: 'アーチ屋根の雪の家', c: { wood: 24, cloth: 12, stone: 10, rope: 8 } }, { n: 'とんがり雪屋根の家', c: { wood: 26, cloth: 12, stone: 6, rope: 8 } }, { n: 'かまくら（イグルー）', c: { wood: 10, cloth: 8, stone: 14, rope: 4 } }, { n: 'ポーチつきの雪の家', c: { wood: 28, cloth: 12, stone: 8, rope: 10 } }, { n: 'バルコニーつきの雪の家', c: { wood: 30, cloth: 14, stone: 10, rope: 10 } }, { n: '水車つきの雪の丸い家', c: { wood: 24, cloth: 10, stone: 12, rope: 10 } }, { n: '日よけのある雪の家', c: { wood: 26, cloth: 14, stone: 8, rope: 8 } }, { n: '雪に埋もれた家', c: { wood: 20, cloth: 10, stone: 10, rope: 6 } }, { n: '赤い旗の雪の家', c: { wood: 26, cloth: 14, stone: 8, rope: 8 } }, { n: '小さな雪の家（2階）', c: { wood: 22, cloth: 10, stone: 6, rope: 6 } }, { n: '小さな雪の家（丸窓）', c: { wood: 20, cloth: 10, stone: 6, rope: 6 } }
];
(function () { const D = window.RAFT.data; if (D.HUT_LOOKS.length !== D.HUT_N) console.error('小屋の見た目の数が合わない', D.HUT_LOOKS.length, D.HUT_N);
  D.HUT_LOOKS.forEach((l, i) => { D.ITEMS['hut' + i] = { name: l.n, lv: 0, w: 0, place: true, size: [2, 3], as: 'hut', hv: i, tip: '自分と相棒と住人の家（2×3マス）。タップで中に入って、休める' }; }); })();
// 見た目の系統（HUT_LOOKS と同じ順）。選ぶ画面の絞り込みに使う
window.RAFT.data.HUT_FAM = ["wood", "wood", "stone", "sea", "green", "stone", "sea", "green", "green", "snow", "stone", "stone", "stone", "green", "wood", "stone", "stone", "stone", "stone", "stone", "wood", "wood", "wood", "wood", "wood", "wood", "wood", "green", "sea", "sea", "sea", "sea", "sea", "sea", "sea", "sea", "sea", "sea", "sea", "sea", "sea", "snow", "snow", "snow", "snow", "snow", "snow", "snow", "snow", "snow", "snow", "snow", "snow", "snow"];
window.RAFT.data.HUT_FAMS = { wood: '木・わら', stone: '石・レンガ', sea: '海', green: '緑', snow: '雪' };
// 作物ごとの種袋（sd_<作物>）。流れてくる確率は、作物のレア度で決める。畑にまくと、その作物が育つ
(function () { const D = window.RAFT.data, W = { 1: 0.12, 2: 0.07, 3: 0.03 };      // 網で流れてくる確率（2026-10-26に、多すぎたので、約1/4に下げた）
  Object.keys(D.CROPS).forEach(k => { const c = D.CROPS[k]; D.ITEMS['sd_' + k] = { name: c.name + 'の種', lv: 2, w: W[c.star], seedOf: k, tip: '畑にまくと、' + c.name + 'が育つ' }; }); })();
