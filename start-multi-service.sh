#!/bin/bash
# =============================================================================
# AI REALTOR + NANOBOT - Multi-Service Quick Start
# =============================================================================
# This script sets up and runs both AI Realtor and Nanobot together
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
echo -e "${BLUE}║   🏠 AI REALTOR + 🐈 NANOBOT                           ║${NC}"
echo -e "${BLUE}║   Multi-Service Platform                                   ║${NC}"
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
    echo "Required keys:"
    echo "  - ANTHROPIC_API_KEY (for AI)"
    echo "  - GOOGLE_PLACES_API_KEY (for addresses)"
    echo "  - RAPIDAPI_KEY (for Zillow/Skip Trace)"
    echo ""
    echo "Chat platform (choose one):"
    echo "  - TELEGRAM_BOT_TOKEN (recommended)"
    echo "  - DISCORD_BOT_TOKEN"
    echo "  - SLACK_BOT_TOKEN + SLACK_APP_TOKEN"
    echo ""
    read -p "Press Enter to open .env file for editing..."
    ${EDITOR:-nano} .env
fi

# Pull Nanobot image
echo ""
echo -e "${BLUE}Pulling Nanobot image...${NC}"
docker pull ghcr.io/hkuds/nanobot:latest

# Build AI Realtor image
echo ""
echo -e "${BLUE}Building AI Realtor image...${NC}"
docker compose -f docker-compose-multi-service.yml build

# Start services
echo ""
echo -e "${BLUE}Starting services...${NC}"
docker compose -f docker-compose-multi-service.yml up -d

# Wait for services to be healthy
echo ""
echo -e "${BLUE}Waiting for services to start...${NC}"
sleep 10

# Check status
echo ""
docker compose -f docker-compose-multi-service.yml ps

# Show access information
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
echo -e "  AI Realtor Health:   ${GREEN}http://localhost:8000/health${NC}"
echo ""
echo -e "  Nanobot Gateway:     ${GREEN}http://localhost:18790${NC}"
echo ""
echo -e "${BLUE}📊 View Logs:${NC}"
echo "  docker compose -f docker-compose-multi-service.yml logs -f"
echo ""
echo -e "${BLUE}🛑 Stop Services:${NC}"
echo "  docker compose -f docker-compose-multi-service.yml down"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo "  1. Add your API keys to .env file"
echo "  2. Configure a chat platform (Telegram recommended)"
echo "  3. Restart: docker compose -f docker-compose-multi-service.yml restart"
echo ""
