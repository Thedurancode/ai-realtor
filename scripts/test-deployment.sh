#!/bin/bash

# Test AI Realtor + Nanobot Docker Deployment
# This script verifies the complete setup

set -e

echo "🧪 Testing AI Realtor + Nanobot Docker Deployment"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test function
test_component() {
    local name=$1
    local command=$2

    echo -n "Testing $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

echo -e "${BLUE}📋 Prerequisites Check${NC}"
echo "────────────────────────────"

# Check Docker
test_component "Docker installation" "docker --version"
test_component "Docker Compose installation" "docker-compose --version"
test_component "Docker daemon running" "docker ps"

echo ""
echo -e "${BLUE}🐳 Container Check${NC}"
echo "────────────────────────"

# Check if containers are running
if docker ps | grep -q ai-realtor; then
    echo -e "${GREEN}✅ AI Realtor containers detected${NC}"
    ((PASSED++))
    docker ps | grep ai-realtor
else
    echo -e "${YELLOW}⚠️  No AI Realtor containers running${NC}"
fi

echo ""
echo -e "${BLUE}🌐 API Connectivity Tests${NC}"
echo "────────────────────────────────"

# Test API endpoint
test_component "API is accessible (port 8000)" "curl -f -s http://localhost:8000/docs"

# Test specific endpoints
echo ""
echo "Testing specific endpoints:"

# Test properties endpoint
echo -n "  GET /properties/ ... "
if curl -s http://localhost:8000/properties/ | jq -e '.' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 200 OK${NC}"
    ((PASSED++))

    # Count properties
    COUNT=$(curl -s http://localhost:8000/properties/ | jq '. | length')
    echo "     Found $COUNT properties"
else
    echo -e "${RED}❌ Failed${NC}"
    ((FAILED++))
fi

# Test docs endpoint
test_component "  GET /docs (Swagger UI)" "curl -f -s http://localhost:8000/docs"

# Test health endpoint if it exists
echo -n "  Checking health endpoint... "
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check OK${NC}"
    ((PASSED++))
elif curl -s -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Using /docs as health check${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ No health endpoint${NC}"
    ((FAILED++))
fi

echo ""
echo -e "${BLUE}🏠 Skill File Check${NC}"
echo "─────────────────────────"

# Check skill file exists
SKILL_FILE="$HOME/.nanobot/workspace/skills/ai-realtor/SKILL.md"
if [ -f "$SKILL_FILE" ]; then
    echo -e "${GREEN}✅ Skill file exists${NC}"
    echo "   Location: $SKILL_FILE"
    ((PASSED++))

    # Check skill content
    echo -n "  Checking skill has URL handling instructions... "
    if grep -q "AI_REALTOR_API_URL" "$SKILL_FILE"; then
        echo -e "${GREEN}✅ Has env var instructions${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠️  No env var instructions${NC}"
    fi
else
    echo -e "${RED}❌ Skill file not found${NC}"
    echo "   Expected: $SKILL_FILE"
    ((FAILED++))
fi

echo ""
echo -e "${BLUE}🔧 Environment Variable Check${NC}"
echo "──────────────────────────────────"

# Check environment variable in running container
if docker ps | grep -q nanobot; then
    echo -n "Checking AI_REALTOR_API_URL in containers... "

    # Try nanobot-gateway first
    if docker ps | grep -q nanobot-gateway; then
        RESULT=$(docker exec nanobot-gateway printenv 2>/dev/null | grep AI_REALTOR_API_URL || echo "")
        if [ -n "$RESULT" ]; then
            echo -e "${GREEN}✅ Found${NC}"
            echo "   $RESULT"
            ((PASSED++))
        else
            echo -e "${YELLOW}⚠️  Not set in nanobot-gateway${NC}"
            ((PASSED++))
        fi
    fi

    # Try ai-realtor-sqlite
    if docker ps | grep -q ai-realtor-sqlite; then
        RESULT=$(docker exec ai-realtor-sqlite printenv 2>/dev/null | grep AI_REALTOR_API_URL || echo "")
        if [ -n "$RESULT" ]; then
            echo "   $RESULT"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  No nanobot container running${NC}"
fi

echo ""
echo -e "${BLUE}🧪 Functional Tests${NC}"
echo "────────────────────────"

# Test creating a property
echo -n "Testing property creation... "
RESPONSE=$(curl -s -X POST "http://localhost:8000/properties/" \
    -H "Content-Type: application/json" \
    -d '{"address":"123 Test St","city":"Miami","state":"FL","zip_code":"33101","price":"500000","property_type":"house","agent_id":1}')

if echo "$RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
    PROPERTY_ID=$(echo "$RESPONSE" | jq -r '.id')
    echo -e "${GREEN}✅ Property created (ID: $PROPERTY_ID)${NC}"
    ((PASSED++))

    # Test getting the property
    echo -n "Testing GET /properties/$PROPERTY_ID ... "
    if curl -s "http://localhost:8000/properties/$PROPERTY_ID" | jq -e '.id' > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Property retrieved${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ Failed to retrieve${NC}"
        ((FAILED++))
    fi

    # Cleanup
    echo -n "Cleaning up test property... "
    if curl -s -X DELETE "http://localhost:8000/properties/$PROPERTY_ID" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Deleted${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not delete (manual cleanup may be needed)${NC}"
    fi
else
    echo -e "${RED}❌ Failed to create property${NC}"
    echo "   Response: $RESPONSE"
    ((FAILED++))
fi

echo ""
echo -e "${BLUE}📊 Summary${NC}"
echo "───────────"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Some tests failed. Check the logs above for details.${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed! ✅${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. View API docs: http://localhost:8000/docs"
    echo "  2. Try voice commands in nanobot"
    echo "  3. Check logs: docker logs -f nanobot-gateway"
    exit 0
fi
