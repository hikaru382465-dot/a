using System;
using System.Collections.Generic;

namespace DotMeikyu.Core
{
    public sealed class SkillState { public string Id; public int Level; public float Timer; public float Aux; }

    // スキルカード24個のうち、魔法の自動攻撃と、召喚した味方（design/cards.csv の「効果」のとおり）
    public sealed partial class Sim
    {
        public readonly List<SkillState> Skills = new List<SkillState>();
        public readonly List<Ally> Allies = new List<Ally>();
        public bool Barrier;                                 // 魔法障壁：攻撃を1回防ぐ
        float barrierTimer;
        sealed class Pending { public float T; public Action Do; }
        readonly List<Pending> pending = new List<Pending>();

        static float Sc(int lv, float per) { return 1f + per * (lv - 1); }

        void SyncSkills()
        {
            foreach (var kv in Cards.Levels)
            {
                if (!kv.Key.StartsWith("SK_") || kv.Value <= 0) continue;
                SkillState s = Skills.Find(x => x.Id == kv.Key);
                if (s == null) { s = new SkillState { Id = kv.Key, Timer = 0.5f }; Skills.Add(s); if (kv.Key == "SK_C6") { Barrier = true; } }
                s.Level = kv.Value;
            }
            SyncAllies();
        }

        int SkillLevel(string id) { return Cards.Level(id); }

        void SyncAllies()
        {
            Want(AllyType.Knight, SkillLevel("SK_M1") <= 0 ? 0 : (SkillLevel("SK_M1") >= 5 ? 2 : 1));
            Want(AllyType.Archer, SkillLevel("SK_M2") <= 0 ? 0 : 1 + (SkillLevel("SK_M2") >= 3 ? 1 : 0) + (SkillLevel("SK_M2") >= 5 ? 1 : 0));
            Want(AllyType.Golem, SkillLevel("SK_M4") <= 0 ? 0 : 1);
            Want(AllyType.SlimeClone, SkillLevel("SK_M6") <= 0 ? 0 : 3 + (SkillLevel("SK_M6") - 1));
        }

        void Want(AllyType t, int n)
        {
            int have = 0; foreach (var a in Allies) if (a.Type == t) have++;
            for (; have < n; have++) Allies.Add(new Ally { Type = t, Pos = Player.Pos, Slot = have, Hp = 60f * (1f + Mods.AllyHpBonus) });
            for (int i = Allies.Count - 1; i >= 0 && have > n; i--) if (Allies[i].Type == t) { Allies.RemoveAt(i); have--; }
        }

        List<Mob> NearestN(Vec2 from, int n, float maxDist)
        {
            var list = new List<Mob>();
            foreach (var m in Mobs) if (m.Alive && m.SpawnDelay <= 0f && (m.Pos - from).Length - m.Radius < maxDist) list.Add(m);
            list.Sort((a, b) => (a.Pos - from).Length.CompareTo((b.Pos - from).Length));
            if (list.Count > n) list.RemoveRange(n, list.Count - n);
            return list;
        }

        // 敵がいちばん集まっている場所の敵（火柱・隕石・毒の霧のねらい）
        Mob Densest(float radius, float maxFromPlayer)
        {
            Mob best = null; int bn = -1;
            foreach (var a in Mobs)
            {
                if (!a.Alive || a.SpawnDelay > 0f || (a.Pos - Player.Pos).Length > maxFromPlayer) continue;
                int n = 0; foreach (var b in Mobs) if (b.Alive && (b.Pos - a.Pos).Length < radius) n++;
                if (n > bn) { bn = n; best = a; }
            }
            return best;
        }

        void AreaHit(Vec2 center, float radius, float dmg, float knock, bool burn = false, float slow = 0f, float freeze = 0f)
        {
            Events.Add(new SimEvent(EventKind.Slash, center, center, radius, "area"));
            foreach (var m in Mobs.ToArray())
            {
                if (!m.Alive || m.SpawnDelay > 0f || (m.Pos - center).Length > radius + m.Radius) continue;
                DamageMob(m, dmg, center, true, knock);
                if (!m.Alive) continue;
                if (burn) { m.BurnDps = Math.Max(m.BurnDps, dmg * 0.15f * Mods.BurnMul * (Mods.EvFire ? 2f : 1f)); m.BurnLeft = Mods.BurnTime; }
                if (slow > 0f) { m.SlowPct = Math.Max(m.SlowPct, slow); m.SlowLeft = Math.Max(m.SlowLeft, 1.5f); }
                if (freeze > 0f) m.Stun = Math.Max(m.Stun, freeze);
            }
        }

