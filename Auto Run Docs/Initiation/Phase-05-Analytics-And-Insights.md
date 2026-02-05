# Phase 05: Analytics Dashboard & Historical Insights

This phase adds powerful analytics and historical insights to the activity feed, transforming it from a live feed into an intelligent analytics platform that reveals patterns, trends, and actionable insights about your AI assistant's performance and usage.

## Tasks

- [ ] Build comprehensive activity analytics backend service:
  - Create `/app/services/activity_analytics.py` with functions for: daily/weekly/monthly aggregations, tool usage frequency ranking, success rate calculations, average execution times, user activity patterns, peak usage hours detection
  - Add database queries using SQLAlchemy to efficiently aggregate large activity datasets
  - Implement caching layer using Redis (or in-memory cache) for expensive analytics queries with 5-minute TTL
  - Create `/app/routers/analytics.py` router with endpoints: GET `/analytics/summary` (overview stats), GET `/analytics/tools` (tool-specific metrics), GET `/analytics/timeline` (time-series data), GET `/analytics/users` (per-user statistics)
  - Add date range filtering, tool filtering, and user filtering to all analytics endpoints

- [ ] Create interactive analytics dashboard components:
  - Create `/frontend/components/Analytics/AnalyticsDashboard.tsx` with tabbed interface: Overview, Tools, Users, Timeline, Performance
  - Build `/frontend/components/Analytics/MetricsGrid.tsx` showing key metrics in cards: total executions today, success rate, avg response time, most used tool, active users
  - Implement animated number counters that count up to current values with easing
  - Add trend indicators (up/down arrows) showing comparison to previous period (yesterday, last week)
  - Style with consistent glassmorphism design matching activity feed aesthetic

- [ ] Implement data visualization charts using Recharts or Chart.js:
  - Create `/frontend/components/Analytics/TimeSeriesChart.tsx` showing activity volume over time with area chart, customizable time ranges (1h, 24h, 7d, 30d)
  - Build `/frontend/components/Analytics/ToolUsagePieChart.tsx` displaying distribution of tool usage with interactive segments
  - Create `/frontend/components/Analytics/SuccessRateChart.tsx` with line chart showing success rate trend over time
  - Implement `/frontend/components/Analytics/ExecutionTimeChart.tsx` with bar chart showing average execution time per tool
  - Add hover tooltips with detailed information and click-to-drill-down interactions
  - Ensure all charts animate smoothly on load and data updates

- [ ] Build activity search and replay functionality:
  - Create `/frontend/components/Analytics/ActivitySearch.tsx` with advanced search filters: date range, tool name, status, user, duration range, metadata contains
  - Implement search results table with sortable columns, pagination, export to CSV button
  - Add "Replay Activity" feature that reconstructs and visualizes past activity execution with animated timeline
  - Create `/frontend/components/Analytics/ActivityReplay.tsx` that shows step-by-step playback of selected activity with pause/play/speed controls
  - Implement activity comparison view to compare two executions side-by-side

- [ ] Create automated insight detection and anomaly alerting:
  - Implement `/app/services/insight_detector.py` that analyzes activity patterns to detect: unusual tool failure rates, performance degradation, spike in usage, new user patterns, dormant tools
  - Create insight scoring system that ranks insights by importance
  - Add `/app/models/insight.py` model to store detected insights with timestamp, type, severity, description, affected entities
  - Build `/frontend/components/Analytics/InsightsPanel.tsx` that displays recent insights as cards with icons, severity badges, and "View Details" links
  - Implement real-time insight notifications that appear in activity feed when new insights are detected
  - Add settings panel to configure insight thresholds and notification preferences

- [ ] Add export and reporting capabilities:
  - Create `/app/routers/reports.py` with endpoints to generate PDF or Excel reports of activity analytics
  - Implement scheduled report generation that can email daily/weekly summaries
  - Add export buttons to all analytics views that download data as JSON, CSV, or Excel
  - Create report template system in `/app/templates/reports/` with HTML templates for PDF generation using WeasyPrint
  - Build `/frontend/components/Analytics/ReportScheduler.tsx` UI for configuring automated reports
  - Test report generation with sample data and verify formatting

- [ ] Integrate analytics into main activity feed interface:
  - Add "Analytics" button to main activity feed header that opens analytics sidebar overlay
  - Create side-by-side view mode showing live feed (70%) and analytics dashboard (30%)
  - Add mini analytics widgets to activity feed: success rate badge, daily activity count, most active tool callout
  - Implement contextual analytics: when hovering over a tool in activity feed, show quick stats for that tool
  - Create smooth transition animation between live feed view and analytics view
  - Document analytics features and usage in `/Auto Run Docs/Initiation/Working/phase-05-analytics-guide.md`
