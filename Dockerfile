FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (gcc + libpq-dev for psycopg2, supervisor for process management)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    supervisor \
    sqlite3 \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY mcp_server ./mcp_server
COPY scripts ./scripts
COPY alembic ./alembic
COPY alembic.ini .
COPY start.sh .
COPY .env.example .env

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN chmod +x start.sh

# Expose ports: 8000 for FastAPI, 8001 for MCP SSE
EXPOSE 8000 8001

# Run both services via supervisor
CMD ["./start.sh"]
