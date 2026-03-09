import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Sequence,
  Audio,
  staticFile,
} from "remotion";
import { FONTS } from "./fonts";

export interface PropertyShowcaseProps {
  [key: string]: unknown;
  // Branding
  logoUrl?: string;
  companyName?: string;
  tagline?: string;
  primaryColor?: string;
  secondaryColor?: string;

  // Property Details
  propertyAddress?: string;
  propertyPrice?: string;
  propertyDetails?: {
    bedrooms?: number;
    bathrooms?: number;
    squareFeet?: number;
    propertyType?: string;
  };

  // Media
  propertyPhotos?: string[];
  audioUrl?: string;  // ElevenLabs voiceover

  // Outro / CTA
  agentName?: string;
  agentPhone?: string;
  agentEmail?: string;
  ctaText?: string;

  // Timing (in frames)
  logoDuration?: number;
  photoDuration?: number;
  outroDuration?: number;
}

export const PropertyShowcase: React.FC<PropertyShowcaseProps> = ({
  logoUrl,
  companyName = "Your Real Estate Experts",
  tagline = "Finding Your Dream Home",
  primaryColor = "#1E40AF",
  secondaryColor = "#3B82F6",
  propertyAddress = "123 Main St",
  propertyPrice = "$500,000",
  propertyDetails = {},
  propertyPhotos = [],
  audioUrl,
  agentName = "",
  agentPhone = "",
  agentEmail = "",
  ctaText = "Schedule a Showing",
  logoDuration = 90,  // 3 seconds
  photoDuration = 120,  // 4 seconds per photo
  outroDuration = 120,  // 4 seconds
}) => {
  const { fps, height } = useVideoConfig();
  const frame = useCurrentFrame();

  // Layout timing
  const photosStartFrame = logoDuration + 30;
  const totalPhotoDuration = propertyPhotos.length * photoDuration;
  const outroStart = photosStartFrame + totalPhotoDuration;

  // Logo intro animation
  const logoOpacity = interpolate(
    frame,
    [0, 30, logoDuration - 30, logoDuration],
    [0, 1, 1, 0],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
  );

  const logoScale = interpolate(
    frame,
    [0, 30],
    [0.8, 1],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
  );

  // Current photo index
  const currentPhotoIndex = Math.floor(
    (frame - photosStartFrame) / photoDuration
  );

  const currentPhoto = propertyPhotos[currentPhotoIndex] || propertyPhotos[0];

  // Photo transition
  const photoOpacity = interpolate(
    frame % photoDuration,
    [0, 15, photoDuration - 15, photoDuration],
    [0, 1, 1, 0],
    { extrapolateRight: "clamp" }
  );

  const photoScale = interpolate(
    frame % photoDuration,
    [0, photoDuration],
    [1, 1.1],
    { extrapolateRight: "clamp" }
  );

  // Text reveal animation for property details
  const textReveal = Math.min(
    1,
    (frame - photosStartFrame) / 30
  );

  // Outro animations
  const outroLocalFrame = frame - outroStart;
  const outroFadeIn = interpolate(outroLocalFrame, [0, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const outroTextY = interpolate(outroLocalFrame, [0, 40], [60, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const outroLineWidth = interpolate(outroLocalFrame, [0, 50], [0, 300], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const outroLogoGlow = interpolate(outroLocalFrame, [10, 40, 60], [0, 20, 10], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const outroFadeOut = interpolate(
    outroLocalFrame,
    [outroDuration - 25, outroDuration],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Cinematic letterbox bars
  const barHeight = height * 0.06;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Audio track */}
      {audioUrl && <Audio src={audioUrl} />}

      {/* LOGO INTRO SEQUENCE */}
      <Sequence from={0} durationInFrames={logoDuration}>
        <AbsoluteFill
          style={{
            backgroundColor: primaryColor,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            opacity: logoOpacity,
          }}
        >
          {/* Logo */}
          {logoUrl && (
            <div
              style={{
                transform: `scale(${logoScale})`,
                marginBottom: 40,
              }}
            >
              <img
                src={logoUrl}
                alt="Company Logo"
                style={{
                  width: 200,
                  height: 200,
                  objectFit: "contain",
                }}
              />
            </div>
          )}

          {/* Company Name */}
          <h1
            style={{
              fontSize: 70,
              fontWeight: "bold",
              color: "#fff",
              textAlign: "center",
              transform: `scale(${logoScale})`,
              fontFamily: FONTS.heading,
              textShadow: "2px 2px 8px rgba(0,0,0,0.5)",
            }}
          >
            {companyName}
          </h1>

          {/* Tagline */}
          <p
            style={{
              fontSize: 40,
              color: secondaryColor,
              textAlign: "center",
              marginTop: 20,
              transform: `scale(${logoScale})`,
              fontFamily: FONTS.accent,
              textShadow: "1px 1px 4px rgba(0,0,0,0.5)",
            }}
          >
            {tagline}
          </p>
        </AbsoluteFill>
      </Sequence>

      {/* PROPERTY PHOTOS SEQUENCE */}
      {propertyPhotos.length > 0 && (
        <Sequence from={photosStartFrame}>
          {propertyPhotos.map((photoUrl, index) => (
            <Sequence
              key={index}
              from={index * photoDuration}
              durationInFrames={photoDuration}
            >
              <AbsoluteFill>
                {/* Background Photo */}
                <img
                  src={photoUrl}
                  alt={`Property photo ${index + 1}`}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    opacity: photoOpacity,
                    transform: `scale(${photoScale})`,
                  }}
                />

                {/* Dark Overlay */}
                <AbsoluteFill
                  style={{
                    backgroundColor: "rgba(0, 0, 0, 0.3)",
                  }}
                />

                {/* Property Details Overlay */}
                <AbsoluteFill
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "flex-end",
                    padding: 60,
                    opacity: Math.min(1, (frame % photoDuration) / 30),
                  }}
                >
                  {/* Price Badge */}
                  <div
                    style={{
                      backgroundColor: primaryColor,
                      padding: "20px 40px",
                      borderRadius: 15,
                      alignSelf: "flex-start",
                      marginBottom: 30,
                      transform: `translateY(${(1 - textReveal) * 100}px)`,
                    }}
                  >
                    <p
                      style={{
                        fontSize: 56,
                        fontWeight: "bold",
                        color: "#fff",
                        margin: 0,
                        fontFamily: FONTS.accent,
                        textShadow: "2px 2px 4px rgba(0,0,0,0.5)",
                      }}
                    >
                      {propertyPrice}
                    </p>
                  </div>

                  {/* Address */}
                  <h2
                    style={{
                      fontSize: 48,
                      fontWeight: "bold",
                      color: "#fff",
                      margin: "0 0 20px 0",
                      fontFamily: FONTS.heading,
                      textShadow: "2px 2px 8px rgba(0,0,0,0.8)",
                      transform: `translateY(${(1 - textReveal) * 100}px)`,
                    }}
                  >
                    {propertyAddress}
                  </h2>

                  {/* Property Details */}
                  <div
                    style={{
                      display: "flex",
                      gap: 30,
                      flexWrap: "wrap",
                      transform: `translateY(${(1 - textReveal) * 100}px)`,
                    }}
                  >
                    {propertyDetails.bedrooms && (
                      <div
                        style={{
                          backgroundColor: "rgba(0, 0, 0, 0.7)",
                          padding: "15px 25px",
                          borderRadius: 10,
                        }}
                      >
                        <p
                          style={{
                            fontSize: 36,
                            fontWeight: "bold",
                            color: secondaryColor,
                            margin: 0,
                            fontFamily: FONTS.accent,
                          }}
                        >
                          {propertyDetails.bedrooms} bed
                        </p>
                      </div>
                    )}

                    {propertyDetails.bathrooms && (
                      <div
                        style={{
                          backgroundColor: "rgba(0, 0, 0, 0.7)",
                          padding: "15px 25px",
                          borderRadius: 10,
                        }}
                      >
                        <p
                          style={{
                            fontSize: 36,
                            fontWeight: "bold",
                            color: secondaryColor,
                            margin: 0,
                            fontFamily: FONTS.accent,
                          }}
                        >
                          {propertyDetails.bathrooms} bath
                        </p>
                      </div>
                    )}

                    {propertyDetails.squareFeet && (
                      <div
                        style={{
                          backgroundColor: "rgba(0, 0, 0, 0.7)",
                          padding: "15px 25px",
                          borderRadius: 10,
                        }}
                      >
                        <p
                          style={{
                            fontSize: 36,
                            fontWeight: "bold",
                            color: secondaryColor,
                            margin: 0,
                            fontFamily: FONTS.accent,
                          }}
                        >
                          {propertyDetails.squareFeet.toLocaleString()} sqft
                        </p>
                      </div>
                    )}
                  </div>
                </AbsoluteFill>
              </AbsoluteFill>
            </Sequence>
          ))}
        </Sequence>
      )}

      {/* OUTRO / CLOSING SEQUENCE */}
      <Sequence from={outroStart} durationInFrames={outroDuration}>
        <AbsoluteFill
          style={{
            background: `linear-gradient(135deg, ${primaryColor} 0%, #0a1628 100%)`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            opacity: outroFadeIn * outroFadeOut,
          }}
        >
          {/* Decorative accent line */}
          <div
            style={{
              width: outroLineWidth,
              height: 3,
              backgroundColor: secondaryColor,
              marginBottom: 40,
            }}
          />

          {/* Logo with glow effect */}
          {logoUrl && (
            <div
              style={{
                marginBottom: 30,
                opacity: outroFadeIn,
                transform: `translateY(${outroTextY}px)`,
                filter: `drop-shadow(0 0 ${outroLogoGlow}px ${secondaryColor})`,
              }}
            >
              <img
                src={logoUrl}
                alt="Logo"
                style={{
                  width: 120,
                  height: 120,
                  objectFit: "contain",
                }}
              />
            </div>
          )}

          {/* Property recap */}
          <h2
            style={{
              fontSize: 52,
              fontWeight: 800,
              color: "#fff",
              textAlign: "center",
              fontFamily: FONTS.heading,
              margin: 0,
              padding: "0 60px",
              opacity: outroFadeIn,
              transform: `translateY(${outroTextY}px)`,
            }}
          >
            {propertyAddress}
          </h2>

          <p
            style={{
              fontSize: 44,
              fontWeight: 700,
              color: secondaryColor,
              fontFamily: FONTS.accent,
              marginTop: 16,
              opacity: interpolate(outroLocalFrame, [15, 45], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            {propertyPrice}
          </p>

          {/* Agent contact info */}
          {agentName && (
            <p
              style={{
                fontSize: 32,
                color: "rgba(255,255,255,0.85)",
                fontFamily: FONTS.body,
                fontWeight: 600,
                marginTop: 30,
                opacity: interpolate(outroLocalFrame, [25, 55], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            >
              {agentName}
            </p>
          )}

          {agentPhone && (
            <p
              style={{
                fontSize: 36,
                color: secondaryColor,
                fontFamily: FONTS.body,
                fontWeight: 700,
                marginTop: 12,
                opacity: interpolate(outroLocalFrame, [35, 60], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            >
              {agentPhone}
            </p>
          )}

          {agentEmail && (
            <p
              style={{
                fontSize: 28,
                color: "rgba(255,255,255,0.6)",
                fontFamily: FONTS.body,
                marginTop: 8,
                opacity: interpolate(outroLocalFrame, [40, 65], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            >
              {agentEmail}
            </p>
          )}

          {/* CTA button */}
          <div
            style={{
              marginTop: 40,
              backgroundColor: secondaryColor,
              padding: "18px 50px",
              borderRadius: 12,
              opacity: interpolate(outroLocalFrame, [45, 70], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              transform: `scale(${interpolate(outroLocalFrame, [45, 70], [0.9, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })})`,
            }}
          >
            <p
              style={{
                fontSize: 34,
                fontWeight: 700,
                color: "#fff",
                margin: 0,
                fontFamily: FONTS.accent,
              }}
            >
              {ctaText}
            </p>
          </div>

          {/* Bottom accent line */}
          <div
            style={{
              width: interpolate(outroLocalFrame, [20, 70], [0, 300], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              height: 3,
              backgroundColor: secondaryColor,
              marginTop: 40,
            }}
          />

          {/* Company name */}
          <p
            style={{
              fontSize: 24,
              color: "rgba(255,255,255,0.4)",
              fontFamily: FONTS.body,
              marginTop: 20,
              opacity: interpolate(outroLocalFrame, [50, 75], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            {companyName}
          </p>
        </AbsoluteFill>
      </Sequence>

      {/* Cinematic letterbox bars */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: barHeight,
            backgroundColor: "#000",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            height: barHeight,
            backgroundColor: "#000",
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
