"""
Migration script to create activity_events table
Run this script directly to create the table
"""
from app.database import engine, Base
from app.models.activity_event import ActivityEvent

def upgrade():
    """Create activity_events table"""
    print("Creating activity_events table...")
    Base.metadata.create_all(bind=engine, tables=[ActivityEvent.__table__])
    print("✅ activity_events table created successfully")

def downgrade():
    """Drop activity_events table"""
    print("Dropping activity_events table...")
    ActivityEvent.__table__.drop(engine)
    print("✅ activity_events table dropped successfully")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
