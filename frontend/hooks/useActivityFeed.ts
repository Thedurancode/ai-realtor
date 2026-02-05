import { create } from 'zustand'
import { useEffect, useRef } from 'react'

export interface ActivityEvent {
  id: number
  timestamp: string
  tool_name: string
  user_source?: string
  event_type: 'tool_call' | 'tool_result' | 'voice_command' | 'system_event'
  status: 'pending' | 'success' | 'error'
  metadata?: any
  duration_ms?: number
  error_message?: string
}

interface ActivityFeedState {
  activities: ActivityEvent[]
  maxActivities: number
  isAutoScrollEnabled: boolean

  // Actions
  addActivity: (activity: ActivityEvent) => void
  updateActivity: (id: number, updates: Partial<ActivityEvent>) => void
  clearActivities: () => void
  setAutoScroll: (enabled: boolean) => void
}

/**
 * Zustand store for managing activity feed state
 * Maintains a rolling buffer of the last 50 activities
 */
export const useActivityFeedStore = create<ActivityFeedState>((set) => ({
  activities: [],
  maxActivities: 50,
  isAutoScrollEnabled: true,

  addActivity: (activity) =>
    set((state) => {
      // Check if activity already exists (avoid duplicates)
      const exists = state.activities.some((a) => a.id === activity.id)
      if (exists) {
        return state
      }

      // Add new activity at the beginning and maintain max limit
      const newActivities = [activity, ...state.activities].slice(0, state.maxActivities)
      return { activities: newActivities }
    }),

  updateActivity: (id, updates) =>
    set((state) => ({
      activities: state.activities.map((activity) =>
        activity.id === id ? { ...activity, ...updates } : activity
      ),
    })),

  clearActivities: () => set({ activities: [] }),

  setAutoScroll: (enabled) => set({ isAutoScrollEnabled: enabled }),
}))

/**
 * Hook for managing activity feed with WebSocket integration
 * Subscribes to WebSocket events and updates the activity store
 */
export const useActivityFeed = (wsUrl?: string) => {
  const { addActivity, updateActivity, activities, isAutoScrollEnabled, setAutoScroll } = useActivityFeedStore()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const handleWebSocketMessage = (event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data)

      switch (message.type) {
        case 'activity_logged':
        case 'tool_started':
          if (message.activity) {
            addActivity({
              id: message.activity.id,
              timestamp: message.activity.timestamp,
              tool_name: message.activity.tool_name,
              user_source: message.activity.user_source,
              event_type: message.activity.event_type,
              status: message.activity.status,
              metadata: message.activity.metadata,
            })
          }
          break

        case 'tool_completed':
        case 'tool_failed':
          if (message.activity) {
            updateActivity(message.activity.id, {
              status: message.activity.status,
              duration_ms: message.activity.duration_ms,
              error_message: message.activity.error_message,
            })
          }
          break
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error)
    }
  }

  const connect = () => {
    if (!wsUrl) return

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('Activity feed WebSocket connected')
      }

      ws.onmessage = handleWebSocketMessage

      ws.onerror = (error) => {
        console.error('Activity feed WebSocket error:', error)
      }

      ws.onclose = () => {
        console.log('Activity feed WebSocket disconnected')

        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect activity feed...')
          connect()
        }, 5000)
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Error creating activity feed WebSocket:', error)
    }
  }

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }

  useEffect(() => {
    if (wsUrl) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [wsUrl])

  return {
    activities,
    isAutoScrollEnabled,
    setAutoScroll,
  }
}

/**
 * Hook for auto-scroll behavior
 * Scrolls to newest activity when not manually scrolling
 */
export const useActivityAutoScroll = (containerRef: React.RefObject<HTMLElement>) => {
  const { isAutoScrollEnabled, setAutoScroll } = useActivityFeedStore()
  const { activities } = useActivityFeedStore()
  const lastScrollTop = useRef(0)
  const userScrollTimeout = useRef<NodeJS.Timeout | null>(null)

  // Auto-scroll to top when new activities arrive
  useEffect(() => {
    if (isAutoScrollEnabled && containerRef.current && activities.length > 0) {
      containerRef.current.scrollTo({
        top: 0,
        behavior: 'smooth',
      })
    }
  }, [activities.length, isAutoScrollEnabled, containerRef])

  // Handle manual scroll - disable auto-scroll temporarily
  const handleScroll = () => {
    if (!containerRef.current) return

    const currentScrollTop = containerRef.current.scrollTop
    const scrollDelta = Math.abs(currentScrollTop - lastScrollTop.current)

    // If user scrolled more than 50px, assume manual scroll
    if (scrollDelta > 50) {
      setAutoScroll(false)

      // Clear existing timeout
      if (userScrollTimeout.current) {
        clearTimeout(userScrollTimeout.current)
      }

      // Re-enable auto-scroll after 10 seconds of no scrolling
      userScrollTimeout.current = setTimeout(() => {
        // Only re-enable if scrolled to top
        if (containerRef.current && containerRef.current.scrollTop < 100) {
          setAutoScroll(true)
        }
      }, 10000)
    }

    lastScrollTop.current = currentScrollTop
  }

  return {
    handleScroll,
    isAutoScrollEnabled,
  }
}
