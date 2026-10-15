// 効果音はすべて数式で作っている（音のファイルは使わない）。
window.Snd = (function () {
  let ctx = null, master = null, muted = false, ambient = null;

  function init() {
    if (ctx) { if (ctx.state === "suspended") ctx.resume(); return; }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    ctx = new AC();
    master = ctx.createGain();
    master.gain.value = muted ? 0 : 0.7;
    master.connect(ctx.destination);
  }
  function ok() { return ctx && master; }

  function noiseBuf(dur) {
    const n = Math.floor(ctx.sampleRate * dur);
    const b = ctx.createBuffer(1, n, ctx.sampleRate);
    const d = b.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
    return b;
  }
  function tone(freq, start, dur, type, vol, slideTo) {
    const t = ctx.currentTime + start;
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type || "sine";
    o.frequency.setValueAtTime(freq, t);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(master);
    o.start(t); o.stop(t + dur + 0.05);
  }
  function burst(start, dur, vol, filterType, freq) {
    const t = ctx.currentTime + start;
    const s = ctx.createBufferSource(); s.buffer = noiseBuf(dur);
    const f = ctx.createBiquadFilter(); f.type = filterType; f.frequency.value = freq;
    const g = ctx.createGain();
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    s.connect(f); f.connect(g); g.connect(master);
    s.start(t);
  }

  const api = {
    init,
    click() { if (!ok()) return; burst(0, 0.03, 0.18, "highpass", 2500); tone(1400, 0, 0.03, "square", 0.02); },
    key() { if (!ok()) return; burst(0, 0.02, 0.10, "highpass", 1800); tone(220 + Math.random() * 40, 0, 0.04, "triangle", 0.03); },
    open() { if (!ok()) return; tone(420, 0, 0.12, "sine", 0.05, 640); },
    close() { if (!ok()) return; tone(520, 0, 0.1, "sine", 0.04, 330); },
    notify() { if (!ok()) return; tone(880, 0, 0.35, "sine", 0.09); tone(1175, 0.16, 0.5, "sine", 0.08); },
    approve() { if (!ok()) return; tone(660, 0, 0.3, "sine", 0.07); tone(990, 0.08, 0.4, "sine", 0.05); },
    reject() { if (!ok()) return; tone(110, 0, 0.35, "sine", 0.18, 55); burst(0, 0.12, 0.12, "lowpass", 500); },
    hold() { if (!ok()) return; tone(520, 0, 0.12, "triangle", 0.05); tone(520, 0.14, 0.12, "triangle", 0.05); },
    error() { if (!ok()) return; tone(150, 0, 0.18, "sawtooth", 0.05, 110); },
    found() { if (!ok()) return; tone(196, 0, 1.6, "sine", 0.08); tone(207.65, 0, 1.6, "sine", 0.07); tone(784, 0.05, 0.7, "sine", 0.03); },
    sting() { if (!ok()) return; tone(60, 0, 2.2, "sine", 0.16, 48); burst(0, 1.4, 0.05, "lowpass", 300); },
    login() { if (!ok()) return; tone(330, 0, 0.18, "sine", 0.05); tone(495, 0.14, 0.3, "sine", 0.05); },
    startAmbient() {
      if (!ok() || ambient) return;
      const s = ctx.createBufferSource(); s.buffer = noiseBuf(4); s.loop = true;
      const f = ctx.createBiquadFilter(); f.type = "lowpass"; f.frequency.value = 140;
      const g = ctx.createGain(); g.gain.value = 0.07;
      const hum = ctx.createOscillator(); hum.frequency.value = 50;
      const hg = ctx.createGain(); hg.gain.value = 0.012;
      s.connect(f); f.connect(g); g.connect(master);
      hum.connect(hg); hg.connect(master);
      s.start(); hum.start();
      ambient = { s, hum };
    },
    toggleMute() {
      muted = !muted;
      if (master) master.gain.value = muted ? 0 : 0.7;
      return muted;
    },
    isMuted() { return muted; }
  };
  return api;
})();
