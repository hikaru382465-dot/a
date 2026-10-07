// 島の設計図データ（24×24マス）。各パーツはここだけを読む。Godot へ移すときもこの考え方を使い回せる。
// 座標：マス(x,z)は [x,x+1]×[z,z+1]。画面の手前（右下）が +x/+z 方向。段の高さは level×LEVEL。
(function (I) {
  const W = 24, D = 24, LEVEL = 0.6;
  const tiles = [];
  for (let z = 0; z < D; z++) {
    tiles[z] = [];
    for (let x = 0; x < W; x++) {
      const dist = Math.hypot((x - 11.5) / 10.8, (z - 11.5) / 10.3) + (I.vnoise(x * 0.35, z * 0.35, 7) - 0.5) * 0.28;
      let h = null;
      if (dist < 1) {
        h = dist > 0.80 ? 0 : 1;
        const tz = 9 + (I.vnoise(x * 0.45, 3, 11) - 0.5) * 2.2;
        if (z <= tz && dist < 0.9) h = 2;
        const pz = 3 + (I.vnoise(x * 0.5, 9, 13) - 0.5) * 2.0;
        if (z <= pz && dist < 0.72) h = 3;
      }
      tiles[z][x] = { h, t: h == null ? 'water' : 'sand' };
    }
  }
  // 小屋 4軒：x,z は左上のマス、w×d マス、h は段、roof は屋根の色
  const houses = [
    { id: 'shop',    x: 9,  z: 13, w: 3, d: 2, h: 1, roof: 'red',   awning: true,  doorX: 10 },
    { id: 'storage', x: 18, z: 12, w: 2, d: 2, h: 1, roof: 'brown', chimney: true, doorX: 18 },
    { id: 'homeA',   x: 8,  z: 6,  w: 2, d: 2, h: 2, roof: 'blue',  doorX: 8 },
    { id: 'homeB',   x: 14, z: 6,  w: 3, d: 2, h: 2, roof: 'red',   chimney: true, doorX: 15 }
  ];
  // 小屋の足もとと、まわり1マスを平らにする
  houses.forEach(hs => {
    for (let z = hs.z - 1; z <= hs.z + hs.d; z++) for (let x = hs.x - 1; x <= hs.x + hs.w; x++) {
      if (tiles[z] && tiles[z][x]) { tiles[z][x].h = hs.h; tiles[z][x].t = 'grass'; }
    }
  });
  // 船着き場：南の浜から海へ（2マス幅・長さ8）
  let zl = 0; for (let z = 0; z < D; z++) if (tiles[z][13].h != null) zl = z;
  for (let x = 13; x <= 14; x++) { tiles[zl][x].h = 0; tiles[zl][x].t = 'sand'; }
  const dock = { x: 13, w: 2, z0: zl, len: 8 };
  // 道
  const paths = [];
  const addPath = (x0, z0, x1, z1) => { for (let z = z0; z <= z1; z++) for (let x = x0; x <= x1; x++) paths.push([x, z]); };
  addPath(13, 8, 14, zl - 1);     // 船着き場から北へ
  addPath(10, 15, 19, 15);        // 手前の東西の道
  addPath(18, 14, 18, 14);        // 倉庫の前
  addPath(8, 8, 16, 8);           // 高い段の東西の道
  paths.forEach(([x, z]) => { const t = tiles[z] && tiles[z][x]; if (t && t.h != null) t.t = 'path'; });
  // 種類：浜(0)は砂、草(1,2)、岩(3)
  for (let z = 0; z < D; z++) for (let x = 0; x < W; x++) {
    const t = tiles[z][x]; if (t.h == null || t.t === 'path') continue;
    t.t = t.h === 0 ? 'sand' : t.h === 3 ? 'rock' : 'grass';
  }
  // 置き物（木・岩・草・たる・ランタン）
  const near = (x, z, m) => houses.some(hs => x >= hs.x - m && x < hs.x + hs.w + m && z >= hs.z - m && z < hs.z + hs.d + 2);
  const props = [];
  for (let z = 0; z < D; z++) for (let x = 0; x < W; x++) {
    const t = tiles[z][x]; if (t.h == null || t.t === 'path') continue;
    if (near(x, z, 1)) continue;
    if (x >= 12 && x <= 15 && z >= zl - 2) continue;
    const r = I.hash(x, z, 21), r2 = I.hash(x, z, 22), r3 = I.hash(x, z, 23);
    const px = x + 0.2 + r2 * 0.6, pz = z + 0.2 + r3 * 0.6;
    if (t.t === 'grass') {
      const pr = t.h === 2 ? 0.26 : 0.11;
      if (r < pr) props.push({ k: 'tree', v: Math.floor(r2 * 100) % 2, x: px, z: pz });
      else if (r < pr + 0.05) props.push({ k: 'bush', x: px, z: pz });
      else if (r < pr + 0.28) props.push({ k: 'tuft', x: px, z: pz });
      else if (r < pr + 0.30) props.push({ k: 'rock', x: px, z: pz });
    } else if (t.t === 'sand') {
      if (r < 0.07) props.push({ k: 'rock', x: px, z: pz });
      else if (r < 0.18) props.push({ k: 'tuft', x: px, z: pz });
    } else if (t.t === 'rock') {
      if (r < 0.35) props.push({ k: 'rock', x: px, z: pz });
      else if (r < 0.50) props.push({ k: 'tree', v: 1, x: px, z: pz });
    }
  }
  // 船着き場のたる・箱、ランタン
  const dz = dock.z0 + 0.5;
  props.push({ k: 'barrel', x: 12.7, z: dz + 1.2 }, { k: 'barrel', x: 12.35, z: dz + 1.55 }, { k: 'crate', x: 15.4, z: dz + 1.4 });
  props.push({ k: 'lantern', x: 13.15, z: dz + dock.len - 0.45, onDock: true }, { k: 'lantern', x: 14.85, z: dz + dock.len - 0.45, onDock: true });
  houses.forEach(hs => props.push({ k: 'lantern', x: hs.doorX + 1.35, z: hs.z + hs.d + 0.3 }));

  I.map = {
    W, D, LEVEL, tiles, houses, dock, paths, props,
    heightAt(x, z) { const t = tiles[Math.floor(z)] && tiles[Math.floor(z)][Math.floor(x)]; return t && t.h != null ? t.h * LEVEL : null; }
  };
})(window.ISLAND);
