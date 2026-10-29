(function () {
  "use strict";
  const D = window.GAME_DATA;
  const S = window.Snd;
  const $ = (s, el) => (el || document).querySelector(s);
  function h(tag, attrs, ...kids) {
    const e = document.createElement(tag);
    for (const k in (attrs || {})) {
      if (k === "class") e.className = attrs[k];
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), attrs[k]);
      else e.setAttribute(k, attrs[k]);
    }
    kids.flat().forEach(c => { if (c != null) e.append(c.nodeType ? c : document.createTextNode(c)); });
    return e;
  }
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const sentences = t => t.split(/(?<=。)/).filter(Boolean);
  const norm = t => t.replace(/[！-～]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0))
    .replace(/[\s　、。．.・「」]/g, "").toLowerCase();

  // ---------- 状態（ブラウザに保存。?reset で消せる） ----------
  const KEY = "horror-arg-v2";
  const fresh = () => ({ day: 1, queue: null, history: [], decisions: {}, found: {}, memoExtra: [], answers: {}, flags: {}, endings: {}, mailRead: {}, searchHistory: [], commentSeen: {} });
  let state = fresh();
  try {
    if (location.search.includes("reset")) localStorage.removeItem(KEY);
    const raw = localStorage.getItem(KEY);
    if (raw) state = Object.assign(fresh(), JSON.parse(raw));
  } catch (e) { /* 保存できなくても遊べる */ }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }

  // ---------- 投稿の組み立て ----------
  function counts() {
    const all = state.history.concat(state.queue || []);
    const c = { d1: { approve: 0, reject: 0 }, d2: { approve: 0, reject: 0 }, d3: { approve: 0, reject: 0 }, d4: { approve: 0, reject: 0 },
      approvedTotal: 0, rejectedTotal: 0, approvedTitles: [] };
    all.forEach(e => {
      const s = state.decisions[e.eid];
      if (s === "approve") { c.approvedTotal++; c.approvedTitles.push(e.title.replace("【再投稿】", "")); if (c["d" + e.day]) c["d" + e.day].approve++; }
      if (s === "reject") { c.rejectedTotal++; if (c["d" + e.day]) c["d" + e.day].reject++; }
    });
    return c;
  }
  function makeEntry(p) {
    return { eid: p.id, base: p.id, day: p.day, title: p.title, author: p.author, authorId: p.authorId,
      time: p.time, device: p.device, origin: p.origin || null, photo: !!p.photo, final: !!p.final, last: !!p.last,
      retryN: 0, body: typeof p.body === "function" ? p.body(counts()) : p.body.slice() };
  }
  function makeRetry(e, day) {
    const n = e.retryN + 1;
    const orig = D.posts.find(p => p.id === e.base);
    return { eid: e.base + "-r" + n, base: e.base, day: day, title: "【再投稿】" + orig.title, author: e.author, authorId: e.authorId,
      time: n === 1 ? "今日 02:36" : "今日 02:39", device: e.device, origin: null, photo: false, final: false, last: false, retryN: n,
      body: [D.retry[e.base]].concat(D.retryTail[n - 1] ? [D.retryTail[n - 1]] : []) };
  }
  if (!state.queue) state.queue = D.posts.filter(p => p.day === state.day).map(makeEntry);
  const status = id => state.decisions[id] || "pending";
  const pendingCount = () => state.queue.filter(e => status(e.eid) === "pending").length;
  const allEntries = () => state.history.concat(state.queue);

  // ---------- 管理画面の事務的な欄（見せかけの値。投稿者IDから決まる） ----------
  const hashN = (t, m) => String(t).split("").reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 9973, 7) % m;
  const fakeIp = t => [hashN(t + "a", 200) + 30, hashN(t + "b", 250), hashN(t + "c", 250), hashN(t + "d", 250) + 2].join(".") + "";

  // 壁紙：日ごとに変わる（空白＝黄色いもや／night／red／最後の投稿だけ lit）
  let curWall = "", wallB = true;
  try { wallB = localStorage.getItem("horror-arg-wall") !== "a"; } catch (e) {}
  function setWall(k) { curWall = k || ""; $("#wallpaper").className = (wallB ? "b " : "") + curWall; if (window.Gimmicks && window.Gimmicks.applyStage) window.Gimmicks.applyStage(); }
  function toggleWall() { wallB = !wallB; try { localStorage.setItem("horror-arg-wall", wallB ? "b" : "a"); } catch (e) {} setWall(curWall); }

  $("#tb-wall").addEventListener("click", toggleWall);
  $("#hint-tab").addEventListener("click", () => { S.click(); openNotes(); });

  // ---------- 時計 ----------
  let clockMin = 0;
  const clockStr = () => String(Math.floor(clockMin / 60) % 24).padStart(2, "0") + ":" + String(clockMin % 60).padStart(2, "0");
  function paintClock() { $("#tb-clock").textContent = window.Gimmicks.clockText(clockStr()); $("#login-clock").textContent = clockStr(); }
  function resetClock() { const [a, b] = D.clockStart.split(":").map(Number); clockMin = a * 60 + b; paintClock(); }
  setInterval(() => { clockMin++; paintClock(); }, 60000);
  resetClock();

  // ---------- トースト ----------
  function toast(title, text, kind) {
    const t = h("div", { class: "toast " + (kind || "") }, h("div", { class: "tt" }, title), text);
    const box = $("#toasts"); box.append(t);
    while (box.children.length > 3) box.firstChild.remove();
    setTimeout(() => { t.style.transition = "opacity .5s"; t.style.opacity = "0"; setTimeout(() => t.remove(), 520); }, 5600);
  }

  // ---------- ウィンドウ管理 ----------
  let wins = {};
  let zTop = 10;
  function focusWin(id) {
    Object.keys(wins).forEach(k => {
      const w = wins[k], on = k === id && !w.min;
      w.el.classList.toggle("inactive", !on); w.tb.classList.toggle("active", on);
    });
    if (wins[id]) wins[id].el.style.zIndex = ++zTop;
  }
  function openWin(id, title, body, o) {
    if (wins[id]) { wins[id].min = false; wins[id].el.style.display = "flex"; focusWin(id); return wins[id]; }
    o = Object.assign({ w: 640, h: 440, x: 120, y: 40 }, o || {});
    const dw = $("#desktop").clientWidth, dh = $("#desktop").clientHeight;
    o.w = Math.min(o.w, dw - 20); o.h = Math.min(o.h, dh - 20);
    o.x = Math.max(0, Math.min(o.x, dw - o.w)); o.y = Math.max(0, Math.min(o.y, dh - o.h));
    const bMin = h("button", { title: "最小化", "aria-label": "最小化" }, "–"), bX = h("button", { class: "x", title: "閉じる", "aria-label": "閉じる" }, "×");
    const bar = h("div", { class: "win-title" }, h("span", { class: "t" }, title), bMin, bX);
    const el = h("div", { class: "win w-" + id, style: `left:${o.x}px;top:${o.y}px;width:${o.w}px;height:${o.h}px` },
      bar, h("div", { class: "win-body" }, body));
    const tb = h("div", { class: "tb-item" }, title);
    $("#desktop").append(el); $("#tb-items").append(tb);
    const w = { el, tb, min: false };
    wins[id] = w;
    el.addEventListener("pointerdown", () => focusWin(id));
    bX.addEventListener("click", () => closeWin(id));
    bMin.addEventListener("click", () => { w.min = true; el.style.display = "none"; focusWin(null); });
    tb.addEventListener("click", () => {
      if (w.min) { w.min = false; el.style.display = "flex"; focusWin(id); }
      else if (el.classList.contains("inactive")) focusWin(id);
      else { w.min = true; el.style.display = "none"; focusWin(null); }
      S.click();
    });
    bar.addEventListener("pointerdown", ev => {
      if (ev.target.tagName === "BUTTON" || window.innerWidth < 760) return;
      const sx = ev.clientX - el.offsetLeft, sy = ev.clientY - el.offsetTop;
      const mv = e => {
        el.style.left = Math.max(-el.offsetWidth + 80, Math.min(dw - 80, e.clientX - sx)) + "px";
        el.style.top = Math.max(0, Math.min(dh - 32, e.clientY - sy)) + "px";
      };
      const up = () => { window.removeEventListener("pointermove", mv); window.removeEventListener("pointerup", up); };
      window.addEventListener("pointermove", mv); window.addEventListener("pointerup", up);
    });
    S.open(); focusWin(id);
    return w;
  }
  function closeWin(id, quiet) {
    const w = wins[id]; if (!w) return;
    w.el.remove(); w.tb.remove(); delete wins[id]; if (!quiet) { S.close(); window.Gimmicks.onWindowClosed(); }
  }

  // ---------- 写真（絵で描く。暗い部屋・光るモニター・後ろ姿・戸口の人影） ----------
  function makePhoto(step) {
    step = step || 0;
    const W = 420, H = 280, cv = document.createElement("canvas");
    cv.width = W; cv.height = H; cv.className = "photo";
    const g = cv.getContext("2d");
    let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    const bg = g.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, "#07090d"); bg.addColorStop(1, "#10151e");
    g.fillStyle = bg; g.fillRect(0, 0, W, H);
    // 戸口と人影（右はし。ほとんど見えない）
    g.fillStyle = "#0b0e14"; g.fillRect(332, 40, 64, 190);
    // 戸口の人影：step が進むほど、座っている人のほうへ近づき、大きくなる
    { const fxp = 364 - step * 21, hy = 78 + step * 9, rr = 11 + step * 2.2, bw = 24 + step * 6;
      g.fillStyle = "#06070a"; g.beginPath(); g.ellipse(fxp, hy, rr, rr * 1.27, 0, 0, 7); g.fill(); g.fillRect(fxp - bw / 2, hy + rr * 1.1, bw, 118 + step * 8);
      if (step >= 4) { g.fillStyle = "rgba(200,194,180,.22)"; g.beginPath(); g.ellipse(fxp, hy, rr * .55, rr * .75, 0, 0, 7); g.fill(); } }
    // 机
    g.fillStyle = "#151b26"; g.fillRect(0, 196, W, 84);
    g.fillStyle = "#222b3b"; g.fillRect(0, 194, W, 3);
    // モニターの光
    const glow = g.createRadialGradient(170, 130, 10, 170, 130, 190);
    glow.addColorStop(0, "rgba(120,170,255,.55)"); glow.addColorStop(1, "rgba(120,170,255,0)");
    g.fillStyle = glow; g.fillRect(0, 0, W, H);
    g.fillStyle = "#cfe0ff"; g.fillRect(110, 80, 120, 80);
    g.fillStyle = "#3b78e0"; g.fillRect(116, 86, 108, 8);
    g.fillStyle = "#e8eefb"; for (let i = 0; i < 5; i++) g.fillRect(120, 100 + i * 11, 40 + (i * 17) % 50, 5);
    g.fillStyle = "#1a2130"; g.fillRect(163, 160, 14, 28); g.fillRect(143, 186, 54, 6);
    // 座っている人の後ろ姿
    g.fillStyle = "#04060a"; g.beginPath(); g.ellipse(250, 150, 22, 27, 0, 0, 7); g.fill();
    g.beginPath(); g.moveTo(205, 235); g.quadraticCurveTo(212, 182, 250, 176); g.quadraticCurveTo(290, 182, 297, 235); g.closePath(); g.fill();
    // 粒子と周辺減光
    const id = g.getImageData(0, 0, W, H), d = id.data;
    for (let i = 0; i < d.length; i += 4) { const n = (rnd() - 0.5) * 26; d[i] += n; d[i + 1] += n; d[i + 2] += n; }
    g.putImageData(id, 0, 0);
    const v = g.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, W * 0.62);
    v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.65)");
    g.fillStyle = v; g.fillRect(0, 0, W, H);
    return cv;
  }

  // ---------- 管理画面 ----------
  let selId = null, tab = "today", renderAdmin = () => {}, badgeEl = null;
  const statusLabel = s => ({ pending: "未審査", approve: "承認", reject: "却下", hold: "保留" }[s]);
  let fStatus = "all", fQuery = "";
  const fakeNo = e => "P-" + String(1000 + hashN(e.eid, 8999));
  function adminTable(rows, pick) {
    const tbody = h("tbody"), count = h("span", { class: "tbl-count" });
    const selSt = h("select", { "aria-label": "状態で絞り込み", onchange: ev => { fStatus = ev.target.value; fill(); } },
      [["all", "すべての状態"], ["pending", "未審査"], ["approve", "承認"], ["reject", "却下"], ["hold", "保留"]].map(([v, l]) => h("option", { value: v }, l)));
    selSt.value = fStatus;
    const q = h("input", { class: "tbl-q", type: "search", placeholder: "タイトル・投稿者で検索", value: fQuery, "aria-label": "検索", oninput: ev => { fQuery = ev.target.value; fill(); } });
    function fill() {
      const list = rows.filter(e => (fStatus === "all" || status(e.eid) === fStatus) && (!fQuery || (e.title + e.author).includes(fQuery)));
      tbody.replaceChildren(...list.map(e => { const st = status(e.eid);
        return h("tr", { tabindex: "0", onclick: () => pick(e), onkeydown: ev => { if (ev.key === "Enter") pick(e); } },
          h("td", {}, h("input", { type: "checkbox", "aria-label": "選択", onclick: ev => ev.stopPropagation() })),
          h("td", { class: "mono" }, fakeNo(e)), h("td", { class: "ttl" }, e.title), h("td", {}, e.author), h("td", {}, (tab === "hist" ? e.day + "日目 " : "") + e.time),
          h("td", {}, e.device), h("td", { class: "num" }, String(hashN(e.authorId + "r", 3))), h("td", {}, h("span", { class: "st " + st }, statusLabel(st)))); }));
      if (!list.length) tbody.append(h("tr", {}, h("td", { colspan: "8", class: "tbl-none" }, "該当する投稿はありません")));
      count.textContent = "全 " + rows.length + " 件中 " + list.length + " 件を表示";
    }
    fill();
    return h("div", { class: "tbl-wrap" },
      h("div", { class: "tbl-bar" }, q, selSt, h("span", { class: "sp" }), count),
      h("div", { class: "tbl-scroll" }, h("table", { class: "tbl" },
        h("thead", {}, h("tr", {}, h("th", {}, h("input", { type: "checkbox", "aria-label": "すべて選択" })), ["投稿番号", "タイトル", "投稿者", "投稿日時", "端末", "通報", "状態"].map(t => h("th", {}, t)))), tbody)),
      h("div", { class: "tbl-foot" }, h("select", { disabled: "", "aria-label": "一括操作" }, h("option", {}, "一括操作を選択")), h("button", { class: "btn", disabled: "" }, "実行"), h("span", { class: "sp" }),
        h("span", { class: "tbl-pg" }, "20件／ページ　‹　1　›")));
  }
  function openAdmin() {
    const finalDay = state.queue.some(e => e.last);
    const bTab1 = h("button", { class: "tab on", onclick: () => { tab = "today"; selId = null; S.click(); renderAdmin(); } }, "本日の投稿");
    const bTab2 = h("button", { class: "tab", onclick: () => { tab = "hist"; selId = null; S.click(); renderAdmin(); } }, "過去の投稿");
    const top = h("div", { class: "adm-top" },
      h("span", { class: "site" }, D.siteName.replace("（仮）", "")), h("span", { class: "tag" }, "管理画面"), h("div", { class: "tabs" }, bTab1, bTab2), h("span", { class: "sp" }),
      h("span", { class: "who" }, "ログイン中：admin_0721"));
    const list = h("div", { class: "adm-list" });
    const detail = h("div", { class: "adm-detail" });
    const bPend = h("span");
    const bCmp = h("button", { class: "btn", onclick: () => { S.click(); openCompare(); } }, "類似チェック");
    const bEnd = h("button", { class: "btn primary", onclick: () => endDay() }, finalDay ? "最後の審査を確定" : "本日の審査を終了");
    const bottom = h("div", { class: "adm-bottom" }, bPend, h("span", { class: "sp" }), bCmp, bEnd);
    const mainEl = h("div", { class: "adm-main" });
    const body = h("div", { style: "display:flex;flex-direction:column;height:100%" },
      top, mainEl, bottom);
    mainEl.append(h("div", { class: "adm-left" }, list), detail);

    renderAdmin = function () {
      bTab1.classList.toggle("on", tab === "today"); bTab2.classList.toggle("on", tab === "hist");
      const rows = tab === "today" ? state.queue : state.history;
      list.replaceChildren(...(rows.length ? rows : [h("div", { class: "adm-empty small" }, "まだありません")]).map(e => {
        if (!e.eid) return e;
        const s = status(e.eid);
        return h("div", { class: "adm-row" + (selId === e.eid ? " sel" : ""), tabindex: "0", role: "button", onkeydown: ev => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); selId = e.eid; S.click(); renderAdmin(); } }, onclick: () => { selId = e.eid; S.click(); renderAdmin(); } },
          h("div", { class: "r1" }, h("span", { class: "ttl" }, e.title), h("span", { class: "st " + s }, statusLabel(s))),
          h("div", { class: "r2" }, h("span", {}, (tab === "hist" ? e.day + "日目　" : "") + e.author), h("span", {}, e.time)));
      }));
      const e = rows.find(x => x.eid === selId);
      mainEl.classList.toggle("has-sel", !!e);
      if (!e) {
        detail.replaceChildren(adminTable(rows, x => { selId = x.eid; S.click(); renderAdmin(); }));
      } else {
        const dec = d => {
          state.decisions[e.eid] = d; save();
          if (d === "approve" && e.last && pendingCount() === 0) { const c = counts(); finaleOpen(c.approvedTotal >= 8); return; }
          if (d === "approve") { window.Apps.onApprove(e); S.approve(); toast("公開しました", "「" + e.title + "」を外部の公開サイトに掲載しました。", "ok"); }
          if (d === "reject") { S.reject(); toast("却下しました", "投稿者には通知されません。", "bad"); }
          if (d === "hold") { S.hold(); openMemo(); toast("保留にしました", "前任者の引き継ぎメモを開きました。", "warn"); }
          renderAdmin();
        };
        const cur = status(e.eid);
        const meta = h("div", { class: "det-meta" },
          h("span", {}, "投稿者：", h("b", {}, e.author)), h("span", {}, "ID：", h("b", {}, e.authorId)),
          h("span", {}, "投稿：", h("b", {}, e.time)), h("span", {}, "端末：", h("b", {}, e.device)),
          h("span", {}, "IP：", h("b", {}, fakeIp(e.authorId))), h("span", {}, "過去の投稿：", h("b", {}, 1 + hashN(e.authorId, 9) + "件")), h("span", {}, "通報：", h("b", {}, hashN(e.authorId + "r", 3) + "件")));
        if (e.origin) meta.append(h("span", { class: "clue", title: "引き継ぎメモの対応表で、ひらがなに読みかえられます" }, "投稿元コード：", h("b", {}, e.origin)));
        const bodyEl = h("div", { class: "det-body" }, e.body.map(t => h("p", {}, t)));
        window.Apps.decorate(e, bodyEl);
        if (e.last) setWall("lit");
        if (e.photo) {
          const info = h("div", { class: "photo-info hidden" });
          const bInfo = h("button", { class: "btn", style: "margin-top:6px", onclick: () => {
            info.classList.toggle("hidden");
            if (!state.flags.photo) {
              state.flags.photo = true; save(); checkQuestions(); S.sting();
              toast("写真の情報", "撮影日時が、「明日」になっています。", "warn");
            } else S.click();
          } }, "写真の情報を見る");
          info.append(h("table", {}, D.photoInfo.map(r => h("tr", {}, h("td", {}, r[0]), h("td", {}, r[1])))));
          bodyEl.append(h("div", { class: "photo-wrap" }, makePhoto(), bInfo, info));
        }
        const bApprove = h("button", { class: "btn ok", onclick: () => dec("approve") }, cur === "approve" ? "承認済み" : "承認");
        const foot = tab === "hist"
          ? h("div", { class: "det-foot" }, h("span", { class: "note", style: "margin-left:0" }, "過去の投稿です。判断：" + statusLabel(cur)))
          : h("div", { class: "det-foot" },
            bApprove,
            h("button", { class: "btn ng", onclick: () => dec("reject") }, cur === "reject" ? "却下済み" : "却下"),
            e.last ? null : h("button", { class: "btn hold", onclick: () => dec("hold") }, "保留"),
            e.last ? h("span", { class: "note" }, "この投稿の判断で、結末が決まります。") : null);
        detail.replaceChildren(
          h("div", { class: "det-head" }, h("button", { class: "btn back", onclick: () => { selId = null; S.click(); renderAdmin(); } }, "← 一覧"), h("h2", {}, e.title), meta), bodyEl, foot);
        window.Gimmicks.onDetail(e, { bodyEl, bApprove: tab === "today" ? bApprove : null });
      }
      const n = pendingCount(), shown = window.Gimmicks.shownPending(n);
      bPend.textContent = shown > 0 ? "未審査：" + shown + "件" : "未審査：なし";
      updateBadge();
      if (n === 0) window.Gimmicks.zeroTrick(bPend, badgeEl);
    };
    openWin("admin", D.siteName.replace("（仮）", "") + " 管理画面", body, { w: 880, h: 520, x: 90, y: 20 });
    renderAdmin();
  }

  // ---------- メモ帳 ----------
  function openMemo() {
    const body = h("div", { class: "memo-body", id: "memo-body" });
    const stat = h("div", { class: "memo-status", id: "memo-status" }, "引き継ぎメモ.txt　最終更新：前任者");
    D.memo.concat(state.memoExtra).forEach(t => body.append(h("p", {}, t)));
    openWin("memo", "引き継ぎメモ.txt - メモ帳", h("div", { style: "display:flex;flex-direction:column;height:100%" }, body, stat),
      { w: 500, h: 380, x: 770, y: 60 });
  }
  async function appendMemo(text, silent) {
    state.memoExtra.push(text); save();
    if (!wins.memo) { if (!silent) { S.notify(); toast("引き継ぎメモ.txt", "ファイルが更新されました。", "warn"); } return; }
    const body = $("#memo-body"), stat = $("#memo-status");
    stat.textContent = "このファイルは外部で更新されました"; stat.classList.add("alert");
    const p = h("p", { class: "new" }); body.append(p);
    for (const ch of text) { p.textContent += ch; S.key(); body.scrollTop = body.scrollHeight; await sleep(70 + Math.random() * 60); }
  }

  // ---------- 類似チェック ----------
  function openCompare() {
    const sources = allEntries().map(e => ({ key: e.eid, label: e.day + "日目：" + e.title, paras: e.body }))
      .concat([{ key: "memo", label: "引き継ぎメモ.txt", paras: D.memo.concat(state.memoExtra) }]);
    let pickA = null, pickB = null, fails = 0;
    const selA = h("select"), selB = h("select");
    sources.forEach(s => { selA.append(h("option", { value: s.key }, s.label)); selB.append(h("option", { value: s.key }, s.label)); });
    selA.value = sources[Math.min(1, sources.length - 1)].key; selB.value = "memo";
    const colA = h("div", { class: "cmp-col" }), colB = h("div", { class: "cmp-col" });
    const msg = h("div", { class: "cmp-msg" }, "2つの文章を選び、同じ言い回しだと思う文を、左右から1つずつ選んでください。");
    const go = h("button", { class: "btn primary", onclick: check }, "照合");
    function paint() {
      pickA = pickB = null;
      [[selA, colA, "A"], [selB, colB, "B"]].forEach(([sel, col, side]) => {
        const src = sources.find(s => s.key === sel.value);
        col.replaceChildren(h("h4", {}, (side === "A" ? "文章A：" : "文章B：") + src.label));
        src.paras.forEach(par => {
          const p = h("p", { style: "margin:0 0 8px" });
          sentences(par).forEach(sn => {
            const sp = h("span", { class: "sent", onclick: () => {
              S.click();
              col.querySelectorAll(".sent").forEach(x => x.classList.remove("picked"));
              sp.classList.add("picked");
              if (side === "A") pickA = sn; else pickB = sn;
            } }, sn);
            p.append(sp);
          });
          col.append(p);
        });
      });
    }
    const tagOf = sn => { for (const k in D.tags) if (sn.includes(D.tags[k])) return k; return null; };
    function check() {
      if (!pickA || !pickB) { S.error(); msg.className = "cmp-msg bad"; msg.textContent = "左右から1文ずつ選んでください。"; return; }
      if (selA.value === selB.value) { S.error(); msg.className = "cmp-msg bad"; msg.textContent = "同じ文章どうしは比べられません。"; return; }
      const ta = tagOf(pickA), tb = tagOf(pickB);
      if (ta && ta === tb) {
        document.querySelectorAll(".cmp-col .picked").forEach(x => { x.classList.remove("picked"); x.classList.add("match"); });
        msg.className = "cmp-msg good";
        msg.textContent = "一致を検出しました。同じ言い回しが、別の投稿者の文章に含まれています。";
        if (!state.found[ta]) {
          state.found[ta] = true; save(); S.found(); checkQuestions();
          if (D.memoAddenda[ta]) setTimeout(() => appendMemo(D.memoAddenda[ta]), 1800);
        }
      } else {
        S.error(); fails++;
        msg.className = "cmp-msg bad";
        msg.textContent = "一致なし。" + (fails >= 3 ? "（ヒント：前任者のメモも、比べる相手に入っています）" : "");
      }
    }
    selA.addEventListener("change", () => { S.click(); paint(); });
    selB.addEventListener("change", () => { S.click(); paint(); });
    openWin("cmp", "類似チェック", h("div", { style: "display:flex;flex-direction:column;height:100%" },
      h("div", { class: "cmp-bar" }, "文章A", selA, "文章B", selB), h("div", { class: "cmp-cols" }, colA, colB),
      h("div", { class: "cmp-foot" }, msg, go)), { w: 820, h: 480, x: 130, y: 50 });
    paint();
  }

  // ---------- 調査メモ（いま調べること／ヒント／わかったことを書き込む） ----------
  const qDone = q => { const [a, b] = q.done.split("."); return !!(state[a] && state[a][b]); };
  const qOpen = q => q.day <= state.day && (!q.after || qDone(D.questions.find(x => x.id === q.after)));
  const qTodo = () => D.questions.filter(q => qOpen(q) && !qDone(q));
  let notesRepaint = null, qToastReady = false;
  function checkQuestions() {
    state.qShown = state.qShown || {};
    const fresh = D.questions.filter(q => qOpen(q) && !state.qShown[q.id]);
    fresh.forEach(q => { state.qShown[q.id] = Date.now(); });
    if (fresh.length) save();
    updateBadge(); if (notesRepaint) notesRepaint();
    const newTodo = fresh.filter(q => !qDone(q));
    if (newTodo.length && qToastReady) toast("調査メモ", "新しく調べることが " + newTodo.length + " 件あります。デスクトップの「調査メモ」を開いてください。");
  }
  function openNotes() {
    state.hintLv = state.hintLv || {}; state.qShown = state.qShown || {};
    const input = h("input", { class: "note-input", placeholder: "答えを書く", autocomplete: "off" });
    const list = h("div", { class: "q-list" });
    const log = h("div", { class: "note-log" });
    const msg = h("div", { class: "cmp-msg" });
    function hintLevel(q) { return state.hintLv[q.id] || 0; }   // 見たい人だけ：自分で押した段まで
    function paint() {
      const items = D.questions.filter(qOpen);
      list.replaceChildren(h("div", { class: "q-h" }, "いま調べること"), ...items.map(q => {
        const done = qDone(q), lv = hintLevel(q);
        return h("div", { class: "q-item" + (done ? " done" : "") },
          h("div", { class: "q-t" }, h("span", { class: "q-ck" }, done ? "✓" : "□"), q.q + (q.len && !done ? "（" + q.len + "文字／けた）" : "")),
          done ? null : h("div", { class: "q-hints" },
            ...[0, 1, 2].filter(i => i < lv).map(i => h("div", { class: "q-hint" }, "ヒント" + "①②③"[i] + "：" + q.hints[i])),
            lv < 3 ? h("button", { class: "btn q-btn", onclick: () => { state.hintLv[q.id] = Math.min(3, lv + 1); save(); S.click(); paint(); } }, lv ? "次のヒント" : "ヒントを見る") : null));
      }), ...(items.length ? [] : [h("div", { class: "adm-empty small" }, "いま調べることはありません")]));
      log.replaceChildren(...(D.answers.filter(a => state.answers[a.id]).map(a => h("div", { class: "note-item" }, "✓ " + a.log))));
    }
    notesRepaint = () => { if (input.isConnected) paint(); };
    function submit() {
      const v = norm(input.value); if (!v) return;
      const a = D.answers.find(x => x.day <= state.day && x.accept.some(c => norm(c) === v));
      if (!a) { S.error(); msg.className = "cmp-msg bad"; msg.textContent = "該当する手がかりが見つかりません。"; return; }
      input.value = "";
      if (state.answers[a.id]) { msg.className = "cmp-msg"; msg.textContent = "すでに記録済みです。"; S.click(); return; }
      state.answers[a.id] = true; save(); S.found(); paint(); checkQuestions();
      msg.className = "cmp-msg good"; msg.textContent = "記録しました。";
      if (a.memo && D.memoAddenda[a.memo]) setTimeout(() => appendMemo(D.memoAddenda[a.memo]), 1600);
      if (a.ending) setTimeout(() => showEnding("secret"), 2600);
    }
    input.addEventListener("keydown", e => { if (e.key === "Enter") submit(); else S.key(); });
    openWin("notes", "調査メモ", h("div", { class: "notes" },
      list,
      h("div", { class: "note-help" }, "答えがわかったら、ここに書き込むと記録されます。（調べるだけで解けるものは、自動でチェックが付きます）"),
      h("div", { class: "note-row" }, input, h("button", { class: "btn primary", onclick: submit }, "記録")),
      msg, log), { w: 520, h: 470, x: 300, y: 60 });
    paint();
  }

  // ---------- 最後の投稿者.txt（暗証番号つき） ----------
  function openLocked() {
    const body = h("div", { style: "display:flex;flex-direction:column;height:100%" });
    function showText() {
      body.replaceChildren(h("div", { class: "memo-body" }, D.lockedFile.map(t => h("p", {}, t))),
        h("div", { class: "memo-status" }, "最後の投稿者.txt　（解除済み）"));
    }
    if (state.flags.lockOpen) showText();
    else {
      const inp = h("input", { class: "note-input", placeholder: "4けたの番号", maxlength: "4", autocomplete: "off", style: "text-align:center;width:140px" });
      const msg = h("div", { class: "cmp-msg", style: "text-align:center" }, "このファイルは、暗証番号で保護されています。");
      const go = () => {
        if (norm(inp.value) === D.lockCode) { state.flags.lockOpen = true; save(); S.found(); showText(); checkQuestions(); }
        else { S.error(); msg.className = "cmp-msg bad"; msg.textContent = "番号が違います。"; }
      };
      inp.addEventListener("keydown", e => { if (e.key === "Enter") go(); else S.key(); });
      body.append(h("div", { class: "lock" }, h("div", { class: "lock-ico" }, "🔒"), msg, inp, h("button", { class: "btn primary", onclick: go }, "解除")));
    }
    openWin("locked", "最後の投稿者.txt", body, { w: 440, h: 340, x: 340, y: 90 });
  }

  // ---------- デスクトップのアイコン ----------
  const TOUCH = () => matchMedia("(pointer: coarse)").matches || window.innerWidth < 760;
  let badgeFns = [];
  function paintHintTab() {
    const t = $("#hint-tab"); if (!t) return;
    const n = qTodo().length; t.classList.toggle("has", n > 0); t.querySelector(".ht-n").textContent = n ? String(n) : "";
  }
  function updateBadge() {
    paintHintTab();
    if (badgeEl) { const n = window.Gimmicks.shownPending(pendingCount()); badgeEl.textContent = n; badgeEl.style.display = n ? "" : "none"; }
    badgeFns.forEach(f => f());
  }
  function buildIcons() {
    badgeFns = [];
    const mk = (label, glyph, color, fn, withBadge, badgeFn) => {
      const el = h("div", { class: "icon", tabindex: "0", role: "button", "aria-label": label, onkeydown: ev => { if (ev.key === "Enter") fn(); } }, h("div", { class: "glyph", style: "background:" + color, "aria-hidden": "true" }, glyph), label);
      el.addEventListener("click", () => { document.querySelectorAll(".icon").forEach(i => i.classList.remove("sel")); el.classList.add("sel"); S.click(); });
      el.addEventListener(TOUCH() ? "click" : "dblclick", fn);
      if (TOUCH()) el.addEventListener("dblclick", () => {});
      if (withBadge) { badgeEl = h("span", { class: "badge" }, "0"); el.append(badgeEl); }
      if (badgeFn) { const b = h("span", { class: "badge" }, "0"); el.append(b); const f = () => { const n = badgeFn(); b.textContent = n; b.style.display = n ? "" : "none"; }; badgeFns.push(f); f(); }
      return el;
    };
    const box = $("#icons"); box.replaceChildren();
    box.append(mk("管理画面", "▤", "linear-gradient(135deg,#3b78e0,#2759b5)", openAdmin, true),
      mk("引き継ぎメモ", "✎", "linear-gradient(135deg,#d9a93a,#a97a14)", openMemo, false));
    window.Apps.iconDefs().forEach(d => box.append(mk(d.label, d.glyph, d.color, d.fn, false, d.badge)));
    box.append(mk("調査メモ", "？", "linear-gradient(135deg,#6a5acd,#46399c)", openNotes, false, () => qTodo().length));
    if (state.day >= 4) box.append(mk("最後の投稿者", "🔒", "linear-gradient(135deg,#555d70,#323847)", openLocked, false));
    box.append(mk("ダウンロード", "↓", "linear-gradient(135deg,#6b7280,#444a56)", () => {}, false), mk("ごみ箱", "🗑", "linear-gradient(135deg,#59606e,#383d48)", () => {}, false));
    updateBadge();
  }
  function resetDesktop() {
    window.Gimmicks.stop();
    Object.keys(wins).forEach(k => closeWin(k, true)); wins = {};
    $("#icons").replaceChildren(); $("#toasts").replaceChildren(); $("#tb-items").replaceChildren();
    badgeEl = null; selId = null; tab = "today";
  }

  // ---------- 文字を1文字ずつ出す演出（終了・エンディング共通） ----------
  async function typeLines(box, items) {
    for (const it of items) {
      const d = h("div", { class: it.cls || "" }); box.append(d);
      for (const ch of it.text) { d.textContent += ch; await sleep(it.speed || 36); }
      await sleep(it.wait == null ? 500 : it.wait);
    }
  }

  // ---------- 1日の終わり ----------
  async function endDay() {
    const q = state.queue, cnt = { approve: 0, reject: 0, hold: 0, pending: 0 };
    q.forEach(e => cnt[status(e.eid)]++);
    if (cnt.pending > 0) { S.error(); toast("まだ終われません", "未審査の投稿が" + cnt.pending + "件あります。", "warn"); return; }
    const last = q.find(e => e.last);
    if (last && !["approve", "reject"].includes(status(last.eid))) { S.error(); toast("まだ終われません", "最後の投稿は、承認か却下を選んでください。", "warn"); return; }
    S.click();
    if (last) {
      const c = counts();
      const heavy = status(last.eid) === "reject" ? c.rejectedTotal >= 8 : c.approvedTotal >= 8;
      return status(last.eid) === "reject" ? showEnding("close", heavy) : finaleOpen(heavy);
    }
    const scr = $("#screen-end"), box = $("#end-box");
    window.Gimmicks.stop(); $("#screen-desk").classList.add("hidden"); scr.classList.remove("hidden"); box.replaceChildren();
    S.sting();
    const day = state.day;
    await typeLines(box, [{ cls: "big", text: day + "日目の審査を終了しました。", wait: 700 }]);
    [["承認", cnt.approve], ["却下", cnt.reject], ["保留", cnt.hold]].forEach(r => box.append(h("div", { class: "row" }, h("span", {}, r[0]), h("span", {}, r[1] + "件"))));
    await sleep(900); box.append(h("div", { style: "height:18px" }));
    const notes = { 1: "前回のログイン：02:38（アカウント削除済み）", 2: "最後の投稿時刻：02:34（あなたのログインの7分前）", 3: "最後の投稿時刻：02:40（あなたのログインの1分前）", 4: "最後の投稿時刻：02:41（あなたのログイン時刻と同じ）" };
    await typeLines(box, [{ cls: "dim", text: "ログアウトします。", wait: 900 }, { cls: "dim", text: "次回のログイン予定：明日 02:41", wait: 1100 },
      { cls: "dim flick", text: notes[day] || "", wait: 1300 }]);
    box.append(h("button", { class: "btn", style: "margin-top:26px", onclick: nextDay }, "ログインする（" + (day + 1) + "日目）"));
  }
  function nextDay() {
    const next = state.day + 1, carry = [], retries = [];
    state.queue.forEach(e => {
      const s = state.decisions[e.eid];
      if (s === "hold") carry.push(e);
      else { state.history.push(Object.assign({}, e)); if (s === "reject" && e.retryN < 2 && D.retry[e.base]) retries.push(makeRetry(e, next)); }
    });
    state.queue = null; state.day = next;
    const news = D.posts.filter(p => p.day === next).map(makeEntry);
    const rest = retries.concat(carry), fin = news.filter(e => e.final), mid = news.filter(e => !e.final);
    state.queue = mid.concat(rest, fin);
    if (next === 2 && !state.flags.day2memo) { state.flags.day2memo = true; state.memoExtra.push(D.memoAddenda.day2); }
    save();
    showLogin();
  }

  // ---------- エンディング ----------
  async function showEnding(kind, heavy, quiet) {
    const c = counts();
    const key = kind === "secret" ? "secret" : kind + (heavy ? "_heavy" : "_light");
    const lines = D.endings[key](c);
    state.endings[kind] = true; save();
    const scr = $("#screen-end"), box = $("#end-box");
    window.Gimmicks.stop(); $("#screen-desk").classList.add("hidden"); scr.classList.remove("hidden"); box.replaceChildren();
    if (!quiet) S.sting();
    for (const t of lines) await typeLines(box, [{ cls: quiet ? "endtext" : "dim", text: t, wait: quiet ? 1500 : 1100, speed: quiet ? 70 : 55 }]);
    await sleep(900);
    box.append(h("div", { class: "big", style: "margin-top:26px" }, D.endingNames[kind]));
    const got = Object.keys(D.endingNames).map(k => (state.endings[k] ? "● " : "○ ") + D.endingNames[k]).join("　");
    box.append(h("div", { class: "dim" }, "到達したエンディング：" + got));
    box.append(h("button", { class: "btn", style: "margin-top:20px", onclick: restart }, "最初からやり直す"));
  }

  // ---------- 承認エンド：自分の画面・自分の部屋に起きる（約35秒） ----------
  let finaleBusy = false;
  async function finaleOpen(heavy) {
    if (finaleBusy) return; finaleBusy = true;
    const G = window.Gimmicks; G.stop(); G.setForced(true);
    const block = h("div", { id: "finale-block" }); document.body.append(block);
    const clock2 = () => { const t = new Date(); return [t.getHours(), t.getMinutes(), t.getSeconds()].map(v => String(v).padStart(2, "0")); };
    S.stopAmbient(0.4);                                     // PCのファンの音が止まる（静けさ）
    await sleep(1500);
    toast("公開しました", "「管理人の夜」を公開サイトに掲載しました。投稿者：（あなた）", "ok");
    await sleep(1600);
    S.vibrate(); G.fx.vibIcon();                           // 机のスマホが震える
    toast("読者コメント", "「管理人の夜」に、コメントが届きました。");
    await sleep(1700);
    const ctl = window.Apps.openSiteStory("p16");           // 自分の投稿ページ（暗い部屋の写真）
    await sleep(2200);
    const [hh, mm] = clock2();
    if (ctl) await ctl.typeComment("（名前なし）", "今日 " + hh + ":" + mm, "この写真、いま撮りました。");   // 端末の時刻を読むだけ（どこにも送らない）
    await sleep(1000);
    for (let st = 1; st <= 4; st++) {                       // 写真の人影が、座っている人の後ろへ近づく（足音つき）
      if (ctl) ctl.setStep(st); S.footstep(-0.75 + 0.2 * st, 0.4 + 0.17 * st); if (st === 3) S.creak(true);
      await sleep(900 + st * 130);
    }
    $("#tb-cam").classList.remove("hidden"); S.relayClick();   // カメラ使用中の赤い点（本物のカメラは使わない）
    await sleep(1400);
    S.heartbeat(); [0, 900, 1700, 2400].forEach(ms => setTimeout(() => G.fx.redPulse(800), ms));
    await sleep(2900);
    Object.keys(wins).forEach(k => { wins[k].el.style.display = "none"; });   // 窓が全部消える
    const wp = $("#wallpaper"); setWall("lit"); wp.classList.remove("st1", "st2", "st3", "st4", "o1", "o2", "o3", "o4"); if (/\bb\b/.test(wp.className)) wp.classList.add("fig");
    S.breath(); await sleep(2600); S.breath(); await sleep(1800);
    const cam = h("div", { id: "screen-cam" }, makePhoto(5), h("div", { class: "cam-rec" }, "● REC"), h("div", { class: "cam-time" }, ""));
    document.body.append(cam);                              // 監視カメラ風の映像（無音）
    const tick = () => { const t = cam.querySelector(".cam-time"); if (t) t.textContent = clock2().join(":"); }; tick(); const ti = setInterval(tick, 500);
    await sleep(3400);
    S.jolt(); G.fx.bigText("うしろ", 600); G.fx.shake(500, true);   // 驚かせるのは、ここ1回だけ
    await sleep(900);
    clearInterval(ti); cam.remove();
    const dark = h("div", { id: "finale-dark" }); document.body.append(dark);
    await sleep(2200);                                      // 真っ暗・無音
    G.setForced(false); block.remove(); dark.remove(); $("#tb-cam").classList.add("hidden"); finaleBusy = false;
    await showEnding("open", heavy, true);
  }

  function restart() {
    state = Object.assign(fresh(), { endings: state.endings });
    state.queue = D.posts.filter(p => p.day === 1).map(makeEntry);
    save(); showLogin();
  }

  // ---------- ログイン画面と起動 ----------
  function showLogin() {
    resetDesktop(); resetClock();
    $("#screen-end").classList.add("hidden"); $("#screen-desk").classList.add("hidden"); $("#screen-boot").classList.add("hidden");
    $("#screen-login").classList.remove("hidden");
    const last = state.day === 1 ? "前回のログイン：02:38（アカウント削除済み）" : "前回のログイン：昨日 02:41（あなた）";
    $("#login-last").textContent = last;
    $("#login-date").textContent = state.day === 1 ? "日付は、いつも通り。" : state.day + "日目";
  }
  async function boot() {
    S.init(); S.login();
    $("#screen-login").classList.add("hidden");
    const bs = $("#screen-boot"), bt = $("#boot-text");
    bt.textContent = ""; bs.classList.remove("hidden");
    const lines = { 1: ["認証しています…", "ログインしました。", "前任の管理人は退会済みです。"],
      2: ["認証しています…", "ログインしました。", "前回のログイン：昨日 02:41（あなた）"],
      3: ["認証しています…", "ログインしました。", "現在のログイン数：2"],
      4: ["認証しています…", "ログインしました。", "現在のログイン数：3"],
      5: ["認証しています…", "ログインしました。", "現在のログイン数：16", "あなたは、1人目ではありません。"] }[state.day] || ["ログインしました。"];
    for (const l of lines) {
      bt.textContent += (bt.textContent ? "\n" : "");
      for (const ch of l) { bt.textContent += ch; S.key(); await sleep(55); }
      await sleep(600);
    }
    await sleep(500);
    bs.classList.add("hidden"); $("#screen-desk").classList.remove("hidden");
    setWall(state.day >= 5 ? "red" : state.day >= 3 ? "night" : ""); buildIcons(); S.startAmbient(); S.setDay(state.day); window.Gimmicks.start();
    await sleep(1400); S.notify();
    const retries = state.queue.filter(e => e.retryN > 0).length;
    toast("新着", "未審査の投稿が" + pendingCount() + "件あります。");
    qToastReady = false; checkQuestions();
    setTimeout(() => { qToastReady = true; const n = qTodo().length; if (n) toast("調査メモ", "いま調べることが " + n + " 件あります。デスクトップの「調査メモ」を開いてください。"); }, 3800);
    if (retries) setTimeout(() => toast("再投稿", "却下した投稿が、" + retries + "件、再投稿されています。", "warn"), 900);
    const um = window.Apps.unread();
    if (um) setTimeout(() => { S.notify(); toast("新着メール", um + "件の未読メールがあります。"); }, 600);
    const odd = window.Apps.newOddCount();
    if (odd) setTimeout(() => toast("公開サイト", "承認した投稿に、新しいコメントが付いています。", "warn"), 1500);
    if (state.day === 2 && state.flags.day2memo) setTimeout(() => { S.notify(); toast("引き継ぎメモ.txt", "ファイルが更新されました。", "warn"); }, 1900);
  }

  $("#login-btn").addEventListener("click", boot);
  $("#login-reset").addEventListener("click", restart);
  $("#tb-mute").addEventListener("click", e => { const m = S.toggleMute(); e.currentTarget.classList.toggle("off", m); });
  window.addEventListener("keydown", e => { if (e.key === "Enter" && !$("#screen-login").classList.contains("hidden") && document.activeElement.tagName !== "BUTTON") boot(); });
  $("#login-site").textContent = D.siteName + "　管理画面";
  window.Apps.bind({ makePhoto, closeWin: id => closeWin(id, true), h, openWin, toast, S, state: () => state, save, norm, D, wins: () => wins, focus: focusWin, refreshBadges: () => updateBadge() });
  window.Gimmicks.bind({ D, S, state: () => state, save, tab: () => tab, selId: () => selId, wins: () => wins, openMemo,
    clockEl: () => $("#tb-clock"), clockMin: () => clockMin, paintClock });
  showLogin();
  window.__game = { fire: n => window.Gimmicks.fire(n), swap: () => { const e = state.queue.find(x => x.eid === selId); return e && window.Gimmicks.doSwap(e, document.querySelector(".det-body"), 2); }, state: () => state, jump: d => { /* 開発用：N日目へ飛ぶ */ while (state.day < d) { state.queue.forEach(e => { if (!state.decisions[e.eid]) state.decisions[e.eid] = "approve"; }); nextDay(); } } };
})();

