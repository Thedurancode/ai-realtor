import { Composition } from "remotion";
import { CaptionedReel } from "./CaptionedReel";
import { Slideshow } from "./Slideshow";
import { TimelineEditor } from "./TimelineEditor";

export const RemotionVideo: React.FC = () => {
  return (
    <>
      <Composition
        id="CaptionedReel"
        component={CaptionedReel}
        durationInFrames={300} // 10 seconds at 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          title: "Amazing Property!",
          subtitle: "123 Main St",
          backgroundUrl: "",
          overlayColor: "#000000",
          overlayOpacity: 0.3
        }}
      />
      <Composition
        id="Slideshow"
        component={Slideshow}
        durationInFrames={450} // 15 seconds at 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          images: [],
          durationPerImage: 90, // 3 seconds per image
          transitionDuration: 15, // 0.5 seconds
          showTitle: true,
          title: "Property Tour",
          showMusic: false
        }}
      />
      <Composition
        id="TimelineEditor"
        component={TimelineEditor}
        durationInFrames={900} // 30 seconds default, will be overridden by props
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          tracks: [],
          duration: 900,
          fps: 30,
          width: 1080,
          height: 1920
        }}
      />
    </>
  );
};
