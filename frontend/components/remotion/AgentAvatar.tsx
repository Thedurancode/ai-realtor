import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion'

interface AgentAvatarProps {
  isSpeaking: boolean
  audioLevel: number
}

export const AgentAvatar: React.FC<AgentAvatarProps> = ({ isSpeaking, audioLevel }) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  // Pulsing animation for the outer circle
  const outerScale = spring({
    frame: frame % 60,
    fps,
    config: {
      damping: 200,
    },
  })

  // Mouth animation based on speaking
  const mouthScale = isSpeaking
    ? interpolate(
        Math.sin(frame * 0.5) * audioLevel,
        [-1, 1],
        [0.3, 1]
      )
    : 0.1

  // Eye blink animation
  const eyeHeight = interpolate(
    frame % 180,
    [0, 5, 10, 175, 180],
    [20, 2, 20, 20, 20]
  )

  // Glow intensity based on speaking
  const glowOpacity = isSpeaking
    ? interpolate(audioLevel, [0, 1], [0.3, 0.8])
    : 0.2

  return (
    <svg width="400" height="400" viewBox="0 0 400 400">
      {/* Outer glow ring */}
      <circle
        cx="200"
        cy="200"
        r={150 + outerScale * 20}
        fill="none"
        stroke="#0052CC"
        strokeWidth="3"
        opacity={glowOpacity}
        style={{
          filter: 'blur(10px)',
        }}
      />

      {/* Main face circle */}
      <circle
        cx="200"
        cy="200"
        r="150"
        fill="url(#gradient)"
      />

      {/* Gradient definition */}
      <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0052CC" />
          <stop offset="100%" stopColor="#1E3A8A" />
        </linearGradient>
        <radialGradient id="eyeGradient">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="100%" stopColor="#DBEAFE" />
        </radialGradient>
      </defs>

      {/* Left eye */}
      <ellipse
        cx="150"
        cy="170"
        rx="20"
        ry={eyeHeight}
        fill="url(#eyeGradient)"
      />
      <circle cx="150" cy="170" r="10" fill="#1E40AF" />

      {/* Right eye */}
      <ellipse
        cx="250"
        cy="170"
        rx="20"
        ry={eyeHeight}
        fill="url(#eyeGradient)"
      />
      <circle cx="250" cy="170" r="10" fill="#1E40AF" />

      {/* Mouth */}
      <ellipse
        cx="200"
        cy="240"
        rx="40"
        ry={20 * mouthScale}
        fill="#1E40AF"
      />

      {/* Audio waveform indicators when speaking */}
      {isSpeaking && (
        <>
          <rect
            x="80"
            y={200 - audioLevel * 50}
            width="8"
            height={audioLevel * 100}
            fill="#00A86B"
            opacity="0.6"
            rx="4"
          />
          <rect
            x="100"
            y={200 - audioLevel * 70}
            width="8"
            height={audioLevel * 140}
            fill="#00A86B"
            opacity="0.6"
            rx="4"
          />
          <rect
            x="292"
            y={200 - audioLevel * 70}
            width="8"
            height={audioLevel * 140}
            fill="#00A86B"
            opacity="0.6"
            rx="4"
          />
          <rect
            x="312"
            y={200 - audioLevel * 50}
            width="8"
            height={audioLevel * 100}
            fill="#00A86B"
            opacity="0.6"
            rx="4"
          />
        </>
      )}
    </svg>
  )
}
