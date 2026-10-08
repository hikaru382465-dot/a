// カメラ：イカダに寄って始まり、イカダが大きくなるほど自動で引いていく（正射影・見下ろし30度）
window.RAFT.parts.camera = function (c) {
  const { THREE, state: s, RAFT: R } = c;
  const yaw = Math.PI / 4, pitch = Math.PI / 6, PPU = 64 / Math.SQRT2;
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, -300, 300);
  const dir = new THREE.Vector3(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch));
  const fixed = parseFloat(new URLSearchParams(location.search).get('zoom'));
  const st = { target: new THREE.Vector3(1, 0.2, 1), zoom: 3, goal: 3, manual: 1 };
  function goalFor() {
    const bb = R.sim.bbox(s), n = bb.w + bb.d;
    const z = c.size(), fit = Math.min(z.w * 0.55 / (n * 32), z.h * 0.45 / (n * 16 + 48));
    return Math.max(0.5, Math.min(3, Math.floor(fit * 4) / 4));     // 0.25きざみで切り下げ（一度引いたら戻らない）
  }
  function apply() {
    const zoom = st.zoom * st.manual, ppu = PPU * zoom, w = c.size().w, h = c.size().h;
    cam.left = -w / 2 / ppu; cam.right = w / 2 / ppu; cam.top = h / 2 / ppu; cam.bottom = -h / 2 / ppu;
    cam.position.copy(st.target).addScaledVector(dir, 60); cam.lookAt(st.target); cam.updateProjectionMatrix();
    s.view.r = Math.hypot(w / 2 / ppu, h / ppu) + 2;
  }
  addEventListener('wheel', e => { st.manual = Math.min(1.35, Math.max(0.75, st.manual * Math.exp(-e.deltaY * 0.001))); apply(); }, { passive: true });
  c.onResize.push(apply);
  st.goal = isNaN(fixed) ? goalFor() : fixed; st.zoom = st.goal; apply();
  c.camera = cam; c.cam = { st, apply, yaw, pitch, PPU };
  return { update(t, dt) {
    const bb = R.sim.bbox(s);
    if (isNaN(fixed)) st.goal = Math.min(st.goal, goalFor());
    const f = 1 - Math.exp(-dt * 1.2);
    st.zoom += (st.goal - st.zoom) * f;
    st.target.x += ((bb.x0 + bb.x1 + 1) / 2 - st.target.x) * f; st.target.z += ((bb.z0 + bb.z1 + 1) / 2 - st.target.z) * f;
    apply();
  } };
};
