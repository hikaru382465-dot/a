# Unity用のC#の下書き（家のパソコンで、Unityに入れて使う）

Unity 6.6 では、まだ動かしていません（私は Unity が動かせない）。ただし、**Unityに依存しない部分は、このフォルダのテストで確かめ済み**です。

## 入れ方（金曜の夜に、家のパソコンで）
1. Unityのプロジェクトの `Assets/Scripts/` に、このフォルダの `Assets/Scripts/Core` と `Assets/Scripts/Unity` をコピー。
2. `design/` の `cards.csv`、`enemies.csv`、`gems.csv` を、`Assets/Data/` にコピー。
3. シーンに空のオブジェクトを作り、`GameData` 部品をつける。3つのCSVを、インスペクターにドラッグ。
4. 再生すると、コンソールに「データを読みこんだ：カード 58、敵 17、宝石 12」と出れば成功。

## 中身
| ファイル | 役目 |
|---|---|
| Core/CsvTable.cs | CSVを読む。メモつきの数字（`2.2（…）`、`0.5%`）も読める |
| Core/Defs.cs | カード・敵・宝石の定義の形 |
| Core/DataLoader.cs | CSV → 定義。表を直すだけで数値が変わる |
| Core/CardPicker.cs | レベルアップの「カード3枚」を決める（強化45/スキル30/変化25、スキル上限4、専用60%、ペット35%など） |
| Unity/GameData.cs | UnityのTextAssetから読みこむ部品 |
| tests/ | Unity無しで動く確認（`mcs` と `mono`。決まりどおりにカードが出るかを、6000回引いて調べる） |

## 決まりごと（CLAUDE.mdのUnityの決まり）
- `Update` の中で `GetComponent` や `Find` を使わない。部品は `[SerializeField]` で受け取る。
- Unityに依存しない部分（`Core`）と、Unityの部品（`Unity`）を分けてある。

## 次に書くもの
敵の動き（スライム・コウモリ・弓兵・キノコ・ひろい屋・スライム王）、プレイヤーの移動とため（指1本）、自動攻撃、ペット。
