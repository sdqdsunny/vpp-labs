#!/bin/bash

# Run OVS initialization in Docker container
# This script sets up OVS infrastructure using Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "OVS Network Infrastructure Initialization"
echo "=========================================="
echo ""
echo "Project Directory: $PROJECT_DIR"
echo "Script Directory: $SCRIPT_DIR"
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "Step 1: Creating OVS initialization container..."
echo ""

# Run OVS initialization in a privileged container
docker run \
    --rm \
    --privileged \
    --network host \
    -v "$SCRIPT_DIR:/scripts:ro" \
    ubuntu:22.04 \
    bash -c "
        set -e
        echo 'Installing OVS...'
        apt-get update > /dev/null 2>&1
        apt-get install -y openvswitch-switch > /dev/null 2>&1
        
        echo 'Starting OVS services...'
        service openvswitch-switch start || true
        
        echo 'Running OVS initialization script...'
        bash /scripts/ovs-init.sh
    "

echo ""
echo "=========================================="
echo "OVS initialization completed successfully!"
echo "=========================================="
echo ""
echo "Verifying OVS configuration..."
echo ""

# Verify OVS is running on host
if command -v ovs-vsctl &> /dev/null; then
    echo "OVS Status:"
    ovs-vsctl show
else
    echo "Note: ovs-vsctl not found on host. OVS is running in Docker."
    echo "To verify configuration, run:"
    echo "  docker run --rm --privileged --network host ubuntu:22.04 bash -c 'apt-get update && apt-get install -y openvswitch-switch && ovs-vsctl show'"
fi

echo ""
echo "Network configuration:"
echo ""

# Try to show network configuration
if command -v ip &> /dev/null; then
    echo "Bridge interfaces:"
    ip addr show | grep -E "^[0-9]+:|inet " || true
else
    echo "Note: ip command not available"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
