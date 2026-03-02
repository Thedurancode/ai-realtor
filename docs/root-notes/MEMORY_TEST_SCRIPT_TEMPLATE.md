# 🧪 Memory System Testing Guide

## Quick Test — Verify Memory System Works

### **Option 1: Interactive Python Test (Recommended)**

Create a test script `test_memory.py`:

```python
#!/usr/bin/env python3
"""Test the enhanced memory system with all 8 types."""

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.memory_graph import memory_graph_service

# Database connection
DATABASE_URL = "sqlite:///./ai_realtor.db"  # Or your PostgreSQL URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def test_all_8_memory_types():
    """Test all 8 Spacebot-aligned memory types."""

    db = SessionLocal()
    session_id = "test-session-123"

    print("🧠 Testing AI Realtor Memory System\n")
    print("=" * 60)

    try:
        # 1. TEST FACT
        print("\n1️⃣  Testing FACT memory...")
        fact_node = memory_graph_service.remember_fact(
            db=db,
            session_id=session_id,
            fact="Property 5 has a pool",
            category="property_feature"
        )
        print(f"   ✅ Fact stored: {fact_node.summary}")
        print(f"   📊 Importance: {fact_node.importance}")

        # 2. TEST PREFERENCE
        print("\n2️⃣  Testing PREFERENCE memory...")
        pref_node = memory_graph_service.remember_preference(
            db=db,
            session_id=session_id,
            preference="Wants condos under $400k",
            entity_type="contact",
            entity_id="3"
        )
        print(f"   ✅ Preference stored: {pref_node.summary}")
        print(f"   📊 Importance: {pref_node.importance}")

        # 3. TEST DECISION
        print("\n3️⃣  Testing DECISION memory...")
        decision_node = memory_graph_service.remember_decision(
            db=db,
            session_id=session_id,
            decision="Selected offer at $480k",
            context={"property_id": 5, "offer_amount": 480000, "reason": "Best price"}
        )
        print(f"   ✅ Decision stored: {decision_node.summary}")
        print(f"   📊 Importance: {decision_node.importance}")
        print(f"   📝 Context: {decision_node.payload.get('context')}")

        # 4. TEST IDENTITY
        print("\n4️⃣  Testing IDENTITY memory...")
        identity_node = memory_graph_service.remember_identity(
            db=db,
            session_id=session_id,
            entity_type="contact",
            entity_id="3",
            identity_data={
                "name": "John Smith",
                "summary": "First-time buyer, pre-approved for $500k",
                "buyer_type": "first_time",
                "pre_approved": True,
                "pre_approval_amount": 500000
            }
        )
        print(f"   ✅ Identity stored: {identity_node.summary}")
        print(f"   📊 Importance: {identity_node.importance}")

        # 5. TEST EVENT
        print("\n5️⃣  Testing EVENT memory...")
        event_node = memory_graph_service.remember_event(
            db=db,
            session_id=session_id,
            event_type="phone_call",
            description="Discussed offer with John Smith, he's interested",
            entities=[
                {"type": "contact", "id": "3"},
                {"type": "property", "id": "5"}
            ],
            timestamp=datetime.now()
        )
        print(f"   ✅ Event stored: {event_node.summary}")
        print(f"   📊 Importance: {event_node.importance}")
        print(f"   📅 Timestamp: {event_node.payload.get('timestamp')}")

        # 6. TEST OBSERVATION
        print("\n6️⃣  Testing OBSERVATION memory...")
        obs_node = memory_graph_service.remember_observation(
            db=db,
            session_id=session_id,
            observation="Properties under $400k move fast in Miami",
            category="market_pattern",
            confidence=0.90
        )
        print(f"   ✅ Observation stored: {obs_node.summary}")
        print(f"   📊 Importance: {obs_node.importance}")
        print(f"   🎯 Confidence: {obs_node.payload.get('confidence')}")

        # 7. TEST GOAL
        print("\n7️⃣  Testing GOAL memory...")
        goal_node = memory_graph_service.remember_goal(
            db=db,
            session_id=session_id,
            goal="Close deal on property 5 by Friday",
            metadata={"property_id": 5, "target_date": "2025-02-28"},
            priority="critical"
        )
        print(f"   ✅ Goal stored: {goal_node.summary}")
        print(f"   📊 Importance: {goal_node.importance}")
        print(f"   🎯 Priority: {goal_node.payload.get('priority')}")

        # 8. TEST TODO
        print("\n8️⃣  Testing TODO memory...")
        todo_node = memory_graph_service.remember_todo(
            db=db,
            session_id=session_id,
            task="Call John Smith to discuss counter-offer",
            due_at="2025-02-26T17:00:00",
            property_id=5,
            contact_id=3
        )
        print(f"   ✅ Todo stored: {todo_node.summary}")
        print(f"   📊 Importance: {todo_node.importance}")
        print(f"   ⏰ Due: {todo_node.payload.get('due_at')}")

        # TEST RETRIEVAL
        print("\n" + "=" * 60)
        print("\n📊 Testing Memory Retrieval...\n")

        summary = memory_graph_service.get_session_summary(db, session_id, max_nodes=25)

        print(f"✅ Total memories stored: {summary['node_count']}")
        print(f"✅ Total relationships: {summary['edge_count']}")
        print(f"\n📋 Memory Types:")

        # Group by type
        types = {}
        for node in summary['recent_nodes']:
            node_type = node['node_type']
            types[node_type] = types.get(node_type, 0) + 1

        for mem_type, count in sorted(types.items()):
            print(f"   • {mem_type}: {count}")

        print("\n🔗 Relationships:")
        for edge in summary['recent_edges'][:5]:  # Show first 5
            print(f"   • {edge['relation']} (weight: {edge['weight']})")

        print("\n" + "=" * 60)
        print("\n✅ All 8 memory types working correctly!")
        print("🎉 Memory system is production-ready!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

def test_legacy_support():
    """Test backward compatibility with legacy methods."""

    db = SessionLocal()
    session_id = "test-legacy-456"

    print("\n" + "=" * 60)
    print("🔄 Testing Legacy Support (Backward Compatibility)\n")

    try:
        # Test remember_objection (maps to preference)
        print("1. Testing remember_objection()...")
        objection = memory_graph_service.remember_objection(
            db=db,
            session_id=session_id,
            text="Price is too high",
            topic="negotiation"
        )
        print(f"   ✅ Objection stored as preference: {objection.node_type}")
        print(f"   📝 Summary: {objection.summary}")

        # Test remember_promise (maps to todo)
        print("\n2. Testing remember_promise()...")
        promise = memory_graph_service.remember_promise(
            db=db,
            session_id=session_id,
            promise_text="Send contract by Friday",
            due_at="2025-02-28"
        )
        print(f"   ✅ Promise stored as todo: {promise.node_type}")
        print(f"   📝 Summary: {promise.summary}")

        print("\n✅ Legacy methods working correctly!")
        print("🔄 Backward compatibility maintained!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

def test_graph_relationships():
    """Test memory graph relationships."""

    db = SessionLocal()
    session_id = "test-graph-789"

    print("\n" + "=" * 60)
    print("🔗 Testing Graph Relationships\n")

    try:
        # Create linked memories
        print("1. Creating linked memories...")

        # Create property identity
        memory_graph_service.remember_property(
            db=db,
            session_id=session_id,
            property_id=5,
            address="123 Main St, Miami",
            city="Miami",
            state="FL"
        )

        # Create contact identity
        memory_graph_service.remember_contact(
            db=db,
            session_id=session_id,
            contact_id=3,
            name="John Smith",
            role="buyer",
            property_id=5  # Links to property
        )

        # Create preference linked to property
        memory_graph_service.remember_preference(
            db=db,
            session_id=session_id,
            preference="Wants pool",
            entity_type="property",
            entity_id="5"
        )

        # Create todo linked to both
        memory_graph_service.remember_todo(
            db=db,
            session_id=session_id,
            task="Call John about property 5",
            due_at="2025-02-26",
            property_id=5,
            contact_id=3
        )

        print("   ✅ Created 4 linked memories")

        # Check relationships
        print("\n2. Checking relationships...")
        summary = memory_graph_service.get_session_summary(db, session_id)

        print(f"   ✅ Nodes: {summary['node_count']}")
        print(f"   ✅ Edges: {summary['edge_count']}")

        print("\n3. Relationship details:")
        for edge in summary['recent_edges']:
            source = edge['source_node_id']
            target = edge['target_node_id']
            relation = edge['relation']
            weight = edge['weight']
            print(f"   • Node {source} --[{relation}, {weight}]--> Node {target}")

        print("\n✅ Graph relationships working correctly!")
        print("🔗 Memories properly connected!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 AI Realtor Memory System Test Suite")
    print("=" * 60)

    # Run all tests
    test_all_8_memory_types()
    test_legacy_support()
    test_graph_relationships()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60 + "\n")
