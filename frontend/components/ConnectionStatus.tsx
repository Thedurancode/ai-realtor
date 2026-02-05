'use client'

import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

export const ConnectionStatus = () => {
  const [isConnected, setIsConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [apiCallCount, setApiCallCount] = useState(0)

  useEffect(() => {
    // Listen for API calls
    const originalFetch = window.fetch
    window.fetch = async (...args) => {
      setApiCallCount(prev => prev + 1)
      setLastUpdate(new Date())
      return originalFetch(...args)
    }

    return () => {
      window.fetch = originalFetch
    }
  }, [])

  useEffect(() => {
    // Check WebSocket connection
    const checkConnection = () => {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
      const ws = new WebSocket(wsUrl + '/ws')

      ws.onopen = () => setIsConnected(true)
      ws.onerror = () => setIsConnected(false)
      ws.onclose = () => setIsConnected(false)

      return ws
    }

    const ws = checkConnection()
    return () => ws.close()
  }, [])

  return (
    <div className="fixed bottom-4 left-4 z-50">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-black/90 backdrop-blur-xl border border-white/20 rounded-xl p-4 min-w-[200px]"
      >
        <div className="flex items-center gap-3">
          <div className="relative">
            <motion.div
              className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
              animate={{
                scale: [1, 1.2, 1],
                opacity: [1, 0.7, 1]
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut'
              }}
            />
            {isConnected && (
              <motion.div
                className="absolute inset-0 bg-green-500 rounded-full"
                animate={{
                  scale: [1, 2, 2],
                  opacity: [0.5, 0, 0]
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeOut'
                }}
              />
            )}
          </div>
          <div>
            <div className="text-white font-semibold text-sm">
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>
            <div className="text-xs text-gray-400">
              {apiCallCount} API calls
            </div>
          </div>
        </div>

        <div className="mt-2 pt-2 border-t border-white/10">
          <div className="text-xs text-gray-500">
            Last update: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
