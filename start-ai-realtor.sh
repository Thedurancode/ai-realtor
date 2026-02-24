#!/bin/bash
# =============================================================================
# AI Realtor - Universal Starter Script
# =============================================================================
# This script detects your setup and starts AI Realtor with the best option:
# - SQLite Docker (recommended, easiest)
# - PostgreSQL Docker (for production)
# - Local Python (for development)
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}║   🏠 AI REALTOR - Universal Starter                      ║${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is available
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    echo -e "${GREEN}✓ Docker detected${NC}"

    # Ask user which setup they want
    echo ""
    echo "Choose your setup:"
    echo "  1) SQLite Docker (Recommended - easiest, zero config)"
    echo "  2) PostgreSQL Docker (Production-ready)"
    echo "  3) Local Python (Development)"
    echo ""
    read -p "Enter choice [1-3] (default: 1): " choice
    choice=${choice:-1}

    case $choice in
        1)
            echo ""
            echo -e "${BLUE}Starting SQLite Docker setup...${NC}"
            if [ -f docker-quick-start-sqlite.sh ]; then
                bash docker-quick-start-sqlite.sh
            else
                echo -e "${YELLOW}Quick start script not found. Using manual setup...${NC}"
                docker compose -f docker-compose.sqlite.yml up -d --build
            fi
            ;;
        2)
            echo ""
            echo -e "${BLUE}Starting PostgreSQL Docker setup...${NC}"
            docker compose up -d --build
            ;;
        3)
            echo ""
            echo -e "${YELLOW}Local Python setup requires manual configuration.${NC}"
            echo "Please follow the local development guide."
            exit 1
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac

# Check if Python is available (local dev)
elif command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python detected${NC}"
    echo -e "${YELLOW}Running local development setup...${NC}"
    echo ""
    echo "Note: Local development requires:"
    echo "  - PostgreSQL database running"
    echo "  - Virtual environment activated"
    echo "  - Dependencies installed"
    echo ""
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 -m uvicorn app.main:app --reload
    fi

else
    echo -e "${RED}❌ No suitable runtime found${NC}"
    echo ""
    echo "Please install one of the following:"
    echo "  • Docker (Recommended): https://docs.docker.com/get-docker/"
    echo "  • Python 3.11+: https://www.python.org/downloads/"
    exit 1
fi
