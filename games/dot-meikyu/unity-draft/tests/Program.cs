using System;
using System.Collections.Generic;
using System.IO;
using DotMeikyu.Core;

// 実行：mcs ... && mono check.exe <designフォルダのパス>
static class Check
{
    static int bad = 0;
    static void Ok(bool cond, string msg) { Console.WriteLine((cond ? "OK   " : "NG   ") + msg); if (!cond) bad++; }

    static int Main(string[] args)
    {
        string dir = args.Length > 0 ? args[0] : "../../design";
        var d = DataLoader.Load(File.ReadAllText(Path.Combine(dir, "cards.csv")), File.ReadAllText(Path.Combine(dir, "enemies.csv")), File.ReadAllText(Path.Combine(dir, "gems.csv")));
        Ok(d.Cards.Count == 61, "カードは61枚 → " + d.Cards.Count);
        Ok(d.Enemies.Count == 17, "敵は17体 → " + d.Enemies.Count);
        Ok(d.Gems.Count == 12, "宝石は12種類 → " + d.Gems.Count);
        var kobold = d.Enemies.Find(e => e.Id == "F05");
        Ok(kobold != null && Math.Abs(kobold.Speed - 2.2f) < 0.001f && kobold.Hp == 30f && kobold.IsThief, "ひろい屋コボルト：速さ2.2・体力30");
        var slime = d.Enemies.Find(e => e.Id == "F01");
        Ok(Math.Abs(slime.WeaponDrop - 0.005f) < 1e-6f && Math.Abs(slime.GemDrop - 0.002f) < 1e-6f, "スライム：武器0.5%・宝石0.2%");
        var king = d.Enemies.Find(e => e.Id == "FB");
        Ok(king.IsBoss && king.Hp == 4000f && Math.Abs(king.WeaponDrop - 1f) < 1e-6f, "スライム王：体力4000・武器100%");
        var mush = d.Enemies.Find(e => e.Id == "F04");
        Ok(mush.RangedMax == 3f, "毒キノコの毒：3 → " + mush.RangedMax);
        var cave = d.Enemies.Find(e => e.Id == "C01");
        Ok(!cave.HasNumbers, "洞窟の敵は、まだ数値なし");
        var potion = d.Cards.Find(c => c.Id == "U14");
        Ok(potion.OnlyWhenHpLow && potion.MaxLevel == 99, "薬びん：HPが低いときだけ");
        Ok(d.Cards.Find(c => c.Id == "EV1").IsEvolution, "進化カードの目印");
        Ok(d.Gems.FindAll(g => g.FirstRelease).Count == 8, "最初の版の宝石は8種類");

        // カード3枚を、たくさん引いて、決まりどおりか調べる
        foreach (string job in new[] { "獣", "騎士団", "精霊" })
        {
            var picker = new CardPicker(d.Cards, new Random(12345));
            var run = new RunCards { Job = job };
            int pet = 0, skillOwn = 0, skillCommon = 0, skillOther = 0, dup = 0, n = 6000, strengthen = 0, skill = 0, change = 0, ev = 0, potionBad = 0, foreign = 0;
            for (int i = 0; i < n; i++)
            {
                var three = picker.Pick3(run);
                if (three.Count != 3) { Ok(false, "3枚出ない"); return 1; }
                var ids = new HashSet<string>(); foreach (var c in three) if (!ids.Add(c.Id)) dup++;
                foreach (var c in three)
                {
                    if (c.Kind == CardKind.Pet) pet++;
                    if (c.Kind == CardKind.Strengthen) strengthen++;
                    if (c.Kind == CardKind.Change) change++;
                    if (c.IsEvolution) ev++;
                    if (c.OnlyWhenHpLow) potionBad++;
                    if (c.Kind == CardKind.Skill)
                    {
                        skill++;
                        if (c.Job == "共通") skillCommon++; else if (c.Job == job) skillOwn++; else { skillOther++; foreign++; }
                    }
                }
            }
            Console.WriteLine("--- 召喚・" + job + "の流派（6000回）：強化" + strengthen + " スキル" + skill + " 変化" + change + " ペット" + pet);
            Ok(dup == 0, "同じカードが重ならない");
            Ok(skillOther == 0, "ほかの流派・あとの更新の魔法使い（連射・範囲）の専用スキルは出ない");
            double share = (double)skillOwn / (skillOwn + skillCommon);
            Ok(share > 0.5 && share < 0.7, "スキルの専用の割合 約60% → " + (share * 100).ToString("0") + "%");
            double petRate = (double)pet / n; Ok(petRate > 0.28 && petRate < 0.42, "3枚の中にペットが出る確率 約35% → " + (petRate * 100).ToString("0") + "%");
            Ok(ev == 0 && potionBad == 0, "進化と薬びんは、条件がないと出ない");
        }

        // スキルが4つそろったら、新しいスキルは出ない
        var full = new RunCards { Job = "騎士団" };
        foreach (var id in new[] { "SK_M1", "SK_M2", "SK_C1", "SK_C2" }) full.Levels[id] = 1;
        var p2 = new CardPicker(d.Cards, new Random(7)); bool newSkill = false;
        for (int i = 0; i < 3000; i++) foreach (var c in p2.Pick3(full)) if (c.Kind == CardKind.Skill && full.Level(c.Id) == 0) newSkill = true;
        Ok(!newSkill, "スキル4つ：新しいスキルは出ない");
        // 進化できるとき
        var evRun = new RunCards { Job = "連射" }; evRun.EvolutionReady.Add("EV2"); evRun.Levels["SK_R1"] = 5;
        var p3 = new CardPicker(d.Cards, new Random(9)); bool sawEv = false;
        for (int i = 0; i < 3000; i++) foreach (var c in p3.Pick3(evRun)) if (c.Id == "EV2") sawEv = true;
        Ok(sawEv, "条件を満たすと進化カードが出る");
        // HPが低いとき薬びん
        var low = new RunCards { HpRatio = 0.3f }; var p4 = new CardPicker(d.Cards, new Random(3)); bool sawPotion = false;
        for (int i = 0; i < 3000; i++) foreach (var c in p4.Pick3(low)) if (c.Id == "U14") sawPotion = true;
        Ok(sawPotion, "HPが低いと薬びんが出る");

        bad += PlayerChecks.Run();
        bad += SimChecks.Run(dir);
        bad += EffectChecks.Run(dir);
        Console.WriteLine(bad == 0 ? "すべてOK" : ("失敗 " + bad + " 件"));
        return bad == 0 ? 0 : 1;
    }
}
