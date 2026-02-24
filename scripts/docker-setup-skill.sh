#!/bin/bash

# AI Realtor Nanobot Skill - Docker/Environment-Friendly Setup
# This script handles different deployment scenarios

set -e

echo "🏠 AI Realtor Nanobot Skill Setup"
echo "================================="
echo ""

# Detect environment
if [ -n "$AI_REALTOR_API_URL" ]; then
    echo "✅ Environment variable detected: $AI_REALTOR_API_URL"
    API_URL="$AI_REALTOR_API_URL"
else
    # Try to detect common scenarios
    if curl -s http://host.docker.internal:8000/docs > /dev/null 2>&1; then
        echo "🐳 Detected: Docker environment (host.docker.internal)"
        API_URL="http://host.docker.internal:8000"
    elif curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo "💻 Detected: Local development server"
        API_URL="http://localhost:8000"
    elif curl -s https://ai-realtor.fly.dev/docs > /dev/null 2>&1; then
        echo "☁️ Detected: Using production API"
        API_URL="https://ai-realtor.fly.dev"
    else
        echo "⚠️  Could not auto-detect API URL"
        echo ""
        read -p "Enter your AI Realtor API URL [https://ai-realtor.fly.dev]: " input_url
        API_URL=${input_url:-https://ai-realtor.fly.dev}
    fi
fi

echo ""
echo "Using API URL: $API_URL"
echo ""

# Create/update skill directory
SKILLS_DIR="$HOME/.nanobot/workspace/skills/ai-realtor"
mkdir -p "$SKILLS_DIR"
echo "✅ Skills directory: $SKILLS_DIR"

# Set environment variable in shell profile
SHELL_PROFILE="$HOME/.bashrc"
if [ -n "$ZSH_VERSION" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
fi

# Check if already configured
if grep -q "AI_REALTOR_API_URL" "$SHELL_PROFILE" 2>/dev/null; then
    echo "📝 Environment variable already in $SHELL_PROFILE"
    read -p "Update it? [y/N]: " update_profile
    if [[ "$update_profile" =~ ^[Yy]$ ]]; then
        # Remove old entries
        sed -i.bak '/AI_REALTOR_API_URL/d' "$SHELL_PROFILE"
        # Add new entry
        echo "" >> "$SHELL_PROFILE"
        echo "# AI Realtor API Configuration" >> "$SHELL_PROFILE"
        echo "export AI_REALTOR_API_URL=\"$API_URL\"" >> "$SHELL_PROFILE"
        echo "✅ Updated $SHELL_PROFILE"
    fi
else
    echo "" >> "$SHELL_PROFILE"
    echo "# AI Realtor API Configuration" >> "$SHELL_PROFILE"
    echo "export AI_REALTOR_API_URL=\"$API_URL\"" >> "$SHELL_PROFILE"
    echo "✅ Added to $SHELL_PROFILE"
fi

# Export for current session
export AI_REALTOR_API_URL="$API_URL"

# Test connection
echo ""
echo "🔍 Testing API connection..."
if curl -s "${API_URL}/properties/" > /dev/null 2>&1; then
    echo "✅ API is accessible!"
else
    echo "⚠️  Warning: Could not reach API at $API_URL"
    echo "   You may need to update this URL later"
fi

# Install wrapper script
mkdir -p ~/.local/bin
cat > ~/.local/bin/ai-realtor-api << 'WRAPPER_EOF'
#!/bin/bash
AI_REALTOR_API_URL="${AI_REALTOR_API_URL:-https://ai-realtor.fly.dev}"
if [[ "$1" == /* ]]; then
    curl "${AI_REALTOR_API_URL}$@"
else
    cmd=$(echo "$@" | sed "s|https://ai-realtor.fly.dev|${AI_REALTOR_API_URL}|g")
    eval "$cmd"
fi
WRAPPER_EOF

chmod +x ~/.local/bin/ai-realtor-api

# Add to PATH if not already
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "" >> "$SHELL_PROFILE"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_PROFILE"
    echo "✅ Added ~/.local/bin to PATH"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Source your shell profile:"
echo "     source $SHELL_PROFILE"
echo ""
echo "  2. Restart nanobot:"
echo "     nanobot restart"
echo ""
echo "  3. Test the skill:"
echo "     curl \$AI_REALTOR_API_URL/properties/ | jq '.'"
echo ""
echo "Configuration:"
echo "  API URL: $API_URL"
echo "  Env var: \$AI_REALTOR_API_URL"
echo "  Wrapper: ~/.local/bin/ai-realtor-api"
echo ""
