import axios from 'axios'
import { Contract, Property } from '@/store/useAgentStore'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request/response interceptors for real-time activity feed
api.interceptors.request.use((config) => {
  // Show API call in activity feed
  if (typeof window !== 'undefined' && (window as any).addActivity) {
    (window as any).addActivity({
      type: 'api_call',
      message: `${config.method?.toUpperCase()} ${config.url}`,
      status: 'pending'
    })
  }

  // Show big activity for important endpoints
  if (typeof window !== 'undefined' && (window as any).showBigActivity) {
    const url = config.url || ''
    if (config.method?.toUpperCase() === 'POST' && url.includes('/properties')) {
      (window as any).showBigActivity({
        type: 'property_added',
        title: 'CREATING PROPERTY',
        message: 'Adding new listing to database...',
        status: 'pending',
        icon: '🏠'
      })
    } else if (config.method?.toUpperCase() === 'POST' && url.includes('/notifications')) {
      (window as any).showBigActivity({
        type: 'notification',
        title: 'NEW NOTIFICATION',
        message: 'Broadcasting to all connected clients...',
        status: 'pending',
        icon: '🔔'
      })
    } else if (url.includes('/enrich')) {
      (window as any).showBigActivity({
        type: 'enrichment',
        title: 'ENRICHING PROPERTY',
        message: 'Fetching Zillow market data...',
        status: 'pending',
        icon: '⚡'
      })
    }
  }

  return config
})

api.interceptors.response.use(
  (response) => {
    // Show successful response in activity feed
    if (typeof window !== 'undefined' && (window as any).addActivity) {
      (window as any).addActivity({
        type: 'response',
        message: `${response.config.method?.toUpperCase()} ${response.config.url}`,
        details: `Status: ${response.status}`,
        status: 'success'
      })
    }

    // Track for Bloomberg terminal
    if (typeof window !== 'undefined' && (window as any).trackAPICall) {
      (window as any).trackAPICall(
        response.config.method?.toUpperCase() || 'GET',
        response.config.url || '',
        'success'
      )
    }

    // Show big success for important endpoints
    if (typeof window !== 'undefined' && (window as any).showBigActivity) {
      const url = response.config.url || ''
      const data = response.data

      if (response.config.method?.toUpperCase() === 'POST' && url.includes('/properties')) {
        (window as any).showBigActivity({
          type: 'property_added',
          title: 'PROPERTY CREATED!',
          message: `${data.title || data.address} - $${(data.price || 0).toLocaleString()}`,
          status: 'success',
          icon: '✓'
        })
      } else if (response.config.method?.toUpperCase() === 'POST' && url.includes('/notifications')) {
        (window as any).showBigActivity({
          type: 'notification',
          title: 'NOTIFICATION SENT!',
          message: data.title || 'Broadcast complete',
          status: 'success',
          icon: '✓'
        })
      } else if (url.includes('/enrich')) {
        const zestimate = data.data?.zestimate
        (window as any).showBigActivity({
          type: 'enrichment',
          title: 'ENRICHMENT COMPLETE!',
          message: zestimate ? `Zestimate: $${zestimate.toLocaleString()}` : 'Property data updated',
          status: 'success',
          icon: '✓'
        })
      }
    }

    return response
  },
  (error) => {
    // Show error in activity feed
    if (typeof window !== 'undefined' && (window as any).addActivity) {
      (window as any).addActivity({
        type: 'response',
        message: `${error.config?.method?.toUpperCase()} ${error.config?.url}`,
        details: error.message,
        status: 'error'
      })
    }
    return Promise.reject(error)
  }
)

// Contracts
export const getContracts = async (): Promise<Contract[]> => {
  const response = await api.get('/contracts/')
  return response.data
}

export const getContract = async (id: number): Promise<Contract> => {
  const response = await api.get(`/contracts/${id}`)
  return response.data
}

export const getContractStatus = async (id: number) => {
  const response = await api.get(`/contracts/${id}/status`)
  return response.data
}

// Properties
export const getProperties = async (): Promise<Property[]> => {
  const response = await api.get('/properties/')
  return response.data
}

export const getProperty = async (id: number): Promise<Property> => {
  const response = await api.get(`/properties/${id}`)
  return response.data
}

export const createProperty = async (property: Partial<Property>): Promise<Property> => {
  const response = await api.post('/properties/', property)
  return response.data
}

// Voice endpoints
export const sendContractVoice = async (data: {
  template_id: string
  property_id: number
  signers: Array<{
    name: string
    email: string
    role: string
  }>
}) => {
  const response = await api.post('/voice/send-contract', data)
  return response.data
}

export const getContractStatusVoice = async (contractId: number) => {
  const response = await api.get(`/voice/contract-status/${contractId}`)
  return response.data
}

export const createPropertyVoice = async (data: {
  address: string
  price: number
  bedrooms: number
  bathrooms: number
  square_feet: number
}) => {
  const response = await api.post('/voice/create-property', data)
  return response.data
}

export default api
