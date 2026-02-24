#!/bin/bash

# AI Realtor Nanobot Skill Setup Script
# This script sets up the AI Realtor skill for nanobot

set -e

echo "🏠 AI Realtor Nanobot Skill Setup"
echo "================================="
echo ""

# Check if nanobot workspace exists
WORKSPACE="$HOME/.nanobot/workspace"
if [ ! -d "$WORKSPACE" ]; then
    echo "❌ Nanobot workspace not found at $WORKSPACE"
    echo "Please install nanobot first: https://github.com/HKD0/nanobot"
    exit 1
fi

echo "✅ Nanobot workspace found: $WORKSPACE"

# Create skills directory
SKILLS_DIR="$WORKSPACE/skills/ai-realtor"
mkdir -p "$SKILLS_DIR"
echo "✅ Created skills directory: $SKILLS_DIR"

# Set API URL (default to production)
read -p "Enter AI Realtor API URL [https://ai-realtor.fly.dev]: " API_URL
API_URL=${API_URL:-https://ai-realtor.fly.dev}

# Set API key (optional)
read -p "Enter API Key (optional, press Enter to skip): " API_KEY

# Add to shell profile
SHELL_PROFILE="$HOME/.bashrc"
if [ -n "$ZSH_VERSION" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
fi

echo ""
echo "Adding environment variables to $SHELL_PROFILE"
echo "" >> "$SHELL_PROFILE"
echo "# AI Realtor API Configuration" >> "$SHELL_PROFILE"
echo "export AI_REALTOR_API_URL=\"$API_URL\"" >> "$SHELL_PROFILE"
if [ -n "$API_KEY" ]; then
    echo "export AI_REALTOR_API_KEY=\"$API_KEY\"" >> "$SHELL_PROFILE"
fi

echo "✅ Environment variables configured"

# Export for current session
export AI_REALTOR_API_URL="$API_URL"
if [ -n "$API_KEY" ]; then
    export AI_REALTOR_API_KEY="$API_KEY"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "The AI Realtor skill has been installed to: $SKILLS_DIR"
echo ""
echo "To use immediately, run:"
echo "  source $SHELL_PROFILE"
echo ""
echo "Then restart nanobot to load the skill."
echo ""
echo "Quick test:"
echo "  curl \$AI_REALTOR_API_URL/properties/ | jq '.'
echo ""
