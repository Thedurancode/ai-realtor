import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Sequence,
  Img,
  Audio,
} from "remotion";
import { FONTS } from "./fonts";

export interface TimelineClip {
  id: string;
  start: number; // frame number
  duration: number; // frames
  type: "video" | "image" | "text" | "audio";
  src?: string; // for video/image/audio
  text?: string; // for text clips
  style?: React.CSSProperties;
  transition?: "none" | "fade" | "slide" | "slideRight" | "slideUp" | "zoom" | "kenBurns";
  volume?: number; // for audio clips
}

export interface TimelineTrack {
  id: string;
  type: "video" | "image" | "text" | "audio";
  clips: TimelineClip[];
}

export interface TimelineProps {
  [key: string]: unknown;
  tracks: TimelineTrack[];
  duration: number; // total frames
  fps?: number;
  width?: number;
  height?: number;
  backgroundColor?: string;
  showProgress?: boolean;
  progressColor?: string;
}

export const TimelineEditor: React.FC<TimelineProps> = ({
  tracks,
  duration,
  fps = 30,
  width = 1080,
  height = 1920,
  backgroundColor = "#000",
  showProgress = false,
  progressColor = "#3B82F6",
}) => {
  const frame = useCurrentFrame();
  const config = useVideoConfig();

  // Progress bar width
  const progressWidth = showProgress
    ? interpolate(frame, [0, duration], [0, width], { extrapolateRight: "clamp" })
    : 0;

  // Render a single clip with transitions
  const renderClip = (clip: TimelineClip, trackType: string) => {
    const relativeFrame = frame - clip.start;

    // Standard transition durations
    const fadeIn = 15;
    const fadeOut = 15;

    // Calculate opacity based on transition type
    let opacity = 1;
    let transform = "";
    let scale = 1;

    switch (clip.transition) {
      case "fade":
        if (relativeFrame < fadeIn) {
          opacity = interpolate(relativeFrame, [0, fadeIn], [0, 1]);
        } else if (relativeFrame > clip.duration - fadeOut) {
          opacity = interpolate(relativeFrame, [clip.duration - fadeOut, clip.duration], [1, 0]);
        }
        break;

      case "slide":
        if (relativeFrame < fadeIn) {
          const x = interpolate(relativeFrame, [0, fadeIn], [-width, 0]);
          transform = `translateX(${x}px)`;
        }
        if (relativeFrame > clip.duration - fadeOut) {
          opacity = interpolate(relativeFrame, [clip.duration - fadeOut, clip.duration], [1, 0]);
        }
        break;

      case "slideRight":
        if (relativeFrame < fadeIn) {
          const x = interpolate(relativeFrame, [0, fadeIn], [width, 0]);
          transform = `translateX(${x}px)`;
        }
        if (relativeFrame > clip.duration - fadeOut) {
          opacity = interpolate(relativeFrame, [clip.duration - fadeOut, clip.duration], [1, 0]);
        }
        break;

      case "slideUp":
        if (relativeFrame < fadeIn) {
          const y = interpolate(relativeFrame, [0, fadeIn], [height, 0]);
          transform = `translateY(${y}px)`;
        }
        if (relativeFrame > clip.duration - fadeOut) {
          opacity = interpolate(relativeFrame, [clip.duration - fadeOut, clip.duration], [1, 0]);
        }
        break;

      case "zoom":
        if (relativeFrame < fadeIn) {
          scale = interpolate(relativeFrame, [0, fadeIn], [0.8, 1]);
        } else if (relativeFrame > clip.duration - fadeOut) {
          scale = interpolate(relativeFrame, [clip.duration - fadeOut, clip.duration], [1, 1.2]);
        }
        opacity = interpolate(
          relativeFrame,
          [0, fadeIn, clip.duration - fadeOut, clip.duration],
          [0, 1, 1, 0],
          { extrapolateRight: "clamp" }
        );
        break;

      case "kenBurns":
        // Slow zoom + subtle pan for cinematic photo effect
        scale = interpolate(relativeFrame, [0, clip.duration], [1, 1.15], {
          extrapolateRight: "clamp",
        });
        const panX = interpolate(relativeFrame, [0, clip.duration], [0, -30], {
          extrapolateRight: "clamp",
        });
        transform = `translateX(${panX}px)`;
        opacity = interpolate(
          relativeFrame,
          [0, 20, clip.duration - 20, clip.duration],
          [0, 1, 1, 0],
          { extrapolateRight: "clamp" }
        );
        break;

      default: // "none"
        break;
    }

    // Render content based on clip type
    if (clip.type === "audio") {
      return clip.src ? <Audio src={clip.src} volume={clip.volume ?? 1} /> : null;
    }

    if (clip.type === "image") {
      return (
        <AbsoluteFill>
          <Img
            src={clip.src || ""}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${scale}) ${transform}`,
            }}
          />
        </AbsoluteFill>
      );
    }

    if (clip.type === "video") {
      return (
        <AbsoluteFill>
          <video
            src={clip.src}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${scale}) ${transform}`,
            }}
          />
        </AbsoluteFill>
      );
    }

    if (clip.type === "text") {
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
              fontFamily: clip.style?.fontFamily || FONTS.heading,
              textAlign: (clip.style?.textAlign as any) || "center",
              textShadow: clip.style?.textShadow || "2px 2px 8px rgba(0,0,0,0.8)",
              padding: "0 60px",
              margin: 0,
              ...clip.style,
            }}
          >
            {clip.text}
          </h1>
        </AbsoluteFill>
      );
    }

    return null;
  };

  // Render each track
  const renderTrack = (track: TimelineTrack) => {
    return track.clips.map((clip) => {
      // Check if clip is visible at current frame
      if (frame < clip.start || frame >= clip.start + clip.duration) {
        return null;
      }

      const relativeFrame = frame - clip.start;
      const fadeIn = 15;
      const fadeOut = 15;

      // Wrapper opacity for all clip types
      let wrapperOpacity = 1;
      let wrapperTransform = "";

      switch (clip.transition) {
        case "fade":
          if (relativeFrame < fadeIn) {
            wrapperOpacity = interpolate(relativeFrame, [0, fadeIn], [0, 1]);
          } else if (relativeFrame > clip.duration - fadeOut) {
            wrapperOpacity = interpolate(relativeFrame, [clip.duration - fadeOut, clip.duration], [1, 0]);
          }
          break;
        case "slide":
          if (relativeFrame < fadeIn) {
            wrapperTransform = `translateX(${interpolate(relativeFrame, [0, fadeIn], [-width, 0])}px)`;
          }
          break;
        case "slideRight":
          if (relativeFrame < fadeIn) {
            wrapperTransform = `translateX(${interpolate(relativeFrame, [0, fadeIn], [width, 0])}px)`;
          }
          break;
        case "slideUp":
          if (relativeFrame < fadeIn) {
            wrapperTransform = `translateY(${interpolate(relativeFrame, [0, fadeIn], [height, 0])}px)`;
          }
          break;
        default:
          break;
      }

      return (
        <Sequence
          key={clip.id}
          from={clip.start}
          durationInFrames={clip.duration}
        >
          <AbsoluteFill
            style={{
              opacity: wrapperOpacity,
              transform: wrapperTransform,
            }}
          >
            {renderClip(clip, track.type)}
          </AbsoluteFill>
        </Sequence>
      );
    });
  };

  return (
    <AbsoluteFill style={{ backgroundColor }}>
      {/* Render tracks in order — later tracks overlay earlier ones */}
      {tracks.map((track) => (
        <React.Fragment key={track.id}>
          {renderTrack(track)}
        </React.Fragment>
      ))}

      {/* Optional progress bar */}
      {showProgress && (
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            width: progressWidth,
            height: 4,
            backgroundColor: progressColor,
          }}
        />
      )}
    </AbsoluteFill>
  );
};
