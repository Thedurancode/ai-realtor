'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Building2,
  MapPin,
  DollarSign,
  Bed,
  Bath,
  Square,
  TrendingUp,
  ArrowUpRight,
  RefreshCw,
  ChevronRight,
  BarChart3,
  Zap,
} from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface PipelineColumn {
  id: string
  label: string
  color: string
  borderColor: string
  bgColor: string
  glowColor: string
  icon: string
}

const columns: PipelineColumn[] = [
  { id: 'new_property', label: 'New', color: 'text-blue-400', borderColor: 'border-blue-500/30', bgColor: 'bg-blue-500/5', glowColor: 'shadow-blue-500/5', icon: '🆕' },
  { id: 'under_contract', label: 'Under Contract', color: 'text-amber-400', borderColor: 'border-amber-500/30', bgColor: 'bg-amber-500/5', glowColor: 'shadow-amber-500/5', icon: '📝' },
  { id: 'closed', label: 'Closed', color: 'text-emerald-400', borderColor: 'border-emerald-500/30', bgColor: 'bg-emerald-500/5', glowColor: 'shadow-emerald-500/5', icon: '✅' },
  { id: 'archived', label: 'Archived', color: 'text-gray-400', borderColor: 'border-gray-500/30', bgColor: 'bg-gray-500/5', glowColor: 'shadow-gray-500/5', icon: '📦' },
]

function KanbanCard({ property, delay }: { property: any; delay: number }) {
  const hasPhoto = property.zillow_enrichment?.photos?.length > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className="rounded-xl bg-[#111318] border border-[#1E2130] overflow-hidden hover:border-[#2A2D3A] transition-all group cursor-pointer"
    >
      {hasPhoto && (
        <div className="h-24 overflow-hidden relative">
          <img src={property.zillow_enrichment.photos[0]} alt="" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#111318] via-transparent to-transparent" />
        </div>
      )}
      <div className="p-3">
        <p className="text-sm font-medium text-white truncate">{property.address || property.title}</p>
        <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
          <MapPin className="w-3 h-3" />
          {property.city}, {property.state}
        </p>

        <div className="flex items-center justify-between mt-3">
          <p className="text-sm font-bold text-white">
            {property.price ? `$${Number(property.price).toLocaleString()}` : 'N/A'}
          </p>
          {property.score_grade && (
            <div className={`
              w-6 h-6 rounded flex items-center justify-center text-[10px] font-bold
              ${property.score_grade === 'A' ? 'bg-emerald-500/20 text-emerald-400' :
                property.score_grade === 'B' ? 'bg-blue-500/20 text-blue-400' :
                property.score_grade === 'C' ? 'bg-amber-500/20 text-amber-400' :
                'bg-rose-500/20 text-rose-400'}
            `}>
              {property.score_grade}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 mt-2 text-[10px] text-gray-500">
          {property.bedrooms && <span className="flex items-center gap-0.5"><Bed className="w-3 h-3" />{property.bedrooms}</span>}
          {property.bathrooms && <span className="flex items-center gap-0.5"><Bath className="w-3 h-3" />{property.bathrooms}</span>}
          {property.square_feet && <span className="flex items-center gap-0.5"><Square className="w-3 h-3" />{Number(property.square_feet).toLocaleString()}</span>}
          {property.property_type && (
            <span className="ml-auto capitalize text-gray-600">{property.property_type.replace(/_/g, ' ')}</span>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default function PipelinePage() {
  const [properties, setProperties] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const fetchProperties = useCallback(async () => {
    try {
      const res = await fetch(`${API}/properties/?limit=200`)
      const data = await res.json()
      setProperties(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to fetch properties:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProperties()
  }, [fetchProperties])

  // Realtime
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
    let ws: WebSocket | null = null
    let reconnectTimeout: NodeJS.Timeout

    const connect = () => {
      try {
        ws = new WebSocket(wsUrl)
        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            if (msg.type === 'property_update') fetchProperties()
          } catch {}
        }
        ws.onclose = () => { reconnectTimeout = setTimeout(connect, 5000) }
      } catch { reconnectTimeout = setTimeout(connect, 5000) }
    }

    connect()
    return () => { ws?.close(); clearTimeout(reconnectTimeout) }
  }, [fetchProperties])

  const grouped = columns.map(col => ({
    ...col,
    properties: properties.filter(p => {
      if (col.id === 'new_property') return p.status === 'new_property' || !p.status
      return p.status === col.id
    }),
  }))

  const totalValue = properties.reduce((sum, p) => sum + (Number(p.price) || 0), 0)

  return (
    <div className="p-6 lg:p-8 h-screen flex flex-col">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Pipeline</h1>
            <p className="text-sm text-gray-500 mt-1">
              {properties.length} properties &middot; ${totalValue.toLocaleString()} total value
            </p>
          </div>
          <button
            onClick={() => { setLoading(true); fetchProperties() }}
            className="px-4 py-2.5 rounded-lg bg-[#1A1D27] border border-[#2A2D3A] text-sm text-gray-300 hover:text-white hover:border-blue-500/30 transition-all flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </motion.div>

      {/* Kanban Board */}
      {loading ? (
        <div className="flex-1 grid grid-cols-4 gap-4">
          {columns.map(col => (
            <div key={col.id} className="rounded-xl bg-[#111318] border border-[#1E2130] animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 overflow-hidden">
          {grouped.map((col, colIdx) => {
            const colValue = col.properties.reduce((sum, p) => sum + (Number(p.price) || 0), 0)
            return (
              <motion.div
                key={col.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: colIdx * 0.1 }}
                className={`rounded-xl border ${col.borderColor} ${col.bgColor} flex flex-col overflow-hidden`}
              >
                {/* Column Header */}
                <div className="p-4 border-b border-[#1E2130]">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{col.icon}</span>
                      <h3 className={`text-sm font-semibold ${col.color}`}>{col.label}</h3>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full bg-[#0B0D15] font-bold ${col.color}`}>
                      {col.properties.length}
                    </span>
                  </div>
                  {colValue > 0 && (
                    <p className="text-xs text-gray-500 mt-1">${colValue.toLocaleString()}</p>
                  )}
                </div>

                {/* Cards */}
                <div className="flex-1 overflow-y-auto p-3 space-y-3 scrollbar-thin">
                  {col.properties.length > 0 ? (
                    col.properties.map((prop, i) => (
                      <KanbanCard key={prop.id} property={prop} delay={i * 0.05} />
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <Building2 className="w-6 h-6 text-gray-700 mx-auto mb-1" />
                      <p className="text-xs text-gray-600">No properties</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
