'use client'

export const LiveIndicator: React.FC = () => {
  return (
    <div className="flex items-center gap-2 bg-red-600 px-4 py-2 rounded-md">
      <div className="w-3 h-3 rounded-full bg-white animate-flash" />
      <span className="text-white font-bold text-sm uppercase tracking-wider">
        LIVE
      </span>
    </div>
  )
}
