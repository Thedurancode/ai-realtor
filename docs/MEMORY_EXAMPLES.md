# 🧠 Memory System — Real-World Examples

## Complete Workflows Showing All 8 Memory Types in Action

---

## Example 1: First-Time Buyer Journey

### **Scenario: John Smith is a first-time buyer looking for a condo in Miami**

#### **Step 1: Initial Contact (Identity + Preference)**

```python
# User says: "Hi, I'm John Smith, I'm a first-time buyer looking for a condo"

# Capture IDENTITY
memory_graph_service.remember_identity(
    db=db,
    session_id="session-abc",
    entity_type="contact",
    entity_id="3",
    identity_data={
        "name": "John Smith",
        "summary": "First-time buyer, looking for condo",
        "buyer_type": "first_time",
        "experience_level": "beginner",
        "motivation": "Primary residence"
    }
)

# Capture PREFERENCE
memory_graph_service.remember_preference(
    db=db,
    session_id="session-abc",
    preference="Looking for condo (not house)",
    entity_type="contact",
    entity_id="3"
)
```

**Memory Graph Created:**
```
[Identity: John is first-time buyer] (0.92)
    ↓ (describes, 0.95)
[Contact: John Smith]

[Preference: Wants condo] (0.85)
    ↓ (preference_for, 0.9)
[Contact: John Smith]
```

---

#### **Step 2: Budget Discussion (Preference + Fact)**

```python
# User says: "My budget is under $400,000"

# Capture PREFERENCE
memory_graph_service.remember_preference(
    db=db,
    session_id="session-abc",
    preference="Budget under $400,000",
    entity_type="contact",
    entity_id="3"
)

# Agent learns FACT about market
memory_graph_service.remember_fact(
    db=db,
    session_id="session-abc",
    fact="Average Miami condo price is $425,000",
    category="market_data"
)
```

---

#### **Step 3: Property Requirements (Preference + Observation)**

```python
# User says: "I need 2 bedrooms, a pool would be nice, and I want to be near the beach"

# Capture PREFERENCES
memory_graph_service.remember_preference(
    db=db,
    session_id="session-abc",
    preference="Needs 2+ bedrooms",
    entity_type="contact",
    entity_id="3"
)

memory_graph_service.remember_preference(
    db=db,
    session_id="session-abc",
    preference="Wants pool",
    entity_type="contact",
    entity_id="3"
)

memory_graph_service.remember_preference(
    db=db,
    session_id="session-abc",
    preference="Wants to be near beach",
    entity_type="contact",
    entity_id="3"
)

# Agent makes OBSERVATION
memory_graph_service.remember_observation(
    db=db,
    session_id="session-abc",
    observation="Beachfront condos with pools under $400k are rare (only 3 active listings)",
    category="market_inventory",
    confidence=0.90
)
```

---

#### **Step 4: Property Found (Identity + Goal)**

```python
# Agent finds property at "123 Ocean Drive, Miami Beach"

# Create PROPERTY IDENTITY
memory_graph_service.remember_identity(
    db=db,
    session_id="session-abc",
    entity_type="property",
    entity_id="5",
    identity_data={
        "address": "123 Ocean Drive, Miami Beach",
        "summary": "2BR condo with pool, 1 block from beach",
        "property_type": "condo",
        "bedrooms": 2,
        "has_pool": True,
        "distance_to_beach": "1 block",
        "price": 385000,
        "category": "beachfront"
    }
)

# Create GOAL
memory_graph_service.remember_goal(
    db=db,
    session_id="session-abc",
    goal="Help John buy 123 Ocean Drive",
    metadata={
        "property_id": 5,
        "contact_id": 3,
        "property_address": "123 Ocean Drive",
        "buyer_budget": 400000,
        "property_price": 385000,
        "within_budget": True
    },
    priority="high"
)
```

**Memory Graph Now:**
```
[Identity: John is first-time buyer] → [Contact: John Smith]
[Preference: Wants condo] → [Contact: John Smith]
[Preference: Budget under $400k] → [Contact: John Smith]
[Preference: Wants pool] → [Contact: John Smith]

[Identity: 123 Ocean Drive condo] → [Property: 5]
[Preference: Wants pool] → [Property: 5]

[Goal: Buy 123 Ocean Drive] (1.0)
    ↓ (for_property, 0.9)
[Property: 5]
    ↓ (associated_with, 0.9)
[Contact: John Smith]
```

