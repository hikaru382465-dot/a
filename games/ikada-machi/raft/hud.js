// 画面の表示：左上の小さな状態、右下の持ち物ボタン、下から出るシート（持ち物／作る）、置くモード、ひとこと、嵐の雨
window.RAFT.parts.hud = function (c) {
  const { state: s, R } = c, D = R.data, sim = R.sim;
  const $ = id => document.getElementById(id);
  c.mode = c.mode || { place: null };
  c.ui = c.ui || { open: false };
  c.aim = c.aim || { active: false, x: 0, z: 0, power: 0 };
  let tab = 'inv', sel = null;
  const times = [[0.2, '朝'], [0.62, '昼'], [0.78, '夕'], [1.01, '夜']];
  const timeName = t => times.find(x => t < x[0])[1];
  const toast = (msg, ms) => { const e = $('toast'); if (!msg) { e.style.opacity = 0; return; } e.textContent = msg; e.style.opacity = 1; clearTimeout(toast.h); toast.h = setTimeout(() => e.style.opacity = 0, ms || 2400); };
  const iconOf = k => c.itemIcon ? c.itemIcon(k) : null;
  const paint = (cv, k) => { const g = cv.getContext('2d'); g.clearRect(0, 0, cv.width, cv.height); const ic = k && iconOf(k); if (!ic) return; g.imageSmoothingEnabled = false;
    let sc = Math.min(cv.width / ic.width, cv.height / ic.height); if (sc >= 1) sc = Math.floor(sc);
    const w = Math.round(ic.width * sc), h = Math.round(ic.height * sc); g.drawImage(ic, Math.round((cv.width - w) / 2), Math.round((cv.height - h) / 2), w, h); };
  const nameOf = k => (D.ITEMS[k] || D.TOOLS[k] || {}).name || k;

  // ---- 本の形のメニュー：左のページ＝枠の一覧、右のページ＝くわしい説明と使うボタン ----
  function slots() {
    const a = [];
    s.tools.forEach(k => a.push({ key: k, t: 'tool', k, name: D.TOOLS[k].name, n: k === 'net' ? 'Lv' + s.net.lv : '', tip: D.TOOLS[k].tip, hand: s.hand === k }));
    Object.keys(D.ITEMS).forEach(k => {
      if ((s.inv[k] || 0) <= 0) return; const it = D.ITEMS[k];
      a.push({ key: k, t: it.place ? 'place' : (it.food || it.drink) ? 'food' : 'mat', k, name: it.name, n: s.inv[k], tip: it.tip });
    });
    return a;
  }
  function recipes() {
    return D.RECIPES.filter(r => !(r.special === 'fix' && !s.tools.includes(r.tool))).map(r => {
      const net = r.special === 'net', nx = net ? sim.nextNet(s) : null, ck = sim.canCraft(s, r);
      return { key: r.id, t: 'recipe', r, net, nx, ck, k: net ? 'net' : r.special === 'fix' ? r.tool : (r.special === 'rod' ? 'rod' : r.out), name: net ? (nx ? '網を強く' : '網（最大）') : r.special === 'fix' ? D.TOOLS[r.tool].name + 'を直す' : (r.special === 'rod' ? D.TOOLS.rod.name : D.ITEMS[r.out].name), n: '' };
    });
  }
  const r_have = o => o.r.special === 'rod' ? 'もう持っている' : 'もう持っている（イカダに1つ）';
  function renderBook() {
    const list = tab === 'inv' ? slots() : recipes();
    if (!list.some(o => o.key === sel)) sel = list.length ? list[0].key : null;
    const fill = Math.max(12, Math.ceil(list.length / 4) * 4) - list.length;
    $('grid').innerHTML = list.map(o => `<button class="slot${o.key === sel ? ' sel' : ''}${o.hand ? ' hand' : ''}${o.ck && o.ck.why === 'locked' ? ' lock' : ''}" data-key="${o.key}"><canvas width="32" height="32" data-k="${o.k}"></canvas><span class="nm">${o.name}</span>${o.n !== '' ? `<span class="n">${o.n}</span>` : ''}</button>`).join('') + '<div class="slot empty"></div>'.repeat(fill);
    $('grid').querySelectorAll('canvas').forEach(cv => paint(cv, cv.dataset.k));
    $('grid').querySelectorAll('button.slot').forEach(b => b.onclick = () => { sel = b.dataset.key; renderBook(); });
    const o = list.find(x => x.key === sel), d = $('detail');
    if (!o) { d.innerHTML = '<div class="hint">まだ何も持っていません。<br>網を投げて、物をあつめよう。</div>'; return; }
    let html = `<div class="big"><canvas width="56" height="56" data-k="${o.k}"></canvas><div><b>${o.name}</b>${o.t === 'tool' ? (o.hand ? '<br><span class="tag">手に持っている</span>' : '') : o.t === 'recipe' ? '' : `<br><span class="tag">×${o.n}</span>`}</div></div>`;
    let btn = '', onclick = null;
    if (o.t === 'recipe') {
      const cost = o.net ? (o.nx ? o.nx.cost : null) : o.r.cost, tip = o.net && o.nx ? `${o.r.tip}（とどく${o.nx.range}マス・${o.nx.cap}個）` : o.r.tip;
      html += `<p>${tip}</p>` + (cost ? '<ul class="cost">' + Object.keys(cost).map(k => `<li class="${(s.inv[k] || 0) >= cost[k] ? '' : 'no'}">${nameOf(k)}　${s.inv[k] || 0} / ${cost[k]}</li>`).join('') + '</ul>' : '');
      const why = { locked: '作業台を置くと作れる', have: r_have(o), max: 'これ以上は強くできない', full: 'まだ新品同様', short: '材料がたりない' }[o.ck.why];
      if (why) html += `<p class="why">${why}</p>`;
      btn = o.r.special === 'fix' ? '直す' : '作る'; onclick = () => { sim.craft(s, o.r.id); refresh(); };
      html += `<button id="act" ${o.ck.ok ? '' : 'disabled'}>${btn}</button>`;
    } else {
      html += `<p>${o.tip || ''}</p>`;
      if (o.t === 'tool') { const du = Math.round(s.dur[o.k]); html += `<p class="${du <= D.DUR.low ? 'why' : ''}">じょうぶさ ${du}%${du <= 0 ? '（ぼろぼろ：遠くへ飛ばない・1個しか取れない）' : du <= D.DUR.low ? '（もうすぐ壊れる：作業台で直せる）' : ''}</p>`; }
      btn = o.t === 'tool' ? (o.hand ? 'しまう' : '手に持つ') : o.t === 'food' ? (D.ITEMS[o.k].drink ? '飲む' : '食べる') : o.t === 'place' ? '置く' : '';
      if (btn) { html += `<button id="act">${btn}</button>`; onclick = () => { if (o.t === 'tool') { sim.hold(s, o.k); closeSheet(); } else if (o.t === 'food') sim.use(s, o.k); else if (o.t === 'place') startPlace(o.k); refresh(); }; }
    }
    d.innerHTML = html;
    d.querySelectorAll('canvas').forEach(cv => paint(cv, cv.dataset.k));
    if (onclick) $('act').onclick = onclick;
  }
  function setTab(t) { if (t !== tab) sel = null; tab = t; $('tInv').classList.toggle('on', t === 'inv'); $('tCraft').classList.toggle('on', t === 'craft'); renderBook(); }
  function openSheet(t) { cancelPlace(); c.ui.open = true; $('sheet').classList.add('open'); setTab(t || tab); }
  function closeSheet() { c.ui.open = false; $('sheet').classList.remove('open'); }
  // ---- 置くモード ----
  function startPlace(k) {
    const cands = sim.placeCandidates(s, k);
    if (!cands.length) { toast(k === 'floor' ? 'これ以上は広げられない（8×8まで）' : 'イカダがせまくて置けない。まず「床板」で広げよう', 3500); return; }
    c.mode.place = { k }; c.setHighlight && c.setHighlight(cands); closeSheet(); placeBar();
  }
  function placeBar() {
    const p = c.mode.place; $('placebar').style.display = p ? 'flex' : 'none';
    if (p) $('placeTx').textContent = `${nameOf(p.k)}を置く：光るマスをタップ（のこり${s.inv[p.k] || 0}）`;
  }
  function cancelPlace() { if (!c.mode.place) return; c.mode.place = null; c.setHighlight && c.setHighlight(null); placeBar(); }
  function tryPlace(x, z) {
    const p = c.mode.place; if (!p) return;
    if (!sim.place(s, p.k, x, z)) { toast(`マス(${x},${z})を押しました。光っているマスをタップ（2人が立っているマスには置けない）`, 3000); return; }
    {
      const cands = (s.inv[p.k] || 0) > 0 ? sim.placeCandidates(s, p.k) : [];
      if (!cands.length) cancelPlace(); else { c.setHighlight(cands); placeBar(); }
      refresh();
    }
  }
  function refresh() {
    const held = s.hand ? (s.hand === 'net' ? 'net' : s.hand) : null;
    paint($('fabIcon'), held || 'wood');
    $('fabBadge').textContent = s.hand === 'net' ? 'Lv' + s.net.lv : '';
    $('fabBadge').style.display = s.hand === 'net' ? '' : 'none';
    if (c.ui.open) renderBook();
  }
  // ---- 相棒にお願い ----
  const jobBtns = [...Object.keys(D.BUDDY.JOBS), null];
  function jobPanel() {
    const bu = s.buddy, nm = bu.job ? D.BUDDY.JOBS[bu.job].name : 'おまかせ（自由に歩く）';
    $('jobNow').textContent = `いまの仕事：${nm}`; $('mood').style.width = bu.mood + '%'; $('mood').classList.toggle('low', bu.mood < 30);
    $('jobBtns').innerHTML = jobBtns.map(k => `<button data-j="${k || ''}" class="${(bu.job || null) === k ? 'on' : ''}">${k ? D.BUDDY.JOBS[k].name : 'おまかせ'}<small>${k ? D.BUDDY.JOBS[k].tip : '仕事をやめて、自由に歩き回る'}</small></button>`).join('');
    $('jobBtns').querySelectorAll('button').forEach(b => b.onclick = () => { sim.setJob(s, b.dataset.j || null); jobPanel(); });
  }
  let lastTools = '';
  function toolsPanel() {
    const bu = s.buddy, nx = D.NET_LV[bu.net.lv], cs = c => Object.keys(c).map(k => `${nameOf(k)}${c[k]}`).join('・'), ok = c => sim.canPay(s, c) && sim.hasBench(s);
    const rows = [
      `<div class="toolrow"><span>網 Lv${bu.net.lv}　じょうぶさ ${Math.round(bu.dur.net)}%</span><span>${nx ? `<button data-t="netup" ${ok(nx.cost) ? '' : 'disabled'}>強くする（${cs(nx.cost)}）</button>` : '最大'} <button data-t="fixnet" ${bu.dur.net >= 95 || !ok(D.DUR.fixCost) ? 'disabled' : ''}>直す</button></span></div>`,
      bu.hasRod ? `<div class="toolrow"><span>釣りざお　じょうぶさ ${Math.round(bu.dur.rod)}%</span><button data-t="fixrod" ${bu.dur.rod >= 95 || !ok(D.DUR.fixCost) ? 'disabled' : ''}>直す（${cs(D.DUR.fixCost)}）</button></div>`
        : `<div class="toolrow"><span>釣りざお：まだない</span><button data-t="rod" ${ok(D.BUDDY.ROD_COST) ? '' : 'disabled'}>作る（${cs(D.BUDDY.ROD_COST)}）</button></div>`];
    const html = rows.join('') + (sim.hasBench(s) ? '' : '<div class="toolrow"><span>作業台を置くと、道具を作れる</span></div>');
    if (html === lastTools) return; lastTools = html; $('buddyTools').innerHTML = html;
    $('buddyTools').querySelectorAll('button').forEach(b => b.onclick = () => { sim.buddyTool(s, b.dataset.t); lastTools = ''; toolsPanel(); });
  }
  // ---- 焚き火（かまど）の画面：枠＋持ち物。タップ＝1つ、ドラッグ＝全部 ----
  let cfId = null; const ghost = $('dragGhost');
  const slotEl = { fish: $('sFish'), wood: $('sWood'), out: $('sOut'), iFish: $('iFish'), iWood: $('iWood'), iGrilled: $('iGrilled') };
  const setSlot = (el, k, n) => { el.classList.toggle('empty', !n); el.querySelector('i').textContent = n || ''; if (el.dataset.k !== k || el.dataset.n === undefined || (!!+el.dataset.n) !== !!n) paint(el.querySelector('canvas'), k); el.dataset.k = k; el.dataset.n = n; };
  function cfPanel() {
    const o = s.objects.find(x => x.id === cfId && x.k === 'campfire'); if (!o) { $('cfbox').style.display = 'none'; return; }
    const C = D.COOK, left = Math.max(0, Math.ceil(C.sec - (o.p || 0))), burn = sim.cfBurning(o);
    $('cfState').textContent = burn ? `燃えている：次の1匹まで あと${left}秒（木くず 燃え残り ${o.fl || 0}匹ぶん）` : (o.fi ? '燃料（木くず）を入れてください' : (o.go >= C.maxOut ? '焼き魚を取り出してください' : '魚と木くずを入れてください'));
    setSlot(slotEl.fish, 'fish', o.fi || 0); setSlot(slotEl.wood, 'wood', o.fw || 0); setSlot(slotEl.out, 'grilled', o.go || 0);
    setSlot(slotEl.iFish, 'fish', s.inv.fish || 0); setSlot(slotEl.iWood, 'wood', s.inv.wood || 0); setSlot(slotEl.iGrilled, 'grilled', s.inv.grilled || 0);
    $('cfBar').style.width = (burn ? (o.p || 0) / C.sec * 100 : 0) + '%'; $('cfFire').style.opacity = burn ? 1 : 0.3;
  }
  const openCf = id => { cfId = id; closeSheet(); $('jobbox').style.display = 'none'; $('cfbox').style.display = 'block'; cfPanel(); };
  // 動かす：from='inv'（持ち物→焚き火）／'slot'（焚き火→持ち物）。n＝1 か 'all'
  const cfMove = (what, from, n) => { const ok = from === 'inv' ? sim.cfPut(s, cfId, what, n) : sim.cfTake(s, cfId, what, n); if (ok) refresh(); cfPanel(); };
  const dropAt = (x, y) => { const e = document.elementFromPoint(x, y); const t = e && e.closest('[data-drop]'); return t ? t.dataset.drop : null; };
  const wire = (el, src) => {      // src：どの枠をつまむか。item＝持ち物の物／slot＝焚き火の枠
    let st = null;
    el.addEventListener('pointerdown', e => { const k = src.what; if (!k) return; st = { x: e.clientX, y: e.clientY, drag: false }; el.setPointerCapture(e.pointerId); });
    el.addEventListener('pointermove', e => { if (!st) return; if (!st.drag && Math.hypot(e.clientX - st.x, e.clientY - st.y) > 10) { st.drag = true; paint(ghost, src.icon); ghost.style.display = 'block'; }
      if (st.drag) { ghost.style.left = e.clientX + 'px'; ghost.style.top = e.clientY + 'px'; const d = dropAt(e.clientX, e.clientY); document.querySelectorAll('[data-drop]').forEach(q => q.classList.toggle('over', q.dataset.drop === d)); } });
    el.addEventListener('pointerup', e => { if (!st) return; const d = st; st = null; ghost.style.display = 'none'; document.querySelectorAll('[data-drop]').forEach(q => q.classList.remove('over'));
      if (!d.drag) { src.tap(); return; } const to = dropAt(e.clientX, e.clientY); src.drop(to); });
    el.addEventListener('pointercancel', () => { st = null; ghost.style.display = 'none'; });
  };
  wire(slotEl.iFish, { what: 'fish', icon: 'fish', tap: () => cfMove('fish', 'inv', 1), drop: to => { if (to === 'fish') cfMove('fish', 'inv', 'all'); } });
  wire(slotEl.iWood, { what: 'wood', icon: 'wood', tap: () => cfMove('wood', 'inv', 1), drop: to => { if (to === 'wood') cfMove('wood', 'inv', 'all'); } });
  wire(slotEl.iGrilled, { what: 'grilled', icon: 'grilled', tap: () => {}, drop: () => {} });
  wire(slotEl.fish, { what: 'fish', icon: 'fish', tap: () => cfMove('fish', 'slot', 1), drop: to => { if (to === 'inv' || to === null) cfMove('fish', 'slot', 'all'); } });
  wire(slotEl.wood, { what: 'wood', icon: 'wood', tap: () => cfMove('wood', 'slot', 1), drop: to => { if (to === 'inv' || to === null) cfMove('wood', 'slot', 'all'); } });
  wire(slotEl.out, { what: 'out', icon: 'grilled', tap: () => cfMove('out', 'slot', 'all'), drop: to => { if (to === 'inv' || to === null) cfMove('out', 'slot', 'all'); } });
  $('bCfClose').onclick = () => { $('cfbox').style.display = 'none'; };
  const openJobs = () => { cancelPlace(); closeSheet(); $('cfbox').style.display = 'none'; $('jobbox').style.display = 'block'; lastTools = ''; jobPanel(); toolsPanel(); };
  $('bJobClose').onclick = () => { $('jobbox').style.display = 'none'; };
  c.hud = { refresh, toast, tryPlace, openJobs, openCf };
  // ---- ボタン ----
  $('fab').onclick = () => { if (c.mode.place) cancelPlace(); else if (c.ui.open) closeSheet(); else openSheet('inv'); };
  $('bClose').onclick = closeSheet; $('sheet').onclick = e => { if (e.target.id === 'sheet') closeSheet(); };
  document.querySelectorAll('.tab canvas').forEach(cv => paint(cv, cv.dataset.k));
  $('tInv').onclick = () => setTab('inv'); $('tCraft').onclick = () => setTab('craft');
  $('bPlaceEnd').onclick = cancelPlace;
  $('pull').onclick = () => { sim.recallNet(s); };
  $('bHelp').onclick = () => { $('helpbox').style.display = 'block'; };
  $('bHelpClose').onclick = () => { $('helpbox').style.display = 'none'; };
  addEventListener('keydown', e => {
    if (e.key === 'e' || e.key === 'E') { if (c.ui.open) closeSheet(); else openSheet('inv'); }
    else if (e.key === 'Escape') { cancelPlace(); closeSheet(); $('helpbox').style.display = 'none'; }
  });
  // ---- 雨 ----
  const rain = $('rain'), rg = rain.getContext('2d'); let rainA = 0;
  const drops = Array.from({ length: 160 }, () => ({ x: Math.random(), y: Math.random(), v: 0.6 + Math.random() * 0.8 }));
  const msgs = {
    caught: e => `かかった：${nameOf(e.k)}`, haul: e => `${e.n}個を持ち物に入れた`, eat: () => '食べた', drink: () => '飲んだ',
    short: () => '材料がたりない', locked: () => '作業台がいる', crafted: e => `${nameOf(e.k)}を作った（持ち物に入った）`, rodcast: () => 'ウキがしずんだら、タップ！', bite: () => 'ひいてる！ いまタップ！', bitegone: () => '逃げられた…', fished: e => (e.q === 'great' ? 'ナイス！ ' : '') + `釣れた：${nameOf(e.k)}${e.n > 1 ? ' ×' + e.n : ''}`, rodempty: () => 'つりあげた（何も釣れなかった）', placed: () => '置いた',
    miss: () => '床に落ちた！ 海へ投げよう', empty: () => '何もかからなかった',
    netlv: e => `網が Lv${e.lv} になった`, noequip: () => '右下の「持ち物」から、網か釣りざおを手に持とう',
    weather: e => `天気：${D.WEATHER[e.id].name}`, tankinfo: e => `貯水槽 ${e.w}/${e.cap}`, tankempty: () => '貯水槽が空（雨をためる／ろ過器を置く）',
    filterinfo: e => `ろ過器：あと${e.left}秒で水が1入る`, equip: e => e.id === 'rod' ? '釣りざおを持った：海をタップして糸をたらす' : e.id ? '網を持った：海を押し続けて、離すと投げる' : '手に何も持っていない'
  };
  let acc = 0;
  return { update(t, dt) {
    s.events.splice(0).forEach(e => {
      c.sfx && c.sfx.onEvent(e);
      if (e.e === 'bench') { openSheet('craft'); return; }
      if (e.e === 'campfire') { openCf(e.id); return; }
      const f = msgs[e.e]; if (f) { const m = f(e); if (m) toast(m); }
      if (['caught', 'fished', 'bfished', 'bhaul', 'bcrafted', 'fixed', 'tear', 'dur', 'haul', 'eat', 'drink', 'crafted', 'netlv', 'netup', 'equip', 'placed', 'filtered', 'weather'].includes(e.e)) refresh();
    });
    $('hunger').style.width = s.needs.hunger + '%'; $('thirst').style.width = s.needs.thirst + '%';
    $('hunger').classList.toggle('low', s.needs.hunger < D.NEEDS.low); $('thirst').classList.toggle('low', s.needs.thirst < D.NEEDS.low);
    $('clock').textContent = `${s.clock.day}日目 ${timeName(s.clock.t)}・${D.WEATHER[s.weather.id].name}`;
    const cs = s.net.cast, nl = D.NET_LV[s.net.lv - 1];
    $('pull').style.display = cs && !c.ui.open ? 'block' : 'none';
    if (cs) $('pull').textContent = `引き寄せる ${cs.held.length}/${nl.cap}`;
    const gv = $('gauge'); gv.style.display = c.aim.active && !cs ? 'block' : 'none';
    if (c.aim.active) { $('gaugeFill').style.width = (c.aim.power * 100) + '%'; $('gaugeTxt').textContent = `${(D.NET_MIN + (nl.range - D.NET_MIN) * c.aim.power).toFixed(1)}マス先`; }
    // 雨と目のかすみ
    const storm = s.weather.id === 'storm'; rainA += ((storm ? 1 : 0) - rainA) * (1 - Math.exp(-dt * 1.5));
    if (rain.width !== innerWidth) { rain.width = innerWidth; rain.height = innerHeight; }
    rg.clearRect(0, 0, rain.width, rain.height);
    if (rainA > 0.02) { rg.strokeStyle = `rgba(200,220,255,${0.35 * rainA})`; rg.lineWidth = 1.5; rg.beginPath();
      drops.forEach(d => { d.y += dt * d.v * 1.6; d.x -= dt * 0.25; if (d.y > 1) { d.y = -0.05; d.x = Math.random() * 1.3; } const x = d.x * rain.width, y = d.y * rain.height; rg.moveTo(x, y); rg.lineTo(x - 5, y + 16); }); rg.stroke(); }
    if ($('cfbox').style.display === 'block') cfPanel();
    if ($('jobbox').style.display === 'block') { toolsPanel(); $('mood').style.width = s.buddy.mood + '%'; $('jobNow').textContent = 'いまの仕事：' + (s.buddy.job ? D.BUDDY.JOBS[s.buddy.job].name : 'おまかせ（自由に歩く）'); }
    acc += dt; if (acc > 10) { acc = 0; sim.save(s); }
    if (!update.first) { update.first = true; toast('右下の「持ち物」から、網を持って、海を押してみよう', 4000); }
  }, init: refresh };
  function update() {}
};
