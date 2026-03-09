#!/bin/bash
# Full Claude Code backup — settings, plugins, memory, MCP, hooks, everything
set -e

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$HOME/.claude/backups/$DATE"
mkdir -p "$BACKUP_DIR"

echo "=== Claude Code Full Backup — $DATE ==="

# 1. Global settings
echo ""
echo "1. Global settings"
for f in settings.json settings.local.json; do
    cp -f "$HOME/.claude/$f" "$BACKUP_DIR/" 2>/dev/null && echo "   ✓ $f" || true
done

# 2. Plugins (installed list, marketplaces, cache)
echo ""
echo "2. Plugins"
mkdir -p "$BACKUP_DIR/plugins"
cp -f "$HOME/.claude/plugins/installed_plugins.json" "$BACKUP_DIR/plugins/" 2>/dev/null && echo "   ✓ installed_plugins.json"
cp -f "$HOME/.claude/plugins/known_marketplaces.json" "$BACKUP_DIR/plugins/" 2>/dev/null && echo "   ✓ known_marketplaces.json"
cp -f "$HOME/.claude/plugins/blocklist.json" "$BACKUP_DIR/plugins/" 2>/dev/null && echo "   ✓ blocklist.json"

# Plugin source repos (lightweight — just the git URLs, not full cache)
if [ -f "$HOME/.claude/plugins/known_marketplaces.json" ]; then
    echo "   Plugin sources:"
    python3 -c "
import json
with open('$HOME/.claude/plugins/known_marketplaces.json') as f:
    data = json.load(f)
for name, info in data.items():
    src = info.get('source', {})
    url = src.get('url', '') or f\"github.com/{src.get('repo', '')}\"
    print(f'     {name}: {url}')
" 2>/dev/null
fi

# 3. Project MCP config
echo ""
echo "3. Project configs"
PROJ_DIR="$HOME/Documents/GitHub/ai-realtor"
cp -f "$PROJ_DIR/.mcp.json" "$BACKUP_DIR/" 2>/dev/null && echo "   ✓ .mcp.json"
cp -f "$PROJ_DIR/CLAUDE.md" "$BACKUP_DIR/" 2>/dev/null && echo "   ✓ CLAUDE.md"
mkdir -p "$BACKUP_DIR/project-claude"
cp -rf "$PROJ_DIR/.claude/"* "$BACKUP_DIR/project-claude/" 2>/dev/null && echo "   ✓ .claude/ directory (settings, yolo-state, OSA framework)"

# Global MCP config
cp -f "$HOME/.claude/.mcp.json" "$BACKUP_DIR/global-mcp.json" 2>/dev/null && echo "   ✓ global .mcp.json"

# Keybindings
cp -f "$HOME/.claude/keybindings.json" "$BACKUP_DIR/" 2>/dev/null && echo "   ✓ keybindings.json"

