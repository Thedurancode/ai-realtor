#!/bin/bash
# Persistent Claude Code session via tmux
# Usage: bash scripts/claude-persistent.sh [session-name]
#
# This keeps Claude Code running in a tmux session that survives:
#   - SSH disconnects
#   - Terminal closes
#   - System sleep (on servers)
#
# Reconnect anytime: tmux attach -t claude

SESSION="${1:-claude}"
PROJ_DIR="$HOME/Documents/GitHub/ai-realtor"

# Install tmux if missing
if ! command -v tmux &>/dev/null; then
    echo "Installing tmux..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install tmux
    else
        sudo apt-get install -y tmux
    fi
fi

# Check if session already exists
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already running. Attaching..."
    tmux attach -t "$SESSION"
    exit 0
fi

# Create new tmux session with Claude Code
tmux new-session -d -s "$SESSION" -c "$PROJ_DIR"

# Window 0: Claude Code (interactive)
tmux send-keys -t "$SESSION" "claude --dangerously-skip-permissions --continue" Enter

# Window 1: ClaudeBot (background agent)
tmux new-window -t "$SESSION" -n "claudebot" -c "$PROJ_DIR"
tmux send-keys -t "$SESSION:claudebot" "python3 claudebot/main.py 2>&1 | tee -a log/claudebot.log" Enter

# Window 2: Logs
tmux new-window -t "$SESSION" -n "logs" -c "$PROJ_DIR"
tmux send-keys -t "$SESSION:logs" "tail -f log/claudebot.log 2>/dev/null || echo 'No logs yet'" Enter

# Go back to Claude Code window
tmux select-window -t "$SESSION:0"

# Attach
echo "Starting persistent Claude session..."
echo ""
echo "  Window 0: Claude Code (interactive)"
echo "  Window 1: ClaudeBot (Telegram + Discord + Cron)"
echo "  Window 2: Logs"
echo ""
echo "  Ctrl+B then D = detach (keeps running)"
echo "  Ctrl+B then 0/1/2 = switch windows"
echo "  tmux attach -t $SESSION = reconnect"
echo ""
tmux attach -t "$SESSION"
