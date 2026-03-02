# 💓 Heartbeat vs Recap - What's the Difference?

## Short Answer

**Yes, they're similar!** Heartbeat is like a **mini-recap** focused on pipeline status. But they serve different purposes.

---

## 🎯 Quick Comparison

| Aspect | Heartbeat | Property Recap |
|--------|-----------|---------------|
| **Purpose** | Pipeline status snapshot | Comprehensive property summary |
| **Length** | 1-2 sentences | 3-4 paragraphs |
| **Format** | Structured data + checklist | Narrative text |
| **Focus** | Progress & next actions | Complete picture |
| **Update Trigger** | Auto on every property view | Auto on key events |
| **Included In** | Every property response | Separate field, not auto-included |

---

## 📊 Side-by-Side Example

### Heartbeat Response

```json
{
  "property_id": 1,
  "address": "123 Main Street",
  "stage_label": "Researched",
  "stage_index": 2,
  "total_stages": 5,
  "health": "healthy",
  "days_in_stage": 0.5,
  "next_action": "Attach required contracts",
  "checklist": [
    {"label": "Zillow Enrichment", "done": true},
    {"label": "Skip Trace", "done": true},
    {"label": "Contracts Attached", "done": false},
    {"label": "Required Contracts Completed", "done": false}
  ],
  "voice_summary": "Property #1 at 123 Main Street is researched and healthy. Next step: attach required contracts."
}
```

**What it tells you:**
- Where is the property in the pipeline? (Stage 2 of 5)
- Is it healthy or stuck? (Healthy)
- What's been completed? (Enrichment ✓, Skip trace ✓)
- What's next? (Attach contracts)
- How long has it been here? (0.5 days)

---

### Property Recap Response

```json
{
  "property_id": 1,
  "recap_text": "**Property Overview**

123 Main Street is a 3-bedroom, 2-bathroom house located in New York, NY, priced at $850,000. This 1,800 sqft property was built on a spacious lot and offers great potential for the right buyer.

**Market Analysis**

The property comes with comprehensive Zillow data showing a rent Zestimate of $1,361/month. The area features three schools within a mile, with ratings ranging from 4-6, making it attractive for families.

**Transaction Status**

Currently in the 'Researched' stage, this property has been enriched with Zillow data and skip-traced to find the owner (Phuc Pham Jr). The next step is to attach required contracts to move toward closing.

**Investment Potential**

With a deal score of 29.5 (Grade D), there's room for improvement. The property would benefit from attaching contracts and identifying a buyer to move forward in the pipeline.",
  "voice_summary": "Property #1 at 123 Main Street in New York is priced at $850,000 with 3 bedrooms and 2 bathrooms. Currently researched and ready for contracts.",
  "recap_context": {
    "price": 850000,
    "bedrooms": 3,
    "bathrooms": 2,
    "square_feet": 1800,
    "zestimate_available": false,
    "rent_zestimate": 1361,
    "has_zillow": true,
    "has_skip_trace": true,
    "owner_name": "Phuc Pham Jr"
  }
}
```

