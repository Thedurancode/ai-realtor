'use client'

import { useEffect, useState } from 'react'
import { Player } from '@remotion/player'
import { useAgentStore } from '@/store/useAgentStore'
import { getContracts, getProperties } from '@/lib/api'
import { AgentComposition } from './remotion/AgentComposition'
import { NewsTicker } from './NewsTicker'
import { LiveIndicator } from './LiveIndicator'
import { PropertyDetailView } from './PropertyDetailView'
import { LiveNotification } from './LiveNotification'
import { EnrichmentAnimation } from './EnrichmentAnimation'

interface Notification {
  id: string
  message: string
  type: 'added' | 'deleted' | 'updated'
}

export const TVDisplay: React.FC = () => {
  const {
    isSpeaking,
    currentMessage,
    audioLevel,
    setContracts,
    setProperties,
    currentContract,
    currentProperty,
    contracts,
    properties,
    focusedProperty,
    setFocusedProperty,
    isEnriching,
    enrichingPropertyAddress,
  } = useAgentStore()

  const [isLoading, setIsLoading] = useState(true)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [previousPropertyIds, setPreviousPropertyIds] = useState<Set<number>>(new Set())

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [contracts, properties] = await Promise.all([
          getContracts(),
          getProperties(),
        ])
        setContracts(contracts)
        setProperties(properties)
        setIsLoading(false)
      } catch (error) {
        console.error('Error fetching data:', error)
        setIsLoading(false)
      }
    }

    fetchData()
  }, [setContracts, setProperties])

  // Real-time polling every 3 seconds for instant updates
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [contracts, newProperties] = await Promise.all([
          getContracts(),
          getProperties(),
        ])

        // Detect property changes
        if (previousPropertyIds.size > 0) {
          const currentIds = new Set(newProperties.map(p => p.id))
          const previousIds = previousPropertyIds

          // Detect deleted properties
          previousIds.forEach(id => {
            if (!currentIds.has(id)) {
              const deletedProperty = properties.find(p => p.id === id)
              if (deletedProperty) {
                addNotification({
                  id: `deleted-${id}-${Date.now()}`,
                  message: `${deletedProperty.address} was removed from listings`,
                  type: 'deleted'
                })
              }
            }
          })

          // Detect new properties
          currentIds.forEach(id => {
            if (!previousIds.has(id)) {
              const newProperty = newProperties.find(p => p.id === id)
              if (newProperty) {
                addNotification({
                  id: `added-${id}-${Date.now()}`,
                  message: `New listing: ${newProperty.address} - $${newProperty.price.toLocaleString()}`,
                  type: 'added'
                })
              }
            }
          })
        }

        setPreviousPropertyIds(new Set(newProperties.map(p => p.id)))
        setContracts(contracts)
        setProperties(newProperties)
      } catch (error) {
        console.error('Error polling data:', error)
      }
    }, 3000) // Reduced to 3 seconds for faster updates

    return () => clearInterval(interval)
  }, [setContracts, setProperties, previousPropertyIds, properties])

  const addNotification = (notification: Notification) => {
    setNotifications(prev => [...prev, notification])
  }

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-news-blue">
        <div className="text-4xl font-bold animate-pulse text-white">Loading AI Realtor News...</div>
      </div>
    )
  }

  return (
    <div className="h-screen w-screen overflow-hidden">
      {/* News Channel Header Bar */}
      <div className="bg-gradient-to-r from-news-blue via-primary to-news-blue border-b-4 border-secondary px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <h1 className="text-5xl font-black text-white tracking-tight">
              REALTIME <span className="text-secondary">REALTOR</span>
            </h1>
            <LiveIndicator />
          </div>
          <div className="flex items-center gap-8">
            <div className="text-right">
              <div className="text-sm text-gray-300 uppercase tracking-wide">Market Activity</div>
              <div className="text-3xl font-bold text-white">{new Date().toLocaleDateString()}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="h-[calc(100vh-180px)] p-6 grid grid-cols-3 gap-6">
        {/* Left Column - Agent & Stats */}
        <div className="col-span-1 flex flex-col gap-6">
          {/* Agent Section */}
          <div className="bg-gradient-to-br from-news-blue/80 to-primary/60 border-2 border-secondary/50 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4 border-b border-white/20 pb-3">
              <div className="text-xl font-bold text-white uppercase tracking-wider">
                AI AGENT
              </div>
              {isSpeaking && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-accent animate-flash" />
                  <span className="text-accent font-semibold text-sm">ON AIR</span>
                </div>
              )}
            </div>

            <Player
              component={AgentComposition}
              durationInFrames={9999999}
              compositionWidth={400}
              compositionHeight={400}
              fps={30}
              style={{
                width: '100%',
                maxWidth: '350px',
                margin: '0 auto',
              }}
              controls={false}
              loop
              inputProps={{
                isSpeaking,
                audioLevel,
                currentMessage,
              }}
            />

            {currentMessage && (
              <div className="mt-4 bg-white/10 border border-white/20 rounded-lg p-4">
                <div className="text-xs text-news-cyan uppercase font-bold mb-2 tracking-wider">
                  TRANSCRIPT
                </div>
                <p className="text-lg text-white leading-relaxed">{currentMessage}</p>
              </div>
            )}
          </div>

          {/* Market Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gradient-to-br from-primary to-news-blue border-2 border-white/20 rounded-lg p-4">
              <div className="text-xs text-gray-300 uppercase font-bold tracking-wider mb-1">
                Active Listings
              </div>
              <div className="text-4xl font-black text-white">{properties.length}</div>
              <div className="text-xs text-accent mt-1">↑ LIVE</div>
            </div>

            <div className="bg-gradient-to-br from-secondary to-news-orange border-2 border-white/20 rounded-lg p-4">
              <div className="text-xs text-gray-300 uppercase font-bold tracking-wider mb-1">
                Contracts
              </div>
              <div className="text-4xl font-black text-white">{contracts.length}</div>
              <div className="text-xs text-news-cyan mt-1">⚡ ACTIVE</div>
            </div>
          </div>
        </div>

        {/* Right Column - Live Feed */}
        <div className="col-span-2 overflow-y-auto pr-4 custom-scrollbar">
          <div className="space-y-4">
            {/* Breaking News Header */}
            <div className="bg-gradient-to-r from-secondary to-news-orange border-l-8 border-news-cyan px-6 py-3 rounded-lg">
              <h2 className="text-3xl font-black text-white uppercase tracking-wide">
                ⚡ LIVE: PROPERTY UPDATES
              </h2>
            </div>

            {/* Properties Feed */}
            {properties.map((property, idx) => (
              <div
                key={property.id}
                className="bg-gradient-to-r from-news-blue/90 to-news-blue/70 border-l-4 border-primary p-6 rounded-lg hover:border-secondary hover:shadow-lg hover:shadow-secondary/20 transition-all animate-slide-in cursor-pointer"
                style={{
                  animationDelay: `${idx * 0.1}s`,
                }}
                onClick={() => setFocusedProperty(property)}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="bg-primary text-white text-xs font-bold px-3 py-1 rounded uppercase">
                        {property.status}
                      </span>
                      <span className="text-news-cyan text-sm font-bold">
                        #{property.id}
                      </span>
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-1">
                      {property.address}
                    </h3>
                    <p className="text-lg text-gray-300">
                      {property.city}, {property.state} {property.zip_code}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-4xl font-black text-accent">
                      ${property.price.toLocaleString()}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-white/20">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">
                      {property.bedrooms || 'N/A'}
                    </div>
                    <div className="text-xs text-gray-400 uppercase">Bedrooms</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">
                      {property.bathrooms || 'N/A'}
                    </div>
                    <div className="text-xs text-gray-400 uppercase">Bathrooms</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">
                      {property.square_feet?.toLocaleString() || 'N/A'}
                    </div>
                    <div className="text-xs text-gray-400 uppercase">Sq Ft</div>
                  </div>
                </div>
              </div>
            ))}

            {properties.length === 0 && (
              <div className="bg-news-blue/50 border border-white/20 rounded-lg p-12 text-center">
                <p className="text-2xl text-gray-400">No active properties at this time</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* News Ticker at Bottom */}
      <NewsTicker />

      {/* Property Detail View Overlay */}
      {focusedProperty && (
        <PropertyDetailView
          property={focusedProperty}
          onClose={() => setFocusedProperty(null)}
        />
      )}

      {/* Enrichment Animation Overlay */}
      {isEnriching && (
        <EnrichmentAnimation propertyAddress={enrichingPropertyAddress} />
      )}

      {/* Live Notifications */}
      <div className="fixed top-24 right-8 z-50 space-y-4">
        {notifications.map((notification, index) => (
          <div
            key={notification.id}
            style={{ marginTop: `${index * 8}px` }}
          >
            <LiveNotification
              message={notification.message}
              type={notification.type}
              onDismiss={() => dismissNotification(notification.id)}
            />
          </div>
        ))}
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(30, 64, 175, 0.3);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(59, 130, 246, 0.7);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(59, 130, 246, 1);
        }
      `}</style>
    </div>
  )
}
