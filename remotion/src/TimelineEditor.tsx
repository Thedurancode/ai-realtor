import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Sequence,
} from "remotion";

export interface TimelineClip {
  id: string;
  start: number; // frame number
  duration: number; // frames
  type: "video" | "image" | "text";
  src?: string; // for video/image
  text?: string; // for text clips
  style?: React.CSSProperties;
  transition?: "none" | "fade" | "slide" | "zoom";
}

export interface TimelineTrack {
  id: string;
  type: "video" | "image" | "text" | "audio";
  clips: TimelineClip[];
}

export interface TimelineProps {
  tracks: TimelineTrack[];
  duration: number; // total frames
  fps?: number;
  width?: number;
  height?: number;
}

export const TimelineEditor: React.FC<TimelineProps> = ({
  tracks,
  duration,
  fps = 30,
  width = 1080,
  height = 1920,
}) => {
  const frame = useCurrentFrame();

  // Render each track
  const renderTrack = (track: TimelineTrack) => {
    return track.clips.map((clip) => {
      // Check if this clip should be visible at current frame
      if (frame < clip.start || frame >= clip.start + clip.duration) {
        return null;
      }

      const relativeFrame = frame - clip.start;

      // Handle transitions
      let opacity = 1;
      let transform = "";
      let scale = 1;

      if (clip.transition === "fade") {
        // Fade in/out
        const fadeInDuration = 15;
        const fadeOutDuration = 15;

        if (relativeFrame < fadeInDuration) {
          opacity = interpolate(relativeFrame, [0, fadeInDuration], [0, 1]);
        } else if (relativeFrame > clip.duration - fadeOutDuration) {
          opacity = interpolate(
            relativeFrame,
            [clip.duration - fadeOutDuration, clip.duration],
            [1, 0]
          );
        }
      } else if (clip.transition === "slide") {
        // Slide in from left
        const slideDuration = 15;
        if (relativeFrame < slideDuration) {
          const x = interpolate(relativeFrame, [0, slideDuration], [-width, 0]);
          transform = `translateX(${x}px)`;
        }
      } else if (clip.transition === "zoom") {
        // Zoom in/out
        const zoomDuration = 15;
        if (relativeFrame < zoomDuration) {
          scale = interpolate(relativeFrame, [0, zoomDuration], [0.8, 1]);
        } else if (relativeFrame > clip.duration - zoomDuration) {
          scale = interpolate(
            relativeFrame,
            [clip.duration - zoomDuration, clip.duration],
            [1, 1.2]
          );
        }
      }

      // Render clip content
      const content = (() => {
        if (clip.type === "video" || clip.type === "image") {
          return (
            <AbsoluteFill
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "#000",
              }}
            >
              {clip.type === "image" ? (
                <img
                  src={clip.src}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    transform: `scale(${scale})`,
                  }}
                />
              ) : (
                <video
                  src={clip.src}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    transform: `scale(${scale})`,
                  }}
                />
              )}
            </AbsoluteFill>
          );
        } else if (clip.type === "text") {
          return (
            <AbsoluteFill
              style={{
                display: "flex",
                alignItems: clip.style?.alignItems || "center",
                justifyContent: clip.style?.justifyContent || "center",
                pointerEvents: "none",
              }}
            >
                <h1
                  style={{
                    fontSize: clip.style?.fontSize || 80,
                    fontWeight: clip.style?.fontWeight || "bold",
                    color: clip.style?.color || "#fff",
                    fontFamily: clip.style?.fontFamily || "Arial",
                    textAlign: clip.style?.textAlign || "center",
                    textShadow: clip.style?.textShadow || "2px 2px 8px rgba(0,0,0,0.8)",
                    ...clip.style,
                  }}
                >
                  {clip.text}
                </h1>
            </AbsoluteFill>
          );
        }
        return null;
      })();

      return (
        <Sequence
          key={clip.id}
          from={clip.start}
          durationInFrames={clip.duration}
        >
          <AbsoluteFill
            style={{
              opacity,
              transform,
            }}
          >
            {content}
          </AbsoluteFill>
        </Sequence>
      );
    });
  };

  return (
    <AbsoluteFill
      style={{
        width,
        height,
        backgroundColor: "#000",
      }}
    >
      {tracks.map((track) => (
        <React.Fragment key={track.id}>
          {renderTrack(track)}
        </React.Fragment>
      ))}
    </AbsoluteFill>
  );
};
