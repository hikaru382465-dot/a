using UnityEngine;
using DotMeikyu.Core;

namespace DotMeikyu
{
    // ダメージの数字を出す部品（EventTrigger型）。SimRunner の SimEventRaised を聞くだけ。ほかの部品は知らない
    // ・用意するもの：TextMesh を1つ持つ小さな Prefab（Anchor＝中央、Font Size＝64、Character Size＝0.05 くらい）
    // ・数字は最初に決まった数だけ作って使い回す（毎回作らない）。足りなければ、古いものから使う
    public sealed class DamageNumbers : MonoBehaviour
    {
        [SerializeField] SimRunner runner;
        [SerializeField] GameObject numberPrefab;
        [SerializeField] int poolSize = 40;
        [SerializeField] float life = 0.7f;
        [SerializeField] float riseSpeed = 1.6f;
        [SerializeField] Color normalColor = new Color(1f, 1f, 1f, 1f);
        [SerializeField] Color critColor = new Color(1f, 0.85f, 0.2f, 1f);
        [SerializeField] Color hurtColor = new Color(1f, 0.3f, 0.3f, 1f);

        struct Item { public GameObject go; public TextMesh text; public float t; public bool alive; public Vector3 pos; }
        Item[] pool; int next; Transform cam;

        void Awake()
        {
            cam = Camera.main != null ? Camera.main.transform : null;      // 毎フレーム探さない
            pool = new Item[poolSize];
            for (int i = 0; i < poolSize; i++)
            {
                var go = Instantiate(numberPrefab, new Vector3(0f, -999f, 0f), Quaternion.identity); go.SetActive(false);
                pool[i] = new Item { go = go, text = go.GetComponent<TextMesh>() };   // 作るときだけ GetComponent
            }
        }

        void OnEnable() { if (runner != null) runner.SimEventRaised += OnEvent; }
        void OnDisable() { if (runner != null) runner.SimEventRaised -= OnEvent; }

        void OnEvent(SimEvent e)
        {
            if (e.Kind == EventKind.Hit) Show(e.Pos, e.Value, e.Tag == "crit" ? critColor : normalColor, e.Tag == "crit" ? 1.4f : 1f);
            else if (e.Kind == EventKind.PlayerHurt) Show(e.Pos, e.Value, hurtColor, 1.2f);
        }

        void Show(Vec2 at, float value, Color color, float scale)
        {
            if (pool == null || value < 0.5f) return;                      // 小さすぎる数字は出さない（毒など細かいもの）
            var it = pool[next]; next = (next + 1) % pool.Length;
            it.pos = new Vector3(at.X + Random.Range(-0.2f, 0.2f), 0.8f, at.Y); it.t = 0f; it.alive = true;
            it.text.text = Mathf.RoundToInt(value).ToString(); it.text.color = color; it.go.transform.localScale = new Vector3(scale, scale, scale);
            it.go.transform.position = it.pos; it.go.SetActive(true); pool[(next + pool.Length - 1) % pool.Length] = it;
        }

        void Update()
        {
            float dt = Time.deltaTime;
            for (int i = 0; i < pool.Length; i++)
            {
                if (!pool[i].alive) continue;
                pool[i].t += dt;
                if (pool[i].t >= life) { pool[i].alive = false; pool[i].go.SetActive(false); continue; }
                pool[i].pos.y += riseSpeed * dt; pool[i].go.transform.position = pool[i].pos;
                if (cam != null) pool[i].go.transform.rotation = cam.rotation;     // いつもカメラのほうを向く
            }
        }
    }
}
