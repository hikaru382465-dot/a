// Unityが無い環境で、コードの書き方のまちがいを調べるための、見せかけの部品（本物とは動きがちがう）
using System;
namespace UnityEngine
{
    public struct Vector2
    {
        public float x, y; public Vector2(float x, float y) { this.x = x; this.y = y; }
        public static Vector2 zero { get { return new Vector2(0, 0); } }
        public float sqrMagnitude { get { return x * x + y * y; } }
        public float magnitude { get { return (float)Math.Sqrt(sqrMagnitude); } }
        public Vector2 normalized { get { float m = magnitude; return m > 1e-6f ? new Vector2(x / m, y / m) : zero; } }
        public static Vector2 operator -(Vector2 a, Vector2 b) { return new Vector2(a.x - b.x, a.y - b.y); }
    }
    public struct Vector3
    {
        public float x, y, z; public Vector3(float x, float y, float z) { this.x = x; this.y = y; this.z = z; }
        public static Vector3 operator +(Vector3 a, Vector3 b) { return new Vector3(a.x + b.x, a.y + b.y, a.z + b.z); }
        public static Vector3 operator *(Vector3 a, float k) { return new Vector3(a.x * k, a.y * k, a.z * k); }
    }
    public struct Rect { public Rect(float a, float b, float c, float d) { } }
    public class Transform { public Vector3 position; }
    public class SpriteRenderer { public bool flipX; }
    public struct Quaternion { public static Quaternion identity { get { return new Quaternion(); } } }
    public class GameObject { public Transform transform = new Transform(); }
    public class MonoBehaviour
    {
        public Transform transform = new Transform();
        public static GameObject Instantiate(GameObject o, Vector3 p, Quaternion q) { return new GameObject(); }
        public static void Destroy(GameObject o) { }
    }
    public class TextAsset { public string text; }
    public class SerializeFieldAttribute : Attribute { }
    public class HeaderAttribute : Attribute { public HeaderAttribute(string s) { } }
    public static class Debug { public static void Log(object o) { Console.WriteLine(o); } }
    public static class Time { public static float deltaTime = 0.016f, time = 0f; }
    public static class Screen { public static float dpi = 160f; }
    public static class Mathf
    {
        public static bool Approximately(float a, float b) { return Math.Abs(a - b) < 1e-6f; }
        public static float Max(float a, float b) { return Math.Max(a, b); }
        public static float Abs(float a) { return Math.Abs(a); }
        public static int RoundToInt(float f) { return (int)Math.Round(f); }
    }
    public static class GUI { public static void Label(Rect r, string s) { } }
}
namespace UnityEngine.InputSystem
{
    public class ButtonControl { public bool isPressed; }
    public class Vector2Control { public Vector2 value; public Vector2 ReadValue() { return value; } }
    public class Keyboard
    {
        public static Keyboard current;
        public ButtonControl aKey = new ButtonControl(), dKey = new ButtonControl(), sKey = new ButtonControl(), wKey = new ButtonControl(),
            leftArrowKey = new ButtonControl(), rightArrowKey = new ButtonControl(), upArrowKey = new ButtonControl(), downArrowKey = new ButtonControl(), spaceKey = new ButtonControl();
    }
    public class Pointer { public static Pointer current; public ButtonControl press = new ButtonControl(); public Vector2Control position = new Vector2Control(); }
}
namespace UnityEngine { public static class Application { public static string persistentDataPath { get { return "/tmp"; } } } }
