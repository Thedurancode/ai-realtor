#!/bin/bash

# Demo script to showcase the TV display with dramatic full-screen animations
# Run this while viewing the TV display at http://localhost:3025

API_URL="https://ai-realtor.fly.dev"

echo "🎬 Starting TV Display Demo..."
echo "📺 Make sure you're viewing http://localhost:3025"
echo ""
sleep 2

echo "1️⃣  Creating a luxury property..."
printf '%s\n' '{"title":"Penthouse Paradise","address":"200 Central Park South","city":"New York","state":"NY","zip_code":"10019","price":12500000,"bedrooms":5,"bathrooms":5.5,"square_feet":4500,"property_type":"condo","status":"available","agent_id":1,"description":"Ultra-luxury penthouse with panoramic Central Park views"}' | \
curl -s -X POST "$API_URL/properties/" -H "Content-Type: application/json" -d @- | jq -r '"✓ Created: \(.title) - $\(.price | tonumber / 1000000)M"'
sleep 5

echo ""
echo "2️⃣  Sending high-priority notification..."
printf '%s\n' '{"title":"VIP Client Alert","message":"Billionaire client arriving from Dubai - interested in properties over 10M","type":"new_lead","priority":"high"}' | \
curl -s -X POST "$API_URL/notifications/" -H "Content-Type: application/json" -d @- | jq -r '"✓ Notification sent: \(.title)"'
sleep 5

echo ""
echo "3️⃣  Enriching property with Zillow data..."
printf '%s\n' '{"property_ref":"1","session_id":"demo"}' | \
curl -s -X POST "$API_URL/context/enrich" -H "Content-Type: application/json" -d @- | jq -r '"✓ Enrichment: \(.message)"'
sleep 5

echo ""
echo "4️⃣  Creating another property..."
printf '%s\n' '{"title":"Brooklyn Heights Brownstone","address":"75 Montague Street","city":"Brooklyn","state":"NY","zip_code":"11201","price":7500000,"bedrooms":4,"bathrooms":4,"square_feet":3800,"property_type":"house","status":"available","agent_id":1,"description":"Historic brownstone with original details and modern amenities"}' | \
curl -s -X POST "$API_URL/properties/" -H "Content-Type: application/json" -d @- | jq -r '"✓ Created: \(.title) - $\(.price | tonumber / 1000000)M"'
sleep 5

echo ""
echo "5️⃣  Sending contract signed notification..."
printf '%s\n' '{"title":"Contract Signed!","message":"Michael Chen signed purchase agreement for Tribeca Penthouse - 4.2M deal closed","type":"contract_signed","priority":"high","property_id":4}' | \
curl -s -X POST "$API_URL/notifications/" -H "Content-Type: application/json" -d @- | jq -r '"✓ Notification: \(.title)"'
sleep 5

echo ""
echo "✅ Demo complete!"
echo ""
echo "🎯 You should have seen:"
echo "   - Full-screen property creation animations"
echo "   - Dramatic notification displays"
echo "   - Enrichment progress indicators"
echo "   - Live activity feed updates"
echo "   - Connection status pulsing"
echo ""
echo "🔄 Run this script again to see more animations!"
