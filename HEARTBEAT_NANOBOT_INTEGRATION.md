# 🤖 Heartbeat + Nanobot Integration Guide

## Overview

The **Property Heartbeat** feature works seamlessly with Nanobot (your Telegram bot). The bot can check heartbeat status anytime you mention a property.

---

## 🔗 How It Works

### Architecture

```
User (Telegram) → Nanobot Bot → AI Realtor API → Heartbeat Service
                                              ↓
                                        Heartbeat Response
                                              ↓
                                      Formatted Bot Message
                                              ↓
                                        User Sees Status
```

### Data Flow

1. **User asks** about property in Telegram
2. **Nanobot** processes the message
3. **AI** identifies property and determines heartbeat is relevant
4. **Nanobot** calls API: `GET /properties/{id}/heartbeat`
5. **API** returns heartbeat data
6. **Bot** formats response beautifully (no curl commands shown!)
7. **User** sees clean, actionable status

---

## 💬 Voice Commands

### Direct Heartbeat Commands

```
"What's the heartbeat on property 1?"
"How is property 3 doing?"
"Is property 5 stuck?"
"Check the pulse on the Hillsborough property"
"What's the status of property 2?"
```

### Indirect Commands (Also Trigger Heartbeat)

```
"Show me property 1"
"What do we have on 123 Main St?"
"Give me an update on property 2"
```

---

## 🎯 Real Examples

### Example 1: Check Heartbeat Directly

**User:** "What's the heartbeat on property 1?"

**Nanobot Response:**
```
💓 Property #1 (123 Main Street) - Healthy

Stage: Researched (2 of 5)
Time in stage: 0.5 days (threshold: 7 days)

Progress:
  ✅ Zillow Enrichment
  ✅ Skip Trace
  ❌ Contracts Attached (0 contracts)
  ❌ Required Contracts Completed (no required)

Next Action: Attach required contracts

Deal Score: 29.5/100 (Grade D)

Voice: Property #1 at 123 Main Street is researched and
healthy. Next step: attach required contracts.
```

---

### Example 2: Health Status Check

**User:** "Is property 2 stuck?"

**Nanobot Response:**
```
🔍 Property Status Check - 141 Throop Ave

Current Status: New Property (Stage 0 of 5)
Health: 🟡 Stale (5 days in stage, threshold: 3 days)

⚠️ ISSUE: Property has been in "New Property" for 5 days,
which exceeds the 3-day threshold.

Checklist:
  ✅ Property created
  ❌ No Zillow enrichment yet
  ❌ No skip trace done
  ❌ No contracts attached

Next Action: Enrich with Zillow data

Recommendation: Enrich this property now to get it moving
through the pipeline again.
```

---

### Example 3: Quick Status Update

**User:** "Give me an update on property 1"

**Nanobot Response:**
```
📊 Property #1 (123 Main Street) - Quick Update

💓 HEALTHY - Making good progress!

Pipeline Stage: Researched (2/5)
  ✅ Enriched with Zillow data
  ✅ Skip traced (owner: Phuc Pham Jr)
  ⏳ Awaiting contract attachment

Deal Score: 29.5/100 (Grade D)
Next: Attach required contracts

Everything looks on track! Ready to move to the
next stage (Waiting for Contracts).
```

---

## 🔧 Behind the Scenes

### Nanobot's Processing

When you ask about a property, Nanobot:

1. **Resolves property ID**
   - From ID you provide ("property 1")
   - From address ("123 Main St")
   - From context ("the Brooklyn property")

2. **Decides what to check**
   - Always includes heartbeat
   - Checks contract status if waiting_for_contracts
   - Checks contacts if contracts exist

3. **Calls multiple API endpoints**
   ```bash
   # Main property data (includes heartbeat)
   curl "$AI_REALTOR_API_URL/properties/1"

   # Contracts (if needed)
   curl "$AI_REALTOR_API_URL/contracts/?property_id=1"

   # Contacts (if needed)
   curl "$AI_REALTOR_API_URL/contacts/?property_id=1"
   ```

