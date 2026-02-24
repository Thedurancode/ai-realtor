'use client'

import { BloombergTerminalV2 } from '@/components/BloombergTerminalV2'
import { FullScreenActivityDisplay } from '@/components/FullScreenActivityDisplay'
import { VoiceCompanion } from '@/components/VoiceCompanion'
import CastButton from '@/components/CastButton'

export default function Home() {
  return (
    <main>
      <CastButton />
      <FullScreenActivityDisplay />
      <VoiceCompanion />
      <BloombergTerminalV2 />
    </main>
  )
}
