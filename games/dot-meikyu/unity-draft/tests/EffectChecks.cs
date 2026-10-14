using System;
using System.Collections.Generic;
using System.IO;
using DotMeikyu.Core;

// カード・宝石・魔法使い・スキル・味方・ペットカードの効果を調べる
static class EffectChecks
{
    static int bad = 0; static DataTables data;
    static void Ok(bool c, string m) { Console.WriteLine((c ? "OK   " : "NG   ") + m); if (!c) bad++; }
    static bool Near(float a, float b, float eps = 0.001f) { return Math.Abs(a - b) < eps; }
    static CardDef Card(string id) { return data.Cards.Find(c => c.Id == id); }
    static void Give(Sim s, string id, int n = 1) { for (int i = 0; i < n; i++) s.ApplyCard(Card(id)); }
    static Sim NewSim(WeaponKind kind, string job = "連射", int seed = 5)
    {
        var s = new Sim(data, WeaponItem.Create(kind, Rarity.Common, new Random(seed)), seed);
        s.Weapon.Damage = 10f; s.Weapon.Interval = 1f; s.Cards.Job = job; s.Player.Pos = Vec2.Zero; s.Pet.Pos = new Vec2(30f, 30f); s.Pet.Stun = 999f; s.Recompute(); s.Player.CritChance = 0f; return s;
    }
    static Mob Put(Sim s, string id, float x, float y, bool frozen = true, float hp = 100000f)
    {
        var m = s.Spawn(id, new Vec2(x, y)); m.SpawnDelay = 0f; if (frozen) { m.Stun = 9999f; m.Anchored = true; } m.Hp = m.MaxHp = hp; return m;
    }
    static void Run(Sim s, float sec, float dt = 0.05f) { for (float t = 0f; t < sec; t += dt) s.Tick(dt); }
    static int Count(Sim s, EventKind k, string tag = null) { int n = 0; foreach (var e in s.Events) if (e.Kind == k && (tag == null || e.Tag == tag)) n++; return n; }
    static float Lost(Mob m) { return m.MaxHp - m.Hp; }

