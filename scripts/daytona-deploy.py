#!/usr/bin/env python3
"""
One-click deploy: ai-realtor + Claude Code into a Daytona sandbox.

Usage:
    # Deploy with defaults
    python3 scripts/daytona-deploy.py

    # Custom Daytona server
    python3 scripts/daytona-deploy.py --api-url https://platform.emprezario.com --api-key dtn_xxx

    # With Anthropic key for Claude
    python3 scripts/daytona-deploy.py --anthropic-key sk-ant-xxx

Environment variables (alternative to flags):
    DAYTONA_API_URL   — Daytona server URL
    DAYTONA_API_KEY   — Daytona API key
    ANTHROPIC_API_KEY — For Claude Code inside the sandbox
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
REPO_URL = "https://github.com/Thedurancode/ai-realtor.git"
REPO_BRANCH = "main"
SANDBOX_LABEL = "ai-realtor"

# The Daytona toolbox exec API parses command strings oddly (splits on flags
# and shell operators).  We write a single setup script to the sandbox
# filesystem via the file-upload endpoint, then execute it with bash.

SETUP_SCRIPT_TEMPLATE = r"""#!/bin/bash
set -e

echo "==> Installing system deps..."
sudo apt-get update -qq
sudo apt-get install -y -qq git curl build-essential libpq-dev locales
sudo locale-gen en_US.UTF-8
export LANG=en_US.UTF-8

echo "==> Cloning repo..."
if [ ! -d /home/daytona/ai-realtor/.git ]; then
    git clone --depth 1 -b {branch} {clone_url} /home/daytona/ai-realtor
else
    cd /home/daytona/ai-realtor && git pull || true
    echo "    (repo already cloned)"
fi

echo "==> Installing Python deps..."
cd /home/daytona/ai-realtor
pip install -q -r requirements.txt

echo "==> Installing Claude Code..."
# nvm-managed node — source nvm first, then use full paths for sudo
export NVM_DIR="/usr/local/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
NPM_PATH=$(which npm 2>/dev/null || echo "/usr/local/nvm/versions/node/v22.14.0/bin/npm")
NODE_PATH=$(dirname $NPM_PATH)
sudo env "PATH=$NODE_PATH:$PATH" npm install -g @anthropic-ai/claude-code

echo "==> Setting up .env..."
cd /home/daytona/ai-realtor
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
    fi
    # Override DATABASE_URL for SQLite (no Postgres in sandbox)
    sed -i 's|^DATABASE_URL=.*|DATABASE_URL=sqlite:///./ai_realtor.db|' .env 2>/dev/null || true
    # Ensure DATABASE_URL is set even if not in example
    grep -q '^DATABASE_URL=' .env 2>/dev/null || echo 'DATABASE_URL=sqlite:///./ai_realtor.db' >> .env
fi

echo "==> Initialising database..."
python3 -c "
from app.database import engine, Base
from sqlalchemy import text
Base.metadata.create_all(engine)
print(f'Tables: {{len(Base.metadata.tables)}}')
" || echo "  (db init failed — may need .env first)"

echo "==> Starting API server..."
cd /home/daytona/ai-realtor
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
    > /tmp/api.log 2>&1 &
API_PID=$!

echo "==> Starting MCP server..."
nohup python3 -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8001 \
    > /tmp/mcp.log 2>&1 &
MCP_PID=$!

echo "==> Waiting for health..."
sleep 3
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "API healthy (PID $API_PID)"
else
    echo "API not yet healthy — check /tmp/api.log"
fi

