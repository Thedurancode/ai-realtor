#!/bin/bash
# Daytona workspace auto-start — runs after container creation
set -e

echo "========================================="
echo "  RealtorClaw AI Platform — Daytona Init"
echo "========================================="

# 1. Create .env from example if not present
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from template — configure your API keys via /setup endpoint"
fi

# 2. Run database migrations
echo "Running database migrations..."
alembic upgrade head 2>/dev/null || echo "Migrations skipped (first run will auto-create tables)"

# 3. Start MCP SSE server in background
echo "Starting MCP server on port 8001..."
python -m mcp_server.property_mcp --transport sse --port 8001 > /tmp/mcp.log 2>&1 &
echo "MCP server started (PID: $!)"

# 4. Start API server
echo ""
echo "Starting API server on port 8000..."
echo "Setup wizard: http://localhost:8000/setup/status"
echo "API docs:     http://localhost:8000/docs"
echo "========================================="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
