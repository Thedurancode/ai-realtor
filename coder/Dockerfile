FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/coder
ENV PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

# System deps
RUN apt-get update && apt-get install -y \
    curl git wget unzip sudo \
    python3 python3-pip python3-venv \
    build-essential ca-certificates gnupg lsb-release \
    jq htop tmux vim nano \
    postgresql-client redis-tools \
    poppler-utils tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Create coder user with sudo
RUN useradd --create-home --shell /bin/bash coder && \
    echo "coder ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/coder

# Node.js 22
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# code-server (VS Code in browser)
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# uv (fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | CARGO_HOME=/usr/local sh

# Bake the repo into the image (no git clone needed at startup)
RUN git clone https://github.com/Thedurancode/ai-realtor.git /opt/ai-realtor && \
    chown -R coder:coder /opt/ai-realtor

# Install Python deps from baked repo
RUN pip3 install --break-system-packages -r /opt/ai-realtor/requirements.txt && \
    pip3 install --break-system-packages python-telegram-bot "discord.py"

# Switch to coder user
USER coder
WORKDIR /home/coder

# Claude Code settings (YOLO mode + plugins)
RUN mkdir -p /home/coder/.claude && \
    cat > /home/coder/.claude/settings.json << 'SETTINGS'
{
  "enabledPlugins": {
    "yolo-mode@yolo-marketplace": true
  },
  "extraKnownMarketplaces": {
    "yolo-marketplace": {
      "source": {
        "source": "git",
        "url": "https://github.com/nbiish/yolo-mode.git"
      }
    },
    "thedotmack": {
      "source": {
        "source": "github",
        "repo": "thedotmack/claude-mem"
      }
    }
  },
  "skipDangerousModePermissionPrompt": true
}
SETTINGS

# Git config
RUN git config --global init.defaultBranch main && \
    git config --global pull.rebase false && \
    git config --global user.name "Ed Duran" && \
    git config --global user.email "emprezarioinc@gmail.com" && \
    git config --global credential.helper ""

# Shell config
RUN cat >> /home/coder/.bashrc << 'BASHRC'

# RealtorClaw workspace aliases
alias claude="claude --dangerously-skip-permissions"
alias codelive="claude --dangerously-skip-permissions"
alias api="cd ~/ai-realtor && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
alias worker="cd ~/ai-realtor && python3 -m arq app.worker.WorkerSettings"
alias agent-worker="cd ~/ai-realtor && python3 -m app.services.agent_worker"
alias api-log="tail -f /tmp/api.log"
alias worker-log="tail -f /tmp/worker.log"
alias dbshell="psql postgresql://realtorclaw:realtorclaw@postgres:5432/realtorclaw"
alias migrate="cd ~/ai-realtor && alembic upgrade head"
alias test="cd ~/ai-realtor && python3 -m pytest -x -q"

# Status on login
echo ""
echo "  RealtorClaw Dev Workspace"
echo "  ========================="
echo "  API:     http://localhost:8000/docs"
echo "  VS Code: http://localhost:13337"
echo "  Aliases: api, worker, agent-worker, dbshell, migrate, test, claude"
echo ""
BASHRC

EXPOSE 8000 13337