echo "==> Setup complete!"
"""


def build_setup_script(github_token: str | None = None) -> str:
    """Build the setup script, injecting GitHub token if provided."""
    if github_token:
        # Insert token into the URL: https://TOKEN@github.com/...
        clone_url = REPO_URL.replace("https://", f"https://{github_token}@")
    else:
        clone_url = REPO_URL
    return SETUP_SCRIPT_TEMPLATE.format(clone_url=clone_url, branch=REPO_BRANCH)


# ---------------------------------------------------------------------------
# Daytona API client (stdlib only — no pip deps needed)
# ---------------------------------------------------------------------------
class DaytonaClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

    def _request(self, method: str, path: str, body: dict | None = None, timeout: int = 30) -> dict | str:
        url = f"{self.api_url}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return raw
        except urllib.error.HTTPError as e:
            body_text = e.read().decode() if e.fp else ""
            raise RuntimeError(f"HTTP {e.code} {method} {path}: {body_text}") from e

    def list_sandboxes(self) -> list[dict]:
        resp = self._request("GET", "/api/sandbox/paginated")
        return resp.get("items", [])

    def create_sandbox(self) -> dict:
        return self._request("POST", "/api/sandbox", {
            "labels": {SANDBOX_LABEL: "true"},
        })

    def get_sandbox(self, sandbox_id: str) -> dict:
        return self._request("GET", f"/api/sandbox/{sandbox_id}")

    def start_sandbox(self, sandbox_id: str) -> dict:
        return self._request("POST", f"/api/sandbox/{sandbox_id}/start")

    def make_public(self, sandbox_id: str) -> dict:
        return self._request("POST", f"/api/sandbox/{sandbox_id}/public/true")

    def exec(self, sandbox_id: str, command: str, timeout: int = 300) -> dict:
        return self._request(
            "POST",
            f"/api/toolbox/{sandbox_id}/toolbox/process/execute",
            {"command": command},
            timeout=timeout,
        )

    def upload_file(self, sandbox_id: str, path: str, content: str) -> None:
        """Upload a file to the sandbox via the multipart upload endpoint."""
        import email.generator
        boundary = "----DaytonaUploadBoundary"
        # Build multipart body manually (no requests library)
        body_parts = [
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(path)}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
            f"{content}\r\n"
            f"--{boundary}--\r\n"
        ]
        body = "".join(body_parts).encode()
        url = f"{self.api_url}/api/toolbox/{sandbox_id}/toolbox/files/upload?path={urllib.parse.quote(path, safe='')}"
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp.read()
        except urllib.error.HTTPError as e:
            body_text = e.read().decode() if e.fp else ""
            raise RuntimeError(f"Upload failed: HTTP {e.code}: {body_text}") from e

    def shell(self, sandbox_id: str, command: str, timeout: int = 300) -> dict:
        """Execute a command through bash (handles shell operators like &&, >, |)."""
        # The toolbox exec API doesn't use a shell by default, so we wrap in bash -c
        # We need to escape single quotes in the command
        escaped = command.replace("'", "'\"'\"'")
        return self.exec(sandbox_id, f"bash -c '{escaped}'", timeout=timeout)


# ---------------------------------------------------------------------------
# Claude settings generator
# ---------------------------------------------------------------------------
def generate_claude_settings() -> dict:
    """Generate ~/.claude/settings.json for the sandbox (Linux-compatible)."""
    return {
        "enabledPlugins": {
            "yolo-mode@yolo-marketplace": True,
            "claude-mem@thedotmack": True,
        },
        "extraKnownMarketplaces": {
            "yolo-marketplace": {
                "source": {"source": "git", "url": "https://github.com/nbiish/yolo-mode.git"}
            },
            "thedotmack": {
                "source": {"source": "github", "repo": "thedotmack/claude-mem"}
            },
        },
        "skipDangerousModePermissionPrompt": True,
    }


def generate_project_settings() -> dict:
    """Generate .claude/settings.local.json for the project."""
    return {
        "permissions": {
            "allow": [
                "Bash(python3 -m pytest:*)",
                "Bash(ls:*)",
                "Bash(curl:*)",
                "Bash(python3:*)",
                "Bash(pip3 list:*)",
                "Bash(gh api:*)",
                "Bash(chmod +x:*)",
            ]
        },
        "enableAllProjectMcpServers": True,
    }


def generate_mcp_json() -> dict:
    """Generate .mcp.json with Linux-compatible paths."""
    return {
        "mcpServers": {
            "realtorclaw": {
                "command": "python3",
                "args": ["-m", "mcp_server.property_mcp"],
                "cwd": "/home/daytona/ai-realtor",
                "env": {
                    "MCP_API_BASE_URL": "http://localhost:8000",
                    "MCP_API_KEY": "${MCP_API_KEY}",
                    "DATABASE_URL": "sqlite:///./ai_realtor.db",
                },
            },
            "sequential-thinking": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
            },
            "fetch": {
                "command": "uvx",
                "args": ["mcp-server-fetch"],
            },
        }
    }


# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------
def deploy(client: DaytonaClient, anthropic_key: str | None = None, github_token: str | None = None) -> str:
    print("=== Daytona One-Click Deploy: ai-realtor ===\n")

    # ---- 1. Find or create sandbox ----------------------------------------
    print("[1/5] Checking for existing sandbox...")
    existing = [
        s for s in client.list_sandboxes()
        if s.get("labels", {}).get(SANDBOX_LABEL) == "true"
        and s.get("state") in ("started", "stopped")
    ]
    if existing:
        sb = existing[0]
        sandbox_id = sb["id"]
        print(f"  Found existing sandbox: {sandbox_id} (state: {sb['state']})")
        if sb["state"] == "stopped":
            print("  Starting sandbox...")
            client.start_sandbox(sandbox_id)
            time.sleep(5)
    else:
        print("  Creating sandbox...")
        sb = client.create_sandbox()
        sandbox_id = sb["id"]
        print(f"  Created: {sandbox_id}")
        for i in range(30):
            info = client.get_sandbox(sandbox_id)
            if info.get("state") == "started":
                break
            time.sleep(2)
            if i % 5 == 0:
                print(f"  Waiting... (state: {info.get('state')})")
        else:
            raise RuntimeError("Sandbox failed to start within 60 seconds")

    # ---- 2. Upload setup script --------------------------------------------
    print("\n[2/5] Uploading setup script...")
    setup_script = build_setup_script(github_token)
    client.upload_file(sandbox_id, "/tmp/setup.sh", setup_script)
    client.exec(sandbox_id, "chmod +x /tmp/setup.sh")
    print("  Uploaded /tmp/setup.sh")

    # ---- 3. Run setup script -----------------------------------------------
    print("\n[3/5] Running setup (this takes a few minutes)...")
    result = client.shell(sandbox_id, "bash /tmp/setup.sh", timeout=600)
    exit_code = result.get("exitCode", -1)
    output = result.get("result", "")
    # Print each ==> line from the script
    for line in output.splitlines():
        if line.startswith("==>") or line.startswith("Tables:") or "healthy" in line.lower():
            print(f"  {line}")
    if exit_code != 0:
        print(f"\n  WARNING: Setup exited with code {exit_code}")
        print(f"  Last output: {output[-300:]}")

    # ---- 4. Write Claude config files --------------------------------------
    print("\n[4/5] Configuring Claude Code...")
    settings_json = json.dumps(generate_claude_settings())
    project_settings_json = json.dumps(generate_project_settings())
    mcp_json = json.dumps(generate_mcp_json())

    client.shell(sandbox_id, "mkdir -p /home/daytona/.claude")
    client.upload_file(sandbox_id, "/home/daytona/.claude/settings.json", settings_json)

    client.shell(sandbox_id, "mkdir -p /home/daytona/ai-realtor/.claude")
    client.upload_file(sandbox_id, "/home/daytona/ai-realtor/.claude/settings.local.json", project_settings_json)

    client.upload_file(sandbox_id, "/home/daytona/ai-realtor/.mcp.json", mcp_json)

    # Anthropic key
    if anthropic_key:
        client.shell(
            sandbox_id,
            f"printf 'export ANTHROPIC_API_KEY=%s\\n' '{anthropic_key}' >> /home/daytona/.bashrc",
        )
        print("  Claude settings + ANTHROPIC_API_KEY configured.")
    else:
        print("  Claude settings written (no ANTHROPIC_API_KEY — set later).")

    # ---- 5. Make public & print summary ------------------------------------
    print("\n[5/5] Finalising...")
    try:
        client.make_public(sandbox_id)
    except Exception:
        pass

    base_domain = client.api_url.replace("https://", "").replace("http://", "").split(":")[0]
    print("\n" + "=" * 60)
    print("DEPLOY COMPLETE!")
    print("=" * 60)
    print(f"\n  Sandbox ID:  {sandbox_id}")
    print(f"  API:         https://8000-{sandbox_id}.{base_domain}")
    print(f"  MCP:         https://8001-{sandbox_id}.{base_domain}")
    print(f"  Dashboard:   {client.api_url}/dashboard")
    print(f"\n  Terminal:    Open dashboard -> click sandbox -> terminal")
    print(f"  Claude:      cd /home/daytona/ai-realtor && claude")
    if not anthropic_key:
        print(f"\n  NOTE: Set your key first:")
        print(f"    export ANTHROPIC_API_KEY=sk-ant-xxx")
    print("=" * 60)

    return sandbox_id


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Deploy ai-realtor to a Daytona sandbox")
    parser.add_argument("--api-url", default=os.environ.get("DAYTONA_API_URL", "https://platform.emprezario.com"))
    parser.add_argument("--api-key", default=os.environ.get("DAYTONA_API_KEY", ""))
    parser.add_argument("--anthropic-key", default=os.environ.get("ANTHROPIC_API_KEY", ""))
    parser.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN", ""))
    args = parser.parse_args()

    if not args.api_key:
        print("Error: --api-key or DAYTONA_API_KEY required")
        sys.exit(1)

    client = DaytonaClient(args.api_url, args.api_key)
    deploy(client, args.anthropic_key or None, args.github_token or None)


if __name__ == "__main__":
    main()
