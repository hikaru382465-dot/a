using System;

namespace DotMeikyu.Core
{
    // 画面のどこを押しても、そこが「スティックの真ん中」になる。指がはなれたら、おしまい
    // 指がスティックの外まで行ったら、真ん中が指についてくる（切りかえしが速くなる）
    public sealed class FloatingStick
    {
        public float MaxRadius = 80f;   // 画面のドット（ピクセル）。Unity側でインチから換算して入れる
        public float DeadZone = 8f;     // これより小さい動きは、動かさない（指のふるえ）
        Vec2 origin;
        public bool Active { get; private set; }

        public void Press(Vec2 pos) { origin = pos; Active = true; }
        public void Release() { Active = false; }

        // 向き（長さ1）と、強さ（0〜1）を返す。dir.Length は、強さではなく、ふつう1か0
        public Vec2 Evaluate(Vec2 pos, out float strength01)
        {
            strength01 = 0f;
            if (!Active) return Vec2.Zero;
            Vec2 d = pos - origin; float dist = d.Length;
            if (dist > MaxRadius) { origin = origin + d.Normalized * (dist - MaxRadius); d = pos - origin; dist = d.Length; }
            if (dist <= DeadZone) return Vec2.Zero;
            strength01 = Math.Min(1f, (dist - DeadZone) / Math.Max(1e-3f, MaxRadius - DeadZone));
            return d.Normalized;
        }
    }
}
