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

  // ---- 本物らしくするための部品 ----
  // 部屋の響き（短い残響）。音を少しだけ混ぜると、「その場所で鳴っている」感じになる
  let room = null;
  function roomBus() {
    if (room) return room;
    const len = Math.floor(ctx.sampleRate * 0.9), ir = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let ch = 0; ch < 2; ch++) { const d = ir.getChannelData(ch); for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 3.2); }
    const cv = ctx.createConvolver(); cv.buffer = ir; const g = ctx.createGain(); g.gain.value = 0.55; cv.connect(g); g.connect(master);
    room = cv; return room;
  }
  // 出口：そのまま(dry)＋響き(wet)
  function wetDry(pan, wet) { const out = dest(pan); const g = ctx.createGain(); g.gain.value = 1; g.connect(out); if (wet) { const w = ctx.createGain(); w.gain.value = wet; g.connect(w); w.connect(roomBus()); } return g; }
  // 1サンプルずつ計算して作る音（きしみなど）
  function bufFrom(dur, fn) { const n = Math.floor(ctx.sampleRate * dur), b = ctx.createBuffer(1, n, ctx.sampleRate), d = b.getChannelData(0); fn(d, ctx.sampleRate, n); return b; }
  function playBuf(buf, out, start) { const s = ctx.createBufferSource(); s.buffer = buf; s.connect(out); s.start(ctx.currentTime + (start || 0)); return s; }
  // ピンクノイズ（ふつうのノイズより低い音が多く、息や風に近い）
  function pinkBuf(dur) {
    return bufFrom(dur, (d, sr, n) => { let b0 = 0, b1 = 0, b2 = 0; for (let i = 0; i < n; i++) { const w = Math.random() * 2 - 1; b0 = 0.99765 * b0 + w * 0.0990460; b1 = 0.96300 * b1 + w * 0.2965164; b2 = 0.57000 * b2 + w * 1.0526913; d[i] = (b0 + b1 + b2 + w * 0.1848) * 0.2; } });
  }
  // 共鳴つきの「カチッ」：とても短い音を、いくつかの細い共鳴（金属・木）に通す
  function resonantClick(out, start, freqs, q, vol, decay) {
    const t = ctx.currentTime + start, src = ctx.createBufferSource();
    src.buffer = bufFrom(0.004, (d, sr, n) => { for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / n); });
    const g = ctx.createGain(); g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(0.0001, t + (decay || 0.06));
    freqs.forEach(f => { const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = f; bp.Q.value = q; src.connect(bp); bp.connect(g); });
    g.connect(out); src.start(t);
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
    // 壁やドアを、こぶしで叩く「ドン、ドン…ドン」。低く重く、壁が少し響く。間隔は不規則で右のほうから
    knock() {
      if (!ok()) return; const out = wetDry(0.35, 0.35), times = [0, 0.42 + Math.random() * 0.06, 1.0 + Math.random() * 0.15];
      times.forEach((t, i) => {
        const v = i === 2 ? 1.15 : 1;
        toneTo(out, 115, t, 0.32, "sine", 0.42 * v, 48);                 // ドン（音の高さが一気に下がる）
        toneTo(out, 62, t, 0.45, "sine", 0.28 * v, 40);                  // 壁の低い響き
        burstTo(out, t, 0.11, 0.35 * v, "lowpass", 420);                 // こぶしが当たる鈍い音
        burstTo(out, t, 0.18, 0.12 * v, "bandpass", 170, 2.5);           // 板がふるえる
      });
    },
    // きしみ（ドア・床）：「ギ…ギィィ」。こすれが小さく引っかかるたびに、木が細く共鳴する（引っかかりの速さが、ゆっくり変わる）
    creak(low) {
      if (!ok()) return;
      const dur = 1.1 + Math.random() * 0.5, out = wetDry(low ? -0.3 : 0.3, 0.3);
      const buf = bufFrom(dur, (d, sr, n) => {
        let ph = 0, next = 0; const r0 = low ? 28 : 45, r1 = low ? 70 : 130;
        for (let i = 0; i < n; i++) {
          const u = i / n, rate = r0 + (r1 - r0) * Math.sin(Math.PI * Math.min(1, u * 1.3)) + Math.sin(u * 37) * 6;   // 引っかかりの速さ
          if (i >= next) { d[i] = (Math.random() < 0.85 ? 1 : 0.4) * (0.6 + Math.random() * 0.4); next = i + sr / Math.max(8, rate * (0.85 + Math.random() * 0.3)); } else d[i] = 0;
          d[i] *= Math.min(1, u * 8) * Math.min(1, (1 - u) * 5);
        }
      });
      const g = ctx.createGain(); g.gain.value = 0.9; g.connect(out);
      (low ? [380, 720, 1150] : [620, 1180, 1790, 2450]).forEach((f, k) => { const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = f; bp.Q.value = 28; const gg = ctx.createGain(); gg.gain.value = 1.6 / (k + 1); bp.connect(gg); gg.connect(g); const s = ctx.createBufferSource(); s.buffer = buf; s.connect(bp); s.start(); });
    },
    // 息：鼻から「スッ」と吸って、口から「はぁぁ…」と吐く。すぐ耳元（中央）。吐く息は「あ」の口の形の響き（ささやき声と同じ作り方）
    breath() {
      if (!ok()) return; const t = ctx.currentTime, out = wetDry(0, 0.08);
      const mk = (start, dur, bands, peak, peakAt, rise) => {
        const src = ctx.createBufferSource(); src.buffer = pinkBuf(dur + 0.1);
        const hp = ctx.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 220; src.connect(hp);
        const g = ctx.createGain(); g.gain.setValueAtTime(0.0001, t + start); g.gain.linearRampToValueAtTime(peak, t + start + dur * peakAt); g.gain.exponentialRampToValueAtTime(0.0001, t + start + dur);
        bands.forEach(([f, q, a]) => { const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.setValueAtTime(f, t + start); if (rise) bp.frequency.linearRampToValueAtTime(f * rise, t + start + dur); bp.Q.value = q; const ga = ctx.createGain(); ga.gain.value = a; hp.connect(bp); bp.connect(ga); ga.connect(g); });
        g.connect(out); src.start(t + start);
      };
      resonantClick(out, 0, [1800, 3200], 6, 0.05, 0.03);                                 // 口をあける小さな音
      mk(0.05, 0.7, [[2200, 4, 1.4], [3400, 5, 0.8], [900, 2, 0.5]], 0.5, 0.75, 1.12);    // 吸う（鼻・細く高い）
      mk(1.0, 1.4, [[720, 5, 1.5], [1220, 6, 1.0], [2600, 6, 0.5]], 0.55, 0.14, 0.92);   // 吐く（「はぁ」）
    },
    creakLow() { api.creak(true); },   // 床のきしみ（低め）
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
    // 置き時計の秒針：「チッ、タッ」（金属の小さな共鳴）。そのあと、逆回りに速く「チチチッ」
    tickBack() {
      if (!ok()) return; const out = wetDry(-0.15, 0.12);
      resonantClick(out, 0, [2650, 4100, 6800], 22, 0.55, 0.05);
      resonantClick(out, 1.0, [2350, 3700, 6100], 22, 0.5, 0.05);
      [1.55, 1.66, 1.77, 1.88].forEach((t, i) => resonantClick(out, t, [2900 + i * 120, 4500, 7200], 22, 0.45, 0.04));
    },
    // ドンと響く低い音（派手な演出用）。音量は控えめにしてある
    jolt() { if (!ok()) return; tone(52, 0, 0.7, "sine", 0.32, 28); tone(190, 0, 0.14, "sawtooth", 0.07, 70); burst(0, 0.3, 0.2, "lowpass", 900); },
    // 不協和音の短い一撃
    stinger() { if (!ok()) return; tone(466, 0, 0.5, "sawtooth", 0.05, 440); tone(493, 0, 0.5, "sawtooth", 0.05, 466); tone(65, 0, 0.8, "sine", 0.22, 40); burst(0, 0.18, 0.12, "highpass", 3000); },
    // 電気の不調（蛍光灯や配線がショートしかける音）：「ジッ…ジジジッ…ジッ」。ブーンという電気のうなりが、不規則に入ったり切れたりし、ときどきパチッと鳴る
    noise() {
      if (!ok()) return; const out = wetDry(0.2, 0.15), t = ctx.currentTime, dur = 0.85;
      const o = ctx.createOscillator(); o.type = "sawtooth"; o.frequency.value = 100;
      const o2 = ctx.createOscillator(); o2.type = "square"; o2.frequency.value = 150;
      const sh = ctx.createWaveShaper(); const c = new Float32Array(256); for (let i = 0; i < 256; i++) { const x = i / 128 - 1; c[i] = Math.tanh(x * 6); } sh.curve = c;
      const hp = ctx.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 350;
      const pk = ctx.createBiquadFilter(); pk.type = "peaking"; pk.frequency.value = 2800; pk.Q.value = 1; pk.gain.value = 9;
      const g = ctx.createGain(); g.gain.setValueAtTime(0, t);
      let x = 0; while (x < dur) { const on = 0.02 + Math.random() * 0.09, off = 0.02 + Math.random() * 0.12; g.gain.setValueAtTime(0.09 + Math.random() * 0.05, t + x); g.gain.setValueAtTime(0, t + x + on); x += on + off; }
      o.connect(sh); o2.connect(sh); sh.connect(hp); hp.connect(pk); pk.connect(g); g.connect(out);
      o.start(t); o2.start(t); o.stop(t + dur + 0.05); o2.stop(t + dur + 0.05);
      for (let i = 0; i < 4; i++) burstTo(out, Math.random() * dur, 0.004, 0.35, "highpass", 3000);   // パチッ
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
