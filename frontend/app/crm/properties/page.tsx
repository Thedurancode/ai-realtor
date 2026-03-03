'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Building2,
  Search,
  Filter,
  X,
  MapPin,
  Bed,
  Bath,
  Square,
  DollarSign,
  Eye,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Home,
  Calendar,
  BarChart3,
  Phone,
  Mail,
  Globe,
  Image,
  RefreshCw,
} from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  new_property: { label: 'New', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
  under_contract: { label: 'Under Contract', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
  closed: { label: 'Closed', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
  archived: { label: 'Archived', color: 'text-gray-400', bg: 'bg-gray-500/10 border-gray-500/20' },
}

const typeIcons: Record<string, string> = {
  house: '🏠', condo: '🏢', townhouse: '🏘️', multi_family: '🏗️',
  land: '🏞️', commercial: '🏪', apartment: '🏬',
}

function PropertyCard({ property, onSelect, isSelected }: { property: any; onSelect: (p: any) => void; isSelected: boolean }) {
  const status = statusConfig[property.status] || statusConfig.new_property
  const hasPhotos = property.zillow_enrichment?.photos?.length > 0
  const photo = hasPhotos ? property.zillow_enrichment.photos[0] : null

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      onClick={() => onSelect(property)}
      className={`
        rounded-xl border overflow-hidden cursor-pointer transition-all duration-200
        ${isSelected
          ? 'bg-[#1A1D27] border-blue-500/40 ring-1 ring-blue-500/20'
          : 'bg-[#111318] border-[#1E2130] hover:border-[#2A2D3A]'
        }
      `}
    >
      {/* Photo */}
      {photo ? (
        <div className="h-36 bg-[#1A1D27] overflow-hidden relative">
          <img src={photo} alt={property.address} className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#111318] via-transparent to-transparent" />
        </div>
      ) : (
        <div className="h-24 bg-gradient-to-br from-[#1A1D27] to-[#111318] flex items-center justify-center">
          <Building2 className="w-8 h-8 text-gray-700" />
        </div>
      )}

      <div className="p-4">
        {/* Status badge */}
        <div className="flex items-center justify-between mb-2">
          <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold uppercase tracking-wider ${status.bg} ${status.color}`}>
            {status.label}
          </span>
          <span className="text-lg">{typeIcons[property.property_type] || '🏠'}</span>
        </div>

        {/* Address */}
        <h3 className="text-sm font-semibold text-white truncate">{property.address || property.title}</h3>
        <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
          <MapPin className="w-3 h-3" />
          {property.city}, {property.state} {property.zip_code}
        </p>

        {/* Price */}
        <p className="text-lg font-bold text-white mt-3">
          {property.price ? `$${Number(property.price).toLocaleString()}` : 'Price N/A'}
        </p>

        {/* Features */}
        <div className="flex items-center gap-3 mt-3 text-xs text-gray-400">
          {property.bedrooms && (
            <span className="flex items-center gap-1"><Bed className="w-3 h-3" />{property.bedrooms}</span>
          )}
          {property.bathrooms && (
            <span className="flex items-center gap-1"><Bath className="w-3 h-3" />{property.bathrooms}</span>
          )}
          {property.square_feet && (
            <span className="flex items-center gap-1"><Square className="w-3 h-3" />{Number(property.square_feet).toLocaleString()} sqft</span>
          )}
        </div>

        {/* Score */}
        {property.score_grade && (
          <div className="mt-3 flex items-center gap-2">
            <div className={`
              w-7 h-7 rounded-md flex items-center justify-center text-xs font-bold
              ${property.score_grade === 'A' ? 'bg-emerald-500/20 text-emerald-400' :
                property.score_grade === 'B' ? 'bg-blue-500/20 text-blue-400' :
                property.score_grade === 'C' ? 'bg-amber-500/20 text-amber-400' :
                'bg-rose-500/20 text-rose-400'}
            `}>
              {property.score_grade}
            </div>
            <span className="text-xs text-gray-500">Deal Score</span>
          </div>
        )}
      </div>
    </motion.div>
  )
}

function PropertyDetail({ property, onClose }: { property: any; onClose: () => void }) {
  const status = statusConfig[property.status] || statusConfig.new_property
  const zillow = property.zillow_enrichment
  const skipTraces = property.skip_traces || []
  const photos = zillow?.photos || []

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="bg-[#111318] border border-[#1E2130] rounded-xl overflow-hidden"
    >
      {/* Header */}
      <div className="relative">
        {photos.length > 0 ? (
          <div className="h-48 overflow-hidden">
            <img src={photos[0]} alt={property.address} className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#111318] via-[#111318]/30 to-transparent" />
          </div>
        ) : (
          <div className="h-32 bg-gradient-to-br from-[#1A1D27] to-[#111318]" />
        )}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 w-8 h-8 rounded-lg bg-black/50 backdrop-blur flex items-center justify-center text-white hover:bg-black/70 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
        {photos.length > 1 && (
          <div className="absolute bottom-3 right-3 flex items-center gap-1 px-2 py-1 rounded-md bg-black/50 backdrop-blur text-xs text-white">
            <Image className="w-3 h-3" />
            {photos.length} photos
          </div>
        )}
      </div>

      <div className="p-5 space-y-5">
        {/* Title */}
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold uppercase ${status.bg} ${status.color}`}>
              {status.label}
            </span>
            {property.property_type && (
              <span className="text-xs text-gray-500 capitalize">{property.property_type.replace(/_/g, ' ')}</span>
            )}
          </div>
          <h2 className="text-lg font-bold text-white">{property.address || property.title}</h2>
          <p className="text-sm text-gray-400 flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            {property.city}, {property.state} {property.zip_code}
          </p>
        </div>

        {/* Price & Zestimate */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg bg-[#1A1D27] border border-[#2A2D3A]">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider">List Price</p>
            <p className="text-xl font-bold text-white mt-1">
              {property.price ? `$${Number(property.price).toLocaleString()}` : 'N/A'}
            </p>
          </div>
          {zillow?.zestimate && (
            <div className="p-3 rounded-lg bg-[#1A1D27] border border-[#2A2D3A]">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">Zestimate</p>
              <p className="text-xl font-bold text-emerald-400 mt-1">
                ${Number(zillow.zestimate).toLocaleString()}
              </p>
            </div>
          )}
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-3 gap-2">
          {[
            { icon: Bed, label: 'Beds', value: property.bedrooms },
            { icon: Bath, label: 'Baths', value: property.bathrooms },
            { icon: Square, label: 'Sqft', value: property.square_feet ? Number(property.square_feet).toLocaleString() : null },
            { icon: Home, label: 'Lot', value: property.lot_size ? `${Number(property.lot_size).toLocaleString()} sqft` : null },
            { icon: Calendar, label: 'Built', value: property.year_built },
            { icon: BarChart3, label: 'Score', value: property.score_grade || 'N/A' },
          ].filter(d => d.value).map((detail) => (
            <div key={detail.label} className="p-2.5 rounded-lg bg-[#0B0D15] text-center">
              <detail.icon className="w-3.5 h-3.5 text-gray-500 mx-auto" />
              <p className="text-sm font-semibold text-white mt-1">{detail.value}</p>
              <p className="text-[10px] text-gray-500">{detail.label}</p>
            </div>
          ))}
        </div>

        {/* Zillow extras */}
        {zillow && (
          <div className="space-y-3">
            {zillow.rent_zestimate && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-[#1A1D27]">
                <span className="text-xs text-gray-400">Rent Estimate</span>
                <span className="text-sm font-semibold text-emerald-400">${Number(zillow.rent_zestimate).toLocaleString()}/mo</span>
              </div>
            )}
            {zillow.description && (
              <div>
                <p className="text-xs font-medium text-gray-400 mb-1">Description</p>
                <p className="text-xs text-gray-500 leading-relaxed line-clamp-4">{zillow.description}</p>
              </div>
            )}
            {zillow.hdp_url && (
              <a
                href={zillow.hdp_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                <Globe className="w-3 h-3" />
                View on Zillow
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        )}

        {/* Skip Traces */}
        {skipTraces.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Owner Info</p>
            {skipTraces.map((trace: any) => (
              <div key={trace.id} className="p-3 rounded-lg bg-[#1A1D27] border border-[#2A2D3A] space-y-2">
                <p className="text-sm font-medium text-white">{trace.owner_name}</p>
                {trace.phone_numbers?.length > 0 && (
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <Phone className="w-3 h-3" />{trace.phone_numbers[0]}
                  </p>
                )}
                {trace.emails?.length > 0 && (
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <Mail className="w-3 h-3" />{trace.emails[0]}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default function PropertiesPage() {
  const [properties, setProperties] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [selected, setSelected] = useState<any>(null)

  const fetchProperties = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: '200' })
      if (statusFilter !== 'all') params.set('status', statusFilter)
      if (typeFilter !== 'all') params.set('property_type', typeFilter)
      const res = await fetch(`${API}/properties/?${params}`)
      const data = await res.json()
      setProperties(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to fetch properties:', err)
    } finally {
      setLoading(false)
    }
  }, [statusFilter, typeFilter])

  useEffect(() => {
    fetchProperties()
  }, [fetchProperties])

  // Realtime updates
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

  const filtered = properties.filter((p) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      p.address?.toLowerCase().includes(q) ||
      p.title?.toLowerCase().includes(q) ||
      p.city?.toLowerCase().includes(q) ||
      p.zip_code?.includes(q)
    )
  })

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <h1 className="text-2xl font-bold text-white">Properties</h1>
        <p className="text-sm text-gray-500 mt-1">{filtered.length} properties found</p>
      </motion.div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by address, city, or zip..."
            className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-[#111318] border border-[#1E2130] text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2.5 rounded-lg bg-[#111318] border border-[#1E2130] text-sm text-gray-300 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer"
        >
          <option value="all">All Status</option>
          <option value="new_property">New</option>
          <option value="under_contract">Under Contract</option>
          <option value="closed">Closed</option>
          <option value="archived">Archived</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2.5 rounded-lg bg-[#111318] border border-[#1E2130] text-sm text-gray-300 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer"
        >
          <option value="all">All Types</option>
          <option value="house">House</option>
          <option value="condo">Condo</option>
          <option value="townhouse">Townhouse</option>
          <option value="multi_family">Multi-Family</option>
          <option value="land">Land</option>
          <option value="commercial">Commercial</option>
        </select>
        <button
          onClick={() => { setLoading(true); fetchProperties() }}
          className="px-4 py-2.5 rounded-lg bg-[#1A1D27] border border-[#2A2D3A] text-sm text-gray-300 hover:text-white hover:border-blue-500/30 transition-all flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Content */}
      <div className="flex gap-6">
        {/* Grid */}
        <div className="flex-1">
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="rounded-xl bg-[#111318] border border-[#1E2130] h-64 animate-pulse" />
              ))}
            </div>
          ) : filtered.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              <AnimatePresence>
                {filtered.map((prop) => (
                  <PropertyCard
                    key={prop.id}
                    property={prop}
                    onSelect={setSelected}
                    isSelected={selected?.id === prop.id}
                  />
                ))}
              </AnimatePresence>
            </div>
          ) : (
            <div className="text-center py-20">
              <Building2 className="w-12 h-12 text-gray-700 mx-auto mb-3" />
              <p className="text-gray-400 font-medium">No properties found</p>
              <p className="text-sm text-gray-600 mt-1">Try adjusting your search or filters</p>
            </div>
          )}
        </div>

        {/* Detail Panel */}
        <AnimatePresence>
          {selected && (
            <div className="hidden lg:block w-[380px] flex-shrink-0">
              <div className="sticky top-6">
                <PropertyDetail property={selected} onClose={() => setSelected(null)} />
              </div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
