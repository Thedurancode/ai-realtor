#!/bin/bash

# AI Realtor + Nanobot Docker Stack Startup Script
# This script ensures proper startup sequence

set -e

echo "🏠 AI Realtor + Nanobot Docker Stack"
echo "===================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it with your API keys:"
        echo "   nano .env"
        echo ""
        read -p "Press Enter after configuring .env file..."
    else
        echo "❌ Error: .env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo "📋 Configuration:"
echo "  API URL will be: http://ai-realtor-api:8000 (internal)"
echo "  Nanobot will connect to: AI_REALTOR_API_URL=http://ai-realtor-api:8000"
echo ""

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose-ai-realtor.yml down 2>/dev/null || true

# Build images if needed
echo "🔨 Building images..."
docker-compose -f docker-compose-ai-realtor.yml build

# Start the stack
echo "🚀 Starting stack..."
echo ""
echo "Startup sequence:"
echo "  1️⃣  PostgreSQL database starts"
echo "  2️⃣  AI Realtor API starts (waits for DB)"
echo "  3️⃣  Nanobot starts (waits for API to be healthy)"
echo ""

docker-compose -f docker-compose-ai-realtor.yml up -d

echo ""
echo "⏳ Waiting for services to be ready..."
echo ""

# Wait for database
echo "Waiting for database..."
until docker exec ai-realtor-db pg_isready -U user > /dev/null 2>&1; do
    echo "  ⏳ Database starting..."
    sleep 2
done
echo "  ✅ Database ready"

# Wait for API
echo "Waiting for AI Realtor API..."
until curl -s http://localhost:8000/docs > /dev/null 2>&1; do
    echo "  ⏳ API starting..."
    sleep 3
done
echo "  ✅ API ready"

# Wait for nanobot to be ready
echo "Waiting for Nanobot..."
sleep 5
if docker ps | grep nanobot-ai-realtor > /dev/null; then
    echo "  ✅ Nanobot ready"
else
    echo "  ⚠️  Check nanobot logs: docker logs nanobot-ai-realtor"
fi

echo ""
echo "🎉 Stack is ready!"
echo ""
echo "─────────────────────────────────────────────────────────────"
echo "📊 Services:"
echo "  • AI Realtor API:  http://localhost:8000"
echo "  • API Docs:        http://localhost:8000/docs"
echo "  • Nanobot logs:    docker logs -f nanobot-ai-realtor"
echo ""
echo "🔧 Management:"
echo "  • View logs:       docker-compose -f docker-compose-ai-realtor.yml logs -f"
echo "  • Stop stack:      docker-compose -f docker-compose-ai-realtor.yml down"
echo "  • Restart:         docker-compose -f docker-compose-ai-realtor.yml restart"
echo ""
echo "💡 To interact with nanobot:"
echo "  docker exec -it nanobot-ai-realtor bash"
echo "─────────────────────────────────────────────────────────────"
echo ""
echo "✨ Try: \"Show me all properties\""
echo ""
