---
tags: [performance]
summary: performance implementation decisions and patterns
relevantTo: [performance]
importance: 0.7
relatedFiles: []
usageStats:
  loaded: 0
  referenced: 0
  successfulFeatures: 0
---
# performance

#### [Gotcha] Property enrichment (Zillow photos, tax history, schools, comps) is blocking operation in voice workflows but has variable latency (1-5sec) due to RapidAPI quota and network variability (2026-02-19)
- **Situation:** Users expect instant property details during voice conversations. Zillow RapidAPI can timeout or rate-limit. Skip tracing can take 2-3sec per property.
- **Root cause:** Real-time voice UX expectations conflict with external API latencies. Caching helps but cache misses still block. Background enrichment loses user context.
- **How to avoid:** Solution: cache aggressively, timeout gracefully, queue background enrichment, accept degraded UX during API outages. Better to say 'Zillow unavailable' than hang.