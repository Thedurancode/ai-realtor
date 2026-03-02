#!/bin/bash

# Telegram Bot Menu Setup Script
# This script configures the AI Realtor bot with custom menus and buttons

BOT_TOKEN="8392020900:AAEKlrigz4_B35slxdJpBIApSrotEf3ceiI"

echo "🤖 AI Realtor Bot - Menu Setup"
echo "================================"

# Set custom bot commands
echo "1️⃣ Setting up bot commands..."
curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {"command": "start", "description": "🏠 Start AI Realtor Bot"},
      {"command": "properties", "description": "📋 View all properties"},
      {"command": "agents", "description": "👥 List all agents"},
      {"command": "create", "description": "➕ Create new property"},
      {"command": "enrich", "description": "📊 Enrich with Zillow data"},
      {"command": "skiptrace", "description": "🔍 Skip trace property"},
      {"command": "contracts", "description": "📄 View contracts"},
      {"command": "search", "description": "🔎 Search properties"},
      {"command": "help", "description": "❓ Get help"},
      {"command": "status", "description": "✅ System status"}
    ]
}' | jq -r '.ok // "false"'

# Set menu button to show commands
echo ""
echo "2️⃣ Setting up menu button..."
curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setChatMenuButton" \
  -H "Content-Type: application/json" \
  -d '{"menu_button":{"type":"commands"}}' | jq -r '.ok // "false"'

echo ""
echo "3️⃣ Current bot commands:"
curl -s "https://api.telegram.org/bot$BOT_TOKEN/getMyCommands" | jq -r '.result[] | "\(.command) - \(.description)"'

echo ""
echo "✅ Menu setup complete!"
echo ""
echo "Your bot now has a custom menu with 10 commands."
echo "Users can access these by:"
echo "  • Tapping the menu button (bottom left)"
echo "  • Typing /commands"
echo "  • Using /start, /properties, /agents, etc."
