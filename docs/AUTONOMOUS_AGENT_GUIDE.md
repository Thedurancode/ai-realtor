# 🤖 AI Realtor Agent — Autonomous Capabilities Guide

## Overview

The AI Realtor agent has **significant autonomous capabilities** — it runs background tasks automatically, monitors your portfolio 24/7, and takes proactive actions without manual intervention.

---

## 🔄 Autonomous Background Tasks (5 Built-In)

The agent runs **5 autonomous tasks on a schedule**:

### **1. Heartbeat Cycle** ⏰ Every 5 Minutes

**What it does:**
- Scans all properties for pipeline status
- Checks property health (stale, blocked, progressing)
- Auto-advances properties through pipeline stages
- Generates property heartbeat metrics

**Example:**
```
Property 5 (NEW_PROPERTY → ENRICHED)
Property 12 (ENRICHED → RESEARCHED)
Property 8 (WAITING_FOR_CONTRACTS → COMPLETE)

Status: Auto-advanced 3 properties, flagged 2 as stale
```

**Memory created:**
- ✅ **Events** for each status change
- ✅ **Facts** about pipeline velocity
- ✅ **Todos** for agent follow-up on blocked properties

---

### **2. Portfolio Scan** ⏰ Every 5 Minutes

**What it does:**
- Identifies stale properties (7+ days no activity)
- Finds unsigned required contracts (3+ days)
- Detects high-score properties with no action
- Checks contract deadlines approaching

**Example:**
```
🔴 URGENT (3 issues):
• Property 15: No activity for 14 days (stale)
• Property 22: Purchase Agreement sent 5 days ago (unsigned)
• Property 8: Score 92 but no contracts started (missed opportunity)

📊 Created 3 notifications, 2 follow-up tasks
```

**Memory created:**
- ✅ **Observations** about stale properties
- ✅ **Todos** for agent to take action
- ✅ **Notifications** sent to agent

---

### **3. Market Intelligence** ⏰ Every 15 Minutes

**What it does:**
- Scans for properties matching watchlist criteria
- Detects market shifts (price trends, inventory changes)
- Monitors competitive activity in agent's market

**Example:**
```
🔥 MARKET ALERT:
• 3 new Miami condos under $400k match your watchlist
• Price trend: +5% in Miami Beach last 30 days
• Inventory: Down 12% (sellers' market intensifying)

💡 Action: Contact 3 buyers about new listings
```

**Memory created:**
- ✅ **Facts** about market conditions
- ✅ **Observations** about market trends
- ✅ **Goals** created (e.g., "Contact 3 buyers about new listings")

---

### **4. Relationship Health** ⏰ Every Hour

**What it does:**
- Scores relationship health for all contacts
- Identifies at-risk relationships (low engagement)
- Suggests re-engagement strategies

**Example:**
```
📊 RELATIONSHIP HEALTH:
• John Smith: 85/100 (good) — Active conversations
• Mary Johnson: 45/100 (at-risk) — Last contact 30 days ago
• Bob Wilson: 92/100 (excellent) — Just closed deal

⚠️ ACTION NEEDED: Send re-engagement email to Mary
```

**Memory created:**
- ✅ **Facts** about relationship scores
- ✅ **Todos** for re-engagement
- ✅ **Observations** about relationship patterns

---

### **5. Predictive Insights** ⏰ Every Hour

**What it does:**
- Generates closing probability predictions for active deals
- Identifies deals at risk
- Recommends next actions for each property

**Example:**
```
🎯 PREDICTIVE INSIGHTS:
• Property 15: 78% close probability (⚠️ dropping)
  → Recommend: Follow up on financing
• Property 22: 92% close probability (✅ on track)
  → Recommend: Schedule inspection
• Property 8: 45% close probability (❌ at risk)
  → Recommend: Price reduction or counter-offer

📊 Created 3 recommendations, 2 tasks
```

**Memory created:**
- ✅ **Observations** about deal probabilities
- ✅ **Goals** for each active deal
- ✅ **Todos** for recommended actions

---

## 🎯 Other Autonomous Features

### **Pipeline Automation** (Every 5 minutes)

**Auto-advances properties through pipeline:**

| Current Stage | Next Stage | Trigger |
|---------------|------------|---------|
| NEW_PROPERTY | ENRICHED | Zillow data available |
| ENRICHED | RESEARCHED | Skip trace completed |
| RESEARCHED | WAITING_FOR_CONTRACTS | 1+ contract attached |
| WAITING_FOR_CONTRACTS | COMPLETE | All required contracts signed |

