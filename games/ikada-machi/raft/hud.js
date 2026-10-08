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
  const paint = (cv, k) => { const g = cv.getContext('2d'); g.clearRect(0, 0, 12, 12); const ic = k && iconOf(k); if (ic) g.drawImage(ic, 0, 0); };
  const nameOf = k => (D.ITEMS[k] || D.TOOLS[k] || {}).name || k;

  // ---- 本の形のメニュー：左のページ＝枠の一覧、右のページ＝くわしい説明と使うボタン ----
  function slots() {
    const a = [];
    s.tools.forEach(k => a.push({ key: k, t: 'tool', k, name: D.TOOLS[k].name, n: 'Lv' + s.net.lv, tip: D.TOOLS[k].tip, hand: s.hand === k }));
    Object.keys(D.ITEMS).forEach(k => {
      if ((s.inv[k] || 0) <= 0) return; const it = D.ITEMS[k];
      a.push({ key: k, t: it.place ? 'place' : (it.food || it.drink) ? 'food' : 'mat', k, name: it.name, n: s.inv[k], tip: it.tip });
    });
    return a;
  }
  function recipes() {
    return D.RECIPES.map(r => {
      const net = r.special === 'net', nx = net ? sim.nextNet(s) : null, ck = sim.canCraft(s, r);
      return { key: r.id, t: 'recipe', r, net, nx, ck, k: net ? 'net' : r.out, name: net ? (nx ? '網を強く' : '網（最大）') : D.ITEMS[r.out].name, n: '' };
    });
  }
  function renderBook() {
    const list = tab === 'inv' ? slots() : recipes();
    if (!list.some(o => o.key === sel)) sel = list.length ? list[0].key : null;
    const fill = Math.max(12, Math.ceil(list.length / 4) * 4) - list.length;
    $('grid').innerHTML = list.map(o => `<button class="slot${o.key === sel ? ' sel' : ''}${o.hand ? ' hand' : ''}${o.ck && o.ck.why === 'locked' ? ' lock' : ''}" data-key="${o.key}"><canvas width="12" height="12" data-k="${o.k}"></canvas><span class="nm">${o.name}</span>${o.n !== '' ? `<span class="n">${o.n}</span>` : ''}</button>`).join('') + '<div class="slot empty"></div>'.repeat(fill);
    $('grid').querySelectorAll('canvas').forEach(cv => paint(cv, cv.dataset.k));
    $('grid').querySelectorAll('button.slot').forEach(b => b.onclick = () => { sel = b.dataset.key; renderBook(); });
    const o = list.find(x => x.key === sel), d = $('detail');
    if (!o) { d.innerHTML = '<div class="hint">まだ何も持っていません。<br>網を投げて、物をあつめよう。</div>'; return; }
    let html = `<div class="big"><canvas width="12" height="12" data-k="${o.k}"></canvas><div><b>${o.name}</b>${o.t === 'tool' ? (o.hand ? '<br><span class="tag">手に持っている</span>' : '') : o.t === 'recipe' ? '' : `<br><span class="tag">×${o.n}</span>`}</div></div>`;
    let btn = '', onclick = null;
    if (o.t === 'recipe') {
      const cost = o.net ? (o.nx ? o.nx.cost : null) : o.r.cost, tip = o.net && o.nx ? `${o.r.tip}（とどく${o.nx.range}マス・${o.nx.cap}個）` : o.r.tip;
      html += `<p>${tip}</p>` + (cost ? '<ul class="cost">' + Object.keys(cost).map(k => `<li class="${(s.inv[k] || 0) >= cost[k] ? '' : 'no'}">${nameOf(k)}　${s.inv[k] || 0} / ${cost[k]}</li>`).join('') + '</ul>' : '');
      const why = { locked: '作業台を置くと作れる', have: 'もう持っている（イカダに1つ）', max: 'これ以上は強くできない', short: '材料がたりない' }[o.ck.why];
      if (why) html += `<p class="why">${why}</p>`;
      btn = '作る'; onclick = () => { sim.craft(s, o.r.id); refresh(); };
      html += `<button id="act" ${o.ck.ok ? '' : 'disabled'}>${btn}</button>`;
    } else {
      html += `<p>${o.tip || ''}</p>`;
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
    if (!cands.length) { toast('置ける場所がない'); return; }
    c.mode.place = { k }; c.setHighlight && c.setHighlight(cands); closeSheet(); placeBar();
  }
  function placeBar() {
    const p = c.mode.place; $('placebar').style.display = p ? 'flex' : 'none';
    if (p) $('placeTx').textContent = `${nameOf(p.k)}を置く：光るマスをタップ（のこり${s.inv[p.k] || 0}）`;
  }
  function cancelPlace() { if (!c.mode.place) return; c.mode.place = null; c.setHighlight && c.setHighlight(null); placeBar(); }
  function tryPlace(x, z) {
    const p = c.mode.place; if (!p) return;
    if (sim.place(s, p.k, x, z)) {
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
  c.hud = { refresh, toast, tryPlace };
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
    short: () => '材料がたりない', locked: () => '作業台がいる', crafted: e => `${nameOf(e.k)}を作った（持ち物に入った）`, placed: () => '置いた',
    miss: () => '床に落ちた！ 海へ投げよう', empty: () => '何もかからなかった', stormnet: () => '嵐の間は網が投げられない（雨水をためよう）',
    netup: () => '嵐！ 網を引き寄せた', netlv: e => `網が Lv${e.lv} になった`, noequip: () => '右下の「持ち物」から、網を手に持とう',
    weather: e => `天気：${D.WEATHER[e.id].name}`, tankinfo: e => `貯水槽 ${e.w}/${e.cap}`, tankempty: () => '貯水槽が空（雨をためる／ろ過器を置く）',
    filterinfo: e => `ろ過器：あと${e.left}秒で水が1入る`, equip: e => e.id ? '網を持った：海を押し続けて、離すと投げる' : '網をしまった'
  };
  let acc = 0;
  return { update(t, dt) {
    s.events.splice(0).forEach(e => {
      c.sfx && c.sfx.onEvent(e);
      if (e.e === 'bench') { openSheet('craft'); return; }
      const f = msgs[e.e]; if (f) toast(f(e));
      if (['caught', 'haul', 'eat', 'drink', 'crafted', 'netlv', 'netup', 'equip', 'placed', 'filtered', 'weather'].includes(e.e)) refresh();
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
    acc += dt; if (acc > 10) { acc = 0; sim.save(s); }
    if (!update.first) { update.first = true; toast('右下の「持ち物」から、網を持って、海を押してみよう', 4000); }
  }, init: refresh };
  function update() {}
};
