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
    uShallow: { value: col('#33a8bf') }, uDeep: { value: col('#1f64b8') }, uFoam: { value: col('#f2f6ee') }, uHi: { value: col('#86d2e0') }, uCam: { value: new THREE.Vector2() }, uGlit: { value: 0.5 }, uGlitCol: { value: new THREE.Color('#fff4d0') }, uChop: { value: 0.3 }, uTint: { value: new THREE.Color(1, 1, 1) }, uRefl: { value: new THREE.Vector2(0.3, 0.3) } };
  const mat = new THREE.ShaderMaterial({ uniforms: u,
    vertexShader: 'varying vec2 vXZ;void main(){vec4 w=modelMatrix*vec4(position,1.);vXZ=w.xz;gl_Position=projectionMatrix*viewMatrix*w;}',
    fragmentShader: `uniform float uTime,uSize,uMin;uniform sampler2D uShore;uniform vec3 uShallow,uDeep,uFoam,uHi,uTint;uniform vec2 uRefl,uCam;uniform float uGlit,uChop;uniform vec3 uGlitCol;varying vec2 vXZ;
float h21(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
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
  vec2 wob=vec2(sin(q.y*7.+uTime*1.4),sin(q.x*7.+uTime*1.1))*.035;
  float r1=1.-step(.004,texture2D(uShore,clamp((q-uRefl+wob-uMin)/uSize,0.,1.)).r*3.);
  float r2=1.-step(.004,texture2D(uShore,clamp((q-uRefl*1.9+wob*1.6-uMin)/uSize,0.,1.)).r*3.);
  float own=step(.03,d);
  float band=.8+.2*step(0.,sin(q.y*28.+uTime*2.));
  vec3 woodR=vec3(.40,.26,.17)*band;
  col=mix(col,woodR,own*(r1*.62+r2*(1.-r1)*.3));
  float f=.2+.07*sin(uTime*1.5-d*6.)+.04*sin(q.x*5.+uTime);
  col=mix(col,uFoam,step(d,f));
  // 海っぽさ：大きなうねり・きらきら・イカダの映りこみ
  col*=1.+.07*sin(q.x*.35+uTime*.3)*sin(q.y*.3-uTime*.25);
  float tw=floor(uTime*2.5);
  float sp=step(.9972,fract(sin(dot(floor(q*16.)+tw*3.1,vec2(12.9898,78.233)))*43758.5453));
  col=mix(col,vec3(.95,1.,1.),sp*.5*smoothstep(.6,1.6,d));
  // 波がしらの白いすじ（沖ほど多い。嵐で増える）
  vec2 wp=vec2(q.x*1.3+uTime*.3,q.y*3.6);vec2 wc=floor(wp);
  float dash=step(1.-.035*(.5+uChop),h21(wc))*step(fract(wp.x),.6)*step(fract(wp.y),.16);
  col=mix(col,vec3(.93,.97,1.),dash*.4*smoothstep(1.,2.4,d));
  // 太陽（月）の光の道：画面の奥へのびる帯のなかで、きらきら
  vec2 dd=vXZ-uCam;float lane=(dd.x-dd.y)*.7071;
  float lb=exp(-lane*lane/.45);
  float g=step(1.-.22*lb,h21(floor(q*16.)*vec2(1.,2.)+floor(uTime*2.5)*1.7));
  col=mix(col,uGlitCol,g*uGlit*smoothstep(.5,1.5,d)*.9);
  col+=uGlitCol*lb*uGlit*.04;
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
