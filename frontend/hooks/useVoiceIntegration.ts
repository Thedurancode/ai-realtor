import { useEffect, useRef, useState } from 'react'
import { useAgentStore } from '@/store/useAgentStore'

/**
 * Hook for integrating real-time voice analysis with the agent display
 * This connects to Web Audio API to analyze microphone input
 */
export const useVoiceIntegration = () => {
  const { setIsSpeaking, setAudioLevel } = useAgentStore()
  const [isListening, setIsListening] = useState(false)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  const startListening = async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Create audio context and analyser
      audioContextRef.current = new AudioContext()
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 256

      // Connect microphone to analyser
      const source = audioContextRef.current.createMediaStreamSource(stream)
      source.connect(analyserRef.current)

      setIsListening(true)

      // Start analyzing audio
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)

      const analyze = () => {
        if (!analyserRef.current) return

        analyserRef.current.getByteFrequencyData(dataArray)

        // Calculate average volume
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length
        const normalizedLevel = Math.min(average / 128, 1) // Normalize to 0-1

        // Update audio level
        setAudioLevel(normalizedLevel)

        // Consider speaking if level is above threshold
        const threshold = 0.1
        setIsSpeaking(normalizedLevel > threshold)

        animationFrameRef.current = requestAnimationFrame(analyze)
      }

      analyze()
    } catch (error) {
      console.error('Error accessing microphone:', error)
    }
  }

  const stopListening = () => {
    // Cancel animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close()
    }

    setIsListening(false)
    setIsSpeaking(false)
    setAudioLevel(0)
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopListening()
    }
  }, [])

  return {
    isListening,
    startListening,
    stopListening,
  }
}
