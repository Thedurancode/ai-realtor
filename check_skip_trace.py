#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/edduran/Documents/GitHub/ai-realtor')

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