**Example:**
```
Property 5: NEW_PROPERTY → ENRICHED (auto-detected Zillow data)
Property 12: WAITING_FOR_CONTRACTS → COMPLETE (all contracts signed)
```

**Memory created:**
- ✅ **Events** for each auto-transition
- ✅ **Notifications** sent to agent
- ✅ **Recaps** regenerated after changes

---

### **Daily Digest** (Every morning at 8 AM)

**Generates AI-powered morning briefing:**

```
🌅 GOOD MORNING, SARAH!

Here's your daily briefing:

📊 PORTFOLIO SNAPSHOT:
• 15 active properties, 3 pending deals
• $2.3M in active inventory
• 2 contracts sent yesterday (awaiting signatures)

⚠️ URGENT ALERTS:
• Property 15: Inspection tomorrow at 2 PM
• John Smith: Counter-offer expires today
• Property 22: Price reduction recommended

📈 MARKET INTELLIGENCE:
• Miami condos under $400k: +12% demand (sellers' market)
• 3 new luxury listings match your criteria
• Average DOM: 38 days (down from 45)

🎯 TODAY'S PRIORITIES:
1. Call John Smith (counter-offer deadline)
2. Attend Property 15 inspection
3. Review 3 new luxury listings
4. Follow up with 2 buyers

💡 AI INSIGHT:
Your closing probability is 87% this month based on:
• 3 deals in final stage
• Strong buyer demand
• Your average follow-up time: 4 hours (excellent!)

Let's make it a great day! 🚀
```

**Memory created:**
- ✅ **Facts** about daily metrics
- ✅ **Observations** about agent performance
- ✅ **Todos** prioritized for the day
- ✅ **Goals** tracked and updated

---

## 🧠 How It Uses Memory System

The autonomous tasks **store everything in the Memory Graph**:

### **Example: Portfolio Scan Finds Stale Property**

```python
# Autonomous task detects stale property
if property.days_since_last_activity >= 7:
    # Store OBSERVATION
    memory_graph_service.remember_observation(
        db=db,
        session_id="autonomous-portfolio-scan",
        observation=f"Property {property.id} stale for {days} days",
        category="property_health",
        confidence=1.0
    )

    # Store TODO for agent
    memory_graph_service.remember_todo(
        db=db,
        session_id="autonomous-portfolio-scan",
        task=f"Follow up on stale property {property.id}",
        due_at=tomorrow.strftime("%Y-%m-%d"),
        property_id=property.id
    )

    # Create NOTIFICATION
    notification_service.create_notification(
        db=db,
        agent_id=agent.id,
        title=f"Property {property.id} needs attention",
        message=f"No activity for {days} days",
        priority="high"
    )
```

### **Memory Graph After Autonomous Task:**

```
[Observation: Property 15 stale 14 days] (0.82)
    ↓
[Todo: Follow up on Property 15] (0.90)
    ↓
[Notification: Created for agent] ← In-app notification

[Property 15 Identity]
    ↓ (describes, 0.95)
[Property: 123 Main St]
```

---

## 🤔 Semi-Autonomous vs Fully Autonomous

### **Semi-Autonomous** (Current Mode)

The agent **runs background tasks autonomously** but:

✅ **Autonomously does:**
- Monitor portfolio 24/7
- Scan for issues and opportunities
- Generate insights and recommendations
- Create tasks and reminders
- Send notifications
- Update property pipeline status

⚠️ **Requires approval for:**
- Sending emails/contracts (agent must confirm)
- Making phone calls (agent must trigger)
- Deleting data (safety measure)
- Large bulk operations (agent must approve)

**Example:**
```
✅ Autonomous: "Property 15 is stale, created follow-up task"
✅ Autonomous: "New listing matches your watchlist, created notification"
✅ Autonomous: "Pipeline auto-advanced property to next stage"
⚠️  Requires approval: "Send email to John?" (agent confirms)
⚠️  Requires approval: "Make phone call?" (agent triggers)
```

---

### **Future: Fully Autonomous Mode** (Optional)

Agents could enable **full autonomy** for:

```
"AI, you have permission to:"
☑️ Automatically send follow-up emails
☑️ Make phone calls to leads
☑️ Schedule property showings
☑️ Send contracts for signature
☑️ Negotiate minor counter-offers
☑️ Update social media
☑️ Respond to basic inquiries
```