4. **Formats response beautifully**
   - Uses emojis for visual appeal
   - Groups related information
   - Provides clear next actions
   - No ugly curl commands or JSON

---

## 📱 Live Demo

### Test It Now

**In Telegram (@Smartrealtoraibot):**

1. **Check heartbeat:**
   ```
   "What's the heartbeat on property 1?"
   ```

2. **Get status:**
   ```
   "How is property 2 doing?"
   ```

3. **Check if stuck:**
   ```
   "Is property 1 stuck?"
   ```

### What You'll See

The bot will respond with:

- 🏠 Property address
- 📊 Pipeline stage (e.g., "Researched 2/5")
- 💚 Health status (Healthy/Stale/Blocked)
- ✅ Checklist with completion status
- ⏱️ Days in stage vs threshold
- 🎯 Next recommended action
- 📈 Deal score and grade (if available)

---

## 🎯 Heartbeat in Bot's Decision Making

### When Bot Checks Heartbeat

The bot **automatically** checks heartbeat when:

1. **User mentions property** - "Show me property 1"
2. **User asks status** - "How's property 2 doing?"
3. **User asks about progress** - "What's the status?"
4. **User mentions blocking** - "What's blocking the deal?"
5. **User asks for recommendations** - "What should I do next?"

### Bot Uses Heartbeat Data To

1. **Prioritize follow-ups**
   - Stale properties = urgent
   - Blocked properties = critical
   - Healthy properties = normal priority

2. **Recommend next actions**
   - Uses `next_action` field directly
   - Tailors advice based on checklist

3. **Generate alerts**
   - Triggers alerts for stale properties
   - Notifies about blocked deals
   - Celebrates completions

4. **Track pipeline health**
   - Reports on pipeline distribution
   - Identifies bottlenecks
   - Suggests process improvements

---

## 🔄 Integration with Other Bot Features

### Heartbeat + Contracts

```
Bot: "Property #1 is in 'waiting for_contracts'
      and has been for 12 days. Let me check..."

[Checks heartbeat → sees blocked status]

Bot: "⚠️ PROPERTY #1 IS BLOCKED!

This property has been stuck in 'Waiting for Contracts'
for 12 days (threshold: 10 days).

Issue: 2 required contracts still unsigned after 12 days

Contracts:
  ❌ Purchase Agreement (sent 12 days ago)
  ❌ Seller Disclosure (not sent)

Action: Follow up urgently on signing!"
```

---

### Heartbeat + Contacts

```
Bot: "Checking property #2 heartbeat...

Stage: Enriched
Health: Stale (6 days, threshold: 5)
Next: Run skip trace

[Checks contacts]

Bot: "I see the issue - property #2 needs to be skip
traced to find the owner, then we'll add a seller contact.

Want me to run skip trace now?"
```

---

### Heartbeat + Follow-Up Queue

```
Bot: "Analyzing follow-up queue...

[Uses heartbeat data to prioritize]

High Priority (stale > threshold):
  • Property #2 - Stale for 6 days (Enriched)
  • Property #5 - Blocked (no contracts)

Medium Priority:
  • Property #1 - Healthy but needs contracts

[Returns prioritized queue]
```

---

## 🎨 Response Formatting

### Visual Status Indicators

| Health | Emoji | Meaning |
|--------|-------|---------|
| Healthy | 🟢/💚 | On track |
| Stale | 🟡/⚠️ | Needs attention |
| Blocked | 🔴/❌ | Critical issue |

### Checklist Format

```
Progress: ████████░░ 50% complete

Checklist:
  ✅ Step 1 done
  ✅ Step 2 done
  ⏳ Step 3 pending
  ❌ Step 4 not started
```

### Stage Progress

```
Stage: Researched (2 of 5)
Progress Bar: ████████░░░░ 40%

[New Property] → [Enriched] → [Researched] → [Contracts] → [Complete]
     ✅            ✅          ✅          ⏳          ⏳
```

---

## 🔧 Configuration

### Nanobot Environment

Nanobot has these variables set:

```bash
AI_REALTOR_API_URL=http://ai-realtor:8000
AI_REALTOR_API_KEY=nanobot-perm-key-2024
```

