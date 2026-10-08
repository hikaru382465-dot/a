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
  const mk = (cv, ppu) => ({ cv, ppu });
  const art = { bench: [mk(bench(), 24)], tank: [0, 1, 2, 3].map(l => mk(tank(l), 24)), filter: [0, 1].map(f => mk(filter(f), 24)) };
  const group = new THREE.Group(); scene.add(group);
  const items = new Map(); let rev = -1, t = 0;
  function build() {
    while (group.children.length) group.remove(group.children[0]); items.clear();
    s.objects.forEach(o => {
      const a = art[o.k]; if (!a) return;
      const m = c.sprite(a[0].cv, { x: o.x + 0.5, y: TOP, z: o.z + 0.5, ppu: a[0].ppu }); group.add(m);
      const tex = a.map(f => c.tex(f.cv));
      items.set(o.id, { m, tex, o, last: -1 });
    });
    rev = s.objRev;
  }
  build();
  return { update(tt, dt) {
    if (s.objRev !== rev) build();
    t += dt;
    items.forEach(it => {
      let idx = 0;
      if (it.o.k === 'tank') idx = Math.min(3, Math.ceil(it.o.w / D.ITEMS.tank.cap * 3));
      else if (it.o.k === 'filter') idx = (it.o.p > 0 && Math.floor(t * 2) % 2) ? 1 : 0;
      if (idx !== it.last) { it.m.material.map = it.tex[idx]; it.last = idx; }
    });
  } };
};
