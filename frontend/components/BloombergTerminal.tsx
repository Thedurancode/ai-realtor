'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getContracts, getProperties } from '@/lib/api'
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
  lastUpdated: Date
}

interface APIEndpoint {
  method: string
  path: string
  description: string
  lastCall?: Date
  status?: 'success' | 'error' | 'pending'
}

export const BloombergTerminal = () => {
  const [stats, setStats] = useState<Stats>({
    properties: 0,
    contracts: 0,
    contacts: 0,
    notifications: 0,
    agents: 0,
    totalValue: 0,
    avgPrice: 0,
    lastUpdated: new Date()
  })

  const [apiActivity, setApiActivity] = useState<APIEndpoint[]>([])
  const [recentProperties, setRecentProperties] = useState<any[]>([])
  const [recentContracts, setRecentContracts] = useState<any[]>([])
  const [liveData, setLiveData] = useState<any[]>([])

  // Define all API endpoints
  const endpoints: APIEndpoint[] = [
    { method: 'GET', path: '/properties/', description: 'List all properties' },
    { method: 'POST', path: '/properties/', description: 'Create property' },
    { method: 'GET', path: '/properties/{id}', description: 'Get property details' },
    { method: 'GET', path: '/contracts/', description: 'List all contracts' },
    { method: 'POST', path: '/contracts/', description: 'Create contract' },
    { method: 'GET', path: '/contacts/', description: 'List all contacts' },
    { method: 'POST', path: '/contacts/', description: 'Create contact' },
    { method: 'GET', path: '/notifications/', description: 'List notifications' },
    { method: 'POST', path: '/notifications/', description: 'Send notification' },
    { method: 'POST', path: '/context/enrich', description: 'Enrich with Zillow' },
    { method: 'GET', path: '/agents/', description: 'List agents' },
    { method: 'POST', path: '/agents/', description: 'Create agent' },
  ]

  // Fetch all stats
  const fetchStats = async () => {
    try {
      const [properties, contracts, contacts, notifications, agents] = await Promise.all([
        axios.get(`${API_BASE_URL}/properties/`),
        axios.get(`${API_BASE_URL}/contracts/`),
        axios.get(`${API_BASE_URL}/contacts/`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE_URL}/notifications/`),
        axios.get(`${API_BASE_URL}/agents/`),
      ])

      const totalValue = properties.data.reduce((sum: number, p: any) => sum + (p.price || 0), 0)
      const avgPrice = properties.data.length > 0 ? totalValue / properties.data.length : 0

      setStats({
        properties: properties.data.length,
        contracts: contracts.data.length,
        contacts: contacts.data.length,
        notifications: notifications.data.length,
        agents: agents.data.length,
        totalValue,
        avgPrice,
        lastUpdated: new Date()
      })

      setRecentProperties(properties.data.slice(0, 5))
      setRecentContracts(contracts.data.slice(0, 5))
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 2000) // Update every 2 seconds
    return () => clearInterval(interval)
  }, [])

  // Track API activity
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).trackAPICall = (method: string, path: string, status: 'success' | 'error') => {
        setApiActivity(prev => [
          { method, path, description: '', lastCall: new Date(), status },
          ...prev.slice(0, 9)
        ])
      }
    }
  }, [])

  const StatBox = ({ label, value, sublabel, trend, color }: any) => (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-black border-2 ${color} p-4`}
    >
      <div className="text-[10px] font-mono tracking-wider text-gray-400 mb-1">{label}</div>
      <div className="flex items-end gap-2">
        <div className={`text-4xl font-bold font-mono ${color.replace('border-', 'text-')}`}>
          {value}
        </div>
        {trend && (
          <div className="text-sm text-green-400 mb-1">▲ {trend}</div>
        )}
      </div>
      {sublabel && (
        <div className="text-[10px] text-gray-500 mt-1 font-mono">{sublabel}</div>
      )}
    </motion.div>
  )

  return (
    <div className="min-h-screen bg-black text-white font-mono p-4">
      {/* Header Bar - Bloomberg Style */}
      <div className="bg-gradient-to-r from-orange-600 to-orange-500 px-6 py-2 mb-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="text-2xl font-bold">AI REALTOR</div>
          <div className="text-sm opacity-90">REAL-TIME PROPERTY MANAGEMENT SYSTEM</div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <motion.div
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="w-2 h-2 bg-green-400 rounded-full"
            />
            <span className="text-sm">LIVE</span>
          </div>
          <div className="text-sm">
            {stats.lastUpdated.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-7 gap-3 mb-4">
        <StatBox
          label="PROPERTIES"
          value={stats.properties}
          sublabel={`$${(stats.totalValue / 1000000).toFixed(1)}M TOTAL`}
          color="border-orange-500"
        />
        <StatBox
          label="CONTRACTS"
          value={stats.contracts}
          sublabel="ACTIVE DEALS"
          color="border-green-500"
        />
        <StatBox
          label="CONTACTS"
          value={stats.contacts}
          sublabel="LEADS IN SYSTEM"
          color="border-blue-500"
        />
        <StatBox
          label="NOTIFICATIONS"
          value={stats.notifications}
          sublabel="ALERTS SENT"
          color="border-purple-500"
        />
        <StatBox
          label="AGENTS"
          value={stats.agents}
          sublabel="ACTIVE USERS"
          color="border-cyan-500"
        />
        <StatBox
          label="AVG PRICE"
          value={`$${(stats.avgPrice / 1000000).toFixed(1)}M`}
          sublabel="PER PROPERTY"
          color="border-yellow-500"
        />
        <StatBox
          label="UPTIME"
          value="99.9%"
          sublabel="API STATUS"
          trend="+0.1%"
          color="border-emerald-500"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-3 gap-4">
        {/* Left Column - API Endpoints */}
        <div className="space-y-4">
          <div className="bg-black border-2 border-orange-500">
            <div className="bg-orange-500/20 border-b border-orange-500 px-4 py-2">
              <div className="text-sm font-bold">API ENDPOINTS</div>
            </div>
            <div className="p-4 max-h-[600px] overflow-y-auto custom-scrollbar">
              <div className="space-y-2">
                {endpoints.map((endpoint, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="border border-gray-800 p-3 hover:border-orange-500 transition-colors"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-bold px-2 py-1 ${
                        endpoint.method === 'GET'
                          ? 'bg-blue-500/20 text-blue-400'
                          : 'bg-green-500/20 text-green-400'
                      }`}>
                        {endpoint.method}
                      </span>
                      <span className="text-xs text-orange-400 font-mono">{endpoint.path}</span>
                    </div>
                    <div className="text-[10px] text-gray-500">{endpoint.description}</div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Middle Column - Recent Properties */}
        <div className="space-y-4">
          <div className="bg-black border-2 border-green-500">
            <div className="bg-green-500/20 border-b border-green-500 px-4 py-2">
              <div className="text-sm font-bold">PROPERTIES FEED</div>
            </div>
            <div className="p-4 max-h-[600px] overflow-y-auto custom-scrollbar">
              <div className="space-y-3">
                {recentProperties.map((property, i) => (
                  <motion.div
                    key={property.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.1 }}
                    className="border-l-4 border-green-500 bg-green-500/5 p-3"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="text-sm font-bold text-green-400">{property.title}</div>
                      <div className="text-xs bg-green-500/20 text-green-400 px-2 py-1">
                        ${(property.price / 1000000).toFixed(1)}M
                      </div>
                    </div>
                    <div className="text-[10px] text-gray-400 mb-1">{property.address}</div>
                    <div className="flex gap-3 text-[10px] text-gray-500">
                      <span>{property.bedrooms} BD</span>
                      <span>{property.bathrooms} BA</span>
                      <span>{property.square_feet?.toLocaleString()} SF</span>
                    </div>
                    {property.zillow_enrichment && (
                      <div className="mt-2 pt-2 border-t border-green-500/20">
                        <div className="text-[10px] text-orange-400">
                          ZESTIMATE: ${(property.zillow_enrichment.zestimate / 1000000).toFixed(2)}M
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Live Activity & Contracts */}
        <div className="space-y-4">
          {/* API Activity */}
          <div className="bg-black border-2 border-cyan-500">
            <div className="bg-cyan-500/20 border-b border-cyan-500 px-4 py-2">
              <div className="text-sm font-bold">LIVE API ACTIVITY</div>
            </div>
            <div className="p-4 max-h-[280px] overflow-y-auto custom-scrollbar">
              <div className="space-y-2">
                <AnimatePresence mode="popLayout">
                  {apiActivity.map((activity, i) => (
                    <motion.div
                      key={`${activity.path}-${activity.lastCall?.getTime()}`}
                      initial={{ opacity: 0, x: 20, height: 0 }}
                      animate={{ opacity: 1, x: 0, height: 'auto' }}
                      exit={{ opacity: 0, x: -20, height: 0 }}
                      className="border border-cyan-500/30 p-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-bold ${
                            activity.method === 'GET' ? 'text-blue-400' : 'text-green-400'
                          }`}>
                            {activity.method}
                          </span>
                          <span className="text-[10px] text-cyan-400">{activity.path}</span>
                        </div>
                        <span className={`text-[10px] ${
                          activity.status === 'success' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {activity.status === 'success' ? '✓' : '✗'}
                        </span>
                      </div>
                      <div className="text-[9px] text-gray-500 mt-1">
                        {activity.lastCall?.toLocaleTimeString()}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </div>

          {/* Contracts */}
          <div className="bg-black border-2 border-purple-500">
            <div className="bg-purple-500/20 border-b border-purple-500 px-4 py-2">
              <div className="text-sm font-bold">CONTRACTS</div>
            </div>
            <div className="p-4 max-h-[280px] overflow-y-auto custom-scrollbar">
              <div className="space-y-2">
                {recentContracts.map((contract, i) => (
                  <motion.div
                    key={contract.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.1 }}
                    className="border border-purple-500/30 p-2"
                  >
                    <div className="text-xs text-purple-400 font-bold mb-1">
                      CONTRACT #{contract.id}
                    </div>
                    <div className="text-[10px] text-gray-400">
                      Property: {contract.property_id}
                    </div>
                    <div className="text-[10px] text-gray-500">
                      {new Date(contract.created_at).toLocaleDateString()}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Ticker */}
      <div className="mt-4 bg-gradient-to-r from-orange-600 to-orange-500 px-6 py-2">
        <motion.div
          animate={{ x: [0, -2000] }}
          transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
          className="whitespace-nowrap text-sm"
        >
          {recentProperties.map((p, i) => (
            <span key={i} className="mr-12">
              <span className="text-white font-bold">{p.title}</span>
              <span className="text-orange-200 ml-2">${(p.price / 1000000).toFixed(1)}M</span>
              <span className="text-orange-300 ml-2">{p.address}</span>
            </span>
          ))}
        </motion.div>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.3);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(249, 115, 22, 0.5);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(249, 115, 22, 0.8);
        }
      `}</style>
    </div>
  )
}
