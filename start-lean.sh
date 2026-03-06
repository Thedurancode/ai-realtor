#!/bin/bash
set -e

echo "Starting AI Realtor (lean mode)..."

# Run migrations — stamp if fresh, upgrade if existing
echo "Running database migrations..."
alembic upgrade head || {
  echo "Migration upgrade failed, stamping current state..."
  alembic stamp head
}
echo "Database ready"

# Start MCP SSE server in background (port 8001)
echo "Starting MCP server on :8001..."
python -m mcp_server.property_mcp --transport sse --port 8001 > /app/log/mcp.log 2>&1 &
echo "MCP server started (PID: $!)"

# Start API (foreground)
echo "Starting API on :8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${API_WORKERS:-2} --loop uvloop --http httptools
