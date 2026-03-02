#!/usr/bin/env python3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal
from app.models.skip_trace import SkipTrace

db = SessionLocal()
skip_traces = db.query(SkipTrace).all()

print(f"Total skip traces in database: {len(skip_traces)}")
print()
for st in skip_traces:
    print(f"Property ID: {st.property_id}")
    print(f"Owner: {st.owner_name}")
    print(f"Phone: {st.phone_numbers}")
    print(f"Email: {st.emails}")
    print(f"Created: {st.created_at}")
    print("---")
