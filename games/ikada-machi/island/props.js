// 置き物：木・茂み・岩・草・たる・箱・ランタン（絵は常にカメラのほうを向く板）
window.ISLAND.parts.props = function (c) {
  const { THREE, scene, map, I } = c, P = I.pal;
  const group = new THREE.Group(); scene.add(group);
  const OUT = '#2b1636';
  // 丸い形を、光（左上）の向きで5段に塗り分ける
  function blob(g, shapes, cols, seed, W, H) {
    const r = I.rng(seed), inside = (x, y) => shapes.find(s => (x - s[0]) ** 2 + (y - s[1]) ** 2 <= s[2] * s[2]);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const s = inside(x, y); if (!s) continue;
      const lit = ((x - s[0]) * -0.55 + (y - s[1]) * -0.75) / s[2];
      let i = Math.round(1.6 - lit * 2 + (r() - 0.5) * 1.3);
      I.dot(g, x, y, cols[Math.max(0, Math.min(cols.length - 1, i))]);
    }
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      if (!inside(x, y)) continue;
      if (!inside(x + 1, y) || !inside(x - 1, y) || !inside(x, y + 1) || !inside(x, y - 1)) I.dot(g, x, y, r() < 0.7 ? OUT : cols[cols.length - 1]);
    }
  }
  const G = [P.grass4, P.grass3, P.grass2, P.grass1, P.grass0];
  function tree(v) {
    const [cv, g] = I.canvas(40, 48); const r = I.rng(100 + v);
    if (v === 0) {
      I.rect(g, 18, 30, 4, 18, P.wood1); I.rect(g, 21, 30, 1, 18, P.wood0); I.rect(g, 17, 45, 6, 3, P.wood1); I.rect(g, 22, 46, 2, 2, P.wood0);
      for (let y = 30; y < 48; y++) { I.dot(g, 17, y, OUT); I.dot(g, 22, y, OUT); }
      blob(g, [[20, 17, 15], [11, 24, 9], [29, 24, 9], [20, 26, 10]], G, 3, 40, 48);
      for (let i = 0; i < 18; i++) I.dot(g, 8 + Math.floor(r() * 24), 5 + Math.floor(r() * 20), P.grass4);
    } else {
      I.rect(g, 19, 38, 3, 10, P.wood1); I.rect(g, 21, 38, 1, 10, P.wood0);
      const tiers = [[20, 12, 11, 14], [20, 22, 15, 14], [20, 33, 19, 13]];
      tiers.forEach(([cx, top, hw, hh], ti) => {
        for (let y = 0; y < hh; y++) {
          const w = Math.round(hw * (y + 1) / hh);
          for (let x = cx - w; x <= cx + w; x++) {
            const lit = (x - cx) / Math.max(w, 1), i = Math.round(1.8 + lit * 1.6 + y / hh * 0.8 + (r() - 0.5));
            I.dot(g, x, top + y, G[Math.max(0, Math.min(4, i))]);
          }
          I.dot(g, cx - w, top + y, r() < 0.7 ? OUT : P.grass0); I.dot(g, cx + w, top + y, r() < 0.7 ? OUT : P.grass0);
        }
        for (let x = cx - hw; x <= cx + hw; x++) if (r() < 0.8) I.dot(g, x, top + hh, OUT);
      });
    }
    return cv;
  }
  function bush() { const [cv, g] = I.canvas(24, 16); blob(g, [[8, 9, 6], [15, 9, 7], [12, 7, 6]], G, 4, 24, 16); return cv; }
  function rock() { const [cv, g] = I.canvas(20, 14); blob(g, [[9, 8, 7], [14, 9, 5]], [P.stone3, P.stone2, P.stone1, P.stone0, P.night0], 5, 20, 14); I.rect(g, 6, 5, 3, 1, P.stone3); return cv; }
  function tuft() { const [cv, g] = I.canvas(14, 10), r = I.rng(6);
    for (let i = 0; i < 6; i++) { const x = 2 + i * 2, h = 4 + Math.floor(r() * 4); for (let y = 0; y < h; y++) I.dot(g, x + (y > h - 3 ? (i % 2 ? 1 : -1) : 0), 9 - y, y > h - 3 ? P.grass4 : G[1 + (i % 2)]); }
    return cv; }
  function barrel() { const [cv, g] = I.canvas(12, 14); I.rect(g, 1, 3, 10, 10, P.wood2); I.rect(g, 0, 5, 12, 6, P.wood2);
    for (let x = 1; x < 11; x += 3) I.rect(g, x, 3, 1, 10, P.wood3); I.rect(g, 8, 3, 3, 10, P.wood1);
    I.rect(g, 0, 5, 12, 1, P.stone3); I.rect(g, 0, 10, 12, 1, P.stone2);
    I.rect(g, 2, 1, 8, 3, P.wood4); I.rect(g, 3, 2, 6, 1, P.wood1);
    for (let x = 1; x < 11; x++) { I.dot(g, x, 0, OUT); I.dot(g, x, 13, OUT); } for (let y = 1; y < 13; y++) { I.dot(g, 0, y, OUT); I.dot(g, 11, y, OUT); } return cv; }
  function crate() { const [cv, g] = I.canvas(14, 14); I.rect(g, 0, 0, 14, 14, P.wood3); I.rect(g, 1, 1, 12, 12, P.wood4);
    I.rect(g, 0, 0, 14, 2, P.wood2); I.rect(g, 0, 12, 14, 2, P.wood2); I.rect(g, 0, 0, 2, 14, P.wood2); I.rect(g, 12, 0, 2, 14, P.wood2);
    for (let i = 0; i < 12; i++) { I.dot(g, 1 + i, 1 + i, P.wood2); I.dot(g, 12 - i, 1 + i, P.wood2); }
    for (let x = 0; x < 14; x++) { I.dot(g, x, 13, OUT); } for (let y = 0; y < 14; y++) I.dot(g, 13, y, OUT); return cv; }
  function lantern() { const [cv, g] = I.canvas(10, 22); I.rect(g, 4, 8, 2, 14, P.wood1); I.dot(g, 5, 8, P.wood0);
    I.rect(g, 2, 3, 6, 6, P.wood0); I.rect(g, 3, 4, 4, 4, P.glow); I.rect(g, 4, 5, 2, 2, '#fff1c8'); I.rect(g, 1, 2, 8, 2, P.wood1); I.rect(g, 3, 0, 4, 2, P.wood2); I.rect(g, 2, 9, 6, 1, P.wood1); return cv; }
  function glow() { const [cv, g] = I.canvas(64, 64); const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    gr.addColorStop(0, 'rgba(255,200,110,1)'); gr.addColorStop(.35, 'rgba(255,150,60,.45)'); gr.addColorStop(1, 'rgba(255,120,40,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return cv; }
  function shadow() { const [cv, g] = I.canvas(32, 16); g.fillStyle = 'rgba(20,10,40,.55)'; g.beginPath(); g.ellipse(16, 8, 15, 7, 0, 0, 6.3); g.fill(); return cv; }

  const cache = {};
  const get = (k, f) => cache[k] || (cache[k] = f());
  const shadowTex = c.tex(shadow()), glowTex = c.tex(glow());
  function place(cv, x, z, opts = {}) {
    const y = opts.y != null ? opts.y : c.ground(x, z);
    const m = c.sprite(cv, { x, y, z, ppu: 16 }); group.add(m);
    if (opts.shadow) {
      const sh = new THREE.Mesh(new THREE.PlaneGeometry(opts.shadow, opts.shadow / 2), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false }));
      sh.rotation.x = -Math.PI / 2; sh.rotation.z = Math.PI / 4; sh.position.set(x + 0.08, y + 0.02, z + 0.08); group.add(sh);
    }
    return m;
  }
  map.props.forEach(p => {
    const onDock = p.onDock, gy = onDock ? 0.1 : undefined;
    if (p.k === 'tree') place(get('tree' + p.v, () => tree(p.v)), p.x, p.z, { shadow: 1.8 });
    else if (p.k === 'bush') place(get('bush', bush), p.x, p.z, { shadow: 1.1 });
    else if (p.k === 'rock') place(get('rock', rock), p.x, p.z, { shadow: 0.9 });
    else if (p.k === 'tuft') place(get('tuft', tuft), p.x, p.z);
    else if (p.k === 'barrel') place(get('barrel', barrel), p.x, p.z, { y: 0.1, shadow: 0.7 });
    else if (p.k === 'crate') place(get('crate', crate), p.x, p.z, { y: 0.1, shadow: 0.8 });
    else if (p.k === 'lantern') {
      const y = onDock ? 0.1 : c.ground(p.x, p.z);
      place(get('lantern', lantern), p.x, p.z, { y, shadow: 0.5 });
      const gm = new THREE.MeshBasicMaterial({ map: glowTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.15 });
      const gp = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 2.4), gm); gp.rotation.y = c.cam.yaw; gp.position.set(p.x, y + 1.05, p.z); group.add(gp);
      c.glows.push({ mat: gm });
    }
  });
};
