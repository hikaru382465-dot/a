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
    seed:    { name: '種袋',     lv: 2, w: 0.9, tip: '畑にまく。何が育つかは、お楽しみ' },
    veg:     { name: '野菜',     lv: 0, w: 0, food: 8, drink: 3, tip: '畑でとれた。そのままだと少し。料理すると、もっと戻る' },
    dried:   { name: '干物',     lv: 0, w: 0, food: 30, tip: '干し魚だなで作る。食べると、おなかが戻る' },
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
    oven:    { name: 'かまど',   lv: 0, w: 0, place: true, tip: '飾り。石のかまど（焼くのは焚き火で）' },
    crate:   { name: '木箱',     lv: 0, w: 0, place: true, tip: '飾り。荷物を置いた感じになる' },
    chest:   { name: '宝箱',     lv: 0, w: 0, place: true, tip: '飾り。かっこいい箱' },
    plot:    { name: '畑', lv: 0, w: 0, place: true, tip: '置いて、タップ。種袋をまくと、野菜が育つ' },
    barrel:  { name: '樽',       lv: 0, w: 0, place: true, tip: '飾り。水の樽（のちに、水をためられるようにしたい）' },
    bed:     { name: 'ベッド',   lv: 0, w: 0, place: true, tip: '飾り。ふかふかのベッド（のちに、ねて回復できるようにしたい）' },
    shelf:   { name: '本棚',     lv: 0, w: 0, place: true, tip: '飾り。本や瓶をならべた棚' },
    windmill:{ name: '風車',     lv: 0, w: 0, place: true, tip: '飾り。小さな風車' },
    hut:     { name: '小屋',     lv: 0, w: 0, place: true, size: [2, 3], tip: '飾り。わらぶき屋根の小屋（2×3マス）' },
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
    { id: 'oven', out: 'oven', cost: { wood: 2, clay: 6, iron: 1 }, need: 'bench', tip: '粘土で作る石のかまど（飾り）' },
    { id: 'barrel', out: 'barrel', cost: { wood: 6, iron: 1 }, need: 'bench', tip: '木の樽を作る' },
    { id: 'bed', out: 'bed', cost: { wood: 8, cloth: 3, rope: 2 }, need: 'bench', tip: '布でふかふかのベッド' },
    { id: 'shelf', out: 'shelf', cost: { wood: 10, rope: 2 }, need: 'bench', tip: '本棚を作る' },
    { id: 'windmill', out: 'windmill', cost: { wood: 8, rope: 3, cloth: 2, iron: 1 }, need: 'bench', tip: '風で回る飾りの風車' },
    { id: 'hut', out: 'hut', cost: { wood: 14, cloth: 4, rope: 4 }, need: 'bench', tip: 'わらぶきの小屋（飾り）' },
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
  COOK: { sec: 12, perWood: 3, maxFish: 8, maxWood: 8, maxOut: 16 },   // 1匹12秒・木くず1個で3匹ぶん・各枠の上限
  // 船の住人との交渉：夕方に、嵐でなければ、1日に1回まで船が来る。1つの船に2つの取引。1つずつ、1回だけ
  BOAT: {
    FROM: 0.55, TO: 0.85, SPEED: 0.9, STAY: 110, OFFSET: 3.2,
    RES: {
      toto: { name: 'トトじいさん', hello: 'やあ、海の上でも商売さ。魚と交換しないかい？', thanks: 'まいど！ また来るよ。',
              deals: [{ want: { fish: 4 }, give: { cloth: 2 } }, { want: { grilled: 2 }, give: { rope: 2 } }] },
      mina: { name: 'ミナ（かじ屋の子）', hello: '鉄は重いんだ。ただじゃ渡せないよ。', thanks: 'いい物をありがとう。大切に使うね。',
              deals: [{ want: { grilled: 3 }, give: { iron: 2 } }, { want: { wood: 10 }, give: { iron: 1, stone: 1 } }] },
      kuro: { name: 'クロさん（焼き物の人）', hello: '雨の日は、土がこねやすいのよ。', thanks: 'また、いい土を持ってくるわ。',
              deals: [{ want: { wood: 8 }, give: { clay: 3 } }, { want: { coconut: 3 }, give: { glass: 2 } }] },
      pipi: { name: 'ピピ（見習い船乗り）', hello: 'ヤシの実、ちょうだい！ 石ならあるよ！', thanks: 'やったあ！ ありがとう！',
              deals: [{ want: { coconut: 2 }, give: { stone: 2 } }, { want: { fish: 3 }, give: { rope: 1, cloth: 1 } }] }
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
  PLOT: { water: 240, sunDry: 1.4, calmGrow: 1.5, seedBack: 0.5 },      // water＝水がもつ秒数／sunDry＝晴れの日の乾きの速さ／calmGrow＝凪の日の育ち／seedBack＝収穫で種が戻る確率
  CROPS: {
    tomato: { name: 'トマト',     sec: 360, star: 1, w: 5, tip: '赤くてつやつや。おなかにもいい' },
    carrot: { name: 'ニンジン',   sec: 420, star: 1, w: 5, tip: '土の中でのびる。ぽりぽりおいしい' },
    potato: { name: 'ジャガイモ', sec: 480, star: 1, w: 5, tip: 'ほくほくのいも。焼くとおいしそう' },
    corn:   { name: 'トウモロコシ', sec: 600, star: 2, w: 3, tip: '背が高くなる。きいろい実が自慢' },
    berry:  { name: 'イチゴ',     sec: 600, star: 2, w: 3, tip: 'あまい赤い実。おやつにぴったり' },
    melon:  { name: 'スイカ',     sec: 720, star: 3, w: 1.5, tip: '大きな丸い実。育つのに時間がかかる' }
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
