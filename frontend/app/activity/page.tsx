'use client'

import { ActivityFeed, ActivityEvent as FeedActivityEvent } from '@/components/ActivityFeed'
import { useActivityFeed, ActivityEvent } from '@/hooks/useActivityFeed'

/**
 * Activity Feed Page
 * Full-screen real-time activity feed displaying MCP tool usage and voice agent activity
 * Accessible at /activity
 */
export default function ActivityPage() {
  // WebSocket URL from environment or default to localhost
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'

  // Connect to WebSocket and get real-time activities
  const { activities } = useActivityFeed(wsUrl)

  // Transform activities from hook format to component format
  const transformedActivities: FeedActivityEvent[] = activities.map((activity: ActivityEvent) => ({
    id: activity.id,
    timestamp: activity.timestamp,
    tool_name: activity.tool_name,
    user_source: activity.user_source || null,
    event_type: activity.event_type,
    status: activity.status,
    data: activity.metadata ? JSON.stringify(activity.metadata) : null,
    duration_ms: activity.duration_ms || null,
    error_message: activity.error_message || null,
  }))

  return <ActivityFeed activities={transformedActivities} />
}
