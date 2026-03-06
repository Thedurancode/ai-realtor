#!/bin/bash
# Install ClaudeBot as a background service (Mac)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST="com.emprezario.claudebot.plist"
LAUNCH_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/.claudebot/logs"

echo "=== ClaudeBot Installer ==="

# Check for .env
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo "No .env file found. Creating from template..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "Edit $SCRIPT_DIR/.env with your API keys, then re-run this script."
    echo ""
    echo "  nano $SCRIPT_DIR/.env"
    echo ""
    exit 1
fi

# Create log dir
mkdir -p "$LOG_DIR"

# Install deps
echo "Installing dependencies..."
pip3 install --user --break-system-packages -q -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null || \
    pip3 install --user -q -r "$SCRIPT_DIR/requirements.txt"

# Install launchd service
echo "Installing background service..."
mkdir -p "$LAUNCH_DIR"
cp "$SCRIPT_DIR/$PLIST" "$LAUNCH_DIR/$PLIST"

# Stop if already running
launchctl bootout "gui/$(id -u)/$PLIST" 2>/dev/null || true

# Start
launchctl bootstrap "gui/$(id -u)" "$LAUNCH_DIR/$PLIST"

echo ""
echo "ClaudeBot installed and running!"
echo ""
echo "  Logs:    tail -f $LOG_DIR/stdout.log"
echo "  Stop:    launchctl bootout gui/$(id -u) $LAUNCH_DIR/$PLIST"
echo "  Restart: launchctl kickstart -k gui/$(id -u)/$PLIST"
echo ""
