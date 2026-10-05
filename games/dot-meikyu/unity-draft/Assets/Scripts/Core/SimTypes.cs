using System;
using System.Collections.Generic;

namespace DotMeikyu.Core
{
    public enum EventKind { Hit, Chain, Slash, Arrow, Kill, PlayerHurt, PetHurt, DropWeapon, WeaponTaken, WeaponStored, WeaponLost, PetAte, PetStunned, PetWoke, Telegraph, ShotFired, Cloud, ExitsOpened, GemDrop, BossDied, Spawned }

    // 見た目（光・音・ダメージの数字）のための知らせ。Unity側が受け取って、エフェクトを出す
    public struct SimEvent
    {
        public EventKind Kind; public Vec2 Pos, Pos2; public float Value; public string Tag;
        public SimEvent(EventKind k, Vec2 p, Vec2 p2, float v, string tag = null) { Kind = k; Pos = p; Pos2 = p2; Value = v; Tag = tag; }
    }

    public sealed class DroppedWeapon { public Vec2 Pos; public WeaponItem Item; public bool Taken; public float Age; }
    public sealed class Shot { public Vec2 Pos, Vel; public float Damage, Life = 6f; public bool Alive = true; }
    public sealed class Cloud { public Vec2 Pos; public float Radius, Life, Damage, Tick; }

    public sealed class Player
    {
        public Vec2 Pos; public float Hp = 100f, MaxHp = 100f, Radius = 0.3f, Invuln, DamageMul = 1f, CritChance = 0.05f, PickupRadius = 1.5f;
        public bool DashInvulnerable;       // ダッシュ中の無敵（PlayerControllerが入れる）
        public bool Alive { get { return Hp > 0f; } }
    }

    // 敵1体（定義＋いまの状態）
    public sealed class Mob
    {
        public EnemyDef Def; public Vec2 Pos; public float Hp, MaxHp, Radius = 0.4f, DamageMul = 1f, Soul = 1f;
        public bool Alive = true, IsElite; public float T, ContactCd, SpawnDelay = 0.4f, Stun, Heading;
        public int State; public float Aux, Aux2;                  // 動きごとの小さなメモ
        public WeaponItem Held; public float FleeLeft;             // ひろい屋が持っている武器
        public Vec2 Knock;
        public bool IsBossLike { get { return Def.Id == "FB" || Def.Id == "FB_MINI"; } }
        public float ContactDamage() { return Def.Id == "FB" && State == 2 ? 20f : Def.Contact; }   // 王の突進は、ダメージ20
    }
}

namespace DotMeikyu.Core
{
    // ペット：ついてきて、体当たりして、落ちた武器をとりにいく。やられたら気絶して休む（いなくならない）
    public sealed class PetState
    {
        public Vec2 Pos; public float Hp = 40f, MaxHp = 40f, Radius = 0.35f, Stun, AttackCd;
        public int Growth;                     // 成長点（食べた武器とペットカードで増える）
        public int AteSword, AteBow, AteStaff, AffixCount;
        public int Stage { get { return Growth >= 15 ? 3 : Growth >= 8 ? 2 : Growth >= 3 ? 1 : 0; } }
        public float Size { get { return 1f + 0.2f * Stage; } }
        public float Damage { get { return Stage == 0 ? 5f : Stage == 1 ? 8f : 11f; } }
        public string EvolutionKind { get { if (Stage < 3) return null; int m = Math.Max(AteSword, Math.Max(AteBow, AteStaff)); return m == AteStaff && AteStaff > 0 ? "魔導スライム" : m == AteBow && AteBow > 0 ? "弓スライム" : "剣スライム"; } }
    }
}
