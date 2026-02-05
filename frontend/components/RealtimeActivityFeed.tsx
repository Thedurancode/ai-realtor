'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useState } from 'react'

interface Activity {
  id: string
  type: 'api_call' | 'response' | 'notification' | 'enrichment' | 'property_added'
  message: string
  timestamp: Date
  status?: 'pending' | 'success' | 'error'
  details?: string
}

export const RealtimeActivityFeed = () => {
  const [activities, setActivities] = useState<Activity[]>([])

  useEffect(() => {
    // Expose function to add activities from external sources
    if (typeof window !== 'undefined') {
      (window as any).addActivity = (activity: Omit<Activity, 'id' | 'timestamp'>) => {
        const newActivity: Activity = {
          ...activity,
          id: `${Date.now()}-${Math.random()}`,
          timestamp: new Date()
        }
        setActivities(prev => [newActivity, ...prev].slice(0, 10)) // Keep last 10
      }
    }
  }, [])

  const getActivityColor = (type: Activity['type'], status?: Activity['status']) => {
    if (status === 'pending') return 'text-yellow-400 bg-yellow-400/10'
    if (status === 'error') return 'text-red-400 bg-red-400/10'

    switch (type) {
      case 'api_call':
        return 'text-blue-400 bg-blue-400/10'
      case 'response':
        return 'text-green-400 bg-green-400/10'
      case 'notification':
        return 'text-purple-400 bg-purple-400/10'
      case 'enrichment':
        return 'text-orange-400 bg-orange-400/10'
      case 'property_added':
        return 'text-emerald-400 bg-emerald-400/10'
      default:
        return 'text-gray-400 bg-gray-400/10'
    }
  }

  const getActivityIcon = (type: Activity['type']) => {
    switch (type) {
      case 'api_call': return '→'
      case 'response': return '✓'
      case 'notification': return '🔔'
      case 'enrichment': return '⚡'
      case 'property_added': return '🏠'
      default: return '•'
    }
  }

  return (
    <div className="fixed top-4 right-4 w-96 max-h-[80vh] overflow-hidden pointer-events-none z-50">
      <div className="bg-black/80 backdrop-blur-xl border border-white/10 rounded-2xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <h3 className="text-white font-semibold text-sm">Live Activity</h3>
        </div>

        <div className="space-y-2">
          <AnimatePresence mode="popLayout">
            {activities.map((activity) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: 50, scale: 0.8 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: -50, scale: 0.8 }}
                transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                className={`${getActivityColor(activity.type, activity.status)} rounded-lg p-3 border border-current/20`}
              >
                <div className="flex items-start gap-2">
                  <span className="text-lg">{getActivityIcon(activity.type)}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white/90 truncate">
                      {activity.message}
                    </p>
                    {activity.details && (
                      <p className="text-xs opacity-60 mt-1">{activity.details}</p>
                    )}
                    <p className="text-xs opacity-40 mt-1">
                      {activity.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                  {activity.status === 'pending' && (
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
