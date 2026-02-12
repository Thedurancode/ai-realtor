#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start supervisor (manages both FastAPI and MCP SSE)
echo "Starting services via supervisor..."
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
