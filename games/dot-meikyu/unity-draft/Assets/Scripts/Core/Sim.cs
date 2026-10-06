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
        public readonly RunCards Cards = new RunCards();                     // いまの挑戦で、持っているカード
        public WeaponItem Weapon;                                            // 持ちこんだ武器（1本）
        public Modifiers Mods = new Modifiers();                             // カード・宝石・魔法使いから決まる強さ
        public float Time, Souls, DangerHpMul = 1f, DangerAtkMul = 1f, StageAtkMul = 1f, Luck = 1f;
        public int Kills, Level = 1, PendingLevelUps; public float Xp;     // 経験値とレベル（design/run.csv）
        public bool BossAlive, Charging;                                     // Charging：ため中（ためこみカードで、受けるダメージが減る）
        readonly Dictionary<string, EnemyDef> defs = new Dictionary<string, EnemyDef>();
        readonly DataTables data;
        float attackCd, healBudget, healRefill;

        public Sim(DataTables tables, WeaponItem weapon, int seed)
        {
            Rng = new Random(seed); Weapon = weapon; data = tables;
            foreach (var e in data.Enemies) defs[e.Id] = e;
            // 小さなスライム王（分裂のあと）は、表にないので、ここで作る
            if (defs.ContainsKey("FB")) { var k = defs["FB"]; defs["FB_MINI"] = new EnemyDef { Id = "FB_MINI", Name = "小さなスライム王", Region = k.Region, Role = "強敵", Hp = 400f, Speed = 1.2f, Contact = 15f, Soul = 5f, Memo = "分裂した王" }; }
            Pet.Pos = new Vec2(-1f, 0f);
            Recompute(); healBudget = Player.MaxHp * 0.02f;
        }

        public void attackCdForTest() { attackCd = 99f; }   // テスト用：自動攻撃が、ため攻撃のじゃまをしないように
        // Lv→Lv+1に必要な経験値：3＋2×Lv＋Lv×Lv÷4（切り捨て）。Lv1→2は5、2→3は8、3→4は11…
        public static int XpNeeded(int level) { return (int)Math.Floor(3.0 + 2.0 * level + level * level / 4.0); }
        public float XpInLevel { get { float acc = 0f; for (int l = 1; l < Level; l++) acc += XpNeeded(l); return Xp - acc; } }
        // レベルアップの待ち（カードを選ぶ回数）があれば、1つ減らして true
        public bool TakeLevelUp() { if (PendingLevelUps <= 0) return false; PendingLevelUps--; return true; }

        void AddXp(float amount)
        {
            if (Level >= 20) { Coins20 += amount / 10f; return; }       // Lv20より先は、経験値がコインにかわる（10ごとに1）
            Xp += amount;
            while (Level < 20) { float need = XpNeeded(Level), acc = 0f; for (int l = 1; l < Level; l++) acc += XpNeeded(l); if (Xp - acc < need) break; Level++; PendingLevelUps++; Events.Add(new SimEvent(EventKind.LevelUp, Player.Pos, Player.Pos, Level)); }
        }
        public float Coins20;
        public readonly GemBag Gems = new GemBag();                          // 宝石の持ち物（死んでも残る）
        public readonly List<string> GemsFoundThisRun = new List<string>();

        // 宝石を1つ落とす（最初の版の8種類から、ランダム）。すぐ持ち物に入る
        public void DropGem(Vec2 pos)
        {
            var pool = data.Gems.FindAll(x => x.FirstRelease); if (pool.Count == 0) return;
            var gd = pool[Rng.Next(pool.Count)]; Gems.Add(gd.Id); GemsFoundThisRun.Add(gd.Id);
            Events.Add(new SimEvent(EventKind.GemDrop, pos, pos, 1f, gd.Id));
        }

        public bool HasDef(string id) { return defs.ContainsKey(id); }

        // ---- 挑戦のはじめと、カードをとったとき ----
        public void StartRun(string job)
        {
            Cards.Job = job; Cards.Levels[ModifierBuilder.StartSkill(job)] = 1;      // 魔法使いごとの、最初から持つスキル
            Recompute();
        }

        public void ApplyCard(CardDef c)
        {
            if (c.Id == "U14") { Player.Hp = Math.Min(Player.MaxHp, Player.Hp + Player.MaxHp * 0.4f); Recompute(); return; }   // 薬びん：すぐ回復
            Cards.Levels[c.Id] = Cards.Level(c.Id) + 1;
            Cards.EvolutionReady.Clear();                                                      // 進化の条件（初版は2つだけ）
            if (Cards.Level("SK_C1") >= 5 && Cards.Level("CH1") >= 1) Cards.EvolutionReady.Add("EV1");
            if (Cards.Level("SK_R1") >= 5 && Cards.Level("U02") >= 1) Cards.EvolutionReady.Add("EV2");
            Recompute();
        }

        // カード・宝石・魔法使いの合計から、強さをつくり直す
        public void Recompute()
        {
            Mods = ModifierBuilder.Build(Cards, Weapon, data);
            Player.DamageMul = 1f + Mods.DamageBonus; Player.CritChance = 0.05f + Mods.CritChanceAdd; Player.CritMul = 1.5f + Mods.CritDmgAdd;
            float newMax = 100f + Mods.MaxHpAdd; if (newMax > Player.MaxHp) Player.Hp += newMax - Player.MaxHp; Player.MaxHp = newMax; if (Player.Hp > newMax) Player.Hp = newMax;
            Player.PickupRadius = 1.5f * (1f + Mods.PickupBonus); Luck = 1f + Mods.LuckBonus;
            SyncSkills();
        }

        public float AttackInterval { get { return Weapon.Interval * IntervalMul; } }   // 武器の間隔×カード・宝石の速さ
        float IntervalMul { get { return Math.Max(0.35f, 1f - Mods.AttackSpeedBonus); } }

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
            healRefill += dt; if (healRefill >= 1f) { healRefill = 0f; healBudget = Player.MaxHp * 0.02f; }   // 吸血は、毎秒、最大HPの2%まで
            int n = Mobs.Count;                                  // 動いている間に、敵が増える（分裂・召喚）ので、数えておく
            for (int i = 0; i < n; i++) if (Mobs[i].Alive) { StepStatus(Mobs[i], dt); if (Mobs[i].Alive) StepMob(Mobs[i], dt); }
            for (int i = 0; i < Mobs.Count; i++) if (Mobs[i].Alive) ContactDamage(Mobs[i], dt);
            StepShots(dt); StepClouds(dt);
            attackCd -= dt;
            if (attackCd <= 0f) attackCd = AutoAttack() ? Weapon.Interval * IntervalMul : 0.1f;
            StepSkills(dt); StepAllies(dt); StepPet(dt);
            if (Mods.PetRegen > 0f && Pet.Stun <= 0f && (Pet.Pos - Player.Pos).Length < 3f) Player.Hp = Math.Min(Player.MaxHp, Player.Hp + Mods.PetRegen * dt);   // ぷにぷに回復
            StepDrops(dt);
            Mobs.RemoveAll(m => !m.Alive); Shots.RemoveAll(s => !s.Alive); Clouds.RemoveAll(c => c.Life <= 0f);
        }

        // 燃える・毒・遅くなる
        void StepStatus(Mob m, float dt)
        {
            if (m.SlowLeft > 0f) m.SlowLeft -= dt;
            if (m.BurnLeft <= 0f && m.PoisonLeft <= 0f) return;
            m.BurnLeft -= dt; m.PoisonLeft -= dt; m.StatusTick += dt;
            if (m.StatusTick < 0.5f) return;
            m.StatusTick -= 0.5f;
            float dot = (m.BurnLeft > 0f ? m.BurnDps : 0f) + (m.PoisonLeft > 0f ? m.PoisonDps : 0f);
            if (dot > 0f) DamageMob(m, dot * 0.5f, m.Pos, false, 0f, false, true);
        }

        // ---- ダメージと倒れたとき ----
        public bool HurtPlayer(float dmg, Vec2 from, bool continuous = false)
        {
            if (Player.DashInvulnerable || !Player.Alive) return false;
            if (!continuous && Player.Invuln > 0f) return false;
            if (!continuous && Barrier)
            {   // 魔法障壁：攻撃を1回防ぐ（Lv5：割れるとき衝撃波）
                Barrier = false; barrierTimer = Math.Max(4f, 10f - 1.5f * (SkillLevel("SK_C6") - 1)); Player.Invuln = 0.3f;
                Events.Add(new SimEvent(EventKind.Cloud, Player.Pos, Player.Pos, 1f, "barrier_break"));
                if (SkillLevel("SK_C6") >= 5) AreaHit(Player.Pos, 2f, 20f, 1f);
                return false;
            }
            dmg *= Mods.DamageTakenMul * (Charging ? Mods.ChargingDamageTaken : 1f);
            Player.Hp = Math.Max(0f, Player.Hp - dmg);
            if (!continuous) Player.Invuln = 0.6f + Mods.InvulnAdd;
            Events.Add(new SimEvent(EventKind.PlayerHurt, Player.Pos, from, dmg));
            return true;
        }

        // fromAttack：ふつうの攻撃・ため攻撃（宝石やカードの「当たったとき」の効果がつく）／dot：燃える・毒（会心・効果なし）
        public void DamageMob(Mob m, float dmg, Vec2 from, bool canCrit = true, float knock = 0f, bool fromAttack = false, bool dot = false)
        {
            if (!m.Alive || m.SpawnDelay > 0f) return;
            bool crit = false;
            if (!dot)
            {
                if (canCrit && Rng.NextDouble() < Player.CritChance) { dmg *= Player.CritMul; crit = true; }
                dmg *= Player.DamageMul;
                if (Mods.FullHpAttackBonus > 0f && Player.Hp >= Player.MaxHp - 0.01f) dmg *= 1f + Mods.FullHpAttackBonus;       // 吸血5
                if (Mods.VsSlowedMul > 1f && (m.SlowLeft > 0f || m.Stun > 0f)) dmg *= Mods.VsSlowedMul;                          // 氷5
            }
            m.Hp -= dmg; Events.Add(new SimEvent(EventKind.Hit, m.Pos, from, dmg, crit ? "crit" : null) { Target = m });
            if (knock > 0f && !m.IsBossLike && !m.Anchored) { Vec2 d = (m.Pos - from).Normalized; m.Knock = m.Knock + d * (knock * 6f); }
            if (!dot && (fromAttack || crit)) Leech(dmg, crit);
            if (m.Hp <= 0f) { KillMob(m); return; }
            if (fromAttack) OnHit(m, dmg, crit, from);
        }

        // 吸血：与えたダメージの一部を回復（毎秒、最大HPの2%まで）
        void Leech(float dealt, bool crit)
        {
            float rate = Mods.Lifesteal + (crit ? Mods.CritVampPct : 0f); if (rate <= 0f) return;
            float heal = Math.Min(dealt * rate, healBudget); healBudget -= heal; Player.Hp = Math.Min(Player.MaxHp, Player.Hp + heal);
        }

        // 当たったときの効果：燃える・毒・遅くする・凍る・小さな連鎖・会心のつらぬき
        void OnHit(Mob m, float dmg, bool crit, Vec2 from)
        {
            if (Mods.BurnPct > 0f) { m.BurnDps = Math.Max(m.BurnDps, dmg * Mods.BurnPct * Mods.BurnMul * (Mods.EvFire ? 2f : 1f)); m.BurnLeft = Mods.BurnTime; }
            if (Mods.PoisonDps > 0f) { m.PoisonDps = Math.Max(m.PoisonDps, Mods.PoisonDps); m.PoisonLeft = Mods.PoisonTime; }
            if (Mods.PoisonPuddleChance > 0f && Rng.NextDouble() < Mods.PoisonPuddleChance) AddFriendlyCloud(m.Pos, 1f, 3f, dmg * 0.15f);
            if (Mods.SlowPct > 0f) { m.SlowPct = Math.Max(m.SlowPct, Mods.SlowPct); m.SlowLeft = 2f; if (Mods.FreezeChance > 0f && Rng.NextDouble() < Mods.FreezeChance) m.Stun = Math.Max(m.Stun, 1f); }
            if (Mods.ChainChance > 0f && Rng.NextDouble() < Mods.ChainChance) { var next = Nearest(m.Pos, 2.5f * (1f + Mods.AreaBonus), new HashSet<Mob> { m }); if (next != null) Chain(m.Pos, next, dmg * 0.5f, 1 + Mods.ChainJumpsAdd, 0.85f, 0f, false); }
            if (crit && Mods.CritPierce) foreach (var o in Mobs.ToArray()) if (o != m && o.Alive && (o.Pos - m.Pos).Length < 1.0f) DamageMob(o, dmg * 0.5f, m.Pos, false);
        }

        public void KillMob(Mob m)
        {
            if (!m.Alive) return;
            m.Alive = false; Kills++; AddXp(m.Def.Xp * (m.IsElite ? 5f : 1f)); Souls += m.Def.Soul * m.Soul * DangerHpMul * (m.LastHitByPet ? Mods.PetSoulMul : 1f);
            Events.Add(new SimEvent(EventKind.Kill, m.Pos, m.Pos, 0f, m.Def.Id));
            if (m.Held != null)
            {   // ひろい屋を倒した：武器がレア度+1で返る（100%）。幸運5なら、10%でレア度+2
                int up = Rng.NextDouble() < Mods.ReturnRarity2Chance ? 2 : 1;
                DropWeapon(m.Pos, WeaponItem.Create(m.Held.Kind, (Rarity)Math.Min(3, (int)m.Held.Rarity + up), Rng)); m.Held = null;
            }
            else if (m.Def.IsThief) { if (Rng.NextDouble() < 0.30) DropWeapon(m.Pos, WeaponItem.Random(Rng)); }
            else if (Rng.NextDouble() < m.Def.WeaponDrop * Luck) DropWeapon(m.Pos, WeaponItem.Random(Rng));
            float gem = m.IsElite ? 0.05f : m.Def.GemDrop;
            if (Rng.NextDouble() < gem * Luck) DropGem(m.Pos);
            if (m.Def.Id == "F04") Clouds.Add(new Cloud { Pos = m.Pos, Radius = 0.9f, Life = 2f, Damage = 3f * StageAtkMul * DangerAtkMul, Tick = 0.5f });
            if (Mods.BurnDeathExplosion && m.BurnLeft > 0f) AreaHit(m.Pos, 1f, 10f, 0.5f);                   // 炎5：燃えている敵が倒れると爆発
            if (Mods.PoisonDeathPuddle && m.PoisonLeft > 0f) AddFriendlyCloud(m.Pos, 1f, 3f, 4f);           // 毒5：毒だまり
            if (m.Def.Id == "FB")
            {
                BossAlive = false; Events.Add(new SimEvent(EventKind.BossDied, m.Pos, m.Pos, 0f));
                DropWeapon(m.Pos, WeaponItem.Random(Rng, 1)); DropGem(m.Pos);
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
                if (Mods.PetBlock > 0f && Pet.Stun <= 0f && (s.Pos - Pet.Pos).Length < 0.6f && Rng.NextDouble() < Mods.PetBlock * dt * 8f) { s.Alive = false; continue; }   // かばう：近くの弾を受け止める
                if ((s.Pos - Player.Pos).Length < Player.Radius + 0.15f) { HurtPlayer(s.Damage * StageAtkMul * DangerAtkMul, s.Pos); s.Alive = false; }
            }
        }

        void StepClouds(float dt)
        {
            foreach (var c in Clouds)
            {
                c.Life -= dt; c.Tick -= dt;
                if (c.Tick > 0f) continue;
                c.Tick = 0.5f;
                if (c.Friendly)
                {   // プレイヤーの毒の足あと・霧：敵に、少しずつダメージ
                    foreach (var m in Mobs.ToArray()) if (m.Alive && m.SpawnDelay <= 0f && (m.Pos - c.Pos).Length < c.Radius + m.Radius) { DamageMob(m, c.Damage, c.Pos, false, 0f, false, true); if (m.Alive && c.Slow > 0f) { m.SlowPct = Math.Max(m.SlowPct, c.Slow); m.SlowLeft = 1f; } }
                }
                else if ((c.Pos - Player.Pos).Length < c.Radius) HurtPlayer(c.Damage, c.Pos, true);
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