# 4. Memory files
echo ""
echo "4. Memory"
MEMORY_DIR="$HOME/.claude/projects/-Users-edduran-Documents-GitHub-ai-realtor/memory"
if [ -d "$MEMORY_DIR" ]; then
    mkdir -p "$BACKUP_DIR/memory"
    cp -f "$MEMORY_DIR"/*.md "$BACKUP_DIR/memory/" 2>/dev/null
    COUNT=$(ls "$BACKUP_DIR/memory/" 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✓ $COUNT memory files"
fi

# 5. Hooks
echo ""
echo "5. Hooks"
if [ -d "$HOME/.claude/hooks" ]; then
    mkdir -p "$BACKUP_DIR/hooks"
    cp -rf "$HOME/.claude/hooks/"* "$BACKUP_DIR/hooks/" 2>/dev/null
    echo "   ✓ hooks directory"
else
    # Check for project-level hooks
    if [ -d "$PROJ_DIR/.claude/hooks" ]; then
        mkdir -p "$BACKUP_DIR/hooks"
        cp -rf "$PROJ_DIR/.claude/hooks/"* "$BACKUP_DIR/hooks/" 2>/dev/null
        echo "   ✓ project hooks"
    else
        echo "   - no hooks found"
    fi
fi

# 6. ClaudeBot config
echo ""
echo "6. ClaudeBot"
if [ -d "$PROJ_DIR/claudebot" ]; then
    mkdir -p "$BACKUP_DIR/claudebot"
    cp -f "$PROJ_DIR/claudebot/.env" "$BACKUP_DIR/claudebot/" 2>/dev/null && echo "   ✓ .env" || echo "   - .env (not created yet)"
    cp -f "$PROJ_DIR/claudebot/.env.example" "$BACKUP_DIR/claudebot/" 2>/dev/null
    cp -f "$PROJ_DIR/claudebot/HEARTBEAT.md" "$BACKUP_DIR/claudebot/" 2>/dev/null && echo "   ✓ HEARTBEAT.md"
fi

# 7. Shell aliases
echo ""
echo "7. Shell config"
grep -n "claude\|codelive" "$HOME/.zshrc" > "$BACKUP_DIR/zshrc-claude-lines.txt" 2>/dev/null && echo "   ✓ zshrc aliases" || echo "   - no aliases"

# 8. Generate restore script
echo ""
echo "8. Generating restore script..."
cat > "$BACKUP_DIR/restore.sh" << 'RESTORE'
#!/bin/bash
# Restore Claude Code settings from backup
set -e
BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Restoring Claude Code from $BACKUP_DIR ==="

# Global settings
cp -f "$BACKUP_DIR/settings.json" "$HOME/.claude/" 2>/dev/null && echo "✓ settings.json"
cp -f "$BACKUP_DIR/settings.local.json" "$HOME/.claude/" 2>/dev/null && echo "✓ settings.local.json"

# Plugins
cp -f "$BACKUP_DIR/plugins/installed_plugins.json" "$HOME/.claude/plugins/" 2>/dev/null && echo "✓ installed_plugins.json"
cp -f "$BACKUP_DIR/plugins/known_marketplaces.json" "$HOME/.claude/plugins/" 2>/dev/null && echo "✓ known_marketplaces.json"

# Reinstall plugins from marketplaces
echo ""
echo "To reinstall plugins, run in Claude Code:"
if [ -f "$BACKUP_DIR/plugins/known_marketplaces.json" ]; then
    python3 -c "
import json
with open('$BACKUP_DIR/plugins/known_marketplaces.json') as f:
    data = json.load(f)
for name, info in data.items():
    src = info.get('source', {})
    url = src.get('url', '') or f\"https://github.com/{src.get('repo', '')}\"
    print(f'  /plugin marketplace add {url}')
print()
for name in data:
    print(f'  /plugin install {name}')
" 2>/dev/null
fi

# Project configs
PROJ_DIR="$HOME/Documents/GitHub/ai-realtor"
cp -f "$BACKUP_DIR/.mcp.json" "$PROJ_DIR/" 2>/dev/null && echo "✓ .mcp.json"
cp -f "$BACKUP_DIR/CLAUDE.md" "$PROJ_DIR/" 2>/dev/null && echo "✓ CLAUDE.md"
cp -f "$BACKUP_DIR/project-settings.local.json" "$PROJ_DIR/.claude/settings.local.json" 2>/dev/null && echo "✓ project settings"

# Memory
MEMORY_DIR="$HOME/.claude/projects/-Users-edduran-Documents-GitHub-ai-realtor/memory"
if [ -d "$BACKUP_DIR/memory" ]; then
    mkdir -p "$MEMORY_DIR"
    cp -f "$BACKUP_DIR/memory/"*.md "$MEMORY_DIR/" 2>/dev/null && echo "✓ memory files"
fi

echo ""
echo "Restore complete. Restart Claude Code."
RESTORE
chmod +x "$BACKUP_DIR/restore.sh"
echo "   ✓ restore.sh created"

# Summary
echo ""
echo "==============================="
echo "Backup complete!"
echo "Location: $BACKUP_DIR"
echo "Files:    $(find "$BACKUP_DIR" -type f | wc -l | tr -d ' ')"
echo "Size:     $(du -sh "$BACKUP_DIR" | cut -f1)"
echo ""
echo "To restore: $BACKUP_DIR/restore.sh"
echo "==============================="

# Cleanup old backups (keep last 10)
BACKUP_ROOT="$HOME/.claude/backups"
BACKUP_COUNT=$(ls -d "$BACKUP_ROOT"/2* 2>/dev/null | wc -l | tr -d ' ')
if [ "$BACKUP_COUNT" -gt 10 ]; then
    echo ""
    echo "Cleaning old backups (keeping last 10)..."
    ls -d "$BACKUP_ROOT"/2* | head -n -10 | xargs rm -rf
fi
