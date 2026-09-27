import { AbsoluteFill, Sequence } from "remotion";
import { HorrorVideo } from "./Video";
import { OutroCTA } from "./OutroCTA";
import scenes from "./scenes.json";

const FPS = 30;
export const STORY_FRAMES = Math.ceil(
  (scenes.totalDuration + scenes.outroPad) * FPS
);

export const FullEpisode = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Sequence from={0} durationInFrames={STORY_FRAMES}>
        <HorrorVideo />
      </Sequence>
      <Sequence from={STORY_FRAMES}>
        <OutroCTA />
      </Sequence>
    </AbsoluteFill>
  );
};
