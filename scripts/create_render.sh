#!/bin/bash
# Create a render job via the API

API_KEY="${API_KEY:-your-api-key-here}"
BASE_URL="${BASE_URL:-http://localhost:8000}"

# Read input props from file or stdin
PROPS_FILE="${1:-input_props.json}"

if [ ! -f "$PROPS_FILE" ]; then
  echo "Error: Props file not found: $PROPS_FILE"
  echo "Usage: $0 <input_props.json> [template_id] [composition_id] [webhook_url]"
  exit 1
fi

TEMPLATE_ID="${2:-captioned-reel}"
COMPOSITION_ID="${3:-CaptionedReel}"
WEBHOOK_URL="${4:-}"

# Make API request
curl -X POST "$BASE_URL/v1/renders" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{
    \"template_id\": \"$TEMPLATE_ID\",
    \"composition_id\": \"$COMPOSITION_ID\",
    \"input_props\": $(cat "$PROPS_FILE"),
    \"webhook_url\": \"$WEBHOOK_URL\"
  }" | jq .

echo ""
echo "✅ Render job created!"
echo ""
echo "Check status:"
echo "  ./scripts/poll_render.sh <render_id>"
