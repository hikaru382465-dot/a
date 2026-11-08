// 段階3のアプリ：メール／公開サイト（読者コメント）／検索「さがす」／ひとこと（SNS風）
// 画面は game.js の道具（api）を借りて作る。文章は data2.js。
window.Apps = (function () {
  let api = null;
  const E = () => window.GAME_EXTRA;
  const day = () => api.state().day;
  function bind(a) { api = a; }
  const h = (...a) => api.h(...a);

  // 小さな線のアイコン（絵文字は使わない）
  const ICONS = {
    reply: '<path d="M4 12a8 8 0 1 0 3-6.2L4 4v5h5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
    comment: '<path d="M4 5h16v10H9l-4 4V15H4z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>',
    repost: '<path d="M7 7h10l-3-3M17 17H7l3 3M17 7v5M7 17v-5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
    heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>',
    views: '<path d="M5 19V11M10 19V6M15 19v-9M20 19V14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    star: '<path d="M12 4l2.4 5 5.4.6-4 3.7 1.1 5.4L12 16l-4.9 2.7 1.1-5.4-4-3.7 5.4-.6z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>',
    clip: '<path d="M8 12l6-6a3 3 0 0 1 4 4l-8 8a5 5 0 0 1-7-7l7-7" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
    eye: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.6"/>',
    fire: '<path d="M12 21c-4 0-6-2.7-6-6 0-4 4-6 4-10 2 1 4 3.5 4 6 1-1 1.5-2 1.5-3 2 2 2.5 4.5 2.5 7 0 3.3-2 6-6 6z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>',
    share: '<path d="M12 4v11M7 9l5-5 5 5M5 14v5h14v-5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
    like: '<path d="M7 11v9H4v-9zM7 11l4-7c1.5 0 2.5 1 2.2 2.6L12.6 10H19a2 2 0 0 1 2 2.3l-1.2 6A2 2 0 0 1 17.8 20H7" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>',
    back: '<path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
  };
  const ico = (n, cls) => { const sp = document.createElement("span"); sp.className = "ico " + (cls || ""); sp.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">' + ICONS[n] + "</svg>"; return sp; };
  const hashN = (t, m) => String(t).split("").reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 99991, 7) % m;
  const AV_COLORS = ["#6b8fd6", "#d67a6b", "#5fae8b", "#c49a3c", "#9a6bd6", "#d66b9e", "#4fa3b8", "#8a8f6b"];
  const avatar = (name, key, cls) => h("span", { class: "av " + (cls || ""), style: "background:" + AV_COLORS[hashN(key || name, AV_COLORS.length)] }, (name || "?").replace(/[（(].*$/, "").trim().slice(0, 1) || "?");

  // 本物の写真（Unsplash。出どころは photos/CREDITS.md）。暗く・粒を足して加工してある
  const PHOTO = { park: "photos/park.jpg", platform: "photos/platform.jpg", cafe: "photos/cafe.jpg", corridor: "photos/corridor.jpg", phone: "photos/phone.jpg", desk: "photos/desk.jpg",
    stairs: "photos/stairs.jpg", wall: "photos/wall.jpg", street: "photos/street.jpg", elevator: "photos/elevator.jpg", hospital: "photos/hospital.jpg", house: "photos/house.jpg" };
  const KIND2PHOTO = { building: "elevator", window: "cafe", room: "desk" };
  const POST_PHOTO = { L01: "stairs", L02: "corridor", L03: "hospital", L04: "phone", L05: "elevator", L06: "cafe", L07: "desk", L08: "street", L09: "wall", L10: "house",
    p01: "elevator", p02: "stairs", p03: "house", p04: "desk", p05: "platform", p06: "phone", p07: "park", p08: "cafe", p09: "wall", p10: "hospital", p11: "desk", p12: "corridor", p13: "desk", p14: "corridor", p15: "stairs", p16: "desk" };

  // ---------- メール ----------
  const visibleMails = () => E().mails.filter(m => m.day <= day());
  const unread = () => visibleMails().filter(m => !api.state().mailRead[m.id]).length;
  function openMail() {
    const st = api.state(); st.mailStar = st.mailStar || {};
    const list = h("div", { class: "ml-list" }), view = h("div", { class: "ml-view" });
    let sel = null;
    var wrap;
    function paint() {
      const ms = visibleMails().slice().sort((a, b) => b.day - a.day || (b.id < a.id ? -1 : 1));
      list.replaceChildren(h("div", { class: "ml-tools" }, h("input", { type: "checkbox", "aria-label": "すべて選択" }), h("span", { class: "ml-tool" }, "受信トレイ"), h("span", { class: "sp" }), h("span", { class: "ml-cnt" }, "1–" + ms.length + " / " + ms.length)),
        ...ms.map(m => h("div", { class: "ml-row" + (sel === m.id ? " sel" : "") + (st.mailRead[m.id] ? "" : " unread"), tabindex: "0", role: "button", onkeydown: ev => { if (ev.key === "Enter") ev.target.click(); }, onclick: () => {
          sel = m.id; st.mailRead[m.id] = true; api.save(); api.S.click(); paint(); api.refreshBadges();
        } },
          h("input", { type: "checkbox", "aria-label": "選択", onclick: ev => ev.stopPropagation() }),
          h("button", { class: "ml-star" + (st.mailStar[m.id] ? " on" : ""), "aria-label": "スター", onclick: ev => { ev.stopPropagation(); st.mailStar[m.id] = !st.mailStar[m.id]; api.save(); api.S.click(); paint(); } }, ico("star")),
          h("div", { class: "ml-mid" }, h("div", { class: "ml-from" }, m.from), h("div", { class: "ml-sub" }, m.subject, h("span", { class: "ml-snip" }, " - " + (m.body[0] || "").slice(0, 40)))),
          h("div", { class: "ml-right" }, m.att ? ico("clip", "ml-att") : null, h("span", { class: "ml-time" }, m.time)))));
      const m = ms.find(x => x.id === sel);
      if (wrap) wrap.classList.toggle("has-sel", !!m);
      view.replaceChildren(m ? h("div", { class: "ml-read" }, h("button", { class: "btn back", onclick: () => { sel = null; paint(); } }, "← 一覧"),
        h("h3", {}, m.subject),
        h("div", { class: "ml-head" }, avatar(m.from, m.addr), h("div", { class: "ml-hinfo" }, h("div", {}, h("b", {}, m.from), h("span", { class: "ml-addr" }, " <" + m.addr + ">")), h("div", { class: "ml-meta" }, "宛先：admin_0721@yobanashi-kan.example")), h("span", { class: "ml-date" }, m.time)),
        h("div", { class: "ml-body" }, m.body.map(t => h("p", {}, t))),
        m.att ? h("div", { class: "ml-attbox", tabindex: "0", role: "button", onclick: () => { api.S.click(); api.toast("ダウンロード", "「" + m.att + "」は、デスクトップにあります。"); } }, ico("clip"), h("div", {}, h("div", { class: "ml-attname" }, m.att), h("div", { class: "ml-meta" }, "1 KB"))) : null,
        h("div", { class: "ml-acts" }, h("button", { class: "btn", onclick: () => { api.S.error(); api.toast("返信できません", "このアドレスは送信専用です。"); } }, "返信"), h("button", { class: "btn", onclick: () => { api.S.error(); api.toast("転送できません", "管理者アカウントからの転送は無効になっています。"); } }, "転送")))
        : h("div", { class: "adm-empty" }, "メールを選んでください"));
    }
    wrap = h("div", { class: "ml" }, list, view);
    api.openWin("mail", "受信トレイ - 夜ばなし投稿館 メール", wrap, { w: 860, h: 480, x: 130, y: 50 });
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
  function openSite(opts) {
    opts = opts || {};
    const D3 = window.GAME_DATA3, items = approvedList();
    const name = api.D.siteName.replace("（仮）", "");
    const pubTone = e => (e.base || "").split("").reduce((a, c) => a + c.charCodeAt(0), 0) % 6;
    const rows = () => items.map(e => ({ id: e.base, title: e.title.replace("【再投稿】", ""), author: e.author, kind: e.body.join("").length > 330 ? "長編" : "短編",
      fire: 2 + ((e.base || "").charCodeAt(2) || 3) % 4, cm: visibleComments(e).length, date: "2026/10/" + String(10 + e.day).padStart(2, "0") + " " + e.time.replace("今日 ", "").replace(/^(\d)/, "0$1"), tone: pubTone(e), body: e.body, mine: true, e: e }))
      .concat(D3.legacy.map(l => Object.assign({ mine: false }, l)));
    let tab = "rank", sel = null, url = "yobanashi-kan.example", heroHost = null, heroStep = 0;
    const heroFor = r => (r.id === "p16" && api.makePhoto) ? api.makePhoto(heroStep) : picEl(r, true);
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
    const picEl = (r, whole) => { const im = document.createElement("img"); im.className = "pub-pic"; im.alt = ""; im.loading = "lazy"; im.src = PHOTO[POST_PHOTO[r.id] || "desk"]; if (whole) im.style.objectPosition = "center"; return im; };
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
        h("div", { class: "pub-cats" }, D3.cats.slice(0, 8).map(c => h("div", { class: "pub-cat" }, c))),
        h("div", { class: "pub-ad" }, h("div", { class: "pub-adimg" }, h("div", { class: "pub-adh" }, "その不眠、枕のせい？"), h("div", { class: "pub-ads" }, "寝具の専門店 ねむりや　今だけ送料無料"), h("span", { class: "pub-adb" }, "詳しくはこちら")), h("span", { class: "pub-adl" }, "PR")),
        h("div", { class: "pub-notice" }, D3.notices.map(n => h("div", { class: "pub-n" }, h("span", { class: "pub-nd" }, n.d), h("span", { class: n.hot ? "pub-nt hot" : "pub-nt" }, n.t)))),
        h("div", { class: "pub-h2" }, h("span", { class: "red" }, "怖い話"), tab === "new" ? "新着" : tab === "hall" ? "殿堂入り" : tab === "rank" ? "ランキング" : tab === "long" ? "長編" : "短編"));
      const list = listFor();
      list.forEach((r, i) => view.append(h("div", { class: "pub-row", tabindex: "0", role: "button", onclick: () => { sel = r; page.scrollTop = 0; paint(); }, onkeydown: ev => { if (ev.key === "Enter") { sel = r; paint(); } } },
        thumb(r, tab === "new" ? null : i),
        h("div", { class: "pub-info" }, h("div", { class: "pub-t" }, r.title), h("div", { class: "pub-a" }, "投稿者：" + r.author)),
        h("div", { class: "pub-side" }, h("div", { class: "pub-cnt" }, ico("fire", "fl"), String(r.fire), ico("comment", "cmi"), String(r.cm)), h("div", { class: "pub-d" }, String(r.date).split(/[ (]/)[0])))));
      view.append(h("div", { class: "pub-pager" }, h("span", { class: "pg on" }, "1"), h("span", { class: "pg" }, "2"), h("span", { class: "pg" }, "3"), h("span", { class: "pg" }, "…"), h("span", { class: "pg" }, "次へ ›"), h("div", { class: "pub-total" }, "全 " + (212 + items.length * 1) + " 件")));
      if (api.D.externalUrl) view.append(h("div", { class: "pub-ext" }, "外のサイトでも読めます：", h("a", { href: api.D.externalUrl, target: "_blank", rel: "noopener" }, name + "（外のサイトを開く）")));
      view.append(h("div", { class: "pub-foot" }, "© " + name + "　運営：管理人室　お問い合わせ　利用規約"));
    }
    function paintStory() {
      const r = sel, cs = r.mine ? visibleComments(r.e) : Array.from({ length: Math.min(r.cm, D3.legacyCm.length) }, (_, k) => {
        const c = D3.legacyCm[(hashN(r.id, D3.legacyCm.length) + k) % D3.legacyCm.length], hh = (19 + hashN(r.id + "h" + (k * 13), 11)) % 24, mm = hashN(r.id + "m" + (k * 29 + 3), 60);
        const dd = new Date(2026, +r.date.slice(5, 7) - 1, +r.date.slice(8, 10) + (hh < 22 ? 1 : 0) + hashN(r.id + "d" + k, 3));
        return { n: c.n, t: c.t, at: (dd.getMonth() + 1) + "/" + dd.getDate() + " " + String(hh).padStart(2, "0") + ":" + String(mm).padStart(2, "0") }; });
      view.append(h("div", { class: "pub-story" },
        h("button", { class: "pub-back", onclick: () => { sel = null; paint(); } }, "‹ 一覧にもどる"),
        h("div", { class: "pub-s-top" }, kindBadge(r), h("h2", {}, r.title)),
        h("div", { class: "pub-s-meta" }, "投稿者：" + r.author + "　" + r.date + "　怖い " + r.fire),
        (heroHost = h("div", { class: "pub-hero t" + r.tone }, heroFor(r))),
        r.body.map(t => h("p", {}, t)),
        h("div", { class: "pub-cmh" }, "読者コメント（" + cs.length + "）"),
        cs.length ? cs.map(c => h("div", { class: "cm" + (c.odd ? " odd" : "") }, h("span", { class: "cm-n" }, c.n), h("span", { class: "cm-t" }, c.at), h("div", {}, c.t))) : h("div", { class: "cm-none" }, "まだコメントはありません"),
        h("div", { class: "pub-form" }, h("div", { class: "pub-input" }, "名前（省略可）"), h("div", { class: "pub-input tall" }, "コメントを書く"), h("span", { class: "pub-sb" }, "投稿する")),
        h("div", { class: "pub-share" }, h("span", {}, "ツイート"), h("span", {}, "LINEで送る"), h("span", {}, "URLをコピー")),
        h("div", { class: "pub-rel" }, h("div", { class: "pub-cmh" }, "この話を読んだ人は、こちらも読んでいます"),
          rows().filter(x => x.id !== r.id).slice(1, 4).map(x => h("div", { class: "pub-relrow", onclick: () => { sel = x; page.scrollTop = 0; paint(); } }, "› " + x.title + "　（" + x.author + "）")))));
    }
    if (opts.story) { sel = rows().find(x => x.id === opts.story) || null; }
    paint();
    api.openWin("site", name + " - ブラウザ", wrap, { w: 460, h: 700, x: 520, y: 8 });
    // エンディング用の操作口：写真を差し替える／コメントを1字ずつ書く
    return {
      setStep(n) { heroStep = n; if (heroHost && sel) heroHost.replaceChildren(heroFor(sel)); },
      async typeComment(who, at, text) {
        const cmh = view.querySelector(".pub-cmh"); if (!cmh) return;
        const box = h("div", { class: "cm odd" }, h("span", { class: "cm-n" }, who), h("span", { class: "cm-t" }, at)), line = h("div"); box.append(line); cmh.after(box);
        for (const ch of text) { line.textContent += ch; api.S.key(); await new Promise(r => setTimeout(r, 110)); }
      }
    };
  }
  // 公開サイトを、指定した記事のページで開く（すでに開いていれば、いったん閉じる）
  function openSiteStory(id) { if (api.wins().site) api.closeWin("site"); return openSite({ story: id }); }
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
    if (/八階|エレベーター/.test(t)) return "elevator";
    if (/ハイツ|マンション|団地|廊下/.test(t)) return "corridor";
    if (/階段/.test(t)) return "stairs";
    if (/病院|看護/.test(t)) return "hospital";
    if (/終電|三番線|駅/.test(t)) return "platform";
    if (/公園|遊具/.test(t)) return "park";
    if (/喫茶|窓際/.test(t)) return "cafe";
    if (/染み|アパート|壁/.test(t)) return "wall";
    if (/電話|留守/.test(t)) return "phone";
    if (/夜道|街灯|住宅地/.test(t)) return "street";
    if (/実家|仏壇|祖母|空き家|町/.test(t)) return "house";
    return "desk";
  }
  // サムネイル：本物の写真を、canvasに「中央をトリミング」して描く（動画の再生ボタン・砂嵐の演出が、そのまま使える）
  function drawThumb(kind, seed, w, hh) {
    const cv = document.createElement("canvas"); cv.width = w; cv.height = hh; cv.className = "thumb";
    const g = cv.getContext("2d"); g.fillStyle = "#0d1118"; g.fillRect(0, 0, w, hh);
    const im = new Image(); im.onload = () => { const sc = Math.max(w / im.width, hh / im.height), dw = im.width * sc, dh = im.height * sc; g.drawImage(im, (w - dw) / 2, (hh - dh) / 2, dw, dh); };
    im.src = PHOTO[PHOTO[kind] ? kind : (KIND2PHOTO[kind] || "desk")];
    return cv;
  }
  function drawThumbOld(kind, seed, w, hh) {
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
  // 画面に出すURL：架空の「.example」は、見た目だけ本物らしいドメインにする（リンクはしない）
  const showUrl = u => u.replace(/^hanamizuki-town\.example/, "www.town.hanamizuki.lg.jp").replace(/\.example\b/g, ".jp");
  const siteOf = u => showUrl(u).split("/")[0];
  const FAV_COLORS = ["#1a73e8", "#d93025", "#188038", "#e37400", "#8430ce", "#007b83", "#b06000", "#5f6368"];
  const favicon = u => { const d = siteOf(u); return h("span", { class: "sr-fav", style: "background:" + FAV_COLORS[hashN(d, FAV_COLORS.length)] }, d.replace(/^www\./, "")[0].toUpperCase()); };
  const siteName = r => /^hanamizuki-town/.test(r.u) ? "はなみずき町公式ホームページ" : ((r.t.match(/(?:｜| - )([^｜]+)$/) || [])[1] || siteOf(r.u).replace(/\.(jp|com|net)$/, "")).trim();
  const views = n => n >= 10000 ? (n / 10000).toFixed(1).replace(/\.0$/, "") + "万回視聴" : n.toLocaleString() + "回視聴";
  // どんな言葉で検索しても出る、ふつうの検索結果（辞書・Q&A・地図・掲示板・フリマ）。開くと、つながらない
  function filler(q) {
    const k = hashN(q, 997), e = encodeURIComponent(q).slice(0, 18);
    return [
      { t: "「" + q + "」の意味・読み方・使い方 - ことのは辞書", u: "kotonoha-jisho.example/word/" + (1203 + k), s: q + "とは？ 意味や使い方、類語をわかりやすく解説。例文つき。", d: "2025/03/" + String(1 + k % 28).padStart(2, "0"), filler: true },
      { t: q + "について質問です - 知恵ノ輪", u: "chienowa.example/qa/q" + (4410000 + k * 37), s: "…" + q + "のことで質問です。最近気になっていて、詳しい方いたら教えてください。回答 " + (k % 5 + 1) + "件", d: "20" + (21 + k % 4) + "/" + String(1 + k % 12).padStart(2, "0") + "/" + String(3 + k % 25).padStart(2, "0"), filler: true },
      { t: q + " 周辺の地図・ルート - まちマップ", u: "machimap.example/search?q=" + e, s: q + "周辺の地図、乗換案内、天気、口コミ。営業時間や電話番号も。", filler: true },
      { t: q + " - ご近所ノート（地域掲示板）", u: "gokinjo-note.example/bbs/" + (2000 + k), s: ">>" + (3 + k % 40) + " それ知ってる。" + q + "の話でしょ？ 前にも誰か書いてた", d: "2024/" + String(1 + k % 12).padStart(2, "0") + "/" + String(2 + k % 26).padStart(2, "0"), filler: true },
      { t: "「" + q + "」の出品一覧 - ラクフリ", u: "rakufuri.example/search/" + e, s: q + " の出品 " + (k % 60 + 3) + "件。送料込み・即購入OKの商品も。", filler: true }
    ];
  }
  function openSearch(q0) {
    if (api.wins().search && searchHandle) { api.focus("search"); if (q0) searchHandle.go(q0); return; }
    const SD = E().search, st = api.state();
    const input = h("input", { class: "sr-input", placeholder: "検索、またはURLを入力", autocomplete: "off", "aria-label": "検索語" });
    const sugg = h("div", { class: "sr-sugg hidden" });
    const barBox = h("div", { class: "sr-box" }, input, sugg);
    const main = h("div", { class: "sr-main" });
    const tabsEl = h("div", { class: "sr-tabs" });
    let curQ = "", curTab = "all", wrap = null;
    const logo = cls => h("span", { class: (cls || "sr-mini") + " sr-wordmark", "aria-label": SD.siteName }, h("span", { class: "sr-moon" }), SD.siteName);
    function oddHist() { return day() >= 3 ? SD.historyOdd : []; }
    function home() {
      curQ = ""; tabsEl.classList.add("hidden"); if (wrap) wrap.classList.add("is-home");
      const hbox = h("div", { class: "sr-hbox" }, h("span", { class: "sr-glass" }, "⌕"), input, sugg); input.value = "";
      main.replaceChildren(h("div", { class: "sr-home" }, logo("sr-logo"), hbox,
        h("div", { class: "sr-hbtns" }, h("button", { class: "sr-hbtn", onclick: () => go(input.value) }, SD.siteName + "検索"), h("button", { class: "sr-hbtn", onclick: () => go(SD.suggest[hashN(Date.now(), SD.suggest.length)]) }, "今日の話題")),
        h("div", { class: "sr-foot" }, h("span", {}, "日本"), h("span", { class: "sp" }), ...["広告", "ビジネス", "検索のしくみ", "プライバシー", "規約", "設定"].map(t => h("span", {}, t)))));
    }
    function paintTabs() {
      tabsEl.classList.remove("hidden");
      tabsEl.replaceChildren(...[["all", "すべて"], ["img", "画像"], ["vid", "動画"], ["news", "ニュース"], ["map", "地図"], ["shop", "ショッピング"]].map(([k, l]) =>
        h("button", { class: "sr-tab" + (curTab === k ? " on" : ""), onclick: () => { curTab = k; api.S.click(); view(); } }, l)));
    }
    function go(q) {
      q = (q || "").trim(); sugg.classList.add("hidden");
      if (!q) return;
      if (wrap) wrap.classList.remove("is-home"); barBox.append(input, sugg); input.value = q;
      api.S.click(); curQ = q; curTab = "all";
      if (!st.searchHistory.includes(q)) { st.searchHistory.unshift(q); st.searchHistory = st.searchHistory.slice(0, 6); api.save(); }
      view();
    }
    const resultItem = (r, q) => h("div", { class: "sr-res", tabindex: "0", role: "button", onclick: () => page(r), onkeydown: e => { if (e.key === "Enter") page(r); } },
      h("div", { class: "sr-site" }, favicon(r.u), h("div", { class: "sr-sitetxt" }, h("div", { class: "sr-sname" }, siteName(r)), h("div", { class: "sr-u" }, "https://" + showUrl(r.u).replace(/\//g, " › ")))),
      h("div", { class: "sr-t" }, r.t), h("div", { class: "sr-s" }, r.d ? h("span", { class: "sr-date" }, r.d + " — ") : null, hl(r.s, q)));
    function view() {
      paintTabs();
      const real = runSearch(curQ) || [], q = curQ, all = real.concat(filler(q));
      main.scrollTop = 0;
      if (curTab === "all") {
        const ms = (0.21 + (q.length * 0.037) % 0.4).toFixed(2), cnt = (real.length ? 12000 : 800) + hashN(q, 90000);
        main.replaceChildren(h("div", { class: "sr-count" }, "約 " + cnt.toLocaleString() + " 件（" + ms + " 秒）"),
          ...all.map(r => resultItem(r, q)),
          h("div", { class: "sr-rel2" }, h("div", { class: "sr-relh" }, "他の人はこちらも検索"), h("div", { class: "sr-relgrid" }, relatedFor(q).map(x => h("span", { class: "sr-relq", tabindex: "0", role: "button", onclick: () => go(x), onkeydown: e => { if (e.key === "Enter") go(x); } }, "⌕ " + x)))),
          h("div", { class: "sr-pager" }, h("span", { class: "on" }, "1"), h("span", {}, "2"), h("span", {}, "3"), h("span", {}, "4"), h("span", {}, "次へ")));
        return;
      }
      if (curTab === "img") { main.replaceChildren(h("div", { class: "sr-grid" }, all.map((r, i) => h("div", { class: "sr-img", tabindex: "0", role: "button", onclick: () => page(r), onkeydown: e => { if (e.key === "Enter") page(r); } },
        drawThumb(sceneFor(r), 11 + i * 7 + r.t.length, 200, 130), h("div", { class: "sr-cap" }, siteOf(r.u)), h("div", { class: "sr-cap2" }, r.t.slice(0, 24) + (r.t.length > 24 ? "…" : "")))))); return; }
      if (curTab === "vid") {
        const vs = runVideos(q);
        main.replaceChildren(...(vs.length ? vs.map((v, i) => h("div", { class: "sr-vid", tabindex: "0", role: "button", onclick: () => video(v, vs), onkeydown: e => { if (e.key === "Enter") video(v, vs); } },
          vthumb(v, 23 + i * 5), h("div", {}, h("div", { class: "sr-t" }, v.t), h("div", { class: "sr-s" }, views(v.views) + "・" + v.when), h("div", { class: "sr-ch" }, avatar(v.ch, v.ch, "sm"), v.ch)))) : [h("div", { class: "sr-none" }, "「" + q + "」に一致する動画はありません。")]));
        return;
      }
      if (curTab === "news") {
        const ns = all.filter(r => /news|life|town/.test(r.u));
        main.replaceChildren(...(ns.length ? ns.map(r => resultItem(r, q)) : [h("div", { class: "sr-none" }, "「" + q + "」に一致するニュースはありません。")]));
        return;
      }
      main.replaceChildren(h("div", { class: "sr-none" }, curTab === "map" ? "地図を読み込めませんでした。（位置情報がオフになっています）" : "「" + q + "」に一致する商品はありません。"));
    }
    function vthumb(v, seed) {
      const cap = v.t.replace(/【([^】]*)】.*/, "$1") || v.t.slice(0, 6);
      return h("div", { class: "sr-vthumb" }, drawThumb(v.scene, seed, 240, 135), h("span", { class: "sr-vcap" }, cap.slice(0, 8)), h("span", { class: "sr-dur" }, v.dur));
    }
    // 記事ページ・動画ページの下に付く、コメント
    function comments(u, cmFallback) {
      const ex = E().pageExtra[u] || { views: 300 + hashN(u, 900), bm: 2 + hashN(u, 9), cm: cmFallback || [] };
      const cms = ex.cm.filter(c => !c[3] || day() >= c[3]);
      return { ex, nodes: [h("div", { class: "sr-cm-h" }, "コメント " + cms.length + "件"),
        cms.length ? cms.map((c, i) => h("div", { class: "sr-cm" + (c[3] ? " odd" : "") }, avatar(c[0], c[0] + i, "sm"), h("div", { class: "sr-cmb" }, h("div", { class: "sr-cm-top" }, h("b", {}, c[0]), h("span", { class: "sr-cm-t" }, c[2])), h("div", {}, c[1])))) : h("div", { class: "cm-none" }, "まだコメントはありません")] };
    }
    const backLink = (label, fn) => h("button", { class: "sr-backlink", onclick: fn }, ico("back"), label);
    function page(r) {
      api.S.click(); main.scrollTop = 0;
      if (r.filler) {   // ふつうの検索結果は、つながらない
        main.replaceChildren(backLink("検索結果", () => view()), h("div", { class: "sr-err" }, h("div", { class: "sr-errico" }, "☹"), h("h3", {}, "このサイトにアクセスできません"),
          h("p", {}, siteOf(r.u) + " からの応答に時間がかかりすぎています。"), h("p", { class: "sr-errcode" }, "ERR_CONNECTION_TIMED_OUT"))); api.S.error(); return;
      }
      const { ex, nodes } = comments(r.u);
      const siblings = (runSearch(curQ) || []).filter(x => x.u !== r.u);
      const sname = siteOf(r.u);
      main.replaceChildren(backLink("検索結果", () => view()),
        h("div", { class: "sr-webpage" },
          h("div", { class: "sr-wphead", style: "background:" + (/lg\.jp$/.test(sname) ? "#2d6a4f" : FAV_COLORS[hashN(sname, FAV_COLORS.length)]) }, h("b", {}, siteName(r)), h("span", { class: "sp" }), h("span", {}, "ホーム"), h("span", {}, "カテゴリ"), h("span", {}, "お問い合わせ")),
          h("div", { class: "sr-page" }, h("div", { class: "sr-crumb" }, "ホーム › " + (r.t.split(/[｜|\-]/).pop() || "").trim()), h("h3", {}, r.t.split(/[｜|]/)[0].trim()),
            h("div", { class: "sr-pmeta" }, (r.d ? r.d + "　" : "") + "閲覧 " + ex.views.toLocaleString() + "　", ico("star"), " " + ex.bm), r.page.map(t => h("p", {}, t)),
            r.link ? h("a", { class: "sr-extlink", href: api.D.externalUrl + "#" + r.link.hash, target: "_blank", rel: "noopener" }, r.link.label + " ›") : null,
            h("div", { class: "sr-share" }, "この記事をシェア：", h("span", {}, "ポスト"), h("span", {}, "LINE"), h("span", {}, "URLをコピー")),
            nodes,
            siblings.length ? h("div", { class: "sr-rel" }, h("div", { class: "sr-cm-h" }, "関連記事"), siblings.map(x => h("div", { class: "sr-relitem", tabindex: "0", role: "button", onclick: () => page(x), onkeydown: ev => { if (ev.key === "Enter") page(x); } }, x.t))) : null),
          h("div", { class: "sr-wpfoot" }, "© " + siteName(r) + "　プライバシーポリシー　運営者情報")));
    }
    function video(v, list) {
      api.S.click(); main.scrollTop = 0;
      const ctrl = h("div", { class: "sr-ctrl" }, h("span", { class: "sr-cplay" }, "▶"), h("span", { class: "sr-ctime" }, "0:00 / " + v.dur), h("div", { class: "sr-cbar" }, h("div", { class: "sr-cbuf" })), h("span", {}, "🔊"), h("span", {}, "⚙"), h("span", {}, "⛶"));
      const screen = h("div", { class: "sr-player" }, drawThumb(v.scene, 31, 640, 360), h("button", { class: "sr-bigplay", "aria-label": "再生" }, "▶"), ctrl);
      const { nodes } = comments(v.u, v.cm);
      screen.querySelector("button").addEventListener("click", async () => {
        const c = screen.querySelector("canvas"), g = c.getContext("2d"); api.S.noise();
        for (let i = 0; i < 14; i++) { const id = g.createImageData(c.width, c.height); for (let k = 0; k < id.data.length; k += 4) { const n = Math.random() * 90; id.data[k] = id.data[k + 1] = id.data[k + 2] = n; id.data[k + 3] = 255; } g.putImageData(id, 0, 0); await new Promise(r => setTimeout(r, 60)); }
        g.fillStyle = "#000"; g.fillRect(0, 0, c.width, c.height); g.fillStyle = "#cfd6e6"; g.font = "18px sans-serif"; g.textAlign = "center"; g.fillText("エラーが発生しました。しばらくしてからもう一度お試しください。", c.width / 2, c.height / 2);
        screen.querySelector("button").remove(); api.S.error();
      });
      const subs = (hashN(v.ch, 90) / 10 + 0.3).toFixed(1).replace(/\.0$/, "");
      const others = (list || []).filter(x => x !== v);
      main.replaceChildren(backLink("動画の検索結果", () => view()),
        h("div", { class: "sr-vpage" }, h("div", { class: "sr-vmain" }, screen, h("h3", { class: "sr-vtitle" }, v.t),
          h("div", { class: "sr-chrow" }, avatar(v.ch, v.ch), h("div", { class: "sr-chinfo" }, h("b", {}, v.ch), h("div", { class: "sr-chsub" }, "チャンネル登録者数 " + subs + "万人")), h("span", { class: "sr-subbtn" }, "登録"), h("span", { class: "sp" }),
            h("span", { class: "sr-pill" }, ico("like"), " " + (Math.round(v.views / 37) + hashN(v.t, 30)).toLocaleString()), h("span", { class: "sr-pill" }, ico("share"), " 共有")),
          h("div", { class: "sr-desc" }, h("b", {}, views(v.views) + "　" + v.when), h("div", {}, v.desc)), nodes),
          others.length ? h("div", { class: "sr-vside" }, ...others.map((x, i) => h("div", { class: "sr-vrel", tabindex: "0", role: "button", onclick: () => video(x, list) }, vthumb(x, 41 + i), h("div", {}, h("div", { class: "sr-vrt" }, x.t), h("div", { class: "sr-s" }, x.ch), h("div", { class: "sr-s" }, views(x.views)))))) : null));
    }
    function showSugg() {
      const v = input.value.trim();
      const hist = st.searchHistory.concat(oddHist());
      const base = SD.suggest.concat(day() >= 3 ? SD.suggestOdd : []);
      const items = v ? base.filter(x => x.includes(v)).map(x => [x, false]) : hist.slice(0, 4).map(x => [x, true]).concat(base.slice(0, 4).map(x => [x, false]));
      sugg.replaceChildren(...items.slice(0, 8).map(([x, isH]) => h("div", { class: "sr-sg" + (day() >= 3 && (SD.suggestOdd.includes(x) || SD.historyOdd.includes(x)) ? " odd" : ""), tabindex: "0", role: "button", onmousedown: e => e.preventDefault(), onclick: () => go(x), onkeydown: e => { if (e.key === "Enter") go(x); } }, h("span", { class: "sr-sgi" }, isH ? "🕘" : "⌕"), x)));
      sugg.classList.toggle("hidden", !items.length);
    }
    input.addEventListener("input", () => { api.S.key(); showSugg(); });
    input.addEventListener("focus", showSugg);
    input.addEventListener("blur", () => setTimeout(() => sugg.classList.add("hidden"), 150));
    input.addEventListener("keydown", e => { if (e.key === "Enter") go(input.value); });
    const logoBtn = h("button", { class: "sr-logobtn", "aria-label": "トップにもどる", onclick: () => { api.S.click(); home(); } }, logo("sr-mini"));
    wrap = h("div", { class: "sr" }, h("div", { class: "sr-bar" }, logoBtn, barBox), tabsEl, main);
    api.openWin("search", SD.siteName + " - 検索", wrap, { w: 900, h: 600, x: 170, y: 30 });
    searchHandle = { go };
    home();
    if (q0) go(q0);
  }

  // ---------- ひとこと（SNS風） ----------
  function openSns() {
    const feed = h("div", { class: "sn-feed" }), side = h("div", { class: "sn-side" });
    let sel = null;
    // 新しい順（「12分」「3時間」「2:41」「10月12日」を、何分前かに直して並べる）
    const ago = t => { let m; if ((m = /^(\d+)分/.exec(t))) return +m[1]; if ((m = /^(\d+)時間/.exec(t))) return +m[1] * 60; if ((m = /^(\d{1,2}):(\d{2})/.exec(t))) return Math.max(0, 161 - (+m[1] * 60 + +m[2])); if ((m = /(\d+)月(\d+)日/.exec(t))) return 100000 - (+m[1] * 31 + +m[2]); return 9999; };
    const items = () => E().sns.filter(s => s.day <= day()).sort((a, b) => ago(a.time) - ago(b.time) || (b.id < a.id ? -1 : 1));
    const num = n => n >= 10000 ? (n / 10000).toFixed(1).replace(/\.0$/, "") + "万" : n >= 1000 ? n.toLocaleString() : String(n);
    function paint() {
      feed.replaceChildren(h("div", { class: "sn-head" }, h("span", { class: "on" }, "おすすめ"), h("span", {}, "フォロー中")),
        ...items().map(s => { const rp = hashN(s.id + "r", 4) + (s.likes > 10 ? 2 : 0), rt = hashN(s.id + "t", 3) + Math.floor(s.likes / 6), vw = s.likes * 41 + 37 + hashN(s.id, 400);
        return h("div", { class: "sn-item" + (sel === s ? " sel" : ""), onclick: () => { sel = s; api.S.click(); paint(); } }, avatar(s.name, s.handle),
          h("div", { class: "sn-body" }, h("div", { class: "sn-top" }, h("b", {}, s.name), h("span", { class: "sn-h" }, "@" + s.handle + " · " + s.time)),
            h("div", { class: "sn-text" }, s.text),
            h("div", { class: "sn-acts" }, h("span", {}, ico("comment"), rp ? String(rp) : ""), h("span", {}, ico("repost"), rt ? String(rt) : ""), h("span", {}, ico("heart"), s.likes ? String(s.likes) : ""), h("span", {}, ico("views"), num(vw))))); }));
      const trends = [["日本のトレンド", "台風22号", "4.6万件のポスト"], ["エンタメ・トレンド", "#新作ドラマ", "1.2万件のポスト"], ["日本のトレンド", "#夜ふかし", "8,317件のポスト"], ["地域", "はなみずき町", "412件のポスト"]].concat(day() >= 3 ? [["トレンド", "02:41", "87件のポスト"]] : []);
      side.replaceChildren(...[
        sel ? h("div", { class: "sn-card" }, avatar(sel.name, sel.handle, "big"), h("h3", {}, sel.name), h("div", { class: "sn-h" }, "@" + sel.handle),
          h("div", { class: "sn-stat" }, h("b", {}, String(hashN(sel.handle, 300) + 12)), " フォロー　", h("b", {}, String(hashN(sel.handle + "f", 900) + 3)), " フォロワー"), h("div", { class: "sn-h" }, "登録：" + (sel.handle === "admin_0721" ? "2026年10月" : "20" + (14 + hashN(sel.handle, 10)) + "年" + (1 + hashN(sel.handle + "m", 12)) + "月"))) : null,
        h("div", { class: "sn-box" }, h("div", { class: "sn-box-h" }, "いまどうしてる？"), ...trends.map(t => h("div", { class: "sn-tr" }, h("div", { class: "sn-h" }, t[0]), h("b", {}, t[1]), h("div", { class: "sn-h" }, t[2])))),
        h("div", { class: "sn-box" }, h("div", { class: "sn-box-h" }, "おすすめユーザー"), ...[["怪談まとめ垢", "kaidan_matome"], ["夜更かし猫", "yofukashi_neko"]].map(([n, hd]) => h("div", { class: "sn-rec" }, avatar(n, hd), h("div", {}, h("b", {}, n), h("div", { class: "sn-h" }, "@" + hd)), h("span", { class: "sn-follow" }, "フォロー"))))].filter(Boolean));
    }
    api.openWin("sns", "ひとこと", h("div", { class: "sn" }, feed, side), { w: 760, h: 520, x: 240, y: 50 });
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
  return { bind, iconDefs, unread, onApprove, newOddCount, openMail, decorate, openSiteStory };
})();
