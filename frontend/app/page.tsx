'use client'

import { BloombergTerminalV2 } from '@/components/BloombergTerminalV2'
import { FullScreenActivityDisplay } from '@/components/FullScreenActivityDisplay'
import { VoiceCompanion } from '@/components/VoiceCompanion'

export default function Home() {
  return (
    <main>
      <FullScreenActivityDisplay />
      <VoiceCompanion />
      <BloombergTerminalV2 />
    </main>
  )
}
