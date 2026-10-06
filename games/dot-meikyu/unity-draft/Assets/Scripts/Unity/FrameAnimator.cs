using System;
using UnityEngine;

namespace DotMeikyu
{
    [Serializable]
    public sealed class FrameClip
    {
        public string name = "attack";
        public Sprite[] frames;
        [Tooltip("コマごとの長さ（秒）。コマ数と同じ数。ためを長く、振りを短く、当たりを少し長く")]
        public float[] durations;
        public bool loop;
        [Tooltip("この番号のコマに来たとき、HitFrame を知らせる（当たりのコマ）。-1で無し")]
        public int hitFrame = -1;
    }

    // コマごとに長さを変えて絵を切りかえる部品（スプライトのアニメ）
    // ・Unityの標準アニメは、全コマ同じ長さになりがち。攻撃は「ため→一瞬で振る→当たりで止まる」の強弱が大事
    // ・時間は unscaledDeltaTime ではなく deltaTime を使う（ヒットストップ中は、いっしょに止まる）
    public sealed class FrameAnimator : MonoBehaviour
    {
        [SerializeField] SpriteRenderer target;
        [SerializeField] FrameClip[] clips;

        public event Action<string> HitFrame;          // 当たりのコマに来た
        public event Action<string> ClipFinished;      // ループしないクリップが終わった

        FrameClip current; int index; float timer; bool playing;

        public void Play(string clipName)
        {
            current = null;
            for (int i = 0; i < clips.Length; i++) if (clips[i].name == clipName) { current = clips[i]; break; }
            if (current == null || current.frames == null || current.frames.Length == 0) return;
            index = 0; timer = 0f; playing = true; Show();
        }

        void Show()
        {
            target.sprite = current.frames[index];
            if (index == current.hitFrame && HitFrame != null) HitFrame(current.name);
        }

        void Update()
        {
            if (!playing) return;
            timer += Time.deltaTime;
            float len = current.durations != null && index < current.durations.Length ? current.durations[index] : 0.1f;
            while (timer >= len)
            {
                timer -= len; index++;
                if (index >= current.frames.Length)
                {
                    if (current.loop) index = 0; else { playing = false; index = current.frames.Length - 1; if (ClipFinished != null) ClipFinished(current.name); return; }
                }
                Show(); len = current.durations != null && index < current.durations.Length ? current.durations[index] : 0.1f;
            }
        }
    }
}