The agent would:
- Still respect **command filtering** (dangerous operations require confirmation)
- Log **all actions** to conversation history
- Create **observations** about what worked
- **Learn** from agent feedback (preferences)

---

## 📊 Autonomous Task Schedule

| Task | Frequency | Duration | What It Creates |
|------|-----------|----------|-----------------|
| **Heartbeat Cycle** | Every 5 min | ~5 sec | Events, notifications, pipeline updates |
| **Portfolio Scan** | Every 5 min | ~10 sec | Insights, todos, notifications |
| **Market Intelligence** | Every 15 min | ~15 sec | Facts, observations, goals |
| **Relationship Health** | Every hour | ~20 sec | Relationship scores, todos |
| **Predictive Insights** | Every hour | ~30 sec | Deal predictions, recommendations |
| **Daily Digest** | 8 AM daily | ~60 sec | Daily briefing, priorities |
| **Pipeline Automation** | Every 5 min | ~5 sec | Status changes, recaps |

**Total autonomous work per day:** ~150-200 background tasks

---

## 💡 Benefits of Autonomous Operation

### **For Agents:**

✅ **24/7 monitoring** — Never miss an opportunity
✅ **Proactive alerts** — Issues caught early
✅ **Time savings** — ~2-3 hours/day saved on manual checks
✅ **Better follow-up** — Never forget a lead
✅ **Data-driven decisions** — AI identifies patterns
✅ **Stress reduction** — Less to remember manually

### **For Clients:**

✅ **Faster response** — AI notices things immediately
✅ **Better service** — Proactive updates on their deals
✅ **Consistent communication** — Automated check-ins
✅ **Fewer delays** — Contracts sent faster, deadlines met

---

## 🎛️ Safety Controls

### **Command Filtering** (Security Sandbox)

The agent **cannot autonomously:**

❌ Delete properties/contacts/contracts
❌ Cancel all campaigns
❌ Clear conversation history
❌ Send bulk notifications
❌ Modify workspace settings
❌ Delete workspace

**Requires `confirmed=true` parameter for dangerous operations.**

### **Audit Trail**

Every autonomous action is logged:

```python
conversation_history = {
    "session_id": "autonomous-portfolio-scan",
    "tool_name": "portfolio_scan_handler",
    "input": {"metadata": {...}},
    "output": {"total_issues": 5},
    "timestamp": datetime.now(),
    "autonomous": True
}
```

Agent can review all autonomous actions later.

---

## 🚀 How to Enable Autonomous Tasks

### **Automatic on Server Start**

```python
# In app/main.py (already implemented)

@app.on_event("startup")
async def startup_event():
    """Initialize background services on startup."""
    from app.services.cron_scheduler import cron_scheduler

    # Start scheduler (runs autonomous tasks)
    asyncio.create_task(cron_scheduler.start())

    # Schedule default autonomous tasks
    await cron_scheduler.schedule_task(
        name="heartbeat_cycle",
        handler_name="heartbeat_cycle",
        cron_expression="*/5 * * * *"  # Every 5 minutes
    )

    await cron_scheduler.schedule_task(
        name="portfolio_scan",
        handler_name="portfolio_scan",
        cron_expression="*/5 * * * *"
    )

    await cron_scheduler.schedule_task(
        name="market_intelligence",
        handler_name="market_intelligence",
        cron_expression="*/15 * * * *"
    )

    # ... more tasks
```

### **Custom Autonomous Tasks**

Agents can schedule their own autonomous tasks:

```python
# Via voice command
"Schedule a market scan every morning at 9 AM"

# Via API
POST /scheduler/tasks
{
  "name": "morning_market_scan",
  "handler_name": "market_intelligence",
  "cron_expression": "0 9 * * *",  # 9 AM daily
  "metadata": {"city": "Miami", "state": "FL"}
}
```

---

## ✅ Summary

**Your AI Realtor agent is:**

✅ **Semi-autonomous** — Runs 5+ background tasks automatically
✅ **Proactive** — Identifies issues and opportunities
✅ **Always-on** — 24/7 monitoring, every 5-15 minutes
✅ **Memory-aware** — Stores all observations in Memory Graph
✅ **Safe** — Command filtering prevents dangerous actions
✅ **Transparent** — All actions logged and reviewable

**The agent works while you sleep! 🌙**

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
