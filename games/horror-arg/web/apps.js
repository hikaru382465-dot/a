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
    const D3 = window.GAME_DATA3, items = approvedList();
    const name = api.D.siteName.replace("（仮）", "");
    const pubTone = e => (e.base || "").split("").reduce((a, c) => a + c.charCodeAt(0), 0) % 6;
    const rows = () => items.map(e => ({ id: e.base, title: e.title.replace("【再投稿】", ""), author: e.author, kind: e.body.join("").length > 330 ? "長編" : "短編",
      fire: 2 + ((e.base || "").charCodeAt(2) || 3) % 4, cm: visibleComments(e).length, date: "2026/10/" + String(10 + e.day).padStart(2, "0") + " " + e.time.replace("今日 ", "").replace(/^(\d)/, "0$1"), tone: pubTone(e), body: e.body, mine: true, e: e }))
      .concat(D3.legacy.map(l => Object.assign({ mine: false }, l)));
    let tab = "rank", sel = null, url = "yobanashi-kan.example";
    // 見ていない間に写真が変わる：閉じていた（見ていなかった）時間が20秒以上あると、1段進む
    const fl = api.state().flags, nowMs = Date.now();
    if (day() >= (api.D.gimmicks.siteDrift || 99) && fl.siteSeen && nowMs - fl.siteSeen > 20000 && !location.search.includes("nogimmick")) { fl.drift = Math.min(4, (fl.drift || 0) + 1); api.save(); }
    const drift = fl.drift || 0;
    const seen = () => { fl.siteSeen = Date.now(); };
    seen();
    const view = h("div", { class: "pub" });
    const bar = h("div", { class: "pub-bar" });
    const page = h("div", { class: "pub-scroll" }, view);
    const wrap = h("div", { class: "pub-wrap" }, bar, page);
    const kindBadge = r => h("span", { class: "pub-kind " + (r.kind === "長編" ? "long" : "short") }, r.kind);
    const PICS = [
      '<path d="M28 60V14h28v46M52 38v3" stroke="#bcd" fill="none" stroke-width="2"/>',
      '<path d="M0 50L30 40H84M0 22L30 30H84" stroke="#ccd" fill="none" stroke-width="1.6" opacity=".7"/><rect x="38" y="30" width="8" height="10" fill="#111"/>',
      '<circle cx="42" cy="26" r="9" fill="#050505"/><path d="M26 60Q42 34 58 60Z" fill="#050505"/>',
      '<rect x="22" y="10" width="40" height="40" fill="none" stroke="#dde" stroke-width="2"/><path d="M42 10V50M22 30H62" stroke="#dde" stroke-width="1.4"/><circle cx="52" cy="22" r="4" fill="#000" opacity=".7"/>',
      '<path d="M10 56H74M16 48H68M22 40H62M28 32H56" stroke="#dde" stroke-width="2" opacity=".75"/>',
      '<path d="M42 12Q60 12 60 30H24Q24 12 42 12ZM42 30V54Q42 58 38 58" stroke="#cdb" fill="none" stroke-width="2"/>'];
    // 見ていない間に、写真の端に写る人影が少しずつ近く・大きくなる（見るたびに1段）
    const driftSvg = L => { const x = 78 - L * 9, h = 10 + L * 8, r = 2 + L * 1.2, y = 60 - h;
      return '<g opacity="' + (0.45 + L * 0.12) + '"><circle cx="' + x + '" cy="' + (y - r + 1) + '" r="' + r + '" fill="#050505"/><path d="M' + (x - r * 1.6) + ' 60 q' + (r * .4) + ' -' + (h - r) + ' ' + (r * 1.6) + ' -' + (h - r) + ' q' + (r * 1.2) + ' 0 ' + (r * 1.6) + ' ' + (h - r) + 'z" fill="#050505"/>' + (L >= 4 ? '<ellipse cx="' + x + '" cy="' + (y - r + 1) + '" rx="' + r * .5 + '" ry="' + r * .7 + '" fill="#e8e0d0" opacity=".55"/>' : "") + "</g>"; };
    const DRIFT_IDS = ["L01", "L03", "L05"];
    const picEl = (r, whole) => { const n = ({ L01: 4, L02: 3, L03: 2, L04: 1, L05: 0, L06: 5, L07: 1, L08: 2, L09: 0, L10: 0 })[r.id] ?? (r.id || "").split("").reduce((a, c) => a + c.charCodeAt(0), 0) % PICS.length; const s = document.createElementNS("http://www.w3.org/2000/svg", "svg"); s.setAttribute("class", "pub-pic"); s.setAttribute("viewBox", "0 0 84 60"); s.innerHTML = PICS[n] + (drift > 0 && DRIFT_IDS.includes(r.id) ? driftSvg(drift) : ""); s.setAttribute("preserveAspectRatio", whole ? "xMidYMid meet" : "xMidYMid slice"); return s; };
    const unused = r => { const n = ({ L01: 4, L02: 3, L03: 2, L04: 1, L05: 0, L06: 5, L07: 1, L08: 2, L09: 0, L10: 0 })[r.id] ?? (r.id || "").split("").reduce((a, c) => a + c.charCodeAt(0), 0) % PICS.length; return h("svg", { class: "pub-pic", viewBox: "0 0 84 60", "aria-hidden": "true", innerhtml: "" }); };
    const thumb = (r, i) => h("div", { class: "pub-thumb t" + r.tone }, picEl(r), i != null ? h("span", { class: "pub-rk" + (i < 3 ? " top" : "") }, String(i + 1)) : null, kindBadge(r));
    function listFor() {
      let r = rows();
      if (tab === "rank") r = r.sort((a, b) => b.fire - a.fire);
      else if (tab === "new") r = r.sort((a, b) => (a.date < b.date ? 1 : -1));
      else if (tab === "hall") r = r.filter(x => !x.mine).sort((a, b) => b.fire - a.fire).slice(0, 5);
      else r = r.filter(x => x.kind === (tab === "long" ? "長編" : "短編")).sort((a, b) => b.fire - a.fire);
      return r;
    }
    function paint() {
      seen();
      const tabs = [["rank", "ランキング"], ["new", "新着"], ["hall", "殿堂入り"]];
      bar.replaceChildren(
        h("div", { class: "pub-nav" }, h("button", { class: "pub-navbtn", "aria-label": "戻る", onclick: () => { if (sel) { sel = null; paint(); } } }, "‹"), h("button", { class: "pub-navbtn", "aria-label": "更新", onclick: paint }, "↻")),
        h("div", { class: "pub-url" }, h("span", { class: "pub-lock" }, "🔒"), sel ? url + "/story/" + sel.id : url + (tab === "rank" ? "/" : "/" + tab)));
      view.replaceChildren();
      if (sel) return paintStory();
      view.append(
        h("div", { class: "pub-head" }, h("div", { class: "pub-logo" }, h("span", { class: "red" }, name.slice(0, 4)), name.slice(4)), h("div", { class: "pub-post" }, "怖い話を投稿")),
        h("div", { class: "pub-search" }, h("span", { class: "pub-sq" }, "キーワードで怖い話を探す"), h("span", { class: "pub-sb" }, "検索")),
        h("div", { class: "pub-tabs" }, tabs.map(([k, l]) => h("button", { class: "pub-tab" + (tab === k ? " on" : ""), onclick: () => { tab = k; paint(); } }, l))),
        h("div", { class: "pub-cats" }, D3.cats.slice(0, 8).map((c, i) => h("div", { class: "pub-cat" }, c.length > 2 ? [h("span", { class: "red" }, c.slice(0, 2)), c.slice(2)] : h("span", { class: "red" }, c)))),
        h("div", { class: "pub-ad" }, h("span", { class: "pub-adl" }, "広告"), h("div", { class: "pub-adt" }, "眠れない夜に。遮光カーテン・防音シート 特集"), h("span", { class: "pub-adb" }, "詳しく見る")),
        h("div", { class: "pub-notice" }, D3.notices.map(n => h("div", { class: "pub-n" }, h("span", { class: "pub-nd" }, "📣 " + n.d), h("span", { class: n.hot ? "pub-nt hot" : "pub-nt" }, n.t)))),
        h("div", { class: "pub-h2" }, h("span", { class: "red" }, "怖い話"), tab === "new" ? "新着" : tab === "hall" ? "殿堂入り" : tab === "rank" ? "ランキング" : tab === "long" ? "長編" : "短編"));
      const list = listFor();
      list.forEach((r, i) => view.append(h("div", { class: "pub-row", tabindex: "0", role: "button", onclick: () => { sel = r; page.scrollTop = 0; paint(); }, onkeydown: ev => { if (ev.key === "Enter") { sel = r; paint(); } } },
        thumb(r, tab === "new" ? null : i),
        h("div", { class: "pub-info" }, h("div", { class: "pub-t" }, r.title), h("div", { class: "pub-a" }, "投稿者：" + r.author)),
        h("div", { class: "pub-side" }, h("div", { class: "pub-cnt" }, h("span", { class: "fl" }, "🔥"), String(r.fire), h("span", { class: "cmi" }, "💬"), String(r.cm)), h("div", { class: "pub-d" }, r.date)))));
      view.append(h("div", { class: "pub-pager" }, h("span", { class: "pg on" }, "1"), h("span", { class: "pg" }, "2"), h("span", { class: "pg" }, "3"), h("span", { class: "pg" }, "…"), h("span", { class: "pg" }, "次へ ›"), h("div", { class: "pub-total" }, "全 " + (212 + items.length * 1) + " 件")));
      if (api.D.externalUrl) view.append(h("div", { class: "pub-ext" }, "外のサイトでも読めます：", h("a", { href: api.D.externalUrl, target: "_blank", rel: "noopener" }, name + "（外のサイトを開く）")));
      view.append(h("div", { class: "pub-foot" }, "© " + name + "　運営：管理人室　お問い合わせ　利用規約"));
    }
    function paintStory() {
      const r = sel, cs = r.mine ? visibleComments(r.e) : D3.legacyCm.slice(0, Math.min(r.cm, 4)).map((c, k) => ({ n: c.n, t: c.t, at: "2026/" + r.date.slice(5, 10) + " " + String((22 + k) % 24).padStart(2, "0") + ":" + String(10 + k * 7).padStart(2, "0") }));
      view.append(h("div", { class: "pub-story" },
        h("button", { class: "pub-back", onclick: () => { sel = null; paint(); } }, "‹ 一覧にもどる"),
        h("div", { class: "pub-s-top" }, kindBadge(r), h("h2", {}, r.title)),
        h("div", { class: "pub-s-meta" }, "投稿者：" + r.author + "　" + r.date + "　🔥 " + r.fire),
        h("div", { class: "pub-hero t" + r.tone }, picEl(r, true)),
        r.body.map(t => h("p", {}, t)),
        h("div", { class: "pub-cmh" }, "読者コメント（" + cs.length + "）"),
        cs.length ? cs.map(c => h("div", { class: "cm" + (c.odd ? " odd" : "") }, h("span", { class: "cm-n" }, c.n), h("span", { class: "cm-t" }, c.at), h("div", {}, c.t))) : h("div", { class: "cm-none" }, "まだコメントはありません"),
        h("div", { class: "pub-form" }, h("div", { class: "pub-input" }, "名前（省略可）"), h("div", { class: "pub-input tall" }, "コメントを書く"), h("span", { class: "pub-sb" }, "投稿する")),
        h("div", { class: "pub-share" }, h("span", {}, "ツイート"), h("span", {}, "LINEで送る"), h("span", {}, "URLをコピー")),
        h("div", { class: "pub-rel" }, h("div", { class: "pub-cmh" }, "この話を読んだ人は、こちらも読んでいます"),
          rows().filter(x => x.id !== r.id).slice(1, 4).map(x => h("div", { class: "pub-relrow", onclick: () => { sel = x; page.scrollTop = 0; paint(); } }, "› " + x.title + "　（" + x.author + "）")))));
    }
    paint();
    api.openWin("site", name + " - ブラウザ", wrap, { w: 460, h: 700, x: 520, y: 8 });
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
  // ---------- 検索「ヨルサガシ」（架空の検索エンジン） ----------
  let searchHandle = null;
  // 画像・動画のサムネイル：暗い場面を絵で描く（kind で場面を変える）
  function sceneFor(r) {
    const t = r.t + r.u + r.s;
    if (/八階|エレベーター|ハイツ|マンション/.test(t)) return "building";
    if (/階段|病院/.test(t)) return "stairs";
    if (/終電|三番線|駅/.test(t)) return "platform";
    if (/公園|遊具/.test(t)) return "park";
    if (/喫茶|窓際/.test(t)) return "window";
    if (/染み|アパート|壁/.test(t)) return "wall";
    if (/電話|留守/.test(t)) return "phone";
    return "room";
  }
  function drawThumb(kind, seed, w, hh) {
    const cv = document.createElement("canvas"); cv.width = w; cv.height = hh; cv.className = "thumb";
    const g = cv.getContext("2d");
    let sd = seed || 7; const rnd = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
    const bg = g.createLinearGradient(0, 0, 0, hh); bg.addColorStop(0, "#0a0d14"); bg.addColorStop(1, "#171d2a");
    g.fillStyle = bg; g.fillRect(0, 0, w, hh);
    const R = (x, y, ww, h2, c) => { g.fillStyle = c; g.fillRect(x * w, y * hh, ww * w, h2 * hh); };
    if (kind === "building") { R(.15, .05, .7, .95, "#10151f"); for (let i = 0; i < 8; i++) for (let j = 0; j < 5; j++) R(.2 + j * .13, .1 + i * .11, .07, .06, (i === 0 && j === 2) ? "#f2d78b" : (rnd() < .12 ? "#6c7a96" : "#0c1018")); }
    if (kind === "stairs") { for (let i = 0; i < 9; i++) R(.1 + i * .08, .85 - i * .09, .9 - (.1 + i * .08), .09, "#" + (i % 2 ? "151b27" : "1c2433")); R(.5, .02, .03, .6, "#2a3446"); }
    if (kind === "platform") { R(0, .72, 1, .28, "#141a25"); R(0, .72, 1, .02, "#c9b458"); R(.62, .1, .06, .62, "#222a3a"); R(.64, .25, .02, .35, "#050609"); }
    if (kind === "park") { R(0, .75, 1, .25, "#101611"); g.strokeStyle = "#2a3446"; g.lineWidth = w * .012; g.beginPath(); g.arc(.5 * w, .5 * hh, .22 * hh, 0, 7); g.stroke(); g.beginPath(); g.moveTo(.5 * w, .5 * hh); g.lineTo(.5 * w, .78 * hh); g.stroke(); R(.47, .68, .06, .1, "#050609"); }
    if (kind === "window") { R(.2, .15, .6, .6, "#e6c27a"); R(.2, .15, .6, .02, "#0a0d14"); R(.49, .15, .02, .6, "#0a0d14"); R(.4, .55, .2, .2, "#6b4d22"); R(0, .75, 1, .25, "#0b0e13"); }
    if (kind === "wall") { R(0, 0, 1, 1, "#161b24"); g.fillStyle = "#0a0c11"; g.beginPath(); g.ellipse(.5 * w, .3 * hh, .06 * w, .1 * hh, 0, 0, 7); g.fill(); g.beginPath(); g.moveTo(.42 * w, .9 * hh); g.quadraticCurveTo(.42 * w, .45 * hh, .5 * w, .42 * hh); g.quadraticCurveTo(.58 * w, .45 * hh, .58 * w, .9 * hh); g.fill(); }
    if (kind === "phone") { R(.38, .1, .24, .8, "#1a2230"); R(.41, .14, .18, .5, "#cfe0ff"); R(.44, .7, .12, .1, "#0b0e13"); }
    if (kind === "room") { R(0, .7, 1, .3, "#10151f"); R(.3, .25, .4, .3, "#6f85b8"); R(.45, .55, .1, .12, "#1a2130"); R(.62, .4, .08, .3, "#05070a"); }
    const id = g.getImageData(0, 0, w, hh), d = id.data;
    for (let i = 0; i < d.length; i += 4) { const n = (rnd() - .5) * 22; d[i] += n; d[i + 1] += n; d[i + 2] += n; }
    g.putImageData(id, 0, 0);
    return cv;
  }
  function hl(text, q) {   // 検索語を太字にする
    const words = q.split(/[\s　]+/).filter(Boolean).filter(w => w.length > 0);
    const out = []; let rest = text;
    while (rest) {
      let best = -1, bw = "";
      words.forEach(w => { const i = rest.indexOf(w); if (i >= 0 && (best < 0 || i < best)) { best = i; bw = w; } });
      if (best < 0) { out.push(rest); break; }
      if (best > 0) out.push(rest.slice(0, best));
      out.push(h("b", {}, bw)); rest = rest.slice(best + bw.length);
    }
    return out;
  }
  const relatedFor = q => {
    const SD = E().search, all = SD.suggest.slice();
    return all.filter(x => x !== q).sort(() => 0.5 - Math.random()).slice(0, 4);
  };
  function runVideos(q) {
    const nq = norm(q); if (!nq) return [];
    return E().search.entries.filter(en => (en.minDay || 0) <= day() && en.keys.some(k => nq.includes(norm(k)))).flatMap(en => en.videos || []);
  }
  function openSearch(q0) {
    if (api.wins().search && searchHandle) { api.focus("search"); if (q0) searchHandle.go(q0); return; }
    const SD = E().search, st = api.state();
    const input = h("input", { class: "sr-input", placeholder: "ことばで さがす", autocomplete: "off", "aria-label": "検索語" });
    const sugg = h("div", { class: "sr-sugg hidden" });
    const main = h("div", { class: "sr-main" });
    const tabsEl = h("div", { class: "sr-tabs" });
    let curQ = "", curTab = "all";
    const logo = (cls) => h("span", { class: cls || "sr-mini", "aria-label": SD.siteName }, [...SD.siteName].map((c, i) => h("span", { style: "color:" + ["#4f8df5", "#e0586b", "#f0b840", "#4f8df5", "#3fb37f"][i % 5] }, c)));
    function oddHist() { return day() >= 3 ? SD.historyOdd : []; }
    function home() {
      curQ = ""; tabsEl.classList.add("hidden");
      const hist = st.searchHistory.concat(oddHist());
      main.replaceChildren(h("div", { class: "sr-home" }, logo("sr-logo"),
        h("div", { class: "sr-hist-h" }, "よく検索されていることば"),
        h("div", {}, SD.suggest.map(x => h("span", { class: "sr-hist", tabindex: "0", role: "button", onclick: () => go(x), onkeydown: e => { if (e.key === "Enter") go(x); } }, x))),
        h("div", { class: "sr-hist-h" }, "検索履歴"),
        hist.length ? h("div", {}, hist.map((x, i) => h("span", { class: "sr-hist" + (i >= st.searchHistory.length ? " odd" : ""), tabindex: "0", role: "button", onclick: () => go(x), onkeydown: e => { if (e.key === "Enter") go(x); } }, x))) : h("div", { class: "cm-none" }, "まだ履歴はありません")));
    }
    function paintTabs() {
      tabsEl.classList.remove("hidden");
      tabsEl.replaceChildren(...[["all", "すべて"], ["img", "画像"], ["vid", "動画"], ["news", "ニュース"]].map(([k, l]) =>
        h("button", { class: "sr-tab" + (curTab === k ? " on" : ""), onclick: () => { curTab = k; api.S.click(); view(); } }, l)));
    }
    function go(q) {
      q = (q || "").trim(); input.value = q; sugg.classList.add("hidden");
      const res = runSearch(q); api.S.click();
      if (res === null) return;
      curQ = q; curTab = "all";
      if (!st.searchHistory.includes(q)) { st.searchHistory.unshift(q); st.searchHistory = st.searchHistory.slice(0, 6); api.save(); }
      view();
    }
    function view() {
      paintTabs();
      const res = runSearch(curQ) || [], q = curQ;
      if (!res.length && curTab !== "vid") { main.replaceChildren(h("div", { class: "sr-none" }, "「" + q + "」" + SD.notFound, h("div", { class: "sr-tip" }, "ことばを変えて、もう一度さがしてみてください。"))); api.S.error(); return; }
      if (curTab === "all") {
        const ms = (0.18 + (q.length * 0.037) % 0.4).toFixed(2);
        main.replaceChildren(h("div", { class: "sr-count" }, "約 " + res.length + " 件（" + ms + " 秒）"),
          ...res.map(r => h("div", { class: "sr-res", tabindex: "0", role: "button", onclick: () => page(r), onkeydown: e => { if (e.key === "Enter") page(r); } },
            h("div", { class: "sr-site" }, h("span", { class: "sr-fav" }, r.u[0].toUpperCase()), h("span", { class: "sr-u" }, r.u.replace(/\//g, " › "))),
            h("div", { class: "sr-t" }, r.t), h("div", { class: "sr-s" }, hl(r.s, q)))),
          h("div", { class: "sr-rel2" }, h("div", { class: "sr-hist-h" }, "ほかにも検索されています"), relatedFor(q).map(x => h("span", { class: "sr-hist", tabindex: "0", role: "button", onclick: () => go(x), onkeydown: e => { if (e.key === "Enter") go(x); } }, x))),
          h("div", { class: "sr-pager" }, h("span", { class: "on" }, "1"), h("span", {}, "2"), h("span", {}, "3"), h("span", {}, "次へ")));
      }
      if (curTab === "img") main.replaceChildren(h("div", { class: "sr-grid" }, res.map((r, i) => h("div", { class: "sr-img", tabindex: "0", role: "button", onclick: () => page(r), onkeydown: e => { if (e.key === "Enter") page(r); } },
        drawThumb(sceneFor(r), 11 + i * 7 + r.t.length, 200, 130), h("div", { class: "sr-cap" }, r.t.slice(0, 22) + (r.t.length > 22 ? "…" : ""))))));
      if (curTab === "vid") {
        const vs = runVideos(q);
        main.replaceChildren(...(vs.length ? vs.map((v, i) => h("div", { class: "sr-vid", tabindex: "0", role: "button", onclick: () => video(v), onkeydown: e => { if (e.key === "Enter") video(v); } },
          h("div", { class: "sr-vthumb" }, drawThumb(v.scene, 23 + i * 5, 200, 118), h("span", { class: "sr-play" }, "▶"), h("span", { class: "sr-dur" }, v.dur)),
          h("div", {}, h("div", { class: "sr-t" }, v.t), h("div", { class: "sr-s" }, v.ch + "　" + v.views.toLocaleString() + "回視聴　" + v.when)))) : [h("div", { class: "sr-none" }, "「" + q + "」に一致する動画は見つかりませんでした。")]));
      }
      if (curTab === "news") {
        const ns = res.filter(r => /news|life/.test(r.u));
        main.replaceChildren(...(ns.length ? ns.map(r => h("div", { class: "sr-res", tabindex: "0", role: "button", onclick: () => page(r), onkeydown: e => { if (e.key === "Enter") page(r); } },
          h("div", { class: "sr-site" }, h("span", { class: "sr-fav" }, "N"), h("span", { class: "sr-u" }, "はなみずき町のおしらせ")), h("div", { class: "sr-t" }, r.t), h("div", { class: "sr-s" }, hl(r.s, q)))) : [h("div", { class: "sr-none" }, "「" + q + "」に一致するニュースは見つかりませんでした。")]));
      }
    }
    // 記事ページ・動画ページの下に付く、反応とコメント
    function extras(u, title, cmFallback) {
      const ex = E().pageExtra[u] || { views: 300 + (u.length * 37) % 900, bm: 5, cm: cmFallback || [] };
      const cms = ex.cm.filter(c => !c[3] || day() >= c[3]);
      const react = (label, n) => { const b = h("button", { class: "btn rx" }, label + "　" + n); let on = false; b.addEventListener("click", () => { on = !on; b.classList.toggle("on", on); b.textContent = label + "　" + (n + (on ? 1 : 0)); api.S.click(); }); return b; };
      return { ex, nodes: [
        h("div", { class: "sr-rx" }, react("役に立った", Math.round(ex.views / 60)), react("こわい", Math.round(ex.views / 45)), react("ブックマーク", ex.bm)),
        h("div", { class: "sr-cm-h" }, "コメント（" + cms.length + "）"),
        cms.length ? cms.map((c, i) => h("div", { class: "sr-cm" + (c[3] ? " odd" : "") }, h("div", { class: "sr-cm-top" }, h("span", { class: "sr-cm-no" }, (i + 1) + "."), h("b", {}, c[0]), h("span", { class: "sr-cm-t" }, c[2])), h("div", {}, c[1]))) : h("div", { class: "cm-none" }, "まだコメントはありません")] };
    }
    function page(r) {
      api.S.click();
      const { ex, nodes } = extras(r.u);
      const siblings = (runSearch(curQ) || []).filter(x => x.u !== r.u);
      main.replaceChildren(h("button", { class: "btn", onclick: () => view() }, "← 検索結果にもどる"),
        h("div", { class: "sr-page" }, h("div", { class: "sr-u" }, r.u), h("h3", {}, r.t),
          h("div", { class: "sr-pmeta" }, "閲覧数 " + ex.views.toLocaleString() + "　ブックマーク " + ex.bm), r.page.map(t => h("p", {}, t)),
          r.link ? h("a", { class: "btn primary ext", href: api.D.externalUrl + "#" + r.link.hash, target: "_blank", rel: "noopener" }, r.link.label) : null,
          nodes,
          siblings.length ? h("div", { class: "sr-rel" }, h("div", { class: "sr-cm-h" }, "関連ページ"), siblings.map(x => h("div", { class: "sr-relitem", tabindex: "0", role: "button", onclick: () => page(x), onkeydown: ev => { if (ev.key === "Enter") page(x); } }, x.t))) : null));
    }
    function video(v) {
      api.S.click();
      const screen = h("div", { class: "sr-player" }, drawThumb(v.scene, 31, 360, 200), h("button", { class: "sr-bigplay", "aria-label": "再生" }, "▶"));
      const { nodes } = extras(v.u, v.t, v.cm);
      screen.querySelector("button").addEventListener("click", async () => {
        const c = screen.querySelector("canvas"), g = c.getContext("2d"); api.S.noise();
        for (let i = 0; i < 14; i++) { const id = g.createImageData(c.width, c.height); for (let k = 0; k < id.data.length; k += 4) { const n = Math.random() * 90; id.data[k] = id.data[k + 1] = id.data[k + 2] = n; id.data[k + 3] = 255; } g.putImageData(id, 0, 0); await new Promise(r => setTimeout(r, 90)); }
        g.fillStyle = "#000"; g.fillRect(0, 0, c.width, c.height); g.fillStyle = "#cfd6e6"; g.font = "14px sans-serif"; g.textAlign = "center"; g.fillText("この動画は、再生できません。", c.width / 2, c.height / 2);
        screen.querySelector("button").remove(); api.S.error();
      });
      main.replaceChildren(h("button", { class: "btn", onclick: () => view() }, "← 動画にもどる"),
        h("div", { class: "sr-page" }, screen, h("h3", {}, v.t), h("div", { class: "sr-pmeta" }, v.ch + "　" + v.views.toLocaleString() + "回視聴　" + v.when), h("p", {}, v.desc), nodes));
    }
    function showSugg() {
      const base = SD.suggest.concat(day() >= 3 ? SD.suggestOdd : []);
      const v = input.value.trim();
      const items = v ? base.filter(x => x.includes(v)) : base;
      sugg.replaceChildren(...items.slice(0, 6).map((x, i) => h("div", { class: "sr-sg" + (day() >= 3 && SD.suggestOdd.includes(x) ? " odd" : ""), tabindex: "0", role: "button", onclick: () => go(x), onkeydown: e => { if (e.key === "Enter") go(x); } }, x)));
      sugg.classList.toggle("hidden", !items.length);
    }
    input.addEventListener("input", () => { api.S.key(); showSugg(); });
    input.addEventListener("focus", showSugg);
    input.addEventListener("keydown", e => { if (e.key === "Enter") go(input.value); });
    const logoBtn = h("button", { class: "sr-logobtn", "aria-label": "トップにもどる", onclick: () => { input.value = ""; api.S.click(); home(); } }, logo("sr-mini"));
    api.openWin("search", SD.siteName + " - 検索", h("div", { class: "sr" }, h("div", { class: "sr-bar" }, logoBtn, h("div", { class: "sr-box" }, input, sugg),
      h("button", { class: "btn primary", onclick: () => go(input.value) }, "さがす")), tabsEl, main), { w: 740, h: 520, x: 190, y: 36 });
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
