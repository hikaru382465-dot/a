using System;

namespace DotMeikyu.Core
{
    // Unityに依存しない、2つの数字の組（向きや位置に使う）
    public struct Vec2
    {
        public float X, Y;
        public Vec2(float x, float y) { X = x; Y = y; }
        public float Length { get { return (float)Math.Sqrt(X * X + Y * Y); } }
        public static readonly Vec2 Zero = new Vec2(0f, 0f);
        public Vec2 Normalized { get { float l = Length; return l > 1e-6f ? new Vec2(X / l, Y / l) : Zero; } }
        public static Vec2 operator +(Vec2 a, Vec2 b) { return new Vec2(a.X + b.X, a.Y + b.Y); }
        public static Vec2 operator -(Vec2 a, Vec2 b) { return new Vec2(a.X - b.X, a.Y - b.Y); }
        public static Vec2 operator *(Vec2 a, float k) { return new Vec2(a.X * k, a.Y * k); }
    }
}
