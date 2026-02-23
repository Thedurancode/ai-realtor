# 🧪 How to Test the Memory System

## Quick Start (3 Methods)

---

## **Method 1: Run the Test Script** ✅ (Easiest)

```bash
# Navigate to project directory
cd /Users/edduran/Documents/GitHub/ai-realtor

# Run the test script
python test_memory.py
```

**What it does:**
- Tests all 8 memory types
- Tests legacy backward compatibility
- Tests graph relationships
- Shows detailed output

**Expected output:**
```
🧪 AI Realtor Memory System Test Suite
============================================================

🧠 Testing AI Realtor Memory System

============================================================

1️⃣  Testing FACT memory...
   ✅ Fact stored: Property 5 has a pool
   📊 Importance: 0.75

2️⃣  Testing PREFERENCE memory...
   ✅ Preference stored: Wants condos under $400k
   📊 Importance: 0.85

...

✅ ALL TESTS PASSED!
```

---

## **Method 2: Interactive Python Shell**

```bash
# Navigate to project
cd /Users/edduran/Documents/GitHub/ai-realtor

# Start Python
python

# Then run these commands:
```

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.memory_graph import memory_graph_service
from datetime import datetime

# Connect to database
engine = create_engine("sqlite:///./ai_realtor.db")
Session = sessionmaker(bind=engine)
db = Session()
session_id = "test-session-123"

# Test 1: Store a FACT
fact = memory_graph_service.remember_fact(
    db=db,
    session_id=session_id,
    fact="Property 5 has a pool",
    category="property_feature"
)
print(f"✅ Fact: {fact.summary}, Importance: {fact.importance}")

# Test 2: Store a PREFERENCE
pref = memory_graph_service.remember_preference(
    db=db,
    session_id=session_id,
    preference="Wants condos under $400k",
    entity_type="contact",
    entity_id="3"
)
print(f"✅ Preference: {pref.summary}, Importance: {pref.importance}")

# Test 3: Store a GOAL
goal = memory_graph_service.remember_goal(
    db=db,
    session_id=session_id,
    goal="Close deal on property 5 by Friday",
    priority="critical"
)
print(f"✅ Goal: {goal.summary}, Importance: {goal.importance}")

# Test 4: Retrieve memories
summary = memory_graph_service.get_session_summary(db, session_id)
print(f"\n📊 Total memories: {summary['node_count']}")
print(f"🔗 Total relationships: {summary['edge_count']}")

# Test 5: List memory types
from collections import Counter
types = Counter([n['node_type'] for n in summary['recent_nodes']])
for mem_type, count in types.items():
    print(f"   • {mem_type}: {count}")

# Cleanup
db.close()
```

---

## **Method 3: Via Voice Commands** (Production Test)

Once your server is running, you can test via voice:

```bash
# Start your server
uvicorn app.main:app --reload

# In Claude Desktop, say:
```

```
"Remember that property 5 has a pool"
"Note that John prefers condos under $400k"
"Remember that I decided to offer $480k"
"Store the fact that Miami market is up 5%"
"Create a goal to close the deal by Friday"
"Add a todo to call John by Thursday"
"Record the event that I called John today"
"Note that properties under $400k move fast"
```

**Then verify via API:**

```bash
# Get session summary
curl http://localhost:8000/context/history?session_id=test-session-123

# Or check memory nodes directly
curl http://localhost:8000/memory/nodes?session_id=test-session-123
```

---

## **Method 4: Direct Database Query**

```bash
# Open database
sqlite3 ai_realtor.db

# Query memory nodes
SELECT node_type, COUNT(*) as count
FROM voice_memory_nodes
WHERE session_id = 'test-session-123'
GROUP BY node_type;

# Query with details
SELECT node_type, summary, importance
FROM voice_memory_nodes
WHERE session_id = 'test-session-123'
ORDER BY created_at DESC
LIMIT 10;

# Query relationships
SELECT e.relation, e.weight,
       n1.node_type as source_type,
       n2.node_type as target_type
FROM voice_memory_edges e
JOIN voice_memory_nodes n1 ON e.source_node_id = n1.id
JOIN voice_memory_nodes n2 ON e.target_node_id = n2.id
WHERE e.session_id = 'test-session-123'
LIMIT 10;
```

---

## **What to Look For**

### ✅ **Success Indicators:**

1. **All 8 types created**
   - fact, preference, decision, identity, event, observation, goal, todo

2. **Importance scores correct**
   - fact: 0.75
   - preference: 0.85
   - decision: 0.95
   - identity: 0.92
   - event: 0.88
   - observation: 0.82
   - goal: 1.0 (critical priority)
   - todo: 0.90

3. **Graph edges created**
   - Relationships between memories
   - Weights between 0.85 and 0.95

4. **Retrieval works**
   - `get_session_summary()` returns memories
   - Edge count > 0 (relationships exist)

5. **Legacy methods work**
   - `remember_objection()` → creates preference
   - `remember_promise()` → creates todo

---

## **Troubleshooting**

### **Issue: Import errors**

```bash
# Make sure you're in the project directory
cd /Users/edduran/Documents/GitHub/ai-realtor

# Check Python path
python -c "import sys; print(sys.path)"

# Install dependencies if needed
pip install -r requirements.txt
```

### **Issue: Database connection error**

```bash
# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Or use SQLite for testing
export DATABASE_URL="sqlite:///./ai_realtor.db"
```

### **Issue: Duplicate memories**

This is normal! The system uses `upsert` logic:
- Same memory → updates `last_seen_at`
- Different memory → creates new node

### **Issue: No relationships created**

Make sure you're:
1. Providing `entity_type` and `entity_id` for preferences
2. Providing `property_id` or `contact_id` for todos
3. Providing `entities` list for events

---

## **Performance Testing**

### **Test with 1000+ memories:**

```python
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.memory_graph import memory_graph_service

engine = create_engine("sqlite:///./ai_realtor.db")
Session = sessionmaker(bind=engine)
db = Session()
session_id = "perf-test-123"

# Create 1000 memories
start = time.time()
for i in range(1000):
    memory_graph_service.remember_fact(
        db=db,
        session_id=session_id,
        fact=f"Test fact {i}",
        category="test"
    )
db.commit()
creation_time = time.time() - start

# Retrieve memories
start = time.time()
summary = memory_graph_service.get_session_summary(db, session_id, max_nodes=100)
retrieval_time = time.time() - start

print(f"✅ Created 1000 memories in {creation_time:.2f}s")
print(f"✅ Retrieved 100 memories in {retrieval_time:.3f}s")
print(f"📊 Total nodes: {summary['node_count']}")

db.close()
```

**Expected:**
- Creation: < 5 seconds
- Retrieval: < 0.1 seconds

---

## **Verification Checklist**

- [ ] All 8 memory types can be created
- [ ] Importance scores are correct
- [ ] Graph edges are created
- [ ] Retrieval works fast (< 100ms)
- [ ] Legacy methods still work
- [ ] Relationships link correctly
- [ ] Payload data is preserved
- [ ] Timestamps are accurate

---

## **Next Steps**

Once tests pass:

1. ✅ Memory system is working
2. 🚀 Deploy to production
3. 📊 Monitor memory usage
4. 🎯 Use in voice commands
5. 📈 Scale to thousands of memories

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
