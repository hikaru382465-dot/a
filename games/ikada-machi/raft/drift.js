// 流れてくる物と、網
window.RAFT.parts.drift = function (c) {
  const { THREE, scene, state: s, I, R } = c, P = I.pal, OUT = P.line;
  const draw = {
    wood(g) { I.rect(g, 1, 6, 10, 3, P.wood3); I.rect(g, 2, 3, 7, 3, P.wood2); I.rect(g, 1, 8, 10, 1, P.wood1); I.rect(g, 1, 6, 2, 3, P.wood4); I.dot(g, 10, 7, P.wood5); },
    fish(g) { I.rect(g, 2, 4, 7, 4, '#9fb8c4'); I.rect(g, 3, 4, 5, 1, '#d6e4ea'); I.rect(g, 9, 3, 2, 6, '#6f8fa3'); I.rect(g, 1, 5, 1, 2, '#9fb8c4'); I.dot(g, 3, 5, OUT); I.rect(g, 4, 7, 4, 1, '#d6e4ea'); },
    coconut(g) { for (let y = 0; y < 12; y++) for (let x = 0; x < 12; x++) if (Math.hypot(x - 5.5, y - 6) < 4.6) I.dot(g, x, y, Math.hypot(x - 4.5, y - 5) < 2.4 ? P.wood3 : P.wood1); I.dot(g, 4, 5, P.wood5); I.dot(g, 6, 8, OUT); I.dot(g, 8, 7, OUT); I.dot(g, 7, 9, OUT); },
    rope(g) { for (let y = 0; y < 12; y++) for (let x = 0; x < 12; x++) { const d = Math.hypot(x - 5.5, y - 6); if (d < 4.6 && d > 1.8) I.dot(g, x, y, (x + y) % 2 ? P.wood5 : P.wood4); } },
    cloth(g) { I.rect(g, 2, 3, 8, 7, P.cream); I.rect(g, 2, 3, 8, 1, '#fff6d8'); I.rect(g, 2, 9, 8, 1, '#cdb98f'); I.rect(g, 3, 6, 6, 1, P.red1); },
    clay(g) { for (let y = 0; y < 12; y++) for (let x = 0; x < 12; x++) if (Math.hypot((x - 5.5) / 1.1, (y - 7) / 0.85) < 4.4) I.dot(g, x, y, y < 6 ? P.wood3 : P.wood2); I.dot(g, 4, 5, P.wood5); },
    stone(g) { for (let y = 0; y < 12; y++) for (let x = 0; x < 12; x++) if (Math.hypot(x - 5.5, (y - 6.5) * 1.2) < 4.3) I.dot(g, x, y, y < 6 ? P.stone3 : P.stone2); I.dot(g, 4, 5, '#d8d8cf'); },
    iron(g) { I.rect(g, 2, 4, 8, 5, P.stone1); I.rect(g, 2, 4, 8, 1, P.stone3); I.rect(g, 3, 7, 6, 2, P.red0); I.dot(g, 5, 6, P.red2); },
    glass(g) { I.rect(g, 3, 3, 6, 7, '#8fc3bd'); I.rect(g, 4, 4, 2, 3, '#e6f6f2'); I.rect(g, 3, 9, 6, 1, '#46909c'); }
  };
  const icon = k => { const [cv, g] = I.canvas(12, 12); draw[k] && draw[k](g);
    const d = g.getImageData(0, 0, 12, 12), o = new Uint8ClampedArray(d.data), on = (x, y) => x >= 0 && y >= 0 && x < 12 && y < 12 && d.data[(y * 12 + x) * 4 + 3] > 0;
    for (let y = 0; y < 12; y++) for (let x = 0; x < 12; x++) if (!on(x, y) && (on(x + 1, y) || on(x - 1, y) || on(x, y + 1) || on(x, y - 1))) { const i = (y * 12 + x) * 4; o[i] = 0x37; o[i + 1] = 1; o[i + 2] = 0x27; o[i + 3] = 255; }
    g.putImageData(new ImageData(o, 12, 12), 0, 0); return cv; };
  c.itemIcon = icon;
  const cache = {}; const mk = k => cache[k] || (cache[k] = icon(k));
  const group = new THREE.Group(); scene.add(group);
  const meshes = new Map();
  // 網の絵（縄のあみ目と、うき）
  const netCv = (() => { const [cv, g] = I.canvas(16, 16); for (let i = 0; i < 16; i += 4) { I.rect(g, i, 0, 1, 16, P.wood5); I.rect(g, 0, i, 16, 1, P.wood5); }
    I.rect(g, 0, 0, 16, 1, P.wood2); I.rect(g, 0, 15, 16, 1, P.wood2); I.rect(g, 0, 0, 1, 16, P.wood2); I.rect(g, 15, 0, 1, 16, P.wood2); return cv; })();
  const netG = new THREE.PlaneGeometry(1, 1); netG.rotateX(-Math.PI / 2);
  const netM = new THREE.MeshBasicMaterial({ map: c.tex(netCv), transparent: true, opacity: 0.85, depthWrite: false, alphaTest: 0.1 }); c.sprites.push(netM);
  const net = new THREE.Mesh(netG, netM); net.visible = false; scene.add(net);
  const floatG = new THREE.CylinderGeometry(0.07, 0.07, 0.1, 8), floatM = new THREE.MeshLambertMaterial({ color: new THREE.Color(P.red1) });
  const floats = [0, 1, 2, 3].map(() => { const f = new THREE.Mesh(floatG, floatM); f.visible = false; scene.add(f); return f; });
  const held = [];
  let t = 0;
  return { update(tt, dt) {
    t += dt;
    const live = new Set();
    s.drift.forEach(it => {
      live.add(it.id);
      let m = meshes.get(it.id);
      if (!m) { m = c.sprite(mk(it.k), { x: it.x, y: 0.05, z: it.z, ppu: 30 }); group.add(m); meshes.set(it.id, m); m.userData.s = m.scale.clone(); }
      m.position.set(it.x, 0.03 + Math.sin(t * 2.2 + it.id) * 0.03, it.z);
      m.scale.copy(m.userData.s).multiplyScalar(Math.min(1, it.born * 2) * 0.9);
    });
    for (const [id, m] of meshes) if (!live.has(id)) { group.remove(m); meshes.delete(id); }
    // 網
    const n = s.net.cell;
    net.visible = !!n; floats.forEach(f => f.visible = !!n);
    if (n) {
      const y = 0.04 + Math.sin(t * 1.7) * 0.012; net.position.set(n[0] + 0.5, y, n[1] + 0.5);
      [[0.04, 0.04], [0.96, 0.04], [0.04, 0.96], [0.96, 0.96]].forEach((p, i) => floats[i].position.set(n[0] + p[0], y + 0.03, n[1] + p[1]));
    }
    while (held.length > (n ? s.net.held.length : 0)) group.remove(held.pop());
    if (n) s.net.held.forEach((k, i) => {
      if (!held[i]) { held[i] = c.sprite(mk(k), { x: 0, y: 0, z: 0, ppu: 36 }); group.add(held[i]); held[i].userData.k = k; }
      if (held[i].userData.k !== k) { group.remove(held[i]); held[i] = c.sprite(mk(k), { x: 0, y: 0, z: 0, ppu: 36 }); group.add(held[i]); held[i].userData.k = k; }
      held[i].position.set(n[0] + 0.25 + (i % 3) * 0.25, 0.07 + Math.sin(t * 2 + i) * 0.015, n[1] + 0.3 + Math.floor(i / 3) * 0.3);
    });
  } };
};
