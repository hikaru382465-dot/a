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
import scenes from "./scenes.json";

const FADE = 0.6; // seconds crossfade between background scenes
const CAP_FADE = 0.12; // seconds caption fade in/out

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
  // slow Ken Burns zoom, alternate direction by index for variety
  const zoomIn = index % 2 === 0;
  const scale = zoomIn
    ? interpolate(t, [0, 1], [1.0, 1.12])
    : interpolate(t, [0, 1], [1.12, 1.0]);

  return (
    <AbsoluteFill style={{ opacity }}>
      <AbsoluteFill
        style={{
          transform: `scale(${scale})`,
          transformOrigin: "center center",
        }}
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
      {/* vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.75) 100%)",
        }}
      />
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
    shakeX = Math.sin(localT * 45) * 3 + Math.sin(localT * 13) * 1.5;
    shakeY = Math.cos(localT * 37) * 2;
    scale = 1.28;
  }

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 130,
      }}
    >
      <div
        style={{
          opacity,
          transform: `translate(${shakeX}px, ${shakeY}px) scale(${scale})`,
          fontFamily: "'IPAGothic', 'Noto Sans JP', sans-serif",
          fontWeight: 700,
          fontSize: emphasis ? 64 : 50,
          color: emphasis ? "#ff2b2b" : "#f5f5f0",
          textShadow: emphasis
            ? "0 0 18px rgba(255,0,0,0.85), 0 2px 6px rgba(0,0,0,0.9)"
            : "0 2px 8px rgba(0,0,0,0.9), 0 0 2px rgba(0,0,0,0.9)",
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

const reveal = scenes.captions.find((c) => c.line === 47);
const BGM_BASE_VOLUME = 0.16;

function bgmVolumeAt(t, fps) {
  const totalEnd = scenes.totalDuration + scenes.outroPad;
  // fade in at the very start
  let v = interpolate(t, [0, 2.5], [0, BGM_BASE_VOLUME], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // duck to silence around the big reveal line, then fade back in
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
  // fade out at the very end
  v = Math.min(
    v,
    interpolate(t, [totalEnd - 2.5, totalEnd], [BGM_BASE_VOLUME, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );
  return Math.max(0, v);
}

export const HorrorVideo = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const currentTime = frame / fps;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {scenes.scenes.map((scene, i) => (
        <SceneImage key={i} scene={scene} index={i} currentTime={currentTime} />
      ))}

      {scenes.captions.map((cap, i) => (
        <Caption key={i} cap={cap} currentTime={currentTime} />
      ))}

      <Audio src={staticFile("narration.wav")} />

      <Sequence from={0} durationInFrames={durationInFrames}>
        <Audio
          src={staticFile("bgm.mp3")}
          loop
          volume={(f) => bgmVolumeAt(f / fps, fps)}
        />
      </Sequence>

      {scenes.sfx.map((s, i) => (
        <Sequence key={i} from={Math.round(s.time * fps)}>
          <Audio src={staticFile("koton.wav")} volume={1.1} />
        </Sequence>
      ))}

      {/* fade to black at the very end */}
      <AbsoluteFill
        style={{
          backgroundColor: "black",
          opacity: interpolate(
            currentTime,
            [scenes.totalDuration + scenes.outroPad - 1.2, scenes.totalDuration + scenes.outroPad],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          ),
        }}
      />
    </AbsoluteFill>
  );
};
