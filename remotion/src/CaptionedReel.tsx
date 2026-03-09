import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Audio,
  Img,
} from "remotion";
import { FONTS } from "./fonts";

export interface CaptionedReelProps {
  [key: string]: unknown;
  title: string;
  subtitle: string;
  backgroundUrl: string;
  overlayColor: string;
  overlayOpacity: number;

  // Branding (optional)
  logoUrl?: string;
  companyName?: string;
  primaryColor?: string;
  accentColor?: string;

  // CTA
  ctaText?: string;
  ctaColor?: string;

  // Audio
  musicUrl?: string;
  musicVolume?: number;
  voiceoverUrl?: string;
}

export const CaptionedReel: React.FC<CaptionedReelProps> = ({
  title,
  subtitle,
  backgroundUrl,
  overlayColor,
  overlayOpacity,
  logoUrl,
  companyName,
  primaryColor = "#1E40AF",
  accentColor = "#3B82F6",
  ctaText = "Schedule a Viewing",
  ctaColor,
  musicUrl,
  musicVolume = 0.5,
  voiceoverUrl,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, height } = useVideoConfig();

  // Ken Burns on background
  const bgScale = interpolate(frame, [0, durationInFrames], [1, 1.15], {
    extrapolateRight: "clamp",
  });
  const bgPanX = interpolate(frame, [0, durationInFrames], [0, -30], {
    extrapolateRight: "clamp",
  });

  // Logo animation (first 60 frames)
  const logoOpacity = logoUrl
    ? interpolate(frame, [0, 20, 60, 80], [0, 1, 1, 0.6], {
        extrapolateRight: "clamp",
      })
    : 0;
  const logoScale = interpolate(frame, [0, 25], [0.7, 1], {
    extrapolateRight: "clamp",
  });

  // Text animations with spring
  const titleOpacity = spring({
    frame: frame - 30,
    fps,
    config: { damping: 100, stiffness: 200 },
  });
  const titleY = interpolate(frame, [30, 60], [40, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const subtitleOpacity = spring({
    frame: frame - 60,
    fps,
    config: { damping: 100, stiffness: 200 },
  });
  const subtitleY = interpolate(frame, [60, 85], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const scale = interpolate(frame, [0, 30], [0.8, 1], {
    extrapolateRight: "clamp",
  });

  // CTA animation (appears at 66% of duration)
  const ctaStart = Math.floor(durationInFrames * 0.66);
  const ctaOpacity = interpolate(frame, [ctaStart, ctaStart + 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const ctaScale = interpolate(frame, [ctaStart, ctaStart + 25], [0.9, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Decorative accent line
  const lineWidth = interpolate(frame, [10, 60], [0, 200], {
    extrapolateRight: "clamp",
  });

  // Cinematic letterbox bars
  const barHeight = height * 0.05;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Background music */}
      {musicUrl && <Audio src={musicUrl} volume={musicVolume} />}
      {voiceoverUrl && <Audio src={voiceoverUrl} volume={1} />}

      {/* Background image with Ken Burns */}
      {backgroundUrl ? (
        <AbsoluteFill>
          <Img
            src={backgroundUrl}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${bgScale}) translateX(${bgPanX}px)`,
            }}
          />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill
          style={{
            background: `linear-gradient(135deg, ${primaryColor} 0%, #0a1628 100%)`,
          }}
        />
      )}

      {/* Dark overlay */}
      <AbsoluteFill
        style={{
          backgroundColor: overlayColor,
          opacity: overlayOpacity,
        }}
      />

      {/* Logo watermark (top-center) */}
      {logoUrl && (
        <div
          style={{
            position: "absolute",
            top: 80,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            opacity: logoOpacity,
            transform: `scale(${logoScale})`,
          }}
        >
          <Img
            src={logoUrl}
            style={{
              width: 100,
              height: 100,
              objectFit: "contain",
            }}
          />
        </div>
      )}

      {/* Text content */}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          textAlign: "center",
          padding: "0 60px",
        }}
      >
        {/* Accent line */}
        <div
          style={{
            width: lineWidth,
            height: 3,
            backgroundColor: accentColor,
            marginBottom: 30,
          }}
        />

        <div
          style={{
            transform: `scale(${scale}) translateY(${titleY}px)`,
            opacity: titleOpacity,
          }}
        >
          <h1
            style={{
              fontSize: 80,
              fontWeight: 800,
              color: "#fff",
              margin: 0,
              textShadow: "2px 2px 8px rgba(0,0,0,0.5)",
              fontFamily: FONTS.heading,
              letterSpacing: -1,
            }}
          >
            {title}
          </h1>
        </div>

        <div
          style={{
            marginTop: 20,
            opacity: subtitleOpacity,
            transform: `translateY(${subtitleY}px)`,
          }}
        >
          <h2
            style={{
              fontSize: 46,
              fontWeight: 400,
              color: "rgba(255,255,255,0.85)",
              margin: 0,
              textShadow: "2px 2px 8px rgba(0,0,0,0.5)",
              fontFamily: FONTS.body,
            }}
          >
            {subtitle}
          </h2>
        </div>

        {/* Bottom accent line */}
        <div
          style={{
            width: interpolate(frame, [50, 90], [0, 200], {
              extrapolateRight: "clamp",
            }),
            height: 3,
            backgroundColor: accentColor,
            marginTop: 30,
          }}
        />
      </AbsoluteFill>

      {/* CTA at the bottom */}
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: 0,
          right: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 16,
          opacity: ctaOpacity,
          transform: `scale(${ctaScale})`,
        }}
      >
        <div
          style={{
            backgroundColor: ctaColor || accentColor,
            padding: "18px 40px",
            borderRadius: 12,
          }}
        >
          <p
            style={{
              fontSize: 36,
              color: "#fff",
              margin: 0,
              fontWeight: 700,
              fontFamily: FONTS.accent,
            }}
          >
            {ctaText}
          </p>
        </div>

        {companyName && (
          <p
            style={{
              fontSize: 22,
              color: "rgba(255,255,255,0.5)",
              margin: 0,
              fontFamily: FONTS.body,
            }}
          >
            {companyName}
          </p>
        )}
      </div>

      {/* Cinematic letterbox bars */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: barHeight, backgroundColor: "#000" }} />
        <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: barHeight, backgroundColor: "#000" }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
