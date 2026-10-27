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

  // 左右の位置（-1左〜1右）つきの出口
  function dest(p) { if (!p || !ctx.createStereoPanner) return master; const sp = ctx.createStereoPanner(); sp.pan.value = p; sp.connect(master); return sp; }
  function burstTo(out, start, dur, vol, filterType, freq, q) {
    const t = ctx.currentTime + start, src = ctx.createBufferSource(); src.buffer = noiseBuf(dur);
    const f = ctx.createBiquadFilter(); f.type = filterType; f.frequency.value = freq; if (q) f.Q.value = q;
    const g = ctx.createGain(); g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(f); f.connect(g); g.connect(out); src.start(t);
  }
  function toneTo(out, freq, start, dur, type, vol, slideTo) {
    const t = ctx.currentTime + start, o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type || "sine"; o.frequency.setValueAtTime(freq, t); if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t + dur);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + 0.006); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(out); o.start(t); o.stop(t + dur + 0.05);
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
    // 謎が解けた：鍵が開く「カチャ・カチッ」＋明るい「チン」
    found() { if (!ok()) return; burst(0, 0.02, 0.28, "highpass", 3500); burst(0.09, 0.02, 0.28, "highpass", 2800); tone(2200, 0.18, 0.45, "triangle", 0.06); tone(3300, 0.18, 0.3, "sine", 0.025); },
    sting() { if (!ok()) return; tone(60, 0, 2.2, "sine", 0.16, 48); burst(0, 1.4, 0.05, "lowpass", 300); },
    login() { if (!ok()) return; tone(330, 0, 0.18, "sine", 0.05); tone(495, 0.14, 0.3, "sine", 0.05); },
    // 部屋の音：PCのファン（やわらかいノイズ）と、冷蔵庫のようなごく小さなブーン。ずっと鳴っているが、止めると「静けさ」になる
    startAmbient() {
      if (!ok() || ambient) return;
      const s = ctx.createBufferSource(); s.buffer = noiseBuf(4); s.loop = true;
      const f = ctx.createBiquadFilter(); f.type = "lowpass"; f.frequency.value = 330;
      const g = ctx.createGain(); g.gain.value = 0.034;
      const hum = ctx.createOscillator(); hum.frequency.value = 100; const hum2 = ctx.createOscillator(); hum2.frequency.value = 150;
      const hg = ctx.createGain(); hg.gain.value = 0.006;
      s.connect(f); f.connect(g); g.connect(master); hum.connect(hg); hum2.connect(hg); hg.connect(master);
      s.start(); hum.start(); hum2.start();
      ambient = { s, hum, hum2, g, f, hg };
    },
    stopAmbient(fade) {
      if (!ambient) return;
      const a = ambient, t = ctx.currentTime, d = fade == null ? 0.5 : fade;
      a.g.gain.cancelScheduledValues(t); a.g.gain.setValueAtTime(a.g.gain.value, t); a.g.gain.linearRampToValueAtTime(0.0001, t + d);
      a.hg.gain.cancelScheduledValues(t); a.hg.gain.setValueAtTime(a.hg.gain.value, t); a.hg.gain.linearRampToValueAtTime(0.0001, t + d);
      ambient = null; setTimeout(() => { try { a.s.stop(); a.hum.stop(); a.hum2.stop(); } catch (e) {} }, d * 1000 + 100);
    },
    // 日が進むほど、環境音が少しだけ低く・大きくなる
    setDay(d) {
      if (!ambient) return;
      const t = ctx.currentTime + 1.5;
      ambient.g.gain.linearRampToValueAtTime(0.03 + 0.005 * d, t);
      ambient.f.frequency.linearRampToValueAtTime(340 - 20 * d, t);
      ambient.hg.gain.linearRampToValueAtTime(0.005 + 0.002 * d, t);
    },
    // 壁（木）を叩く音：コン・コン…コン。間隔は不規則で、右のほうから聞こえる
    knock() {
      if (!ok()) return; const out = dest(0.45), gap = 0.5 + Math.random() * 0.12;
      [0, 0.28, gap].forEach(t => { burstTo(out, t, 0.06, 0.34, "bandpass", 250, 4); toneTo(out, 150, t, 0.09, "sine", 0.26, 95); });
    },
    // きしみ：引っかかっては滑る低い音（不規則に揺れるパルス列をバンドパスで細くする）
    creak(low) {
      if (!ok()) return;
      const t = ctx.currentTime, dur = 0.7 + Math.random() * 0.5, o = ctx.createOscillator(), f = ctx.createBiquadFilter(), g = ctx.createGain();
      o.type = "square"; o.frequency.setValueAtTime(40, t);
      for (let x = 0; x < dur; x += 0.045) o.frequency.setValueAtTime(22 + Math.random() * 50, t + x);
      f.type = "bandpass"; f.Q.value = 12; f.frequency.setValueAtTime(low ? 480 : 850, t); f.frequency.linearRampToValueAtTime(low ? 560 : 1050, t + dur);
      g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.16, t + 0.12); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(f); f.connect(g); g.connect(master); o.start(t); o.stop(t + dur + 0.05);
    },
    // 息：吸う→間→吐く。すぐ後ろで誰かが息をしている（中央・近い）
    breath() {
      if (!ok()) return; const t = ctx.currentTime;
      const mk = (start, dur, f0, f1, peak, peakAt) => {
        const src = ctx.createBufferSource(); src.buffer = noiseBuf(dur + 0.1);
        const f = ctx.createBiquadFilter(); f.type = "lowpass"; f.frequency.setValueAtTime(f0, t + start); f.frequency.linearRampToValueAtTime(f1, t + start + dur);
        const g = ctx.createGain(); g.gain.setValueAtTime(0.0001, t + start); g.gain.linearRampToValueAtTime(peak, t + start + dur * peakAt); g.gain.exponentialRampToValueAtTime(0.0001, t + start + dur);
        src.connect(f); f.connect(g); g.connect(master); src.start(t + start);
      };
      mk(0, 0.85, 500, 900, 0.1, 0.8);       // 吸う（だんだん大きく・高く）
      mk(1.05, 1.2, 900, 380, 0.13, 0.18);   // 吐く（はじめが強く、だんだん低く・弱く）
    },
    whisper() { api.breath(); },   // 古い名前。息に置き換えた
    // 足音：ドスッ…ドスッ。n回、だんだん近く・大きく（左→中央）
    footstep(pan, vol) { if (!ok()) return; const o = dest(pan || 0), v = vol == null ? 1 : vol; burstTo(o, 0, 0.07, 0.24 * v, "lowpass", 280); toneTo(o, 72, 0, 0.06, "sine", 0.2 * v, 50); },
    footsteps(n) { if (!ok()) return; let t = 0; for (let i = 0; i < (n || 4); i++) { const k = i, pn = (n || 4) - 1 || 1; setTimeout(() => api.footstep(-0.7 + 0.7 * k / pn, 0.35 + 0.65 * k / pn), t * 1000); t += 0.55 + Math.random() * 0.2; } },
    // 机の上のスマホが震える：ブブッ、ブブッ（右）
    vibrate() {
      if (!ok()) return; const t = ctx.currentTime, o = ctx.createOscillator(), f = ctx.createBiquadFilter(), g = ctx.createGain(), out = dest(0.7);
      o.type = "square"; o.frequency.value = 150; f.type = "lowpass"; f.frequency.value = 420;
      g.gain.setValueAtTime(0.0001, t);
      [0, 0.55].forEach(b => { for (let k = 0; k < 10; k++) { g.gain.setValueAtTime(k % 2 ? 0.01 : 0.1, t + b + k * 0.04); } g.gain.setValueAtTime(0.0001, t + b + 0.4); });
      o.connect(f); f.connect(g); g.connect(out); o.start(t); o.stop(t + 1.1);
      burstTo(out, 0, 0.1, 0.1, "lowpass", 600); burstTo(out, 0.55, 0.1, 0.1, "lowpass", 600);
    },
    relayClick() { if (!ok()) return; burst(0, 0.012, 0.32, "highpass", 4000); tone(300, 0, 0.03, "square", 0.04); },
    recBeep() { if (!ok()) return; tone(1000, 0, 0.12, "sine", 0.06); },
    // 時計の秒針：コチ、カチ…のあと、逆回りに速く3回
    tickBack() {
      if (!ok()) return;
      [[0, 3000], [0.45, 2400]].forEach(([t, fq]) => { burst(t, 0.02, 0.2, "highpass", fq); tone(fq * 0.6, t, 0.03, "square", 0.03); });
      [0.95, 1.03, 1.11].forEach((t, i) => { burst(t, 0.02, 0.2, "highpass", 3200 - i * 500); tone(1800 - i * 350, t, 0.03, "square", 0.03); });
    },
    // ドンと響く低い音（派手な演出用）。音量は控えめにしてある
    jolt() { if (!ok()) return; tone(52, 0, 0.7, "sine", 0.32, 28); tone(190, 0, 0.14, "sawtooth", 0.07, 70); burst(0, 0.3, 0.2, "lowpass", 900); },
    // 不協和音の短い一撃
    stinger() { if (!ok()) return; tone(466, 0, 0.5, "sawtooth", 0.05, 440); tone(493, 0, 0.5, "sawtooth", 0.05, 466); tone(65, 0, 0.8, "sine", 0.22, 40); burst(0, 0.18, 0.12, "highpass", 3000); },
    // 電気の不調「ジジッ…ジッ」：高いパルスが不規則に並び、50Hzのブーンが少し持ち上がる（画面の帯と同時に鳴らす）
    noise() {
      if (!ok()) return; const n = 9 + Math.floor(Math.random() * 7);
      for (let i = 0; i < n; i++) burst(Math.random() * 0.45, 0.003, 0.16 + Math.random() * 0.1, "highpass", 4000 + Math.random() * 2500);
      tone(50, 0, 0.4, "sawtooth", 0.05); tone(100, 0, 0.3, "sawtooth", 0.025);
    },
    // 鼓動
    // 鼓動：ドクン…ドクン（1拍は2つの音。間隔はだんだん縮む）
    heartbeat() { if (!ok()) return; [0, 0.9, 1.7, 2.4].forEach(t => { burst(t, 0.09, 0.2, "lowpass", 150); tone(60, t, 0.09, "sine", 0.22, 45); burst(t + 0.25, 0.08, 0.12, "lowpass", 150); tone(58, t + 0.25, 0.08, "sine", 0.13, 44); }); },
    toggleMute() {
      muted = !muted;
      if (master) master.gain.value = muted ? 0 : 0.7;
      return muted;
    },
    isMuted() { return muted; }
  };
  return api;
})();
