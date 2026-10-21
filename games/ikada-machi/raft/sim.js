// しくみ本体：THREE を使わない。state（ただのデータ）だけを書き換える。Godot へはこのファイルの考え方を移す。
(function (R) {
  const D = R.data, S = R.sim = {};
  const key = (x, z) => x + ',' + z;
  const N4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  S.rand = Math.random;
  S.KEY = 'ikada-save-v4';

  // 住人：4人ぶんの状態（trades＝取引の回数／live＝住んでいるか）。x,z,path,dir,act はキャラとして動かすため
  S.newRes = function () { const r = {}; Object.keys(D.BOAT.RES).forEach(id => { r[id] = { trades: 0, live: false, x: 3.5, z: 3.5, dir: 'down', path: [], act: null, wanderT: 3, giftDay: 0 }; }); return r; };
  S.liveRes = s => Object.keys(s.res).filter(k => s.res[k].live);
  S.hutCount = s => s.objects.filter(o => o.k === 'hut').length;
  S.hutFree = s => S.hutCount(s) - S.liveRes(s).length;
  S.freeFloor = function (s) {      // 住人を置く、空いている床
    const cells = s.raft.cells.filter(c => free(s, c[0], c[1])); if (!cells.length) return null; return cells[Math.floor(S.rand() * cells.length)];
  };
  S.placeRes = function (s, r) { const c = S.freeFloor(s); if (c) { r.x = c[0] + 0.5; r.z = c[1] + 0.5; } r.path = []; r.act = null; };
  S.newState = function () {
    return {
      v: 4, raftRev: 1, objRev: 1, uid: 1, events: [],
      raft: { cells: [[0, 0], [1, 0], [0, 1], [1, 1]] },
      objects: [],          // 置いた物：{ id, k, x, z, w（貯水槽の水）, p（ろ過器の進み・秒）}
      inv: { wood: 10, coconut: 3, fish: 1 },
      needs: { hunger: 90, thirst: 100 },
      clock: { day: 1, t: 0.16 },
      weather: { id: 'sunny', left: 80 },
      current: { ang: 0 },
      net: { lv: 1, cast: null }, tools: ['net'], hand: 'net', rod: null, dur: { net: 100, rod: 100 }, flags: {},
      // player＝ひかるが操作する男の子、buddy＝自動で動く相棒の女の子。dir は絵の向き（down 前／up 後／left／right）
      player: { x: 1.5, z: 1.5, dir: 'down', path: [], task: null, act: null },
      buddy: { x: 0.5, z: 1.5, dir: 'down', path: [], task: null, act: null, eatT: 4, wanderT: 3, job: null, mood: 80, jobT: 0, spot: null, line: null, fx: null, viewT: 0, net: { lv: 1, cast: null }, dur: { net: 100, rod: 100 }, hasRod: false },
      res: S.newRes(), drift: [], spawnT: 2, rainT: 0, view: { r: 9 }, boat: null, boatDay: 0, lastRes: null, look: null, calm: 0, scenes: {}, fishdex: {}, cropdex: {}, dishdex: {}, sleepNight: -1
    };
  };
  S.has = (s, x, z) => s.raft.cells.some(c => c[0] === x && c[1] === z);
  S.bbox = s => {
    let x0 = 1e9, z0 = 1e9, x1 = -1e9, z1 = -1e9;
    s.raft.cells.forEach(([x, z]) => { x0 = Math.min(x0, x); z0 = Math.min(z0, z); x1 = Math.max(x1, x); z1 = Math.max(z1, z); });
    return { x0, z0, x1, z1, w: x1 - x0 + 1, d: z1 - z0 + 1 };
  };
  S.flow = s => { const a = Math.PI / 4 * -1 + s.current.ang; return { x: Math.cos(a), z: Math.sin(a) }; };   // 画面の左から右へ流れる向き
  S.speed = s => D.WEATHER[s.weather.id].speed;

  // 置き物の大きさ（マス）：data.js の ITEMS[k].size＝[横x, 縦z]。置いた位置(x,z)は、左上（x・zが小さいほう）の角
  // 小屋の見た目：まだ置いていない見た目から、ランダムに選ぶ（全部出たら、全体からランダム）
  S.pickHutLook = function (s) { const used = new Set(s.objects.filter(o => o.k === 'hut').map(o => o.hv || 0)), all = []; for (let i = 0; i < D.HUT_N; i++) all.push(i); const pool = all.filter(i => !used.has(i)); const a = pool.length ? pool : all; return a[Math.floor(S.rand() * a.length)]; };
  S.sizeOf = o => (D.ITEMS[o.k] && D.ITEMS[o.k].size) || [1, 1];      // 小屋の見た目ちがい（hutw・huts）は、置くとき k='hut'、hv=見た目の番号になる
  S.footprint = o => { const [fw, fd] = S.sizeOf(o), out = []; for (let i = 0; i < fw; i++) for (let j = 0; j < fd; j++) out.push([o.x + i, o.z + j]); return out; };
  S.objAt = (s, x, z) => s.objects.find(o => { const [fw, fd] = S.sizeOf(o); return x >= o.x && x < o.x + fw && z >= o.z && z < o.z + fd; }) || null;
  S.hasBench = s => s.objects.some(o => o.k === 'bench');
  const free = (s, x, z) => S.has(s, x, z) && !S.objAt(s, x, z);
  S.bfs = function (s, from, to) {
    const k0 = key(from[0], from[1]), k1 = key(to[0], to[1]);
    if (!free(s, to[0], to[1])) return null;
    if (k0 === k1) return [];
    const prev = { [k0]: null }, q = [from];
    while (q.length) {
      const c = q.shift();
      for (const [dx, dz] of N4) {
        const x = c[0] + dx, z = c[1] + dz, k = key(x, z);
        if (k in prev || !free(s, x, z)) continue;
        prev[k] = c; if (k === k1) { const out = []; let p = [x, z]; while (p && key(p[0], p[1]) !== k0) { out.push(p); p = prev[key(p[0], p[1])]; } return out.reverse(); }
        q.push([x, z]);
      }
    }
    return null;
  };
  const cellOf = a => [Math.floor(a.x), Math.floor(a.z)];
  const bcell = s => cellOf(s.player);
  S.walkTo = function (s, x, z, a) {
    a = a || s.player; const p = S.bfs(s, cellOf(a), [x, z]); if (!p) return false;
    a.path = p; a.task = null; a.act = null; return true;
  };
  // 物のそばまで歩いて、着いたら task を実行する
  S.walkNear = function (s, x, z, task, a) {
    a = a || s.player; let best = null;
    const ob = task && task.id != null ? s.objects.find(q => q.id === task.id) : null, cells = ob ? S.footprint(ob) : [[x, z]];
    for (const [cx, cz] of cells) for (const [dx, dz] of N4) {
      const X = cx + dx, Z = cz + dz; if (!free(s, X, Z)) continue;
      const p = S.bfs(s, cellOf(a), [X, Z]); if (p && (!best || p.length < best.length)) best = p;
    }
    if (!best) return false;
    a.path = best; a.act = null; a.task = task; return true;
  };
  // 動いた向き → 絵の向き（画面で、+z＝手前（前）、-z＝奥（後ろ）、+x＝右、-x＝左）
  const dirOf = (dx, dz) => Math.abs(dz) > Math.abs(dx) ? (dz > 0 ? 'down' : 'up') : (dx > 0 ? 'right' : 'left');
  // ひかるの道具と、相棒の道具は、別々（網のレベル・いたみ・ざお）
  const kit = (s, w) => w === 'buddy' ? { net: s.buddy.net, dur: s.buddy.dur, actor: s.buddy } : { net: s.net, dur: s.dur, actor: s.player };
  const netNow = (s, w) => D.NET_LV[kit(s, w).net.lv - 1];
  S.worn = (s, k, w) => kit(s, w).dur[k] <= 0;
  const netRange = (s, w) => netNow(s, w).range * (S.weak(s) ? D.DIFF.weak : 1) * (S.worn(s, 'net', w) ? D.DUR.worn.range : 1);
  const netCap = (s, w) => S.worn(s, 'net', w) ? D.DUR.worn.cap : netNow(s, w).cap;
  S.weak = s => s.needs.hunger <= 0 || s.needs.thirst <= 0;
  const diffNeed = s => 1 + Math.min(D.DIFF.needMax, (s.clock.day - 1) * D.DIFF.needPerDay);
  // 網を投げる：(tx,tz) の向きへ、ゲージ power(0〜1) の強さで飛ばす。海に落ちたら、とる時間のあいだ水の上にただよう
  S.throwTarget = function (s, tx, tz, power) {
    const b = s.player, dx = tx - b.x, dz = tz - b.z, d = Math.hypot(dx, dz) || 1, nl = netNow(s);
    const dist = D.NET_MIN + (netRange(s) - D.NET_MIN) * clamp(power, 0, 1);
    return { x: b.x + dx / d * dist, z: b.z + dz / d * dist, dist };
  };
  S.throwNet = function (s, tx, tz, power) {
    if (s.net.cast) return false;
    if (s.hand !== 'net') { s.events.push({ e: 'noequip' }); return false; }
    s.dur.net = Math.max(0, s.dur.net - D.DUR.net.use); s.events.push({ e: 'dur', k: 'net' });
    const b = s.player, t = S.throwTarget(s, tx, tz, power);
    b.path = []; b.task = null; b.act = { type: 'throw', t: 0.5 }; b.dir = dirOf(t.x - b.x, t.z - b.z);
    s.net.cast = { phase: 'fly', sx: b.x, sz: b.z, tx: t.x, tz: t.z, x: b.x, z: b.z, t: 0, held: [] };
    s.events.push({ e: 'throw' }); return true;
  };
  S.recallNet = function (s) { const c = s.net.cast; if (!c) return false; if (c.phase !== 'back') c.phase = 'back'; return true; };
  // 魚の図鑑：どの魚か決める（how＝'rod'か'net'、great＝釣りざおのぴったり）。出やすさは、時間と天気で上がる
  S.rollFish = function (s, how, great) {
    const F = D.FISH, lvl = Math.max(s.net.lv, s.buddy.net.lv), tk = S.sceneKey(s).split('_'), list = [];
    Object.keys(F).forEach(id => { const f = F[id]; if (f.lv > lvl || (f.by && f.by !== how) || (f.great && !great)) return;
      list.push([id, f.w * (f.time === tk[0] ? 2.5 : 1) * (f.wx === tk[1] ? 2.5 : 1)]); });
    let tot = 0; list.forEach(x => tot += x[1]); let r = S.rand() * tot;
    for (const x of list) { r -= x[1]; if (r <= 0) return x[0]; }
    return list.length ? list[0][0] : 'iwashi';
  };
  S.addDex = function (s, id) {
    S.tally(s, 'fish', id); S.note(s, 'fish'); s.fishdex = s.fishdex || {}; const first = !s.fishdex[id]; s.fishdex[id] = (s.fishdex[id] || 0) + 1;
    if (first) s.events.push({ e: 'fishnew', id });
    return D.FISH[id].star >= 3 ? 2 : 0;      // めずらしい魚は、魚が2匹おまけ（合わせて3匹）
  };
  function collect(s, w) {
    const K = kit(s, w), c = K.net.cast; if (!c) return;
    c.held.forEach(k => { s.inv[k] = (s.inv[k] || 0) + 1; if (k === 'fish') s.inv.fish += S.addDex(s, S.rollFish(s, 'net', false)); });
    if (c.by === 'buddy') { s.buddy.jobT = D.BUDDY.NET_REST; if (c.held.length) { s.events.push({ e: 'bhaul', n: c.held.length }); s.buddy.cheer = s.uid++; s.buddy.cheerKind = 'net'; } }
    else if (c.held.length) s.events.push({ e: 'haul', n: c.held.length }); else s.events.push({ e: 'empty' });
    K.net.cast = null;
  }
  // 手に持つ（道具の切りかえ）
  S.hold = function (s, id) { if (!s.tools.includes(id)) return false; s.rod = null; s.hand = s.hand === id ? null : id; s.events.push({ e: 'equip', id: s.hand }); return true; };
  // 食べ物・飲み物を使う
  S.use = function (s, k, a) {
    a = a || s.player; const it = D.ITEMS[k]; if (!it || (s.inv[k] || 0) <= 0 || (!it.food && !it.drink)) return false;
    s.inv[k]--;
    if (it.food) s.needs.hunger = clamp(s.needs.hunger + it.food, 0, 100);
    if (it.mood) { s.buddy.mood = clamp(s.buddy.mood + it.mood, 0, 100); if (a !== s.buddy) s.calm = Math.min(100, (s.calm || 0) + it.mood); }
    if (it.drink) s.needs.thirst = clamp(s.needs.thirst + it.drink, 0, 100);
    { const d = a === s.buddy ? 1.6 : 0.5; a.act = { type: 'eat', kind: it.drink ? 'drink' : 'eat', t: d, dur: d }; } s.events.push({ e: it.drink ? 'drink' : 'eat', k }); return true;
  };
  S.canPay = (s, cost) => Object.keys(cost).every(k => (s.inv[k] || 0) >= cost[k]);
  S.pay = (s, cost) => Object.keys(cost).forEach(k => s.inv[k] -= cost[k]);
  S.nextNet = s => D.NET_LV[s.net.lv];       // 次のレベル（なければ undefined）
  // ミナが住んでいれば、鉄・石を使う物は、その材料が1つ少なくて済む
  S.discount = function (s, cost) { if (!cost || !s.res.mina.live) return cost; const o = {}; Object.keys(cost).forEach(k => { const n = D.RESIDENT.perk.mina.off.includes(k) ? Math.max(0, cost[k] - 1) : cost[k]; if (n > 0) o[k] = n; }); return o; };
  const costOf = (s, r) => S.discount(s, r.special === 'net' ? (S.nextNet(s) ? S.nextNet(s).cost : null) : r.cost);
  S.costOf = costOf;
  // その日にあったこと（住人の会話に使う）。日がかわると、昨日ぶんが prev に残る
  S.note = function (s, k) { const d = s.clock.day; let h = s.hist; if (!h || h.day !== d) { h = s.hist = { day: d, prev: h && h.day === d - 1 ? { storm: h.storm || 0 } : {} }; } h[k] = (h[k] || 0) + 1; };
  S.hist = function (s) { const h = s.hist; return h && h.day === s.clock.day ? h : { day: s.clock.day, prev: h && h.day === s.clock.day - 1 ? { storm: h.storm || 0 } : {} }; };
  // トト：1日に1回ずつ、安く交換してくれる
  S.resDeal = function (s, i) {
    const r = s.res.toto; if (!r.live) return false; const dl = D.RESIDENT.perk.toto.deals[i]; r.dealDay = r.dealDay || {};
    if (r.dealDay[i] === s.clock.day) { s.events.push({ e: 'dealdone' }); return false; }
    if (!S.canPay(s, dl.want)) { s.events.push({ e: 'short' }); return false; }
    S.pay(s, dl.want); Object.keys(dl.give).forEach(k => { s.inv[k] = (s.inv[k] || 0) + dl.give[k]; }); r.dealDay[i] = s.clock.day; s.events.push({ e: 'traded' }); return true;
  };
  // 作れるか：{ ok, why }  why = 'locked'（作業台がいる）／'short'（材料がたりない）／'max'／'have'（もうある）
  S.canCraft = function (s, r, hv) {
    const cost = r.special === 'hut' ? S.discount(s, D.HUT_LOOKS[hv == null ? 0 : hv].c) : costOf(s, r);
    if (r.special === 'net' && !cost) return { ok: false, why: 'max' };
    if (r.need === 'bench' && !S.hasBench(s)) return { ok: false, why: 'locked' };
    if (r.special === 'fix' && (s.dur[r.tool] >= 95)) return { ok: false, why: 'full' };
    if (r.special === 'rod' && s.tools.includes('rod')) return { ok: false, why: 'have' };
    if (r.out === 'bench' && (S.hasBench(s) || (s.inv.bench || 0) > 0)) return { ok: false, why: 'have' };
    if (!S.canPay(s, cost)) return { ok: false, why: 'short' };
    return { ok: true };
  };
  S.craft = function (s, id, hv) {
    const r = D.RECIPES.find(x => x.id === id); if (!r) return false;
    if (r.special === 'hut') {      // 家：選んだ見た目（hv）で作る。持ち物に hut<番号> が入る
      hv = hv == null ? S.pickHutLook(s) : hv; const c = S.canCraft(s, r, hv); if (!c.ok) { s.events.push({ e: c.why === 'locked' ? 'locked' : 'short' }); return false; }
      S.pay(s, S.discount(s, D.HUT_LOOKS[hv].c)); S.tally(s, 'craft', r.id); s.inv['hut' + hv] = (s.inv['hut' + hv] || 0) + 1; s.events.push({ e: 'crafted', k: 'hut' + hv }); return true;
    }
    const c = S.canCraft(s, r); if (!c.ok) { s.events.push({ e: c.why === 'locked' ? 'locked' : 'short' }); return false; }
    S.pay(s, costOf(s, r)); S.tally(s, 'craft', r.id);
    if (r.special === 'fix') { s.dur[r.tool] = 100; s.events.push({ e: 'fixed', k: r.tool }); }
    else if (r.special === 'net') { s.net.lv = S.nextNet(s).lv; s.events.push({ e: 'netlv', lv: s.net.lv }); }
    else if (r.special === 'rod') { s.tools.push('rod'); s.events.push({ e: 'crafted', k: 'rod' }); }
    else { s.inv[r.out] = (s.inv[r.out] || 0) + 1; s.events.push({ e: 'crafted', k: r.out }); }
    return true;
  };
  // 床板：海に面した、まだ床でないマス（8×8まで）
  S.floorCandidates = function (s) {
    const bb = S.bbox(s), out = [], seen = new Set();
    s.raft.cells.forEach(([x, z]) => N4.forEach(([dx, dz]) => {
      const X = x + dx, Z = z + dz, k = key(X, Z); if (seen.has(k) || S.has(s, X, Z)) return; seen.add(k);
      if (Math.max(bb.x1, X) - Math.min(bb.x0, X) + 1 > D.MAX_SIZE || Math.max(bb.z1, Z) - Math.min(bb.z0, Z) + 1 > D.MAX_SIZE) return;
      if ([s.net.cast, s.buddy.net.cast].some(q => q && Math.floor(q.x) === X && Math.floor(q.z) === Z)) return;
      out.push([X, Z, 0.06]);
    }));
    return out;
  };
  // 置き場所：床板は海側のマス。ほかの物は、イカダの空いているマス。置いたあとも、空きマスがつながって2つ以上残ること
  S.placeCandidates = function (s, k) {
    if (k === 'floor') return S.floorCandidates(s);
    const cs = [cellOf(s.player), cellOf(s.buddy)], out = [], [fw, fd] = (D.ITEMS[k] && D.ITEMS[k].size) || [1, 1];
    const freeCells = s.raft.cells.filter(([x, z]) => !S.objAt(s, x, z)), isFree = (x, z) => freeCells.some(c => c[0] === x && c[1] === z);
    s.raft.cells.forEach(([x, z]) => {
      const fp = []; for (let i = 0; i < fw; i++) for (let j = 0; j < fd; j++) fp.push([x + i, z + j]);
      if (fp.some(([X, Z]) => !isFree(X, Z) || cs.some(q => q[0] === X && q[1] === Z))) return;
      const rest = freeCells.filter(c => !fp.some(f => f[0] === c[0] && f[1] === c[1])); if (rest.length < 2) return;
      const seen = new Set([key(rest[0][0], rest[0][1])]), q = [rest[0]];
      while (q.length) { const c = q.shift(); for (const [dx, dz] of N4) { const X = c[0] + dx, Z = c[1] + dz, kk = key(X, Z); if (!seen.has(kk) && rest.some(r => r[0] === X && r[1] === Z)) { seen.add(kk); q.push([X, Z]); } } }
      if (seen.size === rest.length) out.push([x, z, 0.215]);
    });
    return out;
  };
  S.place = function (s, k, x, z) {
    if ((s.inv[k] || 0) <= 0) return false;
    const cands = S.placeCandidates(s, k), sz = (D.ITEMS[k] && D.ITEMS[k].size) || [1, 1];
    let hit = cands.find(c => c[0] === x && c[1] === z);
    if (!hit && k !== 'floor' && (sz[0] > 1 || sz[1] > 1)) hit = cands.find(c => x >= c[0] && x < c[0] + sz[0] && z >= c[1] && z < c[1] + sz[1]);      // 大きい物は、広がるどこのマスを押してもよい
    if (!hit) return false; x = hit[0]; z = hit[1];
    s.inv[k]--;
    if (k === 'floor') { s.raft.cells.push([x, z]); s.raftRev++; }
    else { const it = D.ITEMS[k] || {}; s.objects.push({ id: s.uid++, k: it.as || k, hv: it.rnd ? S.pickHutLook(s) : (it.hv || 0), x, z, w: 0, p: 0 }); s.objRev++; [s.player, s.buddy].forEach(a => { a.path = []; a.task = null; }); S.liveRes(s).forEach(k => { s.res[k].path = []; }); }
    s.events.push({ e: 'placed', k }); return true;
  };
  // 置いた物をタップ：作業台＝作るを開く／貯水槽＝飲む／ろ過器＝進みを見る
  S.useObj = function (s, id, a) {
    const o = s.objects.find(x => x.id === id); if (!o) return false;
    if (a) return S.walkNear(s, o.x, o.z, { type: o.k, id }, a);
    if (o.k === 'tank') s.events.push({ e: 'tankinfo', w: o.w, cap: D.ITEMS.tank.cap });
    if (o.k === 'filter') s.events.push({ e: 'filterinfo', left: Math.max(0, Math.ceil(D.ITEMS.filter.sec - o.p)) });
    return S.walkNear(s, o.x, o.z, { type: o.k, id });
  };
  // 釣り：海をタップすると糸をたらす（手前のマスから ROD.range まで）。ウキがしずんだ間にタップすると釣れる
  S.castRod = function (s, tx, tz) {
    if (s.hand !== 'rod' || s.rod) return false;
    s.dur.rod = Math.max(0, s.dur.rod - D.DUR.rod.use); s.events.push({ e: 'dur', k: 'rod' });
    const b = s.player, dx = tx - b.x, dz = tz - b.z, d = Math.hypot(dx, dz) || 1, dist = clamp(d, D.ROD.min, D.ROD.range);
    const x = b.x + dx / d * dist, z = b.z + dz / d * dist;
    if (S.has(s, Math.floor(x), Math.floor(z))) return false;
    b.path = []; b.task = null; b.act = { type: 'throw', t: 0.5 }; b.dir = dirOf(dx, dz);
    const w = D.ROD.wait; s.rod = { x, z, phase: 'wait', t: 0, wait: w[0] + S.rand() * (w[1] - w[0]) };
    s.events.push({ e: 'rodcast' }); return true;
  };
  S.reelRod = function (s) {
    const r = s.rod; if (!r) return false;
    s.rod = null; s.player.act = { type: 'throw', t: 0.4 };
    if (r.phase !== 'bite') { s.events.push({ e: 'rodempty' }); s.reelFx = { id: s.uid++, k: null, x: r.x, z: r.z }; return true; }
    const g = D.ROD.great, q = Math.abs(r.t / D.ROD.bite - g[0]) <= g[1] ? 'great' : 'good';   // リズム：輪が重なる頃にタップ
    let k = 'fish';
    if (S.rand() > D.ROD.fishP) { const o = ['wood', 'coconut', 'cloth', 'rope']; k = o[Math.floor(S.rand() * o.length)]; }
    let n = q === 'great' ? 2 : 1; let sp = null; if (k === 'fish') { sp = S.rollFish(s, 'rod', q === 'great'); n += S.addDex(s, sp); } s.inv[k] = (s.inv[k] || 0) + n; s.reelFx = { id: s.uid++, k, x: r.x, z: r.z }; s.events.push({ e: 'fished', k, n, q, sp }); return true;
  };
  // ---- 相棒の仕事 ----
  const faceOf = (s, x, z) => { const o = N4.find(([dx, dz]) => !S.has(s, x + dx, z + dz)); return o || [0, 1]; };
  S.edgeCells = s => s.raft.cells.filter(([x, z]) => !S.objAt(s, x, z) && N4.some(([dx, dz]) => !S.has(s, x + dx, z + dz)));
  S.setJob = function (s, job) {
    const bu = s.buddy; if (job && !D.BUDDY.JOBS[job]) return false;
    if (job === 'fish' && !bu.hasRod) { s.events.push({ e: 'needrod' }); return false; }
    bu.inHut = null; bu.job = job || null; bu.spot = null; bu.line = null; bu.jobT = 0; bu.working = false; bu.path = []; bu.task = null; bu.act = null;
    s.events.push({ e: 'job', job: bu.job }); return true;
  };
  function goSpot(s, bu) {      // 水ぎわのマスに立つ。着いたら true
    const me = cellOf(bu);
    if (bu.spot && !(S.has(s, bu.spot[0], bu.spot[1]) && !S.objAt(s, bu.spot[0], bu.spot[1]))) bu.spot = null;
    if (!bu.spot) {
      const es = S.edgeCells(s).filter(c => !(cellOf(s.player)[0] === c[0] && cellOf(s.player)[1] === c[1]));
      if (!es.length) return false;
      es.sort((a, b) => Math.hypot(a[0] - me[0], a[1] - me[1]) - Math.hypot(b[0] - me[0], b[1] - me[1]));
      bu.spot = es[Math.floor(S.rand() * Math.min(3, es.length))];
    }
    if (me[0] === bu.spot[0] && me[1] === bu.spot[1]) { const f = faceOf(s, me[0], me[1]); bu.face = f; bu.dir = dirOf(f[0], f[1]); return true; }
    if (!S.walkTo(s, bu.spot[0], bu.spot[1], bu)) bu.spot = null;
    return false;
  }
  function jobStep(s, dt) {
    const bu = s.buddy, B = D.BUDDY, J = bu.job, eff = 0.5 + 0.5 * bu.mood / 100;
    if (!J) { bu.mood = Math.min(100, bu.mood + B.IDLE * dt); return; }
    const isRest = J === 'rest' || J === 'sit' || J === 'sleep';
    if (isRest) bu.mood = Math.min(100, bu.mood + B.REST_RATE[J] * dt);
    else bu.mood = Math.max(0, bu.mood - B.DRAIN * dt);
    const sea = J === 'fish' || J === 'net';
    if (sea && s.weather.id === 'storm') { bu.line = null; if (!bu.stormMsg) { bu.stormMsg = true; s.events.push({ e: 'bstorm' }); } return; }
    bu.stormMsg = false;
    if (S.weak(s) && !isRest) bu.mood = Math.max(0, bu.mood - B.DRAIN * 2 * dt);       // 飢えて渇くと、疲れが速い
    if (!isRest && bu.mood < B.TIRED) { S.setJob(s, 'sleep'); s.events.push({ e: 'btired' }); return; }
    if (J === 'water') {
      const o = s.objects.find(x => x.k === 'filter') || s.objects.find(x => x.k === 'tank');
      if (!o) { S.setJob(s, null); s.events.push({ e: 'jobfail' }); return; }
      const me = cellOf(bu); bu.working = Math.abs(me[0] - o.x) + Math.abs(me[1] - o.z) === 1 && !bu.path.length;
    }
    if (bu.act || bu.task || bu.path.length) return;
    const rr = (a) => a[0] + S.rand() * (a[1] - a[0]);
    if (J === 'water') {
      const o = s.objects.find(x => x.k === 'filter') || s.objects.find(x => x.k === 'tank');
      if (!bu.working) { S.walkNear(s, o.x, o.z, { type: 'work', id: null }, bu); return; }
      bu.act = { type: 'work', t: 0.7 }; return;
    }
    if (!goSpot(s, bu)) return;
    const f = bu.face || [0, 1];
    if (isRest) { bu.viewT += dt; if (bu.viewT >= B.VIEW_SEC) { bu.viewT = 0; if (J === 'rest') s.events.push({ e: 'bview' }); } return; }
    if (J === 'fish') {
      if (!bu.line) {
        if (bu.jobT > 0) { bu.jobT -= dt * eff; return; }
        bu.dur.rod = Math.max(0, bu.dur.rod - D.DUR.rod.use); bu.line = { x: bu.x + f[0] * 2.4, z: bu.z + f[1] * 2.4, t: 0, wait: rr(B.FISH_WAIT) }; bu.act = { type: 'throw', t: 0.5 }; s.events.push({ e: 'bcast' });
      } else {
        bu.line.t += dt * eff;
        if (bu.line.t >= bu.line.wait) {
          const o = ['wood', 'coconut', 'cloth', 'rope'], k = S.rand() < D.ROD.fishP ? 'fish' : o[Math.floor(S.rand() * o.length)];
          s.inv[k] = (s.inv[k] || 0) + 1; if (k === 'fish') s.inv.fish += S.addDex(s, S.rollFish(s, 'rod', false)); bu.fx = { id: s.uid++, k, x: bu.line.x, z: bu.line.z }; s.events.push({ e: 'bfished', k }); bu.cheer = s.uid++; bu.cheerKind = 'fish';
          bu.line = null; bu.jobT = rr(B.FISH_REST); bu.act = { type: 'throw', t: 0.4 };
        }
      }
      return;
    }
    if (J === 'net') {
      if (bu.net.cast) return;
      if (bu.jobT > 0) { bu.jobT -= dt * eff; return; }
      const dist = D.NET_MIN + (netRange(s, 'buddy') - D.NET_MIN) * B.NET_POWER; bu.dur.net = Math.max(0, bu.dur.net - D.DUR.net.use);
      bu.net.cast = { phase: 'fly', sx: bu.x, sz: bu.z, tx: bu.x + f[0] * dist, tz: bu.z + f[1] * dist, x: bu.x, z: bu.z, t: 0, held: [], by: 'buddy' };
      bu.act = { type: 'throw', t: 0.5 }; s.events.push({ e: 'throw' });
    }
  }
  // 焚き火（マイクラのかまどのように）：魚の枠・燃料の枠・できた焼き魚の枠。燃料は木くず（1個で3匹ぶん）
  S.cfPut = function (s, id, what, n) {       // 持ち物 → 焚き火
    const o = s.objects.find(x => x.id === id && x.k === 'campfire'); if (!o) return false;
    const C = D.COOK, key = what === 'fish' ? 'fi' : 'fw'; o[key] = o[key] || 0;
    const k = what === 'fish' ? 'fish' : 'wood', room = (what === 'fish' ? C.maxFish : C.maxWood) - o[key], m = Math.min(n === 'all' ? 99 : n, room, s.inv[k] || 0);
    if (m <= 0) return false; o[key] += m; s.inv[k] -= m; return true;
  };
  S.cfTake = function (s, id, what, n) {          // 焚き火 → 持ち物（できた焼き魚を取る／入れた物を戻す）。n＝個数（省略で全部）
    const o = s.objects.find(x => x.id === id && x.k === 'campfire'); if (!o) return false;
    const all = n === undefined || n === 'all';
    if (what === 'out') { if (!o.go) return false; const m = all ? o.go : Math.min(n, o.go); s.inv.grilled = (s.inv.grilled || 0) + m; o.go -= m; return true; }
    const key = what === 'fish' ? 'fi' : 'fw', k = what === 'fish' ? 'fish' : 'wood'; if (!o[key]) return false;
    const m = all ? o[key] : Math.min(n, o[key]); s.inv[k] = (s.inv[k] || 0) + m; o[key] -= m; if (what === 'fish' && !o.fi) o.p = 0; return true;
  };
  S.cfBurning = o => (o.fi || 0) > 0 && ((o.fl || 0) > 0 || (o.fw || 0) > 0) && (o.go || 0) < D.COOK.maxOut;
  // かまど（焚き火のように）：野菜・魚・燃料（木くず）の枠に入れると、作れる料理のうち、いちばんごちそうなものを自動で作る。できた料理は「できた」の枠から取る
  const OV_KEY = { veg: 'iv', fish: 'ifi', wood: 'iw' };
  S.ovPut = function (s, id, what, n) {       // 持ち物 → かまど
    const o = s.objects.find(x => x.id === id && x.k === 'oven'), key = OV_KEY[what]; if (!o || !key) return false; o[key] = o[key] || 0;
    const m = Math.min(n === 'all' ? 99 : n, D.OVEN.maxIn - o[key], s.inv[what] || 0); if (m <= 0) return false; o[key] += m; s.inv[what] -= m; return true;
  };
  S.ovTake = function (s, id, what, n) {      // かまど → 持ち物（できた料理を取る／入れた物を戻す）
    const o = s.objects.find(x => x.id === id && x.k === 'oven'); if (!o) return false;
    if (what === 'out') { const out = o.out || {}; let any = false; Object.keys(out).forEach(k => { if (out[k] > 0) { s.inv[k] = (s.inv[k] || 0) + out[k]; any = true; } }); o.out = {}; if (any) s.events.push({ e: 'ovengot' }); return any; }
    const key = OV_KEY[what]; if (!key || !o[key]) return false; const m = (n === undefined || n === 'all') ? o[key] : Math.min(n, o[key]); s.inv[what] = (s.inv[what] || 0) + m; o[key] -= m; return true;
  };
  S.ovOutN = o => Object.keys(o.out || {}).reduce((a, k) => a + o.out[k], 0);
  S.ovNext = function (o) {      // 入っている材料で、いま作れるいちばんごちそうな料理
    const have = { veg: o.iv || 0, fish: o.ifi || 0, wood: o.iw || 0 };
    return D.DISHES.slice().reverse().find(d => Object.keys(d.need).every(k => have[k] >= d.need[k])) || null;
  };
  // 相棒の道具（ひかるの道具とは別）：網を強く・釣りざおを作る・直す
  S.buddyTool = function (s, act) {
    const bu = s.buddy; let cost, ok = true;
    if (!S.hasBench(s)) { s.events.push({ e: 'locked' }); return false; }
    if (act === 'netup') { const nx = D.NET_LV[bu.net.lv]; if (!nx) { s.events.push({ e: 'bmax' }); return false; } cost = nx.cost; }
    else if (act === 'rod') { if (bu.hasRod) return false; cost = D.BUDDY.ROD_COST; }
    else if (act === 'fixnet') { if (bu.dur.net >= 95) return false; cost = D.DUR.fixCost; }
    else if (act === 'fixrod') { if (!bu.hasRod || bu.dur.rod >= 95) return false; cost = D.DUR.fixCost; }
    else return false;
    if (!S.canPay(s, cost)) { s.events.push({ e: 'short' }); return false; }
    S.pay(s, cost);
    if (act === 'netup') bu.net.lv++; else if (act === 'rod') bu.hasRod = true; else if (act === 'fixnet') bu.dur.net = 100; else bu.dur.rod = 100;
    s.events.push({ e: 'bcrafted', act }); return true;
  };
  // ---- 船の住人 ----
  S.dealOk = (s, i) => { const b = s.boat; if (!b || b.phase !== 'stay' || b.done[i]) return false; return S.canPay(s, D.BOAT.RES[b.res].deals[i].want); };
  S.deal = function (s, i) {
    const b = s.boat; if (!b || b.phase !== 'stay' || b.done[i]) return false; const dl = D.BOAT.RES[b.res].deals[i];
    if (!S.canPay(s, dl.want)) { s.events.push({ e: 'short' }); return false; }
    S.pay(s, dl.want); Object.keys(dl.give).forEach(k => { s.inv[k] = (s.inv[k] || 0) + dl.give[k]; });
    b.done[i] = true; b.thanks = true; s.events.push({ e: 'traded' });
    const r = s.res[b.res]; r.trades++; if (!r.live && r.trades >= D.BOAT.RES[b.res].ask) { b.ask = true; b.left = Math.max(b.left, 40); s.events.push({ e: 'resask', id: b.res }); }
    if (b.done.every(x => x) && !b.ask) b.left = Math.min(b.left, 5); return true;
  };
  S.invite = function (s, yes) {      // 「ここに住んでいい？」への答え
    const b = s.boat; if (!b || !b.ask) return false;
    if (!yes) { b.ask = false; b.left = Math.min(b.left, 5); return true; }
    if (S.hutFree(s) <= 0) { s.events.push({ e: 'nohut' }); return false; }
    const r = s.res[b.res]; r.live = true; S.placeRes(s, r); b.ask = false; b.phase = 'leave'; s.events.push({ e: 'resjoin', id: b.res }); return true;
  };
  S.callBoat = function (s) { if (s.boat) { s.events.push({ e: 'boatalready' }); return false; } if (s.weather.id === 'storm') { s.events.push({ e: 'boatnostorm' }); return false; } s.boatForce = true; return true; };
  S.boatLeave = function (s) { const b = s.boat; if (b && b.phase !== 'leave') b.phase = 'leave'; };
  function boatStep(s, dt, f, bb) {
    const B = D.BOAT, cx = (bb.x0 + bb.x1 + 1) / 2, cz = (bb.z0 + bb.z1 + 1) / 2;
    let b = s.boat;
    if (!b && s.weather.id !== 'storm' && (s.boatForce || (s.boatDay !== s.clock.day && s.clock.t >= B.FROM && s.clock.t <= B.TO))) {
      s.boatForce = false;
      let ids = Object.keys(B.RES).filter(k => !s.res[k].live && k !== s.lastRes); if (!ids.length) ids = Object.keys(B.RES).filter(k => !s.res[k].live);
      if (!ids.length) { s.boatDay = s.clock.day; return; }
      const id = ids[Math.floor(S.rand() * ids.length)];
      const px = -f.z, pz = f.x, rad = Math.max(bb.w, bb.d) / 2 + B.OFFSET, R = 9;
      const tx = cx + px * rad, tz = cz + pz * rad;
      s.boat = b = { res: id, phase: 'come', x: tx - f.x * R, z: tz - f.z * R, tx, tz, left: B.STAY, done: B.RES[id].deals.map(() => false), thanks: false };
      s.boatDay = s.clock.day; s.lastRes = id; s.events.push({ e: 'boatcome' });
    }
    if (!b) return;
    if (s.weather.id === 'storm' && b.phase !== 'leave') { b.phase = 'leave'; s.events.push({ e: 'boatstorm' }); }
    const sp = B.SPEED * dt;
    if (b.phase === 'come') { const dx = b.tx - b.x, dz = b.tz - b.z, d = Math.hypot(dx, dz); if (d <= sp) { b.x = b.tx; b.z = b.tz; b.phase = 'stay'; s.events.push({ e: 'boatarrive', res: b.res }); } else { b.x += dx / d * sp; b.z += dz / d * sp; } }
    else if (b.phase === 'stay') { b.left -= dt; if (b.left <= 0) b.phase = 'leave'; }
    else { b.x += f.x * sp * 1.3; b.z += f.z * sp * 1.3; if ((b.x - cx) * f.x + (b.z - cz) * f.z > 14) s.boat = null; }
  }
  // ---- 景色を眺める ----
  // 干し魚だな：できた干物があれば取る→魚があれば1匹つるす→どちらもなければ、ようすを知らせる
  S.rackUse = function (s, o) {
    o.h = o.h || []; const R = D.RACK, done = o.h.filter(t => t >= R.sec).length;
    if (done) { o.h = o.h.filter(t => t < R.sec); s.inv.dried = (s.inv.dried || 0) + done; s.events.push({ e: 'rackdone', n: done }); return true; }
    if (o.h.length < R.max && (s.inv.fish || 0) > 0) { s.inv.fish--; o.h.push(0); s.events.push({ e: 'rackhang', n: o.h.length, max: R.max }); return true; }
    if (!o.h.length) s.events.push({ e: 'racknone' });
    else if (o.h.length >= R.max) s.events.push({ e: 'rackfull', left: Math.ceil(R.sec - Math.max.apply(null, o.h)) });
    else s.events.push({ e: 'rackwait', left: Math.ceil(R.sec - Math.max.apply(null, o.h)) });
    return false;
  };
  // 畑：できていれば収穫→空なら種をまく→水が切れていれば水をやる→そうでなければようすを知らせる
  S.plotUse = function (s, o) {
    const P = D.PLOT, C = D.CROPS, cr = o.c && C[o.c];
    if (cr && o.p >= cr.sec) {
      const n = cr.star === 3 ? 3 : cr.star === 2 ? 2 : 1; s.inv.veg = (s.inv.veg || 0) + n; S.tally(s, 'veg', n); S.note(s, 'farm'); const first = !(s.cropdex || (s.cropdex = {}))[o.c]; s.cropdex[o.c] = (s.cropdex[o.c] || 0) + 1;
      const back = S.rand() < P.seedBack; if (back) s.inv.seed = (s.inv.seed || 0) + 1;
      s.events.push({ e: 'plotharvest', c: o.c, n, back }); if (first) s.events.push({ e: 'cropnew', id: o.c }); o.c = null; o.p = 0; o.w = 0; return true;
    }
    if (!cr) {
      if ((s.inv.seed || 0) <= 0) { s.events.push({ e: 'plotnoseed' }); return false; }
      const ids = Object.keys(C); let tot = 0; ids.forEach(k => tot += C[k].w); let r = S.rand() * tot, pick = ids[0];
      for (const k of ids) { r -= C[k].w; if (r <= 0) { pick = k; break; } }
      s.inv.seed--; o.c = pick; o.p = 0; o.w = 0; s.events.push({ e: 'plotplant' }); return true;
    }
    if ((o.w || 0) <= 0) {
      const t = s.objects.filter(x => x.k === 'tank' && x.w > 0).sort((a, b) => b.w - a.w)[0];
      if (!t) { s.events.push({ e: 'plotnowater' }); return false; }
      t.w--; o.w = P.water; s.events.push({ e: 'plotwater' }); return true;
    }
    s.events.push({ e: 'plotgrow', left: Math.ceil((cr.sec - o.p) / (s.weather.id === 'calm' ? P.calmGrow : 1)) }); return false;
  };
  // 【テスト】広いイカダに、置き物を全部ならべる（見た目の確認用。畑は作物を1種ずつ、実のなった姿で）
  S.demoSet = function (s) {
    s.raft.cells = []; for (let x = 0; x < 7; x++) for (let z = 0; z < 5; z++) s.raft.cells.push([x, z]); s.raftRev++;
    s.objects = []; const kinds = ['bench', 'tank', 'filter', 'campfire', 'seat', 'rack', 'oven', 'crate', 'chest', 'barrel', 'bed', 'shelf', 'windmill', 'hut'];
    const crops = Object.keys(D.CROPS); let i = 0;
    const put = (k, x, z, extra) => { s.objects.push(Object.assign({ id: s.uid++, k, x, z, w: 0, p: 0 }, extra || {})); };
    crops.forEach((c, n) => put('plot', n, 0, { c, p: D.CROPS[c].sec, w: D.PLOT.water }));
    put('hut', 5, 2);
    kinds.filter(k => k !== 'hut').forEach((k, n) => { const x = n % 5, z = 1 + Math.floor(n / 5) * 2; put(k, x, z, k === 'tank' ? { w: 8 } : {}); });
    s.player.x = 3.5; s.player.z = 4.5; s.buddy.x = 4.5; s.buddy.z = 4.5; s.player.path = []; s.buddy.path = []; s.objRev++;
  };
  // 小屋＝自分と相棒の家。入ると絵が消えて、おなか・のどの減りがゆるみ、「ほっとした」が上がる。動こうとすると出る
  S.enterHut = function (s, o) {
    if (s.player.inHut) return; if (s.net.cast || s.rod) { s.events.push({ e: 'hutbusy' }); return; }
    s.player.inHut = o.id; s.events.push({ e: 'hutin' });
  };
  S.exitHut = function (s) { if (!s.player.inHut) return; s.player.inHut = null; s.events.push({ e: 'hutout' }); };
  function hutStep(s, dt) {
    const p = s.player; if (!p.inHut) return;
    if (p.path.length || p.task || s.net.cast || s.rod || !s.objects.some(o => o.id === p.inHut)) { S.exitHut(s); return; }
    s.calm = Math.min(100, (s.calm || 0) + D.HUT.calm * dt);
  }
  // 相棒の小屋：夜と嵐のとき、ひまなら（仕事なし・おなかとのどが足りている）自分から小屋に入って休む。朝・晴れたら出てくる
  function buddyHutStep(s) {
    const bu = s.buddy, hut = s.objects.find(o => o.k === 'hut');
    if (!hut) { bu.inHut = null; return; }
    const t = s.clock.t, night = t >= 0.78 || t < 0.2, storm = s.weather.id === 'storm', ok = s.needs.hunger >= D.NEEDS.low && s.needs.thirst >= D.NEEDS.low;
    const want = (night || storm) && !bu.job && ok;
    if (bu.inHut && !want) { bu.inHut = null; s.events.push({ e: 'bhutout' }); return; }
    if (want && !bu.inHut && !bu.path.length && !bu.task && !bu.act) S.walkNear(s, hut.x, hut.z, { type: 'hut', id: hut.id }, bu);
  }
  // 小屋の中でできること：「ごはん」（持ち物の食べ物を1つ）／「朝まで眠る」（夜だけ。1晩に1回。おなか・のどが20以上のとき。朝までの時間が一気にすすむ）
  S.hutEat = function (s) {
    if (!s.player.inHut) return false; const k = ['grilled', 'dried', 'yakiyasai', 'soup', 'tsukeni', 'nabe', 'veg', 'fish', 'coconut'].find(q => (s.inv[q] || 0) > 0);
    if (!k) { s.events.push({ e: 'hutnofood' }); return false; } return S.use(s, k);
  };
  // 日記：その日のできごとを数えておいて、小屋の中で「日記を書く」と1日1回、1行たまる
  S.tally = function (s, k, v) { const t = s.tally || (s.tally = { fish: {}, veg: 0, craft: [], scene: [] });
    if (k === 'fish') t.fish[v] = (t.fish[v] || 0) + 1; else if (k === 'veg') t.veg += v; else if (k === 'craft') t.craft.push(v); else if (k === 'scene') t.scene.push(v); };
  S.diaryText = function (s) {
    const t = s.tally || { fish: {}, veg: 0, craft: [], scene: [] }, wx = D.WEATHER[s.weather.id].name, bits = [], ids = Object.keys(t.fish), n = ids.reduce((a, i) => a + t.fish[i], 0);
    if (n) { const top = ids.sort((a, b) => t.fish[b] - t.fish[a])[0]; bits.push(n === 1 ? `${D.FISH[top].name}が1匹つれた。` : `魚が${n}匹とれた。いちばん多いのは${D.FISH[top].name}。`); }
    if (t.veg) bits.push(`畑から野菜を${t.veg}つとった。`);
    if (t.craft.length) { const r = D.RECIPES.find(x => x.id === t.craft[t.craft.length - 1]); bits.push(`${r && r.name ? r.name : 'あたらしいもの'}を作った。`); }
    if (t.scene.length) bits.push('はじめて見る景色があった。');
    if (!bits.length) bits.push(['なにもしない日。それも、わるくない。', 'のんびり波を見ていた。', '相棒と、ぼーっとして過ごした。'][s.clock.day % 3]);
    if (s.buddy.mood >= 70) bits.push('相棒は楽しそうだった。'); else if (s.buddy.mood < 30) bits.push('相棒は、すこし元気がなかった。');
    return `${wx}。` + bits.join('');
  };
  S.writeDiary = function (s) {
    if (!s.player.inHut) return false; if (s.diaryDay === s.clock.day) { s.events.push({ e: 'diarydone' }); return false; }
    s.diary = s.diary || []; s.diary.push({ day: s.clock.day, text: S.diaryText(s) }); if (s.diary.length > 200) s.diary.shift();
    s.diaryDay = s.clock.day; s.tally = null; s.calm = Math.min(100, (s.calm || 0) + 10); s.buddy.mood = Math.min(100, s.buddy.mood + 5); s.events.push({ e: 'diarywrote' }); return true;
  };
  S.isNight = s => s.clock.t >= 0.78 || s.clock.t < 0.2;
  S.sleepHut = function (s) {
    if (!s.player.inHut) return false;
    if (!S.isNight(s)) { s.events.push({ e: 'hutnotnight' }); return false; }
    const nid = s.clock.t >= 0.78 ? s.clock.day : s.clock.day - 1; if (s.sleepNight === nid) { s.events.push({ e: 'hutslept2' }); return false; }
    if (s.needs.hunger < 20 || s.needs.thirst < 20) { s.events.push({ e: 'hutnosleep' }); return false; }
    s.sleepNight = nid; let guard = 0; s.hutSleeping = true;
    while (S.isNight(s) && guard++ < 700) { S.step(s, 1); s.needs.hunger = Math.max(s.needs.hunger, 3); s.needs.thirst = Math.max(s.needs.thirst, 3); }
    s.hutSleeping = false; s.calm = Math.min(100, (s.calm || 0) + 30); s.buddy.mood = Math.min(100, s.buddy.mood + 30); s.events.push({ e: 'hutwake' }); return true;
  };
  S.startLook = function (s, o) { if (s.look) return; s.look = { id: o.id, t: 0, gift: D.LOOK.giftSec * 0.6, setBuddy: false }; const bu = s.buddy; if (!bu.job) { S.setJob(s, 'rest'); s.look.setBuddy = true; } s.events.push({ e: 'lookstart' }); };
  S.stopLook = function (s) { const L = s.look; if (!L) return; if (L.setBuddy && s.buddy.job === 'rest') S.setJob(s, null); s.look = null; s.events.push({ e: 'lookstop' }); };
  S.sceneKey = s => { const h = s.clock.t, w = s.weather.id; return (h < 0.2 ? 'dawn' : h < 0.62 ? 'day' : h < 0.78 ? 'dusk' : 'night') + '_' + w; };
  function lookStep(s, dt) {
    const L = s.look, K = D.LOOK;
    if (!L) { s.calm = Math.max(0, (s.calm || 0) - K.decay * dt); return; }
    if (s.player.path.length || s.player.task || !s.objects.some(o => o.id === L.id)) { S.stopLook(s); return; }
    const sk = S.sceneKey(s); if (!s.scenes[sk]) { S.tally(s, 'scene', sk); s.scenes[sk] = 1; s.events.push({ e: 'scenenew', k: sk }); }
    L.t += dt; s.calm = Math.min(100, (s.calm || 0) + K.gain * dt); s.buddy.mood = Math.min(100, s.buddy.mood + K.buddyBonus * dt);
    L.gift -= dt; if (L.gift <= 0) { L.gift = K.giftSec * (0.8 + S.rand() * 0.5); const k = K.gifts[Math.floor(S.rand() * K.gifts.length)]; s.inv[k] = (s.inv[k] || 0) + 1; s.events.push({ e: 'lookgift', k }); }
  }
  S.upgradeNet = function (s) { return S.craft(s, 'net'); };

  function pickItem(s) {
    const list = Object.keys(D.ITEMS).filter(k => D.ITEMS[k].w > 0 && D.ITEMS[k].lv <= Math.max(s.net.lv, s.buddy.net.lv));
    const wt = k => D.ITEMS[k].w * (k === 'wood' && (s.inv.wood || 0) < 3 ? 4 : 1);
    let tot = 0; list.forEach(k => tot += wt(k)); let r = S.rand() * tot;
    for (const k of list) { r -= wt(k); if (r <= 0) return k; }
    return list[0];
  }
  function rollWeather(s) {
    const ids = Object.keys(D.WEATHER).filter(k => k !== s.weather.id), df = D.DIFF, d = s.clock.day - 1;
    const wt = k => k === 'storm' ? Math.min(df.stormMax, df.stormBase + d * df.stormPerDay) : k === 'sunny' ? Math.max(df.sunnyMin, df.sunnyBase - d * 0.4) : D.WEATHER[k].w;
    let tot = 0; ids.forEach(k => tot += wt(k));
    let r = S.rand() * tot, id = ids[0]; for (const k of ids) { r -= wt(k); if (r <= 0) { id = k; break; } }
    return id;
  }
  // 住人：うろうろ歩く／座る。クロは毎朝、粘土かガラスをくれる
  function resStep(s, dt) {
    const P = D.RESIDENT.perk;
    Object.keys(s.res).forEach(id => {
      const r = s.res[id]; if (!r.live) return;
      if (!free(s, Math.floor(r.x), Math.floor(r.z)) && !r.path.length) S.placeRes(s, r);
      if (r.act) { r.act.t -= dt; if (r.act.t <= 0) r.act = null; }
      else if (r.path.length) {
        const tgt = r.path[0], tx = tgt[0] + 0.5, tz = tgt[1] + 0.5, dx = tx - r.x, dz = tz - r.z, d = Math.hypot(dx, dz), step = 1.4 * dt;
        if (d > 0.01) r.dir = dirOf(dx, dz); if (d <= step) { r.x = tx; r.z = tz; r.path.shift(); if (!r.path.length && S.rand() < 0.45) r.act = { type: 'sit', t: 6 + S.rand() * 10 }; } else { r.x += dx / d * step; r.z += dz / d * step; }
      } else { r.wanderT -= dt; if (r.wanderT <= 0) { r.wanderT = 4 + S.rand() * 8; const c = S.freeFloor(s); if (c) S.walkTo(s, c[0], c[1], r); } }
      if (id === 'kuro' && r.giftDay !== s.clock.day && s.clock.t > 0.06) { r.giftDay = s.clock.day; const k = P.kuro.gift[(s.clock.day) % P.kuro.gift.length]; s.inv[k] = (s.inv[k] || 0) + 1; s.events.push({ e: 'resgift', id, k }); }
    });
  }
  function nextWeather(s) {
    const id = s.weather.nx || rollWeather(s);
    s.weather = { id, left: 60 + S.rand() * 60 }; if (id === 'storm') S.note(s, 'storm');
    s.events.push({ e: 'weather', id });
  }

  S.step = function (s, dt) {
    // 時計・天気
    s.clock.t += dt / D.DAY_SEC; if (s.clock.t >= 1) { s.clock.t -= 1; s.clock.day++; }
    s.weather.left -= dt; if (s.weather.left <= 0) nextWeather(s);
    if (s.res.pipi.live && !s.weather.nx && s.weather.left < D.RESIDENT.perk.pipi.warn) { s.weather.nx = rollWeather(s); if (s.weather.nx === 'storm') s.events.push({ e: 'stormsoon' }); }      // ピピ：嵐の前に知らせる
    s.current.ang = Math.sin(s.clock.day * 1.7 + s.clock.t * 6.28) * 0.35;
    const W = D.WEATHER[s.weather.id];
    // おなか・のどのかわき（0で止まる。死なない）
    const dn = diffNeed(s) * (s.player.inHut ? D.HUT.needMul : 1); s.needs.hunger = Math.max(0, s.needs.hunger - D.NEEDS.hunger * dn * dt);
    s.needs.thirst = Math.max(0, s.needs.thirst - D.NEEDS.thirst * dn * W.thirst * dt);
    const wk = S.weak(s); if (wk !== !!s.flags.weak) { s.flags.weak = wk; if (wk) s.events.push({ e: 'weak' }); }
    const wm = (s.buddy.job === 'water' && s.buddy.working && !s.buddy.path.length) ? 1 + 0.5 + 0.5 * s.buddy.mood / 100 : 1;
    const tcap = D.ITEMS.tank.cap, tanks = s.objects.filter(o => o.k === 'tank');
    if (s.weather.id === 'storm') { s.rainT += dt * wm; if (s.rainT >= D.RAIN_SEC) { s.rainT = 0; tanks.forEach(t => { t.w = Math.min(tcap, t.w + 1); }); } }
    s.objects.forEach(o => { if (o.k !== 'oven') return;     // かまど：材料がそろえば、ごちそうから順に作る
      if (!o.cook && S.ovOutN(o) < D.OVEN.maxOut) { const d = S.ovNext(o); if (d) { o.iv = (o.iv || 0) - (d.need.veg || 0); o.ifi = (o.ifi || 0) - (d.need.fish || 0); o.iw = (o.iw || 0) - (d.need.wood || 0); o.cook = { d: d.id, t: 0 }; s.events.push({ e: 'cookstart', d: d.id }); } }
      if (o.cook) { o.cook.t += dt * (s.res.kuro.live ? D.RESIDENT.perk.kuro.cookMul : 1); const d = D.DISHES.find(x => x.id === o.cook.d); if (o.cook.t >= d.sec) { o.out = o.out || {}; o.out[d.id] = (o.out[d.id] || 0) + 1; S.note(s, 'cooked'); s.dishdex = s.dishdex || {}; if (!s.dishdex[d.id]) s.events.push({ e: 'dishnew', id: d.id }); s.dishdex[d.id] = (s.dishdex[d.id] || 0) + 1; o.lastOut = d.id; o.cook = null; s.events.push({ e: 'cooked', d: d.id }); } } });
    s.objects.forEach(o => {     // 焚き火：燃料があれば、魚を1匹ずつ焼く
      if (o.k !== 'campfire') return; delete o.cook;
      if (!S.cfBurning(o)) { o.burn = false; return; }
      if ((o.fl || 0) <= 0) { o.fw--; o.fl = D.COOK.perWood; }
      o.burn = true; o.p = (o.p || 0) + dt;
      if (o.p >= D.COOK.sec) { o.p = 0; o.fi--; o.fl--; o.go = (o.go || 0) + 1; s.events.push({ e: 'grilled', n: 1 }); }
    });
    s.objects.forEach(o => { if (o.k === 'plot' && o.c) {     // 畑：水があるあいだ育つ。嵐の雨は水を入れる。晴れは早く乾く、凪はよく育つ
      const P = D.PLOT, cr = D.CROPS[o.c]; if (s.weather.id === 'storm') o.w = P.water;
      if ((o.w || 0) > 0 && o.p < cr.sec) { o.p = Math.min(cr.sec, o.p + dt * (s.weather.id === 'calm' ? P.calmGrow : 1)); o.w = Math.max(0, o.w - dt * (s.weather.id === 'sunny' ? P.sunDry : 1)); }
    } });
    s.objects.forEach(o => { if (o.k === 'rack' && o.h) for (let i = 0; i < o.h.length; i++) o.h[i] = Math.min(o.h[i] + dt, D.RACK.sec); });     // 干し魚だな：つるした魚が干物になっていく
    s.objects.forEach(o => {    // ろ過器：貯水槽に空きがあれば、決まった間隔で水が1入る
      if (o.k !== 'filter') return;
      const t = tanks.filter(x => x.w < tcap).sort((a, c) => a.w - c.w)[0];
      if (!t) { o.p = Math.min(o.p, D.ITEMS.filter.sec); return; }
      o.p += dt * wm; if (o.p >= D.ITEMS.filter.sec) { o.p = 0; t.w++; s.events.push({ e: 'filtered' }); }
    });
    // 相棒（女の子）：おなか・のどが減ったら自分で食べる・飲む。ひまなときは、イカダの上を歩き回る
    const bu = s.buddy, b = s.player; bu.eatT -= dt; bu.wanderT -= dt;
    if (!bu.act && !bu.task && !bu.path.length && bu.eatT <= 0) {
      if (s.needs.hunger < D.NEEDS.low && (s.inv.grilled > 0 ? S.use(s, 'grilled', bu) : s.inv.dried > 0 ? S.use(s, 'dried', bu) : s.inv.veg > 0 ? S.use(s, 'veg', bu) : s.inv.fish > 0 ? S.use(s, 'fish', bu) : (s.inv.coconut > 0 && S.use(s, 'coconut', bu)))) bu.eatT = 3;
      else if (s.needs.thirst < D.NEEDS.low) {
        const t = tanks.find(x => x.w > 0);
        if (t) { S.useObj(s, t.id, bu); bu.eatT = 3; } else if (s.inv.coconut > 0 && S.use(s, 'coconut', bu)) bu.eatT = 3;
      } else if (bu.wanderT <= 0 && !bu.job && !bu.inHut) {
        const fc = s.raft.cells.filter(([x, z]) => !S.objAt(s, x, z)); const t = fc[Math.floor(S.rand() * fc.length)];
        if (t) S.walkTo(s, t[0], t[1], bu); bu.wanderT = 4 + S.rand() * 7;
      }
    }
    jobStep(s, dt); if (!bu.job || bu.job !== 'fish') bu.line = null;
    // 2人の動き
    const slow = (s.needs.hunger <= 0 || s.needs.thirst <= 0) ? 0.5 : 1;
    [b, bu].forEach(a => {
      if (a.act) { a.act.t -= dt; if (a.act.t <= 0) a.act = null; }
      else if (a.path.length) {
        const tgt = a.path[0], tx = tgt[0] + 0.5, tz = tgt[1] + 0.5, dx = tx - a.x, dz = tz - a.z, d = Math.hypot(dx, dz), step = 2 * slow * dt;
        if (d > 0.01) a.dir = dirOf(dx, dz);
        if (d <= step) { a.x = tx; a.z = tz; a.path.shift(); } else { a.x += dx / d * step; a.z += dz / d * step; }
      } else if (a.task) {     // 着いたら、物を使う
        const t = a.task; a.task = null; const o = s.objects.find(x => x.id === t.id);
        if (o && o.k === 'bench' && a === b) s.events.push({ e: 'bench' });
        else if (o && o.k === 'campfire' && a === b) s.events.push({ e: 'campfire', id: o.id });
        else if (o && o.k === 'oven' && a === b) s.events.push({ e: 'oven', id: o.id });
        else if (o && o.k === 'seat' && a === b) S.startLook(s, o);
        else if (o && o.k === 'rack' && a === b) S.rackUse(s, o);
        else if (o && o.k === 'plot' && a === b) S.plotUse(s, o);
        else if (o && o.k === 'hut' && a === b) S.enterHut(s, o);
        else if (o && o.k === 'hut' && a === s.buddy) { s.buddy.inHut = o.id; s.events.push({ e: 'bhutin' }); }
        else if (o && o.k === 'tank') {
          if (o.w > 0) { o.w--; s.needs.thirst = clamp(s.needs.thirst + D.TANK_SIP, 0, 100); { const d = a === s.buddy ? 1.6 : 0.7; a.act = { type: 'eat', kind: 'drink', t: d, dur: d }; } s.events.push({ e: 'drink', k: 'tank' }); }
          else s.events.push({ e: 'tankempty' });
        }
      }
    });
    // 流れてくる物
    const f = S.flow(s), bb = S.bbox(s), cx = (bb.x0 + bb.x1 + 1) / 2, cz = (bb.z0 + bb.z1 + 1) / 2, R = s.view.r;
    s.spawnT -= dt;
    if (s.spawnT <= 0) {
      s.spawnT = (3 + S.rand() * 2.5) / W.rate;
      const off = (S.rand() - 0.5) * 2 * Math.min(R * 0.7, 6);
      s.drift.push({ id: s.uid++, k: pickItem(s), x: cx - f.x * R - f.z * off, z: cz - f.z * R + f.x * off, born: 0 });
    }
    resStep(s, dt); boatStep(s, dt, f, bb); lookStep(s, dt); hutStep(s, dt); buddyHutStep(s);
    const v = W.speed, rests = [];
    ['player', 'buddy'].forEach(w => {
      const K = kit(s, w), cast = K.net.cast, nl = netNow(s, w), ow = K.actor; if (!cast) return;
      if (cast.phase === 'fly') {
        cast.t += dt / D.NET_FLY; const k = Math.min(1, cast.t);
        cast.x = cast.sx + (cast.tx - cast.sx) * k; cast.z = cast.sz + (cast.tz - cast.sz) * k;
        if (cast.t >= 1) { cast.phase = 'rest'; cast.t = 0; if (S.has(s, Math.floor(cast.x), Math.floor(cast.z))) { K.net.cast = null; if (w === 'player') s.events.push({ e: 'miss' }); else s.buddy.jobT = 2; return; } else s.events.push({ e: 'splash' }); }
      } else if (cast.phase === 'rest') {
        cast.t += dt; cast.x += f.x * v * 0.5 * dt; cast.z += f.z * v * 0.5 * dt;
        if (cast.t >= D.NET_REST || cast.held.length >= netCap(s, w)) cast.phase = 'back';
      } else {   // 引きずって引き寄せる：網が水の上を滑って、イカダの端に着いたら持ち物に入る
        const dx = ow.x - cast.x, dz = ow.z - cast.z, d = Math.hypot(dx, dz), step = D.NET_DRAG * dt;
        if (d <= step + 0.3 || S.has(s, Math.floor(cast.x), Math.floor(cast.z))) { collect(s, w); return; } else { cast.x += dx / d * step; cast.z += dz / d * step; }
      }
      if (cast.phase !== 'fly' && s.weather.id === 'storm' && !cast.torn) {      // 嵐：網が破れる
        const df = D.DIFF, p = Math.min(df.tearMax, df.tearBase + (s.clock.day - 1) * df.tearPerDay);
        if (S.rand() < p * dt) { cast.torn = true; cast.held.length = 0; cast.phase = 'back'; K.dur.net = Math.max(0, K.dur.net - df.tearDmg); s.events.push({ e: 'tear', who: w }); }
      }
      if (cast.phase === 'rest' || cast.phase === 'back') rests.push({ cast, nl, w });
    });
    const rd = s.rod;
    if (rd) { rd.t += dt; if (rd.phase === 'wait' && rd.t >= rd.wait) { rd.phase = 'bite'; rd.t = 0; s.events.push({ e: 'bite' }); } else if (rd.phase === 'bite' && rd.t >= D.ROD.bite * (S.worn(s, 'rod') ? D.DUR.worn.bite : 1)) { rd.phase = 'wait'; rd.t = 0; const w = D.ROD.wait; rd.wait = w[0] + S.rand() * (w[1] - w[0]); s.events.push({ e: 'bitegone' }); } }
    const inRaft = (x, z) => S.has(s, Math.floor(x), Math.floor(z));
    for (let i = s.drift.length - 1; i >= 0; i--) {
      const it = s.drift[i], sp = v * dt; it.born += dt;
      // 流れてきた物がイカダにぶつかったら、なくならずに、へりに沿ってすべって、また流れていく
      let nx = it.x + f.x * sp, nz = it.z + f.z * sp;
      if (inRaft(nx, nz)) {
        if (!inRaft(it.x + f.x * sp * 1.4, it.z)) { nx = it.x + f.x * sp * 1.4; nz = it.z; }
        else if (!inRaft(it.x, it.z + f.z * sp * 1.4)) { nx = it.x; nz = it.z + f.z * sp * 1.4; }
        else { const px = -f.z, pz = f.x, side = ((it.x - cx) * px + (it.z - cz) * pz) >= 0 ? 1 : -1; nx = it.x + px * side * sp * 1.5; nz = it.z + pz * side * sp * 1.5; }
      }
      it.x = nx; it.z = nz;
      if (inRaft(it.x, it.z)) {   // イカダが広がって、物の上にかぶさったとき：外へ押し出す
        const px = -f.z, pz = f.x, side = ((it.x - cx) * px + (it.z - cz) * pz) >= 0 ? 1 : -1;
        it.x += px * side * sp * 3; it.z += pz * side * sp * 3;
      }
      const hit = rests.find(q => Math.hypot(it.x - q.cast.x, it.z - q.cast.z) < q.nl.r && q.cast.held.length < netCap(s, q.w));
      if (hit) { hit.cast.held.push(it.k); s.events.push({ e: 'caught', k: it.k }); s.drift.splice(i, 1); continue; }
      if ((it.x - cx) * f.x + (it.z - cz) * f.z > R + 3) s.drift.splice(i, 1);
    }
  };

  S.save = function (s) { try { localStorage.setItem(S.KEY, JSON.stringify(s)); } catch (e) {} };
  S.load = function () { try { const j = localStorage.getItem(S.KEY); if (!j) return null; const s = JSON.parse(j); if (!(s && s.v === 4)) return null; const base = S.newState(), out = Object.assign(base, s, { events: [], view: { r: 9 } }); out.buddy = Object.assign({}, base.buddy, s.buddy || {}); out.buddy.net = Object.assign({ lv: 1 }, out.buddy.net, { cast: null }); out.buddy.dur = Object.assign({ net: 100, rod: 100 }, out.buddy.dur); out.dur = Object.assign({ net: 100, rod: 100 }, s.dur); out.flags = s.flags || {}; out.boat = s.boat || null; out.look = null; out.player.inHut = null; out.buddy.inHut = null; out.scenes = s.scenes || {}; out.fishdex = s.fishdex || {}; out.cropdex = s.cropdex || {}; out.sleepNight = s.sleepNight == null ? -1 : s.sleepNight; out.dishdex = s.dishdex || {}; out.res = S.newRes(); Object.keys(out.res).forEach(k => { if (s.res && s.res[k]) Object.assign(out.res[k], s.res[k]); out.res[k].path = []; out.res[k].act = null; }); out.diary = s.diary || []; out.diaryDay = s.diaryDay == null ? -1 : s.diaryDay; out.tally = s.tally || null; out.calm = s.calm || 0; out.boatDay = s.boatDay || 0; if (out.net.cast && out.net.cast.by === 'buddy') out.net.cast = null; return out; } catch (e) { return null; } };
})(window.RAFT);
