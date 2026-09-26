import {
  AbsoluteFill,
  Audio,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Sequence,
} from "remotion";
import scenes from "./short_scenes.json";

const FADE = 0.6;
const CAP_FADE = 0.12;

function SceneImage({ scene, index, currentTime }) {
  const { start, end, image } = scene;
  const dur = end - start;
  let opacity = 0;
  if (currentTime >= start - FADE && currentTime <= end + FADE) {
    if (currentTime < start) {
      opacity = interpolate(currentTime, [start - FADE, start], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
    } else if (currentTime > end) {
      opacity = interpolate(currentTime, [end, end + FADE], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
    } else {
      opacity = 1;
    }
  }
  if (opacity <= 0) return null;

  const elapsed = Math.min(Math.max(currentTime - start, 0), dur);
  const t = dur > 0 ? elapsed / dur : 0;
  const zoomIn = index % 2 === 0;
  const scale = zoomIn
    ? interpolate(t, [0, 1], [1.05, 1.22])
    : interpolate(t, [0, 1], [1.22, 1.05]);

  return (
    <AbsoluteFill style={{ opacity }}>
      <AbsoluteFill
        style={{ transform: `scale(${scale})`, transformOrigin: "center center" }}
      >
        <Img
          src={staticFile(`images/${image}`)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "brightness(0.55) saturate(0.9)",
          }}
        />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(0,0,0,0) 40%, rgba(0,0,0,0.8) 100%)",
        }}
      />
    </AbsoluteFill>
  );
}

function TitleBar({ title }) {
  if (!title) return null;
  const m = title.match(/^(【[^】]+】)(.*)$/);
  const bracket = m ? m[1] : null;
  const rest = m ? m[2] : title;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center" }}>
      <div
        style={{
          marginTop: 90,
          width: "88%",
          textAlign: "center",
          fontFamily: "'IPAGothic', 'Noto Sans JP', sans-serif",
          fontWeight: 700,
          lineHeight: 1.35,
          textShadow: "0 2px 8px rgba(0,0,0,0.9), 0 0 3px rgba(0,0,0,0.9)",
        }}
      >
        {bracket && (
          <span style={{ color: "#ff2b2b", fontSize: 56, fontWeight: 900 }}>
            {bracket}
            <br />
          </span>
        )}
        <span style={{ color: "#f5f5f0", fontSize: 50 }}>{rest}</span>
      </div>
    </AbsoluteFill>
  );
}

function Caption({ cap, currentTime }) {
  const { start, end, text, emphasis } = cap;
  if (currentTime < start - CAP_FADE || currentTime > end + 0.15) return null;

  let opacity = 1;
  if (currentTime < start) {
    opacity = interpolate(currentTime, [start - CAP_FADE, start], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else if (currentTime > end - CAP_FADE) {
    opacity = interpolate(currentTime, [end - CAP_FADE, end + 0.15], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  }

  let shakeX = 0;
  let shakeY = 0;
  let scale = 1;
  if (emphasis) {
    const localT = currentTime - start;
    shakeX = Math.sin(localT * 45) * 2.5 + Math.sin(localT * 13) * 1.2;
    shakeY = Math.cos(localT * 37) * 1.6;
    scale = 1.22;
  }

  return (
    <AbsoluteFill
      style={{ justifyContent: "center", alignItems: "center" }}
    >
      <div
        style={{
          opacity,
          transform: `translate(${shakeX}px, ${shakeY}px) scale(${scale})`,
          fontFamily: "'IPAGothic', 'Noto Sans JP', sans-serif",
          fontWeight: 700,
          fontSize: emphasis ? 52 : 42,
          color: emphasis ? "#ff2b2b" : "#f5f5f0",
          textShadow: emphasis
            ? "0 0 16px rgba(255,0,0,0.85), 0 2px 6px rgba(0,0,0,0.9)"
            : "0 2px 8px rgba(0,0,0,0.9), 0 0 2px rgba(0,0,0,0.9)",
          textAlign: "center",
          maxWidth: "90%",
          lineHeight: 1.45,
          letterSpacing: 1,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
}

const reveal = scenes.captions.find(
  (c) => c.text === "「次はあなたの番です」"
);
const BGM_BASE_VOLUME = 0.045;

function bgmVolumeAt(t) {
  const totalEnd = scenes.totalDuration;
  let v = interpolate(t, [0, 1.5], [0, BGM_BASE_VOLUME], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  if (reveal) {
    const duckStart = reveal.start - 0.6;
    const duckOutEnd = reveal.start - 0.1;
    const duckInStart = reveal.end + 0.2;
    const duckInEnd = reveal.end + 1.4;
    if (t > duckStart && t < duckInEnd) {
      if (t < duckOutEnd) {
        v = interpolate(t, [duckStart, duckOutEnd], [v, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
      } else if (t < duckInStart) {
        v = 0;
      } else {
        v = interpolate(t, [duckInStart, duckInEnd], [0, BGM_BASE_VOLUME], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
      }
    }
  }
  v = Math.min(
    v,
    interpolate(t, [totalEnd - 1.8, totalEnd], [BGM_BASE_VOLUME, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );
  return Math.max(0, v);
}

export const HorrorShort = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const currentTime = frame / fps;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {scenes.scenes.map((scene, i) => (
        <SceneImage key={i} scene={scene} index={i} currentTime={currentTime} />
      ))}

      <TitleBar title={scenes.title} />

      {scenes.captions.map((cap, i) => (
        <Caption key={i} cap={cap} currentTime={currentTime} />
      ))}

      <Audio src={staticFile("narration_short.wav")} />

      <Sequence from={0} durationInFrames={durationInFrames}>
        <Audio src={staticFile("bgm.mp3")} loop volume={bgmVolumeAt(currentTime)} />
      </Sequence>

      {scenes.sfx.map((s, i) => (
        <Sequence key={i} from={Math.round(s.time * fps)}>
          <Audio src={staticFile("koton.wav")} volume={1.1} />
        </Sequence>
      ))}

      <AbsoluteFill
        style={{
          backgroundColor: "black",
          opacity: interpolate(
            currentTime,
            [scenes.totalDuration - 1.0, scenes.totalDuration],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          ),
        }}
      />
    </AbsoluteFill>
  );
};