### Bot Can Access

```bash
# From nanobot container
docker exec nanobot-gateway sh -c '
  curl -s "$AI_REALTOR_API_URL/properties/1/heartbeat" \
    -H "X-API-Key: $AI_REALTOR_API_KEY"
'

# Returns heartbeat JSON
```

---

## 📊 Heartbeat Data Bot Receives

```json
{
  "property_id": 1,
  "address": "123 Main Street",
  "stage": "researched",
  "stage_label": "Researched",
  "stage_index": 2,
  "total_stages": 5,
  "checklist": [
    {"key": "enriched", "label": "Zillow Enrichment", "done": true},
    {"key": "researched", "label": "Skip Trace", "done": true},
    {"key": "contracts_attached", "label": "Contracts Attached", "done": false},
    {"key": "contracts_completed", "label": "Required Contracts Completed", "done": false}
  ],
  "health": "healthy",
  "health_reason": null,
  "days_in_stage": 0.5,
  "stale_threshold_days": 7,
  "days_since_activity": 0.5,
  "next_action": "Attach required contracts",
  "deal_score": 29.5,
  "score_grade": "D",
  "voice_summary": "Property #1 at 123 Main Street is researched and healthy. Next step: attach required contracts."
}
```

Bot uses this data to generate user-friendly responses!

---

## 🎯 Key Benefits

### 1. At-a-Glance Status
- No need to dig through data
- Instant health check
- Clear next steps

### 2. Proactive Monitoring
- Bot alerts when properties become stale
- Bot notices when deals are blocked
- Bot suggests actions

### 3. Pipeline Tracking
- See where each property is in 5-stage pipeline
- 4-item checklist shows progress
- Time tracking prevents stagnation

### 4. Voice-Native
- Ask naturally: "How's property 1 doing?"
- Get TTS-optimized voice summaries
- No technical language needed

---

## 🚀 Try It Now!

### In Telegram (@Smartrealtoraibot)

**Test these commands:**

1. **Direct heartbeat:**
   ```
   "What's the heartbeat on property 1?"
   ```

2. **Status check:**
   ```
   "How is property 2 doing?"
   ```

3. **Stuck check:**
   ```
   "Is property 1 stuck?"
   ```

4. **General update:**
   ```
   "Give me an update on property 1"
   ```

### Expected Response

The bot will respond with:
- 🏠 Property address
- 📊 Stage and progress
- 💚 Health status
- ✅ Checklist with items marked as done/pending
- ⏱️ Days in stage vs threshold
- 🎯 Clear next action
- 📈 Deal score if available

---

## 🔗 Files Involved

### Nanobot Side

1. **MCP Tool:** `mcp_server/tools/heartbeat.py`
   - Tool name: `get_property_heartbeat`
   - Handles property ID resolution
   - Calls API endpoint
   - Formats response for voice

2. **AI Skill:** `~/.nanobot/workspace/skills/ai-realtor/SKILL.md`
   - Contains usage instructions
   - Voice command examples
   - API calling patterns

### AI Realtor Side

1. **Service:** `app/services/heartbeat_service.py`
   - Core heartbeat logic
   - Health detection
   - Next action recommendations

2. **API Router:** `app/routers/properties.py`
   - `GET /properties/{id}/heartbeat`
   - Auto-included in property endpoints

3. **Schema:** `app/schemas/property.py`
   - `HeartbeatResponse` model
   - 18 fields total

---

## ✅ Summary

**How Heartbeat Works with Nanobot:**

1. ✅ **User asks** about property in Telegram
2. ✅ **Nanobot** resolves property and calls API
3. ✅ **API** returns heartbeat data (18 fields)
4. ✅ **Bot** formats into beautiful response
5. ✅ **User** sees clean, actionable status

**Total Integration:**
- 3 files (service + router + schema)
- 1 MCP tool
- 1 API endpoint
- ~500 lines of code
- Fully voice-native
- Zero configuration needed

**Just ask your bot:**
```
"What's the heartbeat on property 1?"
```

And get instant property status! 💓
