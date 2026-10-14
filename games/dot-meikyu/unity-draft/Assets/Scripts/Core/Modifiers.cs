using System;
using System.Collections.Generic;

namespace DotMeikyu.Core
{
    // 持っているカード・宝石・魔法使いから決まる「強さの合計」。毎回つくり直す（design/cards.csv・gems.csv・synergy.csv・jobs.csv）
    public sealed class Modifiers
    {
        // 数字の強化
        public float DamageBonus, AttackSpeedBonus, MoveBonus, CritChanceAdd, CritDmgAdd, Lifesteal, MaxHpAdd, DamageTakenMul = 1f;
        public float AreaBonus, ChargeTimeMul = 1f, PickupBonus, LuckBonus, DashCooldownMul = 1f, SkillIntervalMul = 1f, BulletIntervalMul = 1f, InvulnAdd, SummonLifeAdd;
        // 当たったときに起きること（ふつうの攻撃・ため攻撃）
        public float BurnPct, BurnMul = 1f, BurnTime = 3f;                 // 燃える：毎秒、攻撃のBurnPct
        public float SlowPct, FreezeChance;                                // 遅くする・たまに凍る
        public float ChainChance; public int ChainJumpsAdd;                // 小さな連鎖
        public float PoisonDps, PoisonTime = 4f, PoisonPuddleChance;       // 毒
        public float VsSlowedMul = 1f;                                     // 氷5：遅い・凍った敵への追加ダメージ
        public float FullHpAttackBonus;                                    // 吸血5：HPが満タンのとき
        public bool BurnDeathExplosion, PoisonDeathPuddle, ChargeShockwave;
        public float ReturnRarity2Chance;                                  // 幸運5：ひろい屋が返す武器がレア度+2になる確率
        public float CritVampPct;                                          // 吸血の刃：会心のとき回復
        public float ChargedDamageMul = 1f, ChargingDamageTaken = 1f;      // ためこみ
        public bool CritPierce, SplitBlade;                                // つらぬく一撃・分かれる刃
        public bool EvFire, EvStar;                                        // 進化：太陽の輪・星くずの雨
        // ペット
        public float PetAtkBonus, PetEatSpeedBonus, PetInheritBonus, PetBlock, PetStunMul = 1f, PetRegen, PetSoulMul = 1f, PetFreeze, PetJumpIntervalMul = 1f;
        public int PetJump, PetAcid;                                       // ペットのジャンプ・消化液のレベル（0＝なし）
        // 味方・ジョブ
        public float AllyAtkBonus, AllyHpBonus, JobPetAtkBonus;
    }

    public static class ModifierBuilder
    {
        static readonly Dictionary<string, string> GemTag = new Dictionary<string, string>
        {
            { "G_FIRE", "炎" }, { "G_ICE", "氷" }, { "G_THUNDER", "雷" }, { "G_POISON", "毒" }, { "G_VAMP", "吸血" }, { "G_SPEED", "速さ" }, { "G_CRIT", "会心" },
            { "G_WIDE", "広がり" }, { "G_GLUTTON", "ペット" }, { "G_MAGNET", "幸運" }, { "G_LUCK", "幸運" }, { "G_CHARGE", "ため" }
        };
        static readonly float[] GemFire = { 0.15f, 0.20f, 0.25f, 0.30f, 0.40f }, GemIce = { 0.03f, 0.05f, 0.07f, 0.09f, 0.12f }, GemThunder = { 0.15f, 0.20f, 0.25f, 0.30f, 0.40f },
            GemPoison = { 0.10f, 0.14f, 0.18f, 0.23f, 0.30f }, GemVamp = { 0.010f, 0.015f, 0.020f, 0.025f, 0.030f }, GemSpeed = { 0.05f, 0.08f, 0.11f, 0.14f, 0.18f },
            GemCrit = { 0.04f, 0.06f, 0.08f, 0.10f, 0.13f }, GemWide = { 0.08f, 0.12f, 0.16f, 0.20f, 0.25f }, GemMagnet = { 0.30f, 0.45f, 0.60f, 0.75f, 1.00f },
            GemLuck = { 0.10f, 0.15f, 0.20f, 0.25f, 0.30f }, GemCharge = { 0.08f, 0.12f, 0.16f, 0.20f, 0.25f }, GemGlutton = { 0.20f, 0.30f, 0.40f, 0.50f, 0.60f }, GemGluttonInherit = { 0.20f, 0.25f, 0.30f, 0.35f, 0.40f };

