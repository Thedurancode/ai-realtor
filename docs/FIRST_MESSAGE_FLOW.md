# 🧠 Memory System — First Message Flow

## What Happens When User Says Their First Message

---

## **Scenario: First-Time User Starts Conversation**

### **User's First Voice Command:**
```
"Hi, I'm John Smith, I'm looking for a condo in Miami under $400,000"
```

---

## **Step-by-Step Memory Creation**

### **🎤 Step 1: Voice Input Received**

```
User says: "Hi, I'm John Smith, I'm looking for a condo in Miami under $400,000"
    ↓
Voice Goal Planner receives the input
    ↓
Session ID: "session-abc-123" (generated automatically)
```

---

### **🧠 Step 2: Memory Graph Extracts Information**

The system analyzes the input and creates **multiple memory types** automatically:

#### **A. IDENTITY Memory Created** (Who is this?)

```python
# System extracts: "John Smith"
memory_graph_service.remember_identity(
    db=db,
    session_id="session-abc-123",
    entity_type="contact",
    entity_id="3",  # Auto-generated or looked up
    identity_data={
        "name": "John Smith",
        "summary": "New client looking for condo",
        "buyer_type": "unknown_yet",
        "first_contact": True
    }
)
```

**Memory stored:**
- **Type:** `identity`
- **Summary:** "New client looking for condo"
- **Importance:** 0.92 (very high — identity defines everything)
- **Payload:** `{name: "John Smith", buyer_type: "unknown_yet", ...}`

---

#### **B. PREFERENCE Memory Created** (What does he want?)

```python
# System extracts: "condo in Miami under $400,000"
memory_graph_service.remember_preference(
    db=db,
    session_id="session-abc-123",
    preference="Looking for condo (not house)",
    entity_type="contact",
    entity_id="3"
)

memory_graph_service.remember_preference(
    db=db,
    session_id="session-abc-123",
    preference="Budget under $400,000",
    entity_type="contact",
    entity_id="3"
)

memory_graph_service.remember_preference(
    db=db,
    session_id="session-abc-123",
    preference="Wants property in Miami",
    entity_type="contact",
    entity_id="3"
)
```

**3 Preferences stored:**
- **Type:** `preference`
- **Importance:** 0.85 (high — preferences drive decisions)
- **Edges:** Each preference linked to Contact 3 with `preference_for` relation

---

#### **C. SESSION STATE Updated** (Quick access)

```python
memory_graph_service.remember_session_state(
    db=db,
    session_id="session-abc-123",
    key="last_contact_name",
    value="John Smith"
)

memory_graph_service.remember_session_state(
    db=db,
    session_id="session-abc-123",
    key="active_search_criteria",
    value={
        "property_type": "condo",
        "city": "Miami",
        "max_price": 400000
    }
)
```

**Session state stored:**
- **Type:** `session_state`
- **Importance:** 0.90 (high — quick access data)
- **Purpose:** Fast lookup without querying full graph

---

### **🔗 Step 3: Memory Graph Built**

After first message, the graph looks like this:

```
┌─────────────────────────────────────────────┐
│          Memory Graph (Session: abc-123)      │
└─────────────────────────────────────────────┘

[Identity: John is new client] (0.92)
    ↓ (describes, 0.95)
[Contact: John Smith] ←────────────────────┐
    ↑                                         │
    │ (preference_for, 0.9)                   │
    │                                         │
[Preference: Wants condo] ──────────────────┤
    │                                         │
[Preference: Budget under $400k] ────────────┤
    │                                         │
[Preference: Wants Miami] ───────────────────┘

[Session State]
    • last_contact_name = "John Smith"
    • active_search_criteria = {type: condo, city: Miami, max_price: 400k}
```

---

### **💾 Step 4: What's Actually Stored in Database**

#### **voice_memory_nodes table:**
```sql
| id | node_type     | summary                    | importance | payload                                      |
|----|---------------|---------------------------|------------|----------------------------------------------|
| 1  | identity      | New client looking for condo| 0.92      | {"name": "John Smith", "buyer_type": "unknown"} |
| 2  | contact       | John Smith                | 0.90      | {"name": "John Smith", "role": "buyer"}       |
| 3  | preference    | Looking for condo         | 0.85      | {"preference": "condo", "entity_id": "3"}      |
| 4  | preference    | Budget under $400,000      | 0.85      | {"preference": "under $400k", "entity_id": "3"} |
| 5  | preference    | Wants property in Miami   | 0.85      | {"preference": "Miami", "entity_id": "3"}      |
| 6  | session_state | last_contact_name         | 0.90      | {"value": "John Smith"}                        |
| 7  | session_state | active_search_criteria    | 0.90      | {"value": {...}}                              |
```

#### **voice_memory_edges table:**
```sql
| id | source_node_id | target_node_id | relation          | weight |
|----|---------------|----------------|-------------------|--------|
| 1  | 1 (identity)   | 2 (contact)    | describes         | 0.95   |
| 2  | 3 (pref)      | 2 (contact)    | preference_for    | 0.9    |
| 3  | 4 (pref)      | 2 (contact)    | preference_for    | 0.9    |
| 4  | 5 (pref)      | 2 (contact)    | preference_for    | 0.9    |
```

---

### **📤 Step 5: Context Auto-Injection (Before AI Response)**

Before the AI responds, the system automatically loads all relevant memories:

