using System.Collections.Generic;

namespace DotMeikyu.Core
{
    public enum CardKind { Strengthen, Skill, Change, Pet }

    public sealed class CardDef
    {
        public string Id, Name, Tag, Effect, Job;      // Job：空＝全員／共通／連射／範囲／召喚
        public CardKind Kind;
        public int MaxLevel;
        public float Weight;
        public bool IsEvolution;                       // EV…：条件を満たしたときだけ出る
        public bool OnlyWhenHpLow;                     // 薬びん：HPが半分以下のときだけ
    }

    public sealed class EnemyDef
    {
        public string Id, Name, Region, Role, Memo, RangedRaw;
        public float Hp, Speed, Contact, RangedMax, Soul, WeaponDrop, GemDrop;
        public int Xp;                                   // 倒したときの経験値（メモの「経験値N」）
        public bool IsBoss { get { return Role == "ボス"; } }
        public bool IsThief { get { return Role == "ひろい屋"; } }
        public bool HasNumbers { get { return Hp > 0f; } }   // 洞窟・沼はまだ数値なし
    }

    public sealed class GemDef
    {
        public string Id, Name, Kind, Effect, Affinity;
        public string[] Levels;                        // Lv1〜5の数値（文字のまま）
        public bool FirstRelease;                      // 最初の版に入れる
    }

    public sealed class DataTables
    {
        public List<CardDef> Cards = new List<CardDef>();
        public List<EnemyDef> Enemies = new List<EnemyDef>();
        public List<GemDef> Gems = new List<GemDef>();
    }
}
