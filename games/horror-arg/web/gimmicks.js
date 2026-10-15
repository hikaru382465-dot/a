// ギミック（画面の中の小さな異変）。いつから起きるかは data.js の gimmicks で決める。
// URLに ?nogimmick を付けると全部止まる。開発用：__game.fire("swap") などで1つだけ起こせる。
window.Gimmicks = (function () {
  let api = null, active = false, timers = [], zeroDone = {};
  const day = () => api.state().day;
  const on = name => active && day() >= (api.D.gimmicks[name] || 99);
  const later = (fn, ms) => { const t = setTimeout(() => { if (active) fn(); }, ms); timers.push(t); return t; };
  function every(name, minMs, maxMs, fn) {
    (function loop() { later(() => { if (on(name)) fn(); loop(); }, minMs + Math.random() * (maxMs - minMs)); })();
  }
  const baseTitle = document.title;

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
    every("silentNotify", 70000, 130000, () => api.S.notify());
    every("title", 50000, 90000, titleBlip);
    every("clock", 45000, 80000, clockGlitch);
    every("windowReturn", 40000, 90000, windowReturn);
    every("windowNudge", 25000, 45000, windowNudge);
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
    textEl.textContent = "未審査：1件";
    if (badgeEl) { badgeEl.textContent = "1"; badgeEl.style.display = ""; }
    api.S.error();
    later(() => { textEl.textContent = "未審査：なし"; if (badgeEl) badgeEl.style.display = "none"; }, 2600);
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
          const p = bodyEl.querySelectorAll("p")[i]; if (p) p.textContent = e.body[i];
          done++; break;
        }
      }
    }
    if (done) { e.swapped = true; api.save(); }
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
        const dx = (Math.random() < 0.5 ? -1 : 1) * (30 + Math.random() * 20);
        c.bApprove.style.transition = "transform .15s";
        c.bApprove.style.transform = "translate(" + dx + "px,-6px)";
        setTimeout(() => { c.bApprove.style.transform = ""; }, 1100);
      });
    }
    // 5. 最後の投稿で「承認」の文字が「あなた」に変わる
    if (on("buttonLabel") && e.last && c.bApprove) {
      later(() => { if (c.bApprove.isConnected) c.bApprove.textContent = "あなた"; }, 5000);
    }
  }

  // 3. 閉じたメモが勝手に戻る／最小化した窓が戻る
  function windowReturn() {
    const w = api.wins();
    Object.keys(w).forEach(k => { if (w[k].min) { w[k].min = false; w[k].el.style.display = "flex"; } });
    if (!w.memo && Math.random() < 0.6) {
      api.openMemo();
      const m = api.wins().memo;
      if (m) { m.el.style.zIndex = 3; m.el.classList.add("inactive"); m.tb.classList.remove("active"); }
    }
  }
  // 3'. 窓が少しだけずれる
  function windowNudge() {
    const w = api.wins(), ks = Object.keys(w).filter(k => !w[k].min);
    if (!ks.length) return;
    const el = w[ks[Math.floor(Math.random() * ks.length)]].el;
    const dx = (Math.random() < 0.5 ? -1 : 1) * (5 + Math.random() * 5);
    const dy = (Math.random() < 0.5 ? -1 : 1) * (3 + Math.random() * 4);
    el.style.transition = "left .12s, top .12s";
    el.style.left = Math.max(0, el.offsetLeft + dx) + "px"; el.style.top = Math.max(0, el.offsetTop + dy) + "px";
    setTimeout(() => { el.style.transition = ""; }, 250);
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
    el.classList.add("flick");
    el.textContent = f(m - 1); await new Promise(r => setTimeout(r, 800));
    el.textContent = "02:41"; await new Promise(r => setTimeout(r, 800));
    el.classList.remove("flick"); api.paintClock();
  }

  // 8. 音だけの通知は silentNotify（start 内）

  function fire(name) {
    const was = active; active = true;
    ({ silentNotify: () => api.S.notify(), title: titleBlip, clock: clockGlitch, windowReturn, windowNudge })[name]?.();
    if (!was) active = false;
  }
  return { bind, start, stop, onDetail, shownPending, zeroTrick, clockText, fire, doSwap };
})();
