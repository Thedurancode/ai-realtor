#!/usr/bin/env python3
"""Test the enhanced memory system with all 8 types."""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.memory_graph import memory_graph_service

DATABASE_URL = "sqlite:///./ai_realtor.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def test_all_8_memory_types():
    db = SessionLocal()
    session_id = "test-session-123"

    print("\n" + "=" * 60)
    print("🧠 Testing AI Realtor Memory System")
    print("=" * 60)

    try:
        # Test all 8 types
        tests = [
            ("FACT", lambda: memory_graph_service.remember_fact(db, session_id, "Property 5 has a pool", "property_feature")),
            ("PREFERENCE", lambda: memory_graph_service.remember_preference(db, session_id, "Wants condos under $400k", "contact", "3")),
            ("DECISION", lambda: memory_graph_service.remember_decision(db, session_id, "Selected offer at $480k", {"property_id": 5})),
            ("IDENTITY", lambda: memory_graph_service.remember_identity(db, session_id, "contact", "3", {"name": "John Smith", "summary": "First-time buyer"})),
            ("EVENT", lambda: memory_graph_service.remember_event(db, session_id, "phone_call", "Called John", [{"type": "contact", "id": "3"}])),
            ("OBSERVATION", lambda: memory_graph_service.remember_observation(db, session_id, "Market slowing down", "market", 0.9)),
            ("GOAL", lambda: memory_graph_service.remember_goal(db, session_id, "Close deal by Friday", {"property_id": 5}, "critical")),
            ("TODO", lambda: memory_graph_service.remember_todo(db, session_id, "Call John", "2025-02-26", 5, 3)),
        ]

        for i, (name, test_func) in enumerate(tests, 1):
            print(f"\n{i}. Testing {name}...")
            node = test_func()
            print(f"   ✅ {name}: {node.summary}")
            print(f"   📊 Importance: {node.importance}")
            db.commit()

        # Summary
        print("\n" + "=" * 60)
        summary = memory_graph_service.get_session_summary(db, session_id)
        print(f"\n✅ Total memories: {summary['node_count']}")
        print(f"✅ Relationships: {summary['edge_count']}")
        print("\n🎉 All 8 memory types working!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_all_8_memory_types()
    print("\n" + "=" * 60 + "\n")
