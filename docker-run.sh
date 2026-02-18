#!/bin/bash

# VPP System Docker Run Script
# This script builds and runs the VPP system in Docker with proper cleanup

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         VPP 虚拟电厂系统 - Docker 启动脚本                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
IMAGE_NAME="vpp-system"
IMAGE_TAG="latest"
CONTAINER_NAME="vpp-container"
PORT_API="8080"
PORT_SECONDARY="8081"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

print_status "Docker found: $(docker --version)"
echo ""

# Step 1: Build Docker image
print_status "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "This may take a few minutes..."
echo ""

if docker build -t ${IMAGE_NAME}:${IMAGE_TAG} vpp-phase2-simulation/; then
    print_success "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    exit 1
fi

echo ""

# Step 2: Check if port is available
print_status "Checking if port ${PORT_API} is available..."

if lsof -Pi :${PORT_API} -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port ${PORT_API} is already in use"
    read -p "Do you want to use a different port? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter port number: " PORT_API
    fi
fi

echo ""

# Step 3: Run Docker container
print_status "Starting Docker container..."
print_status "Container will be automatically removed after exit (--rm flag)"
echo ""

docker run --rm \
    --name ${CONTAINER_NAME} \
    -p ${PORT_API}:8080 \
    -p ${PORT_SECONDARY}:8081 \
    -e PYTHONUNBUFFERED=1 \
    -e API_PORT=8080 \
    -v $(pwd)/vpp-phase2-simulation/logs:/app/logs \
    ${IMAGE_NAME}:${IMAGE_TAG}

print_status "Container stopped and removed"
echo ""

# Step 4: Cleanup message
print_success "Docker container has been cleaned up (--rm parameter used)"
print_status "Verifying container is removed..."

if docker ps -a | grep -q ${CONTAINER_NAME}; then
    print_warning "Container still exists in docker ps -a"
else
    print_success "Container successfully removed from docker ps -a"
fi

echo ""
print_success "Done!"
