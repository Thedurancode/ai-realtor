import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion'
import { Contract } from '@/store/useAgentStore'

interface ContractCardProps {
  contract: Contract
  delay?: number
}

export const ContractCard: React.FC<ContractCardProps> = ({ contract, delay = 0 }) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  // Slide in animation
  const slideIn = spring({
    frame: frame - delay,
    fps,
    config: {
      damping: 100,
      stiffness: 200,
      mass: 0.5,
    },
  })

  const translateX = interpolate(slideIn, [0, 1], [100, 0])
  const opacity = interpolate(slideIn, [0, 1], [0, 1])

  // Calculate completion percentage
  const totalSigners = contract.signers.length
  const signedCount = contract.signers.filter(s => s.status === 'completed').length
  const completionPercent = (signedCount / totalSigners) * 100

  // Status color
  const statusColor =
    contract.status === 'completed' ? '#10B981' :
    contract.status === 'pending' ? '#F59E0B' :
    '#3B82F6'

  return (
    <div
      style={{
        transform: `translateX(${translateX}%)`,
        opacity,
      }}
      className="glass-effect rounded-2xl p-8 mb-6 w-full"
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-4xl font-bold mb-2">Contract #{contract.id}</h3>
          <p className="text-xl text-gray-300">Template: {contract.template_id}</p>
        </div>
        <div
          className="px-6 py-3 rounded-full text-2xl font-semibold"
          style={{
            backgroundColor: statusColor + '20',
            color: statusColor,
            border: `2px solid ${statusColor}`,
          }}
        >
          {contract.status.toUpperCase()}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-xl mb-2">
          <span>Completion Progress</span>
          <span className="font-bold">{Math.round(completionPercent)}%</span>
        </div>
        <div className="w-full h-4 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full transition-all duration-500 rounded-full"
            style={{
              width: `${completionPercent}%`,
              background: `linear-gradient(90deg, ${statusColor} 0%, ${statusColor}aa 100%)`,
            }}
          />
        </div>
      </div>

      {/* Signers */}
      <div>
        <h4 className="text-2xl font-semibold mb-4">Signers ({signedCount}/{totalSigners})</h4>
        <div className="space-y-3">
          {contract.signers.map((signer, idx) => (
            <div
              key={idx}
              className="flex justify-between items-center p-4 rounded-lg bg-white/5"
            >
              <div>
                <p className="text-xl font-semibold">{signer.name}</p>
                <p className="text-lg text-gray-400">{signer.role}</p>
              </div>
              <div className="flex items-center gap-4">
                {signer.signed_at && (
                  <span className="text-sm text-gray-400">
                    {new Date(signer.signed_at).toLocaleDateString()}
                  </span>
                )}
                <div
                  className={`w-4 h-4 rounded-full ${
                    signer.status === 'completed' ? 'bg-green-500' : 'bg-yellow-500'
                  }`}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Timestamps */}
      {contract.sent_at && (
        <div className="mt-6 pt-6 border-t border-white/10 text-lg text-gray-400">
          <p>Sent: {new Date(contract.sent_at).toLocaleString()}</p>
          {contract.completed_at && (
            <p className="mt-1">Completed: {new Date(contract.completed_at).toLocaleString()}</p>
          )}
        </div>
      )}
    </div>
  )
}
