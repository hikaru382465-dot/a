// 海：ドット絵の格子に合わせた波の帯と、岸の白い泡
window.ISLAND.parts.water = function (c) {
  const { THREE, scene, map } = c, tiles = map.tiles;
  const MARG = 8, SIZE = map.W + MARG * 2, RES = 8, N = SIZE * RES;
  const data = new Uint8Array(N * N * 4);
  const land = (x, z) => tiles[z] && tiles[z][x] && tiles[z][x].h != null;
  for (let py = 0; py < N; py++) for (let px = 0; px < N; px++) {
    const wx = px / RES - MARG + 0.5 / RES, wz = py / RES - MARG + 0.5 / RES;
    const cx = Math.floor(wx), cz = Math.floor(wz); let d = 3;
    for (let dz = -4; dz <= 4; dz++) for (let dx = -4; dx <= 4; dx++) {
      const X = cx + dx, Z = cz + dz; if (!land(X, Z)) continue;
      const ddx = Math.max(X - wx, 0, wx - X - 1), ddz = Math.max(Z - wz, 0, wz - Z - 1);
      const dd = Math.hypot(ddx, ddz); if (dd < d) d = dd;
    }
    const o = (py * N + px) * 4; data[o] = Math.round(d / 3 * 255); data[o + 3] = 255;
  }
  const shore = new THREE.DataTexture(data, N, N, THREE.RGBAFormat);
  shore.magFilter = THREE.LinearFilter; shore.minFilter = THREE.LinearFilter; shore.needsUpdate = true;

  const col = h => new THREE.Color(h);
  const u = {
    uTime: { value: 0 }, uShore: { value: shore }, uSize: { value: SIZE }, uMarg: { value: MARG },
    uShallow: { value: col('#46909c') }, uDeep: { value: col('#1f4e6b') }, uFoam: { value: col('#e6efe0') },
    uHi: { value: col('#8fc3bd') }, uTint: { value: new THREE.Color(1, 1, 1) }
  };
  const mat = new THREE.ShaderMaterial({
    uniforms: u,
    vertexShader: 'varying vec2 vXZ;void main(){vec4 w=modelMatrix*vec4(position,1.);vXZ=w.xz;gl_Position=projectionMatrix*viewMatrix*w;}',
    fragmentShader: `uniform float uTime,uSize,uMarg;uniform sampler2D uShore;uniform vec3 uShallow,uDeep,uFoam,uHi,uTint;varying vec2 vXZ;
void main(){
  vec2 q=floor(vXZ*16.)/16.;
  float d=texture2D(uShore,(q+uMarg)/uSize).r*3.;
  float k=smoothstep(.1,2.6,d);
  vec3 col=mix(uShallow,uDeep,k);
  float a=sin(q.x*2.1+q.y*1.3+uTime*.9)+sin(q.x*1.1-q.y*2.3-uTime*.7)+sin((q.x+q.y)*.6+uTime*.4);
  col=mix(col,uHi,step(2.5,a)*.4);
  col*=1.-.08*step(a,-2.0);
  float ring=sin(d*7.-uTime*1.6);
  col=mix(col,uHi,step(.93,ring)*step(d,2.2)*.35*(1.-k));
  float f=.22+.07*sin(uTime*1.5-d*6.)+.04*sin(q.x*5.+uTime);
  col=mix(col,uFoam,step(d,f));
  gl_FragColor=vec4(col*uTint,1.);
  #include <colorspace_fragment>
}`
  });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(220, 220), mat);
  m.rotation.x = -Math.PI / 2; m.position.set(12, c.WATER_Y == null ? -0.25 : c.WATER_Y, 12); scene.add(m);
  c.water = { uniforms: u };
  return { update(t) { u.uTime.value = t; } };
};
