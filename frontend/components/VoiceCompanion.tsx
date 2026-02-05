'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface VoiceContext {
  type: 'property' | 'contract' | 'contact' | 'general'
  entityId?: number
  topic?: string
  transcript?: string
  timestamp: Date
}

interface ConversationMessage {
  speaker: 'user' | 'agent'
  text: string
  timestamp: Date
  context?: VoiceContext
}

export const VoiceCompanion = () => {
  const [isListening, setIsListening] = useState(false)
  const [currentContext, setCurrentContext] = useState<VoiceContext | null>(null)
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [focusedEntity, setFocusedEntity] = useState<any>(null)

  useEffect(() => {
    // Set up global function for voice agent to update context
    if (typeof window !== 'undefined') {
      (window as any).updateVoiceContext = (context: VoiceContext) => {
        setCurrentContext(context)
        setIsListening(true)
      }

      (window as any).addVoiceMessage = (speaker: 'user' | 'agent', text: string, context?: VoiceContext) => {
        setMessages(prev => [
          { speaker, text, timestamp: new Date(), context },
          ...prev.slice(0, 9)
        ])
      }

      (window as any).setVoiceFocus = (entity: any) => {
        setFocusedEntity(entity)
      }

      (window as any).clearVoiceFocus = () => {
        setFocusedEntity(null)
      }
    }
  }, [])

  const getContextColor = (type: string) => {
    switch (type) {
      case 'property': return 'from-orange-600 to-orange-500'
      case 'contract': return 'from-purple-600 to-purple-500'
      case 'contact': return 'from-blue-600 to-blue-500'
      default: return 'from-cyan-600 to-cyan-500'
    }
  }

  const getContextIcon = (type: string) => {
    switch (type) {
      case 'property': return '🏠'
      case 'contract': return '📝'
      case 'contact': return '👤'
      default: return '🎤'
    }
  }

  return (
    <>
      {/* Voice Status Indicator - Top Right Corner */}
      <AnimatePresence>
        {isListening && (
          <motion.div
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            className="fixed top-20 right-4 z-50"
          >
            <div className="bg-gradient-to-r from-green-600 to-green-500 rounded-lg px-4 py-2 shadow-2xl border-2 border-green-400">
              <div className="flex items-center gap-2">
                <motion.div
                  animate={{ scale: [1, 1.3, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="w-3 h-3 bg-white rounded-full"
                />
                <span className="text-sm font-bold text-white">VOICE ACTIVE</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Current Context Display */}
      <AnimatePresence>
        {currentContext && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            className="fixed top-4 left-1/2 -translate-x-1/2 z-50"
          >
            <div className={`bg-gradient-to-r ${getContextColor(currentContext.type)} rounded-lg px-6 py-3 shadow-2xl border-2 border-white/30`}>
              <div className="flex items-center gap-3">
                <span className="text-3xl">{getContextIcon(currentContext.type)}</span>
                <div>
                  <div className="text-xs text-white/80 font-semibold">DISCUSSING</div>
                  <div className="text-lg font-black text-white">{currentContext.topic || currentContext.type.toUpperCase()}</div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Live Conversation Transcript - Bottom Left */}
      <div className="fixed bottom-4 left-4 z-40 w-96 max-h-96 overflow-hidden">
        <div className="bg-black/90 border-2 border-cyan-500 rounded-lg backdrop-blur-sm">
          <div className="bg-cyan-500/20 border-b border-cyan-500 px-3 py-2 flex items-center gap-2">
            <motion.div
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="w-2 h-2 bg-green-400 rounded-full"
            />
            <span className="text-xs font-bold text-cyan-400">LIVE CONVERSATION</span>
          </div>
          <div className="p-3 space-y-2 max-h-80 overflow-y-auto custom-scroll">
            <AnimatePresence mode="popLayout">
              {messages.map((msg, i) => (
                <motion.div
                  key={`${msg.timestamp.getTime()}-${i}`}
                  initial={{ opacity: 0, x: msg.speaker === 'user' ? -20 : 20, height: 0 }}
                  animate={{ opacity: 1, x: 0, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className={`flex ${msg.speaker === 'user' ? 'justify-start' : 'justify-end'}`}
                >
                  <div className={`max-w-[80%] rounded-lg p-2 ${
                    msg.speaker === 'user'
                      ? 'bg-blue-500/20 border border-blue-500/30'
                      : 'bg-green-500/20 border border-green-500/30'
                  }`}>
                    <div className="text-[10px] font-bold mb-1 ${
                      msg.speaker === 'user' ? 'text-blue-400' : 'text-green-400'
                    }">
                      {msg.speaker === 'user' ? 'YOU' : 'AGENT'}
                    </div>
                    <div className="text-xs text-white leading-tight">{msg.text}</div>
                    <div className="text-[8px] text-gray-500 mt-1">
                      {msg.timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Focused Entity Display - Full Screen Overlay */}
      <AnimatePresence>
        {focusedEntity && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] bg-black/80 backdrop-blur-lg flex items-center justify-center"
            onClick={() => setFocusedEntity(null)}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="max-w-4xl w-full mx-8"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="bg-gradient-to-br from-orange-900 to-black border-4 border-orange-500 rounded-2xl p-8 shadow-2xl">
                {/* Property Focus Display */}
                {focusedEntity.price && (
                  <>
                    <div className="text-6xl mb-4">{getContextIcon('property')}</div>
                    <h2 className="text-5xl font-black text-orange-400 mb-4">{focusedEntity.title}</h2>
                    <div className="text-7xl font-black text-green-400 mb-6">
                      ${(focusedEntity.price / 1000000).toFixed(2)}M
                    </div>
                    <div className="grid grid-cols-2 gap-6 text-xl">
                      <div>
                        <div className="text-gray-400 text-sm mb-1">ADDRESS</div>
                        <div className="text-white font-semibold">{focusedEntity.address}, {focusedEntity.city}</div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-sm mb-1">DETAILS</div>
                        <div className="text-white font-semibold">
                          {focusedEntity.bedrooms} BD • {focusedEntity.bathrooms} BA • {focusedEntity.square_feet?.toLocaleString()} SF
                        </div>
                      </div>
                      {focusedEntity.zillow_enrichment && (
                        <div className="col-span-2">
                          <div className="text-gray-400 text-sm mb-1">ZESTIMATE</div>
                          <div className="text-cyan-400 font-black text-2xl">
                            ${(focusedEntity.zillow_enrichment.zestimate / 1000000).toFixed(2)}M
                          </div>
                        </div>
                      )}
                    </div>
                    {focusedEntity.zillow_enrichment?.photos?.[0] && (
                      <div className="mt-6 rounded-lg overflow-hidden border-4 border-orange-500/30">
                        <img
                          src={focusedEntity.zillow_enrichment.photos[0]}
                          alt={focusedEntity.title}
                          className="w-full h-96 object-cover"
                        />
                      </div>
                    )}
                  </>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <style jsx>{`
        .custom-scroll::-webkit-scrollbar {
          width: 3px;
        }
        .custom-scroll::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.3);
        }
        .custom-scroll::-webkit-scrollbar-thumb {
          background: rgba(34, 211, 238, 0.5);
        }
      `}</style>
    </>
  )
}
