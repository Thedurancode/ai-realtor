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
# Parameters
# ---------------------------------------------------------------------------

data "coder_parameter" "role" {
  name         = "role"
  display_name = "Workspace Role"
  description  = "What this workspace does"
  type         = "string"
  default      = "dev"
  mutable      = true
  icon         = "/emojis/1f916.png"
  option {
    name  = "Development"
    value = "dev"
    description = "Full dev environment — API + code-server + Claude Code"
  }
  option {
    name  = "Boss Agent"
    value = "boss"
    description = "Orchestrator — dispatches tasks to workers"
  }
  option {
    name  = "Worker Agent"
    value = "worker"
    description = "Picks up and executes tasks from the boss"
  }
}

data "coder_parameter" "cpu" {
  name         = "cpu"
  display_name = "CPU Cores"
  type         = "number"
  default      = "4"
  mutable      = true
  validation {
    min = 1
    max = 8
  }
}

data "coder_parameter" "memory" {
  name         = "memory"
  display_name = "Memory (GB)"
  type         = "number"
  default      = "8"
  mutable      = true
  validation {
    min = 2
    max = 32
  }
}

data "coder_parameter" "enable_postgres" {
  name         = "enable_postgres"
  display_name = "PostgreSQL"
  description  = "Run PostgreSQL sidecar"
  type         = "bool"
  default      = "true"
  mutable      = true
}

data "coder_parameter" "enable_redis" {
  name         = "enable_redis"
  display_name = "Redis"
  description  = "Run Redis sidecar"
  type         = "bool"
  default      = "true"
  mutable      = true
}

# ---------------------------------------------------------------------------
# Docker Network
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
  lifecycle { ignore_changes = all }
  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
}

