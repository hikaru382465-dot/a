// 島の設計図データ（48×48マス＝24×24のブロック4つぶん）。各パーツはここだけを読む。
// 座標：マス(x,z)は [x,x+1]×[z,z+1]。画面の手前（右下）が +x/+z 方向。段の高さは level×LEVEL。
// 島を広げるときは W,D と下の「小屋」「道」の座標を足す。
(function (I) {
  const W = 48, D = 48, LEVEL = 0.6, CX = W / 2 - 0.5, CZ = D / 2 - 0.5;
  const RX = W * 0.45, RZ = D * 0.43;
  const tiles = [];
  for (let z = 0; z < D; z++) {
    tiles[z] = [];
    for (let x = 0; x < W; x++) {
      const dist = Math.hypot((x - CX) / RX, (z - CZ) / RZ) + (I.vnoise(x * 0.18, z * 0.18, 7) - 0.5) * 0.26 + (I.vnoise(x * 0.5, z * 0.5, 8) - 0.5) * 0.06;
      let h = null;
      if (dist < 1) {
        h = dist > 0.85 ? 0 : 1;
        const tz = 18 + (I.vnoise(x * 0.22, 3, 11) - 0.5) * 4.4;
        if (z <= tz && dist < 0.93) h = 2;
        const pz = 14 + (I.vnoise(x * 0.25, 9, 13) - 0.5) * 3;
        if (z <= pz && dist < 0.70) h = 3;
      }
      tiles[z][x] = { h, t: h == null ? 'water' : 'sand' };
    }
  }
  // 小屋：x,z は左上のマス、w×d マス、h は段、roof は屋根の色、doorX は入口のマス
  const houses = [
    { id: 'shop',    x: 14, z: 31, w: 3, d: 2, h: 1, roof: 'red',   awning: true,  doorX: 15 },
    { id: 'storage', x: 30, z: 31, w: 2, d: 2, h: 1, roof: 'brown', chimney: true, doorX: 30 },
    { id: 'homeC',   x: 28, z: 26, w: 2, d: 2, h: 1, roof: 'green', doorX: 28 },
    { id: 'homeD',   x: 17, z: 26, w: 2, d: 2, h: 1, roof: 'brown', chimney: true, doorX: 18 },
    { id: 'homeE',   x: 10, z: 22, w: 2, d: 2, h: 1, roof: 'green', doorX: 10 },
    { id: 'homeF',   x: 35, z: 22, w: 2, d: 2, h: 1, roof: 'blue',  doorX: 36 },
    { id: 'homeA',   x: 12, z: 13, w: 2, d: 2, h: 2, roof: 'blue',  doorX: 12 },
    { id: 'homeB',   x: 33, z: 13, w: 3, d: 2, h: 2, roof: 'red',   chimney: true, doorX: 34 }
  ];
  const plaza = { x: 20, z: 30, w: 8, d: 6, h: 1 };
  const flat = (x0, z0, x1, z1, h) => { for (let z = z0; z <= z1; z++) for (let x = x0; x <= x1; x++) if (tiles[z] && tiles[z][x]) { tiles[z][x].h = h; tiles[z][x].t = 'grass'; } };
  houses.forEach(hs => flat(hs.x - 1, hs.z - 1, hs.x + hs.w, hs.z + hs.d, hs.h));
  flat(plaza.x - 1, plaza.z - 1, plaza.x + plaza.w, plaza.z + plaza.d, 1);
  // 船着き場：南の浜から海へ（2マス幅・長さ10）
  let zl = 0; for (let z = 0; z < D; z++) if (tiles[z][23].h != null) zl = z;
  for (let x = 23; x <= 24; x++) { tiles[zl][x].h = 0; tiles[zl][x].t = 'sand'; }
  const dock = { x: 23, w: 2, z0: zl, len: 10 };
  // 道
  const paths = [];
  const addPath = (x0, z0, x1, z1) => { for (let z = z0; z <= z1; z++) for (let x = x0; x <= x1; x++) paths.push([x, z]); };
  addPath(23, 36, 24, zl - 1);   // 船着き場から広場へ
  addPath(23, 15, 24, 29);       // 広場から北の高い段へ
  addPath(15, 33, 19, 33);       // 広場の西（店）
  addPath(28, 33, 31, 33);       // 広場の東（倉庫）
  addPath(18, 28, 22, 28); addPath(25, 28, 29, 28);   // 広場の北の小屋
  addPath(10, 24, 36, 24);       // 中ほどの東西の道
  addPath(12, 15, 36, 15);       // 高い段の東西の道
  paths.forEach(([x, z]) => { const t = tiles[z] && tiles[z][x]; if (t && t.h != null) t.t = 'path'; });
  for (let z = plaza.z; z < plaza.z + plaza.d; z++) for (let x = plaza.x; x < plaza.x + plaza.w; x++) tiles[z][x].t = 'plaza';
  // 種類：浜(0)は砂、草(1,2)、岩(3)
  for (let z = 0; z < D; z++) for (let x = 0; x < W; x++) {
    const t = tiles[z][x]; if (t.h == null || t.t === 'path' || t.t === 'plaza') continue;
    t.t = t.h === 0 ? 'sand' : t.h === 3 ? 'rock' : 'grass';
  }
  // 置き物（木・岩・草・たる・ランタン・井戸）
  const near = (x, z, m) => houses.some(hs => x >= hs.x - m && x < hs.x + hs.w + m && z >= hs.z - m && z < hs.z + hs.d + 2);
  const props = [];
  for (let z = 0; z < D; z++) for (let x = 0; x < W; x++) {
    const t = tiles[z][x]; if (t.h == null || t.t === 'path' || t.t === 'plaza') continue;
    if (near(x, z, 2)) continue;
    if (x >= 21 && x <= 26 && z >= zl - 2) continue;
    const r = I.hash(x, z, 21), r2 = I.hash(x, z, 22), r3 = I.hash(x, z, 23);
    const px = x + 0.2 + r2 * 0.6, pz = z + 0.2 + r3 * 0.6;
    if (t.t === 'grass') {
      const pr = t.h === 2 ? 0.20 : 0.08;
      if (r < pr) props.push({ k: 'tree', v: Math.floor(r2 * 100) % 2, x: px, z: pz });
      else if (r < pr + 0.04) props.push({ k: 'bush', x: px, z: pz });
      else if (r < pr + 0.24) props.push({ k: 'tuft', x: px, z: pz });
      else if (r < pr + 0.26) props.push({ k: 'rock', x: px, z: pz });
    } else if (t.t === 'sand') {
      if (r < 0.05) props.push({ k: 'rock', x: px, z: pz });
      else if (r < 0.15) props.push({ k: 'tuft', x: px, z: pz });
    } else if (t.t === 'rock') {
      if (r < 0.30) props.push({ k: 'rock', x: px, z: pz });
      else if (r < 0.42) props.push({ k: 'tree', v: 1, x: px, z: pz });
    }
  }
  const dz = dock.z0 + 0.5;
  props.push({ k: 'barrel', x: 22.7, z: dz + 1.2 }, { k: 'barrel', x: 22.35, z: dz + 1.55 }, { k: 'crate', x: 25.4, z: dz + 1.4 });
  props.push({ k: 'lantern', x: 23.15, z: dz + dock.len - 0.45, onDock: true }, { k: 'lantern', x: 24.85, z: dz + dock.len - 0.45, onDock: true });
  houses.forEach(hs => props.push({ k: 'lantern', x: hs.doorX + 1.35, z: hs.z + hs.d + 0.3 }));
  props.push({ k: 'well', x: plaza.x + plaza.w / 2, z: plaza.z + plaza.d / 2 });
  [[0.5, 0.5], [plaza.w - 0.5, 0.5], [0.5, plaza.d - 0.5], [plaza.w - 0.5, plaza.d - 0.5]].forEach(([a, b]) => props.push({ k: 'lantern', x: plaza.x + a, z: plaza.z + b }));

  I.map = {
    W, D, LEVEL, tiles, houses, dock, paths, props, plaza,
    heightAt(x, z) { const t = tiles[Math.floor(z)] && tiles[Math.floor(z)][Math.floor(x)]; return t && t.h != null ? t.h * LEVEL : null; }
  };
})(window.ISLAND);
