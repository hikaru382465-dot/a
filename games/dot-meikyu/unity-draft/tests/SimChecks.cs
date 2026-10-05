using System;
using System.Collections.Generic;
using System.IO;
using DotMeikyu.Core;

// 戦闘の世界（Sim）の決まりを、時間を進めて調べる
static class SimChecks
{
    static int bad = 0; static DataTables data;
    static void Ok(bool c, string m) { Console.WriteLine((c ? "OK   " : "NG   ") + m); if (!c) bad++; }

    static Sim NewSim(WeaponKind kind, Rarity r = Rarity.Common, int seed = 1)
    {
        var s = new Sim(data, WeaponItem.Create(kind, r, new Random(seed)), seed);
        s.Player.CritChance = 0f; s.Player.Pos = Vec2.Zero; s.Pet.Pos = new Vec2(-1f, 0f); return s;
    }
    static Mob Put(Sim s, string id, float x, float y, bool frozen = true, float hp = -1f)
    {
        var m = s.Spawn(id, new Vec2(x, y)); m.SpawnDelay = 0f; if (frozen) m.Stun = 99f; if (hp > 0f) { m.Hp = m.MaxHp = hp; } return m;
    }
    static void Run(Sim s, float sec, float dt = 0.05f) { for (float t = 0f; t < sec; t += dt) s.Tick(dt); }
    static int Count(Sim s, EventKind k) { int n = 0; foreach (var e in s.Events) if (e.Kind == k) n++; return n; }

