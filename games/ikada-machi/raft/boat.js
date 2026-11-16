// 船の住人の船：夕方に来て、イカダのそばにとまる。タップで交渉の画面（hud.js の openBoat）
window.RAFT.parts.boat = function (c) {
  const { THREE, scene, state: s, I, R } = c, OA = R.objArt;
  let m = null, cv = null, t = 0;
  if (OA && OA.icons && OA.icons.boat) { const f = OA.icons.boat[0], [cvs, g] = I.canvas(f.w, f.h), im = new Image(); im.onload = () => { g.drawImage(im, 0, 0); cv = cvs; }; im.src = f.src; }
  const flag = (() => { const [cvf, g] = I.canvas(3, 4); I.rect(g, 0, 0, 3, 3, '#e0503c'); I.rect(g, 0, 3, 1, 1, '#4a2c20'); return cvf; })();
  const ppu = 52, D = R.data, BW = 190, Q = 3;
  // 船の上のふきだし：まだ終わっていない取引の、「ほしい物（いま持っている数/ひつような数）→もらえる物」を出す
  let bub = null, bcv = null, bg = null, btx = null, bkey = '';
  const drawBubble = (b, deals) => {
    const rowH = 34, H = 14 + deals.length * rowH + 10; if (!bcv) { [bcv, bg] = I.canvas(BW * Q, 120 * Q); btx = new THREE.CanvasTexture(bcv); btx.colorSpace = THREE.SRGBColorSpace; btx.minFilter = btx.magFilter = THREE.LinearFilter; btx.generateMipmaps = false; }      // 文字が、ぼやけないように、3倍の細かさで描く
    bg.setTransform(Q, 0, 0, Q, 0, 0); bg.clearRect(0, 0, BW, 120); bg.imageSmoothingEnabled = false; bg.translate(0, 120 - H - 2);      // 下ぞろえ（しっぽの先が、キャンバスの下）
    const x0 = 2, y0 = 2, w = BW - 4, h = H - 12; bg.fillStyle = '#fff8e6'; bg.strokeStyle = '#3a2216'; bg.lineWidth = 2;
    bg.beginPath(); bg.roundRect ? bg.roundRect(x0, y0, w, h, 8) : bg.rect(x0, y0, w, h); bg.fill(); bg.stroke();
    bg.fillStyle = '#fff8e6'; bg.beginPath(); bg.moveTo(BW / 2 - 7, y0 + h - 1); bg.lineTo(BW / 2, y0 + h + 9); bg.lineTo(BW / 2 + 7, y0 + h - 1); bg.fill(); bg.strokeStyle = '#3a2216'; bg.beginPath(); bg.moveTo(BW / 2 - 7, y0 + h); bg.lineTo(BW / 2, y0 + h + 9); bg.lineTo(BW / 2 + 7, y0 + h); bg.stroke();
    bg.font = 'bold 13px "DotGothic16", sans-serif'; bg.textBaseline = 'middle';
    const icon = (k, x, y, sz) => { const ic = c.itemIcon(k); if (ic) { const sc = Math.min(sz / ic.width, sz / ic.height); bg.drawImage(ic, x + (sz - ic.width * sc) / 2, y + (sz - ic.height * sc) / 2, ic.width * sc, ic.height * sc); } };
    deals.forEach((d, i) => {
      let x = 10; const cy = y0 + 8 + i * rowH + 14;
      Object.keys(d.want).forEach(k => { icon(k, x, cy - 13, 26); const have = (s.inv[k] || 0), ok = have >= d.want[k]; bg.fillStyle = ok ? '#2f7a3a' : '#b0402f'; bg.textAlign = 'left'; bg.fillText(have + '/' + d.want[k], x + 28, cy); x += 28 + 36; });
      bg.fillStyle = '#3a2216'; bg.textAlign = 'center'; bg.fillText('→', x + 6, cy); x += 18;
      Object.keys(d.give).forEach(k => { icon(k, x, cy - 13, 26); bg.fillStyle = '#3a2216'; bg.textAlign = 'left'; bg.fillText('×' + d.give[k], x + 28, cy); x += 28 + 28; });
    });
    btx.needsUpdate = true;
  };
  return { update(tt, dt) {
    t += dt; const b = s.boat;
    if (!m && cv) { m = c.sprite(cv, { x: 0, y: 0, z: 0, ppu }); m.visible = false; scene.add(m); }
    if (!m) return;
    m.visible = !!b;
    if (b) {
      const bob = Math.sin(t * 1.8 + 1) * 0.04;
      m.position.set(b.x, 0.0 + bob, b.z); m.rotation.z = Math.sin(t * 1.2) * 0.03;
      const k = b.phase === 'come' || b.phase === 'leave' ? 1 : 1;
      m.scale.set(cv.width / ppu * k, cv.height / ppu / Math.cos(c.cam.pitch), 1);
    }
    const open = b && b.phase === 'stay' ? D.BOAT.RES[b.res].deals.filter((d, i) => !b.done[i]) : [];      // ふきだし
    if (open.length) {
      if (!bub) { const pg = new THREE.PlaneGeometry(1, 1); pg.translate(0, 0.5, 0); bub = new THREE.Mesh(pg, new THREE.MeshBasicMaterial({ transparent: true, depthTest: false })); bub.renderOrder = 6; bub.rotation.y = c.cam.yaw; scene.add(bub); drawBubble(b, open); bub.material.map = btx; bub.material.needsUpdate = true; }
      const key = b.res + '|' + open.map(d => Object.keys(d.want).map(k => s.inv[k] || 0).join(',')).join(';') + '|' + open.length;
      if (key !== bkey) { bkey = key; drawBubble(b, open); bub.material.map = btx; }
      bub.scale.set(2.0, 2.0 * 120 / BW, 1); bub.position.set(b.x, m.scale.y * 0.7 + Math.sin(t * 2.4) * 0.03, b.z); bub.visible = true;
    } else if (bub) bub.visible = false;
  } };
};
