'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Building2,
  Users,
  HandCoins,
  CheckSquare,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Activity,
  Clock,
  DollarSign,
  Zap,
  BarChart3,
  ArrowUpRight,
  GitBranch,
} from 'lucide-react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Stats {
  totalProperties: number
  totalContacts: number
  totalOffers: number
  pendingTasks: number
  pipeline: { new: number; under_contract: number; closed: number; archived: number }
  recentProperties: any[]
  recentActivity: any[]
}

function StatCard({ icon: Icon, label, value, change, color, delay }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="relative overflow-hidden rounded-xl bg-[#111318] border border-[#1E2130] p-5 hover:border-[#2A2D3A] transition-colors group"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</p>
          <p className="text-3xl font-bold text-white mt-2">{value}</p>
          {change !== undefined && (
            <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {change >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              <span>{change >= 0 ? '+' : ''}{change}% this week</span>
            </div>
          )}
        </div>
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      <div className={`absolute bottom-0 left-0 right-0 h-[2px] opacity-0 group-hover:opacity-100 transition-opacity ${color}`} />
    </motion.div>
  )
}

function PipelineBar({ pipeline }: { pipeline: Stats['pipeline'] }) {
  const total = pipeline.new + pipeline.under_contract + pipeline.closed + pipeline.archived
  if (total === 0) return null

  const segments = [
    { label: 'New', count: pipeline.new, color: 'bg-blue-500', text: 'text-blue-400' },
    { label: 'Under Contract', count: pipeline.under_contract, color: 'bg-amber-500', text: 'text-amber-400' },
    { label: 'Closed', count: pipeline.closed, color: 'bg-emerald-500', text: 'text-emerald-400' },
    { label: 'Archived', count: pipeline.archived, color: 'bg-gray-600', text: 'text-gray-400' },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.3 }}
      className="rounded-xl bg-[#111318] border border-[#1E2130] p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          <h3 className="text-sm font-semibold text-white">Deal Pipeline</h3>
        </div>
        <Link href="/crm/pipeline" className="text-xs text-gray-500 hover:text-blue-400 transition-colors flex items-center gap-1">
          View all <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {/* Pipeline bar */}
      <div className="flex rounded-full overflow-hidden h-3 bg-[#1A1D27] mb-5">
        {segments.map((seg) =>
          seg.count > 0 ? (
            <motion.div
              key={seg.label}
              initial={{ width: 0 }}
              animate={{ width: `${(seg.count / total) * 100}%` }}
              transition={{ duration: 0.8, delay: 0.5 }}
              className={`${seg.color} transition-all`}
              title={`${seg.label}: ${seg.count}`}
            />
          ) : null
        )}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-4 gap-3">
        {segments.map((seg) => (
          <div key={seg.label} className="text-center">
            <p className="text-2xl font-bold text-white">{seg.count}</p>
            <p className={`text-[10px] font-medium ${seg.text} uppercase tracking-wider mt-0.5`}>{seg.label}</p>
          </div>
        ))}
      </div>
    </motion.div>
  )
}

function PropertyRow({ property, index }: { property: any; index: number }) {
  const statusColors: Record<string, string> = {
    new_property: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    under_contract: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    closed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    archived: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: 0.1 * index }}
      className="flex items-center gap-4 p-3 rounded-lg hover:bg-[#1A1D27] transition-colors group cursor-pointer"
    >
      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600/20 to-violet-600/20 border border-blue-500/10 flex items-center justify-center flex-shrink-0">
        <Building2 className="w-4 h-4 text-blue-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{property.address || property.title}</p>
        <p className="text-xs text-gray-500">{property.city}, {property.state}</p>
      </div>
      <div className="text-right flex-shrink-0">
        <p className="text-sm font-semibold text-white">
          {property.price ? `$${Number(property.price).toLocaleString()}` : 'N/A'}
        </p>
        <span className={`inline-block text-[10px] px-2 py-0.5 rounded-full border font-medium ${statusColors[property.status] || statusColors.new_property}`}>
          {(property.status || 'new').replace(/_/g, ' ')}
        </span>
      </div>
      <ArrowUpRight className="w-4 h-4 text-gray-600 group-hover:text-blue-400 transition-colors flex-shrink-0" />
    </motion.div>
  )
}

