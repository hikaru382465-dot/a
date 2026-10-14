// 光と時間帯、仕上げ（ブルーム・奥と手前のぼかし・色の調整・周辺の暗がり）
window.ISLAND.parts.light = function (c) {
  const { THREE, scene, renderer, camera, I } = c;
  const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.set(-0.5, 1.2, 0.8); scene.add(sun);
  const amb = new THREE.AmbientLight(0xffffff, 1.5); scene.add(amb);
  const hemi = new THREE.HemisphereLight(0xaac8ff, 0x553322, 0.5); scene.add(hemi);
  const C = h => new THREE.Color(h);
  const presets = {
    morning: { sun: C('#ffe4bd'), sunI: 2.2, amb: C('#a9bde0'), ambI: 1.5, tint: C('#ffffff'), water: C('#ffffff'), bg: C('#1f4e6b'), bloom: 0.35, glow: 0.0, win: 0.9, grade: C('#fff4e6'), vig: 0.35 },
    dusk:    { sun: C('#ffb47c'), sunI: 1.9, amb: C('#9a7fc0'), ambI: 1.35, tint: C('#ffd6c0'), water: C('#ffe8d8'), bg: C('#4a3a62'), bloom: 0.55, glow: 0.55, win: 1.6, grade: C('#ffd9c4'), vig: 0.5 },
    night:   { sun: C('#7f94ff'), sunI: 0.9, amb: C('#5c70c0'), ambI: 1.05, tint: C('#8fa2e6'), water: C('#a3b6f4'), bg: C('#0c1530'), bloom: 0.85, glow: 1.0, win: 2.6, grade: C('#cfd9ff'), vig: 0.65 }
  };
  const cur = { sun: new THREE.Color(), sunI: 2, amb: new THREE.Color(), ambI: .8, tint: new THREE.Color(), water: new THREE.Color(), bg: new THREE.Color(), bloom: .4, glow: 0, win: 1, grade: new THREE.Color(), vig: .4 };
  let target = presets.morning; Object.keys(cur).forEach(k => cur[k].copy ? cur[k].copy(target[k]) : cur[k] = target[k]);
  c.setTime = name => { if (presets[name]) target = presets[name]; };

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
  const k = (a, b, f) => a + (b - a) * f;
  return {
    update(t, dt) {
      const f = 1 - Math.exp(-dt * 3);
      for (const key of Object.keys(cur)) { if (cur[key].lerp) cur[key].lerp(target[key], f); else cur[key] = k(cur[key], target[key], f); }
      sun.color.copy(cur.sun); sun.intensity = cur.sunI; amb.color.copy(cur.amb); amb.intensity = cur.ambI;
      scene.background = cur.bg;
      c.sprites.forEach(m => m.color.copy(cur.tint));
      if (c.water) c.water.uniforms.uTint.value.copy(cur.water);
      c.glows.forEach(g => g.mat.opacity = 0.12 + cur.glow * 0.88);
      c.windows.forEach(w => w.mat.color.copy(w.base).multiplyScalar(cur.win));
      if (bloom) bloom.strength = cur.bloom;
      if (grade) { grade.uniforms.uTint.value.copy(cur.grade); grade.uniforms.uVig.value = cur.vig; }
    }
  };
};
