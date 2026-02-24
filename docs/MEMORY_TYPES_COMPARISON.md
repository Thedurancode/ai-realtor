# 🧠 Memory Types — Quick Reference

## Spacebot vs AI Realtor Comparison

| Spacebot Type | AI Realtor Type | Importance | Example |
|--------------|-----------------|------------|---------|
| **Fact** | `fact` | 0.75 | "Property 5 has a pool" |
| **Preference** | `preference` | 0.85 | "Wants condos under $400k" |
| **Decision** | `decision` | 0.95 | "Selected offer at $480k" |
| **Identity** | `identity` | 0.92 | "John is first-time buyer" |
| **Event** | `event` | 0.88 | "Phone call with John" |
| **Observation** | `observation` | 0.82 | "Market slowing down" |
| **Goal** | `goal` | 1.0 | "Close deal by Friday" |
| **Todo** | `todo` | 0.90 | "Call John by Thursday" |

---

## Memory Type Decision Tree

```
Is it a specific action to take?
└─ YES → TODO (task, due date)
└─ NO → Is it an objective?
    └─ YES → GOAL (outcome to achieve)
    └─ NO → Did it happen at a specific time?
        └─ YES → EVENT (phone call, meeting, showing)
        └─ NO → Is it a pattern the agent noticed?
            └─ YES → OBSERVATION (market trend, pattern)
            └─ NO → Is it a choice that was made?
                └─ YES → DECISION (offer selected, financing chosen)
                └─ NO → Is it who/what something is?
                    └─ YES → IDENTITY (John is buyer, Property 5 is luxury)
                    └─ NO → Is it something the user likes/wants?
                        └─ YES → PREFERENCE (wants pool, dislikes busy road)
                        └─ NO → FACT (learned information)
```

---

## When to Use Each Type

### **FACT** 📚
- Agent learns something new
- Market data, regulations, processes
- Property features, contact info
- "Miami market is up 5%"

### **PREFERENCE** ❤️
- User expresses requirements
- User rejects/compliments something
- "Wants pool", "Prefers condos"
- Mapped from legacy `objection`

### **DECISION** ✅
- User makes a choice
- Offer accepted, financing selected
- "Selected $480k offer"
- Irreversible, high importance

### **IDENTITY** 🪪
- Who/what something is
- Core attributes defining entity
- "John is first-time buyer"
- "Property 5 is luxury condo"

### **EVENT** 📅
- Something happened at specific time
- Phone calls, showings, signings
- "Called John on Tuesday"
- Creates timeline

### **OBSERVATION** 👀
- Agent notices pattern/trend
- Market shifts, behaviors
- "Properties under $400k move fast"
- Guides strategy

### **GOAL** 🎯
- Objective to achieve
- Has priority (critical/high/medium/low)
- "Close deal by Friday"
- Drives todos

### **TODO** ✍️
- Actionable task
- Has due date, linked to property/contact
- "Call John by Thursday"
- Mapped from legacy `promise`

---

## Code Examples

```python
# FACT
memory_graph_service.remember_fact(
    db, session_id,
    fact="Property 5 has a pool",
    category="property_feature"
)

# PREFERENCE
memory_graph_service.remember_preference(
    db, session_id,
    preference="Wants properties with pools",
    entity_type="property",
    entity_id="5"
)

# DECISION
memory_graph_service.remember_decision(
    db, session_id,
    decision="Selected offer at $480k",
    context={"property_id": 5, "reason": "Best price"}
)

# IDENTITY
memory_graph_service.remember_identity(
    db, session_id,
    entity_type="contact",
    entity_id="3",
    identity_data={
        "name": "John Smith",
        "summary": "First-time buyer, pre-approved $500k",
        "buyer_type": "first_time"
    }
)

# EVENT
memory_graph_service.remember_event(
    db, session_id,
    event_type="phone_call",
    description="Discussed offer with John",
    entities=[{"type": "contact", "id": "3"}],
    timestamp=datetime.now()
)

# OBSERVATION
memory_graph_service.remember_observation(
    db, session_id,
    observation="Properties under $400k move fast in Miami",
    category="market_pattern",
    confidence=0.85
)

# GOAL
memory_graph_service.remember_goal(
    db, session_id,
    goal="Close deal on property 5 by Friday",
    metadata={"property_id": 5},
    priority="high"
)

# TODO
memory_graph_service.remember_todo(
    db, session_id,
    task="Call John to discuss counter-offer",
    due_at="2025-02-26T17:00:00",
    property_id=5,
    contact_id=3
)
```

---

## Memory Graph Example

```
[Identity: John is first-time buyer] (0.92)
    ↓ (describes, 0.95)
[Contact: John Smith]
    ↓ (associated_with, 0.9)
[Property: 123 Main St]
    ↑ (preference_for, 0.9)
[Preference: Wants pool] (0.85)

[Event: Phone call with John] (0.88)
    ↓ (involved, 0.85)
[Contact: John Smith]

[Goal: Close deal by Friday] (1.0)
    ↓ (for_property, 0.9)
[Property: 123 Main St]
    ↓ (for_property, 0.9)
[Todo: Call John by Thursday] (0.90)

[Decision: Selected $480k offer] (0.95)
    ↓ (for_property, 0.9)
[Property: 123 Main St]

[Observation: Market slowing] (0.82)
    ↓ (blocks, 0.85)
[Goal: Close deal by Friday]
```

---

## Quick Tips

1. **Every memory should have a type** — Don't leave it generic
2. **Link memories with edges** — Relationships make the graph powerful
3. **Set appropriate importance** — Goals = 1.0, Facts = 0.75
4. **Add timestamps to events** — When matters as much as what
5. **Include context in payload** — Explain why/who/what
6. **Check for duplicates** — Don't create same memory twice
7. **Decisions are permanent** — Highest importance after goals
8. **Preferences drive recommendations** — Track what user likes/dislikes
9. **Observations guide strategy** — Learn from patterns
10. **Todos come from goals** — Break goals into actionable tasks

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
