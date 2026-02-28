#!/bin/bash

# AI Realtor Nanobot Skill Setup Script
# This script sets up the AI Realtor skill for nanobot
# Usage: bash scripts/setup-ai-realtor-skill.sh

set -e

echo "🏠 AI Realtor Nanobot Skill Setup"
echo "=================================="
echo ""

# Get the repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SOURCE="$REPO_ROOT/skills/ai-realtor/SKILL.md"

# Check if skill file exists
if [ ! -f "$SKILL_SOURCE" ]; then
    echo "❌ AI Realtor skill file not found at: $SKILL_SOURCE"
    echo "Please ensure you're running this script from the ai-realtor repository."
    exit 1
fi

echo "✅ Found AI Realtor skill at: $SKILL_SOURCE"

# Check if nanobot workspace exists
WORKSPACE="$HOME/.nanobot/workspace"
if [ ! -d "$WORKSPACE" ]; then
    echo "❌ Nanobot workspace not found at $WORKSPACE"
    echo "Please install nanobot first:"
    echo "  pip install nanobot-ai"
    echo "  nanobot onboard"
    exit 1
fi

echo "✅ Nanobot workspace found: $WORKSPACE"

# Create skills directory
SKILLS_DIR="$WORKSPACE/skills/ai-realtor"
mkdir -p "$SKILLS_DIR"
echo "✅ Created skills directory: $SKILLS_DIR"

# Copy skill file
cp "$SKILL_SOURCE" "$SKILLS_DIR/SKILL.md"
echo "✅ Installed AI Realtor skill to: $SKILLS_DIR/SKILL.md"

# Set API URL (default to production)
read -p "Enter AI Realtor API URL [https://ai-realtor.fly.dev]: " API_URL
API_URL=${API_URL:-https://ai-realtor.fly.dev}

# Set API key (optional)
read -p "Enter API Key (optional, press Enter to skip): " API_KEY

# Determine shell profile
SHELL_PROFILE="$HOME/.bashrc"
if [ -n "$ZSH_VERSION" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ -n "$FISH_VERSION" ]; then
    SHELL_PROFILE="$HOME/.config/fish/config.fish"
fi

# Add to shell profile
echo ""
echo "Adding environment variables to $SHELL_PROFILE"

# Remove old AI_REALTOR vars if they exist
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' '/# AI Realtor API Configuration/,/^export AI_REALTOR_/d' "$SHELL_PROFILE" 2>/dev/null || true
else
    # Linux
    sed -i '/# AI Realtor API Configuration/,/^export AI_REALTOR_/d' "$SHELL_PROFILE" 2>/dev/null || true
fi

# Add new configuration
{
    echo ""
    echo "# AI Realtor API Configuration"
    echo "export AI_REALTOR_API_URL=\"$API_URL\""
    if [ -n "$API_KEY" ]; then
        echo "export AI_REALTOR_API_KEY=\"$API_KEY\""
    fi
} >> "$SHELL_PROFILE"

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
echo "Skill details:"
echo "  • Name: ai-realtor"
echo "  • Description: AI-powered real estate platform with 162+ voice commands"
echo "  • Features: Property management, contracts, analytics, marketing, calendar"
echo "  • API: $API_URL"
echo ""
echo "To use immediately, run:"
if [ -n "$FISH_VERSION" ]; then
    echo "  source $SHELL_PROFILE"
else
    echo "  source $SHELL_PROFILE"
fi
echo ""
echo "Then restart nanobot to load the skill:"
echo "  nanobot agent"
echo ""
echo "Quick test commands:"
echo "  curl \$AI_REALTOR_API_URL/properties/ | jq '.'"
echo "  curl \$AI_REALTOR_API_URL/analytics/portfolio | jq '.'"
echo "  curl \$AI_REALTOR_API_URL/docs"
echo ""
echo "Voice examples (after loading nanobot):"
echo "  • 'Create a property at 123 Main St, New York for \$850,000'"
echo "  • 'Enrich property 5 with Zillow data'"
echo "  • 'Check if property 5 is ready to close'"
echo "  • 'Schedule a showing for tomorrow at 2pm'"
echo "  • 'Predict the outcome for property 5'"
echo ""
echo "For full documentation:"
echo "  • API Docs: https://ai-realtor.fly.dev/docs"
echo "  • GitHub: https://github.com/Thedurancode/ai-realtor"
echo ""
