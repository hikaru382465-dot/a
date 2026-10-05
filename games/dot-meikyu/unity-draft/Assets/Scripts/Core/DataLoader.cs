using System;

namespace DotMeikyu.Core
{
    // design/ のCSVの文字を、ゲームで使う形（定義）にする。表を直すだけで数値が変わる
    public static class DataLoader
    {
        public static DataTables Load(string cardsCsv, string enemiesCsv, string gemsCsv)
        {
            var d = new DataTables();
            if (cardsCsv != null) LoadCards(CsvTable.Parse(cardsCsv), d);
            if (enemiesCsv != null) LoadEnemies(CsvTable.Parse(enemiesCsv), d);
            if (gemsCsv != null) LoadGems(CsvTable.Parse(gemsCsv), d);
            return d;
        }

        public static void LoadCards(CsvTable t, DataTables d)
        {
            foreach (var r in t.Rows)
            {
                var c = new CardDef();
                c.Id = t.Get(r, "id"); if (c.Id.Length == 0) continue;
                c.Kind = ToKind(t.Get(r, "種類"));
                c.Name = t.Get(r, "名前"); c.Tag = t.Get(r, "タグ"); c.Effect = t.Get(r, "効果");
                c.MaxLevel = Math.Max(1, Loose.FirstInt(t.Get(r, "最大レベル")));
                c.Weight = Loose.First(t.Get(r, "出現の重み"));
                c.Job = t.Get(r, "専用ジョブ");
                c.IsEvolution = c.Id.StartsWith("EV");
                c.OnlyWhenHpLow = c.Effect.Contains("HPが50%以下のときだけ");
                d.Cards.Add(c);
            }
        }

        public static void LoadEnemies(CsvTable t, DataTables d)
        {
            foreach (var r in t.Rows)
            {
                var e = new EnemyDef();
                e.Id = t.Get(r, "id"); if (e.Id.Length == 0) continue;
                e.Name = t.Get(r, "名前"); e.Region = t.Get(r, "地域"); e.Role = t.Get(r, "役割");
                e.Hp = Loose.First(t.Get(r, "体力")); e.Speed = Loose.First(t.Get(r, "速さ"));
                e.Contact = Loose.First(t.Get(r, "接触ダメージ"));
                e.RangedRaw = t.Get(r, "遠距離ダメージ"); e.RangedMax = Loose.Max(e.RangedRaw);
                e.Soul = Loose.First(t.Get(r, "魂ドロップ"));
                e.WeaponDrop = Loose.Percent(t.Get(r, "武器ドロップ率")); e.GemDrop = Loose.Percent(t.Get(r, "宝石ドロップ率"));
                e.Memo = t.Get(r, "メモ（特殊行動）");
                int xi = e.Memo.IndexOf("経験値"); if (xi >= 0) e.Xp = Loose.FirstInt(e.Memo.Substring(xi + 3));
                d.Enemies.Add(e);
            }
        }

        public static void LoadGems(CsvTable t, DataTables d)
        {
            foreach (var r in t.Rows)
            {
                string id = t.Get(r, "id");
                if (!id.StartsWith("G_")) continue;            // 合成の費用などの行は、ここでは読まない
                var g = new GemDef();
                g.Id = id; g.Name = t.Get(r, "名前"); g.Kind = t.Get(r, "種類"); g.Effect = t.Get(r, "効果");
                g.Levels = new[] { t.Get(r, "Lv1"), t.Get(r, "Lv2"), t.Get(r, "Lv3"), t.Get(r, "Lv4"), t.Get(r, "Lv5") };
                g.FirstRelease = t.Get(r, "初版") == "○"; g.Affinity = t.Get(r, "相性");
                d.Gems.Add(g);
            }
        }

        static CardKind ToKind(string s)
        {
            switch (s)
            {
                case "スキル": return CardKind.Skill;
                case "変化": return CardKind.Change;
                case "ペット": return CardKind.Pet;
                default: return CardKind.Strengthen;
            }
        }
    }
}
