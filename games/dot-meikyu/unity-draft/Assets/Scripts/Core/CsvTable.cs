using System;
using System.Collections.Generic;
using System.Text;

namespace DotMeikyu.Core
{
    // CSVを読む小さな部品。ダブルクォートと改行、先頭の目印（BOM）に対応。Unityに依存しない
    public sealed class CsvTable
    {
        public string[] Header { get; private set; }
        public List<string[]> Rows { get; private set; }
        readonly Dictionary<string, int> col = new Dictionary<string, int>();

        public static CsvTable Parse(string text)
        {
            var t = new CsvTable();
            var all = ParseRows(text);
            if (all.Count == 0) { t.Header = new string[0]; t.Rows = new List<string[]>(); return t; }
            t.Header = all[0];
            for (int i = 0; i < t.Header.Length; i++) t.col[t.Header[i].Trim()] = i;
            t.Rows = all.GetRange(1, all.Count - 1);
            return t;
        }

        // 列名で取り出す。列がない・足りないときは空文字
        public string Get(string[] row, string name)
        {
            int i;
            if (!col.TryGetValue(name, out i) || i >= row.Length) return "";
            return row[i].Trim();
        }

        static List<string[]> ParseRows(string text)
        {
            var rows = new List<string[]>();
            if (string.IsNullOrEmpty(text)) return rows;
            if (text[0] == '﻿') text = text.Substring(1);
            var field = new StringBuilder(); var cur = new List<string>(); bool quoted = false;
            for (int i = 0; i < text.Length; i++)
            {
                char c = text[i];
                if (quoted)
                {
                    if (c == '"') { if (i + 1 < text.Length && text[i + 1] == '"') { field.Append('"'); i++; } else quoted = false; }
                    else field.Append(c);
                }
                else if (c == '"') quoted = true;
                else if (c == ',') { cur.Add(field.ToString()); field.Length = 0; }
                else if (c == '\n' || c == '\r')
                {
                    if (c == '\r' && i + 1 < text.Length && text[i + 1] == '\n') i++;
                    cur.Add(field.ToString()); field.Length = 0;
                    if (!(cur.Count == 1 && cur[0].Length == 0)) rows.Add(cur.ToArray());
                    cur = new List<string>();
                }
                else field.Append(c);
            }
            if (field.Length > 0 || cur.Count > 0) { cur.Add(field.ToString()); rows.Add(cur.ToArray()); }
            return rows;
        }
    }

    // 「2.2（武器を持つと3.0）」「0.5%」「毎0.5秒3」のような、メモつきの数字を読む
    public static class Loose
    {
        public static float First(string s)
        {
            float f; return TryNumber(s, 0, false, out f) ? f : 0f;
        }
        public static float Max(string s)
        {
            float best = 0f; int i = 0;
            while (i < s.Length) { float f; int next; if (Scan(s, i, out f, out next)) { if (f > best) best = f; i = next; } else i++; }
            return best;
        }
        // 「0.5%」→0.005、「100%（レア以上）」→1.0。「取られた武器を100%返す」のような文は0
        public static float Percent(string s)
        {
            if (string.IsNullOrEmpty(s)) return 0f;
            int p = s.IndexOf('%'); if (p < 0) return 0f;
            for (int k = 0; k < p; k++) if (!(char.IsDigit(s[k]) || s[k] == '.' || s[k] == '-' )) return 0f;
            float f; return float.TryParse(s.Substring(0, p), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out f) ? f / 100f : 0f;
        }
        public static int FirstInt(string s) { return (int)First(s); }

        static bool TryNumber(string s, int from, bool unused, out float f)
        {
            int next; for (int i = from; i < s.Length; i++) if (Scan(s, i, out f, out next)) return true;
            f = 0f; return false;
        }
        static bool Scan(string s, int i, out float f, out int next)
        {
            f = 0f; next = i;
            if (!char.IsDigit(s[i])) return false;
            int j = i; while (j < s.Length && (char.IsDigit(s[j]) || s[j] == '.')) j++;
            string num = s.Substring(i, j - i).TrimEnd('.');
            next = j;
            return float.TryParse(num, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out f);
        }
    }
}
