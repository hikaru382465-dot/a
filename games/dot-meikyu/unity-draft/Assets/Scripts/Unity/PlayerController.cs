using System;
using UnityEngine;
using UnityEngine.InputSystem;
using DotMeikyu.Core;

namespace DotMeikyu
{
    // プレイヤーの移動・ため攻撃・ダッシュ（指1本）。見下ろしの地面は、x と z の平面
    // ・画面のどこを押しても、そこがスティックの真ん中。動いている間ゲージがたまり、満タンで指を離すとため攻撃
    // ・PCの確認用：WASDで動く。スペースを押している間が「指を置いている」。離すと発射
    // ・ため攻撃が出たときの中身は、この部品は知らない。ChargedAttackFired を受け取る別の部品が受け持つ
    //   （「再利用できるEventTrigger型の部品」にするため）
    public sealed class PlayerController : MonoBehaviour
    {
        [Header("動き")]
        [SerializeField] float moveSpeed = 3.5f;                 // マス/秒（design/run.csv）
        [SerializeField] float stickRadiusInches = 0.35f;        // スティックの大きさ（インチ）
        [SerializeField] float deadZoneInches = 0.05f;
        [Header("ため・ダッシュ（design/run.csv）")]
        [SerializeField] float chargeTime = 3.0f;
        [SerializeField] float recoil = 0.3f;
        [SerializeField] float chargeCooldown = 1.0f;
        [SerializeField] float dashDistance = 3f;
        [SerializeField] float dashCooldown = 2.0f;
        [Header("見た目")]
        [SerializeField] SpriteRenderer sprite;                  // 向きで左右反転する
        [SerializeField] bool showDebugGauge = true;

        public event Action ChargedAttackFired;                  // ため攻撃が出た
        public event Action<float> ChargeChanged;                // ゲージ（0〜1）が変わった
        public Vector2 Facing { get; private set; }              // 最後に動いた向き
        public bool IsInvulnerable { get { return dash.IsInvulnerable; } }

        readonly FloatingStick stick = new FloatingStick();
        ChargeController charge;
        DashController dash;
        Transform tr;
        bool prevPressed; float maxDragDist; Vector2 pressPos; float lastCharge = -1f;

        void Awake()
        {
            tr = transform;                                      // 毎フレーム探さないよう、ここで取っておく
            charge = new ChargeController(new ChargeSettings { ChargeTime = chargeTime, Recoil = recoil, Cooldown = chargeCooldown });
            dash = new DashController(new DashSettings { Distance = dashDistance, Cooldown = dashCooldown });
            float dpi = Screen.dpi > 1f ? Screen.dpi : 160f;     // 取れないときは、ふつうのスマホの値
            stick.MaxRadius = stickRadiusInches * dpi; stick.DeadZone = deadZoneInches * dpi;
            Facing = new Vector2(1f, 0f);
        }

        void Update()
        {
            float dt = Time.deltaTime;
            bool held; Vector2 dir; float strength;
            ReadInput(out held, out dir, out strength);

            if (dir.sqrMagnitude > 0.0001f) Facing = dir;
            bool moving = strength > 0.001f;

            // ため：動いている間だけたまる。満タンで離すと発射
            if (charge.Tick(dt, held, moving) && ChargedAttackFired != null) ChargedAttackFired();
            if (!Mathf.Approximately(lastCharge, charge.Charge01)) { lastCharge = charge.Charge01; if (ChargeChanged != null) ChargeChanged(lastCharge); }

            // 動く：ダッシュ中は、ダッシュの分だけ。うった直後は、動けない
            Vec2 dashMove = dash.Tick(dt);
            Vector3 delta = new Vector3(dashMove.X, 0f, dashMove.Y);
            if (!dash.IsDashing && charge.CanMove) delta += new Vector3(dir.x, 0f, dir.y) * (moveSpeed * strength * dt);
            tr.position += delta;
            if (sprite != null && Mathf.Abs(Facing.x) > 0.2f) sprite.flipX = Facing.x < 0f;   // 右向きの絵を、左なら反転
        }

        // 画面の押し方（マウス・タッチ）とキーボードを読んで、「押しているか・向き・強さ」にする
        void ReadInput(out bool held, out Vector2 dir, out float strength)
        {
            held = false; dir = Vector2.zero; strength = 0f;
            Keyboard kb = Keyboard.current;
            if (kb != null)
            {
                Vector2 k = Vector2.zero;
                if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) k.x -= 1f;
                if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) k.x += 1f;
                if (kb.sKey.isPressed || kb.downArrowKey.isPressed) k.y -= 1f;
                if (kb.wKey.isPressed || kb.upArrowKey.isPressed) k.y += 1f;
                if (k.sqrMagnitude > 0f || kb.spaceKey.isPressed)
                {
                    held = kb.spaceKey.isPressed; dir = k.normalized; strength = k.sqrMagnitude > 0f ? 1f : 0f;
                    return;
                }
            }
            Pointer p = Pointer.current;                          // マウスもタッチも、これで読める
            if (p == null) return;
            bool pressed = p.press.isPressed; Vector2 pos = p.position.ReadValue();
            float now = Time.time;
            if (pressed && !prevPressed) { stick.Press(new Vec2(pos.x, pos.y)); dash.OnPress(now, new Vec2(Facing.x, Facing.y)); pressPos = pos; maxDragDist = 0f; }
            if (pressed) maxDragDist = Mathf.Max(maxDragDist, (pos - pressPos).magnitude);
            if (!pressed && prevPressed) { dash.OnRelease(now, maxDragDist > stick.DeadZone * 2f); stick.Release(); }
            prevPressed = pressed;
            held = pressed;
            float s; Vec2 d = stick.Evaluate(new Vec2(pos.x, pos.y), out s);
            dir = new Vector2(d.X, d.Y); strength = s;
        }

        void OnGUI()
        {
            if (!showDebugGauge || charge == null) return;
            int n = Mathf.RoundToInt(charge.Charge01 * 10f); string bar = "";
            for (int i = 0; i < 10; i++) bar += i < n ? "■" : "□";
            GUI.Label(new Rect(10f, 10f, 400f, 30f), "ため " + bar + "  " + charge.State + (dash.IsInvulnerable ? "  無敵" : ""));
        }
    }
}
