using System.Collections.Generic;
using UnityEngine;
using DotMeikyu;
using DotMeikyu.Core;

namespace DotMeikyu
{
    // 当たった敵を、一瞬しろ光りさせる部品（EventTrigger型）。SimRunner の SimEventRaised を聞く
    // ・絵（SpriteRenderer）のマテリアルを、白ぬりのマテリアルに一瞬だけ取りかえて、もどす
    // ・毎フレームの検索はしない。敵の絵ごとの SpriteRenderer は、最初の1回だけ取って覚える
    public sealed class HitFlash : MonoBehaviour
    {
        [SerializeField] SimRunner runner;
        [SerializeField] Material flashMaterial;                 // DotMeikyu/SpriteFlash のマテリアル
        [SerializeField] float flashTime = 0.07f;

        sealed class Active { public SpriteRenderer sr; public Material original; public float left; }
        readonly Dictionary<GameObject, SpriteRenderer> cache = new Dictionary<GameObject, SpriteRenderer>();
        readonly List<Active> active = new List<Active>();

        void OnEnable() { if (runner != null) runner.SimEventRaised += OnEvent; }
        void OnDisable() { if (runner != null) runner.SimEventRaised -= OnEvent; }

        void OnEvent(SimEvent e)
        {
            if (e.Kind != EventKind.Hit || e.Target == null) return;
            GameObject go = runner.ViewOf(e.Target); if (go == null) return;
            SpriteRenderer sr; if (!cache.TryGetValue(go, out sr)) { sr = go.GetComponentInChildren<SpriteRenderer>(); cache[go] = sr; }
            if (sr == null) return;
            for (int i = 0; i < active.Count; i++) if (active[i].sr == sr) { active[i].left = flashTime; return; }   // すでに光っているなら、延ばすだけ
            active.Add(new Active { sr = sr, original = sr.sharedMaterial, left = flashTime });
            sr.sharedMaterial = flashMaterial;
        }

        void Update()
        {
            for (int i = active.Count - 1; i >= 0; i--)
            {
                active[i].left -= Time.deltaTime;
                if (active[i].left > 0f) continue;
                if (active[i].sr != null) active[i].sr.sharedMaterial = active[i].original;   // 敵が消えていたら、何もしない
                active.RemoveAt(i);
            }
        }
    }
}
