using System;
using System.Collections.Generic;
using UnityEngine;
using DotMeikyu.Core;

namespace DotMeikyu
{
    [Serializable] public sealed class EnemyPrefab { public string id; public GameObject prefab; }

    // 戦闘の世界（Sim）を動かし、敵やペットや落ちた武器の絵（オブジェクト）を、その位置に合わせる部品
    // ・中身（強さ・動き・ダメージ）は、すべて Core の Sim が決める。ここは、時間を進めて、見た目を合わせるだけ
    // ・光・音・ダメージの数字は、SimEventRaised を受け取る別の部品に任せる（EventTrigger型）
    public sealed class SimRunner : MonoBehaviour
    {
        [SerializeField] GameData data;
        [SerializeField] PlayerController player;
        [SerializeField] Transform petView;
        [SerializeField] GameObject defaultEnemyPrefab;
        [SerializeField] EnemyPrefab[] enemyPrefabs;
        [SerializeField] GameObject weaponDropPrefab;
        [Header("はじめの設定（あとでホーム画面から渡す）")]
        [SerializeField] string startRegion = "森";                 // 森／洞窟
        [SerializeField] int startStage = 0;
        [SerializeField] WeaponKind startWeapon = WeaponKind.Staff;
        [SerializeField] Rarity startRarity = Rarity.Common;
        [SerializeField] string startJob = "騎士団";               // 獣／騎士団／精霊（召喚の流派）
        [SerializeField] int rerollsPerRun = 1;

        public Sim Sim { get; private set; }
        public StageDirector Director { get; private set; }
        public event Action<SimEvent> SimEventRaised;
        public event Action<IList<CardDef>> LevelUpOffered;      // カード選びの画面を出す合図（3枚）
        public event Action CardChosen;                           // 選び終わった合図
        public bool IsChoosingCard { get { return offer != null; } }
        public int RerollsLeft { get; private set; }
        public float Coins { get; private set; }

        // 敵の絵（見た目）を返す。なければ null（しろ光りなどの部品が使う）
        public GameObject ViewOf(Mob m) { GameObject go; return mobViews.TryGetValue(m, out go) ? go : null; }

        // 挑戦が終わったとき（死んだときも）に呼ぶ。拾った武器・宝石は残る
        public void SaveNow() { SaveStore.Save(Sim, Coins); }

        readonly Dictionary<string, GameObject> prefabById = new Dictionary<string, GameObject>();
        readonly Dictionary<Mob, GameObject> mobViews = new Dictionary<Mob, GameObject>();
        readonly Dictionary<DroppedWeapon, GameObject> dropViews = new Dictionary<DroppedWeapon, GameObject>();
        readonly List<Mob> staleMobs = new List<Mob>();
        readonly List<DroppedWeapon> staleDrops = new List<DroppedWeapon>();
        Transform playerTr;
        CardPicker picker;
        List<CardDef> offer;

        // GameData の Awake が終わったあとに始めるため、Start を使う
        void Start()
        {
            if (enemyPrefabs != null) foreach (var e in enemyPrefabs) if (e != null && e.prefab != null) prefabById[e.id] = e.prefab;
            Sim = new Sim(data.Tables, WeaponItem.Create(startWeapon, startRarity, new System.Random()), Environment.TickCount);
            Coins = SaveStore.Load(Sim);                // 前回までの倉庫・宝石を戻す
            Sim.StartRun(startJob); RerollsLeft = rerollsPerRun;
            picker = new CardPicker(data.Tables.Cards, new System.Random());
            Director = new StageDirector(Sim) { Region = startRegion }; Director.Begin(startStage);
            playerTr = player.transform;
            player.ChargedAttackFired += OnCharged;
            player.ApplyModifiers(Sim.Mods);
        }

        // カード選び：1〜3 番目のカードを選ぶ（UIのボタンから呼ぶ）
        public void ChooseCard(int index)
        {
            if (offer == null || index < 0 || index >= offer.Count) return;
            Sim.ApplyCard(offer[index]); player.ApplyModifiers(Sim.Mods);
            offer = null; if (CardChosen != null) CardChosen();
        }

        // 引きなおし（1回の挑戦で、決まった回数だけ）
        public void Reroll()
        {
            if (offer == null || RerollsLeft <= 0) return;
            RerollsLeft--; Offer();
        }

        void Offer() { offer = picker.Pick3(Sim.Cards); if (LevelUpOffered != null) LevelUpOffered(offer); }

        void OnDestroy() { if (player != null) player.ChargedAttackFired -= OnCharged; }

        void OnCharged() { if (Sim != null) Sim.FireCharged(); }

        void Update()
        {
            if (Sim == null || offer != null) return;               // カードを選んでいる間は、世界が止まる
            if (Sim.TakeLevelUp()) { Offer(); return; }
            Sim.Charging = player.IsCharging;
            Vector3 p = playerTr.position;
            Sim.Player.Pos = new Vec2(p.x, p.z); Sim.Player.DashInvulnerable = player.IsInvulnerable;
            Sim.Tick(Time.deltaTime); Director.Tick(Time.deltaTime);
            if (SimEventRaised != null) foreach (var e in Sim.Events) SimEventRaised(e);
            SyncViews();
        }

        void SyncViews()
        {
            foreach (var m in Sim.Mobs)
            {
                GameObject go;
                if (!mobViews.TryGetValue(m, out go))
                {
                    GameObject prefab; if (!prefabById.TryGetValue(m.Def.Id, out prefab)) prefab = defaultEnemyPrefab;
                    if (prefab == null) continue;
                    go = Instantiate(prefab, new Vector3(m.Pos.X, 0f, m.Pos.Y), Quaternion.identity); mobViews[m] = go;   // 数が増えたら、使い回し（プール）にする
                }
                go.transform.position = new Vector3(m.Pos.X, 0f, m.Pos.Y);
            }
            staleMobs.Clear(); foreach (var kv in mobViews) if (!kv.Key.Alive) staleMobs.Add(kv.Key);
            foreach (var m in staleMobs) { Destroy(mobViews[m]); mobViews.Remove(m); }

            foreach (var d in Sim.Drops)
            {
                GameObject go;
                if (!dropViews.TryGetValue(d, out go)) { if (weaponDropPrefab == null) continue; go = Instantiate(weaponDropPrefab, new Vector3(d.Pos.X, 0f, d.Pos.Y), Quaternion.identity); dropViews[d] = go; }
            }
            staleDrops.Clear(); foreach (var kv in dropViews) if (kv.Key.Taken || !Sim.Drops.Contains(kv.Key)) staleDrops.Add(kv.Key);
            foreach (var d in staleDrops) { Destroy(dropViews[d]); dropViews.Remove(d); }

            if (petView != null) petView.position = new Vector3(Sim.Pet.Pos.X, 0f, Sim.Pet.Pos.Y);
        }
    }
}
