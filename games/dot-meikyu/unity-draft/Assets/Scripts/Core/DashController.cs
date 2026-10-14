using System;

namespace DotMeikyu.Core
{
    public sealed class DashSettings
    {
        public float Distance = 3f, Duration = 0.15f, Invulnerable = 0.25f, Cooldown = 2.0f;
        public float DoubleTapWindow = 0.30f;   // 1回目のタップのあと、この秒数のうちに2回目を押すとダッシュ
        public float TapMaxHold = 0.20f;        // これより長く押したものは、タップと数えない
    }

    // ダッシュ：画面を軽く2回たたく（ダブルタップ）。1本指でもできる。細かい決め方は、遊んで決める
    public sealed class DashController
    {
        readonly DashSettings s;
        float cooldownLeft, dashLeft, invLeft;
        float lastTapTime = -999f, pressTime; bool pressed;
        Vec2 dashDir;

        public DashController(DashSettings settings) { s = settings; }
        public bool IsDashing { get { return dashLeft > 0f; } }
        public bool IsInvulnerable { get { return invLeft > 0f; } }

        public void OnPress(float now, Vec2 facing)
        {
            pressTime = now; pressed = true;
            if (now - lastTapTime <= s.DoubleTapWindow && cooldownLeft <= 0f && !IsDashing)
            {
                dashDir = facing.Length > 0.001f ? facing.Normalized : new Vec2(1f, 0f);
                dashLeft = s.Duration; invLeft = s.Invulnerable; cooldownLeft = s.Cooldown; lastTapTime = -999f;
            }
        }

        // movedFar：押している間に、指を大きく動かしたか（動かしたなら、タップではなく、移動）
        public void OnRelease(float now, bool movedFar)
        {
            if (pressed && now - pressTime <= s.TapMaxHold && !movedFar) lastTapTime = now;
            pressed = false;
        }

        // 毎フレーム呼ぶ。このフレームで、ダッシュで動く距離を返す
        public Vec2 Tick(float dt)
        {
            if (cooldownLeft > 0f) cooldownLeft = Math.Max(0f, cooldownLeft - dt);
            if (invLeft > 0f) invLeft = Math.Max(0f, invLeft - dt);
            if (dashLeft <= 0f) return Vec2.Zero;
            float step = Math.Min(dt, dashLeft); dashLeft -= step;
            return dashDir * (s.Distance / s.Duration * step);
        }
    }
}
