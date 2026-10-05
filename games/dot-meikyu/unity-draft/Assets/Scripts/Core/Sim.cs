using System;
using System.Collections.Generic;

namespace DotMeikyu.Core
{
    // 戦闘の「世界」。Unityに依存しない。Unity側は、ここの位置や知らせ（Events）を見て、絵や光を出すだけ
    // 座標は、地面の平面（x と z）を、Vec2 の X と Y で表す
    public sealed partial class Sim
    {
        public readonly Random Rng;
        public readonly Player Player = new Player();
        public readonly PetState Pet = new PetState();
        public readonly List<Mob> Mobs = new List<Mob>();
        public readonly List<DroppedWeapon> Drops = new List<DroppedWeapon>();
        public readonly List<Shot> Shots = new List<Shot>();
        public readonly List<Cloud> Clouds = new List<Cloud>();
        public readonly List<WeaponItem> Storage = new List<WeaponItem>();   // 拾った武器は、死んでも残る（倉庫）
        public readonly List<SimEvent> Events = new List<SimEvent>();        // 1回の Tick ぶんの知らせ（毎回、空にする）
        public WeaponItem Weapon;                                            // 持ちこんだ武器（1本）
        public float Time, Souls, DangerHpMul = 1f, DangerAtkMul = 1f, StageAtkMul = 1f, Luck = 1f;
        public int Kills;
        public bool BossAlive;
        readonly Dictionary<string, EnemyDef> defs = new Dictionary<string, EnemyDef>();
        float attackCd;

        public Sim(DataTables data, WeaponItem weapon, int seed)
        {
            Rng = new Random(seed); Weapon = weapon;
            foreach (var e in data.Enemies) defs[e.Id] = e;
            // 小さなスライム王（分裂のあと）は、表にないので、ここで作る
            if (defs.ContainsKey("FB")) { var k = defs["FB"]; defs["FB_MINI"] = new EnemyDef { Id = "FB_MINI", Name = "小さなスライム王", Region = k.Region, Role = "強敵", Hp = 400f, Speed = 1.2f, Contact = 15f, Soul = 5f, Memo = "分裂した王" }; }
            Pet.Pos = new Vec2(-1f, 0f);
        }

        public void attackCdForTest() { attackCd = 99f; }   // テスト用：自動攻撃が、ため攻撃のじゃまをしないように
        public bool HasDef(string id) { return defs.ContainsKey(id); }

        public Mob Spawn(string id, Vec2 pos, float hpMul = 1f, bool elite = false)
        {
            EnemyDef d = defs[id];
            var m = new Mob { Def = d, Pos = pos, IsElite = elite };
            m.MaxHp = m.Hp = d.Hp * hpMul * DangerHpMul * (elite ? 6f : 1f);
            m.Radius = id == "FB" ? 1.2f : id == "FB_MINI" ? 0.8f : (elite ? 0.6f : 0.4f);
            m.Soul = elite ? 5f : 1f;
            if (id == "FB") BossAlive = true;
            Mobs.Add(m); Events.Add(new SimEvent(EventKind.Spawned, pos, pos, 0f, id));
            return m;
        }

        public int AliveCount(string id = null) { int n = 0; foreach (var m in Mobs) if (m.Alive && (id == null || m.Def.Id == id)) n++; return n; }

        public void Tick(float dt)
        {
            Events.Clear(); Time += dt;
            if (Player.Invuln > 0f) Player.Invuln -= dt;
            if (!Player.Alive) return;
            int n = Mobs.Count;                                  // 動いている間に、敵が増える（分裂・召喚）ので、数えておく
            for (int i = 0; i < n; i++) if (Mobs[i].Alive) StepMob(Mobs[i], dt);
            for (int i = 0; i < Mobs.Count; i++) if (Mobs[i].Alive) ContactDamage(Mobs[i], dt);
            StepShots(dt); StepClouds(dt);
            attackCd -= dt;
            if (attackCd <= 0f) attackCd = AutoAttack() ? Weapon.Interval : 0.1f;
            StepPet(dt);
            StepDrops(dt);
            Mobs.RemoveAll(m => !m.Alive); Shots.RemoveAll(s => !s.Alive); Clouds.RemoveAll(c => c.Life <= 0f);
        }

        // ---- ダメージと倒れたとき ----
        public bool HurtPlayer(float dmg, Vec2 from, bool continuous = false)
        {
            if (Player.DashInvulnerable || !Player.Alive) return false;
            if (!continuous && Player.Invuln > 0f) return false;
            Player.Hp = Math.Max(0f, Player.Hp - dmg);
            if (!continuous) Player.Invuln = 0.6f;
            Events.Add(new SimEvent(EventKind.PlayerHurt, Player.Pos, from, dmg));
            return true;
        }

        public void DamageMob(Mob m, float dmg, Vec2 from, bool canCrit = true, float knock = 0f)
        {
            if (!m.Alive || m.SpawnDelay > 0f) return;
            if (canCrit && Rng.NextDouble() < Player.CritChance) dmg *= 1.5f;
            dmg *= Player.DamageMul;
            m.Hp -= dmg; Events.Add(new SimEvent(EventKind.Hit, m.Pos, from, dmg));
            if (knock > 0f && !m.IsBossLike) { Vec2 d = (m.Pos - from).Normalized; m.Knock = m.Knock + d * (knock * 6f); }
            if (m.Hp <= 0f) KillMob(m);
        }

