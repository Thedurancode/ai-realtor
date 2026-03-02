#!/bin/bash
# Test Script - New Features for AI Realtor Platform

echo "🚀 AI Realtor - New Features Test Script"
echo "=========================================="
echo ""

# Check server is running
echo "📡 Checking if API server is running..."
SERVER_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" 2>/dev/null)

if [ "$SERVER_CHECK" != "200" ]; then
    echo "❌ API server is not responding"
    echo ""
    echo "To start the server:"
    echo "  docker-compose -f docker-compose-local-nanobot.yml restart ai-realtor"
    echo ""
    exit 1
fi

echo "✅ API server is running"
echo ""

# Test existing watchlist endpoints
echo "🔍 Testing watchlist endpoints..."
echo ""

echo "1. List watchlists:"
curl -s "http://localhost:8000/watchlists/" -H "X-API-Key: nanobot-perm-key-2024" | python3 -m json.tool | head -20
echo ""

echo "2. Get scan status:"
curl -s "http://localhost:8000/watchlists/scan/status" -H "X-API-Key: nanobot-perm-key-2024" | python3 -m json.tool
echo ""

# Test existing voice assistant endpoints
echo "📞 Testing voice assistant endpoints..."
echo ""

echo "3. List phone numbers:"
curl -s "http://localhost:8000/voice-assistant/phone-numbers" -H "X-API-Key: nanobot-perm-key-2024" | python3 -m json.tool | head -20
echo ""

echo "4. Get call analytics:"
curl -s "http://localhost:8000/voice-assistant/phone-calls/analytics/overview" -H "X-API-Key: nanobot-perm-key-2024" | python3 -m json.tool
echo ""

# Test campaigns (if server is restarted)
echo "📧 Testing campaign endpoints..."
echo ""

echo "5. List campaign types:"
RESPONSE=$(curl -s "http://localhost:8000/campaigns/types" -H "X-API-Key: nanobot-perm-key-2024" 2>/dev/null)
if [ "$?" -eq 0 ] && [ "$RESPONSE" != "null" ]; then
    echo "$RESPONSE" | python3 -m json.tool
else
    echo "⚠️  Campaign endpoints not loaded yet (server needs restart)"
fi
echo ""

# Test document analysis (if server is restarted)
echo "📄 Testing document analysis endpoints..."
echo ""

echo "6. List document types:"
RESPONSE=$(curl -s "http://localhost:8000/documents/types" -H "X-API-Key: nanobot-perm-key-2024" 2>/dev/null)
if [ "$?" -eq 0 ] && [ "$RESPONSE" != "null" ]; then
    echo "$RESPONSE" | python3 -m json.tool
else
    echo "⚠️  Document analysis endpoints not loaded yet (server needs restart)"
fi
echo ""

echo "=========================================="
echo "✅ Test Complete!"
echo ""
echo "To see ALL new endpoints, restart the server:"
echo "  docker-compose -f docker-compose-local-nanobot.yml restart ai-realtor"
echo ""
echo "Then visit: http://localhost:8000/docs"
echo ""
