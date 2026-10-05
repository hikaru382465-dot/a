using System;
using System.Collections.Generic;

namespace DotMeikyu.Core
{
    // 敵の動き（design/enemies.csv の「メモ」のとおり）
    public sealed partial class Sim
    {
        static Vec2 FromAngle(double a) { return new Vec2((float)Math.Cos(a), (float)Math.Sin(a)); }

        void StepMob(Mob m, float dt)
        {
            if (m.SpawnDelay > 0f) { m.SpawnDelay -= dt; return; }
            m.T += dt;
            m.Pos = m.Pos + m.Knock * dt; m.Knock = m.Knock * (float)Math.Pow(0.02, dt);
            if (m.Stun > 0f) { m.Stun -= dt; return; }
            Vec2 to = Player.Pos - m.Pos; float dist = to.Length; Vec2 dir = to.Normalized; float spd = m.Def.Speed;
            switch (m.Def.Id)
            {
                case "F02":   // コウモリ：0.5秒ごとに向きを±40度かえて、ジグザグに飛ぶ
                    m.Aux -= dt; if (m.Aux <= 0f) { m.Aux = 0.5f; m.Aux2 = Rng.Next(2) == 0 ? -1f : 1f; }
                    m.Pos = m.Pos + FromAngle(Math.Atan2(dir.Y, dir.X) + m.Aux2 * 40.0 * Math.PI / 180.0) * (spd * dt); break;
                case "F03": StepArcher(m, dt, dist, dir); break;
                case "F04": StepMushroom(m, dt, dir); break;
                case "F05": StepThief(m, dt, dist, dir); break;
                case "FB": StepKing(m, dt, dist, dir); break;
                default:      // スライムなど：まっすぐ寄ってくる
                    if (dist > 0.05f) m.Pos = m.Pos + dir * (spd * dt); break;
            }
        }

        // ゴブリン弓兵：4〜6マスの距離を保つ。2.2秒ごとに、0.5秒の赤い予告のあと矢（弾速5）
        void StepArcher(Mob m, float dt, float dist, Vec2 dir)
        {
            if (m.State == 1)
            {
                m.Aux2 -= dt;
                if (m.Aux2 <= 0f) { AddShot(m.Pos, (Player.Pos - m.Pos).Normalized, 5f, m.Def.RangedMax); m.State = 0; m.Aux = 2.2f; }
                return;
            }
            if (dist > 6f) m.Pos = m.Pos + dir * (m.Def.Speed * dt); else if (dist < 4f) m.Pos = m.Pos - dir * (m.Def.Speed * dt);
            m.Aux -= dt;
            if (m.Aux <= 0f && dist < 9f) { m.State = 1; m.Aux2 = 0.5f; Events.Add(new SimEvent(EventKind.Telegraph, m.Pos, Player.Pos, 0.5f, "line")); }
        }

        // 毒キノコ：ゆっくり寄る。4秒ごとに止まって、1秒後に胞子（半径1.5・3秒・毎0.5秒3）
        void StepMushroom(Mob m, float dt, Vec2 dir)
        {
            m.Aux += dt;
            if (m.State == 0) { m.Pos = m.Pos + dir * (m.Def.Speed * dt); if (m.Aux >= 4f) { m.State = 1; m.Aux = 0f; Events.Add(new SimEvent(EventKind.Telegraph, m.Pos, m.Pos, 1f, "ring")); } }
            else if (m.Aux >= 1f) { AddCloud(m.Pos, 1.5f, 3f, 3f); m.State = 0; m.Aux = 0f; }
        }