        public void KillMob(Mob m)
        {
            if (!m.Alive) return;
            m.Alive = false; Kills++; Souls += m.Def.Soul * m.Soul * DangerHpMul;
            Events.Add(new SimEvent(EventKind.Kill, m.Pos, m.Pos, 0f, m.Def.Id));
            if (m.Held != null)
            {   // ひろい屋を倒した：武器がレア度+1で返る（100%）
                var up = WeaponItem.Create(m.Held.Kind, (Rarity)Math.Min(3, (int)m.Held.Rarity + 1), Rng);
                DropWeapon(m.Pos, up); m.Held = null;
            }
            else if (m.Def.IsThief) { if (Rng.NextDouble() < 0.30) DropWeapon(m.Pos, WeaponItem.Random(Rng)); }
            else if (Rng.NextDouble() < m.Def.WeaponDrop * Luck) DropWeapon(m.Pos, WeaponItem.Random(Rng));
            float gem = m.IsElite ? 0.05f : m.Def.GemDrop;
            if (Rng.NextDouble() < gem * Luck) Events.Add(new SimEvent(EventKind.GemDrop, m.Pos, m.Pos, 1f));
            if (m.Def.Id == "F04") Clouds.Add(new Cloud { Pos = m.Pos, Radius = 0.9f, Life = 2f, Damage = 3f * StageAtkMul * DangerAtkMul, Tick = 0.5f });
            if (m.Def.Id == "FB")
            {
                BossAlive = false; Events.Add(new SimEvent(EventKind.BossDied, m.Pos, m.Pos, 0f));
                DropWeapon(m.Pos, WeaponItem.Random(Rng, 1)); Events.Add(new SimEvent(EventKind.GemDrop, m.Pos, m.Pos, 1f));
                foreach (var o in Mobs) if (o.Alive && o != m && (o.Def.Id == "FB_MINI")) KillMob(o);
            }
        }

        public DroppedWeapon DropWeapon(Vec2 pos, WeaponItem item)
        {
            var d = new DroppedWeapon { Pos = pos, Item = item }; Drops.Add(d);
            Events.Add(new SimEvent(EventKind.DropWeapon, pos, pos, (float)item.Rarity, item.Kind.ToString())); return d;
        }

        // 落ちた武器を取る。先に着いたほうが取る（取られたものは、ほかの人は取れない）
        public bool TryTake(DroppedWeapon d, string who)
        {
            if (d.Taken) return false;
            d.Taken = true;
            if (who == "player") { Storage.Add(d.Item); Events.Add(new SimEvent(EventKind.WeaponStored, d.Pos, d.Pos, (float)d.Item.Rarity, "player")); }
            return true;
        }

        void StepDrops(float dt)
        {
            foreach (var d in Drops) { d.Age += dt; if (!d.Taken && (d.Pos - Player.Pos).Length <= Player.PickupRadius) TryTake(d, "player"); }
            Drops.RemoveAll(d => d.Taken);
        }

        void ContactDamage(Mob m, float dt)
        {
            if (m.SpawnDelay > 0f) return;
            if (m.ContactCd > 0f) m.ContactCd -= dt;
            if (m.ContactCd > 0f) return;
            float dmg = m.ContactDamage() * m.DamageMul * StageAtkMul * DangerAtkMul;
            if ((m.Pos - Player.Pos).Length < m.Radius + Player.Radius) { if (HurtPlayer(dmg, m.Pos)) m.ContactCd = 0.5f; }
            else if ((m.Pos - Pet.Pos).Length < m.Radius + Pet.Radius && Pet.Stun <= 0f) { HurtPet(dmg * 0.5f); m.ContactCd = 0.5f; }
        }

        void StepShots(float dt)
        {
            foreach (var s in Shots)
            {
                s.Pos = s.Pos + s.Vel * dt; s.Life -= dt; if (s.Life <= 0f) { s.Alive = false; continue; }
                if ((s.Pos - Player.Pos).Length < Player.Radius + 0.15f) { HurtPlayer(s.Damage * StageAtkMul * DangerAtkMul, s.Pos); s.Alive = false; }
            }
        }

        void StepClouds(float dt)
        {
            foreach (var c in Clouds)
            {
                c.Life -= dt; c.Tick -= dt;
                if (c.Tick <= 0f) { c.Tick = 0.5f; if ((c.Pos - Player.Pos).Length < c.Radius) HurtPlayer(c.Damage, c.Pos, true); }
            }
        }

        public void AddShot(Vec2 pos, Vec2 dir, float speed, float dmg) { Shots.Add(new Shot { Pos = pos, Vel = dir.Normalized * speed, Damage = dmg }); Events.Add(new SimEvent(EventKind.ShotFired, pos, pos + dir.Normalized, speed)); }
        public void AddCloud(Vec2 pos, float radius, float life, float dmg) { Clouds.Add(new Cloud { Pos = pos, Radius = radius, Life = life, Damage = dmg * StageAtkMul * DangerAtkMul, Tick = 0.5f }); Events.Add(new SimEvent(EventKind.Cloud, pos, pos, radius)); }

        public Mob Nearest(Vec2 from, float maxDist, HashSet<Mob> exclude = null)
        {
            Mob best = null; float bd = maxDist;
            foreach (var m in Mobs)
            {
                if (!m.Alive || m.SpawnDelay > 0f || (exclude != null && exclude.Contains(m))) continue;
                float d = (m.Pos - from).Length - m.Radius; if (d < bd) { bd = d; best = m; }
            }
            return best;
        }
    }
}
