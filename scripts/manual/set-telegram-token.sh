#!/bin/bash
# Easy Telegram bot token setup script
# Usage: ./scripts/manual/set-telegram-token.sh YOUR_TOKEN_HERE

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🤖 Telegram Bot Token Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if token provided
if [ -z "$1" ]; then
    # Try to use existing token from .env.bak
    if [ -f "$PROJECT_ROOT/.env.bak" ]; then
        TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "$PROJECT_ROOT/.env.bak" 2>/dev/null | cut -d'=' -f2)
        if [ -n "$TOKEN" ]; then
            echo -e "${GREEN}✓ Using existing token from .env.bak${NC}"
            echo -e "${YELLOW}Token: ${NC}${TOKEN:0:20}...${NC}"
        else
            echo -e "${YELLOW}No TELEGRAM_BOT_TOKEN found in .env.bak${NC}"
            echo ""
            echo -e "${YELLOW}Usage: ./set-telegram-token.sh YOUR_TOKEN_HERE${NC}"
            echo ""
            echo "Example: ./set-telegram-token.sh 8392020900:AAEKlrigz4_B35slxdJpBIApSrotEf3cei"
            exit 1
        fi
    else
        echo -e "${YELLOW}No .env.bak file found${NC}"
        echo ""
        echo -e "${YELLOW}Usage: ./set-telegram-token.sh YOUR_TOKEN_HERE${NC}"
        echo ""
        echo "Example: ./set-telegram-token.sh 8392020900:AAEKlrigz4_B35slxdJpBIApSrotEf3cei"
        exit 1
    fi
else
    TOKEN="$1"
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}Token received: ${NC}${TOKEN:0:20}...${NC}"
echo ""

# Check if .env exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}✓ .env file exists${NC}"

    # Check if TELEGRAM_BOT_TOKEN already exists
    if grep -q "TELEGRAM_BOT_TOKEN" "$PROJECT_ROOT/.env" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  TELEGRAM_BOT_TOKEN already exists${NC}"

        # Ask to update
        read -p "$(echo -e "${YELLOW}Update existing token? (y/N): ${NC})" -n 1 -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}Cancelled. Token not updated.${NC}"
            exit 0
        fi
    fi
else
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo -e "${YELLOW}→ Creating new .env file...${NC}"
fi

# Update or create .env file
if grep -q "TELEGRAM_BOT_TOKEN" "$PROJECT_ROOT/.env" 2>/dev/null; then
    # Update existing token
    sed -i '' "s/^TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=$TOKEN/" "$PROJECT_ROOT/.env"
    echo -e "${GREEN}✓ Updated TELEGRAM_BOT_TOKEN in .env${NC}"
else
    # Add new token
    echo "" >> "$PROJECT_ROOT/.env"
    echo "TELEGRAM_BOT_TOKEN=$TOKEN" >> "$PROJECT_ROOT/.env"
    echo -e "${GREEN}✓ Added TELEGRAM_BOT_TOKEN to .env${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Telegram token configured!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Restart AI Realtor server"
echo "2. Test bot in Telegram"
echo ""
echo -e "${YELLOW}Restart command:${NC}"
echo "pkill -f 'uvicorn app.main:app' && source venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
