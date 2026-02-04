'use client'

import { useAgentStore } from '@/store/useAgentStore'

export const NewsTicker: React.FC = () => {
  const { contracts, properties } = useAgentStore()

  const newsItems = [
    `${properties.length} PROPERTIES ACTIVE`,
    `${contracts.length} CONTRACTS IN PROGRESS`,
    ...properties.slice(0, 3).map(p =>
      `NEW LISTING: ${p.address} - $${p.price.toLocaleString()}`
    ),
    ...contracts.filter(c => c.status === 'completed').map(c =>
      `CONTRACT COMPLETED: Property #${c.property_id}`
    ),
  ]

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-r from-news-orange via-secondary to-news-cyan h-12 overflow-hidden z-50">
      <div className="flex items-center h-full">
        {/* Breaking News Label */}
        <div className="bg-white text-secondary px-6 py-2 font-bold text-sm uppercase flex-shrink-0">
          LIVE
        </div>

        {/* Scrolling Ticker */}
        <div className="flex-1 overflow-hidden bg-news-blue/90">
          <div className="animate-ticker whitespace-nowrap py-2">
            <span className="text-white font-semibold text-sm">
              {newsItems.map((item, idx) => (
                <span key={idx} className="mx-8">
                  <span className="text-news-cyan">●</span> {item}
                </span>
              ))}
            </span>
          </div>
        </div>

        {/* Time */}
        <div className="bg-white text-news-blue px-6 py-2 font-bold text-sm flex-shrink-0">
          {new Date().toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}
