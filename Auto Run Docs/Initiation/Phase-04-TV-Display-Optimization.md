# Phase 04: TV Display Optimization & Full-Screen Experience

This phase optimizes the activity feed for large TV displays with full-screen layouts, enhanced readability from distance, adaptive animations, and multi-monitor support. The interface becomes a stunning mission control dashboard perfect for wall-mounted displays.

## Tasks

- [ ] Create TV-optimized layout with enhanced readability and spacing:
  - Update `/frontend/components/ActivityFeed/ActivityFeed.tsx` to detect display mode (desktop vs TV) using viewport size and URL parameter `?display=tv`
  - Implement TV layout with larger font sizes (minimum 24px for body text, 48px for headers), increased line height (1.8), wider spacing between cards (32px gaps)
  - Add high-contrast color scheme optimized for TV viewing: deeper blacks, brighter accent colors, increased saturation
  - Create grid layout option for TV mode showing multiple activity cards simultaneously in 2-3 column layout
  - Implement auto-scaling system that adjusts font sizes based on viewport resolution for 4K, 1080p, 720p displays

- [ ] Build cinematic full-screen animations and transitions:
  - Create `/frontend/components/ActivityFeed/CinematicTransitions.tsx` with page transition animations: curtain wipe, zoom blur, particle dissolve
  - Implement hero entrance animation when new high-priority activities arrive: full-screen takeover with dramatic zoom and fade
  - Add cinematic notification overlays for critical events: contract signed, property sold, using full-screen animated graphics
  - Create ambient motion background with subtle parallax scrolling layers
  - Implement time-of-day theme transitions: gradual color shifts throughout the day (morning blues, afternoon gold, evening purples, night dark blues)

- [ ] Design and implement activity prioritization and smart routing for TV display:
  - Create activity priority scoring algorithm in `/app/services/activity_priority.py` based on: event type, user importance, business impact, recency
  - Implement smart feed curation that highlights high-priority items with larger cards, vibrant animations, longer display duration
  - Add automatic rotation system that cycles through different views: recent activity, top performers, system health, daily statistics
  - Create "feature" slots that give prominent position to important events (contracts, property sales)
  - Implement intelligent auto-dismiss for low-priority items after shorter duration (15 seconds) vs high-priority (60+ seconds)

- [ ] Build multi-zone TV layout with simultaneous information displays:
  - Create `/frontend/components/ActivityFeed/MultiZoneLayout.tsx` that divides screen into sections: main feed (70%), stats sidebar (15%), mini property carousel (15%)
  - Implement picture-in-picture mode showing property details while activity feed continues in background
  - Add split-screen mode for showing two activity timelines side-by-side (e.g., MCP tools vs system events)
  - Create corner widgets for: current time, weather, active sessions count, system health status
  - Ensure all zones animate independently without interfering with each other

- [ ] Implement TV-specific controls and automation features:
  - Add screensaver mode that activates after 5 minutes of no activity: slow-motion replay of today's highlights with ambient music visualization
  - Create auto-refresh system that periodically re-queries backend for new activities (every 2 seconds) without WebSocket dependency
  - Implement gesture control support for touchscreen TVs: swipe to navigate, pinch to zoom, tap to expand
  - Add remote control navigation support using keyboard arrow keys and enter (for TV remotes)
  - Create URL-based configuration for kiosk mode: `?kiosk=true&autoRotate=30` (rotate views every 30 seconds)
  - Add QR code overlay in corner that links to mobile control interface

- [ ] Test on actual TV display and optimize performance for 24/7 operation:
  - Test on 1080p and 4K displays to verify scaling and readability
  - Run long-duration stress test (24+ hours) to check for memory leaks or performance degradation
  - Implement cleanup routines that purge old activities from memory to prevent growth
  - Verify animations remain smooth under continuous operation
  - Test WebSocket reconnection logic if connection drops during overnight operation
  - Create deployment guide in `/Auto Run Docs/Initiation/Working/phase-04-tv-deployment-guide.md` with instructions for setting up on dedicated TV hardware, auto-start on boot, kiosk mode configuration
