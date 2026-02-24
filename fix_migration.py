#!/usr/bin/env python3
"""
Manual migration fix for the failed property status migration.

This script connects to the production database and fixes the status enum issue.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check current state
    print("\n1. Checking current property statuses...")
    result = conn.execute(text("SELECT DISTINCT status FROM properties;"))
    statuses = [row[0] for row in result]
    print(f"   Current statuses: {statuses}")

    # Check if enum type exists
    print("\n2. Checking enum type...")
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'propertystatus'
        );
    """))
    enum_exists = result.scalar()
    print(f"   Enum exists: {enum_exists}")

    if enum_exists:
        # Get enum values
        result = conn.execute(text("""
            SELECT enumlabel FROM pg_enum
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'propertystatus')
            ORDER BY enumsortorder;
        """))
        enum_values = [row[0] for row in result]
        print(f"   Current enum values: {enum_values}")

    # Fix the data
    print("\n3. Fixing property statuses...")
    conn.execute(text("BEGIN"))

    try:
        # Convert to varchar if needed
        print("   Converting status column to varchar...")
        conn.execute(text("""
            ALTER TABLE properties
            ALTER COLUMN status TYPE VARCHAR(30) USING status::text;
        """))

        # Normalize to lowercase and trim
        print("   Normalizing statuses (lowercase + trim)...")
        conn.execute(text("""
            UPDATE properties
            SET status = TRIM(LOWER(status))
            WHERE status IS NOT NULL;
        """))

        # Map old values to new values
        print("   Mapping old statuses to new pipeline...")
        status_map = {
            'available': 'new_property',
            'pending': 'waiting_for_contracts',
            'sold': 'complete',
            'rented': 'complete',
            'off_market': 'new_property',
        }

        for old_val, new_val in status_map.items():
            conn.execute(text(f"""
                UPDATE properties
                SET status = '{new_val}'
                WHERE status = '{old_val}';
            """))

        # Handle NULLs
        print("   Setting NULL values to 'new_property'...")
        conn.execute(text("""
            UPDATE properties
            SET status = 'new_property'
            WHERE status IS NULL OR status = '';
        """))

        # Verify no invalid values remain
        print("   Verifying all statuses are valid...")
        result = conn.execute(text("""
            SELECT DISTINCT status FROM properties
            WHERE status NOT IN ('new_property','enriched','researched','waiting_for_contracts','complete');
        """))
        invalid = [row[0] for row in result]
        if invalid:
            print(f"   WARNING: Found invalid statuses: {invalid}")
            print("   Setting them to 'new_property'...")
            conn.execute(text("""
                UPDATE properties
                SET status = 'new_property'
                WHERE status NOT IN ('new_property','enriched','researched','waiting_for_contracts','complete');
            """))

        # Drop and recreate enum
        print("   Dropping old enum type...")
        conn.execute(text("DROP TYPE IF EXISTS propertystatus"))

        print("   Creating new enum type...")
        conn.execute(text("""
            CREATE TYPE propertystatus AS ENUM (
                'new_property',
                'enriched',
                'researched',
                'waiting_for_contracts',
                'complete'
            );
        """))

        # Convert column back to enum
        print("   Converting status column back to enum...")
        conn.execute(text("""
            ALTER TABLE properties
            ALTER COLUMN status TYPE propertystatus
            USING status::propertystatus;
        """))

        # Set default
        conn.execute(text("""
            ALTER TABLE properties
            ALTER COLUMN status SET DEFAULT 'new_property';
        """))

        conn.execute(text("COMMIT"))
        print("\n✅ SUCCESS: Database migration fixed!")

    except Exception as e:
        conn.execute(text("ROLLBACK"))
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

    # Verify the fix
    print("\n4. Verification...")
    result = conn.execute(text("""
        SELECT DISTINCT status FROM properties ORDER BY status;
    """))
    final_statuses = [row[0] for row in result]
    print(f"   Final statuses: {final_statuses}")

    result = conn.execute(text("""
        SELECT enumlabel FROM pg_enum
        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'propertystatus')
        ORDER BY enumsortorder;
    """))
    final_enum = [row[0] for row in result]
    print(f"   Final enum values: {final_enum}")

print("\n✅ All done!")
