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

export interface PropertyShowcaseProps {
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

  // Timing (in frames)
  logoDuration?: number;
  photoDuration?: number;
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
  logoDuration = 90,  // 3 seconds
  photoDuration = 120,  // 4 seconds per photo
}) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

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
  const photosStartFrame = logoDuration + 30; // 1 second transition after logo
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
              fontFamily: "Arial",
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
              fontFamily: "Arial",
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
                        fontFamily: "Arial",
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
                      fontFamily: "Arial",
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
                            fontFamily: "Arial",
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
                            fontFamily: "Arial",
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
                            fontFamily: "Arial",
                          }}
                        >
                          {propertyDetails.squareFeet.toLocaleString()} sqft
                        </p>
                      </div>
                    )}
                  </div>

                  {/* CTA */}
                  <div
                    style={{
                      marginTop: 40,
                      backgroundColor: secondaryColor,
                      padding: "15px 40px",
                      borderRadius: 10,
                      alignSelf: "flex-start",
                      transform: `translateY(${(1 - textReveal) * 100}px)`,
                    }}
                  >
                    <p
                      style={{
                        fontSize: 32,
                        fontWeight: "bold",
                        color: "#fff",
                        margin: 0,
                        fontFamily: "Arial",
                      }}
                    >
                      Call Now!
                    </p>
                  </div>
                </AbsoluteFill>
              </AbsoluteFill>
            </Sequence>
          ))}
        </Sequence>
      )}
    </AbsoluteFill>
  );
};
