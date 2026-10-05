using System;
using System.Collections.Generic;

namespace DotMeikyu.Core
{
    // いまの挑戦の状態（カードを選ぶのに必要なぶんだけ）
    public sealed class RunCards
    {
        public string Job = "連射";                                              // 連射／範囲／召喚
        public float HpRatio = 1f;                                               // 0〜1
        public Dictionary<string, int> Levels = new Dictionary<string, int>();   // カードid → いまのレベル
        public HashSet<string> EvolutionReady = new HashSet<string>();           // 進化の条件を満たしたカードid
        public int Level(string id) { int v; return Levels.TryGetValue(id, out v) ? v : 0; }
        public int OwnedSkillCount { get { int n = 0; foreach (var kv in Levels) if (kv.Key.StartsWith("SK_") && kv.Value > 0) n++; return n; } }
    }

    // レベルアップのときの「カード3枚」を決める（design/run.csv のカードの決まりどおり）
    public sealed class CardPicker
    {
        public const int SkillLimit = 4;
        public float WStrengthen = 45f, WSkill = 30f, WChange = 25f;   // 1枚ごとの種類の割合
        public float PetSlotChance = 0.35f;                            // 3枚のうち1枚をペットにする確率
        public float JobSpecificShare = 0.60f;                         // スキルは専用60%・共通40%

        readonly List<CardDef> all; readonly Random rng;
        public CardPicker(List<CardDef> cards, Random random) { all = cards; rng = random; }

        public List<CardDef> Pick3(RunCards run)
        {
            var picked = new List<CardDef>();
            if (rng.NextDouble() < PetSlotChance) { var p = PickPet(run, picked); if (p != null) picked.Add(p); }
            int guard = 0;
            while (picked.Count < 3 && guard++ < 60)
            {
                var c = PickOne(run, picked); if (c != null) picked.Add(c);
            }
            // 候補が足りないとき：のこりのどれかで埋める
            if (picked.Count < 3) foreach (var c in Eligible(run, picked, null)) { if (picked.Count >= 3) break; picked.Add(c); }
            return picked;
        }

        CardDef PickPet(RunCards run, List<CardDef> picked) { return Weighted(Eligible(run, picked, CardKind.Pet)); }

        CardDef PickOne(RunCards run, List<CardDef> picked)
        {
            var kinds = new[] { CardKind.Strengthen, CardKind.Skill, CardKind.Change };
            var w = new[] { WStrengthen, WSkill, WChange };
            // 候補のない種類は、割合を0にする
            for (int i = 0; i < kinds.Length; i++) if (Eligible(run, picked, kinds[i]).Count == 0) w[i] = 0f;
            float total = 0f; foreach (var x in w) total += x; if (total <= 0f) return null;
            float r = (float)rng.NextDouble() * total; int k = 0;
            for (; k < w.Length - 1; k++) { if (r < w[k]) break; r -= w[k]; }
            if (kinds[k] == CardKind.Skill) return PickSkill(run, picked);
            return Weighted(Eligible(run, picked, kinds[k]));
        }

        // スキル：4つそろったら、持っているスキルのレベル上げだけ。それまでは専用60%・共通40%
        CardDef PickSkill(RunCards run, List<CardDef> picked)
        {
            var pool = Eligible(run, picked, CardKind.Skill); if (pool.Count == 0) return null;
            var special = new List<CardDef>(); var common = new List<CardDef>();
            foreach (var c in pool) { if (c.Job == "共通") common.Add(c); else special.Add(c); }
            bool wantSpecial = rng.NextDouble() < JobSpecificShare;
            var from = (wantSpecial && special.Count > 0) || common.Count == 0 ? special : common;
            return Weighted(from.Count > 0 ? from : pool);
        }

        // いま出していい候補（レベル上限・ジョブ・条件・かぶりを除く）
        public List<CardDef> Eligible(RunCards run, List<CardDef> picked, CardKind? kind)
        {
            var res = new List<CardDef>();
            bool skillsFull = run.OwnedSkillCount >= SkillLimit;
            foreach (var c in all)
            {
                if (kind.HasValue && c.Kind != kind.Value) continue;
                if (picked.Contains(c)) continue;
                if (run.Level(c.Id) >= c.MaxLevel) continue;
                if (c.OnlyWhenHpLow && run.HpRatio > 0.5f) continue;
                if (c.IsEvolution && !run.EvolutionReady.Contains(c.Id)) continue;
                if (c.Kind == CardKind.Skill)
                {
                    if (c.Job != "共通" && c.Job != run.Job) continue;          // ほかの魔法使いの専用スキルは出ない
                    if (skillsFull && run.Level(c.Id) == 0) continue;           // 4つそろったら、新しいスキルは出ない
                }
                else if (c.Job != "" && c.Job != "共通" && c.Job != run.Job) continue;
                res.Add(c);
            }
            return res;
        }

        CardDef Weighted(List<CardDef> pool)
        {
            if (pool.Count == 0) return null;
            float total = 0f; foreach (var c in pool) total += Math.Max(0.0001f, c.Weight);
            float r = (float)rng.NextDouble() * total;
            foreach (var c in pool) { r -= Math.Max(0.0001f, c.Weight); if (r < 0f) return c; }
            return pool[pool.Count - 1];
        }
    }
}
