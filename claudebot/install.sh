#!/bin/bash
# Install ClaudeBot as a background service (Mac + Linux)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

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

# Install deps
echo "Installing dependencies..."
pip3 install --break-system-packages -q -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null || \
    pip3 install --user -q -r "$SCRIPT_DIR/requirements.txt"

OS="$(uname -s)"

if [ "$OS" = "Darwin" ]; then
    # --- macOS: launchd ---
    PLIST="com.emprezario.claudebot.plist"
    LAUNCH_DIR="$HOME/Library/LaunchAgents"
    LOG_DIR="$HOME/.claudebot/logs"

    mkdir -p "$LOG_DIR" "$LAUNCH_DIR"
    cp "$SCRIPT_DIR/$PLIST" "$LAUNCH_DIR/$PLIST"

    launchctl bootout "gui/$(id -u)/$PLIST" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$LAUNCH_DIR/$PLIST"

    echo ""
    echo "ClaudeBot installed and running! (macOS launchd)"
    echo ""
    echo "  Logs:    tail -f $LOG_DIR/stdout.log"
    echo "  Stop:    launchctl bootout gui/$(id -u) $LAUNCH_DIR/$PLIST"
    echo "  Restart: launchctl kickstart -k gui/$(id -u)/$PLIST"
    echo ""

elif [ "$OS" = "Linux" ]; then
    # --- Linux: systemd ---
    SERVICE="claudebot.service"
    SERVICE_SRC="$SCRIPT_DIR/$SERVICE"
    SERVICE_DST="/etc/systemd/system/$SERVICE"

    # Update paths in service file to match actual location
    sed "s|WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|" "$SERVICE_SRC" | \
    sed "s|ExecStart=.*|ExecStart=/usr/bin/python3 $SCRIPT_DIR/main.py|" | \
    sed "s|EnvironmentFile=.*|EnvironmentFile=$SCRIPT_DIR/.env|" | \
    sed "s|User=.*|User=$(whoami)|" > "$SERVICE_DST"

    systemctl daemon-reload
    systemctl enable claudebot
    systemctl restart claudebot

    echo ""
    echo "ClaudeBot installed and running! (Linux systemd)"
    echo ""
    echo "  Logs:    journalctl -u claudebot -f"
    echo "  Stop:    systemctl stop claudebot"
    echo "  Restart: systemctl restart claudebot"
    echo "  Status:  systemctl status claudebot"
    echo ""

else
    echo "Unsupported OS: $OS"
    exit 1
fi
