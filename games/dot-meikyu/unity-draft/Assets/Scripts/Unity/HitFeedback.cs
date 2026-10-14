using UnityEngine;
using DotMeikyu.Core;

namespace DotMeikyu
{
    // 当たったときの「手ごたえ」の部品（EventTrigger型）：ヒットストップ・画面の揺れ。SimEvent を聞くだけ
    // ・ヒットストップ：一瞬、時間をほぼ止める（Time.timeScale）。重く感じる
    // ・揺れ：カメラを小さく揺らして、元にもどす
    // ・やりすぎると酔う。数字は金曜に、遊びながら決める（最初は小さめ）
    public sealed class HitFeedback : MonoBehaviour
    {
        [SerializeField] SimRunner runner;
        [SerializeField] Transform cameraTransform;
        [Header("ヒットストップ（秒・実時間）")]
        [SerializeField] float hitStop = 0.04f;
        [SerializeField] float critHitStop = 0.07f;
        [SerializeField] float stopScale = 0.05f;
        [Header("画面の揺れ")]
        [SerializeField] float shakePower = 0.06f;
        [SerializeField] float critShakePower = 0.12f;
        [SerializeField] float hurtShakePower = 0.15f;
        [SerializeField] float shakeTime = 0.12f;

        float stopLeft, shakeLeft, power; Vector3 camHome;

        void Awake() { camHome = cameraTransform.localPosition; }
        void OnEnable() { if (runner != null) runner.SimEventRaised += OnEvent; }
        void OnDisable() { if (runner != null) runner.SimEventRaised -= OnEvent; Time.timeScale = 1f; }

        void OnEvent(SimEvent e)
        {
            if (e.Kind == EventKind.Hit && e.Tag == "crit") { Stop(critHitStop); Shake(critShakePower); }
            else if (e.Kind == EventKind.PlayerHurt) { Shake(hurtShakePower); }
            else if (e.Kind == EventKind.BossDied) { Stop(0.2f); Shake(0.25f); }
        }

        void Stop(float sec) { stopLeft = Mathf.Max(stopLeft, sec); Time.timeScale = stopScale; }
        void Shake(float p) { if (p >= power || shakeLeft <= 0f) power = p; shakeLeft = shakeTime; }

        void Update()
        {
            float real = Time.unscaledDeltaTime;
            if (stopLeft > 0f) { stopLeft -= real; if (stopLeft <= 0f) Time.timeScale = 1f; }
            if (shakeLeft > 0f)
            {
                shakeLeft -= real; float k = Mathf.Max(0f, shakeLeft / shakeTime);
                cameraTransform.localPosition = camHome + new Vector3(Random.Range(-1f, 1f), 0f, Random.Range(-1f, 1f)) * (power * k);
            }
            else cameraTransform.localPosition = camHome;
        }
    }
}
