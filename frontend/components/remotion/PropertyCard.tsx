import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion'
import { Property } from '@/store/useAgentStore'

interface PropertyCardProps {
  property: Property
  delay?: number
}

export const PropertyCard: React.FC<PropertyCardProps> = ({ property, delay = 0 }) => {
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

  const translateX = interpolate(slideIn, [0, 1], [-100, 0])
  const opacity = interpolate(slideIn, [0, 1], [0, 1])

  // Format price
  const formattedPrice = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
  }).format(property.price)

  // Status color
  const statusColor =
    property.status === 'sold' ? '#10B981' :
    property.status === 'pending' ? '#F59E0B' :
    property.status === 'active' ? '#3B82F6' :
    '#6B7280'

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
        <div className="flex-1">
          <h3 className="text-4xl font-bold mb-3">{property.address}</h3>
          <div
            className="inline-block px-4 py-2 rounded-full text-xl font-semibold"
            style={{
              backgroundColor: statusColor + '20',
              color: statusColor,
              border: `2px solid ${statusColor}`,
            }}
          >
            {property.status.toUpperCase()}
          </div>
        </div>
        <div className="text-right">
          <div className="text-5xl font-bold text-green-400">{formattedPrice}</div>
        </div>
      </div>

      {/* Property Details Grid */}
      <div className="grid grid-cols-3 gap-6 mt-8">
        <div className="bg-white/5 rounded-xl p-6 text-center">
          <div className="text-5xl mb-2">🛏️</div>
          <div className="text-3xl font-bold">{property.bedrooms}</div>
          <div className="text-xl text-gray-400 mt-1">Bedrooms</div>
        </div>

        <div className="bg-white/5 rounded-xl p-6 text-center">
          <div className="text-5xl mb-2">🛁</div>
          <div className="text-3xl font-bold">{property.bathrooms}</div>
          <div className="text-xl text-gray-400 mt-1">Bathrooms</div>
        </div>

        <div className="bg-white/5 rounded-xl p-6 text-center">
          <div className="text-5xl mb-2">📐</div>
          <div className="text-3xl font-bold">{property.square_feet.toLocaleString()}</div>
          <div className="text-xl text-gray-400 mt-1">Sq Ft</div>
        </div>
      </div>

      {/* Property ID */}
      <div className="mt-6 pt-6 border-t border-white/10 text-lg text-gray-400">
        Property ID: #{property.id}
      </div>
    </div>
  )
}
