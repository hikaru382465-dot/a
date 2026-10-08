// 光と時間帯、仕上げ（ブルーム・奥と手前のぼかし・色の調整・周辺の暗がり）
window.RAFT.parts.light = function (c) {
  const { THREE, scene, renderer, camera, state: s } = c;
  const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.set(-0.5, 1.2, 0.8); scene.add(sun);
  const amb = new THREE.AmbientLight(0xffffff, 1.5); scene.add(amb);
  const hemi = new THREE.HemisphereLight(0xaac8ff, 0x553322, 0.5); scene.add(hemi);
  const C = h => new THREE.Color(h);
  const presets = {
    morning: { sun: C('#ffe4bd'), sunI: 2.2, amb: C('#a9bde0'), ambI: 1.5, tint: C('#ffffff'), water: C('#ffffff'), bg: C('#1f4e6b'), bloom: 0.35, glow: 0.0, grade: C('#fff4e6'), vig: 0.35 },
    noon:    { sun: C('#fff4dc'), sunI: 2.5, amb: C('#b4c8e8'), ambI: 1.55, tint: C('#ffffff'), water: C('#ffffff'), bg: C('#2a6a8a'), bloom: 0.3, glow: 0.0, grade: C('#ffffff'), vig: 0.3 },
    dusk:    { sun: C('#ffb47c'), sunI: 1.9, amb: C('#9a7fc0'), ambI: 1.35, tint: C('#ffd6c0'), water: C('#ffe8d8'), bg: C('#4a3a62'), bloom: 0.55, glow: 0.55, grade: C('#ffd9c4'), vig: 0.5 },
    night:   { sun: C('#7f94ff'), sunI: 0.9, amb: C('#5c70c0'), ambI: 1.05, tint: C('#8fa2e6'), water: C('#a3b6f4'), bg: C('#0c1530'), bloom: 0.85, glow: 1.0, grade: C('#cfd9ff'), vig: 0.65 }
  };
  const keys = [[0, 'morning'], [0.2, 'noon'], [0.5, 'noon'], [0.66, 'dusk'], [0.78, 'night'], [0.93, 'night'], [1, 'morning']];
  const names = Object.keys(presets.morning);
  const cur = {}; names.forEach(k => cur[k] = presets.morning[k].clone ? presets.morning[k].clone() : presets.morning[k]);
  function at(t) {
    let i = 0; while (i < keys.length - 2 && t > keys[i + 1][0]) i++;
    const [t0, n0] = keys[i], [t1, n1] = keys[i + 1], f = Math.max(0, Math.min(1, (t - t0) / (t1 - t0))), A = presets[n0], B = presets[n1];
    names.forEach(k => { if (cur[k].lerpColors) cur[k].lerpColors(A[k], B[k], f); else cur[k] = A[k] + (B[k] - A[k]) * f; });
  }
  let storm = 0;
  const stormTint = C('#8e9bb0');

  let composer = null, bloom = null, tilt = null, grade = null;
  if (!c.low) {
    const { EffectComposer, RenderPass, UnrealBloomPass, ShaderPass, OutputPass } = c;
    composer = new EffectComposer(renderer); composer.setPixelRatio(Math.min(devicePixelRatio, 2)); composer.setSize(innerWidth, innerHeight);
    composer.addPass(new RenderPass(scene, camera));
    bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.4, 0.55, 0.95); composer.addPass(bloom);
    tilt = new ShaderPass({
      uniforms: { tDiffuse: { value: null }, uAmt: { value: 0.0035 }, uFocus: { value: 0.35 }, uAsp: { value: innerWidth / innerHeight } },
      vertexShader: 'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
      fragmentShader: `uniform sampler2D tDiffuse;uniform float uAmt,uFocus,uAsp;varying vec2 vUv;
void main(){
  float m=smoothstep(uFocus,1.,abs(vUv.y-.5)*2.);
  float r=m*uAmt;
  vec4 s=texture2D(tDiffuse,vUv);float n=1.;
  for(int i=0;i<12;i++){float a=float(i)*2.39996,d=sqrt(float(i)+.5)/3.46;
    vec2 o=vec2(cos(a)/uAsp,sin(a))*d*r;s+=texture2D(tDiffuse,vUv+o);n+=1.;}
  gl_FragColor=s/n;}`
    });
    composer.addPass(tilt);
    grade = new ShaderPass({
      uniforms: { tDiffuse: { value: null }, uTint: { value: new THREE.Color(1, 1, 1) }, uVig: { value: 0.4 }, uAsp: { value: innerWidth / innerHeight } },
      vertexShader: 'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
      fragmentShader: `uniform sampler2D tDiffuse;uniform vec3 uTint;uniform float uVig,uAsp;varying vec2 vUv;
void main(){
  vec2 p=vUv-.5;vec2 ca=p*.0025;
  vec3 c=vec3(texture2D(tDiffuse,vUv+ca).r,texture2D(tDiffuse,vUv).g,texture2D(tDiffuse,vUv-ca).b);
  float l=dot(c,vec3(.299,.587,.114));
  c=mix(vec3(l),c,1.12);
  c*=uTint;
  c=(c-.5)*1.06+.5;
  c*=1.-uVig*smoothstep(.25,.85,length(p*vec2(uAsp*.75,1.)));
  gl_FragColor=vec4(c,1.);}`
    });
    composer.addPass(grade); composer.addPass(new OutputPass());
    c.onResize.push(() => { composer.setSize(innerWidth, innerHeight); tilt.uniforms.uAsp.value = grade.uniforms.uAsp.value = innerWidth / innerHeight; });
    c.render = () => composer.render();
  }
  c.fx = {
    setBloom(on) { if (bloom) bloom.enabled = on; },
    setBlur(on) { if (tilt) tilt.enabled = on; }
  };
  return {
    update(t, dt) {
      at(s.clock.t);
      storm += ((s.weather.id === 'storm' ? 1 : 0) - storm) * (1 - Math.exp(-dt * 0.8));
      const dim = 1 - storm * 0.4;
      sun.color.copy(cur.sun); sun.intensity = cur.sunI * (1 - storm * 0.5); amb.color.copy(cur.amb); amb.intensity = cur.ambI * (1 - storm * 0.1);
      const tint = cur.tint.clone().lerp(stormTint, storm * 0.5).multiplyScalar(dim);
      scene.background = cur.bg.clone().multiplyScalar(dim);
      c.sprites.forEach(m => m.color.copy(tint));
      if (c.water) c.water.uniforms.uTint.value.copy(cur.water.clone().lerp(stormTint, storm * 0.5).multiplyScalar(dim));
      c.glows.forEach(g => g.mat.opacity = 0.12 + Math.min(1, cur.glow + storm * 0.3) * 0.88);
      if (bloom) bloom.strength = cur.bloom;
      if (grade) { grade.uniforms.uTint.value.copy(cur.grade); grade.uniforms.uVig.value = cur.vig + storm * 0.15; }
      c.lowNeeds = s.needs.hunger <= 0 || s.needs.thirst <= 0;
      if (tilt) tilt.uniforms.uAmt.value = c.lowNeeds ? 0.012 : 0.0035;
    }
  };
};