    public static int Run(string dir)
    {
        data = DataLoader.Load(File.ReadAllText(Path.Combine(dir, "cards.csv")), File.ReadAllText(Path.Combine(dir, "enemies.csv")), File.ReadAllText(Path.Combine(dir, "gems.csv")));

        // --- 武器 ---
        var sw = NewSim(WeaponKind.Sword); var sl = Put(sw, "F01", 1f, 0f, true, 100f); var far = Put(sw, "F01", 3f, 0f, true, 100f);
        sw.Tick(0.05f); Ok(sl.Hp < 100f && far.Hp == 100f, "剣：まわり1.6マスの敵だけ切る");
        var bw = NewSim(WeaponKind.Bow); for (int i = 0; i < 4; i++) Put(bw, "F01", 2f + i, 0f, true, 100f); bw.Tick(0.05f);
        Ok(Count(bw, EventKind.Hit) == 3, "弓：まっすぐ3体までつらぬく → " + Count(bw, EventKind.Hit));
        var st = NewSim(WeaponKind.Staff); for (int i = 0; i < 6; i++) Put(st, "F01", 3f + 2f * i, 0f, true, 1000f); st.Tick(0.05f);
        var hits = new List<float>(); foreach (var e in st.Events) if (e.Kind == EventKind.Hit) hits.Add(e.Value);
        Ok(hits.Count == 4, "杖：稲妻は、最初の1体＋3回飛びうつる（4体）→ " + hits.Count);
        Ok(hits.Count == 4 && Math.Abs(hits[1] / hits[0] - 0.85f) < 0.001f && Math.Abs(hits[3] / hits[0] - 0.85f * 0.85f * 0.85f) < 0.001f, "杖：1回ごとに-15%");
        var far2 = NewSim(WeaponKind.Staff); Put(far2, "F01", 3f, 0f, true, 1000f); Put(far2, "F01", 8f, 0f, true, 1000f); far2.Tick(0.05f);
        Ok(Count(far2, EventKind.Hit) == 1, "杖：2.5マスより遠い敵へは、飛びうつらない");

        // --- ため攻撃 ---
        var cs = NewSim(WeaponKind.Sword); var a = Put(cs, "F01", 3f, 0f, true, 1000f); var b = Put(cs, "F01", 0f, -3f, true, 1000f); var c = Put(cs, "F01", 5f, 0f, true, 1000f);
        cs.attackCdForTest(); cs.FireCharged();
        Ok(a.Hp < 1000f && b.Hp < 1000f && c.Hp == 1000f, "剣のため：大回転（半径3.2）");
        Ok(Math.Abs((1000f - a.Hp) / cs.Weapon.Damage - 5f) < 0.01f, "剣のため：ダメージ×5");
        var cb = NewSim(WeaponKind.Bow); var m1 = Put(cb, "F01", 3f, 0f, true, 1000f); var m2 = Put(cb, "F01", 6f, 0f, true, 1000f); var m3 = Put(cb, "F01", 5f, 2.0f, true, 1000f);
        cb.FireCharged(); Ok(m1.Hp < 1000f && m2.Hp < 1000f, "弓のため：扇の矢が、何体でもつらぬく");
        var cst = NewSim(WeaponKind.Staff); var ms = new List<Mob>(); for (int i = 0; i < 5; i++) ms.Add(Put(cst, "F01", 3f + 2f * i, 0f, true, 10000f));
        cst.FireCharged(); Ok(ms[4].Hp < 10000f && ms[0].Stun >= 0.99f, "杖のため：12回連鎖（5体ぜんぶにあたる）＋しびれ1秒");

        // --- 敵の動き ---
        var ar = NewSim(WeaponKind.Staff); ar.Player.DamageMul = 0.0001f; Put(ar, "F03", 5f, 0f, false, 1000f);
        bool tele = false; float hpBefore = ar.Player.Hp; for (int i = 0; i < 40; i++) { ar.Tick(0.05f); if (Count(ar, EventKind.Telegraph) > 0) tele = true; }
        Ok(tele && ar.Player.Hp < hpBefore, "弓兵：赤い予告のあと矢を撃ち、あたると痛い（HP -" + (hpBefore - ar.Player.Hp).ToString("0") + "）");
        var mu = NewSim(WeaponKind.Staff); mu.Player.DamageMul = 0.0001f; Put(mu, "F04", 6f, 0f, false, 1000f); bool cloud = false;
        for (int i = 0; i < 110; i++) { mu.Tick(0.05f); if (Count(mu, EventKind.Cloud) > 0) cloud = true; }
        Ok(cloud && mu.Clouds.Count >= 1, "毒キノコ：4秒歩いて、止まって、胞子の雲を出す");
        mu.Player.Pos = mu.Clouds[0].Pos; float h0 = mu.Player.Hp; Run(mu, 1.2f); Ok(mu.Player.Hp < h0, "毒の雲の中にいると、少しずつ減る（-" + (h0 - mu.Player.Hp).ToString("0.0") + "）");
        var bat = NewSim(WeaponKind.Staff); bat.Player.DamageMul = 0.0001f; var bm = Put(bat, "F02", 6f, 0f, false, 1000f); bat.Player.Invuln = 99f; Run(bat, 1.5f);
        Ok((bm.Pos - bat.Player.Pos).Length < 6f, "コウモリ：ジグザグでも、近づいてくる");

        // --- ひろい屋とペット（取り合い）---
        var tf = NewSim(WeaponKind.Staff); tf.Player.DamageMul = 0.0001f; var drop = tf.DropWeapon(new Vec2(5f, 0f), WeaponItem.Create(WeaponKind.Bow, Rarity.Epic, new Random(3)));
        var thief = Put(tf, "F05", 6f, 0f, false, 100f); tf.Player.Invuln = 99f; Run(tf, 1.0f);
        Ok(thief.Held != null && tf.Storage.Count == 0, "ひろい屋：近いほうが先に取る（ひろい屋が取った）");
        tf.KillMob(thief);
        DroppedWeapon back = tf.Drops.Find(x => !x.Taken);
        Ok(back != null && back.Item.Rarity == Rarity.Legend, "ひろい屋を倒すと、武器がレア度+1で返る（エピック→レジェンド）");
        var pf = NewSim(WeaponKind.Sword, Rarity.Legend); pf.Player.Pos = new Vec2(20f, 20f); pf.Pet.Pos = new Vec2(0f, 0f);
        pf.DropWeapon(new Vec2(1f, 0f), WeaponItem.Create(WeaponKind.Bow, Rarity.Common, new Random(4))); var th2 = Put(pf, "F05", 8f, 0f, false, 100f); Run(pf, 2f);
        Ok(pf.Pet.Growth == 1 && pf.Pet.AteBow == 1 && pf.Storage.Count == 0 && th2.Held == null, "ペットが先に着くと取る。弱い武器は、食べて消える（成長点+1）");
        var ps = NewSim(WeaponKind.Sword, Rarity.Common); ps.Player.Pos = new Vec2(20f, 20f); ps.Pet.Pos = Vec2.Zero;
        ps.DropWeapon(new Vec2(1f, 0f), WeaponItem.Create(WeaponKind.Staff, Rarity.Legend, new Random(5))); Run(ps, 1f);
        Ok(ps.Storage.Count == 1 && ps.Pet.Growth == 0, "強い武器は、ペットが倉庫へ送る（残る）");
        var pk = NewSim(WeaponKind.Sword); pk.HurtPet(1000f); Ok(pk.Pet.Stun > 7f && pk.Pet.Hp == 0f, "ペット：やられると気絶（8秒）");
        Run(pk, 8.2f); Ok(pk.Pet.Stun <= 0f && pk.Pet.Hp == pk.Pet.MaxHp, "ペット：8秒後に、元気になって戻る");
        var pe = NewSim(WeaponKind.Sword); pe.Pet.Growth = 15; pe.Pet.AteStaff = 3; pe.Pet.AteBow = 1;
        Ok(pe.Pet.Stage == 3 && pe.Pet.EvolutionKind == "魔導スライム", "ペット：成長点15で進化（杖をいちばん食べたら、魔導スライム）");
        var pa = NewSim(WeaponKind.Sword); pa.Player.Pos = new Vec2(50f, 50f); pa.Pet.Pos = new Vec2(0f, 0f); var pm = Put(pa, "F01", 0.5f, 0f, true, 100f); Run(pa, 1.3f);
        Ok(pm.Hp < 100f, "ペット：近くの敵に体当たりする");

        // --- スライム王 ---
        var bs = NewSim(WeaponKind.Staff); bs.Player.DamageMul = 0.0001f; bs.Player.DashInvulnerable = true; var bdir = new StageDirector(bs); bdir.Begin(5);
        var king = bs.Mobs.Find(x => x.Def.Id == "FB"); bool dash = false, ring = false, shots = false; king.Hp = king.MaxHp * 0.6f;
        for (int i = 0; i < 1200; i++) { bs.Tick(0.05f); bdir.Tick(0.05f); if (Count(bs, EventKind.Telegraph) > 0) foreach (var e in bs.Events) { if (e.Tag == "dash") dash = true; if (e.Tag == "ring") ring = true; } if (Count(bs, EventKind.ShotFired) >= 12) shots = true; }
        Ok(dash && ring && shots, "スライム王：赤く光る予告（突進・輪）と、弾12発");
        king.Hp = king.MaxHp * 0.3f; Run(bs, 0.2f); int minis = bs.AliveCount("FB_MINI"); Ok(minis == 2, "スライム王：体力40%以下で、小さな王2体に分裂 → " + minis);
        Run(bs, 9f); Ok(bs.AliveCount("F01") >= 3, "スライム王：さらにスライムを呼ぶ");
        bs.KillMob(king); Ok(!bs.BossAlive && bs.AliveCount("FB_MINI") == 0 && bs.Drops.Count >= 1, "スライム王を倒すと、小さな王も消えて、武器が落ちる");
        bdir.Tick(0.05f); Ok(bdir.ExitsOpen, "ボス戦：倒すと、出口が出る");

        // --- 場所の進行 ---
        var sg = NewSim(WeaponKind.Sword, Rarity.Legend); sg.Player.DashInvulnerable = true; var d0 = new StageDirector(sg); d0.Begin(0);
        Ok(sg.AliveCount() == 6, "場所1のはじめ：敵6体");
        float opened = -1f; for (float t = 0f; t < 90f; t += 0.05f) { sg.Tick(0.05f); d0.Tick(0.05f); if (d0.ExitsOpen && opened < 0f) { opened = t; break; } }
        Ok(opened > 0f && opened <= 75.1f, "場所1：75秒か30体で出口が出る（" + opened.ToString("0.0") + "秒・倒した" + d0.StageKills + "体）");
        int spawnedAfter = 0; for (int i = 0; i < 100; i++) { sg.Tick(0.05f); d0.Tick(0.05f); spawnedAfter += Count(sg, EventKind.Spawned); }
        Ok(spawnedAfter == 0, "出口が出たあとは、敵が増えない");
        Ok(Math.Abs(sg.StageAtkMul - 1f) < 1e-4f, "場所1の敵の攻撃：×1.0（場所が進むごとに+10%）");
        d0.Begin(3); Ok(Math.Abs(sg.StageAtkMul - 1.3f) < 1e-4f, "場所4の敵の攻撃：×1.3");

        // --- 通しの試走（ボットが、よけながら戦う。カードなしなので、強さの目安ではない）---
        Console.WriteLine("--- 試走（カードなし・ボットが逃げながら戦う）---");
        foreach (WeaponKind k in new[] { WeaponKind.Sword, WeaponKind.Bow, WeaponKind.Staff })
        {
            var s = NewSim(k, Rarity.Rare, 11); var dr = new StageDirector(s); string log = k + "：";
            for (int stg = 0; stg <= 5 && s.Player.Alive; stg++)
            {
                dr.Begin(stg); float t = 0f;
                while (!dr.ExitsOpen && s.Player.Alive && t < 200f) { Bot(s); s.Tick(0.05f); dr.Tick(0.05f); t += 0.05f; if (float.IsNaN(s.Player.Pos.X)) { Ok(false, "位置がNaN"); return 1; } }
                log += "場所" + (stg + 1) + "[" + t.ToString("0") + "秒 HP" + s.Player.Hp.ToString("0") + " 倒" + dr.StageKills + "] ";
            }
            Console.WriteLine(log + (s.Player.Alive ? "（生きのこり）" : "（倒れた）") + " ペット成長点" + s.Pet.Growth + " 倉庫" + s.Storage.Count);
        }
        return bad;
    }

    // ためしの動き：近い敵から遠ざかり、近くに敵がいなければ落ちた武器へ
    static void Bot(Sim s)
    {
        Vec2 away = Vec2.Zero; foreach (var m in s.Mobs) { if (!m.Alive) continue; Vec2 d = s.Player.Pos - m.Pos; float l = d.Length; if (l < 4f && l > 0.01f) away = away + d.Normalized * (1f / l); }
        Vec2 go = away.Length > 0.01f ? away.Normalized : Vec2.Zero;
        if (go.Length < 0.01f) { foreach (var d in s.Drops) if (!d.Taken && (d.Pos - s.Player.Pos).Length < 8f) { go = (d.Pos - s.Player.Pos).Normalized; break; } }
        s.Player.Pos = s.Player.Pos + go * (3.5f * 0.05f);
    }
}
