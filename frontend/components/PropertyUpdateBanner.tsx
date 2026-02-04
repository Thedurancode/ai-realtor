'use client'

export const PropertyUpdateBanner: React.FC<{ count: number }> = ({ count }) => {
  if (count === 0) return null

  return (
    <div className="bg-gradient-to-r from-accent to-emerald-600 border-2 border-white/30 rounded-lg px-6 py-3 mb-4 animate-pulse">
      <div className="flex items-center justify-center gap-3">
        <span className="text-3xl">⚡</span>
        <span className="text-xl font-bold text-white">
          {count} PROPERTIES UPDATED IN REAL-TIME
        </span>
        <span className="text-3xl">⚡</span>
      </div>
    </div>
  )
}
