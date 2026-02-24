#!/bin/bash

# =============================================================================
# NANOBOT SETUP SCRIPT
# =============================================================================
# Automatically configures Nanobot gateway to work with AI Realtor
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== AI Realtor - Nanobot Setup Script ===${NC}"
echo ""

# =============================================================================
# CHECK DOCKER
# =============================================================================

echo -e "${YELLOW}Checking Docker status...${NC}"

if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# =============================================================================
# CHECK CONTAINERS
# =============================================================================

echo -e "${YELLOW}Checking AI Realtor containers...${NC}"

AI_REALTOR_RUNNING=$(docker ps --filter "name=ai-realtor-sqlite" --format "{{.Status}}" | grep -c "Up" || true)
NANOBOT_RUNNING=$(docker ps --filter "name=nanobot-gateway" --format "{{.Status}}" | grep -c "Up" || true)

if [ "$AI_REALTOR_RUNNING" -eq 0 ]; then
    echo -e "${RED}✗ AI Realtor container not running${NC}"
    echo "Starting containers..."
    cd /Users/edduran/Documents/GitHub/ai-realtor
    docker-compose -f docker-compose-local-nanobot.yml up -d
    sleep 10
fi

if [ "$NANOBOT_RUNNING" -eq 0 ]; then
    echo -e "${RED}✗ Nanobot container not running${NC}"
    echo "Starting containers..."
    cd /Users/edduran/Documents/GitHub/ai-realtor
    docker-compose -f docker-compose-local-nanobot.yml up -d
    sleep 10
fi

echo -e "${GREEN}✓ Containers are running${NC}"
echo ""

# =============================================================================
# CREATE NANOBOT CONFIG
# =============================================================================

echo -e "${YELLOW}Creating Nanobot configuration...${NC}"

docker exec nanobot-gateway bash -c "
cat > /root/.nanobot/config.json << 'EOF'
{
  \"agents\": {
    \"defaults\": {
      \"model\": \"glm-4.7\",
      \"provider\": \"openai\"
    }
  },
  \"providers\": {
    \"openai\": {
      \"api_key\": \"\${ZHIPU_API_KEY}\",
      \"api_base\": \"https://open.bigmodel.cn/api/paas/v4\"
    }
  },
  \"skills\": {
    \"ai-realtor\": {
      \"type\": \"api\",
      \"endpoint\": \"http://ai-realtor-sqlite:8000\",
      \"description\": \"AI Realtor Platform - Property Management\"
    }
  }
}
EOF
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Configuration file created${NC}"
else
    echo -e "${RED}✗ Failed to create configuration${NC}"
    exit 1
fi

echo ""

# =============================================================================
# VERIFY CONFIG
# =============================================================================

echo -e "${YELLOW}Verifying configuration...${NC}"

CONFIG_CHECK=$(docker exec nanobot-gateway cat /root/.nanobot/config.json 2>/dev/null | grep -c "ai-realtor" || true)

if [ "$CONFIG_CHECK" -gt 0 ]; then
    echo -e "${GREEN}✓ AI Realtor skill configured${NC}"
else
    echo -e "${RED}✗ Configuration verification failed${NC}"
    exit 1
fi

echo ""

# =============================================================================
# RESTART NANOBOT
# =============================================================================

echo -e "${YELLOW}Restarting Nanobot to load configuration...${NC}"

docker restart nanobot-gateway > /dev/null 2>&1

sleep 5

NANOBOT_HEALTH=$(docker ps --filter "name=nanobot-gateway" --format "{{.Status}}" | grep -c "Up" || true)

if [ "$NANOBOT_HEALTH" -gt 0 ]; then
    echo -e "${GREEN}✓ Nanobot restarted successfully${NC}"
else
    echo -e "${RED}✗ Nanobot failed to restart${NC}"
    exit 1
fi

echo ""

# =============================================================================
# CHECK ENVIRONMENT VARIABLES
# =============================================================================

echo -e "${YELLOW}Checking environment variables...${NC}"

ZHIPU_KEY=$(docker exec nanobot-gateway printenv ZHIPU_API_KEY 2>/dev/null || echo "")
TELEGRAM_TOKEN=$(docker exec nanobot-gateway printenv TELEGRAM_BOT_TOKEN 2>/dev/null || echo "")

if [ -n "$ZHIPU_KEY" ]; then
    echo -e "${GREEN}✓ ZHIPU_API_KEY is set${NC}"
else
    echo -e "${RED}✗ ZHIPU_API_KEY is missing${NC}"
    echo "  Add ZHIPU_API_KEY to docker-compose-local-nanobot.yml"
fi

if [ -n "$TELEGRAM_TOKEN" ]; then
    echo -e "${GREEN}✓ TELEGRAM_BOT_TOKEN is set${NC}"

    # Extract bot username from token
    BOT_INFO=$(curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe" | python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('username', 'Unknown'))" 2>/dev/null || echo "Unknown")
    echo "  Bot username: @${BOT_INFO}"
else
    echo -e "${YELLOW}⚠ TELEGRAM_BOT_TOKEN is missing${NC}"
    echo "  Add TELEGRAM_BOT_TOKEN to docker-compose-local-nanobot.yml"
    echo "  Get your token from @BotFather on Telegram"
fi

echo ""

# =============================================================================
# TEST CONNECTIONS
# =============================================================================

echo -e "${YELLOW}Testing connections...${NC}"

# Test AI Realtor health
AI_HEALTH=$(curl -s http://localhost:8000/health | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null || echo "error")

if [ "$AI_HEALTH" == "healthy" ]; then
    echo -e "${GREEN}✓ AI Realtor API is healthy${NC}"
else
    echo -e "${RED}✗ AI Realtor API health check failed${NC}"
fi

# Test Nanobot (may not have health endpoint, so just check if container is up)
NANOBOT_STATUS=$(docker ps --filter "name=nanobot-gateway" --format "{{.Status}}" | head -1)
if [[ $NANOBOT_STATUS == *"Up"* ]]; then
    echo -e "${GREEN}✓ Nanobot gateway is running${NC}"
else
    echo -e "${RED}✗ Nanobot gateway is not running${NC}"
fi

echo ""

# =============================================================================
# SUMMARY
# =============================================================================

echo -e "${BLUE}=== Setup Complete ===${NC}"
echo ""
echo "Nanobot is now configured and ready to use!"
echo ""
echo "Next steps:"
echo "  1. Test your Telegram bot:"
echo "     • Open Telegram"
echo "     • Search for your bot"
echo "     • Send: Show me all properties"
echo ""
echo "  2. Check Nanobot logs:"
echo "     docker logs nanobot-gateway --tail 50 -f"
echo ""
echo "  3. View Nanobot config:"
echo "     docker exec nanobot-gateway cat /root/.nanobot/config.json"
echo ""
echo "Available commands (via Telegram):"
echo "  • Show me all properties"
echo "  • Create a property at 123 Main St"
echo "  • Enrich property 1"
echo "  • How's my portfolio?"
echo "  • What needs attention?"
echo ""
echo -e "${GREEN}✓ Nanobot setup complete!${NC}"
echo ""
