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
    floor(g) { I.rect(g, 1, 3, 10, 6, P.wood3); I.rect(g, 1, 3, 10, 1, P.wood4); I.rect(g, 1, 8, 10, 1, P.wood1); I.rect(g, 1, 5, 10, 1, P.wood2); I.rect(g, 1, 3, 2, 6, P.wood5); },
    bench(g) { I.rect(g, 1, 3, 10, 3, P.wood4); I.rect(g, 1, 3, 10, 1, P.wood5); I.rect(g, 2, 6, 2, 5, P.wood1); I.rect(g, 8, 6, 2, 5, P.wood1); I.rect(g, 3, 1, 3, 2, P.stone3); },
    tank(g) { I.rect(g, 2, 2, 8, 9, P.wood2); I.rect(g, 3, 2, 6, 1, P.blue2); I.rect(g, 2, 5, 8, 1, P.stone3); I.rect(g, 2, 8, 8, 1, P.stone2); I.rect(g, 7, 3, 2, 8, P.wood1); },
    filter(g) { I.rect(g, 2, 6, 8, 5, P.wood2); I.rect(g, 3, 1, 6, 5, P.cream); I.rect(g, 3, 3, 6, 1, P.red1); I.rect(g, 10, 8, 2, 1, P.stone2); I.dot(g, 11, 10, P.blue3); },
    bag(g) { I.rect(g, 3, 4, 6, 7, P.wood2); I.rect(g, 2, 5, 8, 5, P.wood2); I.rect(g, 3, 2, 6, 3, P.wood3); I.rect(g, 4, 3, 4, 1, P.wood1); I.rect(g, 4, 7, 4, 2, P.wood4); I.rect(g, 3, 5, 6, 1, P.wood1); },
    hammer(g) { I.rect(g, 2, 2, 7, 3, P.stone3); I.rect(g, 2, 2, 7, 1, '#d8d8cf'); I.rect(g, 8, 3, 2, 2, P.stone1); I.rect(g, 5, 5, 2, 6, P.wood3); I.rect(g, 5, 5, 1, 6, P.wood4); },
    glass(g) { I.rect(g, 3, 3, 6, 7, '#8fc3bd'); I.rect(g, 4, 4, 2, 3, '#e6f6f2'); I.rect(g, 3, 9, 6, 1, '#46909c'); }
  };
  const icon = k => { const [cv, g] = I.canvas(12, 12); draw[k] && draw[k](g);
    const d = g.getImageData(0, 0, 12, 12), o = new Uint8ClampedArray(d.data), on = (x, y) => x >= 0 && y >= 0 && x < 12 && y < 12 && d.data[(y * 12 + x) * 4 + 3] > 0;
    for (let y = 0; y < 12; y++) for (let x = 0; x < 12; x++) if (!on(x, y) && (on(x + 1, y) || on(x - 1, y) || on(x, y + 1) || on(x, y - 1))) { const i = (y * 12 + x) * 4; o[i] = 0x37; o[i + 1] = 1; o[i + 2] = 0x27; o[i + 3] = 255; }
    g.putImageData(new ImageData(o, 12, 12), 0, 0); return cv; };
  // ひかるの漂流物の絵（items.js）。読み込めるまでは、プログラムで描いた小さい絵を使う
  const IA = R.itemArt, OAr = R.objArt, artCv = {}, cache = {};
  const load = (k, list) => { artCv[k] = list.map(f => { const [cv, g] = I.canvas(f.w, f.h); cv.ok = false; cv.ppu = f.ppu || 90; cv.tip = f.tip; const im = new Image(); im.onload = () => { g.drawImage(im, 0, 0); cv.ok = true; }; im.src = f.src; return cv; }); };
  if (IA) for (const k in IA.art) load(k, IA.art[k]);
  if (OAr) { for (const k in OAr.icons) load(k, OAr.icons[k]); load('bench', OAr.bench); load('tank', [OAr.tank[3]]); load('filter', [OAr.filter[0]]); }   // 新しい絵で、前のをおきかえる
  const artOf = (k, v) => { const a = artCv[k]; if (!a) return null; const cv = a[(v || 0) % a.length]; return cv.ok ? cv : null; };
  const mk = (k, v) => artOf(k, v) || cache[k] || (cache[k] = icon(k));
  c.itemIcon = k => mk(k, 0);
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
    let left = 0; const all = [].concat(NA.fly, NA.splash, NA.idle, NA.haul);
    all.forEach(f => { left++; const im = new Image(); im.onload = () => { const tx = new THREE.Texture(im); tx.colorSpace = THREE.SRGBColorSpace; tx.magFilter = tx.minFilter = THREE.NearestFilter; tx.generateMipmaps = false; tx.needsUpdate = true; f.tex = tx; if (--left === 0) art.ready = true; }; im.src = f.src; });
  }
  const camRight = new THREE.Vector3(Math.cos(c.cam.yaw), 0, -Math.sin(c.cam.yaw));
  function showArt(f, u, x, y, z) {
    artM.map = f.tex; artM.needsUpdate = true;
    artMesh.scale.set(f.w * u, f.h * u / Math.cos(c.cam.pitch), 1);
    const dx = (f.ax - f.w / 2) * u, dy = (f.ay - f.h / 2) * u / Math.cos(c.cam.pitch);
    artMesh.position.set(x - camRight.x * dx, y + dy, z - camRight.z * dx);
    artMesh.visible = true;
  }
  // 釣りのウキと糸
  const bobCv = (() => { const [cv, g] = I.canvas(5, 7); I.rect(g, 1, 0, 3, 3, P.red1); I.rect(g, 1, 3, 3, 2, P.cream); I.rect(g, 2, 5, 1, 2, P.night1); return cv; })();
  const bob = c.sprite(bobCv, { x: 0, y: 0, z: 0, ppu: 40 }); bob.visible = false; group.add(bob);
  const lineRod = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3(1, 0, 0)]), new THREE.LineBasicMaterial({ color: 0xf1ead8 })); lineRod.visible = false; scene.add(lineRod);
  // 釣りの動き：ざおをふる／ひいたら「！」／釣れた物がとんでくる／水しぶき
  const bangCv = (() => { const [cv, g] = I.canvas(7, 13); I.rect(g, 0, 0, 7, 13, '#fff1e0'); I.rect(g, 1, 1, 5, 7, '#ff2020'); I.rect(g, 1, 10, 5, 2, '#ff2020'); return cv; })();
  const bang = c.sprite(bangCv, { x: 0, y: 0, z: 0, ppu: 50 }); bang.visible = false; group.add(bang);
  let bobY = 0, rodM = null, rodB = null, rodTip = null, fxLast = s.reelFx ? s.reelFx.id : 0, flyFx = null, wasRod = null, castT = 9, reelT = 9;
  const splashRing = new THREE.Mesh(flat, new THREE.MeshBasicMaterial({ map: ringTex, transparent: true, depthWrite: false, color: new THREE.Color(1.3, 1.5, 1.7) })); splashRing.visible = false; scene.add(splashRing);
  const beatM = new THREE.MeshBasicMaterial({ map: ringTex, transparent: true, depthWrite: false, depthTest: false, color: new THREE.Color(2, 0.5, 0.4) });
  const beat = new THREE.Mesh(flat, beatM); beat.visible = false; beat.renderOrder = 4; scene.add(beat);
  const beatT = new THREE.Mesh(flat, new THREE.MeshBasicMaterial({ map: ringTex, transparent: true, depthWrite: false, depthTest: false, color: new THREE.Color(2, 2, 2) })); beatT.visible = false; beatT.renderOrder = 4; beatT.scale.set(0.5, 1, 0.5); scene.add(beatT);
  let splashT = 9, splashAt = [0, 0];
  const held = [];
  let t = 0;
  c.aim = c.aim || { active: false, x: 0, z: 0, power: 0 };
  return { update(tt, dt) {
    t += dt;
    const live = new Set();
    s.drift.forEach(it => {
      live.add(it.id);
      let m = meshes.get(it.id);
      if (!m) { const ac = artOf(it.k, it.id); m = c.sprite(ac || mk(it.k), { x: it.x, y: 0.05, z: it.z, ppu: ac ? ac.ppu : 30 }); group.add(m); meshes.set(it.id, m); m.userData.s = m.scale.clone(); const rm = ringM.clone(); rm.opacity = 0; const rg = new THREE.Mesh(flat, rm); scene.add(rg); m.userData.rg = rg; }
      const ph = t * 2.4 + it.id, hop = Math.sin(ph);
      m.position.set(it.x, -0.07 + hop * 0.06, it.z);   // 下半分は水の中にしずむ m.rotation.z = Math.sin(ph * 0.7) * 0.12;
      const rg = m.userData.rg, rk = ((ph / 6.283 + 0.75) % 1);    // さざ波が、広がって消える（ときどき小さなしぶき）
      rg.position.set(it.x, 0.06, it.z); rg.scale.set(0.25 + rk * 0.7, 1, 0.25 + rk * 0.7); rg.material.opacity = (1 - rk) * 0.7 * Math.min(1, it.born * 2); rg.material.color.set(0xd8f4ff);
      m.scale.copy(m.userData.s).multiplyScalar(Math.min(1, it.born * 2) * 0.9);
    });
    for (const [id, m] of meshes) if (!live.has(id)) { scene.remove(m.userData.rg); group.remove(m); meshes.delete(id); }
    // ねらい（押している間、ゲージの強さで落ちる場所が動く）
    const a = c.aim, b = s.player, nl = R.data.NET_LV[s.net.lv - 1];
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
        else { f = NA.idle[Math.floor(t * (cast.phase === 'back' ? 10 : 5)) % 4]; u = 2 * nl.r / NA.idleDiscW; if (cast.phase === 'back') u *= 0.92; }
        showArt(f, u, cast.x, y + 0.02, cast.z);
      } else { net.position.set(cast.x, y, cast.z); net.scale.set(sc, 1, sc); net.rotation.y = cast.phase === 'fly' ? t * 8 : 0; }
      setLine(ropeLine, b.x, 0.55, b.z, cast.x, y, cast.z);
    }
    const rd = s.rod; bob.visible = lineRod.visible = !!rd;
    if (rd) {
      const dip = rd.phase === 'bite' ? -0.1 - Math.abs(Math.sin(t * 20)) * 0.05 : Math.sin(t * 2.4) * 0.02;
      bob.position.set(rd.x, 0.08 + dip, rd.z);
      bobY = 0.12 + dip;
    }
    // ざお（手にもっている間）
    if (!rodM && artOf('rod', 0) && artOf('rodBody', 0)) {
      const mkr = k => { const cv = artOf(k, 0), m = c.sprite(cv, { x: 0, y: 0, z: 0, ppu: cv.ppu }); m.rotation.order = 'YXZ'; m.rotation.y = c.cam.yaw; m.visible = false; group.add(m); return m; };
      rodM = mkr('rod'); rodB = mkr('rodBody');
    }
    if (rodM) {
      rodM.visible = s.hand === 'rod' && !rd; rodB.visible = s.hand === 'rod' && !!rd;
      if (rd && !wasRod) { castT = 0; splashT = 0; splashAt = [rd.x, rd.z]; }
      if (!rd && wasRod) { reelT = 0; splashT = 0; splashAt = [wasRod.x, wasRod.z]; }
      wasRod = rd ? { x: rd.x, z: rd.z } : null; castT += dt; reelT += dt;
      let ang = -0.1;                                                 // 立てた角度（絵がもともと右にかたむいているので、ほぼ0）
      if (castT < 0.45) ang = -0.1 + Math.sin(Math.min(1, castT / 0.45) * Math.PI) * 1.2 - (castT / 0.45) * 0.5;   // 後ろにふりかぶって、前へ投げる
      else if (reelT < 0.5) ang = -0.1 + Math.sin(Math.min(1, reelT / 0.5) * Math.PI) * 0.9;                      // 引き上げる
      else if (rd) ang = -0.25 + (rd.phase === 'bite' ? Math.sin(t * 40) * 0.14 : Math.sin(t * 1.5) * 0.03);
      rodM.rotation.z = rodB.rotation.z = -ang; rodM.position.set(b.x + 0.4, 0.4, b.z - 0.05); rodB.position.copy(rodM.position);
      rodTip = null;
      if (rodB.visible) {      // 糸は、ざおの先から出す
        const cv = artOf('rodBody', 0), pc = Math.cos(c.cam.pitch), lx = (cv.tip[0] - cv.width / 2) / cv.ppu, ly = (cv.height - cv.tip[1]) / cv.ppu / pc, rz = -ang;
        const px = lx * Math.cos(rz) - ly * Math.sin(rz), py = lx * Math.sin(rz) + ly * Math.cos(rz);
        rodTip = [rodB.position.x + camRight.x * px, rodB.position.y + py, rodB.position.z + camRight.z * px];
      }
    }
    if (rd) { const tp = rodTip || [b.x, 0.7, b.z]; setLine(lineRod, tp[0], tp[1], tp[2], rd.x, bobY, rd.z); }
    beat.visible = beatT.visible = !!rd && rd.phase === 'bite';
    if (beat.visible) { const k = rd.t / R.data.ROD.bite; beat.position.set(rd.x, 0.1, rd.z); beatT.position.set(rd.x, 0.1, rd.z); const sc = 0.5 + Math.max(0, R.data.ROD.great[0] - k) * 3.2 + Math.max(0, k - R.data.ROD.great[0]) * 1.2; beat.scale.set(sc, 1, sc); }
    bang.visible = !!rd && rd.phase === 'bite'; if (bang.visible) bang.material.depthTest = false; bang.renderOrder = 5; bang.position.set(b.x, 1.4 + Math.abs(Math.sin(t * 12)) * 0.08, b.z);
    splashT += dt; splashRing.visible = splashT < 0.7;
    if (splashRing.visible) { const k = splashT / 0.7; splashRing.position.set(splashAt[0], 0.07, splashAt[1]); splashRing.scale.set(0.2 + k * 1.1, 1, 0.2 + k * 1.1); splashRing.material.opacity = 1 - k; }
    // 釣れた物が、水面からとんでくる
    if (s.reelFx && s.reelFx.id !== fxLast) {
      fxLast = s.reelFx.id; const fk = s.reelFx.k;
      if (fk) { const ac = artOf(fk, 0); flyFx = { m: c.sprite(ac || mk(fk), { x: 0, y: 0, z: 0, ppu: ac ? ac.ppu : 30 }), x: s.reelFx.x, z: s.reelFx.z, t: 0 }; group.add(flyFx.m); }
    }
    if (flyFx) {
      flyFx.t += dt / 0.6; const k = Math.min(1, flyFx.t);
      flyFx.m.position.set(flyFx.x + (b.x - flyFx.x) * k, 0.1 + Math.sin(Math.PI * k) * 1.1 + (0.5 * k), flyFx.z + (b.z - flyFx.z) * k);
      if (k >= 1) { group.remove(flyFx.m); flyFx = null; }
    }
    const showHeld = !!cast;
    while (held.length > (showHeld ? cast.held.length : 0)) group.remove(held.pop());
    if (showHeld) cast.held.forEach((k, i) => {
      if (!held[i] || held[i].userData.k !== k) { if (held[i]) group.remove(held[i]); const ac = artOf(k, 0); held[i] = c.sprite(ac || mk(k), { x: 0, y: 0, z: 0, ppu: ac ? ac.ppu * 1.2 : 36 }); group.add(held[i]); held[i].userData.k = k; }
      const ang = i * 2.4, rr = Math.min(nl.r * 0.55, 0.15 + i * 0.1);
      held[i].position.set(cast.x + Math.cos(ang) * rr, net.position.y + 0.03 + Math.sin(t * 2 + i) * 0.015, cast.z + Math.sin(ang) * rr);
    });
  } };
};
