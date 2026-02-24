import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { CastScriptLoader } from '@/components/CastScriptLoader'
import SetupBanner from '@/components/SetupBanner'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Realtime Realtor TV Display',
  description: 'Real-time AI agent visualization for real estate operations',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <SetupBanner />
        <CastScriptLoader />
        {children}
      </body>
    </html>
  )
}
