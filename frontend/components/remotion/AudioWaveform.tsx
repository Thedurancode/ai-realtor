import { useCurrentFrame, interpolate } from 'remotion'

interface AudioWaveformProps {
  audioLevel: number
  barCount?: number
  color?: string
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({
  audioLevel,
  barCount = 50,
  color = '#00A86B',
}) => {
  const frame = useCurrentFrame()
  const bars = Array.from({ length: barCount }, (_, i) => i)

  return (
    <div className="flex items-center justify-center gap-1 h-32">
      {bars.map((i) => {
        const offset = (frame + i * 3) * 0.1
        const baseHeight = Math.sin(offset) * 0.5 + 0.5
        const height = interpolate(
          baseHeight * audioLevel,
          [0, 1],
          [10, 100]
        )

        return (
          <div
            key={i}
            style={{
              width: '4px',
              height: `${height}px`,
              backgroundColor: color,
              borderRadius: '2px',
              opacity: 0.6 + audioLevel * 0.4,
              transition: 'height 0.1s ease-out',
            }}
          />
        )
      })}
    </div>
  )
}
