#!/bin/bash
set -e

# OVS Network Infrastructure Cleanup Script
# Purpose: Clean up OVS bridge and veth-pair ports

BRIDGE_NAME="br-vpp"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Delete bridge
delete_bridge() {
    log_info "Deleting OVS bridge: $BRIDGE_NAME"
    
    if ovs-vsctl br-exists $BRIDGE_NAME; then
        ovs-vsctl --if-exists del-br $BRIDGE_NAME
        log_info "Bridge $BRIDGE_NAME deleted"
    else
        log_warn "Bridge $BRIDGE_NAME does not exist"
    fi
}

# Delete veth-pair ports
delete_veth_ports() {
    log_info "Deleting veth-pair ports..."
    
    local ports=("veth-master" "veth-vcc" "veth-upf" "veth-gen" "veth-analyzer")
    
    for port in "${ports[@]}"; do
        if ip link show $port &> /dev/null; then
            ip link del $port 2>/dev/null || log_warn "Failed to delete $port"
            log_info "Deleted veth port: $port"
        else
            log_warn "Veth port $port does not exist"
        fi
    done
}

# Verify cleanup
verify_cleanup() {
    log_info "Verifying cleanup..."
    
    # Check bridge is deleted
    if ovs-vsctl br-exists $BRIDGE_NAME 2>/dev/null; then
        log_error "Bridge $BRIDGE_NAME still exists"
        exit 1
    fi
    
    # Check veth ports are deleted
    local ports=("veth-master" "veth-vcc" "veth-upf" "veth-gen" "veth-analyzer")
    for port in "${ports[@]}"; do
        if ip link show $port &> /dev/null; then
            log_warn "Veth port $port still exists"
        fi
    done
    
    log_info "Cleanup verified successfully"
}

# Main execution
main() {
    log_info "Starting OVS cleanup..."
    log_info ""
    
    delete_bridge
    delete_veth_ports
    verify_cleanup
    
    log_info ""
    log_info "OVS cleanup completed successfully!"
}

# Run main function
main
