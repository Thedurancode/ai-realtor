import { AbsoluteFill } from 'remotion'
import { AgentAvatar } from './AgentAvatar'
import { AudioWaveform } from './AudioWaveform'

interface AgentCompositionProps {
  isSpeaking: boolean
  audioLevel: number
  currentMessage: string
}

export const AgentComposition: React.FC<AgentCompositionProps> = ({
  isSpeaking,
  audioLevel,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: 'transparent' }}>
      <div className="flex flex-col items-center justify-center h-full">
        {/* Agent Avatar */}
        <AgentAvatar isSpeaking={isSpeaking} audioLevel={audioLevel} />

        {/* Audio Waveform Below Avatar */}
        {isSpeaking && (
          <div className="mt-8">
            <AudioWaveform audioLevel={audioLevel} barCount={40} />
          </div>
        )}
      </div>
    </AbsoluteFill>
  )
}
