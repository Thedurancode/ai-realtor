import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useState } from 'react'

export interface Notification {
  id: number
  type: string
  priority: string
  title: string
  message: string
  icon?: string
  property_id?: number
  contact_id?: number
  contract_id?: number
  auto_dismiss_seconds?: number
  created_at: string
}

interface NotificationToastProps {
  notification: Notification
  onDismiss: (id: number) => void
}

export function NotificationToast({ notification, onDismiss }: NotificationToastProps) {
  const [progress, setProgress] = useState(100)

  useEffect(() => {
    if (notification.auto_dismiss_seconds) {
      const totalMs = notification.auto_dismiss_seconds * 1000
      const intervalMs = 50
      const decrementPerInterval = (100 / totalMs) * intervalMs

      const interval = setInterval(() => {
        setProgress((prev) => {
          const newProgress = prev - decrementPerInterval
          if (newProgress <= 0) {
            clearInterval(interval)
            onDismiss(notification.id)
            return 0
          }
          return newProgress
        })
      }, intervalMs)

      return () => clearInterval(interval)
    }
  }, [notification.id, notification.auto_dismiss_seconds, onDismiss])

  const getPriorityColor = () => {
    switch (notification.priority) {
      case 'urgent':
        return 'from-red-500/20 to-red-600/20 border-red-500'
      case 'high':
        return 'from-orange-500/20 to-orange-600/20 border-orange-500'
      case 'medium':
        return 'from-blue-500/20 to-blue-600/20 border-blue-500'
      case 'low':
        return 'from-gray-500/20 to-gray-600/20 border-gray-500'
      default:
        return 'from-blue-500/20 to-blue-600/20 border-blue-500'
    }
  }

  return (
    <motion.div
      initial={{ x: 400, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 400, opacity: 0 }}
      className={`
        relative w-96 rounded-lg border-2 backdrop-blur-md
        bg-gradient-to-br ${getPriorityColor()}
        shadow-2xl overflow-hidden
      `}
    >
      {/* Progress bar */}
      {notification.auto_dismiss_seconds && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-white/20">
          <motion.div
            className="h-full bg-white/60"
            style={{ width: `${progress}%` }}
            transition={{ duration: 0.05, ease: 'linear' }}
          />
        </div>
      )}

      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Icon */}
          {notification.icon && (
            <div className="text-3xl flex-shrink-0 mt-1">
              {notification.icon}
            </div>
          )}

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h4 className="text-white font-bold text-lg leading-tight mb-1">
              {notification.title}
            </h4>
            <p className="text-white/90 text-sm leading-relaxed">
              {notification.message}
            </p>

            {/* Metadata */}
            <div className="flex items-center gap-2 mt-2 text-xs text-white/60">
              <span className="capitalize">{notification.type.replace('_', ' ')}</span>
              <span>•</span>
              <span>{new Date(notification.created_at).toLocaleTimeString()}</span>
            </div>
          </div>

          {/* Close button */}
          <button
            onClick={() => onDismiss(notification.id)}
            className="text-white/60 hover:text-white transition-colors p-1"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </motion.div>
  )
}

interface NotificationContainerProps {
  notifications: Notification[]
  onDismiss: (id: number) => void
}

export function NotificationContainer({ notifications, onDismiss }: NotificationContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-3 pointer-events-none">
      <div className="pointer-events-auto">
        <AnimatePresence mode="popLayout">
          {notifications.map((notification) => (
            <NotificationToast
              key={notification.id}
              notification={notification}
              onDismiss={onDismiss}
            />
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
