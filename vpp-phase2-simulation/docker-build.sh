#!/bin/bash

# Docker Build and Verification Script for VPP Phase 2 Simulation
# This script builds the Docker image and verifies the compilation environment

set -e

echo "=========================================="
echo "VPP Phase 2 Simulation - Docker Build"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="vpp-phase2-simulation"
IMAGE_TAG="latest"
DOCKERFILE="Dockerfile"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Step 1: Check Docker installation
echo -e "${YELLOW}[1/5] Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"
echo "  Version: $(docker --version)"
echo ""

# Step 2: Check Docker Compose installation
echo -e "${YELLOW}[2/5] Checking Docker Compose installation...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}ERROR: Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is installed${NC}"
echo "  Version: $(docker-compose --version)"
echo ""

# Step 3: Build Docker image
echo -e "${YELLOW}[3/5] Building Docker image...${NC}"
echo "  Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "  Dockerfile: ${DOCKERFILE}"
echo ""

if docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" -f "${DOCKERFILE}" .; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}ERROR: Failed to build Docker image${NC}"
    exit 1
fi
echo ""

# Step 4: Verify image
echo -e "${YELLOW}[4/5] Verifying Docker image...${NC}"
if docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker image verified${NC}"
    echo "  Image ID: $(docker image inspect -f '{{.ID}}' ${IMAGE_NAME}:${IMAGE_TAG} | cut -d: -f2 | cut -c1-12)"
    echo "  Size: $(docker image inspect -f '{{.Size}}' ${IMAGE_NAME}:${IMAGE_TAG} | numfmt --to=iec 2>/dev/null || echo 'N/A')"
else
    echo -e "${RED}ERROR: Failed to verify Docker image${NC}"
    exit 1
fi
echo ""

# Step 5: Verify compilation environment
echo -e "${YELLOW}[5/5] Verifying compilation environment...${NC}"
echo "  Checking Python dependencies..."

# Create a temporary container to verify dependencies
TEMP_CONTAINER=$(docker create "${IMAGE_NAME}:${IMAGE_TAG}" python -c "
import sys
print('Python version:', sys.version)

# Check protocol libraries
try:
    import paho.mqtt.client
    print('✓ paho-mqtt installed')
except ImportError:
    print('✗ paho-mqtt NOT installed')
    sys.exit(1)

try:
    import pymodbus
    print('✓ pymodbus installed')
except ImportError:
    print('✗ pymodbus NOT installed')
    sys.exit(1)

try:
    import sqlalchemy
    print('✓ sqlalchemy installed')
except ImportError:
    print('✗ sqlalchemy NOT installed')
    sys.exit(1)

try:
    import pytest
    print('✓ pytest installed')
except ImportError:
    print('✗ pytest NOT installed')
    sys.exit(1)

print('All dependencies verified!')
")

if docker start -a "$TEMP_CONTAINER" 2>&1 | tee /tmp/docker_verify.log; then
    echo -e "${GREEN}✓ Compilation environment verified${NC}"
    docker rm "$TEMP_CONTAINER" > /dev/null 2>&1
else
    echo -e "${RED}ERROR: Failed to verify compilation environment${NC}"
    docker rm "$TEMP_CONTAINER" > /dev/null 2>&1
    exit 1
fi
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}Docker Build Completed Successfully!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start services: docker-compose up -d"
echo "  2. Check logs: docker-compose logs -f vpp-api"
echo "  3. Run tests: docker-compose exec vpp-api pytest tests/"
echo "  4. Stop services: docker-compose down"
echo ""