        // ひろい屋：床に落ちた武器へ走る（先に着いたほうが取る）→ 取ったら、プレイヤーから逃げる（30秒逃げ切ると、武器は失う）
        void StepThief(Mob m, float dt, float dist, Vec2 dir)
        {
            if (m.Held != null)
            {
                m.FleeLeft -= dt;
                m.Pos = m.Pos - dir * (3.0f * dt);
                if (m.FleeLeft <= 0f) { m.Alive = false; Events.Add(new SimEvent(EventKind.WeaponLost, m.Pos, m.Pos, (float)m.Held.Rarity)); }
                return;
            }
            DroppedWeapon target = null; float bd = 1e9f;
            foreach (var d in Drops) { if (d.Taken) continue; float k = (d.Pos - m.Pos).Length; if (k < bd) { bd = k; target = d; } }
            if (target == null) { if (dist > 0.05f) m.Pos = m.Pos + dir * (m.Def.Speed * dt); return; }   // 武器がないとき：プレイヤーへ
            Vec2 td = (target.Pos - m.Pos).Normalized; m.Pos = m.Pos + td * (m.Def.Speed * dt);
            if ((target.Pos - m.Pos).Length < 0.5f && TryTake(target, "thief"))
            {
                m.Held = target.Item; m.FleeLeft = 30f; m.MaxHp *= 1f + 0.5f * (float)m.Held.Rarity; m.Hp = m.MaxHp; m.DamageMul = 1.3f;
                Events.Add(new SimEvent(EventKind.WeaponTaken, m.Pos, m.Pos, (float)m.Held.Rarity, "thief"));
            }
        }

        // スライム王：体力に合わせて、突進→突進＋弾の輪→分裂＋スライムを呼ぶ。攻撃の前に赤く光る
        void StepKing(Mob m, float dt, float dist, Vec2 dir)
        {
            float ratio = m.Hp / m.MaxHp;
            if (ratio < 0.4f && m.Aux2 < 1f)
            {   // 分裂：小さな王2体（体力400）
                m.Aux2 = 1f; Spawn("FB_MINI", m.Pos + new Vec2(1.5f, 0f)); Spawn("FB_MINI", m.Pos + new Vec2(-1.5f, 0f));
            }
            if (ratio < 0.4f) { m.FleeLeft -= dt; if (m.FleeLeft <= 0f) { m.FleeLeft = 8f; for (int i = 0; i < 3; i++) Spawn("F01", m.Pos + FromAngle(i * 2.1) * 2f); } }
            switch (m.State)
            {
                case 0:   // ゆっくり近づいて、次の攻撃をえらぶ
                    m.Pos = m.Pos + dir * (m.Def.Speed * dt); m.Aux += dt;
                    if (m.Aux >= 1.5f)
                    {
                        m.Aux = 0f; bool ring = ratio < 0.7f && Rng.Next(2) == 0;
                        if (ring) { m.State = 3; m.Aux = 0.5f; Events.Add(new SimEvent(EventKind.Telegraph, m.Pos, m.Pos, 0.5f, "ring")); }
                        else { m.State = 1; m.Aux = 0.8f; m.Heading = (float)Math.Atan2(dir.Y, dir.X); Events.Add(new SimEvent(EventKind.Telegraph, m.Pos, m.Pos + dir * 8f, 0.8f, "dash")); }
                    }
                    break;
                case 1:   // 突進の予告（0.8秒）：向きを、つねにプレイヤーへ
                    m.Aux -= dt; m.Heading = (float)Math.Atan2(dir.Y, dir.X);
                    if (m.Aux <= 0f) { m.State = 2; m.Aux = 0.6f; }
                    break;
                case 2:   // 突進（速さ8・0.6秒）
                    m.Pos = m.Pos + FromAngle(m.Heading) * (8f * dt); m.Aux -= dt;
                    if (m.Aux <= 0f) { m.State = 0; m.Aux = 0f; }
                    break;
                case 3:   // 弾の輪（12発・弾速4・ダメージ8）の予告→発射
                    m.Aux -= dt;
                    if (m.Aux <= 0f) { for (int i = 0; i < 12; i++) AddShot(m.Pos, FromAngle(i * Math.PI * 2.0 / 12.0), 4f, 8f); m.State = 0; m.Aux = 0f; }
                    break;
            }
        }
    }
}
