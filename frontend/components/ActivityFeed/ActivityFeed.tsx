'use client'

import { motion } from 'framer-motion'
import { ActivityTimeline } from './ActivityTimeline'
import { useEffect, useState } from 'react'

export interface ActivityEvent {
  id: number
  timestamp: string
  tool_name: string
  user_source: string | null
  event_type: 'tool_call' | 'tool_result' | 'voice_command' | 'system_event'
  status: 'pending' | 'success' | 'error'
  data: string | null
  duration_ms: number | null
  error_message: string | null
}

interface ActivityFeedProps {
  activities?: ActivityEvent[]
  className?: string
}

export const ActivityFeed = ({ activities = [], className = '' }: ActivityFeedProps) => {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  return (
    <div className={`relative w-full h-screen overflow-hidden bg-gradient-to-br from-slate-950 via-indigo-950 to-purple-950 ${className}`}>
      {/* Animated background gradients */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute top-0 left-0 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl"
      />
      <motion.div
        animate={{
          scale: [1, 1.3, 1],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: 'easeInOut',
          delay: 1,
        }}
        className="absolute bottom-0 right-0 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl"
      />
      <motion.div
        animate={{
          scale: [1, 1.15, 1],
          opacity: [0.25, 0.45, 0.25],
        }}
        transition={{
          duration: 12,
          repeat: Infinity,
          ease: 'easeInOut',
          delay: 2,
        }}
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl"
      />

      {/* Main content container with glassmorphism */}
      <div className="relative z-10 h-full flex flex-col p-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <div className="glass-panel rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <motion.div
                  animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.7, 1, 0.7],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: 'easeInOut',
                  }}
                  className="w-3 h-3 bg-emerald-400 rounded-full shadow-lg shadow-emerald-400/50"
                />
                <h1 className="text-4xl font-bold text-white">
                  Live Activity Feed
                </h1>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Total Events</p>
                <p className="text-2xl font-bold text-white">{activities.length}</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Activity Timeline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="flex-1 overflow-hidden"
        >
          <ActivityTimeline activities={activities} />
        </motion.div>
      </div>
    </div>
  )
}
