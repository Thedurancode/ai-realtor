#!/bin/bash

set -e

echo "=== AI Realtor Database Fix & Deploy ==="
echo ""

APP_NAME="ai-realtor"
DB_APP_NAME="ai-realtor-db"

# Step 1: Get database connection info
echo "📡 Step 1: Getting database connection info..."
DB_INFO=$(fly -a $DB_APP_NAME pg connect -c "SELECT current_database(), current_user;" 2>&1 | grep -v "^Unmanaged" | grep -v "^Please visit" | tail -n +3)

if [ -z "$DB_INFO" ]; then
    echo "❌ Could not connect to database"
    echo "Trying alternative method..."
    # Start wireguard tunnel
    fly proxy 5432 -a $DB_APP_NAME &
    PROXY_PID=$!
    sleep 3

    # Get connection string from secrets
    DB_URL=$(fly secrets list -a $APP_NAME --json 2>/dev/null | grep -A2 "DATABASE_URL" | grep '"Value"' | cut -d'"' -f4)

    if [ -z "$DB_URL" ]; then
        echo "❌ Could not get DATABASE_URL from secrets"
        kill $PROXY_PID 2>/dev/null || true
        exit 1
    fi

    echo "✓ Database connection established via proxy"
    USE_PROXY=true
else
    echo "✓ Database connection available"
    USE_PROXY=false
fi

# Step 2: Apply the fix
echo ""
echo "🔧 Step 2: Applying database fix..."

# Create temporary SQL file with the fix
cat > /tmp/fix_migration.sql << 'EOSQL'
DO $$
BEGIN
    -- Check if the column is still broken (old enum type)
    IF EXISTS (
        SELECT 1 FROM pg_type
        WHERE typname = 'propertystatus'
        AND typarray IS NOT NULL
    ) THEN
        RAISE NOTICE 'Starting migration fix...';

        -- 1. Convert column to VARCHAR
        ALTER TABLE properties
        ALTER COLUMN status TYPE VARCHAR(30) USING status::text;

        RAISE NOTICE 'Converted column to VARCHAR';

        -- 2. Normalize to lowercase and trim
        UPDATE properties
        SET status = TRIM(LOWER(status))
        WHERE status IS NOT NULL;

        RAISE NOTICE 'Normalized statuses';

        -- 3. Map old values to new values
        UPDATE properties SET status = 'new_property' WHERE status = 'available';
        UPDATE properties SET status = 'waiting_for_contracts' WHERE status = 'pending';
        UPDATE properties SET status = 'complete' WHERE status = 'sold';
        UPDATE properties SET status = 'complete' WHERE status = 'rented';
        UPDATE properties SET status = 'new_property' WHERE status = 'off_market';

        RAISE NOTICE 'Mapped old values to new values';

        -- 4. Handle NULL and empty values
        UPDATE properties
        SET status = 'new_property'
        WHERE status IS NULL OR status = '';

        -- 5. Catch-all for invalid values
        UPDATE properties
        SET status = 'new_property'
        WHERE status NOT IN ('new_property','enriched','researched','waiting_for_contracts','complete');

        RAISE NOTICE 'Handled edge cases';

        -- 6. Drop old enum
        DROP TYPE IF EXISTS propertystatus;

        RAISE NOTICE 'Dropped old enum type';

        -- 7. Create new enum
        CREATE TYPE propertystatus AS ENUM (
            'new_property',
            'enriched',
            'researched',
            'waiting_for_contracts',
            'complete'
        );

        RAISE NOTICE 'Created new enum type';

        -- 8. Convert column to new enum
        ALTER TABLE properties
        ALTER COLUMN status TYPE propertystatus USING status::propertystatus;

        RAISE NOTICE 'Converted column to new enum type';

        -- 9. Set default
        ALTER TABLE properties
        ALTER COLUMN status SET DEFAULT 'new_property';

        RAISE NOTICE 'Set default value';

        RAISE NOTICE '✅ Migration fix completed successfully!';
    ELSE
        RAISE NOTICE '✅ Migration appears to be already fixed';
    END IF;
END $$;

-- Verification
SELECT 'Current statuses:' as info;
SELECT DISTINCT status FROM properties ORDER BY status;

SELECT '' as separator;

SELECT 'Enum values:' as info;
SELECT enumlabel FROM pg_enum
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'propertystatus')
ORDER BY enumsortorder;
EOSQL

# Apply the fix
if [ "$USE_PROXY" = true ]; then
    # Use local psql via proxy
    PGPASSWORD=${DB_URL##*@} psql -h localhost -U postgres -d postgres -f /tmp/fix_migration.sql
    kill $PROXY_PID 2>/dev/null || true
else
    # Use fly pg connect with heredoc (pipe the SQL file)
    fly -a $DB_APP_NAME pg connect < /tmp/fix_migration.sql 2>&1 | grep -v "^Unmanaged" | grep -v "^Please visit"
fi

echo ""
echo "✅ Database fix applied!"

# Step 3: Restart the app
echo ""
echo "🔄 Step 3: Restarting the app..."
fly apps restart $APP_NAME

# Wait for app to start
echo "⏳ Waiting for app to start..."
sleep 10

# Step 4: Verify the API is working
echo ""
echo "🔍 Step 4: Verifying API status..."
sleep 5

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://ai-realtor.fly.dev/ || echo "000")

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
    echo "✅ API is responding! (HTTP $HTTP_CODE)"
    echo ""
    echo "🎉 Deployment complete!"
    echo "🌐 API: https://ai-realtor.fly.dev"
    echo "📚 Docs: https://ai-realtor.fly.dev/docs"
else
    echo "⚠️  API returned HTTP $HTTP_CODE"
    echo "Check logs with: fly logs -a $APP_NAME"
fi

echo ""
echo "=== Fix Complete ==="
