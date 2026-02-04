'use client'

import { TVDisplay } from '@/components/TVDisplay'
import { useAgentStore } from '@/store/useAgentStore'
import { useEffect } from 'react'

export default function Home() {
  const { setIsSpeaking, setAudioLevel, setCurrentMessage, setFocusedProperty, properties, setEnrichmentStatus } = useAgentStore()

  // Simulate voice activity for demo purposes
  useEffect(() => {
    // Listen for keyboard shortcuts to simulate agent speaking
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 's') {
        // Press 's' to simulate speaking
        setIsSpeaking(true)
        setCurrentMessage('Let me show you the details of that property...')

        // Simulate varying audio levels
        const interval = setInterval(() => {
          setAudioLevel(Math.random() * 0.8 + 0.2)
        }, 100)

        // Auto-show first property after 2 seconds
        setTimeout(() => {
          if (properties.length > 0) {
            setFocusedProperty(properties[0])
          }
        }, 2000)

        // Stop after 3 seconds
        setTimeout(() => {
          clearInterval(interval)
          setIsSpeaking(false)
          setAudioLevel(0)
        }, 3000)
      }

      if (e.key === 'q') {
        // Press 'q' to stop speaking
        setIsSpeaking(false)
        setAudioLevel(0)
        setCurrentMessage('')
        setFocusedProperty(null)
      }

      if (e.key === 'p' && properties.length > 0) {
        // Press 'p' to show first property detail
        setFocusedProperty(properties[0])
        setCurrentMessage('Here are the details for this property...')
      }

      if (e.key === 'Escape') {
        // Press ESC to close detail view
        setFocusedProperty(null)
      }

      // Press 'b' to simulate asking about Broadway property
      if (e.key === 'b' && properties.length > 0) {
        const broadwayProperty = properties.find(p =>
          p.address.toLowerCase().includes('broadway')
        )
        if (broadwayProperty) {
          setIsSpeaking(true)
          setCurrentMessage(`Let me show you the details for ${broadwayProperty.address}...`)

          const interval = setInterval(() => {
            setAudioLevel(Math.random() * 0.8 + 0.2)
          }, 100)

          setTimeout(() => {
            setFocusedProperty(broadwayProperty)
          }, 1500)

          setTimeout(() => {
            clearInterval(interval)
            setIsSpeaking(false)
            setAudioLevel(0)
          }, 2500)
        }
      }

      // Press 'm' to simulate asking about Main Street property
      if (e.key === 'm' && properties.length > 0) {
        const mainProperty = properties.find(p =>
          p.address.toLowerCase().includes('main')
        )
        if (mainProperty) {
          setIsSpeaking(true)
          setCurrentMessage(`Here are the details for ${mainProperty.address}...`)

          const interval = setInterval(() => {
            setAudioLevel(Math.random() * 0.8 + 0.2)
          }, 100)

          setTimeout(() => {
            setFocusedProperty(mainProperty)
          }, 1500)

          setTimeout(() => {
            clearInterval(interval)
            setIsSpeaking(false)
            setAudioLevel(0)
          }, 2500)
        }
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [setIsSpeaking, setAudioLevel, setCurrentMessage, setFocusedProperty, properties])

  // Expose function for AI to call
  if (typeof window !== 'undefined') {
    (window as any).showPropertyByAddress = (address: string) => {
      const property = properties.find(p =>
        p.address.toLowerCase().includes(address.toLowerCase())
      )
      if (property) {
        setCurrentMessage(`Showing you ${property.address}...`)
        setFocusedProperty(property)
        return property
      }
      return null
    }
  }

  // WebSocket connection for real-time control from backend/CLI
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')

    ws.onopen = () => {
      console.log('WebSocket connected to backend')
    }

    ws.onmessage = (event) => {
      const command = JSON.parse(event.data)
      console.log('Received command:', command)

      if (command.action === 'show_property') {
        // Find property by ID or address
        let property
        if (command.property_id) {
          property = properties.find(p => p.id === command.property_id)
        } else if (command.address) {
          property = properties.find(p =>
            p.address.toLowerCase().includes(command.address.toLowerCase())
          )
        }

        if (property) {
          setIsSpeaking(true)
          setCurrentMessage(command.message || `Let me show you ${property.address}...`)

          // Simulate audio levels
          const interval = setInterval(() => {
            setAudioLevel(Math.random() * 0.8 + 0.2)
          }, 100)

          // Show property after 1.5 seconds
          setTimeout(() => {
            setFocusedProperty(property)
          }, 1500)

          // Stop speaking after 2.5 seconds
          setTimeout(() => {
            clearInterval(interval)
            setIsSpeaking(false)
            setAudioLevel(0)
          }, 2500)
        }
      } else if (command.action === 'agent_speak') {
        setIsSpeaking(true)
        setCurrentMessage(command.message)

        const interval = setInterval(() => {
          setAudioLevel(Math.random() * 0.8 + 0.2)
        }, 100)

        setTimeout(() => {
          clearInterval(interval)
          setIsSpeaking(false)
          setAudioLevel(0)
        }, 3000)
      } else if (command.action === 'close_detail') {
        setFocusedProperty(null)
        setCurrentMessage('')
      } else if (command.action === 'enrichment_start') {
        // Show enrichment animation
        setEnrichmentStatus(true, command.property_id, command.property_address)
      } else if (command.action === 'enrichment_complete') {
        // Hide enrichment animation
        setEnrichmentStatus(false)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }

    return () => ws.close()
  }, [setIsSpeaking, setAudioLevel, setCurrentMessage, setFocusedProperty, properties, setEnrichmentStatus])

  return (
    <main>
      <TVDisplay />
    </main>
  )
}
