// 相棒（人間の女の子）と、クリックの操作：床をクリック＝歩く／海をクリック＝網を投げる／網をクリック＝引き上げる
window.RAFT.parts.buddy = function (c) {
  const { THREE, scene, state: s, I, R } = c, P = I.pal;
  function frame(f) {
    const W = 16, H = 26, [cv, g] = I.canvas(W, H), OUT = P.line;
    const skin = '#eec3a0', skin2 = '#cf9c78', hair = P.wood1, hair2 = P.wood3, hair3 = P.wood0;
    const top = '#f0e6c8', top2 = '#cdb98f', sk = P.blue2, sk2 = P.blue1, sk3 = P.blue3, boot = P.wood1, rib = P.red2;
    const px = (x, y, col) => I.dot(g, x, y, col), rc = (x, y, w, h, col) => I.rect(g, x, y, w, h, col);
    const disc = (cx, cy, rx, ry, col) => { for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (((x - cx + 0.5) / rx) ** 2 + ((y - cy + 0.5) / ry) ** 2 <= 1) px(x, y, col); };
    const swing = f === 0 ? 0 : (f === 1 ? 1 : -1), aL = swing, aR = -swing, legL = swing > 0 ? 1 : 0, legR = swing < 0 ? 1 : 0;
    rc(2, 8, 2, 8, hair); rc(2, 14, 2, 2, hair3); px(3, 9, hair2);              // ポニーテール
    disc(8, 6, 5, 5, hair); rc(5, 6, 6, 5, skin); rc(6, 10, 4, 1, skin2);        // 頭・顔
    rc(4, 2, 8, 3, hair); rc(4, 5, 2, 3, hair); rc(10, 5, 2, 3, hair); px(7, 5, hair); px(8, 5, hair2); rc(6, 2, 3, 1, hair2);   // 前髪
    rc(6, 7, 1, 2, P.wine); rc(10, 7, 1, 2, P.wine); px(5, 9, '#e0a090'); px(11, 9, '#e0a090'); px(8, 10, P.red1);          // 目・ほお・口
    rc(7, 11, 2, 1, skin2);
    rc(5, 12, 6, 5, top); rc(10, 12, 1, 5, top2); rc(5, 16, 6, 1, rib); px(8, 16, '#f0c9a0');       // 上着・帯
    rc(3, 12 + aL, 2, 3, top); rc(3, 15 + aL, 2, 2, skin); rc(11, 12 + aR, 2, 3, top); rc(11, 15 + aR, 2, 2, skin);
    rc(4, 17, 8, 4, sk); rc(3, 20, 10, 2, sk); rc(3, 21, 10, 1, sk2); px(6, 18, sk2); px(9, 19, sk2); px(6, 20, sk2); px(9, 21, sk3); px(5, 18, sk3); px(10, 18, sk3);   // スカート
    rc(6, 22, 2, 2 - legL, skin); rc(9, 22, 2, 2 - legR, skin); rc(5, 24 - legL, 3, 2, boot); rc(9, 24 - legR, 3, 2, boot);
    const d = g.getImageData(0, 0, W, H), o = new Uint8ClampedArray(d.data), on = (x, y) => x >= 0 && y >= 0 && x < W && y < H && d.data[(y * W + x) * 4 + 3] > 0;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (!on(x, y) && (on(x + 1, y) || on(x - 1, y) || on(x, y + 1) || on(x, y - 1))) { const k = (y * W + x) * 4; o[k] = 0x37; o[k + 1] = 0x01; o[k + 2] = 0x27; o[k + 3] = 255; }
    g.putImageData(new ImageData(o, W, H), 0, 0);
    return cv;
  }
  const texs = [0, 1, 2].map(f => c.tex(frame(f)));
  const m = c.sprite(frame(0), { x: s.buddy.x, y: 0.2, z: s.buddy.z, ppu: 30 }); scene.add(m);
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
