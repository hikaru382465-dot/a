using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace DotMeikyu.Core
{
    // 宝石の持ち物（死んでも残る）。同じ宝石の同じLvを2個で、次のLvにできる（design/gems.csv の FUSE）
    public sealed class GemBag
    {
        public const int MaxLevel = 5;
        public static readonly int[] FuseCost = { 0, 0, 20, 50, 100, 200 };   // Lv(n-1)×2 → Lv n に必要なコイン（添字がn）
        readonly Dictionary<string, int> counts = new Dictionary<string, int>();
        static string Key(string id, int lv) { return id + "|" + lv; }

        public int Count(string id, int lv) { int v; return counts.TryGetValue(Key(id, lv), out v) ? v : 0; }
        public void Add(string id, int lv = 1, int n = 1) { counts[Key(id, lv)] = Count(id, lv) + n; }
        public bool Take(string id, int lv) { int c = Count(id, lv); if (c <= 0) return false; counts[Key(id, lv)] = c - 1; return true; }

        // 合成：Lv(lv)を2個 → Lv(lv+1)を1個。コインが足りないとき・Lv5のときは、何もしない
        public bool Fuse(string id, int lv, ref float coins)
        {
            if (lv >= MaxLevel || Count(id, lv) < 2) return false;
            int cost = FuseCost[lv + 1]; if (coins < cost) return false;
            coins -= cost; counts[Key(id, lv)] = Count(id, lv) - 2; Add(id, lv + 1); return true;
        }

        // 武器の穴にはめる（slot 0か1）。すでにはまっているものは、袋にもどる。袋に無ければ false
        public bool Equip(WeaponItem w, int slot, string id, int lv)
        {
            if (slot < 0 || slot >= w.Gems.Length || !Take(id, lv)) return false;
            Unequip(w, slot); w.Gems[slot] = new GemSlot(id, lv); return true;
        }
        public void Unequip(WeaponItem w, int slot)
        {
            var g = w.Gems[slot]; if (g == null) return; Add(g.Id, g.Level); w.Gems[slot] = null;
        }

        public IEnumerable<KeyValuePair<string, int>> All() { return counts; }
    }

    // 保存：倉庫の武器・宝石・コインを、文字にして出し入れする（Unity側は PlayerPrefs やファイルに書くだけ）
    public static class SaveText
    {
        static readonly CultureInfo C = CultureInfo.InvariantCulture;

        public static string Write(IList<WeaponItem> storage, GemBag bag, float coins)
        {
            var sb = new StringBuilder(); sb.Append("v1\n"); sb.Append("coins,").Append(coins.ToString(C)).Append('\n');
            foreach (var kv in bag.All()) if (kv.Value > 0) { var p = kv.Key.Split('|'); sb.Append("gem,").Append(p[0]).Append(',').Append(p[1]).Append(',').Append(kv.Value).Append('\n'); }
            foreach (var w in storage)
            {
                sb.Append("weapon,").Append(w.Kind).Append(',').Append(w.Rarity).Append(',').Append(w.Damage.ToString(C)).Append(',').Append(w.Interval.ToString(C)).Append(',').Append(w.AffixCount);
                for (int i = 0; i < w.Gems.Length; i++) sb.Append(',').Append(w.Gems[i] == null ? "-" : w.Gems[i].Id + ":" + w.Gems[i].Level);
                sb.Append('\n');
            }
            return sb.ToString();
        }

        // 読めない行は、とばす（こわれたセーブでも、ゲームが止まらないように）
        public static void Read(string text, List<WeaponItem> storage, GemBag bag, out float coins)
        {
            coins = 0f; if (string.IsNullOrEmpty(text)) return;
            foreach (var raw in text.Split('\n'))
            {
                var p = raw.Trim().Split(','); try
                {
                    if (p[0] == "coins") coins = float.Parse(p[1], C);
                    else if (p[0] == "gem") bag.Add(p[1], int.Parse(p[2]), int.Parse(p[3]));
                    else if (p[0] == "weapon")
                    {
                        var w = new WeaponItem { Kind = (WeaponKind)Enum.Parse(typeof(WeaponKind), p[1]), Rarity = (Rarity)Enum.Parse(typeof(Rarity), p[2]), Damage = float.Parse(p[3], C), Interval = float.Parse(p[4], C), AffixCount = int.Parse(p[5]) };
                        for (int i = 0; i < w.Gems.Length && 6 + i < p.Length; i++) if (p[6 + i] != "-") { var g = p[6 + i].Split(':'); w.Gems[i] = new GemSlot(g[0], int.Parse(g[1])); }
                        storage.Add(w);
                    }
                }
                catch (Exception) { }
            }
        }
    }
}
