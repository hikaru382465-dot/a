// 2人のキャラ（ひかるが操作する男の子／自動で動く相棒の女の子）と、クリックの操作
// 絵は art/chars/sheet.png から切り出した chars.js（歩く4コマ×4方向）。読み込めるまでは何も出さない
window.RAFT.parts.buddy = function (c) {
  const { THREE, scene, state: s, I, R } = c, CA = R.charArt;
  const group = new THREE.Group(); scene.add(group);
  const shadowCv = (() => { const [cv, g] = I.canvas(32, 16); g.fillStyle = 'rgba(20,10,40,.5)'; g.beginPath(); g.ellipse(16, 8, 15, 7, 0, 0, 6.3); g.fill(); return cv; })();
  const shadowTex = c.tex(shadowCv);
  const DIRS = ['down', 'up', 'left', 'right'];
  function makeChar(name, actor) {
    const set = CA && CA[name]; if (!set) return null;
    const ch = { actor, tex: {}, ready: false };
    let left = 0;
    DIRS.forEach(d => { ch.tex[d] = []; set[d].forEach((f, i) => { left++; const im = new Image(); im.onload = () => { const tx = new THREE.Texture(im); tx.colorSpace = THREE.SRGBColorSpace; tx.magFilter = tx.minFilter = THREE.NearestFilter; tx.generateMipmaps = false; tx.needsUpdate = true; ch.tex[d][i] = tx; if (--left === 0) ch.ready = true; }; im.src = f.src; }); });
    const g = new THREE.PlaneGeometry(1, 1); g.translate(0, 0.5, 0);
    ch.mat = new THREE.MeshBasicMaterial({ transparent: true, alphaTest: 0.45 }); c.sprites.push(ch.mat);
    ch.mesh = new THREE.Mesh(g, ch.mat); ch.mesh.rotation.y = c.cam.yaw; ch.mesh.visible = false; group.add(ch.mesh);
    ch.sh = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 0.4), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false }));
    ch.sh.rotation.x = -Math.PI / 2; ch.sh.rotation.z = Math.PI / 4; group.add(ch.sh);
    ch.set = set; return ch;
  }
  const chars = [makeChar('boy', s.player), makeChar('girl', s.buddy)].filter(Boolean);
  c.chars = chars;

  // ---- 操作 ----
  // 床・置いた物をタップ＝歩く・使う／海を押し続ける＝ゲージがたまる→離すと、その強さの距離へ網を投げる（網を手に持っているとき）
  // 網が出ている間に押す＝引き寄せる／置くモード（持ち物から選んだ物）では、光るマスをタップして置く
  const el = c.renderer.domElement, ray = new THREE.Raycaster(), plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -0.2), pt = new THREE.Vector3();
  let down = null, aimT0 = 0;
  const GAUGE_SEC = 1.1;
  // 画面の位置 → 地面の位置。置くモードでは、光っている面の高さ（床板は海面ぎわ、ほかはイカダの上）で測る
  const world = e => {
    const pl = c.mode.place ? (c.mode.place.k === 'floor' ? 0.06 : 0.215) : 0.2; plane.constant = -pl;
    const rc = el.getBoundingClientRect();
    ray.setFromCamera(new THREE.Vector2((e.clientX - rc.left) / rc.width * 2 - 1, -((e.clientY - rc.top) / rc.height) * 2 + 1), c.camera); return ray.ray.intersectPlane(plane, pt) ? pt.clone() : null;
  };
  const power = () => { const p = ((performance.now() - aimT0) / 1000 / GAUGE_SEC) % 2; return p < 1 ? p : 2 - p; };
  const setAim = (p, pw) => { const t = R.sim.throwTarget(s, p.x, p.z, pw); c.aim.x = t.x; c.aim.z = t.z; c.aim.power = pw; c.aim.px = p.x; c.aim.pz = p.z; };
  el.addEventListener('pointerdown', e => {
    if (c.ui && c.ui.open) return;
    const p = world(e); down = { x: e.clientX, y: e.clientY, p, aim: false };
    if (!p || c.mode.place) return;
    if (s.net.cast) { R.sim.recallNet(s); down.recall = true; return; }
    if (R.sim.has(s, Math.floor(p.x), Math.floor(p.z))) return;
    if (s.hand !== 'net') { s.events.push({ e: 'noequip' }); down = null; return; }
    down.aim = true; aimT0 = performance.now(); c.aim.active = true; setAim(p, 0);
  });
  el.addEventListener('pointermove', e => { if (down && down.aim) { const p = world(e); if (p) down.p = p; } });
  el.addEventListener('pointerup', e => {
    const d = down; down = null; c.aim.active = false;
    if (!d) return;
    if (d.aim) { const p = d.p; if (p) R.sim.throwNet(s, p.x, p.z, power()); return; }
    if (d.recall || !d.p || Math.hypot(e.clientX - d.x, e.clientY - d.y) > 6) return;
    const x = Math.floor(d.p.x), z = Math.floor(d.p.z), sim = R.sim;
    if (c.mode.place) { c.hud.tryPlace(x, z); return; }
    const o = sim.objAt(s, x, z);
    if (o) { sim.useObj(s, o.id); return; }
    if (sim.has(s, x, z)) sim.walkTo(s, x, z);
  });
  let t = 0;
  return { update(tt, dt) {
    t += dt;
    if (down && down.aim && down.p) setAim(down.p, power());
    chars.forEach(ch => {
      if (!ch.ready) return; const a = ch.actor, walking = a.path.length > 0, dir = a.dir || 'down';
      const fr = walking ? Math.floor(t * 8) % 4 : (a.act ? Math.floor(t * 4) % 2 : 0), f = ch.set[dir][fr], tx = ch.tex[dir][fr];
      if (!tx) return;
      ch.mat.map = tx; ch.mat.needsUpdate = false;
      const bob = walking ? 0 : (a.act ? Math.abs(Math.sin(t * 14)) * 0.04 : 0);
      ch.mesh.scale.set(f.w / CA.ppu, f.h / CA.ppu / Math.cos(c.cam.pitch), 1);
      ch.mesh.position.set(a.x, 0.2 + bob, a.z); ch.mesh.visible = true; ch.sh.position.set(a.x + 0.04, 0.215, a.z + 0.04);
    });
  } };
};
