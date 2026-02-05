'use client'

import { motion } from 'framer-motion'
import { ActivityEvent } from './ActivityFeed'

interface ActivityCardProps {
  activity: ActivityEvent
  index: number
}

const getToolIcon = (toolName: string, eventType: string): string => {
  // Map tool names to appropriate icons
  if (toolName.includes('property') || toolName.includes('list_properties')) return '🏠'
  if (toolName.includes('contract')) return '📝'
  if (toolName.includes('contact')) return '👤'
  if (toolName.includes('notification')) return '🔔'
  if (toolName.includes('enrich')) return '⚡'
  if (toolName.includes('skip_trace')) return '🔍'
  if (eventType === 'voice_command') return '🎤'
  if (eventType === 'system_event') return '⚙️'
  return '🔧'
}

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'pending':
      return 'status-pending'
    case 'success':
      return 'status-success'
    case 'error':
      return 'status-error'
    default:
      return 'status-pending'
  }
}

const getStatusBadge = (status: string): { text: string; icon: string } => {
  switch (status) {
    case 'pending':
      return { text: 'In Progress', icon: '⏳' }
    case 'success':
      return { text: 'Success', icon: '✓' }
    case 'error':
      return { text: 'Error', icon: '✕' }
    default:
      return { text: 'Unknown', icon: '?' }
  }
}

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  })
}

const formatDuration = (durationMs: number | null): string => {
  if (durationMs === null) return 'N/A'
  if (durationMs < 1000) return `${durationMs}ms`
  return `${(durationMs / 1000).toFixed(2)}s`
}

const parseMetadata = (data: string | null): any => {
  if (!data) return null
  try {
    return JSON.parse(data)
  } catch {
    return null
  }
}

export const ActivityCard = ({ activity, index }: ActivityCardProps) => {
  const icon = getToolIcon(activity.tool_name, activity.event_type)
  const statusColor = getStatusColor(activity.status)
  const statusBadge = getStatusBadge(activity.status)
  const metadata = parseMetadata(activity.data)

  return (
    <motion.div
      initial={{ opacity: 0, x: 100, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: -100, scale: 0.9 }}
      transition={{
        type: 'spring',
        damping: 25,
        stiffness: 200,
        delay: index * 0.05,
      }}
      className="activity-card"
    >
      {/* Card Header */}
      <div className="flex items-start gap-4">
        {/* Icon */}
        <motion.div
          animate={
            activity.status === 'pending'
              ? {
                  rotate: [0, 10, -10, 10, 0],
                  scale: [1, 1.1, 1],
                }
              : {}
          }
          transition={{
            duration: 2,
            repeat: activity.status === 'pending' ? Infinity : 0,
            ease: 'easeInOut',
          }}
          className="text-5xl flex-shrink-0"
        >
          {icon}
        </motion.div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Tool Name & Status Badge */}
          <div className="flex items-center justify-between gap-2 mb-2">
            <h3 className="text-xl font-bold text-white truncate">
              {activity.tool_name}
            </h3>
            <span className={`badge ${statusColor}`}>
              <span className="mr-1">{statusBadge.icon}</span>
              {statusBadge.text}
            </span>
          </div>

          {/* Event Type & User Source */}
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className="text-sm px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full border border-blue-500/30">
              {activity.event_type.replace('_', ' ')}
            </span>
            {activity.user_source && (
              <span className="text-sm px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full border border-purple-500/30">
                {activity.user_source}
              </span>
            )}
          </div>

          {/* Metadata */}
          {metadata && (
            <div className="mb-3 p-3 bg-black/30 rounded-lg border border-white/5">
              <pre className="text-xs text-gray-300 overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(metadata, null, 2)}
              </pre>
            </div>
          )}

          {/* Error Message */}
          {activity.error_message && (
            <div className="mb-3 p-3 bg-red-500/10 rounded-lg border border-red-500/30">
              <p className="text-sm text-red-300">{activity.error_message}</p>
            </div>
          )}

          {/* Footer: Timestamp & Duration */}
          <div className="flex items-center justify-between text-sm text-gray-400">
            <span className="flex items-center gap-2">
              <span>⏰</span>
              {formatTimestamp(activity.timestamp)}
            </span>
            {activity.duration_ms !== null && (
              <span className="flex items-center gap-2">
                <span>⚡</span>
                {formatDuration(activity.duration_ms)}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Loading Spinner for Pending Status */}
      {activity.status === 'pending' && (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: 'linear',
          }}
          className="absolute top-4 right-4 w-6 h-6 border-3 border-yellow-400 border-t-transparent rounded-full"
        />
      )}
    </motion.div>
  )
}
