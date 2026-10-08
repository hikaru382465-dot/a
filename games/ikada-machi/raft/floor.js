// イカダの床：木の板とロープ（見本 raft_floor_ref.png に近づけた仮のドット絵）。マスが増えたら作り直す
window.RAFT.parts.floor = function (c) {
  const { THREE, scene, state: s, I } = c, P = I.pal;
  const TOP = 0.2, THICK = 0.26;
  function topCv() {
    const [cv, g] = I.canvas(16, 16), r = I.rng(41);
    for (let row = 0; row < 4; row++) {
      const y = row * 4, base = row % 2 ? P.wood2 : P.wood3;
      I.rect(g, 0, y, 16, 4, base);
      for (let x = 0; x < 16; x++) { I.dot(g, x, y, P.wood4); if (r() < 0.4) I.dot(g, x, y + 1, P.wood4); if (r() < 0.35) I.dot(g, x, y + 2, P.wood1); I.dot(g, x, y + 3, P.wood1); }
      const sx = 3 + Math.floor(r() * 9); for (let k = 0; k < 4; k++) I.dot(g, sx, y + k, P.wine);
    }
    I.rect(g, 0, 0, 2, 16, P.wood5); for (let y = 0; y < 16; y += 3) { I.dot(g, 0, y, P.wood2); I.dot(g, 1, y + 1, P.wood2); }
    I.rect(g, 2, 0, 1, 16, P.wood1);
    for (let y = 2; y < 16; y += 4) I.dot(g, 6, y, P.stone3);
    return cv;
  }
  function sideCv() {
    const [cv, g] = I.canvas(16, 8); I.rect(g, 0, 0, 16, 8, P.wood1);
    for (let i = 0; i < 2; i++) { const cx = 4 + i * 8;
      for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) { const d = Math.hypot(x - 3.5, y - 3.5); if (d < 3.6) I.dot(g, cx - 4 + x, y, d < 1.4 ? P.wood4 : d < 2.6 ? P.wood3 : P.wood2); else if (d < 4.4) I.dot(g, cx - 4 + x, y, P.wine); } }
    for (let x = 0; x < 16; x++) I.dot(g, x, 7, P.wood0);
    return cv;
  }
  const topT = c.tex(topCv(), { repeat: true }), sideT = c.tex(sideCv(), { repeat: true });
  const topM = new THREE.MeshLambertMaterial({ map: topT }), sideM = new THREE.MeshLambertMaterial({ map: sideT });
  const group = new THREE.Group(); scene.add(group);
  const hl = new THREE.Group(); scene.add(hl);
  const hlGeo = new THREE.PlaneGeometry(0.94, 0.94); hlGeo.rotateX(-Math.PI / 2);
  const hlMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(1.4, 1.2, 0.7), transparent: true, opacity: 0.45, depthWrite: false });
  const boxG = new THREE.BoxGeometry(1, THICK, 1);
  let rev = -1, hlRev = '', hlList = null;
  function build() {
    while (group.children.length) group.remove(group.children[0]);
    s.raft.cells.forEach(([x, z]) => {
      const m = new THREE.Mesh(boxG, [sideM, sideM, topM, sideM, sideM, sideM]);
      m.position.set(x + 0.5, TOP - THICK / 2, z + 0.5); group.add(m);
    });
    rev = s.raftRev;
  }
  build();
  // ランタン（夜に光る）
  function lantern() { const [cv, g] = I.canvas(10, 20); I.rect(g, 4, 8, 2, 12, P.wood1); I.rect(g, 2, 3, 6, 6, P.wood0); I.rect(g, 3, 4, 4, 4, P.glow); I.rect(g, 4, 5, 2, 2, '#fff1c8'); I.rect(g, 1, 2, 8, 2, P.wood1); I.rect(g, 3, 0, 4, 2, P.wood2); return cv; }
  const gl = (() => { const [cv, g] = I.canvas(64, 64), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,200,110,1)'); gr.addColorStop(.35, 'rgba(255,150,60,.45)'); gr.addColorStop(1, 'rgba(255,120,40,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return cv; })();
  const lp = c.sprite(lantern(), { x: 0.28, y: TOP, z: 0.28, ppu: 22 }); scene.add(lp);
  const gm = new THREE.MeshBasicMaterial({ map: c.tex(gl), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.15 });
  const gp = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 2.4), gm); gp.rotation.y = c.cam.yaw; gp.position.set(0.28, TOP + 1.0, 0.28); scene.add(gp); c.glows.push({ mat: gm });
  // 置ける場所の光（置くモード）：[[x, z, 高さ], ...] を渡す。空で消える
  c.setHighlight = list => { hlList = list && list.length ? list : null; hlRev = '#'; };
  return { update() {
    if (s.raftRev !== rev) build();
    const want = hlList ? hlList.map(p => p.join(',')).join('|') : '';
    if (want !== hlRev) {
      while (hl.children.length) hl.remove(hl.children[0]);
      if (hlList) hlList.forEach(([x, z, y]) => { const m = new THREE.Mesh(hlGeo, hlMat); m.position.set(x + 0.5, y, z + 0.5); hl.add(m); });
      hlRev = want;
    }
  } };
};
