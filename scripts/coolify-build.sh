#!/bin/bash

# =============================================================================
# AI REALTOR + NANOBOT - Coolify Build Script
# =============================================================================
# This script builds and pushes Docker images to a container registry
# for deployment on Coolify
#
# Usage:
#   ./coolify-build.sh docker.io your-username
#   ./coolify-build.sh ghcr.io your-username
#   ./coolify-build.sh registry.gitlab.com your-username
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
REGISTRY=${1:-"docker.io"}
USERNAME=${2:-"your-username"}

echo -e "${GREEN}=== AI Realtor + Nanobot Coolify Build Script ===${NC}"
echo ""
echo "Registry: $REGISTRY"
echo "Username: $USERNAME"
echo ""

# Validate registry
if [[ ! "$REGISTRY" =~ ^(docker\.io|ghcr\.io|registry\.gitlab\.com)$ ]]; then
    echo -e "${YELLOW}Warning: Using custom registry: $REGISTRY${NC}"
    echo "Supported registries: docker.io, ghcr.io, registry.gitlab.com"
    echo ""
fi

# Check if user is logged in
echo -e "${YELLOW}Checking Docker login status...${NC}"
if ! docker info | grep -q "Username: $USERNAME"; then
    echo -e "${RED}Not logged in as $USERNAME${NC}"
    echo "Please login first:"
    echo "  docker login $REGISTRY -u $USERNAME"
    exit 1
fi

echo -e "${GREEN}✓ Logged in as $USERNAME${NC}"
echo ""

# =============================================================================
# Build AI Realtor SQLite Image
# =============================================================================
echo -e "${YELLOW}Building AI Realtor SQLite image...${NC}"
docker build -f Dockerfile.sqlite \
    -t $REGISTRY/$USERNAME/ai-realtor-sqlite:latest \
    -t $REGISTRY/$USERNAME/ai-realtor-sqlite:v$(date +%Y%m%d) \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ AI Realtor image built successfully${NC}"
else
    echo -e "${RED}✗ AI Realtor image build failed${NC}"
    exit 1
fi

echo ""

# =============================================================================
# Build Nanobot Image
# =============================================================================
echo -e "${YELLOW}Building Nanobot Gateway image...${NC}"
cd nanobot
docker build \
    -t $REGISTRY/$USERNAME/nanobot-gateway:latest \
    -t $REGISTRY/$USERNAME/nanobot-gateway:v$(date +%Y%m%d) \
    .
cd ..

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Nanobot image built successfully${NC}"
else
    echo -e "${RED}✗ Nanobot image build failed${NC}"
    exit 1
fi

echo ""

# =============================================================================
# Push Images to Registry
# =============================================================================
echo -e "${YELLOW}Pushing images to $REGISTRY...${NC}"
echo ""

# Push AI Realtor
echo "Pushing ai-realtor-sqlite:latest..."
docker push $REGISTRY/$USERNAME/ai-realtor-sqlite:latest

echo "Pushing ai-realtor-sqlite:v$(date +%Y%m%d)..."
docker push $REGISTRY/$USERNAME/ai-realtor-sqlite:v$(date +%Y%m%d)

echo ""

# Push Nanobot
echo "Pushing nanobot-gateway:latest..."
docker push $REGISTRY/$USERNAME/nanobot-gateway:latest

echo "Pushing nanobot-gateway:v$(date +%Y%m%d)..."
docker push $REGISTRY/$USERNAME/nanobot-gateway:v$(date +%Y%m%d)

echo ""
echo -e "${GREEN}=== Build Complete! ===${NC}"
echo ""
echo "Images pushed to $REGISTRY/$USERNAME:"
echo "  • ai-realtor-sqlite:latest"
echo "  • nanobot-gateway:latest"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. In Coolify, create a new Docker Compose service"
echo "  2. Use docker-compose.coolify.yml"
echo "  3. Update image references in compose file:"
echo "     - image: $REGISTRY/$USERNAME/ai-realtor-sqlite:latest"
echo "     - image: $REGISTRY/$USERNAME/nanobot-gateway:latest"
echo "  4. Configure environment variables in Coolify UI"
echo "  5. Deploy!"
echo ""
