# 🫀 ZeroClaw-Inspired Heartbeat System — Implementation Plan

## Overview

Transform the AI Realtor Platform from a **reactive** system (waits for commands) into a **proactive, autonomous agent** (continuously monitors and acts) by implementing a ZeroClaw-inspired heartbeat system.

---

## 🎯 What This Achieves

### Before: Reactive System
- Agent only responds when you talk to it
- No background monitoring
- No proactive alerts
- Manual checks required

### After: Proactive Autonomous Agent
- **Continuous monitoring** of portfolio, market, relationships
- **Proactive alerts** when action needed
- **Autonomous tasks** run on schedule
- **Self-healing** detects and fixes issues
- **Always-on intelligence** working 24/7

---

## 📚 ZeroClaw Heartbeat Learnings

### Key Concepts from ZeroClaw

1. **Periodic Task Engine**
   - Runs background checks on configurable intervals
   - Reads tasks from `HEARTBEAT.md` configuration
   - Executes monitoring tasks autonomously

2. **Ultra-Lightweight Architecture**
   - Minimal resource usage
   - Fast startup (<10ms)
   - No external dependencies for core functionality

3. **Four-Part Daemon Architecture**
   - **Gateway**: HTTP/WebSocket service
   - **Channels**: Message platform management
   - **Heartbeat**: Background task monitoring
   - **Scheduler**: Cron-based task triggering

4. **Configuration-Driven Tasks**
   - Tasks defined in markdown files
   - Easy to add/remove monitoring activities
   - Human-readable configuration

5. **Health Status Reporting**
   - Binary status indicators (OK/ACTION_NEEDED)
   - Detailed logging of each cycle
   - Notification system for alerts

---

## 🏗️ Architecture Design for AI Realtor

### Components

#### 1. **Heartbeat Engine** (`app/services/heartbeat_service.py`)
```python
class HeartbeatEngine:
    """Periodic task execution engine for autonomous monitoring."""

    - Runs on configurable interval (default: 60 seconds)
    - Reads checklist from HEARTBEAT.md or database config
    - Executes monitoring tasks sequentially
    - Logs results and triggers notifications
    - Tracks last execution time and status
```

**Key Methods:**
- `start()` - Start heartbeat loop
- `stop()` - Stop heartbeat loop
- `execute_cycle()` - Run one heartbeat cycle
- `register_task(name, handler, schedule)` - Add monitoring task
- `get_status()` - Return current heartbeat status

#### 2. **Monitoring Tasks** (Built-in Checklists)

**Default Heartbeat Checklist:**

```markdown
# HEARTBEAT.md — Autonomous Monitoring Checklist

## Portfolio Monitoring (Every 5 minutes)
- [ ] Check for stale properties (no activity 7+ days)
- [ ] Scan for contract deadlines approaching
- [ ] Detect unsigned required contracts
- [ ] Verify pipeline auto-advancement is working
- [ ] Check for high-score properties with no action

## Market Intelligence (Every 15 minutes)
- [ ] Scan for new properties matching watchlist criteria
- [ ] Detect market shifts in agent's active cities
- [ ] Monitor competitive activity in key markets
- [ ] Check for price changes on tracked properties

## Relationship Health (Every hour)
- [ ] Score relationships with all active contacts
- [ ] Detect cooling relationships (↓10%+ score)
- [ ] Flag overdue follow-ups
- [ ] Identify contacts needing outreach

## System Health (Every 5 minutes)
- [ ] Verify database connectivity
- [ ] Check external API status (Zillow, Google, etc.)
- [ ] Monitor background worker processes
- [ ] Verify MCP server connectivity

## Predictive Insights (Every hour)
- [ ] Re-score all active properties
- [ ] Update closing probabilities
- [ ] Identify deals needing attention
- [ ] Generate follow-up queue rankings

## Scheduled Tasks (Every minute)
- [ ] Process due reminders and follow-ups
- [ ] Execute recurring task generation
- [ ] Check for task completion triggers
- [ ] Send notifications for due tasks
```

#### 3. **Scheduler Integration** (Leverage Existing)

**Current Background Tasks:**
- Task runner (60-second loop)
- Pipeline automation (5-minute loop)
- Daily digest (8 AM daily)
- Campaign worker

**New: Unified Heartbeat Scheduler**
```python
class UnifiedScheduler:
    """Central scheduler for all periodic tasks."""

    - Task runner: Check due tasks every 60s
    - Pipeline: Auto-advance properties every 5m
    - Heartbeat: Full monitoring cycle every 5m
    - Insights: Quick scan every 15m
    - Market: Market check every 15m
    - Relationships: Deep scan every hour
    - Daily digest: 8 AM every day
```

#### 4. **Health Check API** (`app/routers/health.py`)

