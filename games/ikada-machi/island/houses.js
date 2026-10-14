// 小屋：同じ形に、大きさ・屋根の色・ひさし・煙突を変えて使い回す
window.ISLAND.parts.houses = function (c) {
  const { THREE, scene, map, I } = c, P = I.pal, L = map.LEVEL;
  const group = new THREE.Group(); scene.add(group);
  function plank(a, b, d, seed) {
    const [cv, g] = I.canvas(16, 16), r = I.rng(seed);
    I.rect(g, 0, 0, 16, 16, a);
    for (let row = 0; row < 4; row++) {
      const y = row * 4;
      for (let x = 0; x < 16; x++) { I.dot(g, x, y, d); if (r() < .5) I.dot(g, x, y + 1, b); if (r() < .12) I.dot(g, x, y + 2, b); }
      const sx = Math.floor(r() * 16); for (let k = 0; k < 4; k++) I.dot(g, sx, y + k, d);
      I.dot(g, (sx + 8) % 16, y + 2, P.stone3);
    }
    return cv;
  }
  function shingle(a, b, d, seed) {
    const [cv, g] = I.canvas(16, 16), r = I.rng(seed);
    I.rect(g, 0, 0, 16, 16, a);
    for (let row = 0; row < 4; row++) for (let x = 0; x < 16; x++) {
      const y = row * 4, off = (row % 2) * 4, edge = ((x + off) % 8) === 0;
      I.dot(g, x, y + 3, d); if (edge) { I.dot(g, x, y + 1, d); I.dot(g, x, y + 2, d); }
      if (r() < .16) I.dot(g, x, y, b);
    }
    return cv;
  }
  const wallBase = { cream: plank(P.wood5, P.wood4, P.wood3, 11), wood: plank(P.wood3, P.wood2, P.wood1, 12) };
  const roofCol = { red: [P.red1, P.red2, P.red0], brown: [P.wood2, P.wood3, P.wood0], blue: [P.blue1, P.blue2, P.blue0], green: [P.grass2, P.grass3, P.grass1] };
  const rep = (cv, w, h) => { const t = c.tex(cv, { repeat: true }); t.repeat.set(w, h); return t; };
  const stoneCv = (() => { const [cv, g] = I.canvas(16, 16), r = I.rng(5); I.rect(g, 0, 0, 16, 16, P.stone2);
    for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) { const v = r(); if (v < .2) I.dot(g, x, y, P.stone1); else if (v < .3) I.dot(g, x, y, P.stone3); }
    for (let x = 0; x < 16; x++) { I.dot(g, x, 7, P.stone1); I.dot(g, x, 15, P.stone0); } return cv; })();
  const windowMat = () => { const m = new THREE.MeshBasicMaterial({ color: new THREE.Color(1, 0.78, 0.4) }); c.windows.push({ mat: m, base: m.color.clone() }); return m; };
  const doorCv = (() => { const [cv, g] = I.canvas(8, 14), r = I.rng(9); I.rect(g, 0, 0, 8, 14, P.wood1);
    for (let x = 1; x < 7; x++) for (let y = 1; y < 14; y++) I.dot(g, x, y, (x % 2) ? P.wood2 : P.wood1);
    for (let x = 0; x < 8; x++) { I.dot(g, x, 0, P.line); } for (let y = 0; y < 14; y++) { I.dot(g, 0, y, P.line); I.dot(g, 7, y, P.line); }
    I.rect(g, 1, 4, 6, 1, P.wood0); I.rect(g, 1, 9, 6, 1, P.wood0); I.dot(g, 5, 7, P.glow); return cv; })();
  const stripeCv = (() => { const [cv, g] = I.canvas(8, 4); for (let x = 0; x < 8; x++) I.rect(g, x, 0, 1, 4, (x >> 1) % 2 ? P.cream : P.red1); I.rect(g, 0, 3, 8, 1, P.red0); return cv; })();

  map.houses.forEach((hs, idx) => {
    const g = new THREE.Group();
    const wallH = 1.1, baseY = hs.h * L, W = hs.w, D = hs.d;
    const wk = hs.id === 'shop' ? 'cream' : 'wood';
    const faceMat = (w, h) => new THREE.MeshLambertMaterial({ map: rep(wallBase[wk], w, h) });
    const plain = new THREE.MeshLambertMaterial({ color: new THREE.Color(P.wood1) });
    const body = new THREE.Mesh(new THREE.BoxGeometry(W, wallH, D), [faceMat(D, wallH), faceMat(D, wallH), plain, plain, faceMat(W, wallH), faceMat(W, wallH)]);
    body.position.set(0, 0.15 + wallH / 2, 0); g.add(body);
    const found = new THREE.Mesh(new THREE.BoxGeometry(W + 0.16, 0.18, D + 0.16), new THREE.MeshLambertMaterial({ map: rep(stoneCv, W + 1, 1) }));
    found.position.set(0, 0.09, 0); g.add(found);
    // 屋根（棟が x 方向）
    const ov = 0.28, x0 = -W / 2 - ov, x1 = W / 2 + ov, zf = D / 2 + ov, rh = 0.55 + D * 0.28, y0 = 0.15 + wallH;
    const rc = roofCol[hs.roof];
    const slopeLen = Math.hypot(zf, rh);
    const sp = new THREE.BufferGeometry();
    sp.setAttribute('position', new THREE.Float32BufferAttribute([
      x0, 0, zf, x1, 0, zf, x1, rh, 0, x0, 0, zf, x1, rh, 0, x0, rh, 0,
      x0, 0, -zf, x0, rh, 0, x1, rh, 0, x0, 0, -zf, x1, rh, 0, x1, 0, -zf], 3));
    const lx = x1 - x0;
    sp.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, lx, 0, lx, slopeLen, 0, 0, lx, slopeLen, 0, slopeLen, 0, 0, 0, slopeLen, lx, slopeLen, 0, 0, lx, slopeLen, lx, 0], 2));
    sp.computeVertexNormals();
    const roof = new THREE.Mesh(sp, new THREE.MeshLambertMaterial({ map: c.tex(shingle(rc[0], rc[1], rc[2], 20 + idx), { repeat: true }), side: THREE.DoubleSide }));
    roof.position.y = y0; g.add(roof);
    const gb = new THREE.BufferGeometry();
    gb.setAttribute('position', new THREE.Float32BufferAttribute([x0, 0, -zf, x0, 0, zf, x0, rh, 0, x1, 0, zf, x1, 0, -zf, x1, rh, 0], 3));
    gb.setAttribute('uv', new THREE.Float32BufferAttribute([-zf, 0, zf, 0, 0, rh, zf, 0, -zf, 0, 0, rh], 2)); gb.computeVertexNormals();
    const gable = new THREE.Mesh(gb, new THREE.MeshLambertMaterial({ map: c.tex(plank(P.wood1, P.wood0, P.wine, 30), { repeat: true }), side: THREE.DoubleSide }));
    gable.position.y = y0; g.add(gable);
    // 棟の板
    const ridge = new THREE.Mesh(new THREE.BoxGeometry(lx + 0.06, 0.07, 0.12), new THREE.MeshLambertMaterial({ color: new THREE.Color(rc[2]) }));
    ridge.position.set(0, y0 + rh, 0); g.add(ridge);
    // ドアと窓（手前 +z の面）
    const dxc = hs.doorX + 0.5 - (hs.x + W / 2);
    const door = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.875), new THREE.MeshBasicMaterial({ map: c.tex(doorCv) }));
    door.position.set(dxc, 0.15 + 0.45, D / 2 + 0.012); g.add(door);
    const wx = [dxc + 1.0, dxc - 0.9].filter(x => Math.abs(x) < W / 2 - 0.3);
    wx.forEach(x => {
      const frame = new THREE.Mesh(new THREE.PlaneGeometry(0.46, 0.46), new THREE.MeshBasicMaterial({ color: new THREE.Color(P.wood1) }));
      frame.position.set(x, 0.15 + 0.72, D / 2 + 0.01); g.add(frame);
      const gl = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.34), windowMat()); gl.position.set(x, 0.15 + 0.72, D / 2 + 0.02); g.add(gl);
      const cross = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.03), new THREE.MeshBasicMaterial({ color: new THREE.Color(P.wood1) })); cross.position.set(x, 0.15 + 0.72, D / 2 + 0.03); g.add(cross);
    });
    // 横の面（+x）にも窓を1つ
    const sx = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.34), windowMat()); sx.rotation.y = Math.PI / 2; sx.position.set(W / 2 + 0.012, 0.15 + 0.72, 0); g.add(sx);
    if (hs.awning) {
      const aw = new THREE.Mesh(new THREE.BoxGeometry(1.1, 0.04, 0.4), new THREE.MeshLambertMaterial({ map: rep(stripeCv, 1, 1) }));
      aw.rotation.x = 0.4; aw.position.set(dxc, 0.15 + 1.0, D / 2 + 0.18); g.add(aw);
    }
    if (hs.chimney) {
      const ch = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.7, 0.3), new THREE.MeshLambertMaterial({ map: rep(stoneCv, 1, 1) }));
      ch.position.set(W / 2 - 0.5, y0 + rh * 0.55 + 0.15, -0.35); g.add(ch);
      const cap = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.06, 0.38), new THREE.MeshLambertMaterial({ color: new THREE.Color(P.stone1) }));
      cap.position.set(W / 2 - 0.5, y0 + rh * 0.55 + 0.52, -0.35); g.add(cap);
    }
    g.position.set(hs.x + W / 2, baseY, hs.z + D / 2);
    group.add(g);
  });
  c.houses = group;
};
