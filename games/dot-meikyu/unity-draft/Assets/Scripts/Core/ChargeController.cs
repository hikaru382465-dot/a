using System;

namespace DotMeikyu.Core
{
    public sealed class ChargeSettings
    {
        public float ChargeTime = 3.0f;   // 満タンまでの秒数（動いている間だけたまる）
        public float Recoil = 0.3f;       // うった直後に動けない秒数
        public float Cooldown = 1.0f;     // うってから、次にためられるまでの秒数
    }

    public enum ChargeState { Idle, Charging, Ready, Recoil, Cooldown }

    // 「ため攻撃」：指を置いて動いている間にゲージがたまり、満タンで指を離すと出る
    // ・満タンでないときに離しても出ない。ゲージは減らない（design/run.csv）
    // ・止まっている間は、たまらない
    public sealed class ChargeController
    {
        readonly ChargeSettings s;
        float charge, recoilLeft, cooldownLeft;
        bool wasHeld;

        public ChargeController(ChargeSettings settings) { s = settings; }

        public float Charge01 { get { return charge; } }
        public bool IsFull { get { return charge >= 1f; } }
        public bool CanMove { get { return recoilLeft <= 0f; } }
        public ChargeState State
        {
            get
            {
                if (recoilLeft > 0f) return ChargeState.Recoil;
                if (cooldownLeft > 0f) return ChargeState.Cooldown;
                if (IsFull) return ChargeState.Ready;
                return charge > 0f ? ChargeState.Charging : ChargeState.Idle;
            }
        }

        // 毎フレーム呼ぶ。ため攻撃が出たフレームだけ true を返す
        public bool Tick(float dt, bool held, bool moving)
        {
            if (recoilLeft > 0f) recoilLeft = Math.Max(0f, recoilLeft - dt);
            if (cooldownLeft > 0f) cooldownLeft = Math.Max(0f, cooldownLeft - dt);
            if (held && moving && recoilLeft <= 0f && cooldownLeft <= 0f && charge < 1f)
                charge = Math.Min(1f, charge + dt / s.ChargeTime);
            bool fired = false;
            if (wasHeld && !held && charge >= 1f && recoilLeft <= 0f)
            {
                fired = true; charge = 0f; recoilLeft = s.Recoil; cooldownLeft = s.Cooldown;
            }
            wasHeld = held;
            return fired;
        }
    }
}