**Endpoints:**
```python
GET /health                    - Overall system health
GET /health/heartbeat          - Heartbeat status
GET /health/database           - Database connectivity
GET /health/external-apis      - External API status
GET /health/background-workers - Background process status
GET /health/metrics            - Performance metrics
```

#### 5. **Heartbeat Configuration** (Database + File)

**Database Table: `heartbeat_config`**
```sql
CREATE TABLE heartbeat_config (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(100) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    schedule_seconds INTEGER DEFAULT 300,  -- 5 minutes
    last_run_at TIMESTAMPTZ,
    last_status VARCHAR(20),  -- success, failed, action_needed
    last_result JSONB,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Fallback: `HEARTBEAT.md` file** for human-readable config

#### 6. **Status Reporting & Alerts**

**Heartbeat Status Response:**
```json
{
  "status": "healthy",
  "last_cycle": "2025-02-22T10:30:00Z",
  "cycle_duration_ms": 1250,
  "tasks_executed": 15,
  "tasks_failed": 0,
  "action_items": [
    {
      "priority": "high",
      "task": "stale_properties",
      "message": "3 properties stale 7+ days",
      "affected_properties": [5, 12, 27]
    }
  ],
  "system_health": {
    "database": "ok",
    "zillow_api": "ok",
    "google_places": "ok",
    "mcp_server": "ok"
  }
}
```

**Notification Types:**
- `HEARTBEAT_CYCLE_COMPLETE` - Normal cycle completion
- `HEARTBEAT_ACTION_NEEDED` - Task requires attention
- `HEARTBEAT_SYSTEM_ALERT` - System health issue
- `HEARTBEAT_TASK_FAILED` - Task execution failed

---

## 🔄 Heartbeat Cycle Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  Heartbeat Cycle Start                      │
│                  (Every 5 minutes)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Check System Health  │
              │  • Database conn      │
              │  • External APIs      │
              │  • Background workers │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Portfolio Scan      │
              │  • Stale properties   │
              │  • Contract deadlines │
              │  • Pipeline status    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Market Intelligence │
              │  • Watchlist matches  │
              │  • Market shifts      │
              │  • Competition        │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Relationship Health │
              │  • Score all contacts │
              │  • Cooling detection  │
              │  • Follow-up flags    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Predictive Insights │
              │  • Re-score deals     │
              │  • Update prob.       │
              │  • Follow-up queue    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Scheduled Tasks     │
              │  • Process due tasks  │
              │  • Generate recurring │
              │  • Send notifications │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Generate Report     │
              │  • Cycle summary      │
              │  • Action items       │
              │  • System metrics     │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Create Notifications│
              │  • High priority      │
              │  • Action items       │
              │  • System alerts      │
              └──────────┬───────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Heartbeat Cycle Complete                    │
│                  Log results, sleep 5m                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Implementation Plan

### Phase 1: Core Heartbeat Engine (1-2 hours)
**Files:**
- `app/services/heartbeat_service.py` - Main heartbeat engine
- `app/models/heartbeat_config.py` - Database model
- `alembic/versions/XXX_add_heartbeat_config.py` - Migration

**Features:**
- Periodic task execution loop
- Task registration system
- Status tracking and logging
- Start/stop controls

### Phase 2: Built-in Monitoring Tasks (2-3 hours)
**Files:**
- `app/services/heartbeat_tasks/` - Task modules
  - `portfolio_tasks.py` - Portfolio monitoring
  - `market_tasks.py` - Market intelligence
  - `relationship_tasks.py` - Relationship health
  - `system_tasks.py` - System health checks
  - `predictive_tasks.py` - Predictive insights

**Features:**
- All default monitoring tasks implemented
- Action item generation
- Notification creation
- Error handling and logging

### Phase 3: Health Check API (1 hour)
**Files:**
- `app/routers/health.py` - Health check endpoints
- Update `app/main.py` - Register router

**Features:**
- Overall health endpoint
- Component-specific checks
- Metrics endpoint
- Heartbeat status endpoint

### Phase 4: MCP Tools (1 hour)
**Files:**
- `mcp_server/tools/heartbeat.py` - Voice control

**Tools (6):**
- `get_heartbeat_status` - Check heartbeat status
- `trigger_heartbeat_cycle` - Manually trigger a cycle
- `pause_heartbeat` - Pause heartbeat
- `resume_heartbeat` - Resume heartbeat
- `configure_heartbeat_task` - Enable/disable tasks
- `get_heartbeat_report` - Detailed last cycle report

### Phase 5: Configuration & Testing (1 hour)
**Files:**
- `HEARTBEAT.md` - Default configuration
- Tests for heartbeat engine
- Integration testing

**Features:**
- Human-readable config file
- Database configuration
- Task scheduling
- Error recovery

---

## 📊 Success Metrics

### Before Heartbeat
- **Agent Mode:** Reactive (waits for commands)
- **Monitoring Frequency:** Manual
- **Proactive Alerts:** None
- **Autonomous Actions:** None
- **Resource Usage:** Static (no background work)

### After Heartbeat
- **Agent Mode:** Proactive (continuously monitoring)
- **Monitoring Frequency:** Every 5 minutes
- **Proactive Alerts:** Automatic for stale deals, contracts, relationships
- **Autonomous Actions:** Pipeline advancement, task processing, notifications
- **Resource Usage:** Slight increase (<5% CPU, <50MB RAM)

---

## 🎤 Voice Commands

```
# Heartbeat Status
"What's the heartbeat status?"
"Is the autonomous agent running?"
"Show me the last heartbeat cycle"

