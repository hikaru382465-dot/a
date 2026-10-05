using System;
using System.Collections.Generic;

namespace DotMeikyu.Core
{
    // プレイヤーの自動攻撃とため攻撃（design/weapons.csv の値）
    public sealed partial class Sim
    {
        // 自動攻撃。ねらう敵がいて攻撃したら true
        bool AutoAttack()
        {
            var w = Weapon; float dmg = w.Damage; Vec2 p = Player.Pos;
            switch (w.Kind)
            {
                case WeaponKind.Sword:
                    {   // 自分のまわり（半径1.6）の敵を、ぜんぶ切る。はね返し0.8マス
                        bool any = false;
                        foreach (var m in Mobs) if (m.Alive && m.SpawnDelay <= 0f && (m.Pos - p).Length < 1.6f + m.Radius) { DamageMob(m, dmg, p, true, 0.8f); any = true; }
                        if (any) Events.Add(new SimEvent(EventKind.Slash, p, p, 1.6f));
                        return any;
                    }
                case WeaponKind.Bow:
                    {   // 一番近い敵（7マス以内）へ。まっすぐ3体までつらぬく
                        Mob t = Nearest(p, 7f); if (t == null) return false;
                        Vec2 dir = (t.Pos - p).Normalized; ShootLine(p, dir, 7f, dmg, 3, false);
                        return true;
                    }
                default:
                    {   // 杖：稲妻の連鎖。一番近い敵（5マス以内）→ 2.5マス以内の次の敵へ、3回飛びうつる（1回ごとに-15%）
                        Mob t = Nearest(p, 5f); if (t == null) return false;
                        Chain(p, t, dmg, 3, 0.85f, 0f); return true;
                    }
            }
        }

        // まっすぐの線上の敵（距離順に maxHits 体まで。pierceAll なら全部）にダメージ
        void ShootLine(Vec2 from, Vec2 dir, float range, float dmg, int maxHits, bool pierceAll)
        {
            var hits = new List<Mob>();
            foreach (var m in Mobs)
            {
                if (!m.Alive || m.SpawnDelay > 0f) continue;
                Vec2 d = m.Pos - from; float along = d.X * dir.X + d.Y * dir.Y; if (along < 0f || along > range + m.Radius) continue;
                float perp = Math.Abs(d.X * dir.Y - d.Y * dir.X); if (perp < 0.35f + m.Radius) hits.Add(m);
            }
            hits.Sort((a, b) => (a.Pos - from).Length.CompareTo((b.Pos - from).Length));
            int n = 0; Vec2 end = from + dir * range;
            foreach (var m in hits) { if (!pierceAll && n >= maxHits) break; DamageMob(m, dmg, from, true, 0.3f); end = m.Pos; n++; }
            Events.Add(new SimEvent(EventKind.Arrow, from, pierceAll || n == 0 ? from + dir * range : end, n));
        }

        // 稲妻：first にあたり、近くの別の敵へ jumps 回飛びうつる。stun>0 なら、あたった敵は、その秒数しびれる
        void Chain(Vec2 from, Mob first, float dmg, int jumps, float falloff, float stun)
        {
            var hit = new HashSet<Mob>(); Mob cur = first; Vec2 last = from; float d = dmg;
            for (int i = 0; i <= jumps && cur != null; i++)
            {
                hit.Add(cur); Events.Add(new SimEvent(EventKind.Chain, last, cur.Pos, d));
                Vec2 pos = cur.Pos; if (stun > 0f) cur.Stun = Math.Max(cur.Stun, stun);
                DamageMob(cur, d, last, true, 0f);
                last = pos; d *= falloff;
                cur = Nearest(last, 2.5f, hit);
            }
        }

        // ため攻撃（満タンで指を離したとき）。PlayerController の ChargedAttackFired から呼ぶ
        public void FireCharged()
        {
            var w = Weapon; float dmg = w.Damage; Vec2 p = Player.Pos;
            switch (w.Kind)
            {
                case WeaponKind.Sword:
                    {   // 大回転斬り：半径3.2を2回転・強くはね返す（合計 ×5）
                        foreach (var m in Mobs) if (m.Alive && (m.Pos - p).Length < 3.2f + m.Radius) DamageMob(m, dmg * 5f, p, true, 2.0f);
                        Events.Add(new SimEvent(EventKind.Slash, p, p, 3.2f, "charged")); break;
                    }
                case WeaponKind.Bow:
                    {   // つらぬく矢の扇：5本（±20度）・何体でもつらぬく。1本ごとに ×4
                        Mob t = Nearest(p, 9f); Vec2 baseDir = t != null ? (t.Pos - p).Normalized : new Vec2(1f, 0f);
                        for (int i = -2; i <= 2; i++)
                        {
                            double a = Math.Atan2(baseDir.Y, baseDir.X) + i * (20.0 / 2.0) * Math.PI / 180.0;
                            ShootLine(p, new Vec2((float)Math.Cos(a), (float)Math.Sin(a)), 7f, dmg * 4f, 99, true);
                        }
                        break;
                    }
                default:
                    {   // 雷の嵐：12回連鎖＋1秒しびれ（×3.5）
                        Mob t = Nearest(p, 8f); if (t != null) Chain(p, t, dmg * 3.5f, 12, 1f, 1f); break;
                    }
            }
        }
    }
}
