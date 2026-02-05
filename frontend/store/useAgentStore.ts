import { create } from 'zustand'

export interface Contract {
  id: number
  template_id: string
  property_id: number
  status: string
  sent_at?: string
  completed_at?: string
  signers: Array<{
    name: string
    email: string
    role: string
    status: string
    signed_at?: string
  }>
}

export interface SkipTrace {
  id: number
  property_id: number
  owner_name?: string
  owner_first_name?: string
  owner_last_name?: string
  phone_numbers: Array<{ number?: string; type?: string; status?: string }>
  emails: Array<{ email?: string; type?: string }>
  mailing_address?: string
  mailing_city?: string
  mailing_state?: string
  mailing_zip?: string
  created_at: string
  updated_at?: string
}

export interface ZillowEnrichment {
  id: number
  property_id: number
  zpid?: number
  zestimate?: number
  zestimate_low?: number
  zestimate_high?: number
  rent_zestimate?: number
  living_area?: number
  lot_size?: number
  lot_area_units?: string
  year_built?: number
  home_type?: string
  home_status?: string
  days_on_zillow?: number
  page_view_count?: number
  favorite_count?: number
  property_tax_rate?: number
  annual_tax_amount?: number
  hdp_url?: string
  zillow_url?: string
  photos?: string[]
  description?: string
  schools?: Array<{
    name?: string
    rating?: number
    grades?: string
    distance?: number
    level?: string
  }>
  tax_history?: Array<{
    year?: number
    amount?: number
  }>
  price_history?: Array<{
    date?: string
    price?: number
    event?: string
  }>
  reso_facts?: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface Property {
  id: number
  title?: string
  description?: string
  address: string
  city?: string
  state?: string
  zip_code?: string
  price: number
  bedrooms: number
  bathrooms: number
  square_feet: number
  lot_size?: number
  year_built?: number
  property_type?: string
  status: string
  agent_id?: number
  created_at?: string
  updated_at?: string
  zillow_enrichment?: ZillowEnrichment
  skip_traces?: SkipTrace[]
}

export interface Notification {
  id: number
  type: string
  priority: string
  title: string
  message: string
  icon?: string
  property_id?: number
  contact_id?: number
  contract_id?: number
  auto_dismiss_seconds?: number
  created_at: string
}

interface AgentState {
  // Agent state
  isSpeaking: boolean
  currentMessage: string
  audioLevel: number

  // Data
  contracts: Contract[]
  properties: Property[]
  currentContract: Contract | null
  currentProperty: Property | null
  focusedProperty: Property | null // Property to show in detail view

  // Enrichment state
  isEnriching: boolean
  enrichingPropertyId: number | null
  enrichingPropertyAddress: string | null

  // Notifications
  notifications: Notification[]

  // Actions
  setIsSpeaking: (speaking: boolean) => void
  setCurrentMessage: (message: string) => void
  setAudioLevel: (level: number) => void
  setContracts: (contracts: Contract[]) => void
  setProperties: (properties: Property[]) => void
  setCurrentContract: (contract: Contract | null) => void
  setCurrentProperty: (property: Property | null) => void
  setFocusedProperty: (property: Property | null) => void
  setEnrichmentStatus: (isEnriching: boolean, propertyId?: number | null, address?: string | null) => void
  addNotification: (notification: Notification) => void
  dismissNotification: (id: number) => void
}

export const useAgentStore = create<AgentState>((set) => ({
  isSpeaking: false,
  currentMessage: '',
  audioLevel: 0,
  contracts: [],
  properties: [],
  currentContract: null,
  currentProperty: null,
  focusedProperty: null,
  isEnriching: false,
  enrichingPropertyId: null,
  enrichingPropertyAddress: null,
  notifications: [],

  setIsSpeaking: (speaking) => set({ isSpeaking: speaking }),
  setCurrentMessage: (message) => set({ currentMessage: message }),
  setAudioLevel: (level) => set({ audioLevel: level }),
  setContracts: (contracts) => set({ contracts }),
  setProperties: (properties) => set({ properties }),
  setCurrentContract: (contract) => set({ currentContract: contract }),
  setCurrentProperty: (property) => set({ currentProperty: property }),
  setFocusedProperty: (property) => set({ focusedProperty: property }),
  setEnrichmentStatus: (isEnriching, propertyId = null, address = null) =>
    set({ isEnriching, enrichingPropertyId: propertyId, enrichingPropertyAddress: address }),
  addNotification: (notification) =>
    set((state) => ({
      notifications: [notification, ...state.notifications].slice(0, 5), // Keep last 5
    })),
  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}))
