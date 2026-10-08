// 画面の表示：おなか・のどのかわき・時計・持ち物・ボタン・ひとこと、嵐の雨
window.RAFT.parts.hud = function (c) {
  const { state: s, R } = c, D = R.data, sim = R.sim;
  const $ = id => document.getElementById(id);
  c.mode = c.mode || { build: false };
  c.aim = c.aim || { active: false, x: 0, z: 0, power: 0 };
  const times = [[0.2, '朝'], [0.62, '昼'], [0.78, '夕'], [1.01, '夜']];
  const timeName = t => times.find(x => t < x[0])[1];
  const toast = msg => { const e = $('toast'); e.textContent = msg; e.style.opacity = 1; clearTimeout(toast.h); toast.h = setTimeout(() => e.style.opacity = 0, 2400); };
  function refresh() {
    const inv = Object.keys(s.inv).filter(k => s.inv[k] > 0).map(k => `<span class="it"><canvas width="12" height="12" data-k="${k}"></canvas>${D.ITEMS[k].name} ${s.inv[k]}</span>`).join('') || '<span class="dim">持ち物なし</span>';
    $('inv').innerHTML = inv;
    $('inv').querySelectorAll('canvas').forEach(cv => { const k = cv.dataset.k; if (c.itemIcon) cv.getContext('2d').drawImage(c.itemIcon(k === 'water' ? 'glass' : k), 0, 0); });
    const nx = sim.nextNet(s);
    $('bNet').textContent = nx ? `網を強くする Lv${s.net.lv}→${nx.lv}（とどく${nx.range}マス・${Object.keys(nx.cost).map(k => D.ITEMS[k].name + nx.cost[k]).join('・')}）` : `網 Lv${s.net.lv}（さいだい）`;
    $('bBuild').textContent = c.mode.build ? '床を足す：えらぶ' : `床を足す（${Object.keys(D.BUILD.floor).map(k => D.ITEMS[k].name + D.BUILD.floor[k]).join('・')}）`;
    $('bBuild').classList.toggle('on', c.mode.build);
  }
  c.hud = { refresh, toast };
  $('bEat').onclick = () => { if (!sim.eat(s)) toast('食べ物がない'); refresh(); };
  $('bDrink').onclick = () => { if (!sim.drink(s)) toast('飲み物がない（嵐の雨でたまる）'); refresh(); };
  $('bBuild').onclick = () => { c.mode.build = !c.mode.build; c.setHighlight && c.setHighlight(c.mode.build); refresh(); toast(c.mode.build ? '光っているマスをタップして床を足す' : ''); };
  $('bNet').onclick = () => { sim.upgradeNet(s); refresh(); };
  $('bHaul').onclick = () => { if (!sim.recallNet(s)) toast('網は出ていない（海を押して投げる）'); };
  // 雨
  const rain = $('rain'), rg = rain.getContext('2d'); let rainA = 0;
  const drops = Array.from({ length: 160 }, () => ({ x: Math.random(), y: Math.random(), v: 0.6 + Math.random() * 0.8 }));
  const msgs = { caught: e => `かかった：${D.ITEMS[e.k].name}`, haul: e => `${e.n}個を持ち物に入れた`, eat: () => '食べた', drink: () => '飲んだ', short: () => '材料がたりない', built: () => '床を足した', throw: () => '', splash: () => '', miss: () => '床に落ちた！ 海へ投げよう', empty: () => '何もかからなかった', stormnet: () => '嵐の間は網が投げられない（雨水をためよう）', netup: () => '嵐！ 網を引き寄せた', netlv: e => `網が Lv${e.lv} になった`, weather: e => `天気：${D.WEATHER[e.id].name}` };
  let acc = 0, lastKey = '';
  return { update(t, dt) {
    s.events.splice(0).forEach(e => { const f = msgs[e.e]; if (f) toast(f(e)); if (['caught', 'haul', 'eat', 'drink', 'built', 'netlv', 'netup'].includes(e.e)) refresh(); });
    $('hunger').style.width = s.needs.hunger + '%'; $('thirst').style.width = s.needs.thirst + '%';
    $('hunger').classList.toggle('low', s.needs.hunger < D.NEEDS.low); $('thirst').classList.toggle('low', s.needs.thirst < D.NEEDS.low);
    const bb = sim.bbox(s);
    $('clock').textContent = `${s.clock.day}日目 ${timeName(s.clock.t)}　${D.WEATHER[s.weather.id].name}　イカダ ${s.raft.cells.length}マス（${bb.w}×${bb.d}）`;
    const nl = D.NET_LV[s.net.lv - 1], cs = s.net.cast, nk = s.net.lv + (cs ? cs.phase + cs.held.length : '-');
    if (nk !== lastKey) { lastKey = nk; $('netinfo').textContent = `網 Lv${s.net.lv}（とどく${nl.range}マス・${nl.cap}個まで）` + (cs ? `　${{ fly: '飛んでいる', rest: 'とっている', back: 'もどってくる' }[cs.phase]} ${cs.held.length}/${nl.cap}` : ''); }
    const gv = $('gauge'); gv.style.display = c.aim.active && !cs ? 'block' : 'none';
    if (c.aim.active) { $('gaugeFill').style.width = (c.aim.power * 100) + '%'; $('gaugeTxt').textContent = `${(D.NET_MIN + (nl.range - D.NET_MIN) * c.aim.power).toFixed(1)}マス先`; }
    // 雨と目のかすみ
    const storm = s.weather.id === 'storm'; rainA += ((storm ? 1 : 0) - rainA) * (1 - Math.exp(-dt * 1.5));
    if (rain.width !== innerWidth) { rain.width = innerWidth; rain.height = innerHeight; }
    rg.clearRect(0, 0, rain.width, rain.height);
    if (rainA > 0.02) { rg.strokeStyle = `rgba(200,220,255,${0.35 * rainA})`; rg.lineWidth = 1.5; rg.beginPath();
      drops.forEach(d => { d.y += dt * d.v * 1.6; d.x -= dt * 0.25; if (d.y > 1) { d.y = -0.05; d.x = Math.random() * 1.3; } const x = d.x * rain.width, y = d.y * rain.height; rg.moveTo(x, y); rg.lineTo(x - 5, y + 16); }); rg.stroke(); }
    acc += dt; if (acc > 10) { acc = 0; sim.save(s); }
  }, init: refresh };
};