export default function CRMDashboard() {
  const [stats, setStats] = useState<Stats>({
    totalProperties: 0,
    totalContacts: 0,
    totalOffers: 0,
    pendingTasks: 0,
    pipeline: { new: 0, under_contract: 0, closed: 0, archived: 0 },
    recentProperties: [],
    recentActivity: [],
  })
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const [propsRes, contactsRes, offersRes, todosRes] = await Promise.allSettled([
        fetch(`${API}/properties/?limit=100`).then(r => r.json()),
        fetch(`${API}/contacts/property/0`).then(r => r.json()).catch(() => ({ contacts: [] })),
        fetch(`${API}/offers/`).then(r => r.json()).catch(() => []),
        fetch(`${API}/todos/voice/search?address_query=all&status=pending`).then(r => r.json()).catch(() => ({ todos: [] })),
      ])

      const properties = propsRes.status === 'fulfilled' ? (Array.isArray(propsRes.value) ? propsRes.value : []) : []
      const contacts = contactsRes.status === 'fulfilled' ? (contactsRes.value?.contacts || []) : []
      const offers = offersRes.status === 'fulfilled' ? (Array.isArray(offersRes.value) ? offersRes.value : []) : []
      const todos = todosRes.status === 'fulfilled' ? (todosRes.value?.todos || []) : []

      const pipeline = { new: 0, under_contract: 0, closed: 0, archived: 0 }
      properties.forEach((p: any) => {
        if (p.status === 'new_property') pipeline.new++
        else if (p.status === 'under_contract') pipeline.under_contract++
        else if (p.status === 'closed') pipeline.closed++
        else if (p.status === 'archived') pipeline.archived++
        else pipeline.new++
      })

      setStats({
        totalProperties: properties.length,
        totalContacts: contacts.length,
        totalOffers: offers.length,
        pendingTasks: todos.length,
        pipeline,
        recentProperties: properties.slice(0, 6),
        recentActivity: [],
      })
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 15000)
    return () => clearInterval(interval)
  }, [fetchData])

  // WebSocket for realtime
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
    let ws: WebSocket | null = null
    let reconnectTimeout: NodeJS.Timeout

    const connect = () => {
      try {
        ws = new WebSocket(wsUrl)
        ws.onmessage = () => {
          fetchData()
        }
        ws.onclose = () => {
          reconnectTimeout = setTimeout(connect, 5000)
        }
      } catch {
        reconnectTimeout = setTimeout(connect, 5000)
      }
    }

    connect()
    return () => {
      ws?.close()
      clearTimeout(reconnectTimeout)
    }
  }, [fetchData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8 max-w-[1400px] mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Real-time overview of your real estate operations</p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard icon={Building2} label="Properties" value={stats.totalProperties} color="bg-blue-600" delay={0} />
        <StatCard icon={Users} label="Contacts" value={stats.totalContacts} color="bg-violet-600" delay={0.05} />
        <StatCard icon={HandCoins} label="Offers" value={stats.totalOffers} color="bg-amber-600" delay={0.1} />
        <StatCard icon={CheckSquare} label="Pending Tasks" value={stats.pendingTasks} color="bg-emerald-600" delay={0.15} />
      </div>

      {/* Pipeline + Recent Properties */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PipelineBar pipeline={stats.pipeline} />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.35 }}
          className="rounded-xl bg-[#111318] border border-[#1E2130] p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-400" />
              <h3 className="text-sm font-semibold text-white">Recent Properties</h3>
            </div>
            <Link href="/crm/properties" className="text-xs text-gray-500 hover:text-blue-400 transition-colors flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-1">
            {stats.recentProperties.length > 0 ? (
              stats.recentProperties.map((prop, i) => (
                <PropertyRow key={prop.id} property={prop} index={i} />
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Building2 className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No properties yet</p>
                <p className="text-xs mt-1">Properties will appear here as they are added</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.5 }}
        className="mt-6 rounded-xl bg-[#111318] border border-[#1E2130] p-6"
      >
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-400" />
          Quick Actions
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Add Property', icon: Building2, href: '/crm/properties', color: 'from-blue-600/10 to-blue-600/5 border-blue-500/10 hover:border-blue-500/30' },
            { label: 'Add Contact', icon: Users, href: '/crm/contacts', color: 'from-violet-600/10 to-violet-600/5 border-violet-500/10 hover:border-violet-500/30' },
            { label: 'View Pipeline', icon: GitBranch, href: '/crm/pipeline', color: 'from-amber-600/10 to-amber-600/5 border-amber-500/10 hover:border-amber-500/30' },
            { label: 'View Tasks', icon: CheckSquare, href: '/crm/tasks', color: 'from-emerald-600/10 to-emerald-600/5 border-emerald-500/10 hover:border-emerald-500/30' },
          ].map((action) => (
            <Link
              key={action.label}
              href={action.href}
              className={`flex items-center gap-3 p-4 rounded-lg bg-gradient-to-br border transition-all ${action.color}`}
            >
              <action.icon className="w-5 h-5 text-gray-300" />
              <span className="text-sm font-medium text-gray-300">{action.label}</span>
            </Link>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
