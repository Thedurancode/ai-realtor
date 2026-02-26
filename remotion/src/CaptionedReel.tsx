import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export interface CaptionedReelProps {
  title: string;
  subtitle: string;
  backgroundUrl: string;
  overlayColor: string;
  overlayOpacity: number;
}

export const CaptionedReel: React.FC<CaptionedReelProps> = ({
  title,
  subtitle,
  backgroundUrl,
  overlayColor,
  overlayOpacity,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Text animations
  const titleOpacity = spring({
    frame: frame - 30,
    fps,
    config: {
      damping: 100,
      stiffness: 200,
    },
  });

  const subtitleOpacity = spring({
    frame: frame - 60,
    fps,
    config: {
      damping: 100,
      stiffness: 200,
    },
  });

  const scale = interpolate(frame, [0, 30], [0.8, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Background image or video */}
      {backgroundUrl ? (
        <AbsoluteFill>
          <img
            src={backgroundUrl}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill style={{ backgroundColor: "#1a1a1a" }} />
      )}

      {/* Dark overlay */}
      <AbsoluteFill
        style={{
          backgroundColor: overlayColor,
          opacity: overlayOpacity,
        }}
      />

      {/* Text content */}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          textAlign: "center",
        }}
      >
        <div
          style={{
            transform: `scale(${scale})`,
            opacity: titleOpacity,
          }}
        >
          <h1
            style={{
              fontSize: 80,
              fontWeight: "bold",
              color: "#fff",
              margin: 0,
              textShadow: "2px 2px 8px rgba(0,0,0,0.5)",
              fontFamily: "Arial, sans-serif",
            }}
          >
            {title}
          </h1>
        </div>

        <div
          style={{
            marginTop: 20,
            opacity: subtitleOpacity,
          }}
        >
          <h2
            style={{
              fontSize: 50,
              fontWeight: "normal",
              color: "#fff",
              margin: 0,
              textShadow: "2px 2px 8px rgba(0,0,0,0.5)",
              fontFamily: "Arial, sans-serif",
            }}
          >
            {subtitle}
          </h2>
        </div>

        {/* CTA at the end */}
        {frame > 200 && (
          <div
            style={{
              position: "absolute",
              bottom: 100,
              opacity: interpolate(frame, [200, 230], [0, 1], {
                extrapolateRight: "clamp",
              }),
            }}
          >
            <p
              style={{
                fontSize: 40,
                color: "#fff",
                margin: 0,
                backgroundColor: "rgba(59, 130, 246, 0.9)",
                padding: "15px 30px",
                borderRadius: 10,
                fontWeight: "bold",
              }}
            >
              Schedule a Viewing
            </p>
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
