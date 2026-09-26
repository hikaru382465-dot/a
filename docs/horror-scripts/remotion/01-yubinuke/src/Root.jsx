import { Composition } from "remotion";
import { HorrorVideo } from "./Video";
import { HorrorShort } from "./ShortVideo";
import scenes from "./scenes.json";
import shortScenes from "./short_scenes.json";

const FPS = 30;
const totalSeconds = scenes.totalDuration + scenes.outroPad;
const DURATION_IN_FRAMES = Math.ceil(totalSeconds * FPS);
const SHORT_DURATION_IN_FRAMES = Math.ceil(shortScenes.totalDuration * FPS);

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="Yubinuke01"
        component={HorrorVideo}
        durationInFrames={DURATION_IN_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="Yubinuke01Short"
        component={HorrorShort}
        durationInFrames={SHORT_DURATION_IN_FRAMES}
        fps={FPS}
        width={1080}
        height={1920}
      />
    </>
  );
};
