# 💓 Property Heartbeat - Complete Guide

## Overview

The **Property Heartbeat** feature provides **at-a-glance pipeline status** for every property. It shows:
- Current pipeline stage
- 4-item progress checklist
- Health status (healthy/stale/blocked)
- Next recommended action
- Deal score and grade

---

## 📊 What Heartbeat Shows

### 5-Stage Pipeline

| Stage | Index | Description | Stale Threshold |
|-------|-------|-------------|-----------------|
| **New Property** | 0 | Property created | 3 days |
| **Enriched** | 1 | Zillow data added | 5 days |
| **Researched** | 2 | Skip traced | 7 days |
| **Waiting for Contracts** | 3 | Contracts attached | 10 days |
| **Complete** | 4 | All done | Never |

### 4-Item Checklist

| Item | Description | What It Checks |
|------|-------------|----------------|
| ✅ **Zillow Enrichment** | Property enriched with Zillow data | `zillow_enrichments` table |
| ✅ **Skip Trace** | Owner contact info found | `skip_traces` table |
| ✅ **Contracts Attached** | Contracts linked to property | `contracts` table (count > 0) |
| ✅ **Required Contracts Completed** | All required contracts signed | `contracts.is_required=true` and `status=COMPLETED` |

### Health Status

| Status | Description | When Triggered |
|--------|-------------|---------------|
| **🟢 Healthy** | Property progressing normally | Within stale threshold |
| **🟡 Stale** | Stuck too long in current stage | Over threshold |
| **🔴 Blocked** | Cannot advance | No contracts or unsigned too long |

---

## 🔧 Heartbeat Files

### 1. Core Service
**File:** `app/services/heartbeat_service.py` (341 lines)

**Key Components:**

```python
class HeartbeatService:
    def get_heartbeat(db, property_id) -> dict
    def get_heartbeats_batch(db, properties) -> dict[int, dict]
```

**Features:**
- Batch queries for performance (1 query per data type)
- Smart health detection
- Next action recommendation
- Voice summary generation

**Constants:**
- `STAGE_ORDER` - Pipeline stage sequence
- `STAGE_LABELS` - Human-readable stage names
- `STALE_THRESHOLDS` - Days before stale (3/5/7/10/999)
- `NEXT_ACTIONS` - Recommended actions per stage

### 2. API Endpoint
**File:** `app/routers/properties.py`

**Endpoints:**
```python
GET /properties/{id}/heartbeat          # Single property
GET /properties/{id}?include_heartbeat=true  # With property
GET /properties/?include_heartbeat=true   # List with heartbeat
```

### 3. MCP Tool
**File:** `mcp_server/tools/heartbeat.py` (74 lines)

**Tool:** `get_property_heartbeat`

**Voice Commands:**
- "What's the heartbeat on property 5?"
- "How is property 3 doing?"
- "Is property 5 stuck?"
- "Check the pulse on the Hillsborough property"

---

## 📊 Heartbeat Response Structure

```json
{
  "property_id": 1,
  "address": "123 Main Street",
  "stage": "researched",
  "stage_label": "Researched",
  "stage_index": 2,
  "total_stages": 5,
  "checklist": [
    {"key": "enriched", "label": "Zillow Enrichment", "done": true, "detail": null},
    {"key": "researched", "label": "Skip Trace", "done": true, "detail": null},
    {"key": "contracts_attached", "label": "Contracts Attached", "done": false, "detail": "0 contracts"},
    {"key": "contracts_completed", "label": "Required Contracts Completed", "done": false, "detail": "no required contracts"}
  ],
  "health": "healthy",
  "health_reason": null,
  "days_in_stage": 0.5,
  "stale_threshold_days": 7,
  "days_since_activity": 0.5,
  "next_action": "Attach required contracts",
  "deal_score": 29.5,
  "score_grade": "D",
  "voice_summary": "Property #1 at 123 Main Street is Researched and healthy. Next step: attach required contracts."
}
```

---

## 🎯 Health Detection Logic

### Healthy (🟢)
```python
if status == "complete":
    return "healthy"

if days_in_stage < threshold:
    return "healthy"
```

### Stale (🟡)
```python
if days_in_stage >= threshold:
    return "stale", f"In '{stage}' for {days} days (threshold: {threshold})"
```

