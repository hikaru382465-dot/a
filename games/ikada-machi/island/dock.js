// 船着き場：板張りの桟橋・杭・ロープ・小舟1そう
window.ISLAND.parts.dock = function (c) {
  const { THREE, scene, map, I } = c, P = I.pal, dk = map.dock;
  const group = new THREE.Group(); scene.add(group);
  function woodCanvas(a, b, d) {
    const [cv, g] = I.canvas(16, 16), r = I.rng(77);
    I.rect(g, 0, 0, 16, 16, a);
    for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) { const v = r(); if (v < .18) I.dot(g, x, y, b); else if (v < .26) I.dot(g, x, y, d); }
    for (let x = 0; x < 16; x++) { I.dot(g, x, 0, P.wine); I.dot(g, x, 15, b); }
    I.dot(g, 2, 7, P.stone3); I.dot(g, 13, 7, P.stone3);
    return cv;
  }
  const plankTex = c.tex(woodCanvas(P.wood3, P.wood2, P.wood4));
  const darkTex = c.tex(woodCanvas(P.wood1, P.wood0, P.wood2));
  const deckY = 0.1, z0 = dk.z0 + 0.5;
  // 板（海のほうへ並べる）
  const planks = [];
  for (let i = 0; i < dk.len * 2; i++) {
    const m = new THREE.MeshLambertMaterial({ map: plankTex });
    m.color.setScalar(0.82 + (I.hash(i, 4, 5) * 0.28));
    const b = new THREE.Mesh(new THREE.BoxGeometry(dk.w, 0.1, 0.46), m);
    b.position.set(dk.x + dk.w / 2, deckY - 0.05, z0 + 0.25 + i * 0.5); group.add(b); planks.push(m);
  }
  // 下の梁と杭
  const beamM = new THREE.MeshLambertMaterial({ map: darkTex });
  [0.12, dk.w - 0.12].forEach(dx => {
    const b = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.14, dk.len), beamM);
    b.position.set(dk.x + dx, deckY - 0.17, z0 + dk.len / 2); group.add(b);
  });
  const pileG = new THREE.CylinderGeometry(0.09, 0.1, 1.0, 8), capG = new THREE.CylinderGeometry(0.11, 0.11, 0.05, 8);
  const ropeM = new THREE.MeshLambertMaterial({ color: new THREE.Color(P.wood5) });
  for (let i = 0; i <= dk.len; i += 2) for (const dx of [-0.02, dk.w + 0.02]) {
    const p = new THREE.Mesh(pileG, beamM); p.position.set(dk.x + dx, deckY + 0.28 - 0.5, z0 + i); group.add(p);
    const cap = new THREE.Mesh(capG, new THREE.MeshLambertMaterial({ color: new THREE.Color(P.wood2) })); cap.position.set(dk.x + dx, deckY + 0.3, z0 + i); group.add(cap);
    const loop = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.025, 4, 8), ropeM); loop.rotation.x = Math.PI / 2;
    loop.position.set(dk.x + dx, deckY + 0.18, z0 + i); group.add(loop);
  }
  // 小舟
  const boat = new THREE.Group();
  const hullM = new THREE.MeshLambertMaterial({ map: plankTex, color: new THREE.Color('#d8c0a0') });
  const inM = new THREE.MeshLambertMaterial({ map: plankTex });
  const mk = (w, h, d, x, y, z, m) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); b.position.set(x, y, z); boat.add(b); return b; };
  mk(0.9, 0.08, 1.9, 0, 0.02, 0, inM);
  mk(0.08, 0.3, 1.9, -0.45, 0.17, 0, hullM); mk(0.08, 0.3, 1.9, 0.45, 0.17, 0, hullM);
  const bow = mk(0.85, 0.3, 0.08, 0, 0.17, 0.95, hullM), stern = mk(0.9, 0.3, 0.08, 0, 0.17, -0.95, hullM);
  mk(0.82, 0.05, 0.3, 0, 0.3, -0.5, darkTex && new THREE.MeshLambertMaterial({ map: darkTex }));
  mk(0.07, 0.07, 1.3, 0.72, 0.28, 0.1, new THREE.MeshLambertMaterial({ map: darkTex })).rotation.z = 0.15;
  boat.position.set(dk.x - 0.85, c.WATER_Y + 0.1, z0 + 4.3); boat.rotation.y = 0.06; group.add(boat);
  // 舟をつなぐロープ
  const rope = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.9, 5), ropeM);
  rope.rotation.z = Math.PI / 2 - 0.18; rope.position.set(dk.x - 0.4, deckY - 0.02, z0 + 3.55); group.add(rope);
  c.dock = { group, boat };
  return { update(t) { boat.position.y = c.WATER_Y + 0.1 + Math.sin(t * 1.6) * 0.025; boat.rotation.z = Math.sin(t * 1.3) * 0.02; boat.rotation.x = Math.sin(t * 1.1 + 1) * 0.015; } };
};
