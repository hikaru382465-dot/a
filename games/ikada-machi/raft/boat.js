// 船の住人の船：夕方に来て、イカダのそばにとまる。タップで交渉の画面（hud.js の openBoat）
window.RAFT.parts.boat = function (c) {
  const { THREE, scene, state: s, I, R } = c, OA = R.objArt;
  let m = null, cv = null, t = 0;
  if (OA && OA.icons && OA.icons.boat) { const f = OA.icons.boat[0], [cvs, g] = I.canvas(f.w, f.h), im = new Image(); im.onload = () => { g.drawImage(im, 0, 0); cv = cvs; }; im.src = f.src; }
  const flag = (() => { const [cvf, g] = I.canvas(3, 4); I.rect(g, 0, 0, 3, 3, '#e0503c'); I.rect(g, 0, 3, 1, 1, '#4a2c20'); return cvf; })();
  const ppu = 52;
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
  } };
};
