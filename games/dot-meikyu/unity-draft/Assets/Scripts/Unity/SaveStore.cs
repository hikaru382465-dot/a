using System.Collections.Generic;
using System.IO;
using UnityEngine;
using DotMeikyu.Core;

namespace DotMeikyu
{
    // セーブの読み書き（倉庫の武器・宝石・コイン）。中身の形は Core の SaveText が決める
    // 保存は、挑戦が終わったとき（死んだときも）と、ホームで宝石をいじったときに呼ぶ
    public static class SaveStore
    {
        static string PathName { get { return Path.Combine(Application.persistentDataPath, "dotmeikyu_save.txt"); } }

        public static void Save(Sim sim, float coins)
        {
            File.WriteAllText(PathName, SaveText.Write(sim.Storage, sim.Gems, coins));
        }

        // 保存があれば、Sim に戻す。コインを返す
        public static float Load(Sim sim)
        {
            float coins = 0f; if (!File.Exists(PathName)) return coins;
            SaveText.Read(File.ReadAllText(PathName), sim.Storage, sim.Gems, out coins);
            return coins;
        }
    }
}
