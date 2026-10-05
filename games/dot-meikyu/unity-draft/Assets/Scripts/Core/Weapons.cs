using System;

namespace DotMeikyu.Core
{
    public enum WeaponKind { Sword, Bow, Staff }
    public enum Rarity { Common, Rare, Epic, Legend }

    // 武器1本。数値のもとは design/weapons.csv（ここでは、そのとおりの値を入れてある。あとで表から読む形にできる）
    public sealed class WeaponItem
    {
        public WeaponKind Kind;
        public Rarity Rarity;
        public float Damage;          // レア度とゆらぎをかけたあとの基本ダメージ
        public float Interval;        // 攻撃の間隔（秒）
        public int AffixCount;        // おまけ効果の数（レア度で0〜3）
        public int[] Gems = new int[2];   // 穴2つ（0＝あいている。宝石のidは、あとで）

        public static readonly float[] RarityMul = { 1.00f, 1.25f, 1.60f, 2.20f };
        public static readonly float[] RarityChance = { 0.70f, 0.22f, 0.07f, 0.01f };

        public float Score { get { return Damage / Interval * (1f + 0.12f * AffixCount) * (Kind == WeaponKind.Sword ? 0.85f : 1f); } }

        public static WeaponItem Create(WeaponKind kind, Rarity rarity, Random rng)
        {
            float baseDmg, baseInterval;
            switch (kind) { case WeaponKind.Bow: baseDmg = 8f; baseInterval = 0.8f; break; case WeaponKind.Staff: baseDmg = 9f; baseInterval = 1.4f; break; default: baseDmg = 10f; baseInterval = 1.0f; break; }
            var w = new WeaponItem { Kind = kind, Rarity = rarity, AffixCount = (int)rarity };
            w.Damage = baseDmg * RarityMul[(int)rarity] * (0.9f + 0.2f * (float)rng.NextDouble());        // ゆらぎ ±10%
            w.Interval = baseInterval * (0.95f + 0.1f * (float)rng.NextDouble());                          // ゆらぎ ±5%
            return w;
        }

        public static WeaponItem Random(Random rng, int rarityBonus = 0)
        {
            double r = rng.NextDouble(); int rar = 0; double acc = 0;
            for (; rar < 3; rar++) { acc += RarityChance[rar]; if (r < acc) break; }
            rar = Math.Min(3, rar + rarityBonus);
            return Create((WeaponKind)rng.Next(3), (Rarity)rar, rng);
        }

        // 拾った武器が、いま持っている武器より弱いか（ペットは、弱いものを食べ、強いものは倉庫へ送る）
        public bool WeakerThan(WeaponItem other) { return Score <= other.Score; }
    }
}
