// イカダに置いた物の絵：作業台・貯水槽（水の量で変わる）・ろ過器（動く）。コードで描いた仮のドット絵
window.RAFT.parts.objects = function (c) {
  const { THREE, scene, state: s, I, R } = c, P = I.pal, D = R.data, OUT = P.line, TOP = 0.2;
  const outline = (cv, g) => {
    const W = cv.width, H = cv.height, d = g.getImageData(0, 0, W, H), o = new Uint8ClampedArray(d.data), on = (x, y) => x >= 0 && y >= 0 && x < W && y < H && d.data[(y * W + x) * 4 + 3] > 0;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (!on(x, y) && (on(x + 1, y) || on(x - 1, y) || on(x, y + 1) || on(x, y - 1))) { const k = (y * W + x) * 4; o[k] = 0x37; o[k + 1] = 1; o[k + 2] = 0x27; o[k + 3] = 255; }
    g.putImageData(new ImageData(o, W, H), 0, 0); return cv;
  };
  function bench() {
    const [cv, g] = I.canvas(22, 20), r = I.rng(3);
    I.rect(g, 2, 8, 18, 4, P.wood4); I.rect(g, 2, 8, 18, 1, P.wood5); I.rect(g, 2, 11, 18, 1, P.wood2);       // 天板
    I.rect(g, 3, 12, 2, 7, P.wood1); I.rect(g, 17, 12, 2, 7, P.wood1); I.rect(g, 4, 12, 1, 7, P.wood2);         // 脚
    I.rect(g, 5, 15, 12, 1, P.wood1);                                                                           // 横木
    I.rect(g, 5, 5, 6, 3, P.stone3); I.rect(g, 5, 5, 6, 1, '#d8d8cf'); I.rect(g, 11, 6, 5, 2, P.wood2); I.rect(g, 11, 6, 1, 2, P.wood4);  // 金づちとのこぎり
    I.rect(g, 14, 4, 3, 4, P.wood3); I.dot(g, 15, 5, P.wood5);                                                     // 木くず
    for (let i = 0; i < 6; i++) I.dot(g, 3 + Math.floor(r() * 16), 9 + Math.floor(r() * 2), P.wood3);
    return outline(cv, g);
  }
  function catchnet(state) {      // 回収ネット（仮の絵）：0＝空、1＝物入り、2＝やぶれ
    const [cv, g] = I.canvas(20, 22);
    I.rect(g, 2, 2, 2, 17, P.wood3); I.rect(g, 16, 2, 2, 17, P.wood3); I.rect(g, 2, 2, 2, 1, P.wood5); I.rect(g, 16, 2, 2, 1, P.wood5);      // 2本の柱
    I.rect(g, 2, 3, 16, 1, P.wood4);                                                                                                            // 上のわく
    for (let y = 5; y < 18; y += 3) I.rect(g, 4, y, 12, 1, P.wood5);                                                                            // あみ目（よこ）
    for (let x = 5; x < 16; x += 3) I.rect(g, x, 5, 1, 13, P.wood5);                                                                            // あみ目（たて）
    if (state === 1) { I.rect(g, 6, 14, 4, 3, P.wood3); I.rect(g, 6, 14, 4, 1, P.wood5); I.rect(g, 11, 15, 3, 2, P.red1); I.dot(g, 8, 12, P.wood2); }
    if (state === 2) { I.rect(g, 7, 8, 6, 5, '#00000000'); g.clearRect(7, 8, 6, 5); I.dot(g, 6, 9, P.wood5); I.dot(g, 13, 12, P.wood5); }
    return outline(cv, g);
  }
  function tank(level) {      // level 0..3
    const [cv, g] = I.canvas(18, 24);
    I.rect(g, 3, 5, 12, 17, P.wood2); I.rect(g, 2, 8, 14, 11, P.wood2);                     // たる
    for (let x = 4; x < 15; x += 3) I.rect(g, x, 6, 1, 15, P.wood3); I.rect(g, 12, 6, 3, 15, P.wood1);
    I.rect(g, 2, 9, 14, 1, P.stone3); I.rect(g, 2, 17, 14, 1, P.stone2);                    // 輪
    I.rect(g, 3, 3, 12, 3, P.wood4); I.rect(g, 4, 4, 10, 1, P.night1);                      // 口
    const lv = [0, 1, 2, 3][level];
    if (lv > 0) { I.rect(g, 4, 4, 10, 1, P.blue2); if (lv > 1) I.rect(g, 4, 3, 10, 1, P.blue3); }
    // 横の目盛り（水の高さ）
    I.rect(g, 15, 8, 2, 12, P.stone1); I.rect(g, 15, 20 - lv * 4, 2, lv * 4 || 1, lv ? P.blue3 : P.stone0);
    if (lv === 3) { I.dot(g, 6, 3, '#ffffff'); I.dot(g, 11, 4, '#ffffff'); }
    return outline(cv, g);
  }
  function filter(f) {       // f 0/1：しずくが動く
    const [cv, g] = I.canvas(18, 26);
    I.rect(g, 3, 14, 12, 10, P.wood2); I.rect(g, 3, 14, 12, 1, P.wood4); for (let x = 5; x < 14; x += 3) I.rect(g, x, 15, 1, 8, P.wood3);
    I.rect(g, 2, 17, 14, 1, P.stone3); I.rect(g, 2, 21, 14, 1, P.stone2);
    I.rect(g, 4, 4, 10, 10, P.cream); I.rect(g, 4, 4, 10, 1, '#fff6d8'); I.rect(g, 4, 13, 10, 1, '#cdb98f');          // 布
    for (let y = 6; y < 13; y += 3) I.rect(g, 4, y, 10, 1, P.red1);
    I.rect(g, 15, 18, 3, 2, P.stone2); I.rect(g, 17, 20, 1, 1, P.stone3);                                           // 管
    I.dot(g, 17, 21 + (f ? 2 : 0), P.blue3); if (f) I.dot(g, 17, 20, P.blue2);
    return outline(cv, g);
  }
  const mk = (cv, ppu, hi) => ({ cv, ppu, hi });
  const art = { catchnet: [0, 1, 2].map(st => mk(catchnet(st), 28)), bench: [mk(bench(), 24)], tank: [0, 1, 2, 3].map(l => mk(tank(l), 24)), filter: [0, 1].map(f => mk(filter(f), 24)) };
  // ひかるの絵（objs_art.js）。読み込めたら、コードで描いた仮の絵のかわりに使う
  const OA = R.objArt; let oaLeft = 0;
  const SH_OF = { catchnet: 0.7, campfire: 1.15, bench: 1.3, rack: 1.15, oven: 0.95, crate: 0.8, chest: 0.9, plot: 1.05, seat: 0.7, barrel: 0.8, bed: 1.15, shelf: 0.9, windmill: 0.9, hut: 1.5 };      // 足もとの影の大きさ（物ごと）
  const SHIFT_OF = { hut: 2.0 };
  const PPU_OF = { catchnet: 36, bench: 36, tank: 36, filter: 34, campfire: 44, seat: 36, rack: 42, oven: 38, crate: 36, chest: 36, plot: 36, barrel: 34, bed: 30, shelf: 34, windmill: 36, hut: 15.4 }, ART_KEYS = ['bench', 'tank', 'filter', 'campfire', 'seat', 'rack', 'oven', 'crate', 'chest', 'plot', 'barrel', 'bed', 'shelf', 'windmill', 'hut', 'catchnet'];
  if (OA) ART_KEYS.filter(k => OA[k]).forEach(k => { const arr = OA[k].map(f => { const [cv, g] = I.canvas(f.w, f.h); oaLeft++; const im = new Image(); im.onload = () => { g.drawImage(im, 0, 0); if (--oaLeft === 0) { ART_KEYS.filter(kk => OA[kk]).forEach(kk => { art[kk] = OA[kk].map((f2, i) => mk(OA.cv[kk][i], (PPU_OF[kk] || 34) * (f2.hi ? f2.hi : 1), !!f2.hi)); }); rev = -1; } }; im.src = f.src; return cv; }); (OA.cv = OA.cv || {})[k] = arr; });
  const glowTex = (() => { const [cv, g] = I.canvas(64, 64), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,190,100,1)'); gr.addColorStop(.4, 'rgba(255,130,50,.4)'); gr.addColorStop(1, 'rgba(255,100,30,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return c.tex(cv); })();
  const shGeo = new THREE.PlaneGeometry(0.85, 0.85); shGeo.rotateX(-Math.PI / 2);
  const shTex = (() => { const [cv, g] = I.canvas(32, 32), gr = g.createRadialGradient(16, 16, 2, 16, 16, 16); gr.addColorStop(0, 'rgba(18,10,28,.55)'); gr.addColorStop(.7, 'rgba(18,10,28,.35)'); gr.addColorStop(1, 'rgba(18,10,28,0)'); g.fillStyle = gr; g.fillRect(0, 0, 32, 32); const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; return t; })();
  const shMat = new THREE.MeshBasicMaterial({ map: shTex, transparent: true, depthWrite: false });
  const group = new THREE.Group(); scene.add(group);
  const items = new Map(); let rev = -1, t = 0;
  function build() {
    while (group.children.length) group.remove(group.children[0]); items.clear();
    s.objects.forEach(o => {
      let a = art[o.k]; if (!a) return;
      if (o.k === 'catchnet') a = a.map(f => ({ cv: subCv(f.cv), ppu: f.ppu, hi: f.hi }));      // 回収ネット：下がわを海にひたす（水にぬれた色にする）
      const [fw, fd] = R.sim.sizeOf(o), cx = o.x + fw / 2, cz = o.z + fd / 2;
      const sf = (SHIFT_OF[o.k] || 0) * 0.7071;      // 台つきの絵は、カメラのほうへずらして、台の中心を床の中心に合わせる（浮いて見えないように）
      const base = o.k === 'hut' && a.length > 2 * (o.hv || 0) ? 2 * (o.hv || 0) : 0;      // 小屋の見た目ちがい：[昼0, 夜0, 昼1, 夜1, …]
      const m = c.sprite(a[base].cv, { x: cx + sf, y: TOP, z: cz + sf, ppu: a[base].ppu, smooth: a[base].hi }); group.add(m);
      const tex = a.map(f => c.tex(f.cv, { smooth: f.hi }));
      const sh = new THREE.Mesh(shGeo, shMat); sh.position.set(cx, TOP + 0.004, cz); sh.rotation.y = Math.PI / 4; sh.scale.setScalar((SH_OF[o.k] || 0.9) * (fw > 1 || fd > 1 ? 2.2 : 1)); group.add(sh);     // 足もとの影（浮いて見えないように）
      if (o.k === 'campfire') m.position.y -= 0.07;
      if (o.k === 'catchnet') { const dir = [[0, 1], [1, 0], [-1, 0], [0, -1]].find(([dx, dz]) => !R.sim.has(s, o.x + dx, o.z + dz)) || [0, 0], front = dir[0] + dir[1] > 0; const h = m.scale.y;      // 手前（カメラに近い辺）をえらぶ。奥の辺は、イカダのかげに入るので、あまりしずめない      // 海に面した辺の外へ出して、下の4割を、水の中に入れる
        m.position.x = cx + dir[0] * 0.62; m.position.z = cz + dir[1] * 0.62; m.position.y = front ? 0.045 - 0.4 * h : 0.12 - 0.12 * h; sh.visible = false; }
      const it = { m, tex, o, last: -1, base };
      if (o.k === 'campfire') { const gm = new THREE.MeshBasicMaterial({ map: glowTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.2 }); const gp = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 2.2), gm); gp.rotation.y = c.cam.yaw; gp.position.set(o.x + 0.5, TOP + 0.35, o.z + 0.5); group.add(gp); it.gm = gm; }
      items.set(o.id, it);
    });
    rev = s.objRev;
  }
  // ネットにたまった数のバッジ（数が変わったときだけ描きなおす）
  const subCache = new Map();
  function subCv(cv) {      // 下の約4割を、うすい水色にかさねて、すこし透かす（水にひたった見た目）
    let r = subCache.get(cv); if (r) return r; const [o, g] = I.canvas(cv.width, cv.height), W = cv.width, H = cv.height, y0 = Math.floor(H * 0.6);
    g.drawImage(cv, 0, 0); g.globalCompositeOperation = 'source-atop'; const gr = g.createLinearGradient(0, y0, 0, H); gr.addColorStop(0, 'rgba(40,130,190,0.25)'); gr.addColorStop(1, 'rgba(25,95,160,0.62)'); g.fillStyle = gr; g.fillRect(0, y0, W, H - y0);
    g.globalCompositeOperation = 'destination-out'; const ga = g.createLinearGradient(0, y0, 0, H); ga.addColorStop(0, 'rgba(0,0,0,0)'); ga.addColorStop(1, 'rgba(0,0,0,0.38)'); g.fillStyle = ga; g.fillRect(0, y0, W, H - y0);
    g.globalCompositeOperation = 'source-over'; g.strokeStyle = 'rgba(235,250,255,0.75)'; g.lineWidth = Math.max(1, H / 70); g.beginPath(); g.ellipse(W / 2, y0, W * 0.4, H * 0.035, 0, 0, 6.3); g.stroke();      // 水面のふち（あわ）
    r = o; subCache.set(cv, r); return r;
  }
  function badge(it, n) {
    if (!it.bd) { const [cv, g] = I.canvas(24, 14); it.bdcv = cv; it.bdg = g; const tx = c.tex(cv); const m = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.3), new THREE.MeshBasicMaterial({ map: tx, transparent: true, depthTest: false })); m.rotation.y = c.cam.yaw; m.renderOrder = 5; m.position.set(it.m.position.x, it.m.position.y + 0.9, it.m.position.z); group.add(m); it.bd = m; it.bdtx = tx; }
    const g = it.bdg; g.clearRect(0, 0, 24, 14); if (n > 0) { g.fillStyle = '#2b1636'; g.fillRect(2, 1, 20, 12); g.fillStyle = '#ffd88a'; g.font = 'bold 11px sans-serif'; g.textAlign = 'center'; g.fillText(String(n), 12, 11); } it.bdtx.needsUpdate = true; it.bd.visible = n > 0;
  }
  build();
  // 見えている絵を、直接おせるようにする：画面の点（px）にある物を、手前から順に返す。exact＝その点の絵が不透明、near＝まわり14px以内に不透明
  const px = new Map();      // canvas → 透明度の配列（はじめに1回だけ読む）
  const alphaOf = cv => { let a = px.get(cv); if (!a) { try { a = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data; } catch (e) { a = null; } px.set(cv, a || false); } return a; };
  c.pickObjs = function (sx, sy) {
    const rc = c.renderer.domElement.getBoundingClientRect(), W = rc.width, H = rc.height, V = new THREE.Vector3(), out = [];
    const scr = (x, y, z) => { V.set(x, y, z).project(c.camera); return [rc.left + (V.x + 1) / 2 * W, rc.top + (1 - V.y) / 2 * H, V.z]; };
    const rx = Math.cos(c.cam.yaw), rz = -Math.sin(c.cam.yaw);
    items.forEach(it => {
      const m = it.m, a = art[it.o.k]; if (!a) return; const fr = a[Math.max(0, it.last)] || a[0]; if (!fr || !fr.cv) return; const al = alphaOf(fr.cv); if (!al) return;
      const p = m.position, sw = m.scale.x, sh = m.scale.y, P0 = scr(p.x, p.y, p.z), PX = scr(p.x + rx * sw, p.y, p.z + rz * sw), PY = scr(p.x, p.y + sh, p.z);
      const ax = PX[0] - P0[0], ay = PX[1] - P0[1], bx = PY[0] - P0[0], by = PY[1] - P0[1], det = ax * by - ay * bx; if (Math.abs(det) < 1e-6) return;
      const hit = (qx, qy) => { const dx = qx - P0[0], dy = qy - P0[1], u = (dx * by - dy * bx) / det, v = (ax * dy - ay * dx) / det; if (u < -0.5 || u > 0.5 || v < 0 || v > 1) return false;
        const ix = Math.min(fr.cv.width - 1, Math.floor((u + 0.5) * fr.cv.width)), iy = Math.min(fr.cv.height - 1, Math.floor((1 - v) * fr.cv.height)); return al[(iy * fr.cv.width + ix) * 4 + 3] > 40; };
      const exact = hit(sx, sy); let near = exact; if (!near) for (const [ox, oy] of [[14, 0], [-14, 0], [0, 14], [0, -14], [10, 10], [-10, 10], [10, -10], [-10, -10]]) if (hit(sx + ox, sy + oy)) { near = true; break; }
      if (near) out.push({ o: it.o, exact, depth: P0[2] });
    });
    out.sort((p, q) => (q.exact - p.exact) || (p.depth - q.depth)); return out;      // 点がまともに当たった物（手前）が先、つぎに近い物
  };
  return { update(tt, dt) {
    if (s.objRev !== rev || rev === -1) build();
    t += dt;
    items.forEach(it => {
      if (it.gm) it.gm.opacity = (it.o.burn ? 0.5 : 0.1) + Math.sin(t * 9 + it.o.id) * 0.06 + Math.sin(t * 5.3) * 0.04;
      let idx = 0;
      if (it.o.k === 'tank') idx = Math.min(3, Math.ceil(it.o.w / D.ITEMS.tank.cap * 3));
      else if (it.o.k === 'filter') idx = (it.o.p > 0 && Math.floor(t * 2) % 2) ? 1 : 0;
      else if (it.o.k === 'catchnet') { idx = !(it.o.dur > 0) ? 2 : R.sim.cnTotal(it.o) > 0 ? 1 : 0; const n = R.sim.cnTotal(it.o); if (n !== it.lastN) { it.lastN = n; badge(it, n); } }
      else if (it.o.k === 'hut') idx = it.base + ((s.clock.t >= 0.72 || s.clock.t < 0.2) && it.tex.length > it.base + 1 ? 1 : 0);
      else if (it.o.k === 'plot') { const cr = it.o.c && D.CROPS[it.o.c]; if (cr) { const f = it.o.p / cr.sec; idx = f >= 1 ? 4 + Math.max(0, (R.cropIds || []).indexOf(it.o.c)) : f < 0.12 ? 1 : f < 0.4 ? 2 : 3; } }
      if (idx !== it.last) { it.m.material.map = it.tex[idx]; it.last = idx; }
    });
  } };
};
