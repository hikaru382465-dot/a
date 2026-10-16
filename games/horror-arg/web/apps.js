// 段階3のアプリ：メール／公開サイト（読者コメント）／検索「さがす」／ひとこと（SNS風）
// 画面は game.js の道具（api）を借りて作る。文章は data2.js。
window.Apps = (function () {
  let api = null;
  const E = () => window.GAME_EXTRA;
  const day = () => api.state().day;
  function bind(a) { api = a; }
  const h = (...a) => api.h(...a);

  // ---------- メール ----------
  const visibleMails = () => E().mails.filter(m => m.day <= day());
  const unread = () => visibleMails().filter(m => !api.state().mailRead[m.id]).length;
  function openMail() {
    const st = api.state();
    const list = h("div", { class: "ml-list" }), view = h("div", { class: "ml-view" });
    let sel = null;
    var wrap;
    function paint() {
      const ms = visibleMails().slice().sort((a, b) => b.day - a.day || (b.id < a.id ? -1 : 1));
      list.replaceChildren(...ms.map(m => h("div", { class: "ml-row" + (sel === m.id ? " sel" : "") + (st.mailRead[m.id] ? "" : " unread"), tabindex: "0", role: "button", onkeydown: ev => { if (ev.key === "Enter") ev.target.click(); }, onclick: () => {
        sel = m.id; st.mailRead[m.id] = true; api.save(); api.S.click(); paint(); api.refreshBadges();
      } }, h("div", { class: "ml-from" }, m.from), h("div", { class: "ml-sub" }, m.subject), h("div", { class: "ml-time" }, m.time))));
      const m = ms.find(x => x.id === sel);
      if (wrap) wrap.classList.toggle("has-sel", !!m);
      view.replaceChildren(m ? h("div", {}, h("button", { class: "btn back", onclick: () => { sel = null; paint(); } }, "← 一覧"),
        h("h3", {}, m.subject), h("div", { class: "ml-meta" }, "差出人：" + m.from + "　<" + m.addr + ">"), h("div", { class: "ml-meta" }, m.time),
        h("div", { class: "ml-body" }, m.body.map(t => h("p", {}, t)))) : h("div", { class: "adm-empty" }, "メールを選んでください"));
    }
    wrap = h("div", { class: "ml" }, list, view);
    api.openWin("mail", "メール", wrap, { w: 760, h: 440, x: 150, y: 60 });
    paint();
  }

  // ---------- 公開サイト（承認した投稿と、読者コメント） ----------
  function approvedList() {
    const st = api.state(), seen = {}, out = [];
    st.history.concat(st.queue).forEach(e => {
      if (st.decisions[e.eid] === "approve" && !seen[e.base]) { seen[e.base] = true; out.push(e); }
    });
    return out;
  }
  const visibleComments = e => (E().comments[e.base] || []).filter(c => !c.odd || day() > e.day);
  function openSite() {
    const items = approvedList();
    const body = h("div", { class: "site" }, h("div", { class: "site-head" }, h("div", { class: "site-logo" }, api.D.siteName.replace("（仮）", "")), h("div", { class: "site-sub" }, "みんなの怖い話　— 公開中の投稿")));
    if (!items.length) body.append(h("div", { class: "adm-empty" }, "まだ掲載された投稿はありません。管理画面で「承認」すると、ここに載ります。"));
    items.forEach(e => {
      const cs = visibleComments(e);
      body.append(h("article", { class: "site-post" },
        h("h3", {}, e.title.replace("【再投稿】", "")), h("div", { class: "site-meta" }, "投稿者：" + e.author + "　" + e.time),
        e.body.map(t => h("p", {}, t)),
        h("div", { class: "site-cm" }, h("div", { class: "site-cm-h" }, "読者コメント（" + cs.length + "）"),
          cs.length ? cs.map(c => h("div", { class: "cm" + (c.odd ? " odd" : "") }, h("span", { class: "cm-n" }, c.n), h("span", { class: "cm-t" }, c.at), h("div", {}, c.t))) : h("div", { class: "cm-none" }, "まだコメントはありません"))));
    });
    api.openWin("site", "公開サイト（読者に見える画面）", h("div", { class: "site-wrap" }, body), { w: 680, h: 500, x: 220, y: 40 });
  }
  // 承認から少し後に、読者コメントが届く（音と通知）
  function onApprove(e) {
    const st = api.state();
    if (st.commentSeen[e.base]) return; st.commentSeen[e.base] = true; api.save();
    if (!(E().comments[e.base] || []).some(c => !c.odd)) return;
    setTimeout(() => {
      if (api.state().decisions[e.eid] !== "approve" || document.querySelector("#screen-desk").classList.contains("hidden")) return;
      api.S.notify(); api.toast("読者コメント", "「" + e.title.replace("【再投稿】", "") + "」に、コメントが届きました。");
    }, 12000 + Math.random() * 6000);
  }
  // 日が変わったとき、新しい（いないはずの人の）コメントがあれば知らせる
  function newOddCount() {
    return approvedList().filter(e => (E().comments[e.base] || []).some(c => c.odd) && e.day === day() - 1).length;
  }

  // ---------- 検索「さがす」 ----------
  const norm = t => api.norm(t);
  function runSearch(q) {
    const nq = norm(q); if (!nq) return null;
    const hit = E().search.entries.filter(en => (en.minDay || 0) <= day() && en.keys.some(k => nq.includes(norm(k))));
    return hit.length ? hit.flatMap(en => en.results) : [];
  }
  let searchHandle = null;
  function openSearch(q0) {
    if (api.wins().search && searchHandle) { api.focus("search"); if (q0) searchHandle.go(q0); return; }
    const SD = E().search, st = api.state();
    const input = h("input", { class: "sr-input", placeholder: "ことばで さがす", autocomplete: "off" });
    const sugg = h("div", { class: "sr-sugg hidden" });
    const main = h("div", { class: "sr-main" });
    function oddHist() { return day() >= 3 ? SD.historyOdd : []; }
    function home() {
      const hist = st.searchHistory.concat(oddHist());
      main.replaceChildren(h("div", { class: "sr-home" }, h("div", { class: "sr-logo" }, SD.siteName),
        h("div", { class: "sr-hist-h" }, "検索履歴"),
        hist.length ? hist.map((x, i) => h("div", { class: "sr-hist" + (i >= st.searchHistory.length ? " odd" : ""), onclick: () => go(x) }, x)) : h("div", { class: "cm-none" }, "まだ履歴はありません")));
    }
    function go(q) {
      input.value = q; sugg.classList.add("hidden");
      const res = runSearch(q); api.S.click();
      if (res === null) return;
      if (!st.searchHistory.includes(q)) { st.searchHistory.unshift(q); st.searchHistory = st.searchHistory.slice(0, 6); api.save(); }
      if (!res.length) { main.replaceChildren(h("div", { class: "sr-none" }, "「" + q + "」" + SD.notFound)); api.S.error(); return; }
      main.replaceChildren(h("div", { class: "sr-count" }, "約 " + res.length + " 件"), ...res.map(r => h("div", { class: "sr-res", onclick: () => page(r, q) },
        h("div", { class: "sr-t" }, r.t), h("div", { class: "sr-u" }, r.u), h("div", { class: "sr-s" }, r.s))));
    }
    function page(r, q) {
      api.S.click();
      main.replaceChildren(h("button", { class: "btn", onclick: () => go(q) }, "← 検索結果にもどる"),
        h("div", { class: "sr-page" }, h("div", { class: "sr-u" }, r.u), h("h3", {}, r.t), r.page.map(t => h("p", {}, t))));
    }
    function showSugg() {
      const base = SD.suggest.concat(day() >= 3 ? SD.suggestOdd : []);
      const v = input.value.trim();
      const items = v ? base.filter(x => x.includes(v)) : base;
      sugg.replaceChildren(...items.slice(0, 6).map((x, i) => h("div", { class: "sr-sg" + (day() >= 3 && SD.suggestOdd.includes(x) ? " odd" : ""), onclick: () => go(x) }, x)));
      sugg.classList.toggle("hidden", !items.length);
    }
    input.addEventListener("input", () => { api.S.key(); showSugg(); });
    input.addEventListener("focus", showSugg);
    input.addEventListener("keydown", e => { if (e.key === "Enter") go(input.value.trim()); });
    api.openWin("search", "さがす", h("div", { class: "sr" }, h("div", { class: "sr-bar" }, h("span", { class: "sr-mini" }, SD.siteName), h("div", { class: "sr-box" }, input, sugg),
      h("button", { class: "btn primary", onclick: () => go(input.value.trim()) }, "さがす")), main), { w: 720, h: 500, x: 190, y: 40 });
    searchHandle = { go };
    home();
    if (q0) go(q0);
  }

  // ---------- ひとこと（SNS風） ----------
  function openSns() {
    const feed = h("div", { class: "sn-feed" }), prof = h("div", { class: "sn-prof" });
    let sel = null;
    const items = () => E().sns.filter(s => s.day <= day()).sort((a, b) => b.id < a.id ? -1 : 1);
    function paint() {
      feed.replaceChildren(...items().map(s => h("div", { class: "sn-item", onclick: () => { sel = s; api.S.click(); paint(); } },
        h("div", { class: "sn-top" }, h("b", {}, s.name), h("span", { class: "sn-h" }, "@" + s.handle), h("span", { class: "sn-time" }, s.time)),
        h("div", { class: "sn-text" }, s.text), h("div", { class: "sn-likes" }, "♡ " + s.likes))));
      prof.replaceChildren(sel ? h("div", {}, h("div", { class: "sn-av" }, sel.name.slice(0, 1)), h("h3", {}, sel.name), h("div", { class: "sn-h" }, "@" + sel.handle),
        h("table", { class: "sn-tbl" },
          [["登録", "昨日 02:41"], ["フォロー", "1（新管理人）"], ["フォロワー", "0"], ["ひとこと", sel.handle === "admin_0721" ? "1" : "3"]].map(r => h("tr", {}, h("td", {}, r[0]), h("td", {}, r[1]))))) :
        h("div", { class: "adm-empty small" }, "ひとことを選ぶと、プロフィールが見られます"));
    }
    api.openWin("sns", "ひとこと", h("div", { class: "sn" }, feed, prof), { w: 640, h: 460, x: 260, y: 70 });
    paint();
  }

  // 本文の「調べられる言葉」に下線をつける（2日目から）。押すと「さがす」が開く
  function decorate(e, bodyEl) {
    if (day() < 2) return;
    const words = E().terms[e.base] || [];
    let any = false;
    words.forEach(w => {
      for (const p of bodyEl.querySelectorAll("p")) {
        const tn = [...p.childNodes].find(n => n.nodeType === 3 && n.textContent.includes(w));
        if (!tn) continue;
        const i = tn.textContent.indexOf(w);
        const mid = tn.splitText(i); mid.splitText(w.length);
        const span = h("span", { class: "term", title: "「さがす」で調べる", onclick: () => { api.S.click(); openSearch(w); } }, w);
        mid.replaceWith(span); any = true; break;
      }
    });
    const st = api.state();
    if (any && !st.flags.termHint) {
      st.flags.termHint = true; api.save();
      setTimeout(() => api.toast("ヒント", "本文の下線の言葉は、タップすると「さがす」で調べられます。"), 1200);
    }
  }

  // ---------- アイコンの定義（game.js が使う） ----------
  function iconDefs() {
    const d = day(), out = [];
    out.push({ key: "mail", label: "メール", glyph: "✉", color: "linear-gradient(135deg,#4c9b6f,#2c6e4a)", fn: openMail, badge: unread });
    out.push({ key: "site", label: "公開サイト", glyph: "◎", color: "linear-gradient(135deg,#c9784a,#8f4a25)", fn: openSite });
    if (d >= 2) out.push({ key: "search", label: "さがす", glyph: "⌕", color: "linear-gradient(135deg,#3b8bb0,#215f80)", fn: () => openSearch() });
    if (d >= 3) out.push({ key: "sns", label: "ひとこと", glyph: "✦", color: "linear-gradient(135deg,#b04f8a,#7a2f5f)", fn: openSns });
    return out;
  }
  return { bind, iconDefs, unread, onApprove, newOddCount, openMail, decorate };
})();
