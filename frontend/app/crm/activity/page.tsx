'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Activity,
  Zap,
  CheckCircle2,
  XCircle,
  Clock,
  Building2,
  FileText,
  Phone,
  Mail,
  Search,
  Users,
  Globe,
  RefreshCw,
  Wifi,
  WifiOff,
  ArrowDown,
  BarChart3,
  CircleDot,
} from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ActivityEvent {
  id: number
  timestamp: string
  tool_name: string
  user_source?: string
  event_type: string
  status: string
  metadata?: any
  duration_ms?: number
  error_message?: string
}

const toolIcons: Record<string, any> = {
  create_property: Building2,
  update_property: Building2,
  enrich_property: Search,
  create_contract: FileText,
  send_contract: FileText,
  create_contact: Users,
  make_call: Phone,
  send_email: Mail,
  calculate_deal: BarChart3,
  web_research: Globe,
}

function getToolIcon(toolName: string) {
  for (const [key, Icon] of Object.entries(toolIcons)) {
    if (toolName?.toLowerCase().includes(key.replace('_', ''))) return Icon
  }
  return Zap
}

function getStatusStyle(status: string) {
  switch (status) {
    case 'success': return { color: 'text-emerald-400', bg: 'bg-emerald-500/10', icon: CheckCircle2 }
    case 'error': return { color: 'text-rose-400', bg: 'bg-rose-500/10', icon: XCircle }
    case 'pending': return { color: 'text-amber-400', bg: 'bg-amber-500/10', icon: Clock }
    default: return { color: 'text-blue-400', bg: 'bg-blue-500/10', icon: CircleDot }
  }
}

function EventCard({ event, index }: { event: ActivityEvent; index: number }) {
  const ToolIcon = getToolIcon(event.tool_name)
  const statusStyle = getStatusStyle(event.status)
  const StatusIcon = statusStyle.icon
  const time = new Date(event.timestamp)
  const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const dateStr = time.toLocaleDateString([], { month: 'short', day: 'numeric' })

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: index * 0.03 }}
      className="flex gap-4 group"
    >
      {/* Timeline line */}
      <div className="flex flex-col items-center">
        <div className={`w-9 h-9 rounded-xl ${statusStyle.bg} flex items-center justify-center flex-shrink-0`}>
          <ToolIcon className={`w-4 h-4 ${statusStyle.color}`} />
        </div>
        <div className="w-px flex-1 bg-[#1E2130] mt-2" />
      </div>

      {/* Content */}
      <div className="flex-1 pb-6 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-sm font-medium text-white">
              {(event.tool_name || 'Unknown Action').replace(/_/g, ' ')}
            </p>
            {event.user_source && (
              <p className="text-xs text-gray-500 mt-0.5">via {event.user_source}</p>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className={`inline-flex items-center gap-1 text-[10px] font-medium ${statusStyle.color}`}>
              <StatusIcon className="w-3 h-3" />
              {event.status}
            </span>
            <span className="text-[10px] text-gray-600">{timeStr}</span>
          </div>
        </div>

        {event.duration_ms && (
          <span className="text-[10px] text-gray-600 flex items-center gap-1 mt-1">
            <Clock className="w-2.5 h-2.5" />
            {event.duration_ms}ms
          </span>
        )}

        {event.error_message && (
          <div className="mt-2 p-2 rounded-lg bg-rose-500/5 border border-rose-500/10">
            <p className="text-xs text-rose-400 font-mono">{event.error_message}</p>
          </div>
        )}

        {event.metadata && Object.keys(event.metadata).length > 0 && (
          <div className="mt-2 p-2 rounded-lg bg-[#0B0D15] border border-[#1E2130]">
            <pre className="text-[10px] text-gray-500 font-mono overflow-x-auto">
              {JSON.stringify(event.metadata, null, 2).slice(0, 200)}
            </pre>
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default function ActivityPage() {
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [connected, setConnected] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  // Fetch historical events
  const fetchEvents = useCallback(async () => {
    try {
      const res = await fetch(`${API}/analytics/activity?limit=100`)
      if (res.ok) {
        const data = await res.json()
        setEvents(Array.isArray(data) ? data : data.events || [])
      }
    } catch {
      // Activity endpoint may not exist; that's OK
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchEvents()
  }, [fetchEvents])

  // WebSocket for realtime
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
    let reconnectTimeout: NodeJS.Timeout

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => setConnected(true)

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            if (['activity_logged', 'tool_started', 'tool_completed', 'tool_failed'].includes(msg.type)) {
              const newEvent: ActivityEvent = {
                id: Date.now(),
                timestamp: msg.data?.timestamp || new Date().toISOString(),
                tool_name: msg.data?.tool_name || msg.type,
                user_source: msg.data?.user_source,
                event_type: msg.type,
                status: msg.type === 'tool_completed' ? 'success' : msg.type === 'tool_failed' ? 'error' : 'pending',
                metadata: msg.data?.metadata,
                duration_ms: msg.data?.duration_ms,
                error_message: msg.data?.error_message,
              }
              setEvents(prev => [newEvent, ...prev].slice(0, 200))
            }
          } catch {}
        }

        ws.onclose = () => {
          setConnected(false)
          reconnectTimeout = setTimeout(connect, 5000)
        }

        ws.onerror = () => {
          setConnected(false)
        }
      } catch {
        reconnectTimeout = setTimeout(connect, 5000)
      }
    }

    connect()
    return () => {
      wsRef.current?.close()
      clearTimeout(reconnectTimeout)
    }
  }, [])

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = 0
    }
  }, [events, autoScroll])

  return (
    <div className="p-6 lg:p-8 max-w-[900px] mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Activity</h1>
            <p className="text-sm text-gray-500 mt-1">Real-time feed of all system activity</p>
          </div>
          <div className="flex items-center gap-3">
            {/* Connection status */}
            <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${connected ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-gray-500/10 text-gray-400 border border-gray-500/20'}`}>
              {connected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
              {connected ? 'Live' : 'Disconnected'}
            </div>
            <button
              onClick={() => { setLoading(true); fetchEvents() }}
              className="px-4 py-2 rounded-lg bg-[#1A1D27] border border-[#2A2D3A] text-sm text-gray-300 hover:text-white hover:border-blue-500/30 transition-all flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Live indicator */}
      {connected && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-500/5 border border-emerald-500/10"
        >
          <div className="relative">
            <div className="w-2 h-2 rounded-full bg-emerald-400" />
            <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          </div>
          <p className="text-xs text-emerald-400 font-medium">Connected to real-time feed</p>
          <span className="text-xs text-gray-600 ml-auto">{events.length} events</span>
        </motion.div>
      )}

      {/* Events */}
      <div ref={scrollRef} className="space-y-0">
        {loading ? (
          <div className="space-y-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="flex gap-4">
                <div className="w-9 h-9 rounded-xl bg-[#111318] animate-pulse flex-shrink-0" />
                <div className="flex-1">
                  <div className="h-4 bg-[#111318] rounded animate-pulse w-48 mb-2" />
                  <div className="h-3 bg-[#111318] rounded animate-pulse w-32" />
                </div>
              </div>
            ))}
          </div>
        ) : events.length > 0 ? (
          <AnimatePresence initial={false}>
            {events.map((event, i) => (
              <EventCard key={event.id} event={event} index={i} />
            ))}
          </AnimatePresence>
        ) : (
          <div className="text-center py-20">
            <Activity className="w-12 h-12 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-400 font-medium">No activity yet</p>
            <p className="text-sm text-gray-600 mt-1">
              {connected ? 'Waiting for new activity...' : 'Connect to see real-time activity'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
