#!/bin/bash
set -e

echo "🚀 Starting AI Realtor with Remotion Rendering..."
echo ""

# Run migrations
echo "📊 Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete"
echo ""

# Start Redis (if not using external Redis)
if [ -n "$REDIS_ENABLED" ]; then
  echo "🔴 Starting Redis..."
  redis-server --daemonize yes --port 6379
  echo "✅ Redis started"
fi

# Start the render worker in background
if [ -n "$WORKER_ENABLED" ] || [ "$WORKER_ENABLED" = "1" ]; then
  echo "🎬 Starting render worker..."
  python worker.py > /app/log/worker.log 2>&1 &
  WORKER_PID=$!
  echo "✅ Worker started (PID: $WORKER_PID)"
  echo ""
fi

# Start MCP SSE server in background (port 8001)
echo "🔧 Starting MCP SSE server on port 8001..."
python -m mcp_server.property_mcp --transport sse --port 8001 > /app/log/mcp.log 2>&1 &
MCP_PID=$!
echo "✅ MCP server started (PID: $MCP_PID)"
echo ""

# Start the API server
echo "🌐 Starting API server..."
echo ""

# Start API (foreground)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