resource "docker_container" "postgres" {
  count = data.coder_workspace.me.start_count * (data.coder_parameter.enable_postgres.value == "true" ? 1 : 0)
  name  = "coder-${data.coder_workspace_owner.me.name}-${lower(data.coder_workspace.me.name)}-pg"
  image = "pgvector/pgvector:pg16"
  env   = ["POSTGRES_USER=realtorclaw", "POSTGRES_PASSWORD=realtorclaw", "POSTGRES_DB=realtorclaw"]
  networks_advanced {
    name    = docker_network.workspace.name
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
  lifecycle { ignore_changes = all }
  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
}

resource "docker_container" "redis" {
  count   = data.coder_workspace.me.start_count * (data.coder_parameter.enable_redis.value == "true" ? 1 : 0)
  name    = "coder-${data.coder_workspace_owner.me.name}-${lower(data.coder_workspace.me.name)}-redis"
  image   = "redis:7-alpine"
  command = ["redis-server", "--appendonly", "yes"]
  networks_advanced {
    name    = docker_network.workspace.name
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
    # --- Fix permissions on persistent volume ---
    sudo chown -R coder:coder /home/coder 2>/dev/null || true
    mkdir -p /home/coder/.config /home/coder/.claude

    # --- Copy repo from baked image (first run only) ---
    REPO_DIR="/home/coder/ai-realtor"
    if [ ! -d "$REPO_DIR/.git" ]; then
      cp -r /opt/ai-realtor "$REPO_DIR"
      echo "Repo copied from image"
    else
      cd "$REPO_DIR"
      git pull origin main 2>/dev/null || echo "Git pull skipped"
    fi

    # --- Load env ---
    if [ -f "$REPO_DIR/.env" ]; then
      set -a && source "$REPO_DIR/.env" && set +a
    fi

    # --- code-server ---
    code-server --auth none --port 13337 --host 0.0.0.0 &

    # --- Wait for Postgres ---
    if [ "${data.coder_parameter.enable_postgres.value}" = "true" ]; then
      echo "Waiting for PostgreSQL..."
      for i in $(seq 1 30); do
        pg_isready -h postgres -U realtorclaw -q 2>/dev/null && echo "PostgreSQL ready" && break
        sleep 1
      done
      cd "$REPO_DIR" && alembic upgrade head 2>&1 || echo "Migration skipped"
    fi

    # --- Wait for Redis ---
    if [ "${data.coder_parameter.enable_redis.value}" = "true" ]; then
      echo "Waiting for Redis..."
      for i in $(seq 1 15); do
        redis-cli -h redis ping 2>/dev/null | grep -q PONG && echo "Redis ready" && break
        sleep 1
      done
    fi

    # --- Start services based on role ---
    ROLE="${data.coder_parameter.role.value}"
    cd "$REPO_DIR"

    if [ "$ROLE" = "dev" ] || [ "$ROLE" = "boss" ]; then
      python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/api.log 2>&1 &
      echo "FastAPI started on :8000"
    fi

    if [ "$ROLE" = "boss" ]; then
      python3 -m arq app.worker.WorkerSettings > /tmp/worker.log 2>&1 &
      echo "arq worker started"
    fi

    if [ "$ROLE" = "worker" ]; then
      WORKER_ID="${lower(data.coder_workspace.me.name)}"
      python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/api.log 2>&1 &
      python3 -m app.services.agent_worker --worker-id "$WORKER_ID" > /tmp/agent-worker.log 2>&1 &
      echo "Agent worker $WORKER_ID started"
    fi

    echo "RealtorClaw workspace ready (role: $ROLE)"
  EOT

  env = {
    ANTHROPIC_API_KEY  = var.anthropic_api_key
    MCP_API_KEY        = var.mcp_api_key
    ELEVENLABS_API_KEY = var.elevenlabs_api_key
    OPENAI_API_KEY     = var.openai_api_key
    DATABASE_URL       = data.coder_parameter.enable_postgres.value == "true" ? "postgresql://realtorclaw:realtorclaw@postgres:5432/realtorclaw" : "sqlite:///./ai_realtor.db"
    REDIS_HOST         = data.coder_parameter.enable_redis.value == "true" ? "redis" : ""
    REDIS_PORT         = "6379"
    WORKSPACE_ROLE     = data.coder_parameter.role.value
  }

  metadata {
    display_name = "Role"
    key          = "role"
    script       = "echo ${data.coder_parameter.role.value}"
    interval     = 600
    timeout      = 1
  }
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
    display_name = "API Status"
    key          = "api_status"
    script       = "curl -sf http://localhost:8000/health | python3 -c \"import sys,json; d=json.load(sys.stdin); print(d['status'])\" 2>/dev/null || echo 'offline'"
    interval     = 30
    timeout      = 3
  }
  metadata {
    display_name = "Worker Status"
    key          = "worker_status"
    script       = "pgrep -f 'agent_worker' >/dev/null && echo 'running' || (pgrep -f 'arq app.worker' >/dev/null && echo 'arq running' || echo 'stopped')"
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
# Apps
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
  command      = "tail -f /tmp/agent-worker.log 2>/dev/null || tail -f /tmp/worker.log 2>/dev/null || echo 'No worker logs yet'"
}

# ---------------------------------------------------------------------------
# Docker Image (repo baked in — no git clone at startup)
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
# Persistent Volume
# ---------------------------------------------------------------------------

resource "docker_volume" "home" {
  name = "coder-${data.coder_workspace.me.id}-home"
  lifecycle { ignore_changes = all }
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
  command  = ["sh", "-c", coder_agent.main.init_script]

  env = [
    "CODER_AGENT_TOKEN=${coder_agent.main.token}",
    "ANTHROPIC_API_KEY=${var.anthropic_api_key}",
    "MCP_API_KEY=${var.mcp_api_key}",
    "ELEVENLABS_API_KEY=${var.elevenlabs_api_key}",
    "OPENAI_API_KEY=${var.openai_api_key}",
    "DATABASE_URL=${data.coder_parameter.enable_postgres.value == "true" ? "postgresql://realtorclaw:realtorclaw@postgres:5432/realtorclaw" : "sqlite:///./ai_realtor.db"}",
    "REDIS_HOST=${data.coder_parameter.enable_redis.value == "true" ? "redis" : ""}",
    "REDIS_PORT=6379",
    "WORKSPACE_ROLE=${data.coder_parameter.role.value}",
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

  cpu_shares = data.coder_parameter.cpu.value * 1024
  memory     = data.coder_parameter.memory.value * 1024

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
# Variables (secrets)
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
