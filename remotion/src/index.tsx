import { Composition, registerRoot } from "remotion";
import { CaptionedReel } from "./CaptionedReel";
import { Slideshow, SlideshowProps } from "./Slideshow";
import { TimelineEditor, TimelineProps } from "./TimelineEditor";
import { PropertyShowcase, PropertyShowcaseProps } from "./PropertyShowcase";
import { CinematicEventRecap, EventRecapProps } from "./CinematicEventRecap";

// Dynamic duration calculators
const calculatePropertyShowcaseDuration = ({
  props,
}: {
  props: Record<string, unknown>;
}) => {
  const p = props as unknown as PropertyShowcaseProps;
  const logoDuration = p.logoDuration || 90;
  const photoDuration = p.photoDuration || 120;
  const outroDuration = p.outroDuration || 120;
  const photoCount = p.propertyPhotos?.length || 0;
  const transition = 30; // gap between logo and photos
  const frames = logoDuration + transition + photoCount * photoDuration + outroDuration;
  return { durationInFrames: Math.max(frames, 300) }; // minimum 10 seconds
};

const calculateEventRecapDuration = ({
  props,
}: {
  props: Record<string, unknown>;
}) => {
  const p = props as unknown as EventRecapProps;
  const introDuration = p.introDuration || 120;
  const photoDuration = p.photoDuration || 90;
  const outroDuration = p.outroDuration || 120;
  const photoCount = p.photos?.length || 0;
  const frames = introDuration + photoCount * photoDuration + outroDuration;
  return { durationInFrames: Math.max(frames, 300) };
};

const calculateSlideshowDuration = ({
  props,
}: {
  props: Record<string, unknown>;
}) => {
  const p = props as unknown as SlideshowProps;
  const imageCount = p.images?.length || 0;
  const dur = p.durationPerImage || 90;
  const trans = p.transitionDuration || 15;
  const frames = imageCount * (dur + trans);
  return { durationInFrames: Math.max(frames, 300) };
};

const calculateTimelineDuration = ({
  props,
}: {
  props: Record<string, unknown>;
}) => {
  const p = props as unknown as TimelineProps;
  return { durationInFrames: p.duration || 900 };
};

export const RemotionVideo: React.FC = () => {
  return (
    <>
      <Composition
        id="CaptionedReel"
        component={CaptionedReel}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          title: "Amazing Property!",
          subtitle: "123 Main St",
          backgroundUrl: "",
          overlayColor: "#000000",
          overlayOpacity: 0.3,
          logoUrl: "",
          companyName: "Emprezario Inc",
          primaryColor: "#1E40AF",
          accentColor: "#3B82F6",
          ctaText: "Schedule a Viewing",
          musicUrl: "",
          musicVolume: 0.5,
          voiceoverUrl: "",
        }}
      />
      <Composition
        id="Slideshow"
        component={Slideshow}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calculateSlideshowDuration}
        defaultProps={{
          images: [],
          durationPerImage: 90,
          transitionDuration: 15,
          showTitle: true,
          title: "Property Tour",
          showMusic: false,
          musicUrl: "",
          musicVolume: 0.6,
        }}
      />
      <Composition
        id="TimelineEditor"
        component={TimelineEditor}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calculateTimelineDuration}
        defaultProps={{
          tracks: [],
          duration: 900,
          fps: 30,
          width: 1080,
          height: 1920,
        }}
      />
      <Composition
        id="PropertyShowcase"
        component={PropertyShowcase}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calculatePropertyShowcaseDuration}
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
            propertyType: "House",
          },
          propertyPhotos: [],
          audioUrl: "",
          agentName: "Ed Duran",
          agentPhone: "(201) 300-5189",
          agentEmail: "ed@emprezario.com",
          ctaText: "Schedule a Showing",
          logoDuration: 90,
          photoDuration: 120,
          outroDuration: 120,
        }}
      />
      <Composition
        id="CinematicEventRecap"
        component={CinematicEventRecap}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calculateEventRecapDuration}
        defaultProps={{
          eventName: "Open House Mixer",
          eventDate: "March 15, 2026",
          eventLocation: "Miami Beach, FL",
          eventDescription: "",
          logoUrl: "",
          hostName: "Ed Duran",
          primaryColor: "#0F172A",
          accentColor: "#F59E0B",
          photos: [],
          musicUrl: "",
          musicVolume: 0.8,
          introDuration: 120,
          photoDuration: 90,
          outroDuration: 120,
          photoCaptions: [],
        }}
      />
    </>
  );
};

registerRoot(RemotionVideo);
