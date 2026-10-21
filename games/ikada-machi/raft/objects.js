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
  const art = { bench: [mk(bench(), 24)], tank: [0, 1, 2, 3].map(l => mk(tank(l), 24)), filter: [0, 1].map(f => mk(filter(f), 24)) };
  // ひかるの絵（objs_art.js）。読み込めたら、コードで描いた仮の絵のかわりに使う
  const OA = R.objArt; let oaLeft = 0;
  const SH_OF = { campfire: 1.15, bench: 1.3, rack: 1.15, oven: 0.95, crate: 0.8, chest: 0.9, plot: 1.05, seat: 0.7, barrel: 0.8, bed: 1.15, shelf: 0.9, windmill: 0.9, hut: 1.5 };      // 足もとの影の大きさ（物ごと）
  const SHIFT_OF = { hut: 2.0 };
  const PPU_OF = { bench: 36, tank: 36, filter: 34, campfire: 44, seat: 36, rack: 42, oven: 38, crate: 36, chest: 36, plot: 36, barrel: 34, bed: 30, shelf: 34, windmill: 36, hut: 15.4 }, ART_KEYS = ['bench', 'tank', 'filter', 'campfire', 'seat', 'rack', 'oven', 'crate', 'chest', 'plot', 'barrel', 'bed', 'shelf', 'windmill', 'hut'];
  if (OA) ART_KEYS.forEach(k => { const arr = OA[k].map(f => { const [cv, g] = I.canvas(f.w, f.h); oaLeft++; const im = new Image(); im.onload = () => { g.drawImage(im, 0, 0); if (--oaLeft === 0) { ART_KEYS.forEach(kk => { art[kk] = OA[kk].map((f2, i) => mk(OA.cv[kk][i], (PPU_OF[kk] || 34) * (f2.hi ? f2.hi : 1), !!f2.hi)); }); rev = -1; } }; im.src = f.src; return cv; }); (OA.cv = OA.cv || {})[k] = arr; });
  const glowTex = (() => { const [cv, g] = I.canvas(64, 64), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,190,100,1)'); gr.addColorStop(.4, 'rgba(255,130,50,.4)'); gr.addColorStop(1, 'rgba(255,100,30,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return c.tex(cv); })();
  const shGeo = new THREE.PlaneGeometry(0.85, 0.85); shGeo.rotateX(-Math.PI / 2);
  const shTex = (() => { const [cv, g] = I.canvas(32, 32), gr = g.createRadialGradient(16, 16, 2, 16, 16, 16); gr.addColorStop(0, 'rgba(18,10,28,.55)'); gr.addColorStop(.7, 'rgba(18,10,28,.35)'); gr.addColorStop(1, 'rgba(18,10,28,0)'); g.fillStyle = gr; g.fillRect(0, 0, 32, 32); const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; return t; })();
  const shMat = new THREE.MeshBasicMaterial({ map: shTex, transparent: true, depthWrite: false });
  const group = new THREE.Group(); scene.add(group);
  const items = new Map(); let rev = -1, t = 0;
  function build() {
    while (group.children.length) group.remove(group.children[0]); items.clear();
    s.objects.forEach(o => {
      const a = art[o.k]; if (!a) return;
      const [fw, fd] = R.sim.sizeOf(o), cx = o.x + fw / 2, cz = o.z + fd / 2;
      const sf = (SHIFT_OF[o.k] || 0) * 0.7071;      // 台つきの絵は、カメラのほうへずらして、台の中心を床の中心に合わせる（浮いて見えないように）
      const base = o.k === 'hut' && a.length > 2 * (o.hv || 0) ? 2 * (o.hv || 0) : 0;      // 小屋の見た目ちがい：[昼0, 夜0, 昼1, 夜1, …]
      const m = c.sprite(a[base].cv, { x: cx + sf, y: TOP, z: cz + sf, ppu: a[base].ppu, smooth: a[base].hi }); group.add(m);
      const tex = a.map(f => c.tex(f.cv, { smooth: f.hi }));
      const sh = new THREE.Mesh(shGeo, shMat); sh.position.set(cx, TOP + 0.004, cz); sh.rotation.y = Math.PI / 4; sh.scale.setScalar((SH_OF[o.k] || 0.9) * (fw > 1 || fd > 1 ? 2.2 : 1)); group.add(sh);     // 足もとの影（浮いて見えないように）
      if (o.k === 'campfire') m.position.y -= 0.07;
      const it = { m, tex, o, last: -1, base };
      if (o.k === 'campfire') { const gm = new THREE.MeshBasicMaterial({ map: glowTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.2 }); const gp = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 2.2), gm); gp.rotation.y = c.cam.yaw; gp.position.set(o.x + 0.5, TOP + 0.35, o.z + 0.5); group.add(gp); it.gm = gm; }
      items.set(o.id, it);
    });
    rev = s.objRev;
  }
  build();
  return { update(tt, dt) {
    if (s.objRev !== rev || rev === -1) build();
    t += dt;
    items.forEach(it => {
      if (it.gm) it.gm.opacity = (it.o.burn ? 0.5 : 0.1) + Math.sin(t * 9 + it.o.id) * 0.06 + Math.sin(t * 5.3) * 0.04;
      let idx = 0;
      if (it.o.k === 'tank') idx = Math.min(3, Math.ceil(it.o.w / D.ITEMS.tank.cap * 3));
      else if (it.o.k === 'filter') idx = (it.o.p > 0 && Math.floor(t * 2) % 2) ? 1 : 0;
      else if (it.o.k === 'hut') idx = it.base + ((s.clock.t >= 0.72 || s.clock.t < 0.2) && it.tex.length > it.base + 1 ? 1 : 0);
      else if (it.o.k === 'plot') { const cr = it.o.c && D.CROPS[it.o.c]; if (cr) { const f = it.o.p / cr.sec; idx = f >= 1 ? 4 + Math.max(0, (R.cropIds || []).indexOf(it.o.c)) : f < 0.12 ? 1 : f < 0.4 ? 2 : 3; } }
      if (idx !== it.last) { it.m.material.map = it.tex[idx]; it.last = idx; }
    });
  } };
};
