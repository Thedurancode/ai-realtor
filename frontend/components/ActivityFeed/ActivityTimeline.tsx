'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { ActivityCard } from './ActivityCard'
import { ActivityEvent } from './ActivityFeed'
import { useEffect, useRef, useState } from 'react'

interface ActivityTimelineProps {
  activities: ActivityEvent[]
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
}

const EmptyState = () => (
  <motion.div
    initial={{ opacity: 0, scale: 0.9 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 0.5 }}
    className="flex flex-col items-center justify-center h-full text-center p-8"
  >
    <motion.div
      animate={{
        scale: [1, 1.1, 1],
        rotate: [0, 5, -5, 0],
      }}
      transition={{
        duration: 3,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
      className="text-8xl mb-6 opacity-30"
    >
      📊
    </motion.div>
    <h2 className="text-3xl font-bold text-white/60 mb-3">No Activity Yet</h2>
    <p className="text-lg text-white/40 max-w-md">
      Activity events will appear here in real-time as they occur. Start using the system to see live updates!
    </p>
  </motion.div>
)

export const ActivityTimeline = ({ activities }: ActivityTimelineProps) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState(true)
  const [userHasScrolled, setUserHasScrolled] = useState(false)
  const lastScrollTop = useRef(0)

  // Sort activities by timestamp (most recent first)
  const sortedActivities = [...activities].sort((a, b) => {
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  })

  // Auto-scroll to top when new activities arrive (if auto-scroll is enabled)
  useEffect(() => {
    if (isAutoScrollEnabled && !userHasScrolled && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: 0,
        behavior: 'smooth',
      })
    }
  }, [activities.length, isAutoScrollEnabled, userHasScrolled])

  // Detect manual scrolling
  useEffect(() => {
    const container = scrollContainerRef.current
    if (!container) return

    const handleScroll = () => {
      const currentScrollTop = container.scrollTop
      const scrollDirection = currentScrollTop > lastScrollTop.current ? 'down' : 'up'

      // If user scrolls down, disable auto-scroll
      if (scrollDirection === 'down' && currentScrollTop > 50) {
        setUserHasScrolled(true)
        setIsAutoScrollEnabled(false)
      }

      // If user scrolls back to near the top, re-enable auto-scroll
      if (currentScrollTop < 50) {
        setUserHasScrolled(false)
        setIsAutoScrollEnabled(true)
      }

      lastScrollTop.current = currentScrollTop
    }

    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => container.removeEventListener('scroll', handleScroll)
  }, [])

  if (activities.length === 0) {
    return <EmptyState />
  }

  return (
    <div className="relative h-full">
      {/* Auto-scroll indicator */}
      <AnimatePresence>
        {!isAutoScrollEnabled && (
          <motion.button
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            onClick={() => {
              setIsAutoScrollEnabled(true)
              setUserHasScrolled(false)
              scrollContainerRef.current?.scrollTo({
                top: 0,
                behavior: 'smooth',
              })
            }}
            className="absolute top-4 left-1/2 -translate-x-1/2 z-20 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all flex items-center gap-2 group"
          >
            <motion.span
              animate={{ y: [0, -3, 0] }}
              transition={{
                duration: 1,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              ↑
            </motion.span>
            <span className="font-semibold">New Activity Available</span>
            <motion.span
              animate={{ scale: [1, 1.2, 1] }}
              transition={{
                duration: 1,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              className="w-2 h-2 bg-white rounded-full"
            />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Timeline container with custom scrollbar */}
      <motion.div
        ref={scrollContainerRef}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="h-full overflow-y-auto scrollbar-custom pr-4"
      >
        <div className="space-y-4 pb-8">
          <AnimatePresence mode="popLayout">
            {sortedActivities.map((activity, index) => (
              <ActivityCard key={activity.id} activity={activity} index={index} />
            ))}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Scroll fade effect at bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-slate-950/80 to-transparent pointer-events-none" />
    </div>
  )
}
