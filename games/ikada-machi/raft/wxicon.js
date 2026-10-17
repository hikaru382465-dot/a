// 日記の天気マーク：茶色いペンの手描き風の線画（コードで描く。ゆれ・二重線・斜線の影つき）
window.RAFT = window.RAFT || {};
window.RAFT.wxIcon = function (id) {
  const N = 128, cv = document.createElement('canvas'); cv.width = cv.height = N; const g = cv.getContext('2d');
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647, J = a => (rnd() - 0.5) * a;
  const INK = '#6b4a2a', PAPER = '#f1e2bd';
  g.lineCap = g.lineJoin = 'round';
  const pen = (pts, w = 3, close) => { g.strokeStyle = INK; for (let pass = 0; pass < 2; pass++) { g.lineWidth = pass ? w * 0.6 : w; g.globalAlpha = pass ? 0.55 : 1; g.beginPath(); pts.forEach((p, i) => { const x = p[0] + (pass ? J(1.6) : 0), y = p[1] + (pass ? J(1.6) : 0); i ? g.lineTo(x, y) : g.moveTo(x, y); }); if (close) g.closePath(); g.stroke(); } g.globalAlpha = 1; };
  const circ = (x, y, r, a0 = 0, a1 = 6.283, n = 28) => { const p = []; for (let i = 0; i <= n; i++) { const a = a0 + (a1 - a0) * i / n, rr = r * (1 + J(0.05)); p.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); } return p; };
  const hatch = (x0, y0, x1, y1, step, inside) => { g.strokeStyle = INK; g.lineWidth = 1.6; g.globalAlpha = 0.7; for (let d = -(y1 - y0); d < x1 - x0; d += step) { g.beginPath(); let started = false; for (let t = 0; t <= (y1 - y0); t += 2) { const x = x0 + d + t, y = y1 - t; if (x >= x0 && x <= x1 && inside(x, y)) { started ? g.lineTo(x, y) : g.moveTo(x, y); started = true; } else started = false; } g.stroke(); } g.globalAlpha = 1; };
  const sun = (cx, cy, r) => {
    const body = circ(cx, cy, r); g.fillStyle = PAPER; g.beginPath(); body.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.fill();
    hatch(cx - r, cy - r, cx + r, cy + r, 5, (x, y) => (x - cx) ** 2 + (y - cy) ** 2 < r * r * 0.9 && x - cx + (y - cy) > r * 0.1);
    pen(body, 3, true); pen(circ(cx, cy, r * 0.62, 0.4, 2.4, 10), 2);
    for (let k = 0; k < 12; k++) { const a = k * Math.PI / 6 + 0.1, long = k % 2 === 0, r0 = r + 6, r1 = r + (long ? 19 : 13); pen([[cx + Math.cos(a) * r0, cy + Math.sin(a) * r0], [cx + Math.cos(a + 0.05) * (r0 + r1) / 2, cy + Math.sin(a + 0.05) * (r0 + r1) / 2], [cx + Math.cos(a) * r1, cy + Math.sin(a) * r1]], 2.6); }
  };
  const cloud = (x, y, s, dark) => {      // 左下(x,y)から右へ。ふくらみ4つ
    const ring = []; const arcs = [[x + 14 * s, y + 0 * s, 15 * s, 1.55, 4.55], [x + 36 * s, y - 14 * s, 21 * s, 3.5, 6.1], [x + 62 * s, y - 10 * s, 19 * s, 3.9, 6.9], [x + 80 * s, y + 2 * s, 14 * s, 4.7, 7.9]];
    arcs.forEach(a => ring.push(...circ(a[0], a[1], a[2], a[3], a[4], 14)));
    ring.push([x + 80 * s, y + 16 * s], [x + 14 * s, y + 15 * s]);
    g.fillStyle = PAPER; g.beginPath(); ring.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.closePath(); g.fill();
    hatch(x - 5, y - 36 * s, x + 95 * s, y + 16 * s, dark ? 4 : 6, (px, py) => py > y - 2 * s && py < y + 15 * s && px > x + 6 * s && px < x + 78 * s);
    pen(ring, 3, true);
    pen([[x + 24 * s, y + 4 * s], [x + 30 * s, y - 2 * s], [x + 40 * s, y - 2 * s]], 2); pen([[x + 56 * s, y - 2 * s], [x + 64 * s, y - 6 * s]], 2);
  };
  const drop = (x, y, sc = 1) => { pen([[x, y - 7 * sc], [x - 4 * sc, y], [x - 3 * sc, y + 4 * sc], [x, y + 6 * sc], [x + 3 * sc, y + 4 * sc], [x + 4 * sc, y]], 2.4, true); };
  if (id === 'sunny') sun(64, 64, 24);
  else if (id === 'calm') { sun(82, 40, 17); cloud(14, 92, 0.85, false); }
  else { cloud(14, 62, 0.85, true); [[28, 88], [50, 94], [72, 88]].forEach(p => drop(p[0], p[1], 1.1)); pen([[78, 74], [64, 94], [74, 94], [60, 120]], 3.4); pen([[78, 74], [88, 76], [74, 94]], 2.2); }
  return cv.toDataURL();
};
