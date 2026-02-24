#!/bin/bash

# Deploy and fix the migration issue
set -e

echo "=== AI Realtor Deployment Fix ==="
echo ""

# Get DATABASE_URL from secrets
echo "1. Getting database connection..."
DB_URL=$(fly secrets list -a ai-realtor --json | jq -r '.[] | select(.Name == "DATABASE_URL") | .Value')

if [ -z "$DB_URL" ]; then
    echo "ERROR: Could not get DATABASE_URL"
    exit 1
fi

# Extract connection parts
DB_HOST=$(echo $DB_URL | grep -oP '@\K[^:]+')
DB_PORT=$(echo $DB_URL | grep -oP ':[^:]+/\K[^ ]+' | cut -d'/' -f1)
DB_USER=$(echo $DB_URL | grep -oP '//\K[^:]+')
DB_PASS=$(echo $DB_URL | grep -oP ':\K[^@]+')
DB_NAME=$(echo $DB_URL | grep -oP '/\K[^?]+')

echo "   Host: $DB_HOST"
echo "   Database: $DB_NAME"
echo ""

# Run the fix via psql through SSH
echo "2. Running database fix..."
fly ssh console -C "psql -h $DB_HOST -U $DB_USER -d $DB_NAME" << 'EOF' < fix_db.sql

echo "   Fix applied!"
echo ""

# Restart the app
echo "3. Restarting the app..."
fly apps restart ai-realtor

echo ""
echo "=== Fix Complete ==="
echo "API should be available at: https://ai-realtor.fly.dev"
