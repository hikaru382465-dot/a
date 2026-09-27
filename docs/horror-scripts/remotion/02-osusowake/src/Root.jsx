import { Composition } from "remotion";
import { FullEpisode, STORY_FRAMES } from "./FullEpisode";
import { HorrorShort } from "./ShortVideo";
import outroCta from "./outro_cta.json";
import shortScenes from "./short_scenes.json";

const FPS = 30;
const OUTRO_FRAMES = Math.ceil(
  (outroCta.totalDuration + outroCta.tailPad) * FPS
);
const DURATION_IN_FRAMES = STORY_FRAMES + OUTRO_FRAMES;
const SHORT_DURATION_IN_FRAMES = Math.ceil(
  (shortScenes.totalDuration + shortScenes.outroPad) * FPS
);

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
      <Composition
        id="Osusowake02Short"
        component={HorrorShort}
        durationInFrames={SHORT_DURATION_IN_FRAMES}
        fps={FPS}
        width={1080}
        height={1920}
      />
    </>
  );
};
