// イカダ暮らし：表（数字はここだけ。あとで Godot の Resource / Dictionary にそのまま移せる）
window.RAFT = { parts: {}, order: ['camera', 'water', 'light', 'floor', 'buddy', 'drift', 'hud'] };
window.RAFT.data = {
  DAY_SEC: 240,                       // 1日の長さ（秒）。URLの最後に ?fast で10倍
  MAX_SIZE: 8,                        // イカダの最大（8×8マス）
  BUILD: { floor: { wood: 4 } },      // 床を1マス足す材料
  NEEDS: { hunger: 0.25, thirst: 0.33, low: 30 },   // 1秒に減る量、相棒が自分で食べ始める値
  // lv：この網のレベル以上で取れる。w：流れてくる重み。food/drink：食べる・飲むで戻る量
  ITEMS: {
    wood:    { name: '木くず',   lv: 1, w: 6 },
    fish:    { name: '小魚',     lv: 1, w: 3, food: 25 },
    coconut: { name: 'ヤシの実', lv: 1, w: 2, food: 8, drink: 22 },
    rope:    { name: '縄',       lv: 2, w: 3 },
    cloth:   { name: '布',       lv: 2, w: 2 },
    clay:    { name: '粘土',     lv: 3, w: 2 },
    stone:   { name: '石',       lv: 3, w: 2 },
    iron:    { name: '鉄くず',   lv: 4, w: 1 },
    glass:   { name: 'ガラス',   lv: 4, w: 1 },
    water:   { name: '真水',     lv: 0, w: 0, drink: 35 }   // 雨でたまる（流れてはこない）
  },
  // 網（投げる）：range＝ゲージ満タンで飛ぶ距離（マス）、r＝網がとる広さ（半径・マス）、cap＝1回で入る数
  // 道具（持ち物の先頭に並ぶ。選ぶと手に持つ）
  TOOLS: { net: { name: '網', tip: '海を押し続けて、離すと投げる' } },
  NET_LV: [
    { lv: 1, range: 4,   r: 0.9, cap: 3 },
    { lv: 2, range: 5.5, r: 1.0, cap: 4, cost: { wood: 8 } },
    { lv: 3, range: 7,   r: 1.1, cap: 5, cost: { wood: 12, rope: 4, cloth: 3 } },
    { lv: 4, range: 9,   r: 1.3, cap: 6, cost: { wood: 16, clay: 5, stone: 5 } }
  ],
  NET_MIN: 1.5,      // ゲージが0でも、これだけは飛ぶ
  NET_REST: 4.5,     // 水の上でとっている時間（秒）
  NET_HAUL: 0.6,     // 引き上げの絵が動く時間（秒）
  NET_FLY: 0.55,     // 飛んでいる時間（秒）
  // speed：流れの速さ（マス/秒）、rate：物の出る多さ、thirst：のどのかわく速さの倍率、w：次に選ばれやすさ
  WEATHER: {
    sunny: { name: '晴れ', speed: 0.6, rate: 1.0, thirst: 1.4, w: 5 },
    calm:  { name: '凪',   speed: 0.25, rate: 0.5, thirst: 0.9, w: 2.5 },
    storm: { name: '嵐',   speed: 1.2, rate: 1.8, thirst: 0.6, w: 2.5 }
  }
};