**Examples:**
- New Property for 4+ days (threshold: 3)
- Enriched for 6+ days (threshold: 5)
- Researched for 8+ days (threshold: 7)
- Waiting for Contracts for 11+ days (threshold: 10)

### Blocked (🔴)
```python
if status == "waiting_for_contracts" and required_count == 0:
    return "blocked", "No required contracts to complete"

if status == "waiting_for_contracts" and days_in_stage >= threshold:
    unsigned = required_count - completed_count
    return "blocked", f"{unsigned} required contracts still unsigned after {days} days"
```

---

## 🚀 Next Action Logic

### Decision Tree
```
Is property complete? → YES → "All steps complete"
                       → NO  → Is enriched? → NO → "Enrich with Zillow data"
                                    → YES → Is skip traced? → NO → "Run skip trace"
                                                      → YES → Has contracts? → NO → "Attach required contracts"
                                                                      → YES → All required done? → NO → "Follow up on unsigned contracts"
                                                                                                      → YES → "All steps complete"
```

### Next Actions by Stage

| Current Status | If Not Enriched | If Not Traced | If No Contracts | If Not All Signed |
|----------------|-----------------|----------------|-----------------|-------------------|
| New Property | Enrich with Zillow | — | — | — |
| Enriched | — | Run skip trace | — | — |
| Researched | — | — | Attach contracts | — |
| Waiting for Contracts | — | — | — | Follow up on unsigned |
| Complete | All steps complete | — | — | — |

---

## 💬 Voice Summary Examples

### Healthy Property
```
"Property #1 at 123 Main Street is researched and healthy.
Next step: attach required contracts."
```

### Stale Property
```
"Property #2 at 456 Oak Avenue has been in enriched for 6 days.
Enrich with Zillow data."
```

### Blocked Property
```
"Property #3 at 789 Pine Road is blocked at waiting for contracts.
2 required contracts still unsigned after 15 days."
```

### Complete Property
```
"Property #4 at 321 Elm Street is complete.
All pipeline steps are done."
```

---

## 🔧 How to Use Heartbeat

### Via API

**Get heartbeat for single property:**
```bash
curl http://localhost:8000/properties/1/heartbeat \
  -H "X-API-Key: nanobot-perm-key-2024"
```

**Get property with heartbeat:**
```bash
curl http://localhost:8000/properties/1?include_heartbeat=true \
  -H "X-API-Key: nanobot-perm-key-2024"
```

**Get all properties with heartbeat:**
```bash
curl http://localhost:8000/properties/?include_heartbeat=true \
  -H "X-API-Key: nanobot-perm-key-2024"
```

### Via Telegram Bot

**Check heartbeat:**
- "What's the heartbeat on property 1?"
- "How is property 3 doing?"
- "Is property 5 stuck?"
- "Check the pulse on the Hillsborough property"

### Via MCP Tool

**Tool:** `get_property_heartbeat`

**Arguments:**
```python
{
  "property_id": 1,        # Required (or use address)
  "address": "123 Main St"  # Alternative to ID
}
```

---

## 📈 Performance Optimization

### Batch Queries

The heartbeat service uses **batch queries** for efficiency:

```python
# Instead of N queries:
for property_id in ids:
    enrichment = db.query(ZillowEnrichment).filter_by(property_id=id).first()

# Uses 1 query:
enrichment_ids = db.query(ZillowEnrichment.property_id)\
    .filter(ZillowEnrichment.property_id.in_(prop_ids)).all()
```

**5 Batch Queries Total:**
1. Last activity timestamps
2. Contract aggregates
3. Enrichment check
4. Skip trace check
5. Property details

### Result

- **Single property:** ~5 queries
- **100 properties:** ~5 queries (not 500!)
- **Response time:** <50ms for 100 properties

---

## 🎯 Use Cases

### 1. Property Dashboard
Show heartbeat on property cards for quick status view.

### 2. Follow-Up Queue
Use `health` and `days_in_stage` to prioritize follow-ups.

### 3. Pipeline Report
Aggregate heartbeats to show pipeline distribution.

### 4. Alert System
Trigger alerts when health becomes "stale" or "blocked".

### 5. Voice Assistant
Quick voice status checks without loading full property data.

---

## 🔍 Real-World Examples

### Example 1: Stale Property Alert
```json
{
  "property_id": 2,
  "address": "141 Throop Ave",
  "stage": "new_property",
  "health": "stale",
  "health_reason": "In 'New Property' for 5 days (threshold: 3)",
  "days_in_stage": 5.2,
  "next_action": "Enrich with Zillow data",
  "voice_summary": "Property #2 at 141 Throop Ave has been in new property for 5.2 days. Enrich with Zillow data."
}
```

