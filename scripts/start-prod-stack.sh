#!/bin/bash

# AI Realtor API + Nanobot Docker Stack Startup
# Complete production-ready deployment

set -e

echo "🏠 AI Realtor API + Nanobot - Docker Stack"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo ""
    if [ -f .env.example ]; then
        echo "Creating from .env.example..."
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file${NC}"
        echo ""
        echo "Please edit .env with your API keys:"
        echo "  nano .env"
        echo ""
        read -p "Press Enter after configuring .env file..."
    else
        echo -e "${RED}❌ Error: .env.example not found${NC}"
        echo ""
        echo "Creating minimal .env file..."
        cat > .env << 'EOF'
# Database
POSTGRES_USER=ai_realtor
POSTGRES_PASSWORD=password
POSTGRES_DB=ai_realtor

# API Port
API_PORT=8000

# API Keys (REQUIRED - add your keys!)
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_PLACES_API_KEY=your-key-here
ZILLOW_API_KEY=your-key-here

# Optional API Keys
SKIP_TRACE_API_KEY=
DOCUSEAL_API_KEY=
DOCUSEAL_WEBHOOK_SECRET=
VAPI_API_KEY=
ELEVENLABS_API_KEY=
EXA_API_KEY=
BRAVE_API_KEY=

# Application
APP_NAME=AI Realtor
APP_ENV=production
LOG_LEVEL=INFO

# Nanobot
NANOBOT_MODEL=anthropic/claude-opus-4-5
NANOBOT_TEMPERATURE=0.1
EXEC_TIMEOUT=60
EOF
        echo -e "${GREEN}✅ Created .env file${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env and add your API keys!${NC}"
        echo "  nano .env"
        echo ""
        read -p "Press Enter to continue (or Ctrl+C to stop)..."
    fi
fi

# Load environment variables
export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)

echo -e "${BLUE}📋 Configuration:${NC}"
echo "  API URL (internal): http://api:8000"
echo "  API URL (external): http://localhost:${API_PORT:-8000}"
echo "  Nanobot URL var:  http://api:8000"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"
if ! command_exists docker; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker and Docker Compose found${NC}"
echo ""

# Stop existing containers
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose-prod.yml down 2>/dev/null || true
echo -e "${GREEN}✅ Containers stopped${NC}"
echo ""

# Build images
echo -e "${BLUE}🔨 Building images (this may take a few minutes)...${NC}"
docker-compose -f docker-compose-prod.yml build
echo -e "${GREEN}✅ Images built${NC}"
echo ""

# Run migrations
echo -e "${BLUE}📊 Running database migrations...${NC}"
docker-compose -f docker-compose-prod.yml --profile migrations up migrations
echo -e "${GREEN}✅ Migrations complete${NC}"
echo ""

# Start the stack
echo -e "${BLUE}🚀 Starting stack...${NC}"
docker-compose -f docker-compose-prod.yml up -d
echo ""
echo -e "${GREEN}✅ Stack started${NC}"
echo ""

# Wait for services
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
echo ""

# Wait for database
echo -n "  Database: "
until docker exec ai-realtor-db pg_isready -U ${POSTGRES_USER:-ai_realtor} >/dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo -e "${GREEN}✅ Ready${NC}"

# Wait for API
echo -n "  API: "
until curl -s http://localhost:${API_PORT:-8000}/docs >/dev/null 2>&1; do
    echo -n "."
    sleep 3
done
echo -e "${GREEN}✅ Ready${NC}"

# Wait for nanobot
echo -n "  Nanobot: "
sleep 5
if docker ps | grep nanobot-ai-realtor >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Ready${NC}"
else
    echo -e "${YELLOW}⚠️  Check nanobot logs: docker logs nanobot-ai-realtor${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 Stack is ready!                                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Services:${NC}"
echo -e "  • AI Realtor API:  ${GREEN}http://localhost:${API_PORT:-8000}${NC}"
echo -e "  • API Docs:        ${GREEN}http://localhost:${API_PORT:-8000}/docs${NC}"
echo -e "  • Health Check:    ${GREEN}http://localhost:${API_PORT:-8000}/health${NC}"
echo ""
echo -e "${BLUE}🔧 Management:${NC}"
echo -e "  • View logs:       ${YELLOW}docker-compose -f docker-compose-prod.yml logs -f${NC}"
echo -e "  • API logs:        ${YELLOW}docker logs -f ai-realtor-api${NC}"
echo -e "  • Nanobot logs:    ${YELLOW}docker logs -f nanobot-ai-realtor${NC}"
echo -e "  • Stop stack:      ${YELLOW}docker-compose -f docker-compose-prod.yml down${NC}"
echo -e "  • Restart:         ${YELLOW}docker-compose -f docker-compose-prod.yml restart${NC}"
echo ""
echo -e "${BLUE}💡 Interact with Nanobot:${NC}"
echo -e "  ${YELLOW}docker exec -it nanobot-ai-realtor bash${NC}"
echo ""
echo -e "${BLUE}✨ Try these voice commands:${NC}"
echo -e "  ${YELLOW}\"Show me all properties\"${NC}"
echo -e "  ${YELLOW}\"Enrich property 5 with Zillow data\"${NC}"
echo -e "  ${YELLOW}\"How's my portfolio doing?\"${NC}"
echo -e "  ${YELLOW}\"What needs attention?\"${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Quick verification
echo -e "${BLUE}🔍 Quick verification:${NC}"
echo ""

# Check API
if curl -s http://localhost:${API_PORT:-8000}/docs >/dev/null 2>&1; then
    echo -e "  ${GREEN}✅ API is responding${NC}"
else
    echo -e "  ${RED}❌ API not responding${NC}"
fi

# Check nanobot env var
if docker exec nanobot-ai-realtor sh -c 'echo $AI_REALTOR_API_URL' 2>/dev/null | grep -q 'http://api:8000'; then
    echo -e "  ${GREEN}✅ Nanobot has correct API URL${NC}"
else
    echo -e "  ${YELLOW}⚠️  Check nanobot environment variable${NC}"
fi

echo ""
echo -e "${GREEN}Done! 🎉${NC}"