        void AddFriendlyCloud(Vec2 pos, float radius, float life, float dps, float slow = 0f)
        {
            Clouds.Add(new Cloud { Pos = pos, Radius = radius, Life = life, Damage = dps * 0.5f, Tick = 0.5f, Friendly = true, Slow = slow });
            Events.Add(new SimEvent(EventKind.Cloud, pos, pos, radius, "friendly"));
        }

        void StepSkills(float dt)
        {
            for (int i = pending.Count - 1; i >= 0; i--) { pending[i].T -= dt; if (pending[i].T <= 0f) { var p = pending[i]; pending.RemoveAt(i); p.Do(); } }
            foreach (var s in Skills.ToArray())
            {
                s.Timer -= dt;
                if (s.Timer > 0f) continue;
                float iv = FireSkill(s);
                bool bullet = s.Id.StartsWith("SK_R") || s.Id == "SK_C2";
                s.Timer = iv * Mods.SkillIntervalMul * (bullet ? Mods.BulletIntervalMul : 1f);
            }
            if (SkillLevel("SK_C6") > 0 && !Barrier) { barrierTimer -= dt; if (barrierTimer <= 0f) { Barrier = true; Events.Add(new SimEvent(EventKind.Cloud, Player.Pos, Player.Pos, 1f, "barrier")); } }
        }

