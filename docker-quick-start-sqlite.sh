#!/bin/bash
# =============================================================================
# AI Realtor - Quick Start Script (SQLite Docker)
# =============================================================================
# One-command setup to get AI Realtor running with SQLite and Docker
# Usage: ./docker-quick-start-sqlite.sh
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
echo -e "${BLUE}║   🏠 AI REALTOR - Docker Quick Start (SQLite)             ║${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "Please install Docker first:"
    echo "  - Mac: https://docs.docker.com/desktop/install/mac-install/"
    echo "  - Linux: curl -fsSL https://get.docker.com | sh"
    echo "  - Windows: https://docs.docker.com/desktop/install/windows-install/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker detected${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ No .env file found${NC}"
    echo "Creating .env from template..."

    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo ""
        echo -e "${YELLOW}⚠ IMPORTANT: Edit .env and add your API keys!${NC}"
        echo "Required keys for full functionality:"
        echo "  - GOOGLE_PLACES_API_KEY"
        echo "  - RAPIDAPI_KEY (for Zillow and Skip Trace)"
        echo "  - ANTHROPIC_API_KEY (for AI features)"
        echo ""
        read -p "Press Enter to continue (or Ctrl+C to stop and add API keys)..."
    else
        echo -e "${RED}❌ .env.example not found!${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Building Docker image...${NC}"

# Build the image
if docker compose -f docker-compose.sqlite.yml build; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build Docker image${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Starting containers...${NC}"

# Start the containers
if docker compose -f docker-compose.sqlite.yml up -d; then
    echo -e "${GREEN}✓ Containers started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start containers${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║   🎉 AI REALTOR IS NOW RUNNING!                           ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📱 Access the application:${NC}"
echo -e "   • API Documentation: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "   • API Root:         ${GREEN}http://localhost:8000${NC}"
echo -e "   • MCP Server:       ${GREEN}http://localhost:8001${NC}"
echo ""
echo -e "${BLUE}📊 Useful commands:${NC}"
echo -e "   • View logs:    ${YELLOW}docker compose -f docker-compose.sqlite.yml logs -f${NC}"
echo -e "   • Stop app:     ${YELLOW}docker compose -f docker-compose.sqlite.yml down${NC}"
echo -e "   • Restart app:  ${YELLOW}docker compose -f docker-compose.sqlite.yml restart${NC}"
echo -e "   • Shell access: ${YELLOW}docker exec -it ai-realtor-sqlite bash${NC}"
echo ""
echo -e "${BLUE}💾 Database location:${NC}"
echo -e "   • Docker volume: ${YELLOW}ai_realtor_sqlite_data${NC}"
echo -e "   • Inside container: ${YELLOW}/app/data/ai_realtor.db${NC}"
echo ""
echo -e "${BLUE}🔍 Check status:${NC}"
echo -e "   • ${YELLOW}docker compose -f docker-compose.sqlite.yml ps${NC}"
echo ""

# Show logs
echo -e "${BLUE}📋 Showing recent logs...${NC}"
echo ""
docker compose -f docker-compose.sqlite.yml logs --tail=20

echo ""
echo -e "${GREEN}✨ Ready to use! Try opening http://localhost:8000/docs in your browser${NC}"
