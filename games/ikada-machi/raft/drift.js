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
    net(g) { for (let i = 1; i < 11; i += 3) { I.rect(g, i, 1, 1, 10, P.wood5); I.rect(g, 1, i, 10, 1, P.wood5); } I.rect(g, 1, 1, 10, 1, P.wood2); I.rect(g, 1, 10, 10, 1, P.wood2); I.rect(g, 1, 1, 1, 10, P.wood2); I.rect(g, 10, 1, 1, 10, P.wood2); I.rect(g, 0, 0, 2, 2, P.red1); I.rect(g, 10, 0, 2, 2, P.red1); },
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
  // 網の絵（縄のあみ目）と、ねらいの輪
  const netCv = (() => { const [cv, g] = I.canvas(16, 16); for (let i = 0; i < 16; i += 4) { I.rect(g, i, 0, 1, 16, P.wood5); I.rect(g, 0, i, 16, 1, P.wood5); }
    for (let i = 0; i < 16; i++) for (let j = 0; j < 16; j++) if (Math.hypot(i - 7.5, j - 7.5) > 7.9) g.clearRect(i, j, 1, 1);
    return cv; })();
  const ringCv = (() => { const [cv, g] = I.canvas(64, 64); g.strokeStyle = 'rgba(255,240,200,.95)'; g.lineWidth = 3; g.setLineDash([6, 5]); g.beginPath(); g.arc(32, 32, 28, 0, 6.3); g.stroke(); return cv; })();
  const ringTex = new THREE.CanvasTexture(ringCv); ringTex.colorSpace = THREE.SRGBColorSpace;
  const flat = new THREE.PlaneGeometry(1, 1); flat.rotateX(-Math.PI / 2);
  const netT = c.tex(netCv);
  const netM = new THREE.MeshBasicMaterial({ map: netT, transparent: true, opacity: 0.9, depthWrite: false, alphaTest: 0.1, side: THREE.DoubleSide }); c.sprites.push(netM);
  const net = new THREE.Mesh(flat, netM); net.visible = false; scene.add(net);
  const ringM = new THREE.MeshBasicMaterial({ map: ringTex, transparent: true, depthWrite: false, color: new THREE.Color(1.3, 1.2, 0.9) });
  const ring = new THREE.Mesh(flat, ringM); ring.visible = false; scene.add(ring);
  const lineG = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3(1, 0, 0)]);
  const aimLine = new THREE.Line(lineG, new THREE.LineDashedMaterial({ color: 0xfff0c8, dashSize: 0.18, gapSize: 0.14, transparent: true, opacity: 0.9 })); aimLine.visible = false; scene.add(aimLine);
  const ropeLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3(1, 0, 0)]), new THREE.LineBasicMaterial({ color: new THREE.Color(P.wood5) })); ropeLine.visible = false; scene.add(ropeLine);
  const setLine = (line, ax, ay, az, bx, by, bz) => { const p = line.geometry.attributes.position; p.setXYZ(0, ax, ay, az); p.setXYZ(1, bx, by, bz); p.needsUpdate = true; line.computeLineDistances(); };
  // ひかるが描いた網の絵（net_art.js）。読み込めたら、プログラムで描いた網のかわりに使う
  const NA = R.netArt, art = { ready: false, fly: [], splash: [], idle: [] };
  const artM = new THREE.MeshBasicMaterial({ transparent: true, alphaTest: 0.04, depthWrite: false, depthTest: false }); c.sprites.push(artM);
  const artMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), artM); artMesh.visible = false; artMesh.rotation.y = c.cam.yaw; artMesh.renderOrder = 2; scene.add(artMesh);
  if (NA) {
    let left = 0; const all = [].concat(NA.fly, NA.splash, NA.idle);
    all.forEach(f => { left++; const im = new Image(); im.onload = () => { const tx = new THREE.Texture(im); tx.colorSpace = THREE.SRGBColorSpace; tx.magFilter = tx.minFilter = THREE.NearestFilter; tx.generateMipmaps = false; tx.needsUpdate = true; f.tex = tx; if (--left === 0) art.ready = true; }; im.src = f.src; });
  }
  const camRight = new THREE.Vector3(Math.cos(c.cam.yaw), 0, -Math.sin(c.cam.yaw));
  function showArt(f, u, x, y, z) {
    artM.map = f.tex; artM.needsUpdate = true;
    artMesh.scale.set(f.w * u, f.h * u / Math.cos(c.cam.pitch), 1);
    const dx = (f.ax - f.w / 2) * u, dy = (f.h / 2 - f.ay) * u / Math.cos(c.cam.pitch);
    artMesh.position.set(x - camRight.x * dx, y + dy, z - camRight.z * dx);
    artMesh.visible = true;
  }
  const held = [];
  let t = 0;
  c.aim = c.aim || { active: false, x: 0, z: 0, power: 0 };
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
    // ねらい（押している間、ゲージの強さで落ちる場所が動く）
    const a = c.aim, b = s.buddy, nl = R.data.NET_LV[s.net.lv - 1];
    ring.visible = aimLine.visible = !!a.active && !s.net.cast;
    if (ring.visible) {
      ring.position.set(a.x, 0.07, a.z); ring.scale.set(nl.r * 2, 1, nl.r * 2); ring.rotation.y = t * 0.6;
      setLine(aimLine, b.x, 0.5, b.z, a.x, 0.07, a.z);
    }
    // 網
    const cast = s.net.cast, useArt = art.ready && cast;
    net.visible = !!cast && !useArt; ropeLine.visible = !!cast; artMesh.visible = false;
    if (cast) {
      let y = 0.06 + Math.sin(t * 1.7) * 0.012, sc = nl.r * 2;
      if (cast.phase === 'fly') { const k = Math.min(1, cast.t); y = 0.7 + Math.sin(Math.PI * k) * 1.3 - k * 0.64; sc *= 0.35 + 0.65 * k; }
      else if (cast.phase === 'back') { y = 0.12; sc *= 0.85; }
      if (useArt) {
        let f, u;
        if (cast.phase === 'fly') { f = NA.fly[Math.min(3, Math.floor(Math.min(1, cast.t) * 4))]; u = 2 * nl.r / NA.flyDiscW; }
        else if (cast.phase === 'rest' && cast.t < 0.5) { f = NA.splash[Math.min(3, Math.floor(cast.t / 0.125))]; u = 2 * nl.r / NA.flyDiscW; }
        else { f = NA.idle[Math.floor(t * 5) % 4]; u = 2 * nl.r / NA.idleDiscW; if (cast.phase === 'back') u *= 0.85; }
        showArt(f, u, cast.x, y + 0.02, cast.z);
      } else { net.position.set(cast.x, y, cast.z); net.scale.set(sc, 1, sc); net.rotation.y = cast.phase === 'fly' ? t * 8 : 0; }
      setLine(ropeLine, b.x, 0.55, b.z, cast.x, y, cast.z);
    }
    while (held.length > (cast ? cast.held.length : 0)) group.remove(held.pop());
    if (cast) cast.held.forEach((k, i) => {
      if (!held[i] || held[i].userData.k !== k) { if (held[i]) group.remove(held[i]); held[i] = c.sprite(mk(k), { x: 0, y: 0, z: 0, ppu: 36 }); group.add(held[i]); held[i].userData.k = k; }
      const ang = i * 2.4, rr = Math.min(nl.r * 0.55, 0.15 + i * 0.1);
      held[i].position.set(cast.x + Math.cos(ang) * rr, net.position.y + 0.03 + Math.sin(t * 2 + i) * 0.015, cast.z + Math.sin(ang) * rr);
    });
  } };
};
