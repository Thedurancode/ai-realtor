#!/bin/bash
# Easy Docker startup script for AI Realtor
# Usage: ./scripts/start-docker.sh

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🐳 AI Realtor Docker Startup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if .env.docker exists
if [ ! -f .env.docker ]; then
    echo -e "${YELLOW}⚠️  .env.docker not found!${NC}"
    echo -e "${YELLOW}Creating .env.docker from example...${NC}"
    echo ""
    cp .env.docker.example .env.docker 2>/dev/null || true
    if [ -f .env.docker.example ]; then
        echo -e "${YELLOW}✓ Created .env.docker${NC}"
    else
        echo -e "${RED}✗ No .env.docker.example found${NC}"
        exit 1
    fi
fi

# Check required environment variables
echo -e "${YELLOW}Checking required variables...${NC}"

if ! grep -q "^ANTHROPIC_API_KEY=sk-" .env.docker; then
    echo -e "${RED}✗ ANTHROPIC_API_KEY not configured${NC}"
    echo -e "${YELLOW}→ Add your Anthropic API key to .env.docker${NC}"
    echo ""
    echo -e "${YELLOW}Get your key at: https://console.anthropic.com/${NC}"
    exit 1
fi

if ! grep -q "^GOOGLE_PLACES_API_KEY=AIz" .env.docker; then
    echo -e "${RED}✗ GOOGLE_PLACES_API_KEY not configured${NC}"
    echo -e "${YELLOW}→ Add your Google Places API key to .env.docker${NC}"
    echo ""
    echo -e "${YELLOW}Get your key at: https://console.cloud.google.com/${NC}"
    exit 1
fi

if ! grep -q "^RAPIDAPI_KEY=" .env.docker; then
    echo -e "${RED}✗ RAPIDAPI_KEY not configured${NC}"
    echo -e "${YELLOW}→ Add your RapidAPI key to .env.docker${NC}"
    echo ""
    echo -e "${YELLOW}Get your key at: https://rapidapi.com/hub/${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Required variables configured!${NC}"
echo ""

# Check optional variables
echo -e "${YELLOW}Optional variables (can run without these):${NC}"

if ! grep -q "^TELEGRAM_BOT_TOKEN=" .env.docker; then
    echo -e "${YELLOW}⚠️  TELEGRAM_BOT_TOKEN not configured${NC}"
    echo -e "${YELLOW}→ Add for Telegram bot integration${NC}"
else
    echo -e "${GREEN}✓ TELEGRAM_BOT_TOKEN configured${NC}"
fi

if ! grep -q "^ELEVENLABS_API_KEY=" .env.docker; then
    echo -e "${YELLOW}⚠️  ELEVENLABS_API_KEY not configured${NC}"
else
    echo -e "${GREEN}✓ ELEVENLABS_API_KEY configured${NC}"
fi

echo ""
echo -e "${YELLOW}Starting Docker containers...${NC}"

# Build and start
docker compose up -d --build

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Docker containers started!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo "  docker compose logs -f"
echo ""
echo -e "${YELLOW}Stop containers:${NC}"
echo "  docker compose down"
echo ""
echo -e "${YELLOW}Rebuild containers:${NC}"
echo "  docker compose up -d --build --force-recreate"
echo ""
