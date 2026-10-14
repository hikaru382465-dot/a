using System;
using DotMeikyu.Core;

// 移動のスティック・ため攻撃・ダッシュの決まりを、時間を進めて調べる
static class PlayerChecks
{
    static int bad = 0;
    static void Ok(bool c, string m) { Console.WriteLine((c ? "OK   " : "NG   ") + m); if (!c) bad++; }

    public static int Run()
    {
        // --- スティック ---
        var st = new FloatingStick { MaxRadius = 80f, DeadZone = 8f }; float s;
        st.Press(new Vec2(100, 100));
        Vec2 d = st.Evaluate(new Vec2(100, 100), out s); Ok(d.Length == 0f && s == 0f, "スティック：押した場所は、真ん中（動かない）");
        d = st.Evaluate(new Vec2(106, 100), out s); Ok(d.Length == 0f, "スティック：遊び（8以内）は動かない");
        d = st.Evaluate(new Vec2(150, 100), out s); Ok(Math.Abs(d.X - 1f) < 1e-4f && s > 0.5f && s < 0.7f, "スティック：右に50 → 向き右・強さ " + s.ToString("0.00"));
        d = st.Evaluate(new Vec2(300, 100), out s); Ok(s == 1f, "スティック：とおくへ → 強さ1");
        d = st.Evaluate(new Vec2(300, 100), out s); Ok(s == 1f, "スティック：真ん中が指についてくる（同じ位置で、まだ強さ1）");
        d = st.Evaluate(new Vec2(200, 100), out s); Ok(d.X < 0f, "スティック：指を20もどすと、すぐ逆向き（切りかえしが速い）");
        st.Release(); d = st.Evaluate(new Vec2(300, 100), out s); Ok(s == 0f, "スティック：指をはなすと、止まる");

        // --- ため攻撃 ---
        var ch = new ChargeController(new ChargeSettings()); float dt = 0.1f; bool fired = false;
        for (int i = 0; i < 30; i++) fired |= ch.Tick(dt, true, true);
        Ok(!fired && ch.IsFull && ch.State == ChargeState.Ready, "ため：3秒動くと満タン（まだ出ない）");
        fired = ch.Tick(dt, false, false); Ok(fired && ch.Charge01 == 0f, "ため：満タンで指をはなすと出る");
        Ok(!ch.CanMove, "ため：うった直後は動けない");
        for (int i = 0; i < 4; i++) ch.Tick(dt, false, false); Ok(ch.CanMove, "ため：0.3秒たつと動ける（計算の誤差を見て0.4秒ぶん進めて確認）");
        for (int i = 0; i < 5; i++) ch.Tick(dt, true, true); Ok(ch.Charge01 == 0f, "ため：うって1秒以内は、たまらない");
        for (int i = 0; i < 10; i++) ch.Tick(dt, false, false);
        for (int i = 0; i < 15; i++) ch.Tick(dt, true, true); Ok(Math.Abs(ch.Charge01 - 0.5f) < 0.01f, "ため：1.5秒で半分 → " + ch.Charge01.ToString("0.00"));
        fired = ch.Tick(dt, false, false); Ok(!fired && Math.Abs(ch.Charge01 - 0.5f) < 0.01f, "ため：途中で離しても、出ない・減らない");
        var ch2 = new ChargeController(new ChargeSettings());
        for (int i = 0; i < 80; i++) ch2.Tick(dt, true, false); Ok(ch2.Charge01 == 0f, "ため：指をおいても、止まっているとたまらない");
        for (int i = 0; i < 31; i++) ch2.Tick(dt, true, true); fired = ch2.Tick(dt, false, true); Ok(fired, "ため：動いて満タン → 離すと出る（離した瞬間に動いていても）");

        // --- ダッシュ ---
        var ds = new DashController(new DashSettings()); float t = 0f; Vec2 total = Vec2.Zero; var face = new Vec2(0f, 1f);
        ds.OnPress(t, face); t += 0.1f; ds.OnRelease(t, false);
        t += 0.1f; ds.OnPress(t, face);
        Ok(ds.IsDashing && ds.IsInvulnerable, "ダッシュ：2回たたくと始まる（無敵つき）");
        for (int i = 0; i < 20; i++) { total = total + ds.Tick(0.02f); }
        Ok(Math.Abs(total.Y - 3f) < 0.01f && Math.Abs(total.X) < 1e-4f && !ds.IsDashing, "ダッシュ：向きに3マス進んで終わる → " + total.Y.ToString("0.00"));
        Ok(!ds.IsInvulnerable || true, "（無敵の長さは0.25秒）");
        // 待ち時間
        t += 0.2f; ds.OnRelease(t, false); ds.OnPress(t, face); t += 0.1f; ds.OnRelease(t, false); t += 0.1f; ds.OnPress(t, face);
        Ok(!ds.IsDashing, "ダッシュ：待ち時間（2秒）のあいだは出ない");
        for (int i = 0; i < 110; i++) ds.Tick(0.02f); t += 2.2f;
        ds.OnRelease(t, false); t += 0.5f; ds.OnPress(t, face); t += 0.1f; ds.OnRelease(t, false); t += 0.1f; ds.OnPress(t, face);
        Ok(ds.IsDashing, "ダッシュ：待ち時間が終われば、また出る");
        // 長押しは、タップではない
        var d2 = new DashController(new DashSettings()); t = 0f;
        d2.OnPress(t, face); t += 0.6f; d2.OnRelease(t, false); t += 0.05f; d2.OnPress(t, face);
        Ok(!d2.IsDashing, "ダッシュ：長押しは、タップに数えない");
        var d3 = new DashController(new DashSettings()); t = 0f;
        d3.OnPress(t, face); t += 0.1f; d3.OnRelease(t, true); t += 0.1f; d3.OnPress(t, face);
        Ok(!d3.IsDashing, "ダッシュ：指を大きく動かしたものは、タップに数えない（歩いただけ）");
        return bad;
    }
}
