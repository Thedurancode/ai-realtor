#!/bin/bash
set -e

API_KEY="${API_KEY:-your-api-key-here}"
BASE_URL="${BASE_URL:-http://localhost:8000}"

# Check environment variables
if [ -z "$META_ACCESS_TOKEN" ] || [ -z "$META_AD_ACCOUNT_ID" ]; then
  echo "❌ Error: META_ACCESS_TOKEN and META_AD_ACCOUNT_ID must be set"
  echo ""
  echo "Set them in your environment or .env file:"
  echo "  export META_ACCESS_TOKEN=EAAxxxxxx"
  echo "  export META_AD_ACCOUNT_ID=act_1234567890"
  exit 1
fi

# Get URL from argument or use default
URL="${1:-https://www.zillow.com/homedetails/2640-Exposition-Blvd-Miami-FL-33133/20747378_zpid/}"
CAMPAIGN_TYPE="${2:-lead_generation}"
BUDGET="${3:-100}"

echo "🚀 Creating Facebook Ad Campaign"
echo "   URL: $URL"
echo "   Type: $CAMPAIGN_TYPE"
echo "   Budget: \$$BUDGET"
echo ""

# Step 1: Create campaign
echo "Step 1: Creating campaign..."
CAMPAIGN=$(curl -s -X POST "$BASE_URL/zuckerbot/campaigns/create" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{
    \"url\": \"$URL\",
    \"campaign_type\": \"$CAMPAIGN_TYPE\",
    \"budget\": $BUDGET,
    \"duration_days\": 7
  }")

# Check for errors
if echo "$CAMPAIGN" | grep -q "detail"; then
  echo "❌ Error creating campaign:"
  echo "$CAMPAIGN" | jq .
  exit 1
fi

CAMPAIGN_ID=$(echo "$CAMPAIGN" | jq -r '.id')
CAMPAIGN_NAME=$(echo "$CAMPAIGN" | jq -r '.business_name')

echo "✅ Campaign created: $CAMPAIGN_ID"
echo "   Name: $CAMPAIGN_NAME"
echo "   Variants: $(echo "$CAMPAIGN" | jq '.variants | length')"
echo ""

# Show campaign details
echo "Campaign Preview:"
echo "$CAMPAIGN" | jq '.variants[] | {headline, copy, cta}' | head -20
echo ""

# Step 2: Launch to Meta
echo "Step 2: Launching to Meta Ads Manager..."
echo "   Account: $META_AD_ACCOUNT_ID"
echo ""

LAUNCH=$(curl -s -X POST "$BASE_URL/zuckerbot/campaigns/launch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"meta_access_token\": \"$META_ACCESS_TOKEN\",
    \"ad_account_id\": \"$META_AD_ACCOUNT_ID\"
  }")

# Check for errors
if echo "$LAUNCH" | grep -q "detail"; then
  echo "❌ Error launching campaign:"
  echo "$LAUNCH" | jq .
  exit 1
fi

STATUS=$(echo "$LAUNCH" | jq -r '.status')
META_CAMPAIGN_ID=$(echo "$LAUNCH" | jq -r '.meta_campaign_id // empty')
META_URL=$(echo "$LAUNCH" | jq -r '.meta_url // empty')

echo "✅ Campaign launched!"
echo "   Status: $STATUS"
echo "   Meta Campaign ID: $META_CAMPAIGN_ID"
echo ""

if [ -n "$META_URL" ]; then
  echo "🔗 View in Meta Ads Manager:"
  echo "   $META_URL"
  echo ""
fi

echo "✨ Done! Your ad is now live on Facebook & Instagram"
