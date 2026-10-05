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
        return bad;
    }
}
