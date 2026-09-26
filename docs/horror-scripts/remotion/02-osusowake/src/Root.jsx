import { Composition } from "remotion";
import { FullEpisode, STORY_FRAMES } from "./FullEpisode";
import outroCta from "./outro_cta.json";

const FPS = 30;
const OUTRO_FRAMES = Math.ceil(
  (outroCta.totalDuration + outroCta.tailPad) * FPS
);
const DURATION_IN_FRAMES = STORY_FRAMES + OUTRO_FRAMES;

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="Osusowake02"
        component={FullEpisode}
        durationInFrames={DURATION_IN_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
      />
    </>
  );
};
