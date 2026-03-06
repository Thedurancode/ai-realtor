#!/bin/bash
# Start ClaudeBot — Telegram + Discord bridge to Claude API
cd "$(dirname "$0")"

# Load env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Install deps if needed
pip3 install -q -r requirements.txt 2>/dev/null

echo "Starting ClaudeBot..."
python3 main.py "$@"