// 効果音テスト：ログイン画面の「効果音テスト」（またはURLに ?sfx）で、全部の効果音を1つずつ聞ける窓が出る（何の音のつもりかも書いてある）
function openSfxPanel() {
  if (document.querySelector("#sfxpanel")) { document.querySelector("#sfxpanel").remove(); return; }
  const list = [["click", "マウスのクリック（カチ・チ）"], ["key", "キーボード（トッ）"], ["open", "窓が開く（小さなポッ）"], ["close", "窓が閉じる"], ["notify", "通知（やわらかいベルの2音）"], ["login", "ログイン（ベルの2音）"],
    ["approve", "承認（ポン）"], ["reject", "却下（ボン）"], ["hold", "保留（トントン）"], ["error", "できない・まちがい（低いボッ）"], ["found", "謎が解けた（鍵が開くカチャ＋チン）"],
    ["knock", "壁やドアをこぶしで叩く（ドン・ドン…ドン）"], ["creak", "ドアがきしむ（ギィィ）"], ["creakLow", "床がきしむ（低めのギシッ）"], ["breath", "耳元の息（鼻でスッ→口ではぁぁ）"], ["footsteps", "木の床の足音（近づく）"], ["vibrate", "机に置いたスマホが震える（ヴーッ＋カタカタ）"],
    ["noise", "電気の不調・蛍光灯がショートしかける（ジッ…ジジジッ）"], ["tickBack", "置き時計の秒針（チッ、タッ）→逆回り"], ["heartbeat", "鼓動（ドクン）"], ["relayClick", "カメラのランプが点くカチッ"], ["recBeep", "録画のピッ"],
    ["jolt", "部屋のどこかでドアが強く閉まる（バタン！）"], ["stinger", "ザッと雑音のあと、小さな耳鳴り"], ["sting", "1日の終わり（外の風と、遠くの低いうなり）"]];
  const panel = document.createElement("div"); panel.id = "sfxpanel";
  panel.append(Object.assign(document.createElement("div"), { textContent: "効果音テスト（聞いて「分かる／分からない」を教えてください）" }));
  list.forEach(([k, label]) => { const r = document.createElement("div"); r.className = "r"; const b = document.createElement("button"); b.textContent = "▶ " + k;
    b.onclick = () => { window.Snd.init(); window.Snd[k] && window.Snd[k](); }; r.append(b, label); panel.append(r); });
  const amb = document.createElement("div"); amb.className = "r";
  const bA = document.createElement("button"); bA.textContent = "▶ 部屋の音（ずっと鳴る）"; bA.onclick = () => { window.Snd.init(); window.Snd.startAmbient(); };
  const bS = document.createElement("button"); bS.textContent = "■ 止める"; bS.onclick = () => window.Snd.stopAmbient && window.Snd.stopAmbient(0.4);
  amb.append(bA, bS); panel.append(amb); document.body.append(panel);
}
if (location.search.includes("sfx")) openSfxPanel();
document.addEventListener("click", ev => { if (ev.target && ev.target.id === "login-sfx") { ev.preventDefault(); openSfxPanel(); } });
