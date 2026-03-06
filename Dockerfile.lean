# ---- Lean Production Image ----
# No Remotion, no Node.js, no Chromium — just Python + the API + MCP
# Image size: ~250MB vs ~1.5GB+ with Remotion stack

FROM python:3.11-slim AS base

WORKDIR /app

# Install only essential system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ---- Dependencies layer (cached) ----
FROM base AS deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Application layer ----
FROM deps AS app

# Copy application code
COPY app ./app
COPY mcp_server ./mcp_server
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts ./scripts
COPY static ./static
COPY start-lean.sh ./start.sh

# Create directories
RUN mkdir -p /app/tmp /app/log /app/uploads

# Make scripts executable + install CLI
RUN chmod +x start.sh scripts/* 2>/dev/null || true
RUN ln -sf /app/scripts/realtorclaw /usr/local/bin/realtorclaw

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TMPDIR=/app/tmp

# Ports: API + MCP SSE
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:8000/docs > /dev/null && \
        curl -sf http://localhost:8001/health > /dev/null || exit 1

CMD ["./start.sh"]
