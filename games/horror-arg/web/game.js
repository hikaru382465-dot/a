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

  // ---------- 状態（ブラウザに保存。開発用に ?reset で消せる） ----------
  const KEY = "horror-arg-v1";
  let state = { decisions: {}, found: {}, memoExtra: [], day: 1 };
  try {
    if (location.search.includes("reset")) localStorage.removeItem(KEY);
    const raw = localStorage.getItem(KEY);
    if (raw) state = Object.assign(state, JSON.parse(raw));
  } catch (e) { /* 保存できなくても遊べる */ }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }

  const posts = D.posts.filter(p => p.day === state.day);
  const statusOf = id => state.decisions[id] || "pending";
  const pendingCount = () => posts.filter(p => statusOf(p.id) === "pending").length;

  // ---------- 時計（ゲーム内。02:41から進む） ----------
  let clockMin = (() => { const [a, b] = D.clockStart.split(":").map(Number); return a * 60 + b; })();
  const clockStr = () => String(Math.floor(clockMin / 60) % 24).padStart(2, "0") + ":" + String(clockMin % 60).padStart(2, "0");
  function paintClock() {
    $("#tb-clock").textContent = clockStr();
    $("#login-clock").textContent = clockStr();
  }
  setInterval(() => { clockMin++; paintClock(); }, 60000);
  paintClock();
  $("#login-date").textContent = "日付は、いつも通り。";
  $("#login-site").textContent = D.siteName + "　管理画面";

  // ---------- トースト ----------
  function toast(title, text, kind) {
    const t = h("div", { class: "toast " + (kind || "") }, h("div", { class: "tt" }, title), text);
    const box = $("#toasts"); box.append(t);
    while (box.children.length > 3) box.firstChild.remove();
    setTimeout(() => { t.style.transition = "opacity .5s"; t.style.opacity = "0"; setTimeout(() => t.remove(), 520); }, 5200);
  }

  // ---------- ウィンドウ管理 ----------
  const wins = {};
  let zTop = 10;
  function focusWin(id) {
    Object.keys(wins).forEach(k => {
      const w = wins[k];
      const on = k === id && !w.min;
      w.el.classList.toggle("inactive", !on);
      w.tb.classList.toggle("active", on);
    });
    if (wins[id]) wins[id].el.style.zIndex = ++zTop;
  }
  function openWin(id, title, body, o) {
    if (wins[id]) {
      wins[id].min = false; wins[id].el.style.display = "flex"; focusWin(id); return wins[id];
    }
    o = Object.assign({ w: 640, h: 440, x: 120, y: 40 }, o || {});
    const dw = $("#desktop").clientWidth, dh = $("#desktop").clientHeight;
    o.w = Math.min(o.w, dw - 20); o.h = Math.min(o.h, dh - 20);
    o.x = Math.max(0, Math.min(o.x, dw - o.w)); o.y = Math.max(0, Math.min(o.y, dh - o.h));
    const tEl = h("span", { class: "t" }, title);
    const bMin = h("button", { title: "最小化" }, "–");
    const bX = h("button", { class: "x", title: "閉じる" }, "×");
    const bar = h("div", { class: "win-title" }, tEl, bMin, bX);
    const el = h("div", { class: "win", style: `left:${o.x}px;top:${o.y}px;width:${o.w}px;height:${o.h}px` },
      bar, h("div", { class: "win-body" }, body));
    const tb = h("div", { class: "tb-item" }, title);
    $("#desktop").append(el); $("#tb-items").append(tb);
    const w = { el, tb, min: false, titleEl: tEl, onClose: o.onClose };
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
    // ドラッグ
    bar.addEventListener("pointerdown", ev => {
      if (ev.target.tagName === "BUTTON") return;
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
  function closeWin(id) {
    const w = wins[id]; if (!w) return;
    if (w.onClose) w.onClose();
    w.el.remove(); w.tb.remove(); delete wins[id]; S.close();
  }

  // ---------- 管理画面 ----------
  let selId = null, renderAdmin = () => {};
  function openAdmin() {
    const top = h("div", { class: "adm-top" },
      h("span", { class: "site" }, D.siteName), h("span", { class: "tag" }, "管理画面"), h("span", { class: "sp" }),
      h("span", { class: "who" }, "管理者：" + D.adminName));
    const list = h("div", { class: "adm-list" });
    const detail = h("div", { class: "adm-detail" });
    const bPend = h("span");
    const bCmp = h("button", { class: "btn", onclick: () => { S.click(); openCompare(); } }, "類似チェック");
    const bEnd = h("button", { class: "btn primary", onclick: () => endDay() }, "本日の審査を終了");
    const bottom = h("div", { class: "adm-bottom" }, bPend, h("span", { class: "sp" }), bCmp, bEnd);
    const body = h("div", { style: "display:flex;flex-direction:column;height:100%" },
      top, h("div", { class: "adm-main" }, list, detail), bottom);

    function statusLabel(s) { return { pending: "未審査", approve: "承認", reject: "却下", hold: "保留" }[s]; }
    renderAdmin = function () {
      list.replaceChildren(...posts.map(p => {
        const s = statusOf(p.id);
        return h("div", { class: "adm-row" + (selId === p.id ? " sel" : ""), onclick: () => { selId = p.id; S.click(); renderAdmin(); } },
          h("div", { class: "r1" }, h("span", { class: "ttl" }, p.title), h("span", { class: "st " + s }, statusLabel(s))),
          h("div", { class: "r2" }, h("span", {}, p.author), h("span", {}, p.time)));
      }));
      const p = posts.find(x => x.id === selId);
      if (!p) {
        detail.replaceChildren(h("div", { class: "adm-empty" }, "左の一覧から投稿を選んでください"));
      } else {
        const dec = d => {
          state.decisions[p.id] = d; save();
          if (d === "approve") { S.approve(); toast("公開しました", "「" + p.title + "」を外部の公開サイトに掲載しました。", "ok"); }
          if (d === "reject") { S.reject(); toast("却下しました", "投稿者には通知されません。", "bad"); }
          if (d === "hold") { S.hold(); openMemo(); toast("保留にしました", "前任者の引き継ぎメモを開きました。", "warn"); }
          renderAdmin();
        };
        const cur = statusOf(p.id);
        detail.replaceChildren(
          h("div", { class: "det-head" }, h("h2", {}, p.title),
            h("div", { class: "det-meta" },
              h("span", {}, "投稿者：", h("b", {}, p.author)),
              h("span", {}, "ID：", h("b", {}, p.authorId)),
              h("span", {}, "投稿：", h("b", {}, p.time)),
              h("span", {}, "端末：", h("b", {}, p.device)))),
          h("div", { class: "det-body" }, p.body.map(t => h("p", {}, t))),
          h("div", { class: "det-foot" },
            h("button", { class: "btn ok", onclick: () => dec("approve") }, cur === "approve" ? "承認済み" : "承認"),
            h("button", { class: "btn ng", onclick: () => dec("reject") }, cur === "reject" ? "却下済み" : "却下"),
            h("button", { class: "btn hold", onclick: () => dec("hold") }, "保留"),
            h("span", { class: "note" }, "承認すると、外部の公開サイトに掲載されます。")));
      }
      const n = pendingCount();
      bPend.textContent = n > 0 ? "未審査：" + n + "件" : "未審査：なし";
      updateBadge();
    };
    openWin("admin", D.siteName + " 管理画面", body, { w: 880, h: 520, x: 90, y: 20 });
    renderAdmin();
  }

  // ---------- メモ帳 ----------
  function openMemo() {
    const body = h("div", { class: "memo-body", id: "memo-body" });
    const status = h("div", { class: "memo-status", id: "memo-status" }, "引き継ぎメモ.txt　最終更新：前任者");
    const lines = D.memo.concat(state.memoExtra);
    lines.forEach(t => body.append(h("p", {}, t)));
    openWin("memo", "引き継ぎメモ.txt - メモ帳", h("div", { style: "display:flex;flex-direction:column;height:100%" }, body, status),
      { w: 500, h: 380, x: 770, y: 60 });
  }
  async function appendMemo(text) {
    state.memoExtra.push(text); save();
    const w = wins.memo;
    if (!w) { toast("引き継ぎメモ.txt", "ファイルが更新されました。", "warn"); return; }
    const body = $("#memo-body"), status = $("#memo-status");
    status.textContent = "このファイルは外部で更新されました"; status.classList.add("alert");
    const p = h("p", { class: "new" }); body.append(p);
    for (const ch of text) { p.textContent += ch; S.key(); body.scrollTop = body.scrollHeight; await sleep(70 + Math.random() * 60); }
  }

  // ---------- 類似チェック ----------
  function openCompare() {
    const sources = posts.map(p => ({ key: p.id, label: p.title, paras: p.body }))
      .concat([{ key: "memo", label: "引き継ぎメモ.txt", paras: D.memo.concat(state.memoExtra) }]);
    let pickA = null, pickB = null, fails = 0;
    const selA = h("select"), selB = h("select");
    sources.forEach((s, i) => { selA.append(h("option", { value: s.key }, s.label)); selB.append(h("option", { value: s.key }, s.label)); });
    selA.value = sources[0].key; selB.value = sources[1].key;
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
    function tagOf(sn) {
      for (const k in D.tags) if (sn.includes(D.tags[k])) return k;
      return null;
    }
    function check() {
      if (!pickA || !pickB) { S.error(); msg.className = "cmp-msg bad"; msg.textContent = "左右から1文ずつ選んでください。"; return; }
      const ta = tagOf(pickA), tb = tagOf(pickB);
      if (selA.value === selB.value) { S.error(); msg.className = "cmp-msg bad"; msg.textContent = "同じ文章どうしは比べられません。"; return; }
      if (ta && ta === tb) {
        document.querySelectorAll(".cmp-col .picked").forEach(x => { x.classList.remove("picked"); x.classList.add("match"); });
        msg.className = "cmp-msg good";
        msg.textContent = "一致を検出しました。同じ言い回しが、別の投稿者の文章に含まれています。";
        const first = !state.found[ta];
        state.found[ta] = true; save();
        if (first) {
          S.found();
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
    const body = h("div", { style: "display:flex;flex-direction:column;height:100%" },
      h("div", { class: "cmp-bar" }, "文章A", selA, "文章B", selB),
      h("div", { class: "cmp-cols" }, colA, colB),
      h("div", { class: "cmp-foot" }, msg, go));
    openWin("cmp", "類似チェック", body, { w: 820, h: 480, x: 130, y: 50 });
    paint();
  }

  // ---------- デスクトップのアイコン ----------
  let badgeEl = null;
  function updateBadge() { if (badgeEl) { const n = pendingCount(); badgeEl.textContent = n; badgeEl.style.display = n ? "" : "none"; } }
  function buildIcons() {
    const mk = (label, glyph, color, fn, withBadge) => {
      const g = h("div", { class: "glyph", style: "background:" + color }, glyph);
      const el = h("div", { class: "icon" }, g, label);
      el.addEventListener("click", () => { document.querySelectorAll(".icon").forEach(i => i.classList.remove("sel")); el.classList.add("sel"); S.click(); });
      el.addEventListener("dblclick", fn);
      if (withBadge) { badgeEl = h("span", { class: "badge" }, "0"); el.append(badgeEl); }
      return el;
    };
    $("#icons").append(
      mk("管理画面", "✉", "linear-gradient(135deg,#3b78e0,#2759b5)", openAdmin, true),
      mk("引き継ぎメモ", "✎", "linear-gradient(135deg,#d9a93a,#a97a14)", openMemo, false));
    updateBadge();
  }

  // ---------- 1日の終わり ----------
  async function endDay() {
    const cnt = { approve: 0, reject: 0, hold: 0, pending: 0 };
    posts.forEach(p => cnt[statusOf(p.id)]++);
    if (cnt.pending > 0) { S.error(); toast("まだ終われません", "未審査の投稿が" + cnt.pending + "件あります。", "warn"); return; }
    S.click();
    const scr = $("#screen-end"), box = $("#end-box");
    $("#screen-desk").classList.add("hidden"); scr.classList.remove("hidden");
    box.innerHTML = "";
    const line = async (cls, text, wait) => {
      const d = h("div", { class: cls }); box.append(d);
      for (const ch of text) { d.textContent += ch; await sleep(36); }
      await sleep(wait || 500);
      return d;
    };
    S.sting();
    await line("big", state.day + "日目の審査を終了しました。", 700);
    const mk = (a, b) => { const r = h("div", { class: "row" }, h("span", {}, a), h("span", {}, b)); box.append(r); };
    mk("承認", cnt.approve + "件"); await sleep(250);
    mk("却下", cnt.reject + "件"); await sleep(250);
    mk("保留", cnt.hold + "件"); await sleep(900);
    box.append(h("div", { style: "height:18px" }));
    await line("dim", "ログアウトします。", 900);
    await line("dim", "次回のログイン予定：明日 02:41", 1100);
    const x = await line("dim flick", "前回のログイン：02:38（アカウント削除済み）", 1400);
    await line("dim", "", 200);
    box.append(h("div", { class: "dim", style: "margin-top:26px" }, "— 試作 第1段階はここまで —"));
    box.append(h("button", { class: "btn", style: "margin-top:14px", onclick: () => { try { localStorage.removeItem(KEY); } catch (e) {} location.href = location.pathname + "?reset"; } }, "最初からやり直す"));
  }

  // ---------- 起動の流れ ----------
  async function boot() {
    S.init(); S.login();
    $("#screen-login").classList.add("hidden");
    const bs = $("#screen-boot"), bt = $("#boot-text");
    bs.classList.remove("hidden");
    const lines = ["認証しています…", "ログインしました。", "前任の管理人は退会済みです。"];
    for (const l of lines) {
      bt.textContent += (bt.textContent ? "\n" : "");
      for (const ch of l) { bt.textContent += ch; S.key(); await sleep(55); }
      await sleep(600);
    }
    await sleep(500);
    bs.classList.add("hidden");
    $("#screen-desk").classList.remove("hidden");
    buildIcons(); S.startAmbient();
    await sleep(1400);
    S.notify();
    toast("新着", "未審査の投稿が" + pendingCount() + "件あります。管理画面をダブルクリックで開いてください。");
  }
  $("#login-btn").addEventListener("click", boot);
  $("#tb-mute").addEventListener("click", e => { const m = S.toggleMute(); e.currentTarget.classList.toggle("off", m); });
  window.addEventListener("keydown", e => { if (e.key === "Enter" && !$("#screen-login").classList.contains("hidden")) boot(); });
})();
