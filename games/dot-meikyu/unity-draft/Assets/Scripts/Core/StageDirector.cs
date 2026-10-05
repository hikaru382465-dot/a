using System;

namespace DotMeikyu.Core
{
    // 1つの場所の進行：敵の出し方・出口が出る条件（design/run.csv）
    public sealed class StageInfo
    {
        public float Duration; public int KillTarget, MaxAlive, Exits, Elites; public float SpawnInterval, HpMul;
        public StageInfo(float dur, int kills, int cap, float interval, float hpMul, int exits, int elites) { Duration = dur; KillTarget = kills; MaxAlive = cap; SpawnInterval = interval; HpMul = hpMul; Exits = exits; Elites = elites; }
    }

    public sealed class StageDirector
    {
        // 場所1〜5（番号0〜4）。5番めの次（番号5）がボス
        public static readonly StageInfo[] Stages =
        {
            new StageInfo(75f, 30, 25, 1.0f, 1.00f, 2, 0),
            new StageInfo(90f, 40, 35, 0.8f, 1.25f, 2, 0),
            new StageInfo(90f, 50, 50, 0.65f, 1.55f, 3, 1),
            new StageInfo(100f, 60, 65, 0.55f, 1.90f, 3, 2),
            new StageInfo(100f, 70, 80, 0.45f, 2.30f, 2, 2),
        };

        public int Index { get; private set; }
        public bool IsBoss { get { return Index >= Stages.Length; } }
        public bool ExitsOpen { get; private set; }
        public float StageTime { get; private set; }
        public int StageKills { get { return sim.Kills - killsAtStart; } }
        readonly Sim sim; float acc, ramp, intervalMul = 1f, hpRamp = 1f, ringAt = 45f; int killsAtStart, elitesLeft; float nextElite;

        public StageDirector(Sim s) { sim = s; }
        public StageInfo Info { get { return IsBoss ? null : Stages[Index]; } }

        public void Begin(int index)
        {
            Index = index; ExitsOpen = false; StageTime = 0f; acc = 0f; ramp = 0f; intervalMul = 1f; hpRamp = 1f; ringAt = 45f; killsAtStart = sim.Kills;
            sim.StageAtkMul = 1f + 0.10f * index;                                   // 場所が1つ進むごとに、敵の攻撃+10%
            sim.Mobs.Clear(); sim.Shots.Clear(); sim.Clouds.Clear();
            if (IsBoss) { sim.Spawn("FB", sim.Player.Pos + new Vec2(0f, 7f)); return; }
            var st = Stages[index]; elitesLeft = st.Elites; nextElite = 20f;
            for (int i = 0; i < 6; i++) SpawnOne(st);
        }

        public void Tick(float dt)
        {
            StageTime += dt;
            if (IsBoss) { if (!sim.BossAlive && !ExitsOpen) { ExitsOpen = true; sim.Events.Add(new SimEvent(EventKind.ExitsOpened, sim.Player.Pos, sim.Player.Pos, 1f, "boss")); } return; }
            var st = Stages[Index];
            if (!ExitsOpen && (StageTime >= st.Duration || StageKills >= st.KillTarget))
            {   // 出口が出る。出たあとは、敵は増えない
                ExitsOpen = true; sim.Events.Add(new SimEvent(EventKind.ExitsOpened, sim.Player.Pos, sim.Player.Pos, st.Exits));
            }
            if (ExitsOpen) return;
            ramp += dt; if (ramp >= 30f) { ramp = 0f; intervalMul *= 0.9f; hpRamp *= 1.05f; }   // 30秒ごとに、出る間隔-10%・強さ+5%
            acc += dt;
            while (acc >= st.SpawnInterval * intervalMul) { acc -= st.SpawnInterval * intervalMul; if (sim.AliveCount() < st.MaxAlive) SpawnOne(st); }
            if (Index == 0 && ringAt > 0f && StageTime >= ringAt)
            {   // 場所1の45秒め：スライム15匹が、輪になって囲む
                ringAt = -1f; for (int i = 0; i < 15; i++) sim.Spawn("F01", sim.Player.Pos + FromAngle(i * Math.PI * 2.0 / 15.0) * 7f, st.HpMul * hpRamp);
            }
            if (elitesLeft > 0 && StageTime >= nextElite) { elitesLeft--; nextElite += 25f; sim.Spawn("F01", RingPos(), st.HpMul * hpRamp, true); }
            // ひろい屋：場所2から。落ちた武器が3秒ほうっておかれたら、画面のはしから出る（同時に1体まで）
            if (Index >= 1 && sim.AliveCount("F05") == 0)
                foreach (var d in sim.Drops) if (!d.Taken && d.Age >= 3f) { sim.Spawn("F05", sim.Player.Pos + (d.Pos - sim.Player.Pos).Normalized * 10f, st.HpMul * hpRamp); break; }
        }

        static Vec2 FromAngle(double a) { return new Vec2((float)Math.Cos(a), (float)Math.Sin(a)); }
        Vec2 RingPos() { return sim.Player.Pos + FromAngle(sim.Rng.NextDouble() * Math.PI * 2.0) * (float)(9.0 + sim.Rng.NextDouble() * 2.0); }

        void SpawnOne(StageInfo st)
        {
            double r = sim.Rng.NextDouble(); string id;
            if (Index == 0) id = r < 0.8 ? "F01" : "F02";
            else if (Index == 1) id = r < 0.5 ? "F01" : r < 0.75 ? "F02" : "F03";
            else id = r < 0.35 ? "F01" : r < 0.55 ? "F02" : r < 0.8 ? "F03" : "F04";
            sim.Spawn(id, RingPos(), st.HpMul * hpRamp);
        }
    }
}
