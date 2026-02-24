#!/bin/bash

# Quick Start Script - AI Realtor Docker Setup
# This script sets up everything you need to run the AI Realtor API with Docker

set -e

echo "=== AI Realtor Docker Quick Start ==="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker is installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - GOOGLE_PLACES_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - Other API keys (optional)"
    echo ""
    read -p "Press Enter after you've updated .env (or press Ctrl+C to do it later)..."
fi

echo "🐳 Starting Docker containers..."
echo ""

# Start Docker Compose
docker-compose up -d

echo ""
echo "⏳ Waiting for containers to be ready..."
sleep 5

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Containers are running!"
    echo ""
    echo "=== Service URLs ==="
    echo "🌐 API:          http://localhost:8000"
    echo "📚 Docs:         http://localhost:8000/docs"
    echo "🔌 MCP SSE:      http://localhost:8001"
    echo "🗄️  Database:    localhost:5433"
    echo ""
    echo "=== Quick Commands ==="
    echo "View logs:        docker-compose logs -f"
    echo "Stop all:         docker-compose down"
    echo "Restart app:      docker-compose restart app"
    echo "Run migrations:   docker-compose exec app alembic upgrade head"
    echo "Access database:  docker-compose exec postgres psql -U postgres -d ai_realtor"
    echo ""

    # Test the API
    echo "🧪 Testing API..."
    if curl -s http://localhost:8000/ > /dev/null; then
        echo "✅ API is responding!"
        echo ""
        echo "🎉 Setup complete! Your AI Realtor API is running."
        echo ""
        echo "Next steps:"
        echo "1. Register an agent: curl -X POST http://localhost:8000/agents/register -H 'Content-Type: application/json' -d '{\"name\":\"Your Name\",\"email\":\"you@example.com\",\"password\":\"password\"}'"
        echo "2. Open docs: http://localhost:8000/docs"
        echo "3. View logs: docker-compose logs -f"
    else
        echo "⚠️  API is not responding yet. Check logs:"
        echo "   docker-compose logs app"
    fi
else
    echo ""
    echo "❌ Failed to start containers. Check logs:"
    echo "   docker-compose logs"
    exit 1
fi

echo ""
echo "=== Done ==="
