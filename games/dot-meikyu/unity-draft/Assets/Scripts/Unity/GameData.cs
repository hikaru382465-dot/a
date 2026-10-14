using UnityEngine;
using DotMeikyu.Core;

namespace DotMeikyu
{
    // CSV（design/ のもの）を、Unityの TextAsset として入れて、ゲームで使う形にする。
    // 使い方：空のオブジェクトにこの部品をつけ、インスペクターに3つのCSVをドラッグする。
    // 他の部品は、[SerializeField] でこの部品を指定して使う（Find は使わない）。
    public sealed class GameData : MonoBehaviour
    {
        [SerializeField] TextAsset cardsCsv;
        [SerializeField] TextAsset enemiesCsv;
        [SerializeField] TextAsset gemsCsv;

        public DataTables Tables { get; private set; }

        void Awake()
        {
            Tables = DataLoader.Load(
                cardsCsv != null ? cardsCsv.text : null,
                enemiesCsv != null ? enemiesCsv.text : null,
                gemsCsv != null ? gemsCsv.text : null);
            Debug.Log("データを読みこんだ：カード " + Tables.Cards.Count + "、敵 " + Tables.Enemies.Count + "、宝石 " + Tables.Gems.Count);
        }
    }
}
