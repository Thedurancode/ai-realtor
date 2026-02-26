#!/bin/bash
# Cancel a render job

API_KEY="${API_KEY:-your-api-key-here}"
BASE_URL="${BASE_URL:-http://localhost:8000}"

RENDER_ID="${1:?Usage: $0 <render_id>}"

echo "⚠️  Canceling render job: $RENDER_ID"
echo ""

RESPONSE=$(curl -s -X POST "$BASE_URL/v1/renders/$RENDER_ID/cancel" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY")

echo "$RESPONSE" | jq .

echo ""
STATUS=$(echo "$RESPONSE" | jq -r '.status')
if [ "$STATUS" = "canceled" ]; then
  echo "✅ Render job canceled successfully"
else
  echo "⚠️  Render job status: $STATUS"
fi
