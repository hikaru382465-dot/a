// 地形：砂浜・草・道・岩の段差。ひとつのマスは 16×16 ピクセルのドット絵の面
window.ISLAND.parts.terrain = function (c) {
  const { THREE, scene, map, I } = c, P = I.pal, L = map.LEVEL, tiles = map.tiles;
  const WATER_Y = -0.25, SEABED = -0.6;

  function topCanvas(kind) {
    const [cv, g] = I.canvas(64, 64), r = I.rng(kind.length * 977 + 5);
    const base = { sand: P.sand0, grass: P.grass2, path: P.wood3, rock: P.stone2, plaza: P.stone2 }[kind];
    const alt = {
      sand: [P.sand1, P.wood5, P.wood4], grass: [P.grass3, P.grass1, P.grass4],
      path: [P.wood2, P.wood4, P.stone3], rock: [P.stone1, P.stone3, P.stone0], plaza: [P.stone1, P.stone3, P.stone0]
    }[kind];
    I.rect(g, 0, 0, 64, 64, base);
    for (let y = 0; y < 64; y++) for (let x = 0; x < 64; x++) {
      const v = r();
      if (v < 0.14) I.dot(g, x, y, alt[0]); else if (v < 0.27) I.dot(g, x, y, alt[1]); else if (v < 0.30) I.dot(g, x, y, alt[2]);
    }
    if (kind === 'plaza') {
      for (let by = 0; by < 64; by += 8) for (let x = 0; x < 64; x++) { I.dot(g, x, by, P.stone1); }
      for (let by = 0; by < 64; by += 8) for (let bx = (by / 8 % 2) * 4; bx < 64; bx += 8) for (let y = 0; y < 8; y++) I.dot(g, bx, by + y, P.stone1);
      return cv;
    }
    for (let i = 0; i < 70; i++) {
      const x = 1 + Math.floor(r() * 61), y = 2 + Math.floor(r() * 60);
      if (kind === 'grass') { I.dot(g, x, y, alt[2]); I.dot(g, x - 1, y - 1, alt[0]); I.dot(g, x + 1, y - 1, alt[0]); I.dot(g, x, y + 1, alt[1]); }
      else if (kind === 'path') { I.rect(g, x, y, 2, 1, alt[2]); I.dot(g, x, y + 1, P.wood1); I.dot(g, x + 1, y + 1, P.wood1); }
      else if (kind === 'sand') { I.dot(g, x, y, alt[1]); I.dot(g, x + 1, y, alt[2]); }
      else { I.rect(g, x, y, 3, 1, alt[2]); I.dot(g, x + 3, y + 1, alt[1]); I.dot(g, x + 1, y + 1, alt[1]); }
    }
    return cv;
  }
  function sideCanvas(kind) {
    const [cv, g] = I.canvas(16, 16), r = I.rng(kind.length * 31 + 3);
    const pal = { earth: [P.wood2, P.wood1, P.wood3, P.wood0], sandside: [P.wood5, P.wood4, P.sand0, P.wood3], rockside: [P.stone2, P.stone1, P.stone3, P.stone0] }[kind];
    I.rect(g, 0, 0, 16, 16, pal[0]);
    for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) { const v = r(); if (v < 0.2) I.dot(g, x, y, pal[1]); else if (v < 0.32) I.dot(g, x, y, pal[2]); }
    for (let x = 0; x < 16; x++) { I.dot(g, x, 0, pal[2]); I.dot(g, x, 1, r() < 0.5 ? pal[0] : pal[2]); I.dot(g, x, 8, pal[1]); if (r() < 0.5) I.dot(g, x, 9, pal[1]); I.dot(g, x, 15, pal[3]); }
    for (let i = 0; i < 3; i++) { const x = 1 + Math.floor(r() * 12), y = 3 + Math.floor(r() * 10); I.rect(g, x, y, 2, 2, pal[2]); I.dot(g, x, y + 1, pal[3]); I.dot(g, x + 1, y + 1, pal[3]); }
    return cv;
  }

  const topKinds = ['sand', 'grass', 'path', 'rock', 'plaza'], sideKinds = ['sandside', 'earth', 'rockside'];
  const sideOf = { sand: 'sandside', grass: 'earth', path: 'earth', rock: 'rockside', plaza: 'rockside' };
  const geo = {};
  topKinds.forEach(k => geo['t_' + k] = { p: [], n: [], u: [], i: [] });
  sideKinds.forEach(k => geo['s_' + k] = { p: [], n: [], u: [], i: [] });
  function quad(g, a, b, cc, d, n, ua, ub, uc, ud) {
    const o = g.p.length / 3; g.p.push(...a, ...b, ...cc, ...d);
    for (let k = 0; k < 4; k++) g.n.push(...n);
    g.u.push(...ua, ...ub, ...uc, ...ud); g.i.push(o, o + 1, o + 2, o, o + 2, o + 3);
  }
  const hAt = (x, z) => (tiles[z] && tiles[z][x] && tiles[z][x].h != null) ? tiles[z][x].h : null;
  for (let z = 0; z < map.D; z++) for (let x = 0; x < map.W; x++) {
    const t = tiles[z][x]; if (t.h == null) continue;
    const y = t.h * L, ux = (x % 4) / 4, uz = (z % 4) / 4, s = 0.25;
    quad(geo['t_' + t.t], [x, y, z], [x, y, z + 1], [x + 1, y, z + 1], [x + 1, y, z], [0, 1, 0], [ux, uz], [ux, uz + s], [ux + s, uz + s], [ux + s, uz]);
    const sg = geo['s_' + sideOf[t.t]];
    const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
    for (const [dx, dz] of dirs) {
      const nh = hAt(x + dx, z + dz), y0 = nh == null ? SEABED : nh * L;
      if (y0 >= y) continue;
      const dv = (y - y0) / L;
      const U = [[0, 0], [1, 0], [1, dv], [0, dv]];
      if (dx === 1) quad(sg, [x + 1, y, z], [x + 1, y, z + 1], [x + 1, y0, z + 1], [x + 1, y0, z], [1, 0, 0], ...U);
      else if (dx === -1) quad(sg, [x, y, z], [x, y, z + 1], [x, y0, z + 1], [x, y0, z], [-1, 0, 0], ...U);
      else if (dz === 1) quad(sg, [x, y, z + 1], [x + 1, y, z + 1], [x + 1, y0, z + 1], [x, y0, z + 1], [0, 0, 1], ...U);
      else quad(sg, [x, y, z], [x + 1, y, z], [x + 1, y0, z], [x, y0, z], [0, 0, -1], ...U);
    }
  }
  const group = new THREE.Group(); scene.add(group);
  function build(key, canvas, repeat) {
    const g = geo[key]; if (!g.p.length) return;
    const bg = new THREE.BufferGeometry();
    bg.setAttribute('position', new THREE.Float32BufferAttribute(g.p, 3));
    bg.setAttribute('normal', new THREE.Float32BufferAttribute(g.n, 3));
    bg.setAttribute('uv', new THREE.Float32BufferAttribute(g.u, 2)); bg.setIndex(g.i);
    const m = new THREE.MeshLambertMaterial({ map: c.tex(canvas, { repeat }), side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(bg, m); group.add(mesh);
  }
  topKinds.forEach(k => build('t_' + k, topCanvas(k), false));
  sideKinds.forEach(k => build('s_' + k, sideCanvas(k), true));

  c.WATER_Y = WATER_Y;
  c.ground = (x, z) => { const h = map.heightAt(x, z); return h == null ? WATER_Y : h; };
};
