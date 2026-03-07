terraform {
  required_providers {
    coder = {
      source = "coder/coder"
    }
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

# --- Providers ---
data "coder_provisioner" "me" {}
provider "coder" {}
provider "docker" {}

# --- Workspace Data ---
data "coder_workspace" "me" {}
data "coder_workspace_owner" "me" {}

# ---------------------------------------------------------------------------
# Parameters (shown in Coder UI when creating workspace)
# ---------------------------------------------------------------------------

data "coder_parameter" "repo_url" {
  name         = "repo_url"
  display_name = "Git Repo URL"
  description  = "Repository to clone"
  default      = "https://github.com/edduran/ai-realtor.git"
  mutable      = true
  icon         = "/icon/git.svg"
}

data "coder_parameter" "repo_branch" {
  name         = "repo_branch"
  display_name = "Branch"
  description  = "Git branch to clone"
  default      = "main"
  mutable      = true
  icon         = "/icon/git.svg"
}

data "coder_parameter" "cpu" {
  name         = "cpu"
  display_name = "CPU Cores"
  description  = "CPU cores for workspace container"
  type         = "number"
  default      = "4"
  mutable      = true
  icon         = "/emojis/1f5a5.png"
  validation {
    min = 1
    max = 8
  }
}

data "coder_parameter" "memory" {
  name         = "memory"
  display_name = "Memory (GB)"
  description  = "RAM for workspace container"
  type         = "number"
  default      = "8"
  mutable      = true
  icon         = "/emojis/1f4be.png"
  validation {
    min = 2
    max = 32
  }
}

data "coder_parameter" "enable_postgres" {
  name         = "enable_postgres"
  display_name = "PostgreSQL"
  description  = "Run PostgreSQL sidecar (otherwise uses SQLite)"
  type         = "bool"
  default      = "true"
  mutable      = true
  icon         = "/icon/database.svg"
}

data "coder_parameter" "enable_redis" {
  name         = "enable_redis"
  display_name = "Redis"
  description  = "Run Redis sidecar for job queue + caching"
  type         = "bool"
  default      = "true"
  mutable      = true
  icon         = "/icon/database.svg"
}

data "coder_parameter" "dotfiles_uri" {
  name         = "dotfiles_uri"
  display_name = "Dotfiles Repo (optional)"
  description  = "Git repo with your dotfiles (e.g. shell config, aliases)"
  default      = ""
  mutable      = true
  icon         = "/icon/widgets.svg"
}

# ---------------------------------------------------------------------------
# Docker Network (so containers can talk to each other)
# ---------------------------------------------------------------------------

resource "docker_network" "workspace" {
  name = "coder-${data.coder_workspace.me.id}-network"
  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
}

# ---------------------------------------------------------------------------
# PostgreSQL Sidecar
# ---------------------------------------------------------------------------

resource "docker_volume" "postgres_data" {
  count = data.coder_parameter.enable_postgres.value == "true" ? 1 : 0
  name  = "coder-${data.coder_workspace.me.id}-pgdata"
  lifecycle {
    ignore_changes = all
  }
  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
}

resource "docker_container" "postgres" {
  count = data.coder_workspace.me.start_count * (data.coder_parameter.enable_postgres.value == "true" ? 1 : 0)
  name  = "coder-${data.coder_workspace_owner.me.name}-${lower(data.coder_workspace.me.name)}-postgres"
  image = "pgvector/pgvector:pg16"

  env = [
    "POSTGRES_USER=realtorclaw",
    "POSTGRES_PASSWORD=realtorclaw",
    "POSTGRES_DB=realtorclaw",
  ]

  networks_advanced {
    name = docker_network.workspace.name
    aliases = ["postgres"]
  }

  volumes {
    container_path = "/var/lib/postgresql/data"
    volume_name    = docker_volume.postgres_data[0].name
    read_only      = false
  }

  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
}

# ---------------------------------------------------------------------------
# Redis Sidecar
# ---------------------------------------------------------------------------

resource "docker_volume" "redis_data" {
  count = data.coder_parameter.enable_redis.value == "true" ? 1 : 0
  name  = "coder-${data.coder_workspace.me.id}-redis"
  lifecycle {
    ignore_changes = all
  }
  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
}

resource "docker_container" "redis" {
  count = data.coder_workspace.me.start_count * (data.coder_parameter.enable_redis.value == "true" ? 1 : 0)
  name  = "coder-${data.coder_workspace_owner.me.name}-${lower(data.coder_workspace.me.name)}-redis"
  image = "redis:7-alpine"

  command = ["redis-server", "--appendonly", "yes"]

  networks_advanced {
    name = docker_network.workspace.name
    aliases = ["redis"]
  }

  volumes {
    container_path = "/data"
    volume_name    = docker_volume.redis_data[0].name
    read_only      = false
  }

  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
}

# ---------------------------------------------------------------------------
# Coder Agent
# ---------------------------------------------------------------------------

resource "coder_agent" "main" {
  arch = data.coder_provisioner.me.arch
  os   = "linux"

  startup_script_behavior = "non-blocking"
  startup_script = <<-EOT
    set -e

    # --- Dotfiles ---
    if [ -n "${data.coder_parameter.dotfiles_uri.value}" ]; then
      coder dotfiles -y "${data.coder_parameter.dotfiles_uri.value}" 2>&1 | tee /tmp/dotfiles.log &
    fi

    # --- Clone / update repo ---
    REPO_DIR="/home/coder/ai-realtor"
    if [ ! -d "$REPO_DIR/.git" ]; then
      git clone --branch "${data.coder_parameter.repo_branch.value}" "${data.coder_parameter.repo_url.value}" "$REPO_DIR" 2>&1 || true
    else
      cd "$REPO_DIR"
      git fetch origin
      git checkout "${data.coder_parameter.repo_branch.value}" 2>/dev/null || true
      git pull origin "${data.coder_parameter.repo_branch.value}" 2>/dev/null || true
    fi

    # --- Install/update Python deps ---
    cd "$REPO_DIR"
    pip3 install --break-system-packages -q -r requirements.txt 2>&1 | tail -1 &

    # --- Load env ---
    if [ -f "$REPO_DIR/.env" ]; then
      set -a && source "$REPO_DIR/.env" && set +a
    fi

    # --- code-server ---
    if command -v code-server &>/dev/null; then
      code-server --auth none --port 13337 --host 0.0.0.0 \
        --user-data-dir /home/coder/.code-server &
    fi

    # --- Wait for Postgres if enabled ---
    if [ "${data.coder_parameter.enable_postgres.value}" = "true" ]; then
      echo "Waiting for PostgreSQL..."
      for i in $(seq 1 30); do
        if pg_isready -h postgres -U realtorclaw -q 2>/dev/null; then
          echo "PostgreSQL ready"
          break
        fi
        sleep 1
      done

      # Run Alembic migrations
      cd "$REPO_DIR"
      alembic upgrade head 2>&1 || echo "Alembic migration skipped"
    fi

    # --- FastAPI server ---
    cd "$REPO_DIR"
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
      > /tmp/api.log 2>&1 &
    echo "FastAPI started on :8000"

    # --- arq worker (if Redis enabled) ---
    if [ "${data.coder_parameter.enable_redis.value}" = "true" ]; then
      echo "Waiting for Redis..."
      for i in $(seq 1 15); do
        if redis-cli -h redis ping 2>/dev/null | grep -q PONG; then
          echo "Redis ready"
          break
        fi
        sleep 1
      done
      cd "$REPO_DIR"
      python3 -m arq app.worker.WorkerSettings > /tmp/worker.log 2>&1 &
      echo "arq worker started"
    fi

    echo "RealtorClaw workspace ready"
  EOT

  env = {
    ANTHROPIC_API_KEY  = var.anthropic_api_key
    MCP_API_KEY        = var.mcp_api_key
    ELEVENLABS_API_KEY = var.elevenlabs_api_key
    OPENAI_API_KEY     = var.openai_api_key
    DATABASE_URL       = data.coder_parameter.enable_postgres.value == "true" ? "postgresql://realtorclaw:realtorclaw@postgres:5432/realtorclaw" : "sqlite:///./ai_realtor.db"
    REDIS_HOST         = data.coder_parameter.enable_redis.value == "true" ? "redis" : ""
    REDIS_PORT         = "6379"
  }

  # --- Dashboard Metadata ---
  metadata {
    display_name = "CPU Usage"
    key          = "cpu_usage"
    script       = "coder stat cpu"
    interval     = 10
    timeout      = 1
  }
  metadata {
    display_name = "RAM Usage"
    key          = "ram_usage"
    script       = "coder stat mem"
    interval     = 10
    timeout      = 1
  }
  metadata {
    display_name = "Disk Usage"
    key          = "disk_usage"
    script       = "coder stat disk --path /home/coder"
    interval     = 600
    timeout      = 1
  }
  metadata {
    display_name = "API Status"
    key          = "api_status"
    script       = "curl -sf http://localhost:8000/health | python3 -c \"import sys,json; d=json.load(sys.stdin); print(d['status'])\" 2>/dev/null || echo 'offline'"
    interval     = 30
    timeout      = 3
  }
  metadata {
    display_name = "Worker Status"
    key          = "worker_status"
    script       = "pgrep -f 'arq app.worker' >/dev/null && echo 'running' || echo 'stopped'"
    interval     = 30
    timeout      = 1
  }
  metadata {
    display_name = "PostgreSQL"
    key          = "pg_status"
    script       = "pg_isready -h postgres -U realtorclaw -q 2>/dev/null && echo 'connected' || echo 'offline'"
    interval     = 30
    timeout      = 2
  }
  metadata {
    display_name = "Redis"
    key          = "redis_status"
    script       = "redis-cli -h redis ping 2>/dev/null | grep -q PONG && echo 'connected' || echo 'offline'"
    interval     = 30
    timeout      = 2
  }
}

# ---------------------------------------------------------------------------
# Apps (buttons in workspace dashboard)
# ---------------------------------------------------------------------------

resource "coder_app" "code-server" {
  agent_id     = coder_agent.main.id
  slug         = "code-server"
  display_name = "VS Code"
  url          = "http://localhost:13337/?folder=/home/coder/ai-realtor"
  icon         = "/icon/code.svg"
  subdomain    = false
  share        = "owner"
}

resource "coder_app" "realtorclaw-api" {
  agent_id     = coder_agent.main.id
  slug         = "realtorclaw-api"
  display_name = "RealtorClaw API"
  url          = "http://localhost:8000/docs"
  icon         = "/icon/swagger.svg"
  subdomain    = false
  share        = "owner"
}

resource "coder_app" "api-health" {
  agent_id     = coder_agent.main.id
  slug         = "api-health"
  display_name = "API Health"
  url          = "http://localhost:8000/health"
  icon         = "/icon/heart.svg"
  subdomain    = false
  share        = "owner"
}

resource "coder_app" "claude-code" {
  agent_id     = coder_agent.main.id
  slug         = "claude-code"
  display_name = "Claude Code"
  icon         = "/icon/terminal.svg"
  command      = "cd /home/coder/ai-realtor && claude --dangerously-skip-permissions"
}

resource "coder_app" "terminal" {
  agent_id     = coder_agent.main.id
  slug         = "terminal"
  display_name = "Terminal"
  icon         = "/icon/terminal.svg"
  command      = "/bin/bash -l"
}

resource "coder_app" "logs-api" {
  agent_id     = coder_agent.main.id
  slug         = "logs-api"
  display_name = "API Logs"
  icon         = "/icon/widgets.svg"
  command      = "tail -f /tmp/api.log"
}

resource "coder_app" "logs-worker" {
  agent_id     = coder_agent.main.id
  slug         = "logs-worker"
  display_name = "Worker Logs"
  icon         = "/icon/widgets.svg"
  command      = "tail -f /tmp/worker.log"
}

# ---------------------------------------------------------------------------
# Docker Image
# ---------------------------------------------------------------------------

resource "docker_image" "realtorclaw" {
  name = "coder-realtorclaw-${data.coder_workspace.me.id}"
  build {
    context    = path.module
    dockerfile = "Dockerfile"
    tag        = ["coder-realtorclaw:latest"]
  }
  triggers = {
    dockerfile = sha256(file("${path.module}/Dockerfile"))
  }
}

# ---------------------------------------------------------------------------
# Persistent Volume (survives rebuilds)
# ---------------------------------------------------------------------------

resource "docker_volume" "home" {
  name = "coder-${data.coder_workspace.me.id}-home"
  lifecycle {
    ignore_changes = all
  }
  labels {
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }
  labels {
    label = "coder.owner_id"
    value = data.coder_workspace_owner.me.id
  }
  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
}

# ---------------------------------------------------------------------------
# Main Workspace Container
# ---------------------------------------------------------------------------

resource "docker_container" "workspace" {
  count = data.coder_workspace.me.start_count
  image = docker_image.realtorclaw.image_id
  name  = "coder-${data.coder_workspace_owner.me.name}-${lower(data.coder_workspace.me.name)}"

  hostname = data.coder_workspace.me.name
  dns      = ["1.1.1.1"]

  command = ["sh", "-c", replace(coder_agent.main.init_script, "/localhost|127\\.0\\.0\\.1/", "host.docker.internal")]

  env = [
    "CODER_AGENT_TOKEN=${coder_agent.main.token}",
    "ANTHROPIC_API_KEY=${var.anthropic_api_key}",
    "MCP_API_KEY=${var.mcp_api_key}",
    "ELEVENLABS_API_KEY=${var.elevenlabs_api_key}",
    "OPENAI_API_KEY=${var.openai_api_key}",
    "DATABASE_URL=${data.coder_parameter.enable_postgres.value == "true" ? "postgresql://realtorclaw:realtorclaw@postgres:5432/realtorclaw" : "sqlite:///./ai_realtor.db"}",
    "REDIS_HOST=${data.coder_parameter.enable_redis.value == "true" ? "redis" : ""}",
    "REDIS_PORT=6379",
  ]

  host {
    host = "host.docker.internal"
    ip   = "host-gateway"
  }

  networks_advanced {
    name = docker_network.workspace.name
  }

  volumes {
    container_path = "/home/coder"
    volume_name    = docker_volume.home.name
    read_only      = false
  }

  resources {
    cpu_shares = data.coder_parameter.cpu.value * 1024
    memory     = data.coder_parameter.memory.value * 1024
  }

  labels {
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }
  labels {
    label = "coder.owner_id"
    value = data.coder_workspace_owner.me.id
  }
  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
  labels {
    label = "coder.workspace_name"
    value = data.coder_workspace.me.name
  }
}

# ---------------------------------------------------------------------------
# Variables (secrets — set in Coder template settings)
# ---------------------------------------------------------------------------

variable "anthropic_api_key" {
  description = "Anthropic API key for Claude Code"
  type        = string
  sensitive   = true
  default     = ""
}

variable "mcp_api_key" {
  description = "RealtorClaw API key for MCP tools"
  type        = string
  sensitive   = true
  default     = ""
}

variable "elevenlabs_api_key" {
  description = "ElevenLabs API key for TTS/voice"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API key (embeddings, fallback)"
  type        = string
  sensitive   = true
  default     = ""
}