        static float At(float[] t, int lv) { return t[Math.Max(1, Math.Min(5, lv)) - 1]; }

        public static Modifiers Build(RunCards run, WeaponItem weapon, DataTables data)
        {
            var m = new Modifiers(); var tags = new Dictionary<string, int>();
            Func<string, int> L = id => run.Level(id);
            // ---- カード ----
            m.DamageBonus += 0.10f * L("U01"); m.AttackSpeedBonus += 0.08f * L("U02"); m.MoveBonus += 0.08f * L("U03");
            m.CritChanceAdd += 0.06f * L("U04"); m.CritDmgAdd += 0.20f * L("U05"); m.Lifesteal += 0.015f * L("U06");
            m.MaxHpAdd += 15f * L("U07"); m.DamageTakenMul *= (float)Math.Pow(1f - 0.06f, L("U08")); m.AreaBonus += 0.10f * L("U09");
            m.ChargeTimeMul *= 1f - 0.10f * L("U10"); m.PickupBonus += 0.25f * L("U11"); m.LuckBonus += 0.15f * L("U12"); m.DashCooldownMul *= 1f - 0.15f * L("U13");
            if (L("CH1") > 0) { m.BurnPct += 0.15f + 0.05f * (L("CH1") - 1); }
            if (L("CH2") > 0) { m.SlowPct = Math.Max(m.SlowPct, 0.25f); if (L("CH2") >= 3) m.FreezeChance += 0.10f; }
            if (L("CH3") > 0) m.ChainChance += 0.20f + 0.10f * (L("CH3") - 1);
            if (L("CH4") > 0) m.PoisonDps += 3f + 2f * (L("CH4") - 1);
            if (L("CH5") > 0) m.SplitBlade = true;
            if (L("CH6") > 0) m.CritPierce = true;
            if (L("CH7") > 0) { m.ChargedDamageMul += 0.30f; m.ChargingDamageTaken = 0.70f; }
            if (L("CH8") > 0) m.CritVampPct = 0.05f;
            m.EvFire = L("EV1") > 0; m.EvStar = L("EV2") > 0;
            // ペットカード
            m.PetAtkBonus += 0.20f * L("PT1"); m.PetJump = L("PT2"); m.PetAcid = L("PT3");
            m.PetEatSpeedBonus += 0.30f * L("PT4"); m.PetInheritBonus += 0.20f * L("PT4"); m.PetBlock = 0.25f * L("PT5");
            m.PetStunMul *= 1f - 0.25f * L("PT6"); m.PetRegen = L("PT6") > 0 ? 0.5f : 0f; m.PetSoulMul += 0.50f * (L("PT7") > 0 ? 1 : 0); m.PetFreeze = L("PT8") > 0 ? 1f : 0f;
            // ---- 宝石（穴2つ）。同じ宝石を2つはめたら、2つめは効果が半分 ----
            var seen = new HashSet<string>(); int gemTags = 0;
            if (weapon != null) foreach (var g in weapon.Gems)
            {
                if (g == null) continue; float k = seen.Add(g.Id) ? 1f : 0.5f; int lv = g.Level;
                switch (g.Id)
                {
                    case "G_FIRE": m.BurnPct += At(GemFire, lv) * k; break;
                    case "G_ICE": m.SlowPct = Math.Max(m.SlowPct, 0.30f); m.FreezeChance += At(GemIce, lv) * k; break;
                    case "G_THUNDER": m.ChainChance += At(GemThunder, lv) * k; break;
                    case "G_POISON": m.PoisonPuddleChance += At(GemPoison, lv) * k; break;
                    case "G_VAMP": m.Lifesteal += At(GemVamp, lv) * k; break;
                    case "G_SPEED": m.AttackSpeedBonus += At(GemSpeed, lv) * k; break;
                    case "G_CRIT": m.CritChanceAdd += At(GemCrit, lv) * k; break;
                    case "G_WIDE": m.AreaBonus += At(GemWide, lv) * k; break;
                    case "G_MAGNET": m.PickupBonus += At(GemMagnet, lv) * k; break;
                    case "G_LUCK": m.LuckBonus += At(GemLuck, lv) * k; break;
                    case "G_CHARGE": m.ChargeTimeMul *= 1f - At(GemCharge, lv) * k; break;
                    case "G_GLUTTON": m.PetEatSpeedBonus += At(GemGlutton, lv) * k; m.PetInheritBonus += At(GemGluttonInherit, lv) * k; break;
                }
                string tg; if (GemTag.TryGetValue(g.Id, out tg) && gemTags < 2) { gemTags++; Inc(tags, tg); }
            }
            // ---- シナジー：持っているカードの「種類の数」＋はめた宝石（最大2枚分）をタグごとに数える ----
            foreach (var c in data.Cards) if (run.Level(c.Id) > 0 && c.Tag != "" && c.Tag != "なし") Inc(tags, c.Tag);
            Func<string, int> T = t => { int v; return tags.TryGetValue(t, out v) ? v : 0; };
            if (T("炎") >= 3) m.BurnMul += 0.30f; if (T("炎") >= 5) m.BurnDeathExplosion = true;
            if (T("氷") >= 3) m.SlowPct += 0.15f * (m.SlowPct > 0f ? 1f : 0f); if (T("氷") >= 5) m.VsSlowedMul = 1.5f;
            if (T("雷") >= 3) m.ChainJumpsAdd += 1;
            if (T("毒") >= 3) m.PoisonTime += 2f; if (T("毒") >= 5) m.PoisonDeathPuddle = true;
            if (T("速さ") >= 3) m.MoveBonus += 0.10f; if (T("速さ") >= 5) m.SkillIntervalMul *= 0.90f;
            if (T("会心") >= 3) m.CritDmgAdd += 0.30f;
            if (T("吸血") >= 5) m.FullHpAttackBonus = 0.15f;
            if (T("広がり") >= 3) m.AreaBonus += 0.15f;
            if (T("守り") >= 3) m.DamageTakenMul *= 0.90f; if (T("守り") >= 5) m.InvulnAdd += 0.4f;
            if (T("ため") >= 3) m.ChargeTimeMul *= 0.85f; if (T("ため") >= 5) m.ChargeShockwave = true;
            if (T("ペット") >= 3) m.PetAtkBonus += 0.25f; if (T("ペット") >= 5) { m.PetStunMul *= 0.5f; m.PetJumpIntervalMul *= 0.8f; }
            if (T("幸運") >= 3) m.LuckBonus += 0.15f; if (T("幸運") >= 5) m.ReturnRarity2Chance = 0.10f;
            // ---- 魔法使いのパッシブ ----
            switch (run.Job)
            {
                case "連射": m.BulletIntervalMul *= 0.90f; break;
                case "範囲": m.AreaBonus += 0.15f; m.BurnTime *= 1.2f; m.PoisonTime *= 1.2f; break;
                case "獣": m.AllyAtkBonus += 0.15f; m.PetAtkBonus += 0.30f; m.AllyHpBonus += 0.30f; m.SummonLifeAdd += 2f; break;
                case "騎士団": m.AllyAtkBonus += 0.25f; m.PetAtkBonus += 0.15f; m.AllyHpBonus += 0.60f; break;
                case "精霊": m.AllyAtkBonus += 0.15f; m.PetAtkBonus += 0.15f; m.AllyHpBonus += 0.30f; m.SkillIntervalMul *= 0.92f; break;
                case "召喚": m.AllyAtkBonus += 0.15f; m.PetAtkBonus += 0.15f; m.AllyHpBonus += 0.30f; break;   // 古い呼び名（テスト用）
            }
            m.ChargeTimeMul = Math.Max(0.3f, m.ChargeTimeMul); m.DashCooldownMul = Math.Max(0.3f, m.DashCooldownMul);
            return m;
        }

        static void Inc(Dictionary<string, int> d, string k) { int v; d.TryGetValue(k, out v); d[k] = v + 1; }

        // 魔法使いごとの、最初から持っているスキル
        public static string StartSkill(string job) { return job == "範囲" ? "SK_A1" : job == "騎士団" || job == "召喚" ? "SK_M1" : job == "獣" ? "SK_M7" : job == "精霊" ? "SK_M3" : "SK_R1"; }
    }
}
