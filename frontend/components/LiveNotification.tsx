'use client'

import { useEffect, useState } from 'react'

interface LiveNotificationProps {
  message: string
  type: 'added' | 'deleted' | 'updated'
  onDismiss: () => void
}

export const LiveNotification: React.FC<LiveNotificationProps> = ({ message, type, onDismiss }) => {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    // Slide in
    setTimeout(() => setIsVisible(true), 100)

    // Auto-dismiss after 5 seconds
    const timer = setTimeout(() => {
      setIsVisible(false)
      setTimeout(onDismiss, 500)
    }, 5000)

    return () => clearTimeout(timer)
  }, [onDismiss])

  const colors = {
    added: {
      bg: 'from-accent to-emerald-600',
      icon: '➕',
      label: 'PROPERTY ADDED'
    },
    deleted: {
      bg: 'from-secondary to-news-orange',
      icon: '🗑️',
      label: 'PROPERTY DELETED'
    },
    updated: {
      bg: 'from-primary to-news-cyan',
      icon: '🔄',
      label: 'PROPERTY UPDATED'
    }
  }

  const config = colors[type]

  return (
    <div
      className={`fixed top-24 right-8 z-50 transition-all duration-500 ${
        isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
      }`}
    >
      <div className={`bg-gradient-to-r ${config.bg} border-2 border-white/30 rounded-xl shadow-2xl shadow-black/50 p-6 min-w-96`}>
        <div className="flex items-start gap-4">
          <div className="text-5xl">{config.icon}</div>
          <div className="flex-1">
            <div className="text-xs font-bold text-white/80 uppercase tracking-wider mb-1">
              {config.label}
            </div>
            <div className="text-xl font-bold text-white leading-tight">
              {message}
            </div>
          </div>
          <button
            onClick={() => {
              setIsVisible(false)
              setTimeout(onDismiss, 500)
            }}
            className="text-white hover:text-white/70 text-2xl font-bold transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Progress bar */}
        <div className="mt-4 h-1 bg-white/20 rounded-full overflow-hidden">
          <div
            className="h-full bg-white animate-[shrink_5s_linear]"
            style={{
              animation: 'shrink 5s linear forwards'
            }}
          />
        </div>
      </div>

      <style jsx>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  )
}
