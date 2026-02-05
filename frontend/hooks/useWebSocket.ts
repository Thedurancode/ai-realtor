import { useEffect, useRef, useState } from 'react'
import { useAgentStore } from '@/store/useAgentStore'

interface WebSocketMessage {
  type: 'agent_speaking' | 'agent_stopped' | 'contract_update' | 'property_update' | 'activity_logged' | 'tool_started' | 'tool_completed' | 'tool_failed'
  message?: string
  audioLevel?: number
  data?: any
  activity?: any
}

/**
 * Hook for WebSocket connection to backend for real-time updates
 */
export const useWebSocket = (url: string) => {
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const {
    setIsSpeaking,
    setCurrentMessage,
    setAudioLevel,
    setContracts,
    setProperties,
    setCurrentContract,
    setCurrentProperty,
  } = useAgentStore()

  const connect = () => {
    try {
      const ws = new WebSocket(url)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
      }

      ws.onmessage = (event) => {
        const message: WebSocketMessage = JSON.parse(event.data)

        switch (message.type) {
          case 'agent_speaking':
            setIsSpeaking(true)
            if (message.message) setCurrentMessage(message.message)
            if (message.audioLevel !== undefined) setAudioLevel(message.audioLevel)
            break

          case 'agent_stopped':
            setIsSpeaking(false)
            setAudioLevel(0)
            break

          case 'contract_update':
            if (message.data) {
              if (Array.isArray(message.data)) {
                setContracts(message.data)
              } else {
                setCurrentContract(message.data)
              }
            }
            break

          case 'property_update':
            if (message.data) {
              if (Array.isArray(message.data)) {
                setProperties(message.data)
              } else {
                setCurrentProperty(message.data)
              }
            }
            break

          // Activity events (activity_logged, tool_started, tool_completed, tool_failed)
          // are handled by the useActivityFeed hook - no action needed here
          case 'activity_logged':
          case 'tool_started':
          case 'tool_completed':
          case 'tool_failed':
            // These are handled by useActivityFeed hook
            break
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)

        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connect()
        }, 5000)
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Error creating WebSocket:', error)
    }
  }

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }

  const sendMessage = (message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [url])

  return {
    isConnected,
    sendMessage,
    disconnect,
    reconnect: connect,
  }
}
