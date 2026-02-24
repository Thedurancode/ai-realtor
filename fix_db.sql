-- Fix the failed property status enum migration
-- This should be run directly against the database

BEGIN;

-- 1. Convert column to VARCHAR to decouple from enum
ALTER TABLE properties
ALTER COLUMN status TYPE VARCHAR(30) USING status::text;

-- 2. Normalize to lowercase and trim
UPDATE properties
SET status = TRIM(LOWER(status))
WHERE status IS NOT NULL;

-- 3. Map old values to new values
UPDATE properties SET status = 'new_property' WHERE status = 'available';
UPDATE properties SET status = 'waiting_for_contracts' WHERE status = 'pending';
UPDATE properties SET status = 'complete' WHERE status = 'sold';
UPDATE properties SET status = 'complete' WHERE status = 'rented';
UPDATE properties SET status = 'new_property' WHERE status = 'off_market';

-- 4. Handle NULL values
UPDATE properties
SET status = 'new_property'
WHERE status IS NULL OR status = '';

-- 5. Catch-all for any remaining invalid values
UPDATE properties
SET status = 'new_property'
WHERE status NOT IN ('new_property','enriched','researched','waiting_for_contracts','complete');

-- 6. Drop old enum type
DROP TYPE IF EXISTS propertystatus;

-- 7. Create new enum type
CREATE TYPE propertystatus AS ENUM (
    'new_property',
    'enriched',
    'researched',
    'waiting_for_contracts',
    'complete'
);

-- 8. Convert column back to enum
ALTER TABLE properties
ALTER COLUMN status TYPE propertystatus USING status::propertystatus;

-- 9. Set default
ALTER TABLE properties
ALTER COLUMN status SET DEFAULT 'new_property';

COMMIT;

-- Verify
SELECT DISTINCT status FROM properties ORDER BY status;
SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'propertystatus') ORDER BY enumsortorder;
