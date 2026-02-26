#!/bin/bash
# Poll render job progress

API_KEY="${API_KEY:-your-api-key-here}"
BASE_URL="${BASE_URL:-http://localhost:8000}"

RENDER_ID="${1:?Usage: $0 <render_id>}"

echo "🎬 Polling render job: $RENDER_ID"
echo "Press Ctrl+C to stop"
echo ""

while true; do
  # Get progress
  RESPONSE=$(curl -s "$BASE_URL/v1/renders/$RENDER_ID/progress" \
    -H "X-API-Key: $API_KEY")

  # Parse response
  STATUS=$(echo "$RESPONSE" | jq -r '.status')
  PROGRESS=$(echo "$RESPONSE" | jq -r '.progress')
  FRAME=$(echo "$RESPONSE" | jq -r '.current_frame // "N/A"')
  TOTAL=$(echo "$RESPONSE" | jq -r '.total_frames // "N/A"')
  ETA=$(echo "$RESPONSE" | jq -r '.eta_seconds // "N/A"')

  # Calculate percentage
  PERCENT=$(python3 -c "print(f'{float($PROGRESS) * 100:.1f}%)")

  # Print progress bar
  BAR_LENGTH=40
  FILLED=$(( $(echo "$PROGRESS" | python3 -c "import sys; print(int(float(sys.stdin.read()) * $BAR_LENGTH))") ))
  EMPTY=$((BAR_LENGTH - FILLED))
  BAR="█$(printf '█%.0s' $(seq 1 $FILLED))$(printf ' %.0s' $(seq 1 $EMPTY))"

  echo -ne "\r[$BAR] $PERCENT | Status: $STATUS | Frame: $FRAME/$TOTAL | ETA: ${ETA}s"

  # Check if complete/failed/canceled
  if [ "$STATUS" = "completed" ]; then
    echo ""
    echo ""
    echo "✅ Render complete!"
    echo ""
    # Get full details
    curl -s "$BASE_URL/v1/renders/$RENDER_ID" \
      -H "X-API-Key: $API_KEY" | jq .
    break
  elif [ "$STATUS" = "failed" ]; then
    echo ""
    echo ""
    echo "❌ Render failed!"
    echo ""
    curl -s "$BASE_URL/v1/renders/$RENDER_ID" \
      -H "X-API-Key: $API_KEY" | jq '.error_message, .error_details'
    break
  elif [ "$STATUS" = "canceled" ]; then
    echo ""
    echo ""
    echo "⚠️  Render canceled"
    break
  fi

  # Wait before next poll
  sleep 1
done