        // スキルを1回うつ。次までの秒数を返す（design/cards.csv）
        float FireSkill(SkillState s)
        {
            int lv = s.Level; Vec2 p = Player.Pos; float am = 1f + Mods.AreaBonus;
            switch (s.Id)
            {
                case "SK_C1":   // 炎の輪：火の玉がまわる。0.5秒ごとにダメ6。Lv3・Lv5で玉+1。進化（太陽の輪）で玉6個・燃やすダメージ2倍
                    { int balls = (2 + (lv >= 3 ? 1 : 0) + (lv >= 5 ? 1 : 0)) * (Mods.EvFire ? 3 : 1); AreaHit(p, 1.8f * am, 6f * Sc(lv, 0.2f) * balls / 2f, 0f, true); return 0.5f; }
                case "SK_C2":   // 魔力の短剣：0.7秒ごとにダメ7。Lv2・Lv4で本数+1
                    { int n = 1 + (lv >= 2 ? 1 : 0) + (lv >= 4 ? 1 : 0); foreach (var m in NearestN(p, n, 8f * am)) { DamageMob(m, 7f, p, true, 0.2f); Events.Add(new SimEvent(EventKind.Arrow, p, m.Pos, 1f)); } return 0.7f * (lv >= 2 ? 0.9f : 1f) * (lv >= 4 ? 0.9f : 1f); }
                case "SK_C3":   // 氷の結晶：3秒ごとに近くの敵3体を1秒凍らせる（ダメ5）
                    { foreach (var m in NearestN(p, 2 + lv, 8f * am)) { DamageMob(m, 5f, p, true); if (m.Alive) m.Stun = Math.Max(m.Stun, 1f + 0.2f * (lv - 1)); } return 3f; }
                case "SK_C4":   // 瘴気の足あと：歩いたあとに毒だまり（3秒・毎秒4）
                    { AddFriendlyCloud(p, 0.8f, 3f + 0.5f * (lv - 1), 4f * Sc(lv, 0.25f)); return 0.5f; }
                case "SK_C5":   // 雷の柱：4秒ごとに画面内のどこかへ3本（ダメ15・半径1）
                    { int n = 2 + lv; for (int i = 0; i < n; i++) { Vec2 at = p + new Vec2((float)(Rng.NextDouble() * 12 - 6), (float)(Rng.NextDouble() * 12 - 6)); Events.Add(new SimEvent(EventKind.Chain, at + new Vec2(0f, 6f), at, 15f, "pillar")); AreaHit(at, 1f * am, 15f * Sc(lv, 0.15f), 0f); } return 4f; }
                case "SK_C6":   // 魔法障壁：10秒ごとに攻撃を1回防ぐ（Lv5：割れるとき衝撃波）
                    return 99f;
                case "SK_R1":   // 魔力の矢：一番近い敵へ0.6秒ごと（ダメ6）。Lv3・Lv5で+1本。進化（星くずの雨）で+4本・間隔短く
                    { int n = 1 + (lv >= 3 ? 1 : 0) + (lv >= 5 ? 1 : 0) + (Mods.EvStar ? 4 : 0); foreach (var m in NearestN(p, n, 9f * am)) { DamageMob(m, 6f * Sc(lv, 0.15f), p, true, 0.2f); Events.Add(new SimEvent(EventKind.Arrow, p, m.Pos, 1f)); } return 0.6f * (Mods.EvStar ? 0.6f : 1f); }
                case "SK_R2":   // 三連星：3方向へ星の弾を1.2秒ごと（ダメ7）。レベルごとに方向+1
                    { Mob t = Nearest(p, 9f * am); if (t != null) { double b = Math.Atan2(t.Pos.Y - p.Y, t.Pos.X - p.X); int n = 2 + lv; for (int i = 0; i < n; i++) { double a = b + (i - (n - 1) / 2.0) * 0.28; ShootLine(p, FromAngle(a), 8f * am, 7f * Sc(lv, 0.1f), 1, false); } } return 1.2f; }
                case "SK_R3":   // 跳ねる火花：敵で2回はねる（ダメ6＋燃やす）。レベルごとにはねる回数+1
                    { Mob t = Nearest(p, 8f * am); if (t != null) { Chain(p, t, 6f, 1 + lv, 1f, 0f, false); } return 1.0f; }
                case "SK_R4":   // 追尾の光珠：追いかける光3つを2秒ごと（ダメ8・会心+10%）。レベルごとに数+1
                    { float c0 = Player.CritChance; Player.CritChance += 0.10f; foreach (var m in NearestN(p, 2 + lv, 9f * am)) { DamageMob(m, 8f, p, true); Events.Add(new SimEvent(EventKind.Arrow, p, m.Pos, 1f)); } Player.CritChance = c0; return 2f; }
                case "SK_R5":   // 氷の針：つらぬく針を前へ5本・1.5秒ごと（ダメ5・遅くする）。レベルごとに本数+2
                    { Mob t = Nearest(p, 9f * am); if (t != null) { double b = Math.Atan2(t.Pos.Y - p.Y, t.Pos.X - p.X); int n = 3 + 2 * lv; for (int i = 0; i < n; i++) { double a = b + (i - (n - 1) / 2.0) * 0.12; ShootLine(p, FromAngle(a), 7f * am, 5f, 99, true); } foreach (var m in NearestN(p, 99, 7f * am)) { m.SlowPct = Math.Max(m.SlowPct, 0.3f); m.SlowLeft = 1.5f; } } return 1.5f; }
                case "SK_R6":   // 雷の連弾：当たると2体に連鎖する弾を0.9秒ごと（ダメ6）。レベルごとに連鎖+1
                    { Mob t = Nearest(p, 8f * am); if (t != null) Chain(p, t, 6f, 1 + lv, 1f, 0f, false); return 0.9f; }
                case "SK_A1":   // 火柱：敵が多い場所に3秒ごと（半径1.5・ダメ18）。レベルごとにダメ+20%・半径+10%
                    { Mob d = Densest(1.5f, 10f); if (d != null) AreaHit(d.Pos, 1.5f * Sc(lv, 0.1f) * am, 18f * Sc(lv, 0.2f), 0f, true); return 3f; }
                case "SK_A2":   // 吹雪：自分のまわり半径2.5に毎秒ダメ4＋遅くする
                    { AreaHit(p, (2.5f + 0.3f * (lv - 1)) * am, 4f + (lv - 1), 0f, false, 0.20f); return 1f; }
                case "SK_A3":   // 隕石：8秒ごとに大爆発（半径3・ダメ40）。落ちる前に、光の円で予告
                    { Mob d = Densest(3f, 10f); if (d != null) { Vec2 at = d.Pos; Events.Add(new SimEvent(EventKind.Telegraph, at, at, 1f, "meteor")); float dmg = 40f * Sc(lv, 0.2f), r = 3f * am; pending.Add(new Pending { T = 1f, Do = () => AreaHit(at, r, dmg, 1f) }); } return Math.Max(4f, 8f - (lv - 1)); }
                case "SK_A4":   // 大地の衝撃：5秒ごとに自分を中心に衝撃波（半径3・ダメ10・押し返す）
                    { AreaHit(p, 3f * am, 10f * Sc(lv, 0.3f), 2f); return 5f; }
                case "SK_A5":   // 瘴気の霧：6秒ごとに敵の群れへ大きな毒雲（半径2.5・6秒・毎秒5）
                    { Mob d = Densest(2.5f, 10f); if (d != null) AddFriendlyCloud(d.Pos, (2.5f + 0.3f * (lv - 1)) * am, 6f, 5f + (lv - 1)); return 6f; }
                case "SK_A6":   // 雷雲：頭の上の雲が1秒ごとに近くの敵へ雷（ダメ9）。Lv3・Lv5で同時に落ちる数+1
                    { int n = 1 + (lv >= 3 ? 1 : 0) + (lv >= 5 ? 1 : 0); foreach (var m in NearestN(p, n, 8f * am)) { Events.Add(new SimEvent(EventKind.Chain, m.Pos + new Vec2(0f, 3f), m.Pos, 9f, "cloud")); DamageMob(m, 9f * Sc(lv, 0.15f), p, true); } return 1f; }
                case "SK_A7":   // 雷球：5秒ごとに雷の球を敵の群れへ。着地で小爆発（ダメ12）→ 近くの3体へ一斉に雷 → そこから連鎖
                    { Mob d = Densest(3f, 9f); if (d == null) return 1f;
                      Vec2 land = d.Pos; Events.Add(new SimEvent(EventKind.Chain, p, land, 0f, "orb")); AreaHit(land, 1.2f * am, 12f * Sc(lv, 0.15f), 0f);
                      foreach (var m in NearestN(land, 3, 5f * am)) Chain(land, m, 8f * Sc(lv, 0.15f), 1 + lv, 0.9f, 0f, false);
                      return 5f; }
                case "SK_M7":   // 幻影の狼：8秒ごとに狼を呼ぶ（2匹・Lv3とLv5で+1・6秒だけ）
                    { int n = 2 + (lv >= 3 ? 1 : 0) + (lv >= 5 ? 1 : 0); int have = 0; foreach (var a in Allies) if (a.Type == AllyType.Wolf) have++;
                      for (int k = 0; k < n; k++) Allies.Add(new Ally { Type = AllyType.Wolf, Pos = Player.Pos + FromAngle(k * 2.4 + Time) * 0.8f, Slot = have + k, Life = 6f });
                      Events.Add(new SimEvent(EventKind.Slash, Player.Pos, Player.Pos, 1.5f, "wolf_summon")); return 8f; }
                case "SK_M3":   // 火の精霊：4秒ごとに精霊が敵へ飛んで爆発（半径1.2・ダメ20）。レベルごとに数+1
                    { foreach (var m in NearestN(p, lv, 9f * am)) AreaHit(m.Pos, 1.2f * am, 20f * (1f + Mods.AllyAtkBonus), 0f, true); return 4f; }
                case "SK_M5":   // 雷の精霊鳥：飛びまわって2秒ごとに雷（連鎖3・ダメ8）。レベルごとに連鎖+1・ダメ+15%
                    { Mob t = Nearest(p, 9f * am); if (t != null) Chain(p, t, 8f * Sc(lv, 0.15f) * (1f + Mods.AllyAtkBonus), 2 + lv, 1f, 0f, false); return 2f; }
                default: return 99f;   // 味方（M1・M2・M4・M6）は、StepAllies が動かす
            }
        }

