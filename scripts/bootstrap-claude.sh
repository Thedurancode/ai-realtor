#!/bin/bash
# Bootstrap Claude Code on a fresh server — one command setup
# Usage: curl -sL <raw-github-url> | bash
#   or:  bash scripts/bootstrap-claude.sh /path/to/backup
set -e

BACKUP_DIR="${1:-}"
PROJ_DIR="$HOME/Documents/GitHub/ai-realtor"

echo "=== Claude Code Bootstrap ==="
echo ""

# 1. Install Node.js if missing
if ! command -v node &>/dev/null; then
    echo "1. Installing Node.js..."
    if [[ "$(uname)" == "Darwin" ]]; then
        if command -v brew &>/dev/null; then
            brew install node
        else
            echo "   Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install node
        fi
    else
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    echo "   ✓ Node $(node -v)"
else
    echo "1. Node.js already installed: $(node -v)"
fi

# 2. Install Claude Code
echo ""
if ! command -v claude &>/dev/null; then
    echo "2. Installing Claude Code..."
    npm install -g @anthropic-ai/claude-code
    echo "   ✓ Claude Code installed"
else
    echo "2. Claude Code already installed: $(claude --version 2>/dev/null || echo 'installed')"
fi

# 3. Clone the repo if not present
echo ""
if [ ! -d "$PROJ_DIR" ]; then
    echo "3. Cloning ai-realtor repo..."
    mkdir -p "$(dirname "$PROJ_DIR")"
    git clone git@github.com:edduran/ai-realtor.git "$PROJ_DIR"
    echo "   ✓ Repo cloned"
else
    echo "3. Repo already exists at $PROJ_DIR"
fi

# 4. Restore from backup if provided
echo ""
if [ -n "$BACKUP_DIR" ] && [ -d "$BACKUP_DIR" ]; then
    echo "4. Restoring from backup: $BACKUP_DIR"

    # Global settings
    mkdir -p "$HOME/.claude"
    cp -f "$BACKUP_DIR/settings.json" "$HOME/.claude/" 2>/dev/null && echo "   ✓ settings.json"
    cp -f "$BACKUP_DIR/settings.local.json" "$HOME/.claude/" 2>/dev/null && echo "   ✓ settings.local.json"
    cp -f "$BACKUP_DIR/keybindings.json" "$HOME/.claude/" 2>/dev/null && echo "   ✓ keybindings.json"
    cp -f "$BACKUP_DIR/global-mcp.json" "$HOME/.claude/.mcp.json" 2>/dev/null && echo "   ✓ global .mcp.json"

    # Plugins
    if [ -d "$BACKUP_DIR/plugins" ]; then
        mkdir -p "$HOME/.claude/plugins"
        cp -f "$BACKUP_DIR/plugins/"* "$HOME/.claude/plugins/" 2>/dev/null && echo "   ✓ plugins"
    fi

    # Memory files
    if [ -d "$BACKUP_DIR/memory" ]; then
        MEMORY_DIR="$HOME/.claude/projects/-Users-edduran-Documents-GitHub-ai-realtor/memory"
        mkdir -p "$MEMORY_DIR"
        cp -f "$BACKUP_DIR/memory/"*.md "$MEMORY_DIR/" 2>/dev/null
        echo "   ✓ $(ls "$MEMORY_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ') memory files"
    fi

    # Project configs
    cp -f "$BACKUP_DIR/.mcp.json" "$PROJ_DIR/" 2>/dev/null && echo "   ✓ project .mcp.json"
    cp -f "$BACKUP_DIR/CLAUDE.md" "$PROJ_DIR/" 2>/dev/null && echo "   ✓ CLAUDE.md"
    if [ -d "$BACKUP_DIR/project-claude" ]; then
        mkdir -p "$PROJ_DIR/.claude"
        cp -rf "$BACKUP_DIR/project-claude/"* "$PROJ_DIR/.claude/" 2>/dev/null && echo "   ✓ .claude/ directory"
    fi

    # ClaudeBot
    if [ -d "$BACKUP_DIR/claudebot" ]; then
        mkdir -p "$PROJ_DIR/claudebot"
        cp -f "$BACKUP_DIR/claudebot/"* "$PROJ_DIR/claudebot/" 2>/dev/null && echo "   ✓ claudebot config"
    fi

    # Shell aliases
    if [ -f "$BACKUP_DIR/zshrc-claude-lines.txt" ]; then
        echo ""
        echo "   Shell aliases to add to ~/.zshrc:"
        sed 's/^/     /' "$BACKUP_DIR/zshrc-claude-lines.txt"
    fi
else
    echo "4. No backup provided — fresh install"
    echo "   To restore later: bash scripts/bootstrap-claude.sh /path/to/backup"
fi

# 5. Install Python deps if in project
echo ""
if [ -f "$PROJ_DIR/requirements.txt" ]; then
    echo "5. Python dependencies"
    if [ ! -d "$PROJ_DIR/venv" ]; then
        python3 -m venv "$PROJ_DIR/venv"
        echo "   ✓ venv created"
    fi
    source "$PROJ_DIR/venv/bin/activate"
    pip install -q -r "$PROJ_DIR/requirements.txt"
    echo "   ✓ $(pip list 2>/dev/null | wc -l | tr -d ' ') packages installed"
else
    echo "5. No requirements.txt found — skipping Python deps"
fi

# 6. Reinstall plugins
echo ""
echo "6. Plugin reinstall"
if [ -f "$HOME/.claude/plugins/known_marketplaces.json" ]; then
    echo "   Run these in Claude Code to reinstall plugins:"
    python3 -c "
import json
with open('$HOME/.claude/plugins/known_marketplaces.json') as f:
    data = json.load(f)
for name, info in data.items():
    src = info.get('source', {})
    url = src.get('url', '') or f\"https://github.com/{src.get('repo', '')}\"
    print(f'     /plugin marketplace add {url}')
for name in data:
    print(f'     /plugin install {name}')
" 2>/dev/null
else
    echo "   No plugins to restore"
fi

# Done
echo ""
echo "==============================="
echo "Bootstrap complete!"
echo ""
echo "Next steps:"
echo "  1. cd $PROJ_DIR"
echo "  2. claude    (authenticate with Anthropic)"
echo "  3. Copy .env from secure storage"
echo "==============================="
