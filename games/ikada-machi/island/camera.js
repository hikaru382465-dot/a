// カメラ：正射影。横に45度回して、見下ろし角30度 → 床のマスが 64×32 のひし形に見える
window.ISLAND.parts.camera = function (c) {
  const { THREE } = c;
  const yaw = Math.PI / 4, pitch = Math.PI / 6;
  const PPU = 64 / Math.SQRT2;            // 1ワールド単位が何ピクセルか（ズーム1のとき）
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, -300, 300);
  const dir = new THREE.Vector3(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch));
  const right = new THREE.Vector3(Math.cos(yaw), 0, -Math.sin(yaw));
  const away = new THREE.Vector3(-Math.sin(yaw), 0, -Math.cos(yaw));
  const st = { target: new THREE.Vector3(12, 0.5, 13.5), zoom: 1 };
  function apply() {
    const ppu = PPU * st.zoom, w = innerWidth, h = innerHeight;
    cam.left = -w / 2 / ppu; cam.right = w / 2 / ppu; cam.top = h / 2 / ppu; cam.bottom = -h / 2 / ppu;
    st.target.x = Math.min(30, Math.max(-6, st.target.x)); st.target.z = Math.min(30, Math.max(-6, st.target.z));
    cam.position.copy(st.target).addScaledVector(dir, 60);
    cam.lookAt(st.target); cam.updateProjectionMatrix();
  }
  const pts = new Map(); let pinch0 = 0, zoom0 = 1;
  const el = c.renderer.domElement; el.style.touchAction = 'none';
  el.addEventListener('pointerdown', e => { el.setPointerCapture(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pts.size === 2) { const [a, b] = [...pts.values()]; pinch0 = Math.hypot(a.x - b.x, a.y - b.y); zoom0 = st.zoom; } });
  el.addEventListener('pointermove', e => {
    const p = pts.get(e.pointerId); if (!p) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y; p.x = e.clientX; p.y = e.clientY;
    if (pts.size === 1) {
      const ppu = PPU * st.zoom;
      st.target.addScaledVector(right, -dx / ppu).addScaledVector(away, 2 * dy / ppu); apply();
    } else if (pts.size === 2) {
      const [a, b] = [...pts.values()]; st.zoom = Math.min(3.5, Math.max(0.6, zoom0 * Math.hypot(a.x - b.x, a.y - b.y) / pinch0)); apply();
    }
  });
  const up = e => pts.delete(e.pointerId);
  el.addEventListener('pointerup', up); el.addEventListener('pointercancel', up);
  el.addEventListener('wheel', e => { e.preventDefault(); st.zoom = Math.min(3.5, Math.max(0.6, st.zoom * Math.exp(-e.deltaY * 0.0012))); apply(); }, { passive: false });
  addEventListener('keydown', e => {
    const s = 0.8 / st.zoom, k = e.key;
    if (k === 'ArrowLeft' || k === 'a') st.target.addScaledVector(right, -s);
    else if (k === 'ArrowRight' || k === 'd') st.target.addScaledVector(right, s);
    else if (k === 'ArrowUp' || k === 'w') st.target.addScaledVector(away, s);
    else if (k === 'ArrowDown' || k === 's') st.target.addScaledVector(away, -s);
    else return; apply();
  });
  c.onResize.push(apply); apply();
  c.camera = cam; c.cam = { st, apply, yaw, pitch, PPU };
};
