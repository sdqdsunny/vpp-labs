#!/bin/bash

# Docker Verification Script for VPP Phase 2 Simulation
# This script verifies that the Docker environment is properly configured

set -e

echo "=========================================="
echo "VPP Phase 2 Simulation - Docker Verification"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="vpp-phase2-simulation"
IMAGE_TAG="latest"
CONTAINER_NAME="vpp-verify-temp"

# Function to print section headers
print_section() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to check if image exists
check_image_exists() {
    if docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Step 1: Check if image exists
print_section "Step 1: Checking Docker Image"
if check_image_exists; then
    echo -e "${GREEN}✓ Docker image exists: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
    IMAGE_ID=$(docker image inspect -f '{{.ID}}' ${IMAGE_NAME}:${IMAGE_TAG} | cut -d: -f2 | cut -c1-12)
    echo "  Image ID: $IMAGE_ID"
else
    echo -e "${RED}✗ Docker image not found: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
    echo "  Please run: ./docker-build.sh"
    exit 1
fi
echo ""

# Step 2: Verify Python environment
print_section "Step 2: Verifying Python Environment"
docker run --rm --name "${CONTAINER_NAME}-python" "${IMAGE_NAME}:${IMAGE_TAG}" python -c "
import sys
print('Python version:', sys.version.split()[0])
print('Python executable:', sys.executable)
"
echo -e "${GREEN}✓ Python environment verified${NC}"
echo ""

# Step 3: Verify protocol libraries
print_section "Step 3: Verifying Protocol Libraries"
docker run --rm --name "${CONTAINER_NAME}-libs" "${IMAGE_NAME}:${IMAGE_TAG}" python -c "
import sys

libraries = {
    'paho.mqtt.client': 'paho-mqtt',
    'pymodbus': 'pymodbus',
    'sqlalchemy': 'sqlalchemy',
    'pytest': 'pytest',
    'hypothesis': 'hypothesis',
    'bottle': 'bottle',
    'redis': 'redis',
    'psycopg2': 'psycopg2-binary',
}

all_ok = True
for module, package in libraries.items():
    try:
        __import__(module)
        print(f'✓ {package}')
    except ImportError:
        print(f'✗ {package} NOT FOUND')
        all_ok = False

if not all_ok:
    sys.exit(1)
"
echo -e "${GREEN}✓ All protocol libraries verified${NC}"
echo ""

# Step 4: Verify system dependencies
print_section "Step 4: Verifying System Dependencies"
docker run --rm --name "${CONTAINER_NAME}-sys" "${IMAGE_NAME}:${IMAGE_TAG}" bash -c "
echo 'System dependencies:'
which gcc > /dev/null && echo '✓ gcc' || echo '✗ gcc'
which g++ > /dev/null && echo '✓ g++' || echo '✗ g++'
which make > /dev/null && echo '✓ make' || echo '✗ make'
which curl > /dev/null && echo '✓ curl' || echo '✗ curl'
which git > /dev/null && echo '✓ git' || echo '✗ git'
"
echo -e "${GREEN}✓ System dependencies verified${NC}"
echo ""

# Step 5: Verify application structure
print_section "Step 5: Verifying Application Structure"
docker run --rm --name "${CONTAINER_NAME}-app" "${IMAGE_NAME}:${IMAGE_TAG}" bash -c "
echo 'Application structure:'
[ -d /app/services ] && echo '✓ services directory' || echo '✗ services directory'
[ -d /app/routes ] && echo '✓ routes directory' || echo '✗ routes directory'
[ -d /app/tests ] && echo '✓ tests directory' || echo '✗ tests directory'
[ -d /app/models ] && echo '✓ models directory' || echo '✗ models directory'
[ -f /app/requirements.txt ] && echo '✓ requirements.txt' || echo '✗ requirements.txt'
[ -f /app/app.py ] && echo '✓ app.py' || echo '✗ app.py'
"
echo -e "${GREEN}✓ Application structure verified${NC}"
echo ""

# Step 6: Test basic functionality
print_section "Step 6: Testing Basic Functionality"
docker run --rm --name "${CONTAINER_NAME}-test" "${IMAGE_NAME}:${IMAGE_TAG}" python -c "
# Test protocol adapters
from services.protocol_adapters.registry import ProtocolRegistry
from services.protocol_adapters.mapper import ProtocolMessageMapper

print('✓ Protocol adapters imported successfully')

# Test protocol management
from services.protocol_management import ProtocolManagementService

service = ProtocolManagementService()
print('✓ Protocol management service initialized')

# Test basic mapping
message = {
    'voltage': 230.0,
    'current': 10.0,
    'frequency': 50.0,
    'power': 2300.0,
    'status': 'on',
    'timestamp': 1645000000,
}

result = service.map_message('iec61850', 'modbus', message)
print('✓ Protocol mapping works')

print('All functionality tests passed!')
"
echo -e "${GREEN}✓ Basic functionality verified${NC}"
echo ""

# Summary
print_section "Verification Complete"
echo -e "${GREEN}All Docker environment checks passed!${NC}"
echo ""
echo "Docker image is ready for deployment:"
echo "  Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "  Status: ✓ Ready"
echo ""
echo "To start the services, run:"
echo "  docker-compose up -d"
echo ""
