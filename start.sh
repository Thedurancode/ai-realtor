#!/bin/bash
set -e

echo "Starting RealtorClaw..."

# ── Database migrations ─────────────────────────────────────────────────
echo "Running database migrations..."
alembic upgrade head 2>/dev/null || {
    echo "Migration upgrade failed, stamping current state..."
    alembic stamp head 2>/dev/null || true
}
echo "Database ready"

# ── Remotion worker (only if WORKER_ENABLED and worker.py exists) ──────
if [ "$WORKER_ENABLED" = "1" ] && [ -f worker.py ]; then
    echo "Starting render worker..."
    python worker.py > /app/log/worker.log 2>&1 &
    echo "Worker started (PID: $!)"
fi

# ── MCP SSE server (port 8001) ─────────────────────────────────────────
if [ -d mcp_server ]; then
    echo "Starting MCP server on :8001..."
    python -m mcp_server.property_mcp --transport sse --port 8001 > /app/log/mcp.log 2>&1 &
    echo "MCP server started (PID: $!)"
fi

# ── API server (foreground) ────────────────────────────────────────────
echo "Starting API on :8000..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers ${API_WORKERS:-1} \
    --loop uvloop \
    --http httptools 2>/dev/null \
    || exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${API_WORKERS:-1}
