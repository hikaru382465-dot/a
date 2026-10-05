// Unityが無い環境で、コードの書き方のまちがいを調べるための、見せかけの部品
namespace UnityEngine
{
    public class MonoBehaviour { }
    public class TextAsset { public string text; }
    public class SerializeFieldAttribute : System.Attribute { }
    public static class Debug { public static void Log(object o) { System.Console.WriteLine(o); } }
}
