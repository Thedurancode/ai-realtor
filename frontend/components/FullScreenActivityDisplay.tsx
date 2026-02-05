'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useState } from 'react'

interface Activity {
  id: string
  type: 'api_call' | 'response' | 'notification' | 'enrichment' | 'property_added' | 'contract_signed'
  title: string
  message: string
  timestamp: Date
  status?: 'pending' | 'success' | 'error'
  icon?: string
  color?: string
}

export const FullScreenActivityDisplay = () => {
  const [currentActivity, setCurrentActivity] = useState<Activity | null>(null)
  const [activityQueue, setActivityQueue] = useState<Activity[]>([])

  useEffect(() => {
    // Expose function to show activities
    if (typeof window !== 'undefined') {
      (window as any).showBigActivity = (activity: Omit<Activity, 'id' | 'timestamp'>) => {
        const newActivity: Activity = {
          ...activity,
          id: `${Date.now()}-${Math.random()}`,
          timestamp: new Date()
        }
        setActivityQueue(prev => [...prev, newActivity])
      }
    }
  }, [])

  useEffect(() => {
    if (activityQueue.length > 0 && !currentActivity) {
      const next = activityQueue[0]
      setCurrentActivity(next)
      setActivityQueue(prev => prev.slice(1))

      // Auto-dismiss after 4 seconds
      setTimeout(() => {
        setCurrentActivity(null)
      }, 4000)
    }
  }, [activityQueue, currentActivity])

  const getActivityStyle = (type: Activity['type']) => {
    switch (type) {
      case 'api_call':
        return {
          bg: 'from-blue-600 via-blue-500 to-cyan-500',
          icon: '→',
          color: 'text-blue-100'
        }
      case 'response':
        return {
          bg: 'from-green-600 via-emerald-500 to-teal-500',
          icon: '✓',
          color: 'text-green-100'
        }
      case 'notification':
        return {
          bg: 'from-purple-600 via-violet-500 to-fuchsia-500',
          icon: '🔔',
          color: 'text-purple-100'
        }
      case 'enrichment':
        return {
          bg: 'from-orange-600 via-amber-500 to-yellow-500',
          icon: '⚡',
          color: 'text-orange-100'
        }
      case 'property_added':
        return {
          bg: 'from-emerald-600 via-green-500 to-lime-500',
          icon: '🏠',
          color: 'text-emerald-100'
        }
      case 'contract_signed':
        return {
          bg: 'from-pink-600 via-rose-500 to-red-500',
          icon: '✍️',
          color: 'text-pink-100'
        }
      default:
        return {
          bg: 'from-gray-600 via-slate-500 to-zinc-500',
          icon: '•',
          color: 'text-gray-100'
        }
    }
  }

  if (!currentActivity) return null

  const style = getActivityStyle(currentActivity.type)

  return (
    <AnimatePresence>
      <motion.div
        key={currentActivity.id}
        initial={{ opacity: 0, scale: 0.8, y: 100 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.8, y: -100 }}
        transition={{
          type: 'spring',
          damping: 20,
          stiffness: 200,
          duration: 0.5
        }}
        className="fixed inset-0 z-[100] flex items-center justify-center pointer-events-none"
      >
        {/* Backdrop blur */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-md"
        />

        {/* Main content */}
        <div className="relative z-10 max-w-5xl mx-auto px-8">
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{
              scale: [0.8, 1.05, 1],
            }}
            transition={{
              duration: 0.6,
              times: [0, 0.6, 1],
              ease: 'easeOut'
            }}
            className={`bg-gradient-to-br ${style.bg} rounded-3xl p-12 shadow-2xl border-4 border-white/20`}
          >
            {/* Icon */}
            <motion.div
              animate={{
                rotate: [0, 10, -10, 10, 0],
                scale: [1, 1.1, 1, 1.1, 1]
              }}
              transition={{
                duration: 0.8,
                repeat: Infinity,
                repeatDelay: 2
              }}
              className="text-9xl text-center mb-8"
            >
              {currentActivity.icon || style.icon}
            </motion.div>

            {/* Title */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className={`text-7xl font-black text-center mb-6 ${style.color} tracking-tight`}
            >
              {currentActivity.title}
            </motion.h1>

            {/* Message */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-3xl text-center text-white/90 font-medium leading-relaxed"
            >
              {currentActivity.message}
            </motion.p>

            {/* Status indicator */}
            {currentActivity.status === 'pending' && (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="mt-8 mx-auto w-16 h-16 border-8 border-white/30 border-t-white rounded-full"
              />
            )}

            {currentActivity.status === 'success' && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.4, type: 'spring', damping: 10 }}
                className="mt-8 mx-auto w-20 h-20 bg-white rounded-full flex items-center justify-center"
              >
                <span className="text-5xl">✓</span>
              </motion.div>
            )}

            {/* Timestamp */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mt-6 text-center text-xl text-white/60"
            >
              {currentActivity.timestamp.toLocaleTimeString()}
            </motion.div>

            {/* Progress bar */}
            <motion.div
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 4, ease: 'linear' }}
              className="mt-8 h-2 bg-white/40 rounded-full overflow-hidden"
              style={{ transformOrigin: 'left' }}
            >
              <div className="h-full bg-white rounded-full" />
            </motion.div>
          </motion.div>

          {/* Decorative elements */}
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.6, 0.3]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut'
            }}
            className={`absolute -inset-20 bg-gradient-to-br ${style.bg} rounded-full blur-3xl -z-10`}
          />
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