---

#### **Step 5: Property Showing (Event + Todo)**

```python
# Schedule and complete property showing

# Create TODO
memory_graph_service.remember_todo(
    db=db,
    session_id="session-abc",
    task="Show 123 Ocean Drive to John Smith",
    due_at="2025-02-27T14:00:00",
    property_id=5,
    contact_id=3
)

# After showing, create EVENT
memory_graph_service.remember_event(
    db=db,
    session_id="session-abc",
    event_type="property_showing",
    description="John viewed 123 Ocean Drive, loved the pool and location",
    entities=[
        {"type": "contact", "id": "3"},
        {"type": "property", "id": "5"}
    ],
    timestamp=datetime.now()
)
```

---

#### **Step 6: Buyer Feedback (Preference + Decision)**

```python
# John says: "I love it! Let's make an offer at $375,000"

# Capture PREFERENCE (positive feedback)
memory_graph_service.remember_preference(
    db=db,
    session_id="session-abc",
    preference="Loves 123 Ocean Drive",
    entity_type="property",
    entity_id="5"
)

# Capture DECISION
memory_graph_service.remember_decision(
    db=db,
    session_id="session-abc",
    decision="Make offer at $375,000 for 123 Ocean Drive",
    context={
        "property_id": 5,
        "offer_amount": 375000,
        "list_price": 385000,
        "below_list_by": 10000,
        "reason": "Starting negotiation",
        "buyer_authorized": True
    }
)

# Create TODOs
memory_graph_service.remember_todo(
    db=db,
    session_id="session-abc",
    task="Prepare purchase offer for $375,000",
    due_at="2025-02-27T18:00:00",
    property_id=5
)

memory_graph_service.remember_todo(
    db=db,
    session_id="session-abc",
    task="Send offer to listing agent",
    due_at="2025-02-27T18:00:00",
    property_id=5
)
```

---

#### **Step 7: Offer Accepted (Event + Decision)**

```python
# Seller accepts offer!

# Create EVENT
memory_graph_service.remember_event(
    db=db,
    session_id="session-abc",
    event_type="offer_accepted",
    description="Seller accepted $375,000 offer for 123 Ocean Drive",
    entities=[
        {"type": "property", "id": "5"},
        {"type": "contact", "id": "3"}
    ],
    timestamp=datetime.now()
)

# Update GOAL status
memory_graph_service.remember_goal(
    db=db,
    session_id="session-abc",
    goal="Close on 123 Ocean Drive by April 15",
    metadata={
        "property_id": 5,
        "contact_id": 3,
        "offer_accepted": True,
        "offer_amount": 375000,
        "closing_date": "2025-04-15",
        "status": "under_contract"
    },
    priority="critical"
)
```

---

#### **Step 8: Inspection & Closing (Event + Todo + Fact)**

```python
# Schedule inspection
memory_graph_service.remember_todo(
    db=db,
    session_id="session-abc",
    task="Schedule property inspection",
    due_at="2025-03-01T12:00:00",
    property_id=5
)

# Inspection completed
memory_graph_service.remember_event(
    db=db,
    session_id="session-abc",
    event_type="inspection_completed",
    description="Property inspection passed, no major issues found",
    entities=[{"type": "property", "id": "5"}],
    timestamp=datetime.now()
)

# Learn FACT
memory_graph_service.remember_fact(
    db=db,
    session_id="session-abc",
    fact="Property 5 inspection passed with no issues",
    category="inspection"
)
```

---

## Memory Graph After Full Journey

