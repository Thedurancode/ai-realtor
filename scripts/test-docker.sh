#!/bin/bash

# Docker Testing Script for AI Realtor Platform
# Tests all new features and endpoints

echo "🐳 AI Realtor Platform - Docker Testing Script"
echo "==========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Build containers
echo "📦 Building Docker containers..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker build successful"
echo ""

# Start containers
echo "🚀 Starting containers..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start containers"
    exit 1
fi

echo "✅ Containers started"
echo ""

# Wait for app to be ready
echo "⏳ Waiting for app to start (10 seconds)..."
sleep 10

# Run database migrations
echo "📊 Running database migrations..."
docker-compose exec app alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Migration failed"
    docker-compose down
    exit 1
fi

echo "✅ Migrations completed"
echo ""

# Test endpoints
echo "🧪 Testing Endpoints"
echo "==================="
echo ""

# Base URL
BASE_URL="http://localhost:8000"

# Test 1: Health check
echo "1. Testing root endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/)
if [ "$response" = "200" ]; then
    echo "   ✅ Root endpoint: 200 OK"
else
    echo "   ❌ Root endpoint failed: $response"
fi
echo ""

# Test 2: API Documentation
echo "2. Testing API docs..."
response=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/docs)
if [ "$response" = "200" ]; then
    echo "   ✅ API docs: 200 OK"
else
    echo "   ❌ API docs failed: $response"
fi
echo ""

# Test 3: Approval Manager endpoints
echo "3. Testing Approval Manager..."
echo "   GET /approval/config"
response=$(curl -s $BASE_URL/approval/config | jq -r '.autonomy_level // "error"')
if [ "$response" != "error" ]; then
    echo "   ✅ Approval config: $response"
else
    echo "   ❌ Approval config failed"
fi

echo "   GET /approval/risk-categories"
response=$(curl -s $BASE_URL/approval/risk-categories | jq -r '.critical // "error"')
if [ "$response" != "error" ]; then
    echo "   ✅ Risk categories loaded"
else
    echo "   ❌ Risk categories failed"
fi
echo ""

# Test 4: Credential Scrubbing endpoints
echo "4. Testing Credential Scrubbing..."
echo "   POST /scrub/text"
response=$(curl -s -X POST $BASE_URL/scrub/test \
    -H "Content-Type: application/json" | jq -r '.passed // 0')
if [ "$response" != "0" ]; then
    echo "   ✅ Scrubbing test: $response tests passed"
else
    echo "   ❌ Scrubbing test failed"
fi
echo ""

# Test 5: Observer Pattern endpoints
echo "5. Testing Observer Pattern..."
echo "   GET /observer/stats"
response=$(curl -s $BASE_URL/observer/stats | jq -r '.enabled // "error"')
if [ "$response" != "error" ]; then
    echo "   ✅ Observer stats: enabled=$response"
else
    echo "   ❌ Observer stats failed"
fi

echo "   GET /observer/event-types"
response=$(curl -s $BASE_URL/observer/event-types | jq -r '.event_types // "error"')
if [ "$response" != "error" ]; then
    echo "   ✅ Event types loaded"
else
    echo "   ❌ Event types failed"
fi
echo ""

# Test 6: SQLite Tuning endpoints
echo "6. Testing SQLite Tuning..."
echo "   GET /sqlite/config"
response=$(curl -s $BASE_URL/sqlite/config | jq -r '.redaction_string // "error"')
if [ "$response" != "error" ]; then
    echo "   ✅ SQLite config: $response"
else
    echo "   ❌ SQLite config failed"
fi
echo ""

# Test 7: Skills System endpoints
echo "7. Testing Skills System..."
echo "   GET /skills/discover"
response=$(curl -s $BASE_URL/skills/discover | jq -r '.total_discovered // 0')
if [ "$response" -gt 0 ]; then
    echo "   ✅ Skills discovered: $response skills"
else
    echo "   ⚠️  No skills discovered (may need to sync)"
fi

echo "   POST /skills/sync"
response=$(curl -s -X POST $BASE_URL/skills/sync | jq -r '.status // "error"')
if [ "$response" = "synced" ]; then
    echo "   ✅ Skills synced"
else
    echo "   ❌ Skills sync failed: $response"
fi
echo ""

# Test 8: Onboarding endpoints
echo "8. Testing Onboarding System..."
echo "   GET /onboarding/questions"
response=$(curl -s $BASE_URL/onboarding/questions | jq -r 'length // "error"')
if [ "$response" -gt 0 ]; then
    echo "   ✅ Onboarding questions: $response questions"
else
    echo "   ❌ Onboarding questions failed"
fi

echo "   GET /onboarding/categories"
response=$(curl -s $BASE_URL/onboarding/categories | jq -r '.categories // "error"')
if [ "$response" != "error" ]; then
    echo "   ✅ Onboarding categories loaded"
else
    echo "   ❌ Onboarding categories failed"
fi
echo ""

# Test 9: Workspace endpoints
echo "9. Testing Workspace Isolation..."
echo "   GET /workspaces"
response=$(curl -s $BASE_URL/workspaces | jq -r '.total // "error"')
if [ "$response" != "error" ]; then
    echo "   ✅ Workspaces endpoint: $response workspaces"
else
    echo "   ❌ Workspaces failed"
fi
echo ""

# Test 10: Cron Scheduler endpoints
echo "10. Testing Cron Scheduler..."
echo "   GET /scheduler/tasks"
response=$(curl -s $BASE_URL/scheduler/tasks | jq -r '.total // "error"')
if [ "$response" != "error" ]; then
    echo "   ✅ Scheduled tasks: $response tasks"
else
    echo "   ❌ Scheduled tasks failed"
fi
echo ""

# Test 11: Hybrid Search endpoints
echo "11. Testing Hybrid Search..."
echo "   GET /search/hybrid?query=test"
response=$(curl -s "$BASE_URL/search/hybrid?query=test" | jq -r '.query // "error"')
if [ "$response" != "error" ]; then
    echo "   ✅ Hybrid search: query='$response'"
else
    echo "   ❌ Hybrid search failed"
fi
echo ""

# Summary
echo "==========================================="
echo "🎉 Testing Complete!"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs app"
echo ""
echo "🔍 View specific service logs:"
echo "   docker-compose logs app"
echo "   docker-compose logs postgres"
echo ""
echo "🛑 Stop all services:"
echo "   docker-compose down"
echo ""
echo "🧹 Clean up everything:"
echo "   docker-compose down -v"
echo ""
echo "📝 API Documentation:"
echo "   http://localhost:8000/docs"
echo "   http://localhost:8000/redoc"
echo ""
