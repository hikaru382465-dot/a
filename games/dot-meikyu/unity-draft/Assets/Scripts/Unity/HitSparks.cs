using UnityEngine;
using DotMeikyu;
using DotMeikyu.Core;

namespace DotMeikyu
{
    // 当たった所に、火花をぱっと散らす部品（EventTrigger型）
    // ・ParticleSystem を1つだけ用意する（Looping=オフ、Play On Awake=オフ、Emission=オフ、Shape=オフ。
    //   Start Lifetime 0.2〜0.35、Start Speed 3〜6、Start Size 0.08〜0.14、Simulation Space=World、Renderer=白い四角）
    // ・こちらで Emit(n) を呼ぶだけ。数や色は、ここで変える。毎回オブジェクトは作らない
    public sealed class HitSparks : MonoBehaviour
    {
        [SerializeField] SimRunner runner;
        [SerializeField] ParticleSystem sparks;
        [SerializeField] int normalCount = 5;
        [SerializeField] int critCount = 12;
        [SerializeField] Color normalColor = new Color(1f, 1f, 1f, 1f);
        [SerializeField] Color critColor = new Color(1f, 0.85f, 0.2f, 1f);

        void OnEnable() { if (runner != null) runner.SimEventRaised += OnEvent; }
        void OnDisable() { if (runner != null) runner.SimEventRaised -= OnEvent; }

        void OnEvent(SimEvent e)
        {
            if (e.Kind != EventKind.Hit) return;
            bool crit = e.Tag == "crit";
            var p = new ParticleSystem.EmitParams();
            p.position = new Vector3(e.Pos.X, 0.6f, e.Pos.Y);
            p.startColor = crit ? critColor : normalColor;
            sparks.Emit(p, crit ? critCount : normalCount);
        }
    }
}
