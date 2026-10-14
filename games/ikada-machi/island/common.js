// 島マップ 共通部品：色・乱数・ノイズ・キャンバス
window.ISLAND = { parts: {}, order: ['camera', 'terrain', 'water', 'dock', 'houses', 'props', 'light'] };
(function (I) {
  // 色は床の見本（raft_floor_ref.png）の色を土台に、緑・水・屋根の色を足した
  I.pal = {
    line: '#370127', wine: '#3d2938',
    wood0: '#513433', wood1: '#6b4231', wood2: '#8a5430', wood3: '#9f704a', wood4: '#b58c64', wood5: '#caa97e',
    sand0: '#d0c09a', sand1: '#d9c8a1',
    stone0: '#383e57', stone1: '#514856', stone2: '#736967', stone3: '#97978b',
    night0: '#272347', night1: '#2e2f4d', sea0: '#223446', teal: '#2d4444',
    grass0: '#2d4444', grass1: '#3b5a3f', grass2: '#587a45', grass3: '#7e9a52', grass4: '#a8b862',
    red0: '#71363c', red1: '#944a45', red2: '#b8654f',
    blue0: '#1f3f5c', blue1: '#2c6f8a', blue2: '#46909c', blue3: '#8fc3bd',
    cream: '#e8dcb8', glow: '#f2c879'
  };
  I.rng = function (a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      let t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  };
  I.hash = function (x, z, s) {
    let h = Math.imul(x | 0, 374761393) + Math.imul(z | 0, 668265263) + Math.imul((s || 0) | 0, 1442695041);
    h = Math.imul(h ^ h >>> 13, 1274126177); h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  };
  I.vnoise = function (x, z, s) {
    const xi = Math.floor(x), zi = Math.floor(z), fx = x - xi, fz = z - zi;
    const u = fx * fx * (3 - 2 * fx), v = fz * fz * (3 - 2 * fz);
    const a = I.hash(xi, zi, s), b = I.hash(xi + 1, zi, s), c = I.hash(xi, zi + 1, s), d = I.hash(xi + 1, zi + 1, s);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  };
  I.canvas = function (w, h) {
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    const g = c.getContext('2d'); g.imageSmoothingEnabled = false;
    return [c, g];
  };
  I.dot = function (g, x, y, col) { g.fillStyle = col; g.fillRect(x | 0, y | 0, 1, 1); };
  I.rect = function (g, x, y, w, h, col) { g.fillStyle = col; g.fillRect(x | 0, y | 0, w | 0, h | 0); };
})(window.ISLAND);
