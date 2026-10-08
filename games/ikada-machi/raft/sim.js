// しくみ本体：THREE を使わない。state（ただのデータ）だけを書き換える。Godot へはこのファイルの考え方を移す。
(function (R) {
  const D = R.data, S = R.sim = {};
  const key = (x, z) => x + ',' + z;
  const N4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  S.rand = Math.random;

  S.newState = function () {
    return {
      v: 2, raftRev: 1, uid: 1, events: [],
      raft: { cells: [[0, 0], [1, 0], [0, 1], [1, 1]] },
      inv: { wood: 8, water: 3, fish: 1 },
      needs: { hunger: 85, thirst: 85 },
      clock: { day: 1, t: 0.16 },
      weather: { id: 'sunny', left: 80 },
      current: { ang: 0 },
      net: { lv: 1, cast: null }, tools: ['net'], equip: null,
      buddy: { x: 1.5, z: 1.5, face: 1, path: [], task: null, act: null, eatT: 0 },
      drift: [], spawnT: 2, rainT: 0, view: { r: 9 }
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

  S.bfs = function (s, from, to) {
    const k0 = key(from[0], from[1]), k1 = key(to[0], to[1]);
    if (!S.has(s, to[0], to[1])) return null;
    if (k0 === k1) return [];
    const prev = { [k0]: null }, q = [from];
    while (q.length) {
      const c = q.shift();
      for (const [dx, dz] of N4) {
        const x = c[0] + dx, z = c[1] + dz, k = key(x, z);
        if (k in prev || !S.has(s, x, z)) continue;
        prev[k] = c; if (k === k1) { const out = []; let p = [x, z]; while (p && key(p[0], p[1]) !== k0) { out.push(p); p = prev[key(p[0], p[1])]; } return out.reverse(); }
        q.push([x, z]);
      }
    }
    return null;
  };
  const bcell = s => [Math.floor(s.buddy.x), Math.floor(s.buddy.z)];
  S.walkTo = function (s, x, z) {
    const p = S.bfs(s, bcell(s), [x, z]); if (!p) return false;
    s.buddy.path = p; s.buddy.task = null; s.buddy.act = null; return true;
  };
  const netNow = s => D.NET_LV[s.net.lv - 1];
  // 網を投げる：(tx,tz) の向きへ、ゲージ power(0〜1) の強さで飛ばす。海に落ちたら、とる時間のあいだ水の上にただよう
  S.throwTarget = function (s, tx, tz, power) {
    const b = s.buddy, dx = tx - b.x, dz = tz - b.z, d = Math.hypot(dx, dz) || 1, nl = netNow(s);
    const dist = D.NET_MIN + (nl.range - D.NET_MIN) * clamp(power, 0, 1);
    return { x: b.x + dx / d * dist, z: b.z + dz / d * dist, dist };
  };
  S.throwNet = function (s, tx, tz, power) {
    if (s.net.cast) return false;
    if (s.equip !== 'net') { s.events.push({ e: 'noequip' }); return false; }
    if (s.weather.id === 'storm') { s.events.push({ e: 'stormnet' }); return false; }
    const b = s.buddy, t = S.throwTarget(s, tx, tz, power);
    b.path = []; b.act = { type: 'throw', t: 0.5 };
    const sx = (t.x - b.x) * 0.7071 - (t.z - b.z) * 0.7071; if (Math.abs(sx) > 0.01) b.face = sx > 0 ? 1 : -1;
    s.net.cast = { phase: 'fly', sx: b.x, sz: b.z, tx: t.x, tz: t.z, x: b.x, z: b.z, t: 0, held: [] };
    s.events.push({ e: 'throw' }); return true;
  };
  S.recallNet = function (s) { const c = s.net.cast; if (!c) return false; if (c.phase !== 'back') c.phase = 'back'; return true; };
  function collect(s) {
    const c = s.net.cast; if (!c) return;
    c.held.forEach(k => { s.inv[k] = (s.inv[k] || 0) + 1; });
    if (c.held.length) s.events.push({ e: 'haul', n: c.held.length }); else s.events.push({ e: 'empty' });
    s.net.cast = null;
  }
  // 持ち物から使う：道具＝手に持つ／切りかえ、食べ物・飲み物＝使う
  S.equip = function (s, id) { if (!s.tools.includes(id)) return false; s.equip = s.equip === id ? null : id; s.events.push({ e: 'equip', id: s.equip }); return true; };
  S.use = function (s, k) {
    const it = D.ITEMS[k]; if (!it || (s.inv[k] || 0) <= 0) return false;
    if (!it.food && !it.drink) { s.events.push({ e: 'material', k }); return false; }
    s.inv[k]--;
    if (it.food) s.needs.hunger = clamp(s.needs.hunger + it.food, 0, 100);
    if (it.drink) s.needs.thirst = clamp(s.needs.thirst + it.drink, 0, 100);
    s.buddy.act = { type: 'eat', t: 0.5 }; s.events.push({ e: it.drink ? 'drink' : 'eat', k }); return true;
  };
  S.eat = function (s) {
    for (const k of ['fish', 'coconut']) if ((s.inv[k] || 0) > 0) {
      s.inv[k]--; s.needs.hunger = clamp(s.needs.hunger + D.ITEMS[k].food, 0, 100);
      if (D.ITEMS[k].drink) s.needs.thirst = clamp(s.needs.thirst + D.ITEMS[k].drink * 0.3, 0, 100);
      s.buddy.act = { type: 'eat', t: 0.5 }; s.events.push({ e: 'eat', k }); return true;
    }
    return false;
  };
  S.drink = function (s) {
    for (const k of ['water', 'coconut']) if ((s.inv[k] || 0) > 0) {
      s.inv[k]--; s.needs.thirst = clamp(s.needs.thirst + D.ITEMS[k].drink, 0, 100);
      if (D.ITEMS[k].food) s.needs.hunger = clamp(s.needs.hunger + D.ITEMS[k].food, 0, 100);
      s.buddy.act = { type: 'eat', t: 0.5 }; s.events.push({ e: 'drink', k }); return true;
    }
    return false;
  };
  S.canPay = (s, cost) => Object.keys(cost).every(k => (s.inv[k] || 0) >= cost[k]);
  S.pay = (s, cost) => Object.keys(cost).forEach(k => s.inv[k] -= cost[k]);
  S.buildCandidates = function (s) {
    const bb = S.bbox(s), out = [], seen = new Set();
    s.raft.cells.forEach(([x, z]) => N4.forEach(([dx, dz]) => {
      const X = x + dx, Z = z + dz, k = key(X, Z); if (seen.has(k) || S.has(s, X, Z)) return; seen.add(k);
      if (Math.max(bb.x1, X) - Math.min(bb.x0, X) + 1 > D.MAX_SIZE || Math.max(bb.z1, Z) - Math.min(bb.z0, Z) + 1 > D.MAX_SIZE) return;
      out.push([X, Z]);
    }));
    return out;
  };
  S.build = function (s, x, z) {
    if (!S.buildCandidates(s).some(c => c[0] === x && c[1] === z)) return false;
    if (!S.canPay(s, D.BUILD.floor)) { s.events.push({ e: 'short' }); return false; }
    S.pay(s, D.BUILD.floor); s.raft.cells.push([x, z]); s.raftRev++; s.events.push({ e: 'built' }); return true;
  };
  S.nextNet = s => D.NET_LV[s.net.lv];       // 次のレベル（なければ undefined）
  S.upgradeNet = function (s) {
    const n = S.nextNet(s); if (!n) return false;
    if (!S.canPay(s, n.cost)) { s.events.push({ e: 'short' }); return false; }
    S.pay(s, n.cost); s.net.lv = n.lv; s.events.push({ e: 'netlv', lv: n.lv }); return true;
  };

  function pickItem(s) {
    const list = Object.keys(D.ITEMS).filter(k => D.ITEMS[k].w > 0 && D.ITEMS[k].lv <= s.net.lv + 1);
    let tot = 0; list.forEach(k => tot += D.ITEMS[k].w); let r = S.rand() * tot;
    for (const k of list) { r -= D.ITEMS[k].w; if (r <= 0) return k; }
    return list[0];
  }
  function nextWeather(s) {
    const ids = Object.keys(D.WEATHER).filter(k => k !== s.weather.id); let tot = 0; ids.forEach(k => tot += D.WEATHER[k].w);
    let r = S.rand() * tot, id = ids[0]; for (const k of ids) { r -= D.WEATHER[k].w; if (r <= 0) { id = k; break; } }
    s.weather = { id, left: 60 + S.rand() * 60 };
    s.events.push({ e: 'weather', id });
    if (id === 'storm' && s.net.cast) { s.net.cast.phase = 'back'; s.events.push({ e: 'netup' }); }
  }

  S.step = function (s, dt) {
    // 時計・天気
    s.clock.t += dt / D.DAY_SEC; if (s.clock.t >= 1) { s.clock.t -= 1; s.clock.day++; }
    s.weather.left -= dt; if (s.weather.left <= 0) nextWeather(s);
    s.current.ang = Math.sin(s.clock.day * 1.7 + s.clock.t * 6.28) * 0.35;
    const W = D.WEATHER[s.weather.id];
    // おなか・のどのかわき（0で止まる。死なない）
    s.needs.hunger = Math.max(0, s.needs.hunger - D.NEEDS.hunger * dt);
    s.needs.thirst = Math.max(0, s.needs.thirst - D.NEEDS.thirst * W.thirst * dt);
    if (s.weather.id === 'storm') { s.rainT += dt; if (s.rainT >= 5) { s.rainT = 0; s.inv.water = Math.min(9, (s.inv.water || 0) + 1); } }
    // 相棒が心配して、自分で食べる・飲む
    const b = s.buddy; b.eatT -= dt;
    if (!b.act && b.eatT <= 0) {
      if (s.needs.hunger < D.NEEDS.low && S.eat(s)) b.eatT = 3;
      else if (s.needs.thirst < D.NEEDS.low && S.drink(s)) b.eatT = 3;
    }
    // 相棒の動き
    const slow = (s.needs.hunger <= 0 || s.needs.thirst <= 0) ? 0.5 : 1;
    if (b.act) {
      b.act.t -= dt;
      if (b.act.t <= 0) b.act = null;
    } else if (b.path.length) {
      const tgt = b.path[0], tx = tgt[0] + 0.5, tz = tgt[1] + 0.5, dx = tx - b.x, dz = tz - b.z, d = Math.hypot(dx, dz), step = 2 * slow * dt;
      if (Math.abs(dx) > 0.01) b.face = dx > 0 ? 1 : -1;
      if (d <= step) { b.x = tx; b.z = tz; b.path.shift(); } else { b.x += dx / d * step; b.z += dz / d * step; }
    }
    // 流れてくる物
    const f = S.flow(s), bb = S.bbox(s), cx = (bb.x0 + bb.x1 + 1) / 2, cz = (bb.z0 + bb.z1 + 1) / 2, R = s.view.r;
    s.spawnT -= dt;
    if (s.spawnT <= 0) {
      s.spawnT = (2.2 + S.rand() * 1.8) / W.rate;
      const off = (S.rand() - 0.5) * 2 * Math.min(R * 0.7, 6);
      s.drift.push({ id: s.uid++, k: pickItem(s), x: cx - f.x * R - f.z * off, z: cz - f.z * R + f.x * off, born: 0 });
    }
    const v = W.speed, nl = netNow(s), cast = s.net.cast;
    // 網の動き
    if (cast) {
      if (cast.phase === 'fly') {
        cast.t += dt / D.NET_FLY; const k = Math.min(1, cast.t);
        cast.x = cast.sx + (cast.tx - cast.sx) * k; cast.z = cast.sz + (cast.tz - cast.sz) * k;
        if (cast.t >= 1) { cast.phase = 'rest'; cast.t = 0; if (S.has(s, Math.floor(cast.x), Math.floor(cast.z))) { s.net.cast = null; s.events.push({ e: 'miss' }); } else s.events.push({ e: 'splash' }); }
      } else if (cast.phase === 'rest') {
        cast.t += dt; cast.x += f.x * v * 0.5 * dt; cast.z += f.z * v * 0.5 * dt;
        if (cast.t >= D.NET_REST || cast.held.length >= nl.cap) cast.phase = 'back';
      } else {   // 引きずって引き寄せる：網が水の上を滑って、イカダの端に着いたら持ち物に入る
        const dx = b.x - cast.x, dz = b.z - cast.z, d = Math.hypot(dx, dz), step = D.NET_DRAG * dt;
        if (d <= step + 0.3 || S.has(s, Math.floor(cast.x), Math.floor(cast.z))) collect(s); else { cast.x += dx / d * step; cast.z += dz / d * step; }
      }
    }
    const rest = s.net.cast && s.net.cast.phase === 'rest' ? s.net.cast : null;
    for (let i = s.drift.length - 1; i >= 0; i--) {
      const it = s.drift[i]; it.x += f.x * v * dt; it.z += f.z * v * dt; it.born += dt;
      if (S.has(s, Math.floor(it.x), Math.floor(it.z))) { s.drift.splice(i, 1); continue; }              // イカダにぶつかって沈む
      if (rest && Math.hypot(it.x - rest.x, it.z - rest.z) < nl.r && D.ITEMS[it.k].lv <= s.net.lv && rest.held.length < nl.cap) {
        rest.held.push(it.k); s.events.push({ e: 'caught', k: it.k }); s.drift.splice(i, 1); continue;
      }
      if ((it.x - cx) * f.x + (it.z - cz) * f.z > R + 3) s.drift.splice(i, 1);
    }
  };

  S.save = function (s) { try { localStorage.setItem('ikada-save-v2', JSON.stringify(s)); } catch (e) {} };
  S.load = function () { try { const j = localStorage.getItem('ikada-save-v2'); if (!j) return null; const s = JSON.parse(j); return s && s.v === 2 ? Object.assign(S.newState(), s, { events: [], view: { r: 9 } }) : null; } catch (e) { return null; } };
})(window.RAFT);
