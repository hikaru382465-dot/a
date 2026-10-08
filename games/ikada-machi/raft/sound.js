// 効果音：ブラウザの中で音を作る（ファイルなし。権利の心配がない）。画面を最初に触ったときから鳴る
window.RAFT.parts.sound = function (c) {
  const { state: s } = c;
  let ctx = null, master = null, nbuf = null, amb = null, rain = null, swish = null, muted = false;
  try { muted = localStorage.getItem('ikada-mute') === '1'; } catch (e) {}
  const btn = document.getElementById('bSound');
  const label = () => { if (btn) { btn.textContent = muted ? '音 OFF' : '音 ON'; btn.classList.toggle('on', !muted); } };
  label();
  if (btn) btn.onclick = () => { muted = !muted; try { localStorage.setItem('ikada-mute', muted ? '1' : '0'); } catch (e) {} if (master) master.gain.value = muted ? 0 : 0.6; label(); start(); };

  function loop(type, f, q, gain) {
    const src = ctx.createBufferSource(); src.buffer = nbuf; src.loop = true;
    const fl = ctx.createBiquadFilter(); fl.type = type; fl.frequency.value = f; fl.Q.value = q;
    const g = ctx.createGain(); g.gain.value = gain; src.connect(fl); fl.connect(g); g.connect(master); src.start(); return g;
  }
  function start() {
    try {
      if (ctx) { if (ctx.state === 'suspended') ctx.resume(); return; }
      const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
      ctx = new AC(); master = ctx.createGain(); master.gain.value = muted ? 0 : 0.6; master.connect(ctx.destination);
      nbuf = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate); const d = nbuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
      amb = loop('lowpass', 520, 0.7, 0.08);                      // 波の音（ゆっくり大きくなったり小さくなったり）
      const lfo = ctx.createOscillator(), lg = ctx.createGain(); lfo.frequency.value = 0.13; lg.gain.value = 0.035; lfo.connect(lg); lg.connect(amb.gain); lfo.start();
      rain = loop('highpass', 2600, 0.5, 0);                      // 雨
      swish = loop('bandpass', 750, 0.9, 0);                      // 網を引きずる音
    } catch (e) { ctx = null; }
  }
  ['pointerdown', 'keydown', 'touchstart'].forEach(ev => addEventListener(ev, start, { passive: true }));

  const env = (g, t0, a, d, peak) => { g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(peak, t0 + a); g.gain.exponentialRampToValueAtTime(0.0001, t0 + a + d); };
  function noise(t0, dur, type, f0, f1, peak, q) {
    const src = ctx.createBufferSource(); src.buffer = nbuf; const f = ctx.createBiquadFilter(); f.type = type; f.Q.value = q || 1;
    f.frequency.setValueAtTime(f0, t0); f.frequency.exponentialRampToValueAtTime(f1, t0 + dur);
    const g = ctx.createGain(); env(g, t0, 0.02, dur, peak); src.connect(f); f.connect(g); g.connect(master); src.start(t0, Math.random()); src.stop(t0 + dur + 0.1);
  }
  function tone(t0, f0, f1, dur, type, peak) {
    const o = ctx.createOscillator(); o.type = type; o.frequency.setValueAtTime(f0, t0); o.frequency.exponentialRampToValueAtTime(f1, t0 + dur);
    const g = ctx.createGain(); env(g, t0, 0.01, dur, peak); o.connect(g); g.connect(master); o.start(t0); o.stop(t0 + dur + 0.05);
  }
  const play = {
    throw: t => noise(t, 0.35, 'bandpass', 300, 1800, 0.35, 1.2),
    splash: t => { noise(t, 0.6, 'lowpass', 3200, 300, 0.5); [0.05, 0.12, 0.2].forEach((o, i) => tone(t + o, 300 + Math.random() * 300, 700 + Math.random() * 500, 0.1, 'sine', 0.12 - i * 0.02)); },
    caught: t => tone(t, 520, 880, 0.12, 'sine', 0.25),
    haul: t => { tone(t, 660, 660, 0.22, 'triangle', 0.22); tone(t + 0.09, 880, 880, 0.26, 'triangle', 0.22); },
    empty: t => tone(t, 220, 170, 0.2, 'sine', 0.2),
    eat: t => tone(t, 180, 120, 0.18, 'sine', 0.3),
    drink: t => { noise(t, 0.25, 'lowpass', 1200, 500, 0.25); tone(t + 0.05, 200, 130, 0.12, 'sine', 0.25); tone(t + 0.16, 190, 120, 0.12, 'sine', 0.25); },
    built: t => { tone(t, 140, 90, 0.12, 'square', 0.22); tone(t + 0.1, 150, 95, 0.12, 'square', 0.22); },
    netlv: t => [523, 659, 784, 1047].forEach((f, i) => tone(t + i * 0.09, f, f, 0.22, 'sine', 0.22)),
    equip: t => tone(t, 900, 1200, 0.06, 'square', 0.1),
    no: t => tone(t, 220, 160, 0.15, 'sawtooth', 0.1),
    thunder: t => noise(t, 1.6, 'lowpass', 420, 60, 0.6)
  };
  const map = { throw: 'throw', splash: 'splash', caught: 'caught', haul: 'haul', empty: 'empty', eat: 'eat', drink: 'drink', built: 'built', netlv: 'netlv', equip: 'equip', noequip: 'no', short: 'no', miss: 'no', material: 'equip' };
  c.sfx = {
    probe: () => ({ ctx, master }),
    onEvent(e) {
      if (!ctx || muted) return;
      const k = e.e === 'weather' ? (e.id === 'storm' ? 'thunder' : null) : map[e.e];
      if (k && play[k]) play[k](ctx.currentTime + 0.01);
    }
  };
  const T = { sunny: [0.09, 0], calm: [0.05, 0], storm: [0.2, 0.12] };
  return { update() {
    if (!ctx) return; const w = T[s.weather.id] || T.sunny, now = ctx.currentTime;
    amb.gain.setTargetAtTime(w[0], now, 0.8); rain.gain.setTargetAtTime(w[1], now, 0.8);
    swish.gain.setTargetAtTime(s.net.cast && s.net.cast.phase === 'back' ? 0.22 : 0, now, 0.08);
  } };
};
