#!/bin/bash
# ============================================
# RealtorClaw — One-command deploy on fresh Linux
# ============================================
# Usage:
#   curl -sSL <raw-url>/deploy.sh | bash
#   OR: ./deploy.sh
#
# Requirements: Ubuntu 22.04+ / Debian 12+ (bare metal or VPS)
# Installs: Docker, pulls code, starts the stack
# Ports: 8000 (API), 8001 (MCP SSE), 5433 (Postgres)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
info() { echo -e "${CYAN}[i]${NC} $1"; }
err()  { echo -e "${RED}[!]${NC} $1"; exit 1; }

INSTALL_DIR="${INSTALL_DIR:-/opt/realtorclaw}"
REPO_URL="${REPO_URL:-https://github.com/your-org/ai-realtor.git}"
BRANCH="${BRANCH:-main}"

# ---- Pre-flight ----
[[ $EUID -ne 0 ]] && err "Run as root: sudo ./deploy.sh"

log "Starting RealtorClaw deployment..."

# ---- Install Docker if missing ----
if ! command -v docker &>/dev/null; then
    log "Installing Docker..."
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") \
        $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable --now docker
    log "Docker installed"
else
    info "Docker already installed"
fi

# ---- Clone or update repo ----
if [ -d "$INSTALL_DIR/.git" ]; then
    info "Updating existing install at $INSTALL_DIR"
    cd "$INSTALL_DIR"
    git pull origin "$BRANCH"
else
    log "Cloning repo to $INSTALL_DIR..."
    git clone --depth 1 -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# ---- Create .env if missing ----
if [ ! -f .env ]; then
    log "Creating .env from template..."
    cp .env.example .env
    # Generate secure secrets
    PORTAL_SECRET=$(openssl rand -hex 32)
    sed -i "s/change-this-in-production-use-a-strong-random-secret/$PORTAL_SECRET/" .env
    info "Edit .env with your API keys: nano $INSTALL_DIR/.env"
fi

# ---- Build & launch ----
log "Building lean Docker image..."
docker compose -f docker-compose-lean.yml build --no-cache

log "Starting services..."
docker compose -f docker-compose-lean.yml up -d

# ---- Wait for health ----
info "Waiting for services to start..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/docs > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

# ---- Verify ----
echo ""
if curl -sf http://localhost:8000/docs > /dev/null 2>&1; then
    log "API is live at http://localhost:8000"
else
    err "API failed to start. Check logs: docker compose -f docker-compose-lean.yml logs api"
fi

if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
    log "MCP SSE server is live at http://localhost:8001/sse"
else
    info "MCP server may still be starting. Check: curl http://localhost:8001/health"
fi

echo ""
log "Deployment complete!"
echo ""
info "Quick reference:"
info "  API docs:    http://localhost:8000/docs"
info "  MCP SSE:     http://localhost:8001/sse"
info "  Logs:        docker compose -f docker-compose-lean.yml logs -f api"
info "  Stop:        docker compose -f docker-compose-lean.yml down"
info "  Restart:     docker compose -f docker-compose-lean.yml restart api"
info "  Shell:       docker exec -it realtorclaw-api bash"
info "  DB shell:    docker exec -it realtorclaw-db psql -U postgres ai_realtor"
echo ""
info "Claude Code MCP config (add to ~/.claude/settings.json):"
cat <<'MCPCFG'
{
  "mcpServers": {
    "realtorclaw": {
      "url": "http://localhost:8001/sse"
    }
  }
}
MCPCFG
echo ""