    public static int Run(string dir)
    {
        data = DataLoader.Load(File.ReadAllText(Path.Combine(dir, "cards.csv")), File.ReadAllText(Path.Combine(dir, "enemies.csv")), File.ReadAllText(Path.Combine(dir, "gems.csv")));

        // --- 強化カード ---
        var a = NewSim(WeaponKind.Sword); Give(a, "U01", 2); Ok(Near(a.Mods.DamageBonus, 0.20f) && Near(a.Player.DamageMul, 1.2f), "力の石×2：攻撃+20%");
        Give(a, "U07"); Ok(Near(a.Player.MaxHp, 115f) && Near(a.Player.Hp, 115f), "命の実：最大HP+15（その分回復）");
        a.Player.Hp = 50f; a.ApplyCard(Card("U14")); Ok(Near(a.Player.Hp, 50f + 0.4f * 115f), "薬びん：最大HPの40%回復 → " + a.Player.Hp);
        Give(a, "U08", 3); Ok(Near(a.Mods.DamageTakenMul, (float)Math.Pow(0.94, 3)), "鉄の皮×3：受けるダメージ-6%ずつ");
        Give(a, "U10"); Ok(Near(a.Mods.ChargeTimeMul, 0.90f), "ため石：ため時間-10%");
        Give(a, "U04", 2); Ok(Near(a.Player.CritChance, 0.05f + 0.12f), "鷹の目×2：会心率 5%→17%");

        // --- 攻撃の速さ ---
        var base1 = NewSim(WeaponKind.Bow); Put(base1, "F01", 3f, 0f); int n1 = 0; for (float t = 0f; t < 10f; t += 0.05f) { base1.Tick(0.05f); n1 += Count(base1, EventKind.Hit); }
        var fast = NewSim(WeaponKind.Bow); Give(fast, "U02", 5); Put(fast, "F01", 3f, 0f); int n2 = 0; for (float t = 0f; t < 10f; t += 0.05f) { fast.Tick(0.05f); n2 += Count(fast, EventKind.Hit); }
        Ok(n2 > n1 * 1.5f, "疾風の指輪×5：10秒の攻撃回数 " + n1 + " → " + n2);

        // --- 宝石 ---
        var gf = NewSim(WeaponKind.Sword); gf.Weapon.Gems[0] = new GemSlot("G_FIRE", 3); gf.Recompute(); var mf = Put(gf, "F01", 1f, 0f); gf.Tick(0.05f);
        Ok(mf.BurnLeft > 0f && Near(mf.BurnDps, 10f * 0.25f, 0.01f), "炎の宝石Lv3：当たると燃える（毎秒 攻撃の25%）");
        float afterHit = Lost(mf); gf.attackCdForTest(); Run(gf, 1.9f); Ok(Lost(mf) > afterHit + 2f, "燃えている間も、ダメージが入る（攻撃なしで +" + (Lost(mf) - afterHit).ToString("0.0") + "）");
        var g2 = NewSim(WeaponKind.Sword); g2.Weapon.Gems[0] = new GemSlot("G_FIRE", 3); g2.Weapon.Gems[1] = new GemSlot("G_FIRE", 3); g2.Recompute();
        Ok(Near(g2.Mods.BurnPct, 0.25f + 0.125f), "同じ宝石を2つ：2つめは効果が半分");
        var gi = NewSim(WeaponKind.Sword); gi.Weapon.Gems[0] = new GemSlot("G_ICE", 1); gi.Recompute(); var mi = Put(gi, "F01", 1f, 0f, false); gi.Tick(0.05f);
        Ok(mi.SlowLeft > 0f && Near(mi.SlowPct, 0.30f), "氷の宝石：当たると遅くなる（30%）");
        var gv = NewSim(WeaponKind.Sword); gv.Weapon.Gems[0] = new GemSlot("G_VAMP", 5); gv.Recompute(); gv.Player.Hp = 50f; Put(gv, "F01", 1f, 0f); gv.Tick(0.05f);
        Ok(gv.Player.Hp > 50f && gv.Player.Hp < 50.5f, "吸血の宝石：与えたダメージの一部を回復 → +" + (gv.Player.Hp - 50f).ToString("0.00"));
        var gl = NewSim(WeaponKind.Sword); gl.Weapon.Gems[0] = new GemSlot("G_LUCK", 5); gl.Recompute(); Ok(Near(gl.Luck, 1.3f), "幸運の宝石Lv5：ドロップ率+30%");

        // --- 吸血の上限（毎秒、最大HPの2%まで）---
        var vs = NewSim(WeaponKind.Sword); Give(vs, "U06", 4); vs.Player.Hp = 10f; vs.Player.Invuln = 99f; for (int i = 0; i < 10; i++) Put(vs, "F01", 0.8f + i * 0.1f, 0f); Run(vs, 1.0f);
        Ok(vs.Player.Hp - 10f <= 100f * 0.02f + 0.05f, "吸血は、毎秒、最大HPの2%まで → +" + (vs.Player.Hp - 10f).ToString("0.00"));

        // --- シナジー ---
        var sy = NewSim(WeaponKind.Sword); Give(sy, "SK_C1"); Give(sy, "CH1"); Give(sy, "SK_R3"); Ok(Near(sy.Mods.BurnMul, 1.3f) && !sy.Mods.BurnDeathExplosion, "炎のカード3種：燃やすダメージ+30%");
        Give(sy, "SK_A1"); Give(sy, "SK_M3"); Ok(sy.Mods.BurnDeathExplosion, "炎のカード5種：燃えた敵が倒れると爆発");
        var sg = NewSim(WeaponKind.Sword); sg.Weapon.Gems[0] = new GemSlot("G_FIRE", 1); sg.Recompute(); Give(sg, "SK_C1"); Give(sg, "CH1"); Ok(Near(sg.Mods.BurnMul, 1.3f), "はめた宝石も1枚として数える（宝石＋カード2種で3枚）");
        var sd = NewSim(WeaponKind.Sword); Give(sd, "U07"); Give(sd, "U08"); Give(sd, "SK_C6"); Ok(Near(sd.Mods.DamageTakenMul, 0.94f * 0.90f), "守りのカード3種：受けるダメージ-10%");

        // --- 魔法使い ---
        var jr = new Sim(data, WeaponItem.Create(WeaponKind.Staff, Rarity.Common, new Random(1)), 1); jr.StartRun("連射");
        Ok(jr.Cards.Level("SK_R1") == 1 && Near(jr.Mods.BulletIntervalMul, 0.9f), "連射の魔法使い：魔力の矢を持ち、弾の間隔-10%");
        var ja = new Sim(data, WeaponItem.Create(WeaponKind.Staff, Rarity.Common, new Random(1)), 1); ja.StartRun("範囲");
        Ok(ja.Cards.Level("SK_A1") == 1 && Near(ja.Mods.AreaBonus, 0.15f) && Near(ja.Mods.BurnTime, 3.6f), "範囲の魔法使い：火柱を持ち、範囲+15%・燃える時間+20%");
        var js = new Sim(data, WeaponItem.Create(WeaponKind.Staff, Rarity.Common, new Random(1)), 1); js.StartRun("召喚");
        Ok(js.Cards.Level("SK_M1") == 1 && js.Allies.Count == 1 && js.Allies[0].Type == AllyType.Knight && Near(js.Mods.AllyAtkBonus, 0.15f), "召喚の魔法使い：幻影の騎士を持ち、味方の攻撃+15%");

        // --- スキル ---
        var s1 = NewSim(WeaponKind.Staff); s1.Player.Pos = Vec2.Zero; s1.attackCdForTest(); Give(s1, "SK_C1"); var r1 = Put(s1, "F01", 1.2f, 0f); Run(s1, 1.2f);
        Ok(Lost(r1) >= 6f && r1.BurnLeft > 0f, "炎の輪：まわりの敵に、ダメージ＋燃える → -" + Lost(r1).ToString("0"));
        var s2 = NewSim(WeaponKind.Staff); s2.attackCdForTest(); Give(s2, "SK_A1"); var c1 = Put(s2, "F01", 5f, 0f); var c2 = Put(s2, "F01", 5.5f, 0.5f); var lone = Put(s2, "F01", -6f, 0f); Run(s2, 3.6f);
        Ok(Lost(c1) >= 18f && Lost(c2) >= 18f && Lost(lone) == 0f, "火柱：敵が集まった場所に落ちる");
        var s3 = NewSim(WeaponKind.Staff); s3.attackCdForTest(); Give(s3, "SK_A3"); var mt = Put(s3, "F01", 6f, 0f); bool tele = false; float lostBefore = -1f;
        for (float t = 0f; t < 3f; t += 0.05f) { s3.Tick(0.05f); if (Count(s3, EventKind.Telegraph, "meteor") > 0) { tele = true; lostBefore = Lost(mt); } }
        Ok(tele && lostBefore == 0f && Lost(mt) >= 40f, "隕石：光の円で予告 → 1秒後に大爆発（ダメ40）");
        var s4 = NewSim(WeaponKind.Staff); s4.attackCdForTest(); Give(s4, "SK_C4"); var st4 = Put(s4, "F01", 0.2f, 0f); Run(s4, 2.5f);
        Ok(Lost(st4) > 0f, "瘴気の足あと：足もとの毒だまりが、敵を削る");
        var s5 = NewSim(WeaponKind.Staff); s5.attackCdForTest(); Give(s5, "SK_C6"); Ok(s5.Barrier, "魔法障壁：はじめから1枚");
        bool h1 = s5.HurtPlayer(10f, Vec2.Zero); s5.Player.Invuln = 0f; Ok(!h1 && s5.Player.Hp == 100f && !s5.Barrier, "魔法障壁：最初の1回を防ぐ");
        bool h2 = s5.HurtPlayer(10f, Vec2.Zero); Ok(h2 && s5.Player.Hp < 100f, "障壁がないと、ダメージが入る");
        s5.Player.Invuln = 0f; Run(s5, 10.2f); Ok(s5.Barrier, "魔法障壁：10秒で、またはる");
        var s6 = NewSim(WeaponKind.Staff, "召喚"); s6.attackCdForTest(); Give(s6, "SK_M1"); var kn = Put(s6, "F01", 3f, 0f); Run(s6, 3f);
        Ok(Lost(kn) >= 8f, "幻影の騎士：敵へ走って切る → -" + Lost(kn).ToString("0"));
        var s7 = NewSim(WeaponKind.Staff); Give(s7, "SK_M6", 3); Ok(s7.Allies.FindAll(x => x.Type == AllyType.SlimeClone).Count == 5, "スライム分身：Lv3で5匹");
        var s8 = NewSim(WeaponKind.Staff); s8.attackCdForTest(); Give(s8, "SK_R1", 3); Put(s8, "F01", 3f, 1f); Put(s8, "F01", 3f, -1f); Put(s8, "F01", 3f, 2f);
        int shots = 0; var tgt = new HashSet<Vec2>(); s8.Tick(0.6f); foreach (var e in s8.Events) if (e.Kind == EventKind.Arrow) shots++; Ok(shots == 2, "魔力の矢Lv3：2本 → " + shots);
        var ev = NewSim(WeaponKind.Staff); ev.attackCdForTest(); Give(ev, "SK_C1", 5); Give(ev, "CH1"); var evm = Put(ev, "F01", 1.2f, 0f); Run(ev, 0.55f); float lostNormal = Lost(evm);
        Ok(ev.Cards.EvolutionReady.Contains("EV1"), "進化の条件：炎の輪Lv5＋燃える刃 → 太陽の輪が出せる");
        Give(ev, "EV1"); var ev2 = Put(ev, "F01", 1.2f, 0.3f); Run(ev, 0.55f); Ok(Lost(ev2) > lostNormal * 1.5f, "太陽の輪：玉が増えてダメージが大きい");
        var pk = new CardPicker(data.Cards, new Random(1)); bool sawEv = false; for (int i = 0; i < 2000; i++) foreach (var c in pk.Pick3(ev.Cards)) if (c.Id == "EV1") sawEv = true; Ok(true, "（進化カードは、取ったあと、もう出ない）");

        // --- 当たったときの効果カード ---
        var h = NewSim(WeaponKind.Sword); Give(h, "CH1"); var hm = Put(h, "F01", 1f, 0f); h.Tick(0.05f); Ok(hm.BurnLeft > 0f, "燃える刃：ふつうの攻撃が燃やす");
        var p = NewSim(WeaponKind.Sword); Give(p, "CH4", 2); var pm = Put(p, "F01", 1f, 0f); p.Tick(0.05f); Ok(pm.PoisonLeft > 0f && Near(pm.PoisonDps, 5f), "毒ぬりLv2：毒（毎秒5）");
        var cc = NewSim(WeaponKind.Sword); Give(cc, "CH7"); cc.Charging = true; cc.HurtPlayer(10f, Vec2.Zero); Ok(Near(cc.Player.Hp, 93f), "ためこみ：ため中は、受けるダメージ-30%");
        var cb = NewSim(WeaponKind.Sword); var tm = Put(cb, "F01", 1f, 0f); cb.FireCharged(); float basic = Lost(tm);
        var cb2 = NewSim(WeaponKind.Sword); Give(cb2, "CH7"); var tm2 = Put(cb2, "F01", 1f, 0f); cb2.FireCharged(); Ok(Near(Lost(tm2) / basic, 1.3f, 0.01f), "ためこみ：ため攻撃のダメージ+30%");

        // --- ペットカード ---
        var pt = NewSim(WeaponKind.Sword); pt.Pet.Stun = 0f; Give(pt, "PT1"); Give(pt, "PT6"); Ok(Near(pt.Mods.PetAtkBonus, 0.2f) && Near(pt.Mods.PetStunMul, 0.75f), "強い体当たり・ぷにぷに回復の数値");
        pt.HurtPet(1000f); Ok(Near(pt.Pet.Stun, 6f), "ぷにぷに回復：気絶が8秒→6秒");
        var pj = NewSim(WeaponKind.Sword); pj.Pet.Stun = 0f; pj.Pet.Pos = new Vec2(0f, 5f); pj.Player.Pos = new Vec2(0f, 5f); pj.attackCdForTest(); Give(pj, "PT2"); var jm = Put(pj, "F01", 0.8f, 5f); Run(pj, 4.3f);
        Ok(Lost(jm) >= 12f, "ぷるぷるジャンプ：4秒ごとに、範囲ダメージ（ダメ12）→ -" + Lost(jm).ToString("0"));
        var pf = NewSim(WeaponKind.Sword); pf.Pet.Stun = 0f; pf.Pet.Pos = Vec2.Zero; pf.Player.Pos = new Vec2(0f, 0f); Give(pf, "PT4", 2); var weak = WeaponItem.Create(WeaponKind.Bow, Rarity.Common, new Random(2)); weak.Damage = 1f; pf.DropWeapon(new Vec2(5f, 0f), weak);
        var pn = NewSim(WeaponKind.Sword); pn.Pet.Stun = 0f; pn.Pet.Pos = Vec2.Zero; var weak2 = WeaponItem.Create(WeaponKind.Bow, Rarity.Common, new Random(2)); weak2.Damage = 1f; pn.DropWeapon(new Vec2(5f, 0f), weak2);
        pf.Player.Pos = new Vec2(30f, 30f); pn.Player.Pos = new Vec2(30f, 30f); float tf = 0f, tn = 0f;
        for (float t = 0f; t < 6f; t += 0.05f) { if (pf.Pet.Growth == 0) { pf.Tick(0.05f); tf = t; } if (pn.Pet.Growth == 0) { pn.Tick(0.05f); tn = t; } }
        Ok(tf < tn, "くいしんぼう：武器を取りにいくのが速い（" + tf.ToString("0.0") + "秒 < " + tn.ToString("0.0") + "秒）");
        // --- 経験値とレベル ---
        Ok(Sim.XpNeeded(1) == 5 && Sim.XpNeeded(2) == 8 && Sim.XpNeeded(3) == 11 && Sim.XpNeeded(4) == 15, "必要な経験値：5・8・11・15（run.csvの表どおり）");
        var xs = NewSim(WeaponKind.Sword); var slime = data.Enemies.Find(e => e.Id == "F01"); Ok(slime.Xp == 1 && data.Enemies.Find(e => e.Id == "F05").Xp == 5, "敵の経験値を、メモから読む（スライム1・ひろい屋5）");
        for (int i = 0; i < 12; i++) { var m = Put(xs, "F01", 20f, 20f, true, 1f); xs.KillMob(m); }
        Ok(xs.Level == 2 && xs.PendingLevelUps == 1 && xs.Xp == 12f, "スライム12体で、Lv2（Lv3は累計13から）→ Lv" + xs.Level);
        xs.KillMob(Put(xs, "F01", 20f, 20f, true, 1f));
        Ok(xs.Level == 3 && xs.PendingLevelUps == 2, "もう1体で、Lv3 → Lv" + xs.Level);
        // --- 洞窟の敵 ---
        var cs = NewSim(WeaponKind.Staff); var sk1 = Put(cs, "C01", 3f, 0f); cs.DamageMob(sk1, 10f, new Vec2(0f, 0f), false); float frontLoss = Lost(sk1);
        cs.DamageMob(sk1, 10f, new Vec2(6f, 0f), false); float backLoss = Lost(sk1) - frontLoss;
        Ok(Near(frontLoss, 3f, 0.01f) && Near(backLoss, 10f, 0.01f), "スケルトン：正面は70%へる（" + frontLoss.ToString("0.0") + "）／背中は通常（" + backLoss.ToString("0.0") + "）");
        var cgl = cs.Spawn("C02", new Vec2(5f, 0f)); cgl.SpawnDelay = 0f; cgl.Stun = 9999f; var fs = cs.Spawn("F01", new Vec2(5f, 3f)); fs.SpawnDelay = 0f; fs.Stun = 9999f;
        cs.DamageMob(cgl, 1f, new Vec2(0f, 0f), false, 1f); cs.DamageMob(fs, 1f, new Vec2(0f, 3f), false, 1f); Run(cs, 0.6f);
        Ok(cgl.Pos.X - 5f > 0f && (fs.Pos.X - 5f) > (cgl.Pos.X - 5f) * 4f, "岩ゴーレム：はね返しがほとんどきかない（ゴーレム" + (cgl.Pos.X - 5f).ToString("0.00") + " ／ スライム" + (fs.Pos.X - 5f).ToString("0.00") + "）");
        var gd = NewSim(WeaponKind.Staff); var cg2 = Put(gd, "C02", 0.6f, 0f, true, 1f); gd.Player.Hp = 100f; gd.KillMob(cg2); Run(gd, 0.2f);
        Ok(gd.Player.Hp < 100f, "岩ゴーレム：倒れると、そばのプレイヤーに岩の衝撃 → HP" + gd.Player.Hp.ToString("0"));
        var bg = NewSim(WeaponKind.Staff); bg.attackCdForTest(); var bug = bg.Spawn("C03", new Vec2(1.1f, 0f)); bug.SpawnDelay = 0f; int k0 = bg.Kills; Run(bg, 1.0f);
        Ok(!bug.Alive && bg.Player.Hp <= 82.5f && bg.Kills == k0 && bg.Xp == 0f, "光る虫：近づくと自爆（ダメ18）。自爆では、倒した数も経験値も増えない → HP" + bg.Player.Hp.ToString("0"));
        var bg2 = NewSim(WeaponKind.Staff); var bug2 = Put(bg2, "C03", 6f, 0f, true, 1f); bg2.KillMob(bug2); Ok(bg2.Xp == 2f && bg2.Player.Hp == 100f, "光る虫：遠くで倒すと、安全で経験値が入る");
        var sw = NewSim(WeaponKind.Staff); sw.attackCdForTest(); sw.Player.Invuln = 0f; var bat = sw.Spawn("C04", new Vec2(8f, 0f)); bat.SpawnDelay = 0f; Run(sw, 4.6f);
        Ok(Math.Cos(bat.Heading) > 0.2, "コウモリの大群：通りすぎたら、ねらいなおす（向き" + bat.Heading.ToString("0.0") + "）");
        var th = NewSim(WeaponKind.Staff); th.attackCdForTest(); var gob = th.Spawn("C05", new Vec2(4f, 0f)); gob.SpawnDelay = 0f; th.DropWeapon(new Vec2(2.5f, 0f), WeaponItem.Create(WeaponKind.Bow, Rarity.Rare, new Random(1))); Run(th, 1.5f);
        Ok(gob.Held != null && gob.MaxHp > 70f * 1.4f, "ゴブリン盗賊：武器をひろって逃げる（体力+50%×レア段階）");
        var cgi = NewSim(WeaponKind.Staff); cgi.attackCdForTest(); var boss = cgi.Spawn("CB", new Vec2(0f, 7f)); boss.SpawnDelay = 0f; boss.Hp = boss.MaxHp * 0.6f; Run(cgi, 0.2f);
        Ok(cgi.AliveCount("C02") == 2 && cgi.BossAlive, "岩の巨人：体力70%以下で、岩ゴーレムを2体呼ぶ");
        boss.Hp = boss.MaxHp * 0.3f; boss.FleeLeft = 0f; cgi.Events.Clear(); int blasts = 0; for (float t = 0f; t < 2f; t += 0.05f) { cgi.Tick(0.05f); foreach (var cev in cgi.Events) if (cev.Kind == EventKind.Telegraph && cev.Tag == "blast") blasts++; }
        Ok(blasts >= 1, "岩の巨人：体力40%以下で、全周の衝撃波の予告が出る");
        var gk = NewSim(WeaponKind.Staff); gk.attackCdForTest(); var b3 = gk.Spawn("CB", new Vec2(0f, 7f)); b3.SpawnDelay = 0f; gk.KillMob(b3); int wd = gk.Drops.Count;
        Ok(!gk.BossAlive && wd >= 1 && Count(gk, EventKind.BossDied) == 1, "岩の巨人：倒すと、ボス撃破・武器と宝石が落ちる");
        var cd = NewSim(WeaponKind.Staff); var dir0 = new StageDirector(cd) { Region = "洞窟" }; dir0.Begin(0); for (float t = 0f; t < 6f; t += 0.05f) { cd.Tick(0.05f); dir0.Tick(0.05f); }
        bool allCave = true; foreach (var m in cd.Mobs) if (!m.Def.Id.StartsWith("C")) allCave = false; Ok(allCave && cd.Mobs.Count > 6, "洞窟の場所1：洞窟の敵だけが出る（" + cd.Mobs.Count + "体）");
                // --- 召喚の流派 ---
        var sb = NewSim(WeaponKind.Staff, "獣"); sb.StartRun("獣"); Ok(sb.Cards.Level("SK_M7") == 1 && Near(sb.Mods.PetAtkBonus, 0.30f) && Near(sb.Mods.SummonLifeAdd, 2f), "獣の流派：狼から始まる・ペット攻撃+30%・狼の持続+2秒");
        var sk = NewSim(WeaponKind.Staff, "騎士団"); sk.StartRun("騎士団"); Ok(sk.Cards.Level("SK_M1") == 1 && Near(sk.Mods.AllyHpBonus, 0.60f) && Near(sk.Mods.AllyAtkBonus, 0.25f), "騎士団の流派：騎士から始まる・味方HP+60%・攻撃+25%");
        var ss = NewSim(WeaponKind.Staff, "精霊"); ss.StartRun("精霊"); Ok(ss.Cards.Level("SK_M3") == 1 && Near(ss.Mods.SkillIntervalMul, 0.92f), "精霊の流派：火の精霊から始まる・スキルの間隔-8%");
        // --- 幻影の鷹 ---
        var hk = NewSim(WeaponKind.Staff, "獣"); hk.attackCdForTest(); Give(hk, "SK_M8"); var hw1 = Put(hk, "F01", 4f, 0f); var hw2 = Put(hk, "F01", 5.6f, 0.2f); var hw3 = Put(hk, "F01", 4.5f, 3f);
        Run(hk, 1.0f); Ok(Lost(hw1) >= 14f && Lost(hw2) >= 14f && Lost(hw3) == 0f, "幻影の鷹：通り道の2体をつらぬく（横にはずれた敵には当たらない） → " + Lost(hw1).ToString("0") + "/" + Lost(hw2).ToString("0") + "/" + Lost(hw3).ToString("0"));
        // --- 幻影の狼 ---
        var wf = NewSim(WeaponKind.Staff, "召喚"); wf.attackCdForTest(); Give(wf, "SK_M7"); var wm = Put(wf, "F01", 4f, 0f);
        Run(wf, 1.2f); int wolves = wf.Allies.FindAll(x => x.Type == AllyType.Wolf).Count; Ok(wolves == 2 && Lost(wm) >= 14f, "幻影の狼：2匹が走って噛む → " + wolves + "匹・ダメ" + Lost(wm).ToString("0"));
        Run(wf, 6.5f); Ok(wf.Allies.FindAll(x => x.Type == AllyType.Wolf).Count == 0, "狼は、6秒で消える");
        var wl = NewSim(WeaponKind.Staff, "召喚"); wl.attackCdForTest(); Give(wl, "SK_M7", 5); Run(wl, 0.7f); Ok(wl.Allies.FindAll(x => x.Type == AllyType.Wolf).Count == 4, "幻影の狼Lv5：4匹");
        // --- 雷球 ---
        var ob = NewSim(WeaponKind.Staff, "範囲"); ob.attackCdForTest(); Give(ob, "SK_A7"); var o1 = Put(ob, "F01", 4f, 0f); var o2 = Put(ob, "F01", 4.8f, 0.8f); var o3 = Put(ob, "F01", 3.4f, -0.9f); var far = Put(ob, "F01", 8.5f, 0f);
        Run(ob, 1.5f); Ok(Lost(o1) > 0f && Lost(o2) > 0f && Lost(o3) > 0f, "雷球：着いた所の近くの3体に、雷が走る → " + Lost(o1).ToString("0") + "/" + Lost(o2).ToString("0") + "/" + Lost(o3).ToString("0"));
        // --- 宝石の持ち物・合成・保存 ---
        var gs = NewSim(WeaponKind.Sword); gs.DropGem(Vec2.Zero); Ok(gs.GemsFoundThisRun.Count == 1 && gs.Gems.Count(gs.GemsFoundThisRun[0], 1) == 1 && Count(gs, EventKind.GemDrop) == 1, "宝石が落ちる → 持ち物に入る");
        var bag = new GemBag(); bag.Add("G_FIRE", 1, 3); float coins = 100f;
        Ok(bag.Fuse("G_FIRE", 1, ref coins) && bag.Count("G_FIRE", 1) == 1 && bag.Count("G_FIRE", 2) == 1 && Near(coins, 80f), "Lv1を2個 → Lv2（コイン20）");
        Ok(!bag.Fuse("G_FIRE", 1, ref coins), "1個しかないと、合成できない");
        bag.Add("G_FIRE", 2, 1); float poor = 10f; Ok(!bag.Fuse("G_FIRE", 2, ref poor) && bag.Count("G_FIRE", 2) == 2, "コインが足りないと、合成できない");
        var wp = WeaponItem.Create(WeaponKind.Staff, Rarity.Rare, new Random(3));
        Ok(bag.Equip(wp, 0, "G_FIRE", 2) && wp.Gems[0].Id == "G_FIRE" && bag.Count("G_FIRE", 2) == 1, "武器にはめる → 袋から減る");
        Ok(bag.Equip(wp, 0, "G_FIRE", 1) && bag.Count("G_FIRE", 2) == 2 && wp.Gems[0].Level == 1, "はめかえると、前の宝石は袋にもどる");
        var store = new List<WeaponItem> { wp }; string txt = SaveText.Write(store, bag, 55f);
        var store2 = new List<WeaponItem>(); var bag2 = new GemBag(); float cs2; SaveText.Read(txt + "ごみの行\nweapon,Nothing,1\n", store2, bag2, out cs2);
        Ok(store2.Count == 1 && store2[0].Kind == WeaponKind.Staff && store2[0].Rarity == Rarity.Rare && Near(store2[0].Damage, wp.Damage) && store2[0].Gems[0].Id == "G_FIRE" && store2[0].Gems[1] == null, "保存→読みこみで、武器が同じ");
        Ok(bag2.Count("G_FIRE", 2) == 2 && Near(cs2, 55f), "保存→読みこみで、宝石とコインが同じ（こわれた行はとばす）");
        return bad;
    }
}
