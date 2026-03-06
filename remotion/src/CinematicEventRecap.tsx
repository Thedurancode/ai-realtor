import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Sequence,
  Audio,
  Img,
  staticFile,
} from "remotion";

export interface EventRecapProps {
  // Event info
  eventName: string;
  eventDate: string;
  eventLocation: string;
  eventDescription?: string;

  // Branding
  logoUrl?: string;
  hostName?: string;
  primaryColor?: string;
  accentColor?: string;

  // Media
  photos: string[];
  musicUrl?: string; // custom music URL — falls back to default
  musicVolume?: number;

  // Timing (in frames)
  introDuration?: number;
  photoDuration?: number;
  outroDuration?: number;

  // Captions for photos (optional, matched by index)
  photoCaptions?: string[];
}

const DEFAULT_MUSIC = staticFile("default-music.mp3");
const DEFAULT_LOGO = staticFile("logo.png");

export const CinematicEventRecap: React.FC<EventRecapProps> = ({
  eventName = "Event Recap",
  eventDate = "",
  eventLocation = "",
  eventDescription = "",
  logoUrl,
  hostName = "",
  primaryColor = "#0F172A",
  accentColor = "#F59E0B",
  photos = [],
  musicUrl,
  musicVolume = 0.8,
  introDuration = 120, // 4 seconds
  photoDuration = 90, // 3 seconds per photo
  outroDuration = 120, // 4 seconds
  photoCaptions = [],
}) => {
  const { fps, width, height } = useVideoConfig();
  const frame = useCurrentFrame();

  const totalPhotoDuration = photos.length * photoDuration;
  const outroStart = introDuration + totalPhotoDuration;

  // Resolve logo — use provided URL or fall back to default
  const resolvedLogo = logoUrl || DEFAULT_LOGO;

  // --- LOGO REVEAL ANIMATIONS ---
  const logoOpacity = interpolate(frame, [0, 35], [0, 1], {
    extrapolateRight: "clamp",
  });
  const logoScale = interpolate(frame, [0, 45], [0.6, 1], {
    extrapolateRight: "clamp",
  });
  const logoGlow = interpolate(frame, [20, 50, 70], [0, 25, 12], {
    extrapolateRight: "clamp",
  });
  const logoBlur = interpolate(frame, [0, 20], [8, 0], {
    extrapolateRight: "clamp",
  });

  // --- INTRO TEXT ANIMATIONS (staggered after logo) ---
  const introTitleY = interpolate(frame, [35, 65], [80, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const introTitleOpacity = interpolate(frame, [35, 65], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const introDateOpacity = interpolate(frame, [55, 80], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const introLocationOpacity = interpolate(frame, [70, 95], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const introFadeOut = interpolate(
    frame,
    [introDuration - 30, introDuration],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // --- OUTRO ANIMATIONS ---
  const outroLocalFrame = frame - outroStart;
  const outroFadeIn = interpolate(outroLocalFrame, [0, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const outroTextY = interpolate(outroLocalFrame, [0, 40], [60, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Cinematic letterbox bars
  const barHeight = height * 0.08;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Background music — uses custom URL or default MP3 */}
      <Audio src={musicUrl || DEFAULT_MUSIC} volume={musicVolume} />

      {/* === INTRO === */}
      <Sequence from={0} durationInFrames={introDuration}>
        <AbsoluteFill
          style={{
            background: `linear-gradient(135deg, ${primaryColor} 0%, #1a1a2e 100%)`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            opacity: introFadeOut,
          }}
        >
          {/* Decorative line */}
          <div
            style={{
              width: interpolate(frame, [0, 50], [0, 300], {
                extrapolateRight: "clamp",
              }),
              height: 3,
              backgroundColor: accentColor,
              marginBottom: 40,
            }}
          />

          {/* Logo — cinematic reveal with scale, glow, and blur */}
          <div
            style={{
              marginBottom: 30,
              opacity: logoOpacity,
              transform: `scale(${logoScale})`,
              filter: `blur(${logoBlur}px) drop-shadow(0 0 ${logoGlow}px ${accentColor})`,
            }}
          >
            <Img
              src={resolvedLogo}
              style={{
                width: 180,
                height: 180,
                objectFit: "contain",
              }}
            />
          </div>

          {/* Event Name */}
          <h1
            style={{
              fontSize: 72,
              fontWeight: 800,
              color: "#fff",
              textAlign: "center",
              fontFamily: "Arial, sans-serif",
              letterSpacing: -1,
              margin: 0,
              padding: "0 60px",
              opacity: introTitleOpacity,
              transform: `translateY(${introTitleY}px)`,
            }}
          >
            {eventName}
          </h1>

          {/* Date */}
          {eventDate && (
            <p
              style={{
                fontSize: 36,
                color: accentColor,
                fontFamily: "Arial, sans-serif",
                fontWeight: 600,
                marginTop: 24,
                opacity: introDateOpacity,
              }}
            >
              {eventDate}
            </p>
          )}

          {/* Location */}
          {eventLocation && (
            <p
              style={{
                fontSize: 30,
                color: "rgba(255,255,255,0.7)",
                fontFamily: "Arial, sans-serif",
                marginTop: 12,
                opacity: introLocationOpacity,
              }}
            >
              {eventLocation}
            </p>
          )}

          {/* Decorative line bottom */}
          <div
            style={{
              width: interpolate(frame, [20, 70], [0, 300], {
                extrapolateRight: "clamp",
              }),
              height: 3,
              backgroundColor: accentColor,
              marginTop: 40,
            }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* === PHOTO SEQUENCES === */}
      {photos.map((photoUrl, index) => {
        const photoStart = introDuration + index * photoDuration;
        const caption = photoCaptions[index] || "";

        return (
          <Sequence
            key={index}
            from={photoStart}
            durationInFrames={photoDuration}
          >
            <PhotoSlide
              photoUrl={photoUrl}
              caption={caption}
              photoDuration={photoDuration}
              accentColor={accentColor}
              index={index}
            />
          </Sequence>
        );
      })}

      {/* === OUTRO === */}
      <Sequence from={outroStart} durationInFrames={outroDuration}>
        <AbsoluteFill
          style={{
            background: `linear-gradient(135deg, ${primaryColor} 0%, #1a1a2e 100%)`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            opacity: outroFadeIn,
          }}
        >
          <div
            style={{
              width: interpolate(outroLocalFrame, [0, 50], [0, 200], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              height: 3,
              backgroundColor: accentColor,
              marginBottom: 40,
            }}
          />

          <h2
            style={{
              fontSize: 56,
              fontWeight: 800,
              color: "#fff",
              textAlign: "center",
              fontFamily: "Arial, sans-serif",
              margin: 0,
              padding: "0 60px",
              opacity: outroFadeIn,
              transform: `translateY(${outroTextY}px)`,
            }}
          >
            Thanks for attending!
          </h2>

          {hostName && (
            <p
              style={{
                fontSize: 32,
                color: accentColor,
                fontFamily: "Arial, sans-serif",
                fontWeight: 600,
                marginTop: 20,
                opacity: interpolate(outroLocalFrame, [20, 50], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            >
              Hosted by {hostName}
            </p>
          )}

          {eventDescription && (
            <p
              style={{
                fontSize: 26,
                color: "rgba(255,255,255,0.6)",
                fontFamily: "Arial, sans-serif",
                marginTop: 16,
                textAlign: "center",
                padding: "0 80px",
                opacity: interpolate(outroLocalFrame, [30, 60], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            >
              {eventDescription}
            </p>
          )}

          <div
            style={{
              width: interpolate(outroLocalFrame, [20, 70], [0, 200], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              height: 3,
              backgroundColor: accentColor,
              marginTop: 40,
            }}
          />
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

// --- Individual photo slide with Ken Burns + caption ---
const PhotoSlide: React.FC<{
  photoUrl: string;
  caption: string;
  photoDuration: number;
  accentColor: string;
  index: number;
}> = ({ photoUrl, caption, photoDuration, accentColor, index }) => {
  const frame = useCurrentFrame();

  // Alternate zoom direction for variety
  const zoomIn = index % 2 === 0;
  const scale = interpolate(
    frame,
    [0, photoDuration],
    zoomIn ? [1, 1.15] : [1.15, 1],
    { extrapolateRight: "clamp" }
  );

  // Subtle horizontal pan
  const panX = interpolate(
    frame,
    [0, photoDuration],
    index % 2 === 0 ? [0, -30] : [-30, 0],
    { extrapolateRight: "clamp" }
  );

  // Fade in/out
  const opacity = interpolate(
    frame,
    [0, 20, photoDuration - 20, photoDuration],
    [0, 1, 1, 0],
    { extrapolateRight: "clamp" }
  );

  // Caption slide up
  const captionOpacity = interpolate(frame, [15, 40], [0, 1], {
    extrapolateRight: "clamp",
  });
  const captionY = interpolate(frame, [15, 40], [30, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      {/* Photo with Ken Burns */}
      <Img
        src={photoUrl}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translateX(${panX}px)`,
        }}
      />

      {/* Gradient overlay for caption readability */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 40%)",
        }}
      />

      {/* Caption */}
      {caption && (
        <div
          style={{
            position: "absolute",
            bottom: 140,
            left: 60,
            right: 60,
            opacity: captionOpacity,
            transform: `translateY(${captionY}px)`,
          }}
        >
          <div
            style={{
              display: "inline-block",
              backgroundColor: "rgba(0,0,0,0.6)",
              padding: "16px 28px",
              borderRadius: 10,
              borderLeft: `4px solid ${accentColor}`,
            }}
          >
            <p
              style={{
                fontSize: 32,
                color: "#fff",
                fontFamily: "Arial, sans-serif",
                fontWeight: 600,
                margin: 0,
              }}
            >
              {caption}
            </p>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
