using System;

namespace DotMeikyu.Core
{
    // ペットのスライム：ついてくる・体当たり・落ちた武器へ自動で向かう（先に着いたほうが取る）
    public sealed partial class Sim
    {
        public static readonly int[] EatPoints = { 1, 2, 3, 5 };   // 食べた武器のレア度ごとの成長点

        public void HurtPet(float dmg)
        {
            if (Pet.Stun > 0f) return;
            Pet.Hp -= dmg; Events.Add(new SimEvent(EventKind.PetHurt, Pet.Pos, Pet.Pos, dmg));
            if (Pet.Hp <= 0f) { Pet.Hp = 0f; Pet.Stun = 8f * Mods.PetStunMul; Events.Add(new SimEvent(EventKind.PetStunned, Pet.Pos, Pet.Pos, Pet.Stun)); }   // やられても、8秒気絶するだけ
        }

        void StepPet(float dt)
        {
            var pt = Pet;
            if (pt.Stun > 0f) { pt.Stun -= dt; if (pt.Stun <= 0f) { pt.Hp = pt.MaxHp; Events.Add(new SimEvent(EventKind.PetWoke, pt.Pos, pt.Pos, 0f)); } return; }
            // 落ちた武器：一番近いものへ（12マス以内）。先に着いたほうが取る
            DroppedWeapon target = null; float bd = 12f;
            foreach (var d in Drops) { if (d.Taken) continue; float k = (d.Pos - pt.Pos).Length; if (k < bd) { bd = k; target = d; } }
            if (target != null)
            {
                pt.Pos = pt.Pos + (target.Pos - pt.Pos).Normalized * (2.5f * (1f + Mods.PetEatSpeedBonus) * dt);
                if ((target.Pos - pt.Pos).Length < 0.5f && TryTake(target, "pet")) PetTake(target);
            }
            else
            {   // ついてくる（1.3マスの距離）
                Vec2 toP = Player.Pos - pt.Pos; float dp = toP.Length;
                if (dp > 1.3f) pt.Pos = pt.Pos + toP.Normalized * (Math.Min(3.5f, 1.5f + dp) * dt);
            }
            // 体当たり：近くの敵に、1.2秒ごと
            pt.AttackCd -= dt;
            if (pt.AttackCd <= 0f)
            {
                Mob t = Nearest(pt.Pos, 0.8f);
                if (t != null)
                {
                    t.LastHitByPet = true; float atk = pt.Damage * (1f + Mods.PetAtkBonus + Mods.JobPetAtkBonus);
                    DamageMob(t, atk, pt.Pos, false, 0.3f);
                    if (t.Alive && Mods.PetFreeze > 0f) t.Stun = Math.Max(t.Stun, Mods.PetFreeze);   // ひっつき
                    pt.AttackCd = 1.2f;
                }
                else pt.AttackCd = 0.1f;
            }
            // ぷるぷるジャンプ：4秒ごとに、着地で範囲ダメージ（半径1.5・ダメ12）
            if (Mods.PetJump > 0) { pt.JumpCd -= dt; if (pt.JumpCd <= 0f) { pt.JumpCd = 4f * Mods.PetJumpIntervalMul; if (Nearest(pt.Pos, 2.5f) != null) AreaHit(pt.Pos, 1.5f, 12f * (1f + 0.3f * (Mods.PetJump - 1)), 0.5f); } }
            // 消化液：1.5秒ごとに、酸の弾（ダメ5・遅くする）
            if (Mods.PetAcid > 0) { pt.AcidCd -= dt; if (pt.AcidCd <= 0f) { pt.AcidCd = 1.5f; Mob t = Nearest(pt.Pos, 6f); if (t != null) { DamageMob(t, 5f * (1f + 0.3f * (Mods.PetAcid - 1)), pt.Pos, false); if (t.Alive) { t.SlowPct = 0.3f; t.SlowLeft = 1.5f; } Events.Add(new SimEvent(EventKind.Arrow, pt.Pos, t.Pos, 1f, "acid")); } } }
        }

        // ペットが武器を取った：いまの武器より弱ければ食べて消える（成長点）。強ければ倉庫へ送る（残る）
        void PetTake(DroppedWeapon d)
        {
            var item = d.Item;
            if (item.WeakerThan(Weapon))
            {
                Pet.Growth += EatPoints[(int)item.Rarity]; Pet.AffixCount = Math.Min(3, Pet.AffixCount + (item.AffixCount > 0 ? 1 : 0));
                if (item.Kind == WeaponKind.Sword) Pet.AteSword++; else if (item.Kind == WeaponKind.Bow) Pet.AteBow++; else Pet.AteStaff++;
                Events.Add(new SimEvent(EventKind.PetAte, d.Pos, d.Pos, (float)item.Rarity, item.Kind.ToString()));
            }
            else { Storage.Add(item); Events.Add(new SimEvent(EventKind.WeaponStored, d.Pos, d.Pos, (float)item.Rarity, "pet")); }
        }
    }
}
