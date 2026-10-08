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

  // ---- 持ち物の一覧 ----
  function slots() {
    const a = [];
    s.tools.forEach(k => a.push({ t: 'tool', k, name: D.TOOLS[k].name, n: 'Lv' + s.net.lv, tip: D.TOOLS[k].tip, hand: s.hand === k }));
    Object.keys(D.ITEMS).forEach(k => {
      if ((s.inv[k] || 0) <= 0) return; const it = D.ITEMS[k];
      a.push({ t: it.place ? 'place' : (it.food || it.drink) ? 'food' : 'mat', k, name: it.name, n: s.inv[k], tip: it.tip });
    });
    return a;
  }
  function renderInv() {
    const list = slots(); if (!list.some(o => o.k === sel)) sel = null;
    $('grid').innerHTML = list.map(o => `<button class="slot${o.k === sel ? ' sel' : ''}${o.hand ? ' hand' : ''}" data-k="${o.k}"><canvas width="12" height="12" data-k="${o.k}"></canvas><span>${o.name}</span><span class="n">${o.n}</span></button>`).join('') || '<span style="opacity:.6">持ち物なし</span>';
    $('grid').querySelectorAll('canvas').forEach(cv => paint(cv, cv.dataset.k));
    $('grid').querySelectorAll('.slot').forEach(b => b.onclick = () => { sel = b.dataset.k; renderInv(); });
    const o = list.find(x => x.k === sel), d = $('detail');
    if (!o) { d.innerHTML = '<span style="opacity:.65">枠をタップすると、くわしい説明と使うボタンが出ます</span>'; return; }
    const label = o.t === 'tool' ? (o.hand ? 'しまう' : '手に持つ') : o.t === 'food' ? (D.ITEMS[o.k].drink ? '飲む' : '食べる') : o.t === 'place' ? '置く' : '';
    d.innerHTML = `<div class="tx"><b>${o.name}</b>${o.t === 'tool' ? '　' + (o.hand ? '手に持っている' : '') : '　×' + o.n}<br><span style="opacity:.8">${o.tip || ''}</span></div>${label ? `<button id="act">${label}</button>` : ''}`;
    if (label) $('act').onclick = () => {
      if (o.t === 'tool') { sim.hold(s, o.k); closeSheet(); }
      else if (o.t === 'food') { sim.use(s, o.k); }
      else if (o.t === 'place') startPlace(o.k);
      refresh();
    };
  }
  // ---- 作る ----
  function renderCraft() {
    const hasBench = sim.hasBench(s);
    $('paneCraft').innerHTML = (hasBench ? '' : '<div style="font-size:12px;color:#f2c879;margin:0 0 8px">まず「作業台」を作って、置こう。作業台があると、ほかの物が作れる。</div>') + D.RECIPES.map(r => {
      const net = r.special === 'net', nx = net ? sim.nextNet(s) : null, cost = net ? (nx ? nx.cost : null) : r.cost;
      const ck = sim.canCraft(s, r), nm = net ? (nx ? `網を強くする Lv${s.net.lv}→${nx.lv}` : '網（さいだい）') : D.ITEMS[r.out].name;
      const need = cost ? Object.keys(cost).map(k => `<span class="need${(s.inv[k] || 0) >= cost[k] ? '' : ' no'}">${nameOf(k)} ${s.inv[k] || 0}/${cost[k]}</span>`).join('　') : '';
      const why = ck.why === 'locked' ? '作業台がいる' : ck.why === 'have' ? 'もうある' : ck.why === 'max' ? '' : '';
      const tip = net && nx ? `${r.tip}（とどく${nx.range}マス・${nx.cap}個）` : r.tip;
      return `<div class="rec${ck.why === 'locked' ? ' lock' : ''}"><canvas width="12" height="12" data-k="${net ? 'net' : r.out}"></canvas><div class="tx"><b>${nm}</b> <span class="why">${why}</span><br>${need}<br><span style="opacity:.7">${tip}</span></div><button data-id="${r.id}" ${ck.ok ? '' : 'disabled'}>作る</button></div>`;
    }).join('');
    $('paneCraft').querySelectorAll('canvas').forEach(cv => paint(cv, cv.dataset.k));
    $('paneCraft').querySelectorAll('button').forEach(b => b.onclick = () => { sim.craft(s, b.dataset.id); refresh(); });
  }
  function setTab(t) { tab = t; $('tInv').classList.toggle('on', t === 'inv'); $('tCraft').classList.toggle('on', t === 'craft'); $('paneInv').style.display = t === 'inv' ? '' : 'none'; $('paneCraft').style.display = t === 'craft' ? '' : 'none'; refresh(); }
  function openSheet(t) { cancelPlace(); c.ui.open = true; $('sheet').classList.add('open'); $('scrim').style.display = 'block'; setTab(t || tab); }
  function closeSheet() { c.ui.open = false; $('sheet').classList.remove('open'); $('scrim').style.display = 'none'; }
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
    if (c.ui.open) { if (tab === 'inv') renderInv(); else renderCraft(); }
  }
  c.hud = { refresh, toast, tryPlace };
  // ---- ボタン ----
  $('fab').onclick = () => { if (c.mode.place) cancelPlace(); else if (c.ui.open) closeSheet(); else openSheet('inv'); };
  $('bClose').onclick = closeSheet; $('scrim').onclick = closeSheet;
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
    if (c.ui.open && tab === 'craft') { const k = s.inv.wood + ',' + s.inv.rope + ',' + s.inv.cloth + ',' + s.net.lv; if (k !== update.k) { update.k = k; renderCraft(); } }
    acc += dt; if (acc > 10) { acc = 0; sim.save(s); }
    if (!update.first) { update.first = true; toast('右下の「持ち物」から、網を持って、海を押してみよう', 4000); }
  }, init: refresh };
  function update() {}
};
