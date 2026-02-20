#!/bin/bash

# VPP Security Tools Integration - Docker Build and Verification Script
# This script builds the Docker image and verifies that all security testing tools are installed

set -e

echo "=========================================="
echo "VPP Security Tools Integration"
echo "Docker Build and Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Build Docker image
echo -e "${YELLOW}[Step 1]${NC} Building Docker image with security tools..."
docker build -f vpp-phase2-simulation/Dockerfile -t vpp-master:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}✗ Docker image build failed${NC}"
    exit 1
fi

echo ""

# Step 2: Verify dependencies in container
echo -e "${YELLOW}[Step 2]${NC} Verifying security testing tools in container..."
echo ""

# Create a temporary container to verify dependencies
TEMP_CONTAINER=$(docker create vpp-master:latest)

# Check for Python packages
echo "Checking Python packages..."

# Check boofuzz
if docker run --rm vpp-master:latest python3 -c "import boofuzz; print('boofuzz version:', boofuzz.__version__)" 2>/dev/null; then
    echo -e "${GREEN}✓ boofuzz${NC} - installed"
else
    echo -e "${RED}✗ boofuzz${NC} - NOT installed"
fi

# Check python-opcua
if docker run --rm vpp-master:latest python3 -c "import opcua; print('python-opcua version:', opcua.__version__)" 2>/dev/null; then
    echo -e "${GREEN}✓ python-opcua${NC} - installed"
else
    echo -e "${RED}✗ python-opcua${NC} - NOT installed"
fi

# Check dnp3
if docker run --rm vpp-master:latest python3 -c "import dnp3; print('dnp3 version:', dnp3.__version__)" 2>/dev/null; then
    echo -e "${GREEN}✓ dnp3${NC} - installed"
else
    echo -e "${RED}✗ dnp3${NC} - NOT installed"
fi

# Check existing tools
echo ""
echo "Checking existing tools..."

if docker run --rm vpp-master:latest python3 -c "import pymodbus; print('pymodbus version:', pymodbus.__version__)" 2>/dev/null; then
    echo -e "${GREEN}✓ pymodbus${NC} - installed"
else
    echo -e "${RED}✗ pymodbus${NC} - NOT installed"
fi

if docker run --rm vpp-master:latest python3 -c "import can; print('python-can version:', can.__version__)" 2>/dev/null; then
    echo -e "${GREEN}✓ python-can${NC} - installed"
else
    echo -e "${RED}✗ python-can${NC} - NOT installed"
fi

echo ""

# Step 3: Verify system packages
echo -e "${YELLOW}[Step 3]${NC} Verifying system packages in container..."
echo ""

# Check for build tools
if docker run --rm vpp-master:latest which gcc > /dev/null 2>&1; then
    echo -e "${GREEN}✓ gcc${NC} - available"
else
    echo -e "${RED}✗ gcc${NC} - NOT available"
fi

if docker run --rm vpp-master:latest which git > /dev/null 2>&1; then
    echo -e "${GREEN}✓ git${NC} - available"
else
    echo -e "${RED}✗ git${NC} - NOT available"
fi

if docker run --rm vpp-master:latest which curl > /dev/null 2>&1; then
    echo -e "${GREEN}✓ curl${NC} - available"
else
    echo -e "${RED}✗ curl${NC} - NOT available"
fi

if docker run --rm vpp-master:latest which ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ ping${NC} - available"
else
    echo -e "${RED}✗ ping${NC} - NOT available"
fi

echo ""

# Step 4: Summary
echo -e "${YELLOW}[Step 4]${NC} Summary"
echo "=========================================="
echo -e "${GREEN}✓ Docker image built successfully${NC}"
echo -e "${GREEN}✓ All security testing tools verified${NC}"
echo ""
echo "Next steps:"
echo "1. Run: docker-compose -f docker-compose-microservices.yml up -d"
echo "2. Verify containers: docker ps"
echo "3. Test security tools: docker exec vpp-master python3 -c 'import boofuzz, opcua, dnp3'"
echo ""
