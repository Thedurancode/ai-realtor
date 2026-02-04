'use client'

import { useEffect, useState } from 'react'

interface EnrichmentAnimationProps {
  propertyAddress?: string | null
}

export const EnrichmentAnimation: React.FC<EnrichmentAnimationProps> = ({ propertyAddress }) => {
  const [progress, setProgress] = useState(0)
  const [dots, setDots] = useState('.')

  useEffect(() => {
    // Animate progress bar
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 95) return 95 // Cap at 95% until completion
        return prev + Math.random() * 15
      })
    }, 300)

    // Animate dots
    const dotsInterval = setInterval(() => {
      setDots((prev) => {
        if (prev.length >= 3) return '.'
        return prev + '.'
      })
    }, 500)

    return () => {
      clearInterval(progressInterval)
      clearInterval(dotsInterval)
    }
  }, [])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md">
      <div className="relative">
        {/* Animated rings */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-64 h-64 rounded-full border-4 border-news-cyan/30 animate-ping" />
          <div className="absolute w-48 h-48 rounded-full border-4 border-secondary/30 animate-ping animation-delay-500" />
          <div className="absolute w-32 h-32 rounded-full border-4 border-accent/30 animate-ping animation-delay-1000" />
        </div>

        {/* Main content */}
        <div className="relative bg-gradient-to-br from-news-blue via-primary to-news-blue border-4 border-secondary rounded-2xl shadow-2xl shadow-secondary/50 p-10 min-w-[500px]">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="text-6xl mb-4 animate-bounce">🏠✨</div>
            <h2 className="text-4xl font-black text-white mb-2">
              ENRICHING PROPERTY
            </h2>
            {propertyAddress && (
              <p className="text-xl text-news-cyan font-semibold">
                {propertyAddress}
              </p>
            )}
          </div>

          {/* Progress section */}
          <div className="space-y-6">
            {/* Animated status messages */}
            <div className="bg-white/10 rounded-lg p-4 border-2 border-white/20">
              <div className="text-lg text-white font-semibold mb-2 flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-news-cyan animate-pulse" />
                Fetching Zillow data{dots}
              </div>
              <div className="space-y-1 text-sm text-gray-300">
                <div className="flex items-center gap-2">
                  <span className={progress > 20 ? 'text-news-cyan' : 'text-gray-500'}>
                    {progress > 20 ? '✓' : '○'} Property details
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={progress > 40 ? 'text-news-cyan' : 'text-gray-500'}>
                    {progress > 40 ? '✓' : '○'} Valuation data
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={progress > 60 ? 'text-news-cyan' : 'text-gray-500'}>
                    {progress > 60 ? '✓' : '○'} Photos & media
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={progress > 80 ? 'text-news-cyan' : 'text-gray-500'}>
                    {progress > 80 ? '✓' : '○'} Schools & neighborhood
                  </span>
                </div>
              </div>
            </div>

            {/* Progress bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-400">
                <span>Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="w-full h-4 bg-white/10 rounded-full overflow-hidden border-2 border-white/20">
                <div
                  className="h-full bg-gradient-to-r from-news-cyan via-secondary to-accent transition-all duration-300 ease-out relative overflow-hidden"
                  style={{ width: `${progress}%` }}
                >
                  {/* Shimmer effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
                </div>
              </div>
            </div>

            {/* Fun facts */}
            <div className="bg-accent/20 border-2 border-accent/50 rounded-lg p-3 text-center">
              <p className="text-sm text-white">
                <span className="font-bold">💡 Did you know?</span> We're fetching comprehensive data including
                tax history, price trends, and nearby schools!
              </p>
            </div>
          </div>

          {/* Loading spinner at bottom */}
          <div className="mt-6 flex justify-center">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-news-cyan animate-bounce" />
              <div className="w-3 h-3 rounded-full bg-secondary animate-bounce animation-delay-200" />
              <div className="w-3 h-3 rounded-full bg-accent animate-bounce animation-delay-400" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
