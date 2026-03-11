# =============================================================================
# RealtorClaw — Unified Multi-Stage Dockerfile
# =============================================================================
# Build targets:
#   docker build --target lean  -t realtorclaw:lean .    (~250MB, no Remotion)
#   docker build --target full  -t realtorclaw:full .    (~1.5GB, with Remotion)
#   docker build --target worker -t realtorclaw:worker . (Remotion render worker)
#
# Default (no --target): builds "full"
# =============================================================================

# ── Stage 1: Base ────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TMPDIR=/app/tmp

# ── Stage 2: Lean (API + MCP only, no Remotion/Node/Chromium) ───────────────
FROM base AS lean

COPY app ./app
COPY mcp_server ./mcp_server
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts ./scripts
COPY static ./static
COPY start.sh .

RUN mkdir -p /app/tmp /app/log /app/uploads /app/data

RUN chmod +x start.sh scripts/* 2>/dev/null || true
RUN ln -sf /app/scripts/realtorclaw /usr/local/bin/realtorclaw 2>/dev/null || true

EXPOSE 8000 8001

HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:8000/docs > /dev/null || exit 1

CMD ["./start.sh"]

# ── Stage 3: Full (Lean + Node.js + Remotion + Chromium) ────────────────────
FROM lean AS full

# Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Chromium system deps for Remotion rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make \
    libnss3 libnspr4 \
    libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpangocairo-1.0-0 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Install Remotion
COPY remotion ./remotion
RUN cd remotion && npm install

COPY worker.py .

ENV REMOTION_RENDER=/app/remotion

# ── Stage 4: Worker (Remotion render worker only, no API) ───────────────────
FROM full AS worker

CMD ["python", "worker.py"]
