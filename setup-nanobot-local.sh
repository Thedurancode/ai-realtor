#!/bin/bash
# =============================================================================
# AI REALTOR + NANOBOT - Setup and Start (Local Build)
# =============================================================================
# This script clones Nanobot and builds it locally, then starts both services
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}║   🏠 AI REALTOR + 🐈 NANOBOT (Local Build)              ║${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Clone Nanobot if it doesn't exist
if [ ! -d "nanobot" ]; then
    echo -e "${BLUE}Cloning Nanobot repository...${NC}"
    git clone https://github.com/HKUDS/nanobot.git
    echo -e "${GREEN}✓ Nanobot cloned${NC}"
else
    echo -e "${YELLOW}⚠ Nanobot directory already exists${NC}"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ No .env file found${NC}"
    echo "Creating from template..."

    if [ -f .env.multi-service.example ]; then
        cp .env.multi-service.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
    else
        echo -e "${RED}❌ Template file not found!${NC}"
        exit 1
    fi

    echo ""
    echo -e "${YELLOW}⚠ IMPORTANT: Edit .env and add your API keys!${NC}"
    echo ""
    echo "Minimum required:"
    echo "  - ANTHROPIC_API_KEY (for AI)"
    echo ""
    echo "Chat platform (choose one):"
    echo "  - TELEGRAM_BOT_TOKEN (recommended - easiest)"
    echo ""
    read -p "Press Enter to continue (or Ctrl+C to add keys first)..."
fi

# Build and start services
echo ""
echo -e "${BLUE}Building and starting services...${NC}"
docker compose -f docker-compose-local-nanobot.yml up -d --build

# Wait for services to start
echo ""
echo -e "${BLUE}Waiting for services to start...${NC}"
sleep 15

# Check status
echo ""
docker compose -f docker-compose-local-nanobot.yml ps

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║   🎉 Platform is Running!                                  ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📱 Access Points:${NC}"
echo ""
echo -e "  AI Realtor API:       ${GREEN}http://localhost:8000${NC}"
echo -e "  AI Realtor Docs:     ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  Nanobot Gateway:     ${GREEN}http://localhost:18790${NC}"
echo ""
echo -e "${BLUE}📊 Next Steps:${NC}"
echo "  1. Add API keys to .env file (ANTHROPIC_API_KEY is required)"
echo "  2. Configure a chat platform:"
echo "     - Telegram: Get token from @BotFather"
echo "     - Discord: Create app at discord.com/developers/applications"
echo "  3. Restart: docker compose -f docker-compose-local-nanobot.yml restart"
echo ""
echo -e "${BLUE}📝 View Logs:${NC}"
echo "  docker compose -f docker-compose-local-nanobot.yml logs -f"
echo ""
echo -e "${BLUE}🛑 Stop Services:${NC}"
echo "  docker compose -f docker-compose-local-nanobot.yml down"
echo ""
