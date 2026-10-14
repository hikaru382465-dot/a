using UnityEngine;
using DotMeikyu;
using DotMeikyu.Core;

namespace DotMeikyu
{
    // 敵の範囲攻撃の「赤い予告」と「炸裂」を見せる部品（EventTrigger型）。SimRunner の SimEventRaised を聞くだけ
    // ・Telegraph（予告）：赤い円（blast・ring・meteor）か、赤い帯（line・dash）を出す。円は、中がだんだん濃くなって、炸裂の瞬間に満たされる
    // ・Cloud の blast（炸裂）：円がぱっと白く光って消え、火花が散る
    // ・用意するもの：①まるい白い絵（Sprite）を持つ Prefab（circlePrefab）②白い四角の絵を持つ Prefab（barPrefab）
    //   ③火花用の ParticleSystem 1つ（HitSparks と同じ設定）。数は最初に作って使い回す（毎回作らない）
    public sealed class TelegraphView : MonoBehaviour
    {
        [SerializeField] SimRunner runner;
        [SerializeField] GameObject circlePrefab;
        [SerializeField] GameObject barPrefab;
        [SerializeField] ParticleSystem burstSparks;
        [SerializeField] int poolSize = 24;
        [SerializeField] Color warnColor = new Color(1f, 0.15f, 0.1f, 0.55f);
        [SerializeField] Color burstColor = new Color(1f, 0.95f, 0.8f, 0.9f);
        [SerializeField] float burstTime = 0.18f;
        [SerializeField] float ringRadius = 1.5f, meteorRadius = 3f;

        struct Item { public GameObject go; public SpriteRenderer sr; public bool alive, burst, bar; public float t, dur, radius; }
        Item[] pool; int next;

        void Awake()
        {
            pool = new Item[poolSize];
            for (int i = 0; i < poolSize; i++)
            {
                bool bar = i % 4 == 3;                                   // 4つに1つは帯用
                var go = Instantiate(bar ? barPrefab : circlePrefab, new Vector3(0f, -999f, 0f), Quaternion.Euler(90f, 0f, 0f)); go.SetActive(false);
                pool[i] = new Item { go = go, sr = go.GetComponent<SpriteRenderer>(), bar = bar };       // 作るときだけ GetComponent
            }
        }

        void OnEnable() { if (runner != null) runner.SimEventRaised += OnEvent; }
        void OnDisable() { if (runner != null) runner.SimEventRaised -= OnEvent; }

        void OnEvent(SimEvent e)
        {
            if (e.Kind == EventKind.Telegraph)
            {
                switch (e.Tag)
                {
                    case "blast": ShowCircle(e.Pos, e.Pos2.X - e.Pos.X, e.Value); break;
                    case "ring": ShowCircle(e.Pos, ringRadius, e.Value); break;
                    case "meteor": ShowCircle(e.Pos, meteorRadius, e.Value); break;
                    case "line": case "dash": ShowBar(e.Pos, e.Pos2, e.Value); break;
                }
            }
            else if (e.Kind == EventKind.Cloud && e.Tag == "blast")
            {
                ShowBurst(e.Pos, e.Value);
                if (burstSparks != null) { var p = new ParticleSystem.EmitParams(); p.position = new Vector3(e.Pos.X, 0.4f, e.Pos.Y); p.startColor = burstColor; burstSparks.Emit(p, 10); }
            }
        }

        Item Take(bool bar)
        {
            for (int k = 0; k < pool.Length; k++) { int i = (next + k) % pool.Length; if (pool[i].bar == bar) { next = (i + 1) % pool.Length; return pool[i]; } }
            return pool[0];
        }

        void Put(Item it) { for (int i = 0; i < pool.Length; i++) if (pool[i].go == it.go) { pool[i] = it; return; } }

        void ShowCircle(Vec2 at, float radius, float dur)
        {
            var it = Take(false); it.alive = true; it.burst = false; it.t = 0f; it.dur = Mathf.Max(0.05f, dur); it.radius = radius;
            it.go.transform.position = new Vector3(at.X, 0.05f, at.Y); it.go.transform.localScale = new Vector3(radius * 2f, radius * 2f, 1f); it.go.SetActive(true); Put(it);
        }

        void ShowBar(Vec2 a, Vec2 b, float dur)
        {
            var it = Take(true); it.alive = true; it.burst = false; it.t = 0f; it.dur = Mathf.Max(0.05f, dur);
            float len = Mathf.Max(0.5f, (new Vector2(b.X - a.X, b.Y - a.Y)).magnitude); float ang = Mathf.Atan2(b.Y - a.Y, b.X - a.X) * 57.29578f;
            it.go.transform.position = new Vector3((a.X + b.X) * 0.5f, 0.05f, (a.Y + b.Y) * 0.5f); it.go.transform.rotation = Quaternion.Euler(90f, -ang, 0f); it.go.transform.localScale = new Vector3(len, 1.2f, 1f); it.go.SetActive(true); Put(it);
        }

        void ShowBurst(Vec2 at, float radius)
        {
            var it = Take(false); it.alive = true; it.burst = true; it.t = 0f; it.dur = burstTime; it.radius = radius;
            it.go.transform.position = new Vector3(at.X, 0.06f, at.Y); it.go.transform.localScale = new Vector3(radius * 2f, radius * 2f, 1f); it.go.SetActive(true); Put(it);
        }

        void Update()
        {
            float dt = Time.deltaTime;
            for (int i = 0; i < pool.Length; i++)
            {
                if (!pool[i].alive) continue;
                pool[i].t += dt; float k = pool[i].t / pool[i].dur;
                if (k >= 1f) { pool[i].alive = false; pool[i].go.SetActive(false); continue; }
                Color c;
                if (pool[i].burst) { c = burstColor; c.a *= 1f - k; }
                else { c = warnColor; c.a = warnColor.a * (0.35f + 0.65f * k); }          // 炸裂に近づくほど、濃くなる
                pool[i].sr.color = c;
            }
        }
    }
}
