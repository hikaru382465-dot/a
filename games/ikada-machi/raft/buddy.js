// 相棒（ねこ）と、クリックの操作：床をクリック＝歩く／海をクリック＝網を投げる／網をクリック＝引き上げる
window.RAFT.parts.buddy = function (c) {
  const { THREE, scene, state: s, I, R } = c, P = I.pal;
  function frame(f) {
    const [cv, g] = I.canvas(20, 20), cream = '#e8dcb8', c2 = '#cdb98f', br = P.wood3, OUT = P.line;
    const px = (x, y, col) => I.dot(g, x, y, col);
    const disc = (cx, cy, rx, ry, col, col2) => { for (let y = 0; y < 20; y++) for (let x = 0; x < 20; x++) { const d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2; if (d <= 1) px(x, y, (x - cx) * -0.4 + (y - cy) * -0.6 > 0.25 * rx ? col : col2 && d > 0.55 ? col2 : col); } };
    // しっぽ
    for (let i = 0; i < 6; i++) { px(16 + (i > 3 ? 1 : 0), 14 - i, cream); px(17 + (i > 3 ? 1 : 0), 14 - i, c2); }
    // 脚（フレームでかわる）
    const lo = f === 1 ? 1 : 0, ro = f === 2 ? 1 : 0;
    I.rect(g, 5, 16 - lo, 3, 3 + lo, cream); I.rect(g, 11, 16 - ro, 3, 3 + ro, cream); I.rect(g, 8, 16, 3, 3, c2);
    disc(10, 13, 7.2, 5, cream, c2);
    I.rect(g, 12, 9, 5, 3, br); I.rect(g, 6, 11, 3, 2, br);
    disc(9, 7, 5.3, 4.6, cream, c2);
    for (let i = 0; i < 3; i++) { I.rect(g, 4 + i, 1 + (2 - i), 1, 3 - (2 - i) + 1, i === 0 ? br : cream); I.rect(g, 12 + i, 1 + i, 1, 3 - i + 1, i === 2 ? br : cream); }
    I.rect(g, 4, 2, 2, 3, br); I.rect(g, 12, 2, 3, 3, br);
    px(7, 7, OUT); px(7, 8, OUT); px(11, 7, OUT); px(11, 8, OUT); px(9, 9, P.red2); px(8, 10, c2); px(10, 10, c2);
    // 輪郭
    const d = g.getImageData(0, 0, 20, 20), o = new Uint8ClampedArray(d.data);
    const on = (x, y) => x >= 0 && y >= 0 && x < 20 && y < 20 && d.data[(y * 20 + x) * 4 + 3] > 0;
    for (let y = 0; y < 20; y++) for (let x = 0; x < 20; x++) if (!on(x, y) && (on(x + 1, y) || on(x - 1, y) || on(x, y + 1) || on(x, y - 1))) { const k = (y * 20 + x) * 4; o[k] = 0x37; o[k + 1] = 0x01; o[k + 2] = 0x27; o[k + 3] = 255; }
    g.putImageData(new ImageData(o, 20, 20), 0, 0);
    return cv;
  }
  const texs = [0, 1, 2].map(f => c.tex(frame(f)));
  const m = c.sprite(frame(0), { x: s.buddy.x, y: 0.2, z: s.buddy.z, ppu: 34 }); scene.add(m);
  const shadowCv = (() => { const [cv, g] = I.canvas(32, 16); g.fillStyle = 'rgba(20,10,40,.5)'; g.beginPath(); g.ellipse(16, 8, 15, 7, 0, 0, 6.3); g.fill(); return cv; })();
  const sh = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 0.4), new THREE.MeshBasicMaterial({ map: c.tex(shadowCv), transparent: true, depthWrite: false }));
  sh.rotation.x = -Math.PI / 2; sh.rotation.z = Math.PI / 4; scene.add(sh);
  m.material.map = texs[0]; m.material.side = THREE.DoubleSide;
  const base = m.scale.x;
  let t = 0;

  // ---- クリック ----
  const el = c.renderer.domElement, ray = new THREE.Raycaster(), plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -0.2), pt = new THREE.Vector3();
  let down = null;
  el.addEventListener('pointerdown', e => { down = { x: e.clientX, y: e.clientY }; });
  el.addEventListener('pointerup', e => {
    if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 6) { down = null; return; }
    down = null;
    ray.setFromCamera(new THREE.Vector2(e.clientX / innerWidth * 2 - 1, -(e.clientY / innerHeight) * 2 + 1), c.camera);
    if (!ray.ray.intersectPlane(plane, pt)) return;
    const x = Math.floor(pt.x), z = Math.floor(pt.z), sim = R.sim;
    if (c.mode.build) { if (sim.build(s, x, z)) c.hud.refresh(); return; }
    if (sim.has(s, x, z)) { sim.walkTo(s, x, z); return; }
    if (s.net.cell && s.net.cell[0] === x && s.net.cell[1] === z) { sim.haulNet(s); return; }
    if (!sim.placeNet(s, x, z)) s.events.push({ e: 'far' });
  });
  return { update(tt, dt) {
    t += dt; const b = s.buddy, walking = b.path.length > 0, bob = walking ? Math.abs(Math.sin(t * 11)) * 0.06 : (b.act ? Math.abs(Math.sin(t * 16)) * 0.04 : 0);
    m.position.set(b.x, 0.2 + bob, b.z); sh.position.set(b.x + 0.04, 0.215, b.z + 0.04);
    m.material.map = texs[walking ? 1 + (Math.floor(t * 6) % 2) : 0]; m.scale.x = base * b.face;
  } };
};
