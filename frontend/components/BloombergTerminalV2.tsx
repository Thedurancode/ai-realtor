'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Stats {
  properties: number
  contracts: number
  contacts: number
  notifications: number
  agents: number
  totalValue: number
  avgPrice: number
  activeListings: number
  pendingContracts: number
}

export const BloombergTerminalV2 = () => {
  const [stats, setStats] = useState<Stats>({
    properties: 0,
    contracts: 0,
    contacts: 0,
    notifications: 0,
    agents: 0,
    totalValue: 0,
    avgPrice: 0,
    activeListings: 0,
    pendingContracts: 0
  })

  const [properties, setProperties] = useState<any[]>([])
  const [contracts, setContracts] = useState<any[]>([])
  const [notifications, setNotifications] = useState<any[]>([])
  const [apiActivity, setApiActivity] = useState<any[]>([])
  const [time, setTime] = useState(new Date())
  const [scrollPaused, setScrollPaused] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)

  // Fetch all data
  const fetchData = async () => {
    try {
      const [propsRes, contractsRes, notificationsRes, agentsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/properties/`),
        axios.get(`${API_BASE_URL}/contracts/`),
        axios.get(`${API_BASE_URL}/notifications/`),
        axios.get(`${API_BASE_URL}/agents/`).catch(() => ({ data: [] })),
      ])

      const props = propsRes.data
      const totalValue = props.reduce((sum: number, p: any) => sum + (p.price || 0), 0)
      const activeListings = props.filter((p: any) => p.status === 'available').length

      setProperties(props)
      setContracts(contractsRes.data)
      setNotifications(notificationsRes.data)

      setStats({
        properties: props.length,
        contracts: contractsRes.data.length,
        contacts: 0,
        notifications: notificationsRes.data.length,
        agents: agentsRes.data.length,
        totalValue,
        avgPrice: props.length > 0 ? totalValue / props.length : 0,
        activeListings,
        pendingContracts: contractsRes.data.length
      })
    } catch (error) {
      console.error('Error fetching data:', error)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 3000)
    const timeInterval = setInterval(() => setTime(new Date()), 1000)

    return () => {
      clearInterval(interval)
      clearInterval(timeInterval)
    }
  }, [])

  // Track API calls
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).trackAPICall = (method: string, path: string, status: string) => {
        setApiActivity(prev => [
          { method, path, status, time: new Date() },
          ...prev.slice(0, 14)
        ])
      }
    }
  }, [])

  // Simulate initial API activity on mount
  useEffect(() => {
    const initialActivity = [
      { method: 'GET', path: '/properties/', status: 'success', time: new Date() },
      { method: 'GET', path: '/contracts/', status: 'success', time: new Date(Date.now() - 1000) },
      { method: 'GET', path: '/notifications/', status: 'success', time: new Date(Date.now() - 2000) },
    ]
    setApiActivity(initialActivity)
  }, [])

  const formatPrice = (price: number) => {
    if (price >= 1000000) return `$${(price / 1000000).toFixed(2)}M`
    if (price >= 1000) return `$${(price / 1000).toFixed(0)}K`
    return `$${price}`
  }

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  return (
    <div className="h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white overflow-hidden flex flex-col">
      {/* Top Header Bar - Modern Gradient */}
      <div className="bg-gradient-to-r from-orange-600/90 via-orange-500/90 to-orange-600/90 backdrop-blur-xl px-6 py-3 flex items-center justify-between border-b border-orange-400/30 shadow-2xl shadow-orange-500/20">
        <div className="flex items-center gap-8">
          <div className="text-2xl font-black tracking-tight bg-gradient-to-r from-white to-orange-100 bg-clip-text text-transparent">AI REALTOR</div>
          <div className="text-sm font-medium text-white/90">Real Estate Intelligence Platform</div>
          <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm px-3 py-1.5 rounded-full border border-white/20">
            <motion.div
              animate={{ scale: [1, 1.3, 1], opacity: [1, 0.5, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="w-2 h-2 bg-emerald-400 rounded-full shadow-lg shadow-emerald-400/50"
            />
            <span className="text-xs font-bold text-white">LIVE</span>
          </div>
        </div>
        <div className="flex items-center gap-6 text-sm font-medium text-white/90">
          <div className="flex items-center gap-2">
            <span className="text-xs text-white/60">NYC</span>
            <span>{time.toLocaleTimeString('en-US', { hour12: false })}</span>
          </div>
          <div>{time.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</div>

          {/* Fullscreen Button */}
          <motion.button
            onClick={toggleFullscreen}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="bg-white/10 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-white/20 hover:bg-white/20 transition-all flex items-center gap-2"
          >
            {isFullscreen ? (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
                </svg>
                <span className="text-xs font-bold">EXIT</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
                <span className="text-xs font-bold">FULLSCREEN</span>
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* Stats Bar - Modern Cards */}
      <div className="grid grid-cols-9 gap-3 p-4 bg-slate-900/50">
        {[
          { label: 'PORTFOLIO', value: formatPrice(stats.totalValue), sub: `${stats.properties} PROPS`, gradient: 'from-orange-500/20 to-orange-600/20', border: 'border-orange-500/50', glow: 'shadow-orange-500/20' },
          { label: 'AVG PRICE', value: formatPrice(stats.avgPrice), sub: 'PER UNIT', gradient: 'from-emerald-500/20 to-emerald-600/20', border: 'border-emerald-500/50', glow: 'shadow-emerald-500/20' },
          { label: 'ACTIVE', value: stats.activeListings, sub: 'LISTINGS', gradient: 'from-blue-500/20 to-blue-600/20', border: 'border-blue-500/50', glow: 'shadow-blue-500/20' },
          { label: 'CONTRACTS', value: stats.contracts, sub: 'PENDING', gradient: 'from-purple-500/20 to-purple-600/20', border: 'border-purple-500/50', glow: 'shadow-purple-500/20' },
          { label: 'AGENTS', value: stats.agents, sub: 'ONLINE', gradient: 'from-cyan-500/20 to-cyan-600/20', border: 'border-cyan-500/50', glow: 'shadow-cyan-500/20' },
          { label: 'ALERTS', value: stats.notifications, sub: 'TOTAL', gradient: 'from-yellow-500/20 to-yellow-600/20', border: 'border-yellow-500/50', glow: 'shadow-yellow-500/20' },
          { label: 'API', value: apiActivity.length, sub: 'CALLS', gradient: 'from-pink-500/20 to-pink-600/20', border: 'border-pink-500/50', glow: 'shadow-pink-500/20' },
          { label: 'UPTIME', value: '99.9%', sub: 'STATUS', gradient: 'from-emerald-500/20 to-emerald-600/20', border: 'border-emerald-500/50', glow: 'shadow-emerald-500/20' },
          { label: 'RESPONSE', value: '45ms', sub: 'AVG', gradient: 'from-indigo-500/20 to-indigo-600/20', border: 'border-indigo-500/50', glow: 'shadow-indigo-500/20' },
        ].map((stat, i) => (
          <div
            key={stat.label}
            className={`bg-gradient-to-br ${stat.gradient} backdrop-blur-sm border ${stat.border} rounded-xl p-3 shadow-lg ${stat.glow} hover:scale-105 transition-all duration-300`}
          >
            <div className="text-[9px] text-gray-300 font-semibold mb-1 tracking-wider">{stat.label}</div>
            <div className="text-2xl font-black leading-none mb-1 bg-gradient-to-br from-white to-gray-300 bg-clip-text text-transparent">{stat.value}</div>
            <div className="text-[8px] text-gray-400 font-medium">{stat.sub}</div>
          </div>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 grid grid-cols-3 gap-4 p-4 overflow-hidden">

        {/* Left Column - Property Listings */}
        <div className="col-span-1 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-orange-500/30 rounded-2xl flex flex-col shadow-2xl shadow-orange-500/10 overflow-hidden">
          <div className="bg-gradient-to-r from-orange-500/20 to-orange-600/20 border-b border-orange-500/30 px-4 py-3 flex items-center justify-between backdrop-blur-sm">
            <span className="text-sm font-bold text-orange-300">PROPERTIES</span>
            <span className="text-sm font-black text-orange-400 bg-orange-500/20 px-2 py-1 rounded-full">{properties.length}</span>
          </div>
          <div
            className="flex-1 overflow-hidden relative"
            onMouseEnter={() => setScrollPaused(true)}
            onMouseLeave={() => setScrollPaused(false)}
          >
            <motion.div
              animate={scrollPaused ? {} : { y: [0, -100] }}
              transition={{
                duration: 20,
                repeat: Infinity,
                ease: "linear"
              }}
              className="p-3 space-y-3"
            >
              {[...properties, ...properties].map((prop, i) => (
                <div
                  key={`${prop.id}-${i}`}
                  className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur-sm border border-orange-500/30 rounded-xl p-4 hover:border-orange-400/60 hover:shadow-xl hover:shadow-orange-500/20 transition-all duration-300 cursor-pointer flex gap-4 group"
                >
                  {/* Property Image */}
                  {prop.zillow_enrichment?.photos?.[0] ? (
                    <div className="flex-shrink-0 w-32 h-32 rounded-lg overflow-hidden border-2 border-orange-500/40 shadow-lg group-hover:scale-105 transition-transform duration-300">
                      <img
                        src={prop.zillow_enrichment.photos[0]}
                        alt={prop.title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : (
                    <div className="flex-shrink-0 w-32 h-32 rounded-lg border-2 border-orange-500/40 bg-gradient-to-br from-orange-500/10 to-orange-600/10 flex items-center justify-center shadow-lg">
                      <div className="text-5xl">🏠</div>
                    </div>
                  )}

                  {/* Property Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start mb-2">
                      <div className="text-lg font-bold text-orange-300 leading-tight">{prop.title}</div>
                    </div>
                    <div className="text-3xl font-black bg-gradient-to-r from-emerald-400 to-green-400 bg-clip-text text-transparent mb-2">{formatPrice(prop.price)}</div>
                    <div className="text-sm text-gray-300 mb-2 font-medium">{prop.address}, {prop.city}</div>
                    <div className="flex gap-3 text-xs text-gray-400 mb-2">
                      <span className="bg-slate-700/50 px-2 py-1 rounded-md font-semibold">{prop.bedrooms} BD</span>
                      <span className="bg-slate-700/50 px-2 py-1 rounded-md font-semibold">{prop.bathrooms} BA</span>
                      <span className="bg-slate-700/50 px-2 py-1 rounded-md font-semibold">{prop.square_feet} SF</span>
                      <span className="bg-orange-500/20 text-orange-300 px-2 py-1 rounded-md font-bold">{prop.property_type?.toUpperCase()}</span>
                    </div>
                    {prop.zillow_enrichment && (
                      <div className="pt-2 border-t border-orange-500/30">
                        <div className="text-sm text-cyan-300 font-semibold">
                          ZESTIMATE: {formatPrice(prop.zillow_enrichment.zestimate)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </motion.div>
          </div>
        </div>

        {/* Middle Column - Activity Cards */}
        <div className="col-span-1 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-cyan-500/30 rounded-2xl flex flex-col shadow-2xl shadow-cyan-500/10 overflow-hidden">
          <div className="bg-gradient-to-r from-cyan-500/20 to-cyan-600/20 border-b border-cyan-500/30 px-4 py-3 flex items-center justify-between backdrop-blur-sm">
            <span className="text-sm font-bold text-cyan-300">LIVE ACTIVITY</span>
            <motion.div
              animate={{ opacity: [1, 0.4, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="flex items-center gap-2 text-xs font-bold text-cyan-300"
            >
              <div className="w-2 h-2 bg-cyan-400 rounded-full shadow-lg shadow-cyan-400/50" />
              STREAMING
            </motion.div>
          </div>
          <div className="flex-1 overflow-y-auto custom-scroll p-4 space-y-3">

            {/* Recent Properties Card */}
            {properties.slice(0, 2).map((prop) => (
              <motion.div
                key={`activity-prop-${prop.id}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gradient-to-br from-orange-500/10 to-orange-600/10 border border-orange-500/40 rounded-xl p-4 hover:border-orange-400/60 hover:shadow-xl hover:shadow-orange-500/20 transition-all"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-16 h-16 rounded-lg bg-gradient-to-br from-orange-500/20 to-orange-600/20 flex items-center justify-center text-3xl border border-orange-500/30">
                    🏠
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-bold text-orange-300 mb-1">NEW PROPERTY</div>
                    <div className="text-sm font-bold text-white mb-1 truncate">{prop.title}</div>
                    <div className="text-lg font-black bg-gradient-to-r from-emerald-400 to-green-400 bg-clip-text text-transparent">
                      {formatPrice(prop.price)}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">{prop.address}</div>
                  </div>
                </div>
              </motion.div>
            ))}

            {/* Notifications Card */}
            {notifications.slice(0, 2).map((notif) => (
              <motion.div
                key={`activity-notif-${notif.id}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={`rounded-xl p-4 border hover:shadow-xl transition-all ${
                  notif.priority === 'high'
                    ? 'bg-gradient-to-br from-red-500/10 to-red-600/10 border-red-500/40 hover:border-red-400/60 hover:shadow-red-500/20'
                    : notif.priority === 'medium'
                    ? 'bg-gradient-to-br from-yellow-500/10 to-yellow-600/10 border-yellow-500/40 hover:border-yellow-400/60 hover:shadow-yellow-500/20'
                    : 'bg-gradient-to-br from-blue-500/10 to-blue-600/10 border-blue-500/40 hover:border-blue-400/60 hover:shadow-blue-500/20'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`flex-shrink-0 w-16 h-16 rounded-lg flex items-center justify-center text-3xl border ${
                    notif.priority === 'high'
                      ? 'bg-gradient-to-br from-red-500/20 to-red-600/20 border-red-500/30'
                      : notif.priority === 'medium'
                      ? 'bg-gradient-to-br from-yellow-500/20 to-yellow-600/20 border-yellow-500/30'
                      : 'bg-gradient-to-br from-blue-500/20 to-blue-600/20 border-blue-500/30'
                  }`}>
                    🔔
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-bold text-purple-300 mb-1">NOTIFICATION</div>
                    <div className="text-sm font-bold text-white mb-1">{notif.title}</div>
                    <div className="text-xs text-gray-300 leading-tight">{notif.message}</div>
                  </div>
                </div>
              </motion.div>
            ))}

            {/* Contracts Card */}
            {contracts.slice(0, 1).map((contract) => (
              <motion.div
                key={`activity-contract-${contract.id}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/40 rounded-xl p-4 hover:border-purple-400/60 hover:shadow-xl hover:shadow-purple-500/20 transition-all"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-16 h-16 rounded-lg bg-gradient-to-br from-purple-500/20 to-purple-600/20 flex items-center justify-center text-3xl border border-purple-500/30">
                    📝
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-bold text-purple-300 mb-1">ACTIVE CONTRACT</div>
                    <div className="text-sm font-bold text-white mb-1">Contract #{contract.id}</div>
                    <div className="text-xs text-gray-300">Property ID: {contract.property_id}</div>
                    <div className="mt-2">
                      <span className="text-[9px] bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-full font-bold border border-emerald-500/30">
                        ACTIVE
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}

          </div>
        </div>

        {/* Right Column - Notifications & Contracts */}
        <div className="col-span-1 flex flex-col gap-0.5">

          {/* Notifications */}
          <div className="flex-1 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-purple-500/30 rounded-2xl flex flex-col shadow-2xl shadow-purple-500/10 overflow-hidden">
            <div className="bg-gradient-to-r from-purple-500/20 to-purple-600/20 border-b border-purple-500/30 px-4 py-3 backdrop-blur-sm">
              <span className="text-sm font-bold text-purple-300">NOTIFICATIONS</span>
            </div>
            <div className="flex-1 overflow-y-auto custom-scroll p-3 space-y-2">
              {notifications.slice(0, 6).map((notif, i) => (
                <div
                  key={notif.id}
                  className={`rounded-lg p-3 border-l-4 ${
                    notif.priority === 'high' ? 'border-red-500 bg-gradient-to-r from-red-500/10 to-red-600/10' :
                    notif.priority === 'medium' ? 'border-yellow-500 bg-gradient-to-r from-yellow-500/10 to-yellow-600/10' :
                    'border-blue-500 bg-gradient-to-r from-blue-500/10 to-blue-600/10'
                  } hover:scale-[1.02] transition-transform`}
                >
                  <div className="text-xs font-bold text-purple-300 mb-1.5">{notif.title}</div>
                  <div className="text-[10px] text-gray-300 leading-tight mb-1.5">{notif.message}</div>
                  <div className="text-[8px] text-gray-500">
                    {new Date(notif.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Contracts */}
          <div className="flex-1 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-yellow-500/30 rounded-2xl flex flex-col shadow-2xl shadow-yellow-500/10 overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-500/20 to-yellow-600/20 border-b border-yellow-500/30 px-4 py-3 backdrop-blur-sm">
              <span className="text-sm font-bold text-yellow-300">CONTRACTS</span>
            </div>
            <div className="flex-1 overflow-y-auto custom-scroll p-3 space-y-2">
              {contracts.slice(0, 5).map((contract, i) => (
                <div
                  key={contract.id}
                  className="bg-gradient-to-r from-yellow-500/10 to-yellow-600/10 border border-yellow-500/30 rounded-lg p-3 hover:border-yellow-400/50 hover:shadow-lg hover:shadow-yellow-500/20 transition-all"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-bold text-yellow-300">CONTRACT #{contract.id}</span>
                    <span className="text-[9px] bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-full font-bold border border-emerald-500/30">ACTIVE</span>
                  </div>
                  <div className="text-[10px] text-gray-300 mb-1">Property ID: {contract.property_id}</div>
                  <div className="text-[9px] text-gray-500">
                    {new Date(contract.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>

      {/* Bottom Ticker - Modern */}
      <div className="bg-gradient-to-r from-orange-600/90 via-orange-500/90 to-orange-600/90 backdrop-blur-xl py-2 border-t border-orange-400/30 overflow-hidden shadow-2xl shadow-orange-500/20">
        <motion.div
          animate={{ x: ['0%', '-50%'] }}
          transition={{ duration: 40, repeat: Infinity, ease: 'linear' }}
          className="flex whitespace-nowrap"
        >
          {[...properties, ...properties].map((prop, i) => (
            <div key={i} className="inline-flex items-center mx-8 text-sm">
              <span className="font-black text-white">{prop.title}</span>
              <span className="mx-3 text-white/40">•</span>
              <span className="font-black bg-gradient-to-r from-emerald-300 to-green-300 bg-clip-text text-transparent">{formatPrice(prop.price)}</span>
              <span className="mx-3 text-white/40">•</span>
              <span className="font-medium text-white/90">{prop.address}</span>
            </div>
          ))}
        </motion.div>
      </div>

      <style jsx>{`
        .custom-scroll::-webkit-scrollbar {
          width: 3px;
        }
        .custom-scroll::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.3);
        }
        .custom-scroll::-webkit-scrollbar-thumb {
          background: rgba(249, 115, 22, 0.5);
        }
        .custom-scroll::-webkit-scrollbar-thumb:hover {
          background: rgba(249, 115, 22, 0.8);
        }
      `}</style>
    </div>
  )
}
