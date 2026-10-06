using System;
using System.Collections.Generic;
using System.IO;
using DotMeikyu.Core;

// 強さの釣り合いを見る試走：ボットが逃げながら戦い、レベルアップでカードを選ぶ。
// 実行：sh tests/run_balance.sh   （本物の遊びより下手な動きなので、「だいたいの目安」）
static class Balance
{
    static DataTables data;
    static void Bot(Sim s)
    {
        Vec2 away = Vec2.Zero; foreach (var m in s.Mobs) { if (!m.Alive) continue; Vec2 d = s.Player.Pos - m.Pos; float l = d.Length; if (l < 4f && l > 0.01f) away = away + d.Normalized * (1f / l); }
        Vec2 go = away.Length > 0.01f ? away.Normalized : Vec2.Zero;
        if (go.Length < 0.01f) { foreach (var d in s.Drops) if (!d.Taken && (d.Pos - s.Player.Pos).Length < 8f) { go = (d.Pos - s.Player.Pos).Normalized; break; } }
        s.Player.Pos = s.Player.Pos + go * (3.5f * 0.05f * (1f + s.Mods.MoveBonus));
    }

    // カード選び：スキルを優先（4つまで）、つぎにレベルの高いものを伸ばす、それ以外はランダム
    static void PickCard(Sim s, CardPicker pk, Random r)
    {
        var three = pk.Pick3(s.Cards); if (three.Count == 0) return;
        CardDef best = null; float bs = -1f;
        foreach (var c in three)
        {
            float sc = (float)r.NextDouble();
            if (c.Kind == CardKind.Skill) sc += 1.0f + (s.Cards.Level(c.Id) > 0 ? 0.3f : 0f);
            else if (c.Kind == CardKind.Pet) sc += 0.4f;
            else if (s.Cards.Level(c.Id) > 0) sc += 0.3f;
            if (sc > bs) { bs = sc; best = c; }
        }
        s.ApplyCard(best);
    }

    // 1回の挑戦：region の場所1〜5とボス。場所の間に、HPを30%回復（出口の「休憩」を、平均して取った想定）
    static float lastBossLeft;
    static string OneRun(string school, string region, Rarity rarity, int seed, out int reached, out bool cleared)
    {
        var rnd = new Random(seed); var w = WeaponItem.Create(WeaponKind.Staff, rarity, rnd);
        var s = new Sim(data, w, seed); s.StartRun(school); var pk = new CardPicker(data.Cards, new Random(seed + 1)); var dr = new StageDirector(s) { Region = region };
        string log = ""; reached = 0; cleared = false;
        for (int stg = 0; stg <= 5 && s.Player.Alive; stg++)
        {
            dr.Begin(stg); float t = 0f; reached = stg + 1;
            while (s.Player.Alive && t < 240f && !(dr.ExitsOpen && t > 0f))
            {
                while (s.PendingLevelUps > 0) { s.TakeLevelUp(); PickCard(s, pk, rnd); }
                Bot(s); s.Tick(0.05f); dr.Tick(0.05f); t += 0.05f;
            }
            string bh = ""; if (stg == 5) { lastBossLeft = 0f; foreach (var m in s.Mobs) if (m.Alive && m.Def.IsBoss && m.Def.Id != "FB_MINI") lastBossLeft = 100f * m.Hp / m.MaxHp; bh = " ボス残り" + lastBossLeft.ToString("0") + "%"; }
            log += (stg == 5 ? "ボス" : "場所" + (stg + 1)) + "[" + t.ToString("0") + "秒 HP" + Math.Max(0f, s.Player.Hp).ToString("0") + " Lv" + s.Level + bh + "] ";
            if (stg == 5 && s.Player.Alive && dr.ExitsOpen) cleared = true;
            if (!s.Player.Alive) break;
            s.Player.Hp = Math.Min(s.Player.MaxHp, s.Player.Hp + s.Player.MaxHp * 0.30f);
        }
        return log;
    }

    public static int Run(string dir)
    {
        data = DataLoader.Load(File.ReadAllText(Path.Combine(dir, "cards.csv")), File.ReadAllText(Path.Combine(dir, "enemies.csv")), File.ReadAllText(Path.Combine(dir, "gems.csv")));
        foreach (string region in new[] { "森", "洞窟" })
        foreach (Rarity rar in new[] { Rarity.Common, Rarity.Rare, Rarity.Epic })
        foreach (string school in new[] { "獣", "騎士団", "精霊" })
        {
            int N = 12, clear = 0; var reach = new int[7]; string sample = ""; float bossLeft = 0f; int bossN = 0;
            for (int i = 0; i < N; i++) { int rc; bool cl; string log = OneRun(school, region, rar, 100 + i * 7, out rc, out cl); reach[rc]++; if (cl) clear++; if (rc == 6) { bossLeft += lastBossLeft; bossN++; } if (i == 0) sample = log; }
            string dist = ""; for (int k = 1; k <= 6; k++) dist += (k == 6 ? "ボス" : "場所" + k) + "止まり" + reach[k] + " ";
            Console.WriteLine(region + "・" + school + "・武器" + rar + "：クリア " + clear + "/" + N + "　ボスまで着いた " + bossN + "回（そのときボスの平均のこり " + (bossN > 0 ? (bossLeft / bossN).ToString("0") : "-") + "%）　" + dist + "\n    例：" + sample);
        }
        return 0;
    }
}
