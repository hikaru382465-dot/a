// 海：イカダのまわりに泡。マスが増えるたびに、岸までの距離の絵を作り直す
window.RAFT.parts.water = function (c) {
  const { THREE, scene, state: s, RAFT: R } = c;
  const MIN = -20, SIZE = 40, RES = 8, N = SIZE * RES, data = new Uint8Array(N * N * 4);
  const tex = new THREE.DataTexture(data, N, N, THREE.RGBAFormat);
  tex.magFilter = tex.minFilter = THREE.LinearFilter;
  let rev = -1;
  function rebuild() {
    const set = new Set(s.raft.cells.map(([x, z]) => x + ',' + z));
    for (let py = 0; py < N; py++) for (let px = 0; px < N; px++) {
      const wx = px / RES + MIN + 0.5 / RES, wz = py / RES + MIN + 0.5 / RES, cx = Math.floor(wx), cz = Math.floor(wz); let d = 3;
      for (let dz = -4; dz <= 4; dz++) for (let dx = -4; dx <= 4; dx++) {
        const X = cx + dx, Z = cz + dz; if (!set.has(X + ',' + Z)) continue;
        const dd = Math.hypot(Math.max(X - wx, 0, wx - X - 1), Math.max(Z - wz, 0, wz - Z - 1)); if (dd < d) d = dd;
      }
      const o = (py * N + px) * 4; data[o] = Math.round(d / 3 * 255); data[o + 3] = 255;
    }
    tex.needsUpdate = true; rev = s.raftRev;
  }
  rebuild();
  const col = h => new THREE.Color(h);
  const u = { uTime: { value: 0 }, uShore: { value: tex }, uSize: { value: SIZE }, uMin: { value: MIN },
    uShallow: { value: col('#46909c') }, uDeep: { value: col('#1f4e6b') }, uFoam: { value: col('#e6efe0') }, uHi: { value: col('#8fc3bd') }, uTint: { value: new THREE.Color(1, 1, 1) } };
  const mat = new THREE.ShaderMaterial({ uniforms: u,
    vertexShader: 'varying vec2 vXZ;void main(){vec4 w=modelMatrix*vec4(position,1.);vXZ=w.xz;gl_Position=projectionMatrix*viewMatrix*w;}',
    fragmentShader: `uniform float uTime,uSize,uMin;uniform sampler2D uShore;uniform vec3 uShallow,uDeep,uFoam,uHi,uTint;varying vec2 vXZ;
void main(){
  vec2 q=floor(vXZ*16.)/16.;
  float d=texture2D(uShore,clamp((q-uMin)/uSize,0.,1.)).r*3.;
  float k=smoothstep(.1,2.6,d);
  vec3 col=mix(uShallow,uDeep,k);
  float a=sin(q.x*2.1+q.y*1.3+uTime*.9)+sin(q.x*1.1-q.y*2.3-uTime*.7)+sin((q.x+q.y)*.6+uTime*.4);
  col=mix(col,uHi,step(2.4,a)*.4);
  col*=1.-.08*step(a,-2.0);
  float ring=sin(d*7.-uTime*1.6);
  col=mix(col,uHi,step(.93,ring)*step(d,2.2)*.35*(1.-k));
  float f=.2+.07*sin(uTime*1.5-d*6.)+.04*sin(q.x*5.+uTime);
  col=mix(col,uFoam,step(d,f));
  gl_FragColor=vec4(col*uTint,1.);
  #include <colorspace_fragment>
}` });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), mat); m.rotation.x = -Math.PI / 2; m.position.set(2, 0, 2); scene.add(m);
  c.water = { uniforms: u }; let phase = 0;
  return { update(t, dt) {
    if (s.raftRev !== rev) rebuild();
    phase += dt * (0.7 + R.sim.speed(s) * 0.9); u.uTime.value = phase;
  } };
};
