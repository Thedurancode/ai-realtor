#!/bin/bash
# Start both FastAPI and MCP SSE server

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start MCP SSE server in background (non-critical, API works without it)
python mcp_server/property_mcp.py --transport sse --port 8001 &

# Start FastAPI in foreground (primary service)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