# Manual Control
"Trigger a heartbeat cycle now"
"Pause the heartbeat system"
"Resume heartbeat monitoring"

# Configuration
"Enable stale property monitoring"
"Disable market intelligence checks"
"Configure heartbeat to run every 10 minutes"

# Reports
"Show me the full heartbeat report"
"What did the last cycle find?"
"Any action items from heartbeat?"
```

---

## 🔧 Technical Details

### Heartbeat Interval Strategy

**Tiered Monitoring Frequencies:**
```
System Health:     Every 5 minutes  (critical)
Portfolio Scan:    Every 5 minutes  (high priority)
Market Intel:      Every 15 minutes (medium priority)
Relationships:     Every hour       (deep analysis)
Predictive Models: Every hour       (computationally expensive)
Scheduled Tasks:   Every minute     (time-sensitive)
Daily Digest:      8 AM daily       (summary)
```

### Task Registration Pattern

```python
# Register a monitoring task
heartbeat_engine.register_task(
    name="stale_properties",
    handler=check_stale_properties,
    schedule=300,  # Every 5 minutes
    priority="high",
    enabled=True,
    notification_on_failure=True
)
```

### Graceful Shutdown

```python
# Ensure heartbeat stops cleanly on shutdown
@app.on_event("shutdown")
async def shutdown_heartbeat():
    await heartbeat_engine.stop()
    logger.info("Heartbeat engine stopped gracefully")
```

---

## 🚀 Deployment

### Environment Variables
```bash
# Heartbeat configuration
HEARTBEAT_ENABLED=true
HEARTBEAT_INTERVAL_SECONDS=300  # 5 minutes
HEARTBEAT_LOG_LEVEL=INFO
HEARTBEAT_NOTIFICATIONS_ENABLED=true
```

### Supervisor Integration

Add to `supervisord.conf`:
```ini
[program:ai-realtor-heartbeat]
command=python -c "from app.services.heartbeat_service import heartbeat_engine; asyncio.run(heartbeat_engine.start())"
directory=/app
autostart=true
autorestart=true
stderr_logfile=/var/log/heartbeat.err.log
stdout_logfile=/var/log/heartbeat.out.log
```

---

## 📈 Integration with Existing Features

### Leverages Current Services
- **Insights Service:** Stale property detection
- **Pipeline Service:** Auto-advancement monitoring
- **Scheduled Tasks:** Due task processing
- **Predictive Intelligence:** Probability updates
- **Relationship Intelligence:** Health scoring
- **Market Scanner:** Opportunity detection
- **Competitive Intelligence:** Market monitoring

### Enhances Current Features
- **Daily Digest:** More accurate with continuous monitoring
- **Follow-Up Queue:** Continuously updated
- **Property Scoring:** Re-scored automatically
- **Notifications:** Proactive instead of reactive

---

## 🎯 Expected Outcomes

### 1. True Autonomy
Agent works for you 24/7 without intervention

### 2. Proactive Intelligence
Alerts you to issues before they become problems

### 3. Zero Manual Monitoring
No need to manually check properties, contracts, relationships

### 4. Always Up-to-Date
Scores, probabilities, and insights continuously refreshed

### 5. Peace of Mind
Know that your AI agent is always watching your portfolio

---

## 📝 Summary

**ZeroClaw-Inspired Heartbeat for AI Realtor:**

✅ **Proactive Monitoring:** Continuous 24/7 portfolio surveillance
✅ **Autonomous Actions:** Background tasks without user input
✅ **Health Tracking:** System health monitoring
✅ **Alert System:** Proactive notifications for action items
✅ **Configuration-Driven:** Easy to customize monitoring tasks
✅ **Lightweight:** Minimal resource usage
✅ **Voice-Controlled:** Full MCP tool integration
✅ **Production-Ready:** Robust error handling and logging

**Estimated Implementation:** 6-8 hours
**Lines of Code:** ~1,500 (service + tasks + API + tools)
**New MCP Tools:** 6 tools (141 total)
**New API Endpoints:** 6 endpoints
**Database Tables:** 1 table (heartbeat_config)

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
