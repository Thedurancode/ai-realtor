#!/bin/bash
# ============================================
# RealtorClaw — AWS Lightsail One-Command Setup
# ============================================
# Run on a fresh Lightsail Ubuntu 22.04 instance:
#   curl -sSL https://raw.githubusercontent.com/Thedurancode/ai-realtor/main/lightsail-setup.sh | bash
#
# Minimum specs: 2GB RAM / 1 vCPU ($10/mo Lightsail plan)
# Recommended:   4GB RAM / 2 vCPU ($20/mo plan)

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
info() { echo -e "${CYAN}[i]${NC} $1"; }
err()  { echo -e "${RED}[!]${NC} $1"; exit 1; }

INSTALL_DIR="/opt/realtorclaw"

# ---- Pre-flight ----
[[ $EUID -ne 0 ]] && err "Run as root: sudo bash lightsail-setup.sh"

log "Starting RealtorClaw setup on Lightsail..."

# ---- System updates ----
log "Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# ---- Install Docker ----
if ! command -v docker &>/dev/null; then
    log "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
    log "Docker installed"
else
    info "Docker already installed"
fi

# ---- Install Docker Compose plugin if missing ----
if ! docker compose version &>/dev/null; then
    log "Installing Docker Compose plugin..."
    apt-get install -y -qq docker-compose-plugin
fi

# ---- Create install directory ----
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# ---- Download compose file ----
log "Downloading docker-compose..."
cat > docker-compose.yml << 'COMPOSE'
# RealtorClaw — Lightsail deployment
services:
  db:
    image: postgres:16-alpine
    container_name: realtorclaw-db
    restart: always
    environment:
      POSTGRES_DB: ai_realtor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD:-realtorclaw2024}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    image: thedurancode/realtorclaw:latest
    container_name: realtorclaw-api
    restart: always
    depends_on:
      db:
        condition: service_healthy
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD:-realtorclaw2024}@db:5432/ai_realtor
      MCP_API_BASE_URL: http://localhost:8000
      MCP_API_KEY: ${REALTORCLAW_API_KEY:-}
      APP_ENV: ${APP_ENV:-production}
      API_WORKERS: ${API_WORKERS:-2}
    ports:
      - "80:8000"
      - "8001:8001"
    volumes:
      - ./log:/app/log
      - ./uploads:/app/uploads

volumes:
  pgdata:
COMPOSE

# ---- Create .env template ----
if [ ! -f .env ]; then
    log "Creating .env file..."
    PORTAL_SECRET=$(openssl rand -hex 32)
    cat > .env << ENVFILE
# ============================================
# RealtorClaw API Keys
# ============================================
# Edit this file: nano /opt/realtorclaw/.env
# Then restart: cd /opt/realtorclaw && docker compose restart api

# Required for AI features
ANTHROPIC_API_KEY=

# Required for address lookup
GOOGLE_PLACES_API_KEY=

# Portal auth (auto-generated)
PORTAL_JWT_SECRET=${PORTAL_SECRET}
APP_ENV=production

# Optional — enable as needed
OPENAI_API_KEY=
OPENROUTER_API_KEY=
ELEVENLABS_API_KEY=
VAPI_API_KEY=
DOCUSEAL_API_KEY=
EXA_API_KEY=
BRAVE_API_KEY=
SHOTSTACK_API_KEY=
PEXELS_API_KEY=
HEYGEN_API_KEY=
LOB_API_KEY=
RESEND_API_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
AWS_S3_BUCKET=
ENVFILE
    chmod 600 .env
    info "Edit API keys: nano $INSTALL_DIR/.env"
fi

# ---- Create log/uploads dirs ----
mkdir -p log uploads

# ---- Pull and start ----
log "Pulling Docker image..."
docker compose pull

log "Starting services..."
docker compose up -d

# ---- Wait for health ----
info "Waiting for API to start..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:80/health > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

# ---- Setup firewall ----
if command -v ufw &>/dev/null; then
    log "Configuring firewall..."
    ufw allow 22/tcp   # SSH
    ufw allow 80/tcp   # API
    ufw allow 8001/tcp # MCP SSE
    ufw --force enable 2>/dev/null || true
fi

# ---- Create management script ----
cat > /usr/local/bin/realtorclaw-ctl << 'CTL'
#!/bin/bash
cd /opt/realtorclaw
case "${1:-}" in
  start)   docker compose up -d ;;
  stop)    docker compose down ;;
  restart) docker compose restart api ;;
  logs)    docker compose logs -f api ;;
  update)  docker compose pull && docker compose up -d ;;
  status)  docker compose ps ;;
  shell)   docker exec -it realtorclaw-api bash ;;
  db)      docker exec -it realtorclaw-db psql -U postgres ai_realtor ;;
  env)     nano /opt/realtorclaw/.env ;;
  *)
    echo "RealtorClaw Management"
    echo "  realtorclaw-ctl start    - Start services"
    echo "  realtorclaw-ctl stop     - Stop services"
    echo "  realtorclaw-ctl restart  - Restart API"
    echo "  realtorclaw-ctl logs     - View live logs"
    echo "  realtorclaw-ctl update   - Pull latest image and restart"
    echo "  realtorclaw-ctl status   - Show service status"
    echo "  realtorclaw-ctl shell    - Shell into API container"
    echo "  realtorclaw-ctl db       - Open database shell"
    echo "  realtorclaw-ctl env      - Edit API keys"
    ;;
esac
CTL
chmod +x /usr/local/bin/realtorclaw-ctl

# ---- Get instance IP ----
PUBLIC_IP=$(curl -sf http://checkip.amazonaws.com 2>/dev/null || echo "YOUR_IP")

# ---- Done ----
echo ""
echo "============================================"
log "RealtorClaw is running!"
echo "============================================"
echo ""
if curl -sf http://localhost:80/health > /dev/null 2>&1; then
    info "API:       http://${PUBLIC_IP}"
    info "API Docs:  http://${PUBLIC_IP}/docs"
    info "MCP SSE:   http://${PUBLIC_IP}:8001/sse"
    info "Health:    http://${PUBLIC_IP}/health"
else
    info "API is still starting. Check: realtorclaw-ctl logs"
fi
echo ""
info "Next steps:"
info "  1. Add API keys:     nano /opt/realtorclaw/.env"
info "  2. Restart API:      realtorclaw-ctl restart"
info "  3. View logs:        realtorclaw-ctl logs"
info "  4. Update later:     realtorclaw-ctl update"
echo ""
info "Claude Code MCP config (add to settings):"
echo "  {\"mcpServers\":{\"realtorclaw\":{\"url\":\"http://${PUBLIC_IP}:8001/sse\"}}}"
echo ""