        // 味方：プレイヤーのまわりにいて、近くの敵をたおす（今は、味方はダメージを受けない）
        void StepAllies(float dt)
        {
            foreach (var a in Allies)
            {
                Vec2 home = Player.Pos + FromAngle(a.Slot * 2.1 + a.Type.GetHashCode() * 0.7) * 1.6f;
                a.AttackCd -= dt; float mul = 1f + Mods.AllyAtkBonus;
                switch (a.Type)
                {
                    case AllyType.Knight:
                        {   // 剣の騎士：近くの敵へ走って切る（1秒ごとにダメ8、レベルごとに+20%）
                            Mob t = Nearest(Player.Pos, 6f); Vec2 goal = t != null ? t.Pos : home;
                            a.Pos = a.Pos + (goal - a.Pos).Normalized * (3.2f * dt);
                            if (t != null && a.AttackCd <= 0f && (t.Pos - a.Pos).Length < 1.2f + t.Radius) { DamageMob(t, 8f * Sc(SkillLevel("SK_M1"), 0.2f) * mul, a.Pos, true, 0.3f); Events.Add(new SimEvent(EventKind.Slash, a.Pos, a.Pos, 0.8f, "ally")); a.AttackCd = 1f; }
                            break;
                        }
                    case AllyType.Archer:
                        {   // 射手：プレイヤーのそばから、0.8秒ごとに矢（ダメ6・射程6）
                            a.Pos = a.Pos + (home - a.Pos).Normalized * (Math.Min(3f, (home - a.Pos).Length * 3f) * dt);
                            Mob t = Nearest(a.Pos, 6f); if (t != null && a.AttackCd <= 0f) { DamageMob(t, 6f * mul, a.Pos, true, 0.1f); Events.Add(new SimEvent(EventKind.Arrow, a.Pos, t.Pos, 1f)); a.AttackCd = 0.8f; }
                            break;
                        }
                    case AllyType.Golem:
                        {   // 氷霊の守護像：まわりを遅くする（Lv5で凍らせる）
                            a.Pos = a.Pos + (home - a.Pos).Normalized * (Math.Min(2f, (home - a.Pos).Length * 3f) * dt);
                            if (a.AttackCd <= 0f) { foreach (var m in Mobs) if (m.Alive && (m.Pos - a.Pos).Length < 2.2f) { m.SlowPct = Math.Max(m.SlowPct, 0.3f); m.SlowLeft = 1.5f; if (SkillLevel("SK_M4") >= 5) m.Stun = Math.Max(m.Stun, 0.5f); } a.AttackCd = 1f; }
                            break;
                        }
                    case AllyType.Wolf:
                        {   // 幻影の狼：いちばん近い敵へ猛ダッシュして、噛む（0.45秒ごとにダメ7）。6秒で消える
                            a.Life -= dt; Mob t = Nearest(a.Pos, 9f); Vec2 goal = t != null ? t.Pos : home;
                            a.Pos = a.Pos + (goal - a.Pos).Normalized * (6.5f * dt);
                            if (t != null && a.AttackCd <= 0f && (t.Pos - a.Pos).Length < 0.9f + t.Radius) { DamageMob(t, 7f * Sc(SkillLevel("SK_M7"), 0.15f) * mul, a.Pos, true, 0.2f); Events.Add(new SimEvent(EventKind.Slash, a.Pos, t.Pos, 0.6f, "wolf")); a.AttackCd = 0.45f; }
                            break;
                        }
                    default:
                        {   // スライム分身：敵へ体当たり（ダメ4・1.2秒ごと）
                            Mob t = Nearest(Pet.Pos, 5f); Vec2 goal = t != null ? t.Pos : (Pet.Pos + FromAngle(a.Slot * 2.1) * 1.0f);
                            a.Pos = a.Pos + (goal - a.Pos).Normalized * (3f * dt);
                            if (t != null && a.AttackCd <= 0f && (t.Pos - a.Pos).Length < 0.8f + t.Radius) { DamageMob(t, 4f * mul, a.Pos, false, 0.2f); a.AttackCd = 1.2f; }
                            break;
                        }
                }
            }
            Allies.RemoveAll(x => x.Life == -1f ? false : x.Life <= 0f);   // 時間がきた味方（狼）は消える
        }
    }
}
