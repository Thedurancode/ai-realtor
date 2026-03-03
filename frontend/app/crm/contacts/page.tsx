'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Users,
  Search,
  Phone,
  Mail,
  Building2,
  Briefcase,
  X,
  User,
  Plus,
  RefreshCw,
  ChevronRight,
} from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const roleColors: Record<string, string> = {
  buyer: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  seller: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  lawyer: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  contractor: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  inspector: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  lender: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  mortgage_broker: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  title_company: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  appraiser: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  tenant: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  landlord: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  property_manager: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
}

function getInitials(name: string) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

function getAvatarGradient(name: string) {
  const gradients = [
    'from-blue-600 to-violet-600',
    'from-emerald-600 to-teal-600',
    'from-amber-600 to-orange-600',
    'from-rose-600 to-pink-600',
    'from-cyan-600 to-blue-600',
    'from-violet-600 to-purple-600',
    'from-teal-600 to-emerald-600',
  ]
  const index = name.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) % gradients.length
  return gradients[index]
}

function ContactRow({ contact, isSelected, onClick }: { contact: any; isSelected: boolean; onClick: () => void }) {
  const roleColor = roleColors[contact.role?.toLowerCase()] || 'bg-gray-500/10 text-gray-400 border-gray-500/20'

  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      onClick={onClick}
      className={`
        flex items-center gap-4 p-4 rounded-xl cursor-pointer transition-all duration-150
        ${isSelected
          ? 'bg-[#1A1D27] border border-blue-500/30'
          : 'border border-transparent hover:bg-[#111318]'
        }
      `}
    >
      <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${getAvatarGradient(contact.name)} flex items-center justify-center flex-shrink-0`}>
        <span className="text-xs font-bold text-white">{getInitials(contact.name)}</span>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{contact.name}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium capitalize ${roleColor}`}>
            {(contact.role || 'other').replace(/_/g, ' ')}
          </span>
          {contact.company && (
            <span className="text-xs text-gray-500 truncate">{contact.company}</span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {contact.phone && (
          <a href={`tel:${contact.phone}`} onClick={e => e.stopPropagation()} className="w-8 h-8 rounded-lg bg-[#1A1D27] flex items-center justify-center text-gray-500 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors">
            <Phone className="w-3.5 h-3.5" />
          </a>
        )}
        {contact.email && (
          <a href={`mailto:${contact.email}`} onClick={e => e.stopPropagation()} className="w-8 h-8 rounded-lg bg-[#1A1D27] flex items-center justify-center text-gray-500 hover:text-blue-400 hover:bg-blue-500/10 transition-colors">
            <Mail className="w-3.5 h-3.5" />
          </a>
        )}
        <ChevronRight className="w-4 h-4 text-gray-600" />
      </div>
    </motion.div>
  )
}

function ContactDetail({ contact, onClose }: { contact: any; onClose: () => void }) {
  const roleColor = roleColors[contact.role?.toLowerCase()] || 'bg-gray-500/10 text-gray-400 border-gray-500/20'

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="bg-[#111318] border border-[#1E2130] rounded-xl overflow-hidden"
    >
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${getAvatarGradient(contact.name)} flex items-center justify-center`}>
              <span className="text-lg font-bold text-white">{getInitials(contact.name)}</span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">{contact.name}</h3>
              <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold uppercase tracking-wider ${roleColor}`}>
                {(contact.role || 'other').replace(/_/g, ' ')}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-lg bg-[#1A1D27] flex items-center justify-center text-gray-500 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="mt-6 space-y-3">
          {contact.email && (
            <a href={`mailto:${contact.email}`} className="flex items-center gap-3 p-3 rounded-lg bg-[#1A1D27] hover:bg-[#1E2130] transition-colors group">
              <div className="w-9 h-9 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Mail className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <p className="text-[10px] text-gray-500 uppercase tracking-wider">Email</p>
                <p className="text-sm text-white group-hover:text-blue-400 transition-colors">{contact.email}</p>
              </div>
            </a>
          )}
          {contact.phone && (
            <a href={`tel:${contact.phone}`} className="flex items-center gap-3 p-3 rounded-lg bg-[#1A1D27] hover:bg-[#1E2130] transition-colors group">
              <div className="w-9 h-9 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <Phone className="w-4 h-4 text-emerald-400" />
              </div>
              <div>
                <p className="text-[10px] text-gray-500 uppercase tracking-wider">Phone</p>
                <p className="text-sm text-white group-hover:text-emerald-400 transition-colors">{contact.phone}</p>
              </div>
            </a>
          )}
          {contact.company && (
            <div className="flex items-center gap-3 p-3 rounded-lg bg-[#1A1D27]">
              <div className="w-9 h-9 rounded-lg bg-violet-500/10 flex items-center justify-center">
                <Briefcase className="w-4 h-4 text-violet-400" />
              </div>
              <div>
                <p className="text-[10px] text-gray-500 uppercase tracking-wider">Company</p>
                <p className="text-sm text-white">{contact.company}</p>
              </div>
            </div>
          )}
        </div>

        {contact.notes && (
          <div className="mt-5">
            <p className="text-xs font-medium text-gray-400 mb-2">Notes</p>
            <p className="text-sm text-gray-400 leading-relaxed bg-[#0B0D15] rounded-lg p-3">{contact.notes}</p>
          </div>
        )}

        <div className="mt-5 text-[10px] text-gray-600">
          Created {new Date(contact.created_at).toLocaleDateString()}
        </div>
      </div>
    </motion.div>
  )
}