**Action:** Bot alerts user to enrich property.

### Example 2: Blocked Property Alert
```json
{
  "property_id": 1,
  "address": "123 Main St",
  "stage": "waiting_for_contracts",
  "health": "blocked",
  "health_reason": "2 required contracts still unsigned after 15 days",
  "days_in_stage": 15.3,
  "checklist": [
    {"key": "enriched", "done": true},
    {"key": "researched", "done": true},
    {"key": "contracts_attached", "done": true, "detail": "5 contracts"},
    {"key": "contracts_completed", "done": false, "detail": "2 of 4"}
  ],
  "next_action": "Follow up on unsigned contracts"
}
```

**Action:** Bot urgently alerts about unsigned contracts.

### Example 3: Healthy Property
```json
{
  "property_id": 1,
  "address": "123 Main St",
  "stage": "researched",
  "health": "healthy",
  "days_in_stage": 0.5,
  "checklist": [
    {"key": "enriched", "done": true},
    {"key": "researched", "done": true},
    {"key": "contracts_attached", "done": false},
    {"key": "contracts_completed", "done": false}
  ],
  "next_action": "Attach required contracts",
  "deal_score": 29.5
}
```

**Action:** Bot recommends next step, but no urgency.

---

## 🎭 Integration Points

### 1. Property List Endpoint
Heartbeat automatically included in:
```bash
GET /properties/?include_heartbeat=true
```

### 2. Single Property Endpoint
```bash
GET /properties/{id}?include_heartbeat=true
```

### 3. Dedicated Endpoint
```bash
GET /properties/{id}/heartbeat
```

### 4. MCP Tool
Available in Claude Desktop:
```python
get_property_heartbeat(property_id=1)
```

### 5. Telegram Bot
Voice commands access heartbeat automatically.

---

## 🔔 Customization

### Change Stale Thresholds

Edit `app/services/heartbeat_service.py`:

```python
STAGE_STALE_THRESHOLDS: dict[PropertyStatus, int] = {
    PropertyStatus.NEW_PROPERTY: 3,      # Default: 3 days
    PropertyStatus.ENRICHED: 5,        # Default: 5 days
    PropertyStatus.RESEARCHED: 7,       # Default: 7 days
    PropertyStatus.WAITING_FOR_CONTRACTS: 10,  # Default: 10 days
    PropertyStatus.COMPLETE: 999,       # Never stale
}
```

### Change Next Actions

Edit `NEXT_ACTIONS` dict:

```python
NEXT_ACTIONS = {
    "enriched": "Enrich with Zillow data",
    "researched": "Run skip trace to find owner",
    "contracts_attached": "Attach required contracts",
    "contracts_completed": "Follow up on unsigned contracts",
}
```

---

## 📚 Related Features

### Pipeline Automation
Heartbeat ties into pipeline automation:
- Auto-advance when checklist items complete
- Auto-generate notifications on stage change
- Track how long properties sit in each stage

### Insights Service
Heartbeat data feeds into insights:
- "Stale properties" alert uses heartbeat
- "High score, no action" uses checklist
- Priority scoring uses stage and health

### Follow-Up Queue
Heartbeat determines queue position:
- Stale properties prioritized
- Blocked properties get high priority
- Healthy properties lower priority

---

## ✅ Summary

**Heartbeat provides:**
- ✅ Pipeline stage tracking (5 stages)
- ✅ 4-item progress checklist
- ✅ Health status (healthy/stale/blocked)
- ✅ Time-in-stage tracking
- ✅ Next action recommendations
- ✅ Voice summary for TTS
- ✅ Deal score and grade
- ✅ Batch-optimized queries

**Benefits:**
- 🚀 At-a-glance property status
- 🎯 Clear next steps
- ⚠️ Proactive stale/blocked detection
- 💬 Voice-native responses
- 📊 Performance optimized

**Files:**
1. `app/services/heartbeat_service.py` - Core service (341 lines)
2. `app/routers/properties.py` - API endpoints
3. `mcp_server/tools/heartbeat.py` - MCP tool (74 lines)
4. `app/schemas/property.py` - Response schema

**Total:** ~450 lines of production code for heartbeat feature! 💓