**What it tells you:**
- Full property description (3-4 paragraphs)
- Market analysis (schools, Zestimate)
- Transaction status (what's happened)
- Investment potential (deal score analysis)
- Property details (beds, baths, sqft, price)
- Context data (structured JSON)

---

## 🔍 Key Differences

### 1. **Purpose**

**Heartbeat = "Status Check"**
- Think: "Quick pulse check"
- Like: Checking your phone's battery percentage
- Question: "Where is this property in the pipeline?"
- Use: Quick decision-making

**Recap = "Full Summary"**
- Think: "Executive summary"
- Like: Reading a property brief
- Question: "Tell me everything about this property"
- Use: Comprehensive understanding

---

### 2. **Length**

| Feature | Heartbeat | Recap |
|---------|-----------|-------|
| Voice Summary | 1-2 sentences | 2-3 sentences |
| Full Response | 8-10 lines | 3-4 paragraphs |
| Words | ~30-50 words | ~150-200 words |

---

### 3. **What's Included**

**Heartbeat:**
- ✅ Pipeline stage (1 of 5)
- ✅ Checklist (4 items)
- ✅ Health status (healthy/stale/blocked)
- ✅ Days in stage
- ✅ Next action
- ✅ Deal score/grade

**Recap:**
- ✅ Property overview (paragraph)
- ✅ Market analysis (paragraph)
- ✅ Transaction status (paragraph)
- ✅ Investment potential (paragraph)
- ✅ Property details (price, beds, baths, sqft)
- ✅ Structured context (JSON with 10+ fields)

---

### 4. **When Used**

**Heartbeat is used:**
- Every time you view a property (auto-included)
- When checking pipeline status
- When prioritizing follow-ups
- When identifying stuck properties

**Recap is used:**
- After major changes (enrichment, skip trace)
- Before making decisions
- When comprehensive context needed
- On-demand when requested

---

### 5. **Voice Examples**

**Heartbeat Voice Command:**
```
User: "What's the heartbeat on property 1?"

Bot: "Property #1 at 123 Main Street is researched and
healthy. Next step: attach required contracts."
(1 sentence, ~15 words)
```

**Recap Voice Command:**
```
User: "Give me the recap for property 1"

Bot: "Property #1 at 123 Main Street in New York is priced at
$850,000 with 3 bedrooms and 2 bathrooms. Currently
researched and ready for contracts."
(2 sentences, ~20 words)
```

---

## 🎯 When to Use Which

### Use Heartbeat For:
- ✅ Quick status checks
- ✅ Pipeline monitoring
- ✅ Prioritizing follow-ups
- ✅ Identifying stuck properties
- ✅ Daily status updates
- ✅ Portfolio health checks

**Example:**
- "How's property 1 doing?"
- "What's blocking my deals?"
- "Which properties need attention?"

### Use Recap For:
- ✅ Comprehensive briefings
- ✅ Decision-making support
- ✅ Client presentations
- ✅ Investment analysis
- ✅ Deal reviews
- ✅ Background research

**Example:**
- "Tell me everything about property 1"
- "Give me the full picture on 123 Main St"
- "What's the investment potential?"
- "Brief me on this property"

---

## 💡 Practical Example

### Scenario: Checking on Your Pipeline

**You ask:** "What needs attention today?"

**Bot uses Heartbeat** (not full recap):
```
🔍 Properties Needing Attention

1. Property #1 (123 Main St)
   💓 Status: Healthy
   📊 Stage: Researched (2/5)
   ⏳ Next: Attach contracts

2. Property #2 (141 Throop Ave)
   💓 Status: Stale (5 days in New Property)
   📊 Stage: New Property (0/5)
   ⚠️ Action: Enrich with Zillow data

3. Property #3 (Park Ave)
   💓 Status: Blocked
   📊 Stage: Waiting for Contracts (3/5)
   🔴 Issue: 2 contracts unsigned for 15 days
   🚨 Urgent: Follow up immediately
```

**Notice:** Quick, actionable, no fluff!

---

### Scenario: Preparing for Client Meeting

**You ask:** "Give me the recap for property 1"

**Bot uses full Recap:**
```
📋 Property #1 (123 Main St) - Full Briefing

**Property Overview:**
123 Main Street is a 3-bedroom, 2-bathroom house located
in New York, NY, priced at $850,000. This 1,800 sqft property
was built on a spacious lot and offers great potential.

**Market Position:**
The property comes with comprehensive Zillow data showing
a rent Zestimate of $1,361/month. The area features three schools
within a mile with ratings of 4-6, making it attractive for families.

**Current Status:**
Currently in 'Researched' stage with owner information secured
(Phuc Pham Jr). Ready to move to contract attachment phase.

**Investment Analysis:**
With a deal score of 29.5 (Grade D), there's room for improvement.
Focus on contract attachment and buyer identification to improve the score.
```

**Notice:** Comprehensive, detailed, perfect for meetings!

---

## 🔗 How They Work Together

```
Property View Request
        ↓
┌───────────────┐
│  Heartbeat    │ ← Always included (quick status)
│  (1-2 sent.)   │
└───────────────┘
        ↓
┌───────────────┐
│  Full Property │
│  Data          │
└───────────────┘
        ↓
┌───────────────┐
│  Recap?        │ ← Only if requested or major event
│  (3-4 para.)   │
└───────────────┘
```

**API Response Structure:**
```json
{
  "id": 1,
  "address": "123 Main St",
  "heartbeat": {     ← Always included
    "stage_label": "Researched",
    "health": "healthy",
    "voice_summary": "1-2 sentences"
  },
  "recap": {           ← Separate field, only when needed
    "recap_text": "3-4 paragraphs...",
    "voice_summary": "2-3 sentences"
  }
}
```

---

## 📊 Data Overlap

Both Heartbeat and Recap include:

| Field | Heartbeat | Recap |
|-------|-----------|-------|
| Property ID | ✅ | ✅ |
| Address | ✅ | ✅ |
| Voice Summary | ✅ (1-2 sent.) | ✅ (2-3 sent.) |
| Deal Score | ✅ | ✅ (in context) |
| Stage | ✅ (detailed) | ✅ (mentioned) |

**But Heartbeat adds:**
- Checklist (4 items)
- Health status
- Days in stage
- Next action

**And Recap adds:**
- Full narrative (3-4 paragraphs)
- Market analysis
- Transaction history
- Investment analysis
- Structured context (10+ JSON fields)

---

## 🎭 Real-World Usage

### Daily Pipeline Check (Heartbeat)

**You:** "What's the status of my properties?"

**Bot** uses Heartbeat (quick overview):
```
📊 Pipeline Status - 2 Properties

Property #1 (123 Main St)
  Stage: Researched (2/5)
  Health: ✅ Healthy
  Next: Attach contracts

Property #2 (141 Throop Ave)
  Stage: New Property (0/5)
  Health: ⚠️ Stale (5 days)
  Next: Enrich with Zillow
```

---

### Client Briefing (Recap)

**You:** "I'm meeting a client for property 1, brief me"

**Bot** uses Recap (comprehensive):
```
📋 Client Briefing - Property #1 (123 Main St)

**Property:**
$850,000 • 3 bed, 2 bath • 1,800 sqft • New York, NY

**Market:**
Rent Zestimate: $1,361/month
Area: 3 schools nearby (rated 4-6)

**Status:**
Researched stage, owner found (Phuc Pham Jr)
Ready for contracts

**Investment:**
Deal Score: 29.5/100 (Grade D)
Potential: Good location, needs contracts

**Next Steps:**
1. Attach purchase agreement
2. Identify buyer
3. Move to closing
```

---

## ✅ Summary

**Heartbeat = Quick Pulse Check** 💓
- "Where is this property?"
- "Is it stuck?"
- "What's next?"
- 1-2 sentences
- Auto-included in property views

**Recap = Full Briefing** 📄
- "Tell me everything"
- "Give me the full picture"
- 3-4 paragraphs
- Separate API call
- Used when comprehensive detail needed

**Think of it this way:**
- **Heartbeat** = Checking your phone's battery percentage
- **Recap** = Reading your phone's full specification

**They complement each other!** 🎯
