// ギミック（画面の中の小さな異変）。いつから起きるかは data.js の gimmicks で決める。
// URLに ?nogimmick を付けると全部止まる。開発用：__game.fire("swap") などで1つだけ起こせる。
window.Gimmicks = (function () {
  let api = null, active = false, timers = [], zeroDone = {};
  const day = () => api.state().day;
  const on = name => active && day() >= (api.D.gimmicks[name] || 99);
  const later = (fn, ms) => { const t = setTimeout(() => { if (active || forced) fn(); }, ms); timers.push(t); return t; };
  function every(name, minMs, maxMs, fn) {
    (function loop() { later(() => { if (on(name)) fn(); loop(); }, minMs + Math.random() * (maxMs - minMs)); })();
  }
  const baseTitle = document.title;

  // ===== 派手な演出の部品（強さは data.js の fxLevel：0なし／1小／2中／3派手）=====
  // 光の点滅は1秒に3回未満・白ではなく暗い色か赤だけ。「動きを減らす」設定のときは、画面の揺れ・光は出さず音だけにする。
  const REDUCE = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const LV = () => Math.max(0, Math.min(3, api.D.fxLevel == null ? 3 : api.D.fxLevel));
  const K = () => [0, 0.45, 0.75, 1][LV()];
  let forced = false;   // エンディング中は、ギミックを止めたままでも演出だけ使えるようにする
  const fxOn = () => (active || forced) && LV() > 0 && !REDUCE;
  const deskEl = () => document.querySelector("#screen-desk");
  function overlay(cls, ms, text) {
    const d = document.createElement("div"); d.className = "fx " + cls; if (text) d.textContent = text;
    document.body.append(d); setTimeout(() => d.remove(), ms); return d;
  }
  // 揺れ：最初に強く、だんだん弱く。向きと速さは不規則で、なめらかに追いかける。少し回り、速いときはほんのりぼける
  let shakeRaf = 0;
  function shake(ms, strong) {
    if (!fxOn()) return;
    const el = deskEl(), amp = (strong ? 16 : 7) * K(), t0 = performance.now();
    cancelAnimationFrame(shakeRaf);
    let tx = 0, ty = 0, tr = 0, cx = 0, cy = 0, cr = 0, next = 0;
    (function f(now) {
      const t = now - t0;
      if (t >= ms) { el.style.transform = ""; el.style.filter = ""; return; }
      const decay = Math.pow(1 - t / ms, 2.2);
      if (now >= next) { tx = Math.random() * 2 - 1; ty = Math.random() * 2 - 1; tr = Math.random() * 2 - 1; next = now + 30 + Math.random() * 35; }
      cx += (tx - cx) * 0.45; cy += (ty - cy) * 0.45; cr += (tr - cr) * 0.35;
      el.style.transform = "scale(1.015) translate(" + (cx * amp * decay).toFixed(2) + "px," + (cy * amp * 0.6 * decay).toFixed(2) + "px) rotate(" + (cr * 0.32 * decay * K()).toFixed(3) + "deg)";
      const v = Math.abs(cx - tx) * decay * amp;
      el.style.filter = v > 4 ? "blur(" + Math.min(1.1, v * 0.07).toFixed(2) + "px)" : "";
      shakeRaf = requestAnimationFrame(f);
    })(t0);
  }
  function glitch(ms) {
    if (!fxOn() || LV() < 2) return;
    const el = document.querySelector("#desktop"); el.classList.add("fx-glitch"); setTimeout(() => el.classList.remove("fx-glitch"), ms);
  }
  function redPulse(ms) { if (fxOn()) overlay("fx-red", ms || 900); }
  function blackout(times) {   // 明かりが一瞬消える（最大2回・0.35秒おき）
    if (!fxOn() || LV() < 2) return;
    for (let i = 0; i < Math.min(times || 1, 2); i++) setTimeout(() => overlay("fx-dark", 160), i * 350);
  }
  // 大きな文字：暗がりの中に、くすんだ赤の細い明朝体。ぼけた状態から現れ、一度かすれてから消える（ベタ塗りの赤は使わない）
  function bigText(text, ms) {
    if (!fxOn() || LV() < 2) return;
    const dur = (ms || 700) + 300, o = overlay("fx-big2", dur + 100);
    o.style.animationDuration = dur + "ms";
    const s = document.createElement("span"); s.textContent = text; s.setAttribute("data-t", text); s.style.animationDuration = dur + "ms";
    s.style.marginLeft = (Math.random() * 14 - 7) + "vw"; s.style.marginTop = (Math.random() * 8 - 4) + "vh";
    o.append(s);
    const t0 = performance.now();      // 出たあとも、1〜2pxだけ不規則に震える
    (function jit(now) { if (!s.isConnected) return; const a = (now - t0) < 160 ? 5 : 1.6;
      s.style.translate = ((Math.random() - .5) * a * 2).toFixed(1) + "px " + ((Math.random() - .5) * a).toFixed(1) + "px"; requestAnimationFrame(jit); })(t0);
  }

  // ノイズ：アナログテレビの「走る帯」。canvasで毎フレーム描く。帯の縁はやわらかく、行ごとに明るさが違い、ときどき白い筋が走り、色のちらつきがある。
  function noiseSweep() {
    api.S.noise(); [0, 140, 330].forEach(ms => setTimeout(() => api.S.click(), ms));
    if (!fxOn()) return;
    const W = 320, H = 180, cv = document.createElement("canvas"); cv.width = W; cv.height = H; cv.className = "fx fx-noise2";
    document.body.append(cv);
    const x = cv.getContext("2d"), img = x.createImageData(W, H), d = img.data, dur = 1500, t0 = performance.now(), dk = document.querySelector("#desktop");
    const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2, clamp = v => Math.max(0, Math.min(1, v));
    const bands = [{ h: H * (0.2 + Math.random() * 0.08), a: 0, b: 1 }, { h: H * 0.09, a: 0.22 + Math.random() * 0.1, b: 0.9 }];
    const rowMul = new Float32Array(H), rowStreak = new Int16Array(H * 2);
    (function f(now) {
      const t = (now - t0) / dur;
      if (t >= 1) { cv.remove(); dk.style.transform = ""; dk.style.filter = ""; return; }
      let inBand = false, gain = 0;
      const cys = bands.map(bd => { const p = ease(clamp((t - bd.a) / (bd.b - bd.a))); return p * (H + bd.h) - bd.h * 0.5 + (Math.random() - .5) * 3; });
      const k = K() * Math.sin(Math.PI * Math.min(1, t * 1.1));
      for (let r = 0; r < H;) { const run = 1 + Math.floor(Math.random() * 5), m = 0.25 + Math.random() * 0.75, st = Math.random() < 0.05; for (let q = 0; q < run && r < H; q++, r++) { rowMul[r] = m; rowStreak[r * 2] = st ? Math.floor(Math.random() * W * .6) : 0; rowStreak[r * 2 + 1] = st ? rowStreak[r * 2] + 40 + Math.floor(Math.random() * 120) : 0; } }
      for (let yy = 0; yy < H; yy++) {
        let edge = 0;
        bands.forEach((bd, i) => { const dist = Math.abs(yy - cys[i]) / (bd.h / 2); if (dist < 1) edge = Math.max(edge, Math.pow(1 - dist, 1.6) * (i ? 0.8 : 1)); });
        if (edge > 0.6) inBand = true; gain = Math.max(gain, edge);
        const a0 = Math.max(edge * 0.85 * k, 0.045 * k);
        for (let xx = 0; xx < W; xx++) {
          const i = (yy * W + xx) * 4, n = Math.random() * 255 * rowMul[yy];
          let rr = n, gg = n, bb = n;
          if (rowStreak[yy * 2] && xx > rowStreak[yy * 2] && xx < rowStreak[yy * 2 + 1]) rr = gg = bb = 235;
          if (edge > 0.3 && Math.random() < 0.012) { rr = 230; gg = 150 + Math.random() * 60; bb = 150; }    // ごく弱い色のちらつき
          d[i] = rr; d[i + 1] = gg; d[i + 2] = bb; d[i + 3] = Math.min(255, a0 * 255 * (edge > 0 ? 1 : 0.4));
        }
      }
      cys.forEach((cy, i) => { const ly = Math.round(cy - bands[i].h / 2); if (ly >= 0 && ly < H) for (let xx = 0; xx < W; xx++) { const j = (ly * W + xx) * 4; d[j] = d[j + 1] = d[j + 2] = 220; d[j + 3] = 120 * k; } });
      x.putImageData(img, 0, 0);
      // 帯が通る間、画面全体が左右にずれ・色が分かれ・明るさがちらつく
      if (inBand) { const sx = (Math.random() - .5) * 2 * 12 * k * gain; dk.style.transform = "translate(" + sx.toFixed(1) + "px," + ((Math.random() - .5) * 2.4).toFixed(1) + "px)";
        dk.style.filter = "drop-shadow(" + (3 * gain).toFixed(1) + "px 0 rgba(255,40,40,.55)) drop-shadow(" + (-3 * gain).toFixed(1) + "px 0 rgba(40,190,255,.45)) brightness(" + (1 + 0.15 * gain * Math.random()).toFixed(2) + ")"; }
      else { dk.style.transform = ""; dk.style.filter = ""; }
      requestAnimationFrame(f);
    })(t0);
  }

  // 壁紙の家の窓に、人影が一瞬だけ立つ（Blender版の壁紙のとき）。
  // 流れ：窓の明かりがつく→奥にぼんやり小さな人影→窓ぎわまで来る→消える。窓が隠れないよう、開いている窓は先にいったん消える。
  let figBusy = false; const figReady = {};
  // 人影の絵は、先に読み込んで解読しておく（初回に一瞬、背景が真っ暗になるのを防ぐ）
  function preloadFigure(wp) {
    const key = wp.className.replace(/\bfig\d?\b/g, "").trim();
    if (figReady[key]) return figReady[key];
    const urls = [], keep = wp.className;
    ["fig0", "fig1", "fig"].forEach(c => {
      wp.className = key + " " + c;
      const m = /url\("?([^")]+)"?\)/.exec(getComputedStyle(wp).backgroundImage); if (m) urls.push(m[1]);
    });
    wp.className = keep;
    figReady[key] = Promise.all(urls.map(src => { const im = new Image(); im.src = src; return im.decode ? im.decode().catch(() => {}) : Promise.resolve(); }));
    return figReady[key];
  }
  function windowFigure() {
    const wp = document.querySelector("#wallpaper");
    if (figBusy || !wp || !/\bb\b/.test(wp.className)) return;
    figBusy = true;
    preloadFigure(wp).then(() => {
      const w = api.wins(), hidden = Object.keys(w).filter(k => !w[k].min);
      const hide = LV() >= 2, t = hide ? 380 : 0;
      api.S.creak();
      if (hide) { api.S.jolt(); shake(380, true); hidden.forEach(k => { w[k].el.style.display = "none"; }); }
      const set = c => { wp.classList.remove("fig0", "fig1", "fig"); if (c) wp.classList.add(c); };
      later(() => set("fig0"), t);                 // 窓に明かりがつく
      later(() => set(null), t + 170);              // 一度消える（ちらつき）
      later(() => set("fig0"), t + 340);
      later(() => { set("fig1"); api.S.footsteps(3); }, t + 640);            // 奥に、ぼんやり小さく（足音）
      later(() => { set("fig"); api.S.breath(); }, t + 1000);   // 窓ぎわまで来る（息）
      later(() => set(null), t + 1550);
      setTimeout(() => {
        set(null);
        hidden.forEach(k => { if (w[k] && !w[k].min) w[k].el.style.display = "flex"; });
        figBusy = false;
      }, t + 1800);
    });
  }
  function whisperText(text) {
    if (!fxOn()) return;
    overlay("fx-sub", 2600, text);
  }

  function bind(a) {
    api = a;
    document.addEventListener("visibilitychange", () => {
      if (!active || !on("title")) { document.title = baseTitle; return; }
      document.title = document.hidden ? "…まだ、見ている" : baseTitle;
    });
  }
  function start() {
    stop();
    if (location.search.includes("nogimmick")) return;
    active = true; zeroDone = {};
    every("silentNotify", 70000, 130000, () => { api.S.vibrate(); if (fxOn()) overlay("fx-vib", 1300, "📱"); });
    every("title", 50000, 90000, titleBlip);
    every("clock", 45000, 80000, clockGlitch);
    every("windowReturn", 40000, 90000, windowReturn);
    every("windowNudge", 25000, 45000, windowNudge);
    every("ambientEvent", 35000, 75000, ambientEvent);
    every("bigFlash", 110000, 190000, bigFlash);
    every("noise", 60000, 110000, noiseSweep);
    every("windowFigure", 150000, 260000, windowFigure);
    later(() => { const wp = document.querySelector("#wallpaper"); if (wp && /\bb\b/.test(wp.className)) preloadFigure(wp); }, 3000);
  }
  function stop() {
    active = false; timers.forEach(clearTimeout); timers = [];
    document.title = baseTitle;
  }

  // 1. 未審査の数がずれる（実際より1多く見える）／3日目からは、0件になった直後に「1件」と出る
  function shownPending(n) { return on("pendingOff") && n > 0 ? n + 1 : n; }
  function zeroTrick(textEl, badgeEl) {
    if (!on("pendingOff") || day() < 4 || zeroDone[day()]) return;
    zeroDone[day()] = true;
    textEl.textContent = "未審査：1件"; textEl.classList.add("fx-redtext");
    if (badgeEl) { badgeEl.textContent = "1"; badgeEl.style.display = ""; badgeEl.classList.add("fx-badgepulse"); }
    api.S.error(); api.S.jolt(); shake(380); redPulse(700);
    later(() => { textEl.textContent = "未審査：なし"; textEl.classList.remove("fx-redtext"); if (badgeEl) { badgeEl.style.display = "none"; badgeEl.classList.remove("fx-badgepulse"); } }, 2600);
  }

  // 2. 読んでいる最中に、本文の1語が変わる
  const SWAPS = [["私", "あなた"], ["ひとり", "ふたり"], ["友人", "あなた"], ["誰も", "あなたが"], ["一枚", "二枚"],
    ["理由を、教えてください。", "理由は、あなたが知っています。"], ["まだ、届いていませんか。", "もう、届いていますよね。"]];
  let swapTimer = null;
  function doSwap(e, bodyEl, times) {
    let done = 0;
    const list = (api.D.swaps[e.base] || []).concat(SWAPS);
    for (let i = 1; i < e.body.length && done < times; i++) {
      for (const [from, to] of list) {
        if (e.body[i].includes(from)) {
          e.body[i] = e.body[i].replace(from, to);
          const p = bodyEl.querySelectorAll("p")[i]; if (p) { p.textContent = e.body[i]; p.classList.add("fx-swapped"); setTimeout(() => p.classList.remove("fx-swapped"), 3200); }
          done++; break;
        }
      }
    }
    if (done) { e.swapped = true; api.save(); api.S.stinger(); shake(420, true); glitch(500); redPulse(900); }
    return done;
  }

  // 9. 読む前に、ある段落だけがうっすら光る
  const GLOW_WORDS = ["あなた", "今日", "二時", "明日", "部屋", "いま", "今夜"];

  // 詳細画面が描かれるたびに呼ばれる
  function onDetail(e, c) {
    clearTimeout(swapTimer);
    if (api.tab() !== "today") return;
    if (on("swap") && !e.swapped) {
      swapTimer = setTimeout(() => {
        if (active && c.bodyEl.isConnected && api.selId() === e.eid) doSwap(e, c.bodyEl, day() >= 4 ? 2 : 1);
      }, 11000 + Math.random() * 5000);
      timers.push(swapTimer);
    }
    if (on("glow")) {
      const ps = [...c.bodyEl.querySelectorAll("p")];
      const target = ps.find((p, i) => i > 0 && GLOW_WORDS.some(w => p.textContent.includes(w))) || (e.last ? ps[0] : null);
      if (target) later(() => { if (target.isConnected) target.classList.add("glow"); }, 6000);
    }
    // 4. 承認ボタンが逃げる
    if (on("flee") && c.bApprove) {
      let fled = 0; const max = e.last ? 2 : 1;
      c.bApprove.addEventListener("pointerenter", () => {
        if (fled >= max || (!e.last && Math.random() < 0.5)) return;
        fled++;
        const big = LV() >= 2, dx = (Math.random() < 0.5 ? -1 : 1) * (big ? 110 + Math.random() * 80 : 30 + Math.random() * 20);
        c.bApprove.style.transition = "transform .12s";
        c.bApprove.style.transform = "translate(" + dx + "px," + (big ? -40 : -6) + "px) rotate(" + (big ? dx / 12 : 0) + "deg)";
        api.S.error(); shake(250);
        setTimeout(() => { c.bApprove.style.transform = ""; }, big ? 1500 : 1100);
      });
    }
    // 5. 最後の投稿で「承認」の文字が「あなた」に変わる
    if (on("buttonLabel") && e.last && c.bApprove) {
      later(() => { if (c.bApprove.isConnected) { c.bApprove.textContent = "あなた"; c.bApprove.classList.add("fx-redbtn"); api.S.heartbeat(); api.S.jolt(); shake(500, true); redPulse(1400); bigText("あなた", 900); } }, 5000);
    }
  }

  // 3. 閉じたメモが勝手に戻る／最小化した窓が戻る
  function windowReturn() {
    const w = api.wins();
    Object.keys(w).forEach(k => { if (w[k].min) { w[k].min = false; w[k].el.style.display = "flex"; } });
    if (!w.memo && Math.random() < 0.6) {
      api.openMemo(); api.S.creak(); api.S.jolt(); shake(500, true); blackout(1);
      const m = api.wins().memo;
      if (m) { m.el.style.zIndex = 3; m.el.classList.add("inactive"); m.tb.classList.remove("active"); }
    }
  }
  // 3'. 窓が少しだけずれる
  function windowNudge() {
    const w = api.wins(), ks = Object.keys(w).filter(k => !w[k].min);
    if (!ks.length) return;
    const el = w[ks[Math.floor(Math.random() * ks.length)]].el;
    const m = LV() >= 2 ? 6 : 1;
    const dx = (Math.random() < 0.5 ? -1 : 1) * (5 + Math.random() * 5) * m;
    const dy = (Math.random() < 0.5 ? -1 : 1) * (3 + Math.random() * 4) * m;
    api.S.knock(); shake(300);
    el.style.transition = "left .12s, top .12s";
    el.style.left = Math.max(0, el.offsetLeft + dx) + "px"; el.style.top = Math.max(0, el.offsetTop + dy) + "px";
    setTimeout(() => { el.style.transition = ""; }, 250);
  }

  // 10. 環境の音：壁をたたく／きしむ／ささやき（5日目は鼓動も）
  function ambientEvent() {
    const S = api.S, pool = ["knock", "footsteps", "breath", "vibrate"];
    if (day() >= 5) pool.push("heartbeat", "heartbeat");
    const k = pool[Math.floor(Math.random() * pool.length)];
    // どの音にも、画面で見える「原因」を合わせる：叩く→揺れ／足音→暗がり／息→画面が曇る／スマホ→📱が震える／鼓動→縁が赤く脈打つ
    if (k === "knock") { S.knock(); setTimeout(() => shake(200, true), 5); setTimeout(() => shake(160), 280); redPulse(600); }
    else if (k === "footsteps") { S.footsteps(4); blackout(1); }
    else if (k === "breath") { S.breath(); if (fxOn()) overlay("fx-fog", 2300); whisperText("…"); }
    else if (k === "vibrate") { S.vibrate(); if (fxOn()) overlay("fx-vib", 1300, "📱"); }
    else { S.heartbeat(); [0, 900, 1700, 2400].forEach(ms => setTimeout(() => { redPulse(800); shake(200); }, ms)); }
  }
  // 11. 画面いっぱいの文字が、一瞬だけ出る（3日目から。音つき）
  function bigFlash() {
    const words = day() >= 5 ? ["あなた", "02:41", "うしろ"] : ["みている", "うしろ", "02:41"];
    api.S.stinger(); shake(500, true); redPulse(1000); bigText(words[Math.floor(Math.random() * words.length)], 650);
  }

  // 6. ブラウザの題名が一瞬変わる
  function titleBlip() {
    document.title = day() >= 4 ? "02:41" : "みている";
    setTimeout(() => { document.title = baseTitle; }, 1100);
  }

  // 7. 時計が1分戻る・4日目は02:41で止まる
  function clockText(t) { return active && day() >= 5 ? "02:41" : t; }
  async function clockGlitch() {
    const el = api.clockEl(), m = api.clockMin();
    const f = x => String(Math.floor(x / 60) % 24).padStart(2, "0") + ":" + String(x % 60).padStart(2, "0");
    api.S.tickBack(); glitch(600); blackout(1); shake(300); if (LV() >= 2) noiseSweep();
    el.classList.add("flick");
    el.textContent = f(m - 1); await new Promise(r => setTimeout(r, 800));
    el.textContent = "02:41"; await new Promise(r => setTimeout(r, 800));
    el.classList.remove("flick"); api.paintClock();
  }

  // 8. 音だけの通知は silentNotify（start 内）

  function fire(name) {
    const was = active; active = true;
    ({ noise: noiseSweep, figure: windowFigure, silentNotify: () => { api.S.vibrate(); if (fxOn()) overlay("fx-vib", 1300, "📱"); }, ambientEvent, bigFlash, shake: () => shake(500, true), glitch: () => glitch(700), blackout: () => blackout(2), title: titleBlip, clock: clockGlitch, windowReturn, windowNudge })[name]?.();
    if (!was) active = false;
  }
  const fx = { shake, bigText, noiseSweep, blackout, redPulse, glitch, overlay, vibIcon: () => { if (fxOn()) overlay("fx-vib", 1300, "📱"); } };
  return { fx, setForced: b => { forced = !!b; }, bind, start, stop, onDetail, shownPending, zeroTrick, clockText, fire, doSwap };
})();
