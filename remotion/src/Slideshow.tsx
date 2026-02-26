import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Sequence,
} from "remotion";

export interface SlideshowProps {
  images: string[];
  durationPerImage: number;
  transitionDuration: number;
  showTitle: boolean;
  title: string;
  showMusic: boolean;
}

export const Slideshow: React.FC<SlideshowProps> = ({
  images,
  durationPerImage,
  transitionDuration,
  showTitle,
  title,
  showMusic,
}) => {
  const frame = useCurrentFrame();

  if (images.length === 0) {
    return (
      <AbsoluteFill style={{ backgroundColor: "#000", justifyContent: "center", alignItems: "center" }}>
        <h1 style={{ color: "#fff", fontSize: 60 }}>No images provided</h1>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Title overlay */}
      {showTitle && (
        <AbsoluteFill
          style={{
            pointerEvents: "none",
            justifyContent: "flex-start",
            alignItems: "center",
            paddingTop: 80,
          }}
        >
          <h1
            style={{
              fontSize: 70,
              fontWeight: "bold",
              color: "#fff",
              margin: 0,
              textShadow: "3px 3px 10px rgba(0,0,0,0.8)",
              fontFamily: "Arial, sans-serif",
              backgroundColor: "rgba(0,0,0,0.5)",
              padding: "10px 30px",
              borderRadius: 10,
            }}
          >
            {title}
          </h1>
        </AbsoluteFill>
      )}

      {/* Slideshow */}
      {images.map((imageUrl, index) => {
        const from = index * (durationPerImage + transitionDuration);
        const to = from + durationPerImage + transitionDuration * 2;

        // Skip if outside timeline
        if (frame < from - transitionDuration || frame > to) {
          return null;
        }

        // Opacity for cross-fade transition
        let opacity = 1;
        if (frame < from) {
          opacity = interpolate(frame, [from - transitionDuration, from], [0, 1]);
        } else if (frame > from + durationPerImage) {
          opacity = interpolate(
            frame,
            [from + durationPerImage, from + durationPerImage + transitionDuration],
            [1, 0]
          );
        }

        // Scale animation for subtle zoom effect
        const scale = interpolate(frame, [from, from + durationPerImage], [1, 1.1], {
          extrapolateRight: "clamp",
        });

        return (
          <Sequence
            key={index}
            from={from - transitionDuration}
            durationInFrames={durationPerImage + transitionDuration * 2}
          >
            <AbsoluteFill style={{ opacity }}>
              <AbsoluteFill
                style={{
                  transform: `scale(${scale})`,
                  justifyContent: "center",
                  alignItems: "center",
                }}
              >
                <img
                  src={imageUrl}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                  }}
                />
              </AbsoluteFill>
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {/* Image counter */}
      <AbsoluteFill
        style={{
          pointerEvents: "none",
          justifyContent: "flex-end",
          alignItems: "flex-end",
          padding: 40,
        }}
      >
        <p
          style={{
            fontSize: 40,
            color: "#fff",
            margin: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            padding: "10px 20px",
            borderRadius: 10,
            fontFamily: "Arial, sans-serif",
          }}
        >
          {Math.min(Math.floor(frame / durationPerImage) + 1, images.length)} / {images.length}
        </p>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
