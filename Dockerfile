FROM python:3.11-slim

WORKDIR /app

# Install Node.js for Remotion
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install system dependencies for Chromium (Remotion rendering)
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    make \
    postgresql-client \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Remotion
COPY remotion ./remotion
RUN cd remotion && npm install

# Copy application code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts ./scripts
COPY worker.py .
COPY start.sh .

# Create directories
RUN mkdir -p /app/alembic/versions /app/tmp /app/log

# Make scripts executable
RUN chmod +x start.sh worker.py scripts/*.sh 2>/dev/null || true

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV REMOTION_RENDER=/app/remotion
ENV TMPDIR=/app/tmp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Run the startup script (API + Worker)
CMD ["./start.sh"]
