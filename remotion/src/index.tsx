import { Composition, registerRoot } from "remotion";
import { CaptionedReel } from "./CaptionedReel";
import { Slideshow } from "./Slideshow";
import { TimelineEditor } from "./TimelineEditor";
import { PropertyShowcase } from "./PropertyShowcase";

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
      <Composition
        id="PropertyShowcase"
        component={PropertyShowcase}
        durationInFrames={900} // 30 seconds default, will be calculated based on photos
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          logoUrl: "",
          companyName: "Your Real Estate Experts",
          tagline: "Finding Your Dream Home",
          primaryColor: "#1E40AF",
          secondaryColor: "#3B82F6",
          propertyAddress: "123 Main St",
          propertyPrice: "$500,000",
          propertyDetails: {
            bedrooms: 3,
            bathrooms: 2,
            squareFeet: 2000,
            propertyType: "House"
          },
          propertyPhotos: [],
          audioUrl: "",
          logoDuration: 90,
          photoDuration: 120
        }}
      />
    </>
  );
};

registerRoot(RemotionVideo);