export default function ContactsPage() {
  const [contacts, setContacts] = useState<any[]>([])
  const [properties, setProperties] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [selected, setSelected] = useState<any>(null)

  const fetchData = useCallback(async () => {
    try {
      const propsRes = await fetch(`${API}/properties/?limit=200`)
      const propsData = await propsRes.json()
      const props = Array.isArray(propsData) ? propsData : []
      setProperties(props)

      const allContacts: any[] = []
      await Promise.all(
        props.map(async (p: any) => {
          try {
            const res = await fetch(`${API}/contacts/property/${p.id}`)
            const data = await res.json()
            const contacts = data.contacts || []
            contacts.forEach((c: any) => {
              c._propertyAddress = p.address
              c._propertyId = p.id
            })
            allContacts.push(...contacts)
          } catch {}
        })
      )

      // Deduplicate by id
      const unique = Array.from(new Map(allContacts.map(c => [c.id, c])).values())
      setContacts(unique)
    } catch (err) {
      console.error('Failed to fetch contacts:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const filtered = contacts.filter((c) => {
    if (roleFilter !== 'all' && c.role?.toLowerCase() !== roleFilter) return false
    if (!search) return true
    const q = search.toLowerCase()
    return (
      c.name?.toLowerCase().includes(q) ||
      c.email?.toLowerCase().includes(q) ||
      c.company?.toLowerCase().includes(q) ||
      c.phone?.includes(q)
    )
  })

  const roles = Array.from(new Set(contacts.map(c => c.role?.toLowerCase()).filter(Boolean)))

  return (
    <div className="p-6 lg:p-8 max-w-[1400px] mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <h1 className="text-2xl font-bold text-white">Contacts</h1>
        <p className="text-sm text-gray-500 mt-1">{filtered.length} contacts across {properties.length} properties</p>
      </motion.div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search contacts..."
            className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-[#111318] border border-[#1E2130] text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-3 py-2.5 rounded-lg bg-[#111318] border border-[#1E2130] text-sm text-gray-300 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer"
        >
          <option value="all">All Roles</option>
          {roles.map(role => (
            <option key={role} value={role}>{role.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <button
          onClick={() => { setLoading(true); fetchData() }}
          className="px-4 py-2.5 rounded-lg bg-[#1A1D27] border border-[#2A2D3A] text-sm text-gray-300 hover:text-white hover:border-blue-500/30 transition-all flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Content */}
      <div className="flex gap-6">
        <div className="flex-1 min-w-0">
          {loading ? (
            <div className="space-y-2">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="rounded-xl bg-[#111318] border border-[#1E2130] h-16 animate-pulse" />
              ))}
            </div>
          ) : filtered.length > 0 ? (
            <div className="space-y-1 rounded-xl bg-[#111318] border border-[#1E2130] p-2">
              {filtered.map((contact) => (
                <ContactRow
                  key={contact.id}
                  contact={contact}
                  isSelected={selected?.id === contact.id}
                  onClick={() => setSelected(contact)}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-20">
              <Users className="w-12 h-12 text-gray-700 mx-auto mb-3" />
              <p className="text-gray-400 font-medium">No contacts found</p>
              <p className="text-sm text-gray-600 mt-1">Contacts will appear as they are added to properties</p>
            </div>
          )}
        </div>

        {/* Detail Panel */}
        <AnimatePresence>
          {selected && (
            <div className="hidden lg:block w-[360px] flex-shrink-0">
              <div className="sticky top-6">
                <ContactDetail contact={selected} onClose={() => setSelected(null)} />
              </div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
