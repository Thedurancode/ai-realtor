import axios from 'axios'
import { Contract, Property } from '@/store/useAgentStore'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
