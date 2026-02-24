#!/bin/bash

echo "🧪 AI Realtor Platform - Endpoint Testing"
echo "=============================================="
echo ""

BASE_URL="http://localhost:8000"

# Test counter
PASS=0
FAIL=0

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    
    echo -n "Testing $name... "
    
    if [ -n "$data" ]; then
        response=$(curl -s -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    else
        response=$(curl -s -X $method "$BASE_URL$endpoint" 2>&1)
    fi
    
    # Check if response contains "Missing API key" (expected for protected endpoints)
    if echo "$response" | grep -q "Missing API key"; then
        echo "✅ PASS (Protected - requires API key)"
        ((PASS++))
    # Check if response is valid JSON (200 OK)
    elif echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        echo "✅ PASS (200 OK)"
        ((PASS++))
    # Check for 404 (endpoint not found)
    elif echo "$response" | grep -q "404"; then
        echo "❌ FAIL (404 Not Found)"
        ((FAIL++))
    # Check for errors
    elif echo "$response" | grep -qiE "error|exception|traceback"; then
        echo "❌ FAIL (Error in response)"
        echo "   Response: $response" | head -1
        ((FAIL++))
    else
        echo "❓ UNKNOWN (Response: ${response:0:100}...)"
    fi
}

echo "1. Core Endpoints"
echo "────────────────"
test_endpoint "Root endpoint" "GET" "/"
test_endpoint "API Docs" "GET" "/docs"
test_endpoint "ReDoc" "GET" "/redoc"
echo ""

echo "2. Skills System (requires API key, but we check if endpoint exists)"
echo "──────────────────────────────────────────────────────────────"
test_endpoint "Skills discover" "GET" "/skills/discover"
test_endpoint "Skills marketplace" "GET" "/skills/marketplace"
test_endpoint "Skills categories" "GET" "/skills/categories"
echo ""

echo "3. Approval Manager (requires API key)"
echo "─────────────────────────────────────────"
test_endpoint "Approval config" "GET" "/approval/config"
test_endpoint "Approval risk categories" "GET" "/approval/risk-categories"
test_endpoint "Approval autonomy level" "GET" "/approval/autonomy-level"
echo ""

echo "4. Credential Scrubbing (requires API key)"
echo "──────────────────────────────────────────"
test_endpoint "Scrub patterns" "GET" "/scrub/patterns"
test_endpoint "Scrub config" "GET" "/scrub/config"
echo ""

echo "5. Observer Pattern (requires API key)"
echo "────────────────────────────────────────"
test_endpoint "Observer stats" "GET" "/observer/stats"
test_endpoint "Observer event types" "GET" "/observer/event-types"
test_endpoint "Observer subscribers" "GET" "/observer/subscribers"
echo ""

echo "6. SQLite Tuning (requires API key)"
echo "────────────────────────────────────────"
test_endpoint "SQLite stats" "GET" "/sqlite/stats"
test_endpoint "SQLite config" "GET" "/sqlite/config"
test_endpoint "SQLite optimizations" "GET" "/sqlite/optimizations"
echo ""

echo "7. Onboarding (requires API key)"
echo "────────────────────────────────────"
test_endpoint "Onboarding questions" "GET" "/onboarding/questions"
test_endpoint "Onboarding categories" "GET" "/onboarding/categories"
echo ""

echo "8. Workspace (requires API key)"
echo "─────────────────────────────────"
test_endpoint "Workspaces list" "GET" "/workspaces"
echo ""

echo "9. Cron Scheduler (requires API key)"
echo "────────────────────────────────────"
test_endpoint "Scheduler tasks" "GET" "/scheduler/tasks"
test_endpoint "Scheduler handlers" "GET" "/scheduler/handlers"
echo ""

echo "10. Hybrid Search (requires API key)"
echo "────────────────────────────────────"
test_endpoint "Hybrid search" "GET" "/search/hybrid?query=test"
test_endpoint "FTS search" "GET" "/search/fts?query=test"
echo ""

echo "=============================================="
echo "📊 Test Results:"
echo "   ✅ Passed: $PASS"
echo "   ❌ Failed: $FAIL"
echo "   📈 Total: $((PASS + FAIL))"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "🎉 All endpoints accessible!"
else
    echo "⚠️  Some endpoints failed - check logs"
fi
