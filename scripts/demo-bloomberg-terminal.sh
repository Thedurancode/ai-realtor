#!/bin/bash

# Bloomberg Terminal Demo Script
# Shows off all features of the real-time terminal

API_URL="https://ai-realtor.fly.dev"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  BLOOMBERG TERMINAL DEMO"
echo "  AI Realtor Real-Time Property Management"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📺 Viewing at: http://localhost:3025"
echo ""
sleep 2

echo "🔵 Phase 1: API Activity Demonstration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Watch the LIVE API ACTIVITY panel (middle right)"
echo ""
sleep 2

echo "→ Fetching properties..."
curl -s "$API_URL/properties/" > /dev/null
sleep 1

echo "→ Fetching contracts..."
curl -s "$API_URL/contracts/" > /dev/null
sleep 1

echo "→ Fetching notifications..."
curl -s "$API_URL/notifications/" > /dev/null
sleep 1

echo "→ Checking agents..."
curl -s "$API_URL/agents/" > /dev/null
sleep 2

echo ""
echo "🟢 Phase 2: Creating New Property"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Watch for FULL-SCREEN animation + property appears in list"
echo ""
sleep 2

printf '%s\n' '{"title":"Upper West Side Condo","address":"88 Central Park West","city":"New York","state":"NY","zip_code":"10023","price":8900000,"bedrooms":3,"bathrooms":3,"square_feet":2600,"property_type":"condo","status":"available","agent_id":1,"description":"Luxury condo with Central Park views"}' | \
curl -s -X POST "$API_URL/properties/" -H "Content-Type: application/json" -d @- | jq -r '"✅ Created: \(.title) - \((.price / 1000000) | floor)M"'
sleep 4

echo ""
echo "🟡 Phase 3: Sending High-Priority Notification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Watch NOTIFICATIONS panel (top right)"
echo ""
sleep 2

printf '%s\n' '{"title":"URGENT: VIP Buyer","message":"Saudi royal family member interested in Central Park West properties - budget unlimited","type":"new_lead","priority":"high"}' | \
curl -s -X POST "$API_URL/notifications/" -H "Content-Type: application/json" -d @- | jq -r '"✅ Notification: \(.title)"'
sleep 4

echo ""
echo "⚡ Phase 4: Property Enrichment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Watch for enrichment animation"
echo ""
sleep 2

printf '%s\n' '{"property_ref":"1","session_id":"bloomberg-demo"}' | \
curl -s -X POST "$API_URL/context/enrich" -H "Content-Type: application/json" -d @- | jq -r '"✅ Enriched with Zestimate: $\((.data.zestimate / 1000000) | floor).\(((.data.zestimate % 1000000) / 100000) | floor)M"'
sleep 4

echo ""
echo "🔄 Phase 5: Rapid API Calls"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Watch activity feed fill up in real-time"
echo ""
sleep 2

for i in {1..10}; do
  curl -s "$API_URL/properties/" > /dev/null &
  curl -s "$API_URL/contracts/" > /dev/null &
  echo "   → Batch $i sent"
  sleep 0.5
done

wait
sleep 3

echo ""
echo "📊 Phase 6: Data Overview"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Fetch current stats
PROPS=$(curl -s "$API_URL/properties/" | jq 'length')
CONTRACTS=$(curl -s "$API_URL/contracts/" | jq 'length')
NOTIFS=$(curl -s "$API_URL/notifications/" | jq 'length')
TOTAL_VALUE=$(curl -s "$API_URL/properties/" | jq '[.[].price] | add')

echo "   📈 Properties: $PROPS"
echo "   📝 Contracts: $CONTRACTS"
echo "   🔔 Notifications: $NOTIFS"
echo "   💰 Total Portfolio: \$$(echo "scale=2; $TOTAL_VALUE / 1000000" | bc)M"
echo ""
sleep 2

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEMO COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 You should have seen:"
echo "   • 9 stat boxes at top updating in real-time"
echo "   • Property list on left with new listing"
echo "   • All 17 API endpoints in middle-left"
echo "   • Live API activity feed streaming calls"
echo "   • Notifications panel with priority colors"
echo "   • Contracts list at bottom-right"
echo "   • Bottom ticker scrolling properties"
echo "   • Full-screen animations for major events"
echo ""
echo "🔥 Bloomberg Terminal is LIVE and tracking everything!"
echo ""