```python
# Context Auto-Injection happens automatically
summary = memory_graph_service.get_session_summary(
    db=db,
    session_id="session-abc-123",
    max_nodes=25
)

# Returns:
{
    "session_id": "session-abc-123",
    "session_state": {
        "last_contact_name": "John Smith",
        "active_search_criteria": {
            "property_type": "condo",
            "city": "Miami",
            "max_price": 400000
        }
    },
    "recent_nodes": [
        {
            "node_type": "identity",
            "summary": "New client looking for condo",
            "importance": 0.92,
            "payload": {"name": "John Smith", ...}
        },
        {
            "node_type": "preference",
            "summary": "Looking for condo",
            "importance": 0.85,
            "payload": {"preference": "condo", ...}
        },
        // ... more memories
    ],
    "recent_edges": [
        {
            "relation": "describes",
            "weight": 0.95,
            "source_node_id": 1,
            "target_node_id": 2
        },
        // ... more edges
    ],
    "node_count": 7,
    "edge_count": 4
}
```

---

### **🤖 Step 6: AI Responds With Full Context**

Now the AI has **complete context** and can respond intelligently:

```
AI: "Hi John! I found 12 condos in Miami under $400,000.

I noticed you're looking for:
• Condos (not houses)
• Under $400,000
• In Miami

Would you like me to show you the top 3 options?"
```

**The AI knows:**
- ✅ User's name (John)
- ✅ What he wants (condo, Miami, under $400k)
- ✅ This is a new client (first-time interaction)

---

## **Second Message: Building on Context**

### **User says:**
```
"Yes, and I need 2 bedrooms, a pool would be nice"
```

### **System creates MORE memories:**

```python
# Additional preferences
memory_graph_service.remember_preference(
    db=db,
    session_id="session-abc-123",
    preference="Needs 2+ bedrooms",
    entity_type="contact",
    entity_id="3"
)

memory_graph_service.remember_preference(
    db=db,
    session_id="session-abc-123",
    preference="Wants pool",
    entity_type="contact",
    entity_id="3"
)
```

### **Memory Graph grows:**
```
[Preference: Needs 2+ bedrooms] ──(preference_for, 0.9)──> [Contact: John]
[Preference: Wants pool] ─────────(preference_for, 0.9)──> [Contact: John]
```

### **AI responds with EVEN MORE context:**
```
AI: "Perfect! I've updated your search:

✅ Condo in Miami
✅ Under $400,000
✅ 2+ bedrooms ← New
✅ Pool ← New

I found 4 condos that match ALL your criteria. Should I show them?"
```

---

## **Third Message: Property Found**

### **User says:**
```
"Show me property 5"
```

### **System creates:**

```python
# PROPERTY IDENTITY
memory_graph_service.remember_property(
    db=db,
    session_id="session-abc-123",
    property_id=5,
    address="123 Ocean Drive, Miami Beach",
    city="Miami",
    state="FL"
)

# EVENT (User viewed property)
memory_graph_service.remember_event(
    db=db,
    session_id="session-abc-123",
    event_type="property_view",
    description="User viewed property 5 details",
    entities=[
        {"type": "contact", "id": "3"},
        {"type": "property", "id": "5"}
    ]
)
```

### **Memory Graph now:**
```
[Contact: John Smith]
    ↓ (associated_with, 0.9)
[Property: 123 Ocean Drive]
    ↑ (preference_for, 0.9)
[Preference: Wants pool] ← This property HAS a pool!

[Event: Property view] ──(involved)──> [Contact: John]
                         └─(involved)──> [Property: 5]
```

---

## **Key Insight: Context Accumulates**

After 3 messages, the AI knows:

1. **Who:** John Smith (identity)
2. **What he wants:** Condo, Miami, <$400k, 2BR, pool (preferences)
3. **What he's doing:** Viewing property 5 (event)
4. **What property:** 123 Ocean Drive, Miami Beach (property identity)

**All automatically, without the user repeating themselves!**

---

## **Why This Matters**

### **❌ WITHOUT Memory System:**

```
User: "Show me property 5"
AI: "Here's property 5 at 123 Ocean Drive"

User: "Does it have a pool?"
AI: "Let me check..." (has to search property details again)

User: "Is it under $400k?"
AI: "Let me check..." (has to search again)

User: "Is it in Miami?"
AI: "Let me check..." (has to search again)
```

### **✅ WITH Memory System:**

```
User: "Show me property 5"
AI: "Here's property 5 at 123 Ocean Drive in Miami Beach.

It's $385,000 (under your $400k budget), has 2 bedrooms,
and includes a pool (which you wanted!).

Should I schedule a showing?"
```

**The AI REMEMBERS everything from previous messages!**

---

## **Technical Flow Diagram**

```
User speaks: "I'm John, want condo in Miami under $400k"
    ↓
[Voice Goal Planner]
    ↓ Extract entities & intents
    ↓
[Memory Graph Service]
    ├─→ remember_identity() → "John is new client"
    ├─→ remember_preference() → "Wants condo"
    ├─→ remember_preference() → "Under $400k"
    ├─→ remember_preference() → "In Miami"
    └─→ remember_session_state() → "last_contact_name = John"
    ↓
[Context Auto-Injection]
    ├─→ Load all memories for session
    ├─→ Build relationship graph
    └─→ Inject into AI context
    ↓
[AI Response]
    "Hi John! I found 12 condos in Miami under $400k..."
```

---

## **Summary: First Message Magic**

On the **very first message**, the system:

1. ✅ **Creates identity** — Learns who the user is
2. ✅ **Captures preferences** — Remembers what they want
3. ✅ **Builds relationships** — Links preferences to user
4. ✅ **Updates session state** — Quick access for next time
5. ✅ **Auto-injects context** — AI has full awareness before responding

**Result:** The AI feels like it has known the user for weeks, not seconds!

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
