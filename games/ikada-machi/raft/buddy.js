// 2人のキャラ（ひかるが操作する男の子／自動で動く相棒の女の子）と、クリックの操作
// 絵は art/chars/sheet.png から切り出した chars.js（歩く4コマ×4方向）。読み込めるまでは何も出さない
window.RAFT.parts.buddy = function (c) {
  const K = 1.3;      // キャラの大きさの倍率（表情やしぐさが見えるように、大きめ）
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
    ch.mat = new THREE.MeshBasicMaterial({ transparent: true, alphaTest: 0.45, side: THREE.DoubleSide }); c.sprites.push(ch.mat);
    ch.mesh = new THREE.Mesh(g, ch.mat); ch.mesh.rotation.y = c.cam.yaw; ch.mesh.visible = false; group.add(ch.mesh);
    ch.sh = new THREE.Mesh(new THREE.PlaneGeometry(0.8 * K, 0.4 * K), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false }));
    ch.sh.rotation.x = -Math.PI / 2; ch.sh.rotation.z = Math.PI / 4; group.add(ch.sh);
    ch.set = set; return ch;
  }
  const chars = [makeChar('boy', s.player), makeChar('girl', s.buddy)].filter(Boolean);
  // 相棒のしぐさ（poses_art.js）：釣り・座る・寝る・水を飲む・やったー！ など。1枚絵なので、左向きは左右反転
  const PA = R.poseArt, poseTex = {};
  if (PA) Object.keys(PA.poses).forEach(k => { const f = PA.poses[k], im = new Image(); im.onload = () => { const tx = new THREE.Texture(im); tx.colorSpace = THREE.SRGBColorSpace; tx.magFilter = tx.minFilter = THREE.NearestFilter; tx.generateMipmaps = false; tx.needsUpdate = true; poseTex[k] = tx; }; im.src = f.src; });
  const animTex = {}; let animName = null, animT = 0;
  if (PA && PA.anims) Object.keys(PA.anims).forEach(k => { animTex[k] = []; PA.anims[k].frames.forEach((f, i) => { const im = new Image(); im.onload = () => { const tx = new THREE.Texture(im); tx.colorSpace = THREE.SRGBColorSpace; tx.magFilter = tx.minFilter = THREE.NearestFilter; tx.generateMipmaps = false; tx.needsUpdate = true; animTex[k][i] = tx; }; im.src = f.src; }); });
  // 吹き出し（emotes_art.js）：状態にあわせて、キャラの頭の上に出す（ふわっと出て、浮かぶ）
  const EA = R.emoteArt, emoTex = {}; let emoteTop = 1, emoKey = null, emoT = 0;
  const emoMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ transparent: true, alphaTest: 0.05, depthTest: false })); emoMesh.rotation.y = c.cam.yaw; emoMesh.renderOrder = 6; emoMesh.visible = false; group.add(emoMesh);
  if (EA) Object.keys(EA.emotes).forEach(k => { const f = EA.emotes[k], im = new Image(); im.onload = () => { const tx = new THREE.Texture(im); tx.colorSpace = THREE.SRGBColorSpace; tx.magFilter = tx.minFilter = THREE.NearestFilter; tx.generateMipmaps = false; tx.needsUpdate = true; emoTex[k] = tx; }; im.src = f.src; });
  let lastWeather = s.weather.id, burstT = 0;
  let cheerId = s.buddy.cheer || 0, cheerT = 0;
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
  // 相棒をタップしたか。置き物（焚き火など）のほうが近いときは、置き物を優先する（イカダがせまくても、まちがえない）
  const scr = (x, y, z, e) => { const v = new THREE.Vector3(x, y, z).project(c.camera), rc = el.getBoundingClientRect(); return Math.hypot(e.clientX - (rc.left + (v.x + 1) / 2 * rc.width), e.clientY - (rc.top + (1 - v.y) / 2 * rc.height)); };
  const hitBuddy = e => { const ch = s.buddy, d = scr(ch.x, 0.55, ch.z, e); if (d >= 30) return false;
    return !s.objects.some(o => scr(o.x + 0.5, 0.4, o.z + 0.5, e) < d + 6); };
  const power = () => { const p = ((performance.now() - aimT0) / 1000 / GAUGE_SEC) % 2; return p < 1 ? p : 2 - p; };
  const setAim = (p, pw) => { const t = R.sim.throwTarget(s, p.x, p.z, pw); c.aim.x = t.x; c.aim.z = t.z; c.aim.power = pw; c.aim.px = p.x; c.aim.pz = p.z; };
  el.addEventListener('pointerdown', e => {
    if (c.ui && c.ui.open) return;
    if (c.pinching) { down = null; return; }
    if (!c.mode.place && s.boat && s.boat.phase === 'stay' && scr(s.boat.x, 0.35, s.boat.z, e) < 55) { down = { x: e.clientX, y: e.clientY, boat: true }; return; }      // 船をタップ：交渉
    if (!c.mode.place && !s.net.cast && !s.rod && hitBuddy(e)) { down = { x: e.clientX, y: e.clientY, buddy: true }; return; }     // 相棒をタップ：お願いの画面
    const p = world(e); down = { x: e.clientX, y: e.clientY, p, aim: false };
    if (!p || c.mode.place) return;
    if (s.rod) { R.sim.reelRod(s); down = null; return; }
    if (s.hand === 'rod' && !R.sim.has(s, Math.floor(p.x), Math.floor(p.z))) { R.sim.castRod(s, p.x, p.z); down = null; return; }
    if (s.net.cast) { R.sim.recallNet(s); down.recall = true; return; }
    if (R.sim.has(s, Math.floor(p.x), Math.floor(p.z))) return;
    if (s.hand !== 'net') { s.events.push({ e: 'noequip' }); down = null; return; }
    down.aim = true; aimT0 = performance.now(); c.aim.active = true; setAim(p, 0);
  });
  el.addEventListener('pointermove', e => { if (down && down.aim) { const p = world(e); if (p) down.p = p; } });
  el.addEventListener('pointerup', e => {
    const d = down; down = null; c.aim.active = false;
    if (!d || c.pinching) return;
    if (d.boat) { if (Math.hypot(e.clientX - d.x, e.clientY - d.y) <= 8) c.hud.openBoat(); return; }
    if (d.buddy) { if (Math.hypot(e.clientX - d.x, e.clientY - d.y) <= 8) c.hud.openJobs(); return; }
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
      if (ch.actor === s.buddy && PA) {
        const bu = s.buddy; if ((bu.cheer || 0) !== cheerId) { cheerId = bu.cheer || 0; cheerT = 1.1; } cheerT = Math.max(0, cheerT - dt);
        let pose = null, anim = null;
        if (bu.act && bu.act.type === 'eat' && PA.anims[bu.act.kind || 'eat']) anim = bu.act.kind || 'eat';
        else if (cheerT > 0) pose = 'cheer';
        else if (bu.job === 'fish' && bu.line && !walking) pose = 'fish';
        else if ((bu.job === 'rest' || bu.job === 'sit' || bu.job === 'sleep') && !walking && bu.spot && Math.floor(a.x) === bu.spot[0] && Math.floor(a.z) === bu.spot[1]) anim = bu.job === 'sleep' ? 'sleep' : bu.job === 'sit' ? 'sit' : 'relax';
        if (anim !== animName) { animName = anim; animT = 0; } animT += dt;
        c.buddyTip = null;
        let f0 = null, tx0 = null;
        if (anim) { const an = PA.anims[anim], n = an.frames.length; let i;
          if (bu.act && bu.act.dur) i = Math.min(n - 1, Math.floor((1 - bu.act.t / bu.act.dur) * n));       // 食べる・飲む：動作の長さにあわせて1回
          else if (an.intro) {       // 落ち着くまで1回 → そのまま止まる。ときどきだけ別の動き
            const dI = an.intro.length / an.fps;
            if (animT < dI) i = an.intro[Math.floor(animT * an.fps)];
            else { const eD = an.extra.length / an.extraFps, tt = (animT - dI) % an.every; i = tt < an.every - eD ? an.hold : an.extra[Math.min(an.extra.length - 1, Math.floor((tt - (an.every - eD)) * an.extraFps))]; } }
          else { i = Math.floor(animT * an.fps); if (an.loop !== null && i >= n) i = an.loop + ((i - an.loop) % (n - an.loop)); i = Math.min(i, n - 1); }
          f0 = an.frames[i]; tx0 = animTex[anim] && animTex[anim][i]; }
        else if (pose && poseTex[pose]) { f0 = PA.poses[pose]; tx0 = poseTex[pose]; }
        if (f0 && tx0) {
          const f = f0, mir = dir === 'left' ? -1 : 1;
          ch.mat.map = tx0; ch.mat.needsUpdate = false;
          let rz = 0, by = 0, sy = 1;      // 1枚絵に、コードで動きをつける
          if (anim === 'sleep') { const w = Math.sin(animT * 1.6); rz = (w > 0 ? w * 0.12 : w * 0.03) * mir; sy = 1 - Math.max(0, w) * 0.025; }     // こっくり
          else if (anim === 'sit' || anim === 'relax') sy = 1 + Math.sin(animT * 2) * 0.014;                                                   // 息づかい
          else if (anim === 'drink' || anim === 'eat') by = Math.abs(Math.sin(animT * 7)) * 0.025;                                              // ごくごく・もぐもぐ
          else if (pose === 'cheer') by = Math.abs(Math.sin(cheerT * 9)) * 0.05;
          ch.mesh.rotation.z = rz; emoteTop = 0.2 + by + f.h * sy / (PA.ppu / K) / Math.cos(c.cam.pitch);
          ch.mesh.scale.set(mir * f.w / (PA.ppu / K), f.h * sy / (PA.ppu / K) / Math.cos(c.cam.pitch), 1); ch.mesh.position.set(a.x, 0.2 + by, a.z); ch.mesh.visible = true; ch.sh.position.set(a.x + 0.04, 0.215, a.z + 0.04);
          if (pose === 'fish' && f.tip) c.buddyTip = [a.x + Math.cos(c.cam.yaw) * mir * (f.tip[0] - f.w / 2) / (PA.ppu / K), 0.2 + (f.h - f.tip[1]) / (PA.ppu / K) / Math.cos(c.cam.pitch), a.z - Math.sin(c.cam.yaw) * mir * (f.tip[0] - f.w / 2) / (PA.ppu / K)];
          return;
        }
      }
      if (ch.actor === s.buddy) { ch.mesh.rotation.z = 0; emoteTop = 0.2 + (ch.set[dir][0].h) / (CA.ppu / K) / Math.cos(c.cam.pitch); }
      const fr = walking ? Math.floor(t * 8) % 4 : (a.act ? Math.floor(t * 4) % 2 : 0), f = ch.set[dir][fr], tx = ch.tex[dir][fr];
      if (!tx) return;
      ch.mat.map = tx; ch.mat.needsUpdate = false;
      const bob = walking ? 0 : (a.act ? Math.abs(Math.sin(t * 14)) * 0.04 : 0);
      ch.mesh.scale.set(f.w / (CA.ppu / K), f.h / (CA.ppu / K) / Math.cos(c.cam.pitch), 1);
      ch.mesh.position.set(a.x, 0.2 + bob, a.z); ch.mesh.visible = true; ch.sh.position.set(a.x + 0.04, 0.215, a.z + 0.04);
    });
    if (EA) {      // 相棒の吹き出し：いちばん大事なものを1つ
      const bu = s.buddy, D = R.data; let key = null;
      if (s.weather.id !== lastWeather) { if (s.weather.id === 'storm') burstT = 2.6; lastWeather = s.weather.id; } burstT = Math.max(0, burstT - dt);
      if (cheerT > 0) key = 'heart';
      else if (burstT > 0) key = 'burst';                                              // 嵐になった：びっくり
      else if (R.sim.weak(s)) key = 'gloom';                                           // 飢えて渇いて、ふらふら
      else if (bu.job === 'sleep' && !bu.path.length) key = 'zz';
      else if (bu.job === 'rest' && !bu.path.length) key = 'music';
      else if (s.needs.hunger < D.NEEDS.low || s.needs.thirst < D.NEEDS.low) key = 'sweat';
      else if (s.weather.id === 'storm' && (bu.job === 'fish' || bu.job === 'net')) key = 'exclaim';
      else if (bu.mood < 20 && bu.job !== 'rest' && bu.job !== 'sit' && bu.job !== 'sleep') key = 'anger';
      if (key !== emoKey) { emoKey = key; emoT = 0; } emoT += dt;
      const VAR = { zz: ['zzzClean'], music: ['note01', 'note13', 'note22', 'note30', 'note03', 'note11', 'note20', 'note32', 'note02', 'note10', 'note23', 'note31', 'note00', 'note12', 'note21', 'note33'], heart: ['heartClean'], sweat: ['sweatClean'], exclaim: ['exclaim2'], anger: ['angerClean'], gloom: ['gloom'], burst: ['burst'] };       // 毎回ちがう形（zzz・ちょうちん・音符）
      const shown = key && VAR[key] && EA.emotes[VAR[key][0]] ? VAR[key][Math.floor(emoT * 0.5) % VAR[key].length] : key;
      const tx = shown && emoTex[shown];
      emoMesh.visible = !!tx;
      if (tx) {
        const f = EA.emotes[shown], u = 1 / (EA.ppu / K) , pop = Math.min(1, emoT / 0.25), p = (emoT * 0.5) % 1, floatUp = (key === 'zz' || key === 'music') ? p * 0.22 : Math.sin(emoT * 4) * 0.02, kh = (EA.k || 1);
        emoMesh.material.map = tx; emoMesh.material.opacity = (key === 'zz' || key === 'music') ? Math.min(1, (1 - p) * 2.2) : 1; emoMesh.material.transparent = true;
        const kk = (EA.k || 1) * 1.4 * (key === 'music' ? 0.7 : 1); emoMesh.scale.set(f.w * u * pop * kk, f.h * u * pop * kk / Math.cos(c.cam.pitch), 1);
        const ox = Math.cos(c.cam.yaw) * 0.26, oz = -Math.sin(c.cam.yaw) * 0.26;
        emoMesh.position.set(bu.x + ox, emoteTop + 0.06 + floatUp + f.h * u * kh * (key === 'music' ? 0.5 : 0.7) / Math.cos(c.cam.pitch), bu.z + oz);
      }
    }
  } };
};