```
[Identity: John is first-time buyer] (0.92)
    ↓ (describes, 0.95)
[Contact: John Smith]
    ↑ (associated_with, 0.9)
[Property: 123 Ocean Drive]
    ↓ (describes, 0.95)
[Identity: 2BR condo with pool] (0.92)

[Preferences]
    ├── Wants condo → [Contact: John]
    ├── Budget under $400k → [Contact: John]
    ├── Wants pool → [Contact: John], [Property: 5]
    └── Loves 123 Ocean Drive → [Property: 5]

[Decision: Offer $375k] (0.95)
    ↓ (for_property, 0.9)
[Property: 5]

[Events]
    ├── Property showing → [Contact: John], [Property: 5]
    ├── Offer accepted → [Contact: John], [Property: 5]
    └── Inspection completed → [Property: 5]

[Goal: Close by April 15] (1.0)
    ↓ (for_property, 0.9)
[Property: 5]

[Todos]
    ├── Show property → [Property: 5]
    ├── Prepare offer → [Property: 5]
    ├── Send offer → [Property: 5]
    └── Schedule inspection → [Property: 5]

[Observation]
    └── Beachfront condos under $400k rare (0.90)

[Facts]
    ├── Average Miami condo $425k
    └── Property 5 inspection passed
```

---

## Example 2: Investment Property Analysis

### **Scenario: Agent notices market opportunity**

```python
# Agent analyzes market data and notices pattern

# OBSERVATION
memory_graph_service.remember_observation(
    db=db,
    session_id="session-def",
    observation="Miami condos under $300k are selling within 7 days (vs 30-day average)",
    category="market_velocity",
    confidence=0.92
)

# FACT (backing observation)
memory_graph_service.remember_fact(
    db=db,
    session_id="session-def",
    fact="Miami market inventory under $300k: 12 listings (down 40% from last month)",
    category="market_inventory"
)

# Create GOAL based on observation
memory_graph_service.remember_goal(
    db=db,
    session_id="session-def",
    goal="Find 3 Miami condos under $300k for investor clients",
    metadata={
        "reason": "High demand, low supply",
        "target_velocity": "7 days to sell",
        "potential_roi": "15-20%"
    },
    priority="high"
)

# Create ACTIONABLE TODOs
memory_graph_service.remember_todo(
    db=db,
    session_id="session-def",
    task="Search MLS for Miami condos under $300k",
    due_at="2025-02-26T10:00:00"
)

memory_graph_service.remember_todo(
    db=db,
    session_id="session-def",
    task="Call investor clients with opportunities",
    due_at="2025-02-26T14:00:00"
)
```

---

## Example 3: Negotiation Strategy

### **Scenario: Multiple offers on same property**

```python
# Property 7 has 3 offers

# EVENT
memory_graph_service.remember_event(
    db=db,
    session_id="session-ghi",
    event_type="multiple_offers",
    description="Received 3 offers on property 7: $450k, $460k, $470k",
    entities=[{"type": "property", "id": "7"}],
    timestamp=datetime.now()
)

# OBSERVATION (agent insight)
memory_graph_service.remember_observation(
    db=db,
    session_id="session-ghi",
    observation="Buyers competing aggressively on properties under $500k",
    category="negotiation_pattern",
    confidence=0.85
)

# DECISION
memory_graph_service.remember_decision(
    db=db,
    session_id="session-ghi",
    decision="Counter highest offer at $480k and request escalation clause",
    context={
        "property_id": 7,
        "highest_offer": 470000,
        "counter_amount": 480000,
        "strategy": "Test buyer ceiling",
        "reasoning": "High demand suggests room to negotiate"
    }
)

# TODO
memory_graph_service.remember_todo(
    db=db,
    session_id="session-ghi",
    task="Send counter-offer to $470k buyer",
    due_at="2025-02-26T16:00:00",
    property_id=7
)
```

---

## Best Practices Summary

### **DO ✅**
1. **Create Identity first** — Define who/what something is
2. **Track Preferences** — Learn what user likes/dislikes
3. **Record Decisions** — Major choices get highest importance
4. **Timestamp Events** — When matters as much as what
5. **Link Everything** — Create edges between related memories
6. **Set Appropriate Importance** — Goals = 1.0, Facts = 0.75
7. **Add Context** — Payload explains why/who/what

### **DON'T ❌**
1. **Don't skip Identity** — Everything needs context
2. **Don't ignore Preferences** — They drive recommendations
3. **Don't forget Edges** — Relationships make graph powerful
4. **Don't over-use Importance 1.0** — Only for critical goals
5. **Don't duplicate** — Check before creating new memory
6. **Don't mix types** — Events ≠ Observations ≠ Facts
7. **Don't leave memories unlinked** — Isolated memories are useless

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
