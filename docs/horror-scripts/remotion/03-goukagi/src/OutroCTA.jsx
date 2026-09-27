import {
  AbsoluteFill,
  Audio,
  staticFile,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import outroCta from "./outro_cta.json";

// 全話共通のエンディングCTA（真っ黒画面＋語り手の声で登録・高評価を促す）
// currentTime はこのセグメント内の相対時間（0スタート）

function OutroCaption({ cap, currentTime }) {
  const { start, end, text } = cap;
  const FADE = 0.15;
  if (currentTime < start - FADE || currentTime > end + FADE) return null;

  let opacity = 1;
  if (currentTime < start) {
    opacity = interpolate(currentTime, [start - FADE, start], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else if (currentTime > end - FADE) {
    opacity = interpolate(currentTime, [end - FADE, end + FADE], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  }

  return (
    <AbsoluteFill
      style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 140 }}
    >
      <div
        style={{
          opacity,
          fontFamily: "'IPAGothic', 'Noto Sans JP', sans-serif",
          fontWeight: 700,
          fontSize: 46,
          color: "#f5f5f0",
          textShadow: "0 2px 8px rgba(0,0,0,0.9)",
          textAlign: "center",
          maxWidth: "82%",
          lineHeight: 1.4,
          letterSpacing: 1,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
}

function ZoomWord({ zw, currentTime }) {
  const { word, start, end } = zw;
  const POP_IN = 0.35;
  const FADE_OUT = 0.25;
  if (currentTime < start || currentTime > end + FADE_OUT) return null;

  let scale;
  let opacity;
  if (currentTime < start + POP_IN) {
    // ズームイン（少しオーバーシュートしてから落ち着く）
    const t = (currentTime - start) / POP_IN;
    scale = interpolate(t, [0, 0.6, 1], [0.2, 1.18, 1.0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    opacity = interpolate(t, [0, 0.3], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else if (currentTime > end) {
    scale = 1.0;
    opacity = interpolate(currentTime, [end, end + FADE_OUT], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else {
    scale = 1.0;
    opacity = 1;
  }

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
          fontFamily: "'IPAGothic', 'Noto Sans JP', sans-serif",
          fontWeight: 900,
          fontSize: 130,
          color: "#ffffff",
          WebkitTextStroke: "4px #ff2b2b",
          textShadow: "0 0 30px rgba(255,43,43,0.85), 0 4px 10px rgba(0,0,0,0.9)",
          textAlign: "center",
          letterSpacing: 4,
        }}
      >
        {word}
      </div>
    </AbsoluteFill>
  );
}

export const OutroCTA = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;
  const totalEnd = outroCta.totalDuration + outroCta.tailPad;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Audio src={staticFile("outro-cta.wav")} />

      {outroCta.captions.map((cap, i) => (
        <OutroCaption key={i} cap={cap} currentTime={currentTime} />
      ))}

      {outroCta.zoomWords.map((zw, i) => (
        <ZoomWord key={i} zw={zw} currentTime={currentTime} />
      ))}

      {/* 最後にフェードアウト */}
      <AbsoluteFill
        style={{
          backgroundColor: "black",
          opacity: interpolate(
            currentTime,
            [totalEnd - 0.6, totalEnd],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          ),
        }}
      />
    </AbsoluteFill>
  );
};
