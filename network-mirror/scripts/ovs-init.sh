#!/bin/bash
set -e

# OVS Network Infrastructure Initialization Script
# Purpose: Set up OVS bridge and veth-pair ports for VPP network mirroring

# Configuration
BRIDGE_NAME="br-vpp"
SUBNET="10.0.1.0/24"
GATEWAY="10.0.1.1"

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

# Check if OVS is installed
check_ovs_installed() {
    if ! command -v ovs-vsctl &> /dev/null; then
        log_error "OVS not installed. Please install openvswitch first."
        exit 1
    fi
    log_info "OVS is installed"
}

# Create OVS bridge
create_bridge() {
    log_info "Creating OVS bridge: $BRIDGE_NAME"
    
    # Delete existing bridge if it exists
    ovs-vsctl --if-exists del-br $BRIDGE_NAME
    
    # Create new bridge
    ovs-vsctl add-br $BRIDGE_NAME
    
    log_info "Bridge $BRIDGE_NAME created successfully"
}

# Configure bridge IP address
configure_bridge_ip() {
    log_info "Configuring bridge IP: $GATEWAY"
    
    # Add IP address to bridge
    ip addr add $GATEWAY/24 dev $BRIDGE_NAME 2>/dev/null || true
    
    # Bring bridge up
    ip link set $BRIDGE_NAME up
    
    log_info "Bridge IP configured: $GATEWAY"
}

# Create veth-pair port
create_veth_port() {
    local port_name=$1
    local ip_addr=$2
    
    log_info "Creating veth port: $port_name (IP: $ip_addr)"
    
    # Create veth-pair (port_name and port_name-br)
    ip link add ${port_name} type veth peer name ${port_name}-br 2>/dev/null || {
        log_warn "Veth pair ${port_name} already exists, skipping creation"
        return
    }
    
    # Add bridge side to OVS bridge
    ovs-vsctl add-port $BRIDGE_NAME ${port_name}-br
    
    # Bring up both sides of veth-pair
    ip link set ${port_name} up
    ip link set ${port_name}-br up
    
    # Configure IP address on host side
    ip addr add ${ip_addr}/24 dev ${port_name} 2>/dev/null || true
    
    log_info "Veth port $port_name created and configured"
}

# Create all business ports
create_business_ports() {
    log_info "Creating business ports..."
    
    create_veth_port "veth-master" "10.0.1.10"
    create_veth_port "veth-vcc" "10.0.1.20"
    create_veth_port "veth-upf" "10.0.1.30"
    create_veth_port "veth-gen" "10.0.1.40"
    
    log_info "All business ports created"
}

# Create mirror port
create_mirror_port() {
    log_info "Creating mirror port"
    
    # Create internal mirror port
    ovs-vsctl add-port $BRIDGE_NAME mirror-port -- set Interface mirror-port type=internal
    
    # Bring up mirror port
    ip link set mirror-port up
    
    # Configure IP address for mirror port
    ip addr add 10.0.1.100/24 dev mirror-port 2>/dev/null || true
    
    log_info "Mirror port created and configured"
}

# Configure mirror rule
configure_mirror_rule() {
    log_info "Configuring mirror rule"
    
    # Create mirror rule that selects all traffic and outputs to mirror-port
    ovs-vsctl -- --id=@m create Mirror name=m0 \
        select-all=true output-port=mirror-port \
        -- set Bridge $BRIDGE_NAME mirrors=@m
    
    log_info "Mirror rule configured"
}

# Create analyzer port
create_analyzer_port() {
    log_info "Creating analyzer port"
    
    create_veth_port "veth-analyzer" "10.0.1.50"
    
    log_info "Analyzer port created"
}

# Display configuration
display_configuration() {
    log_info "OVS configuration completed successfully"
    log_info ""
    log_info "Bridge configuration:"
    ovs-vsctl show
    log_info ""
    log_info "Port statistics:"
    ovs-ofctl dump-ports $BRIDGE_NAME
    log_info ""
    log_info "Mirror configuration:"
    ovs-vsctl list Mirror
    log_info ""
    log_info "All ports are ready!"
}

# Verify configuration
verify_configuration() {
    log_info "Verifying configuration..."
    
    # Check bridge exists
    if ! ovs-vsctl br-exists $BRIDGE_NAME; then
        log_error "Bridge $BRIDGE_NAME does not exist"
        exit 1
    fi
    
    # Check all ports are UP
    local ports=("veth-master-br" "veth-vcc-br" "veth-upf-br" "veth-gen-br" "mirror-port" "veth-analyzer-br")
    for port in "${ports[@]}"; do
        if ! ovs-vsctl list-ports $BRIDGE_NAME | grep -q $port; then
            log_warn "Port $port not found in bridge"
        fi
    done
    
    # Check mirror rule exists
    if ! ovs-vsctl list Mirror | grep -q "m0"; then
        log_error "Mirror rule m0 not found"
        exit 1
    fi
    
    log_info "Configuration verified successfully"
}

# Main execution
main() {
    log_info "Starting OVS initialization..."
    log_info "Bridge: $BRIDGE_NAME"
    log_info "Subnet: $SUBNET"
    log_info "Gateway: $GATEWAY"
    log_info ""
    
    check_ovs_installed
    create_bridge
    configure_bridge_ip
    create_business_ports
    create_mirror_port
    configure_mirror_rule
    create_analyzer_port
    verify_configuration
    display_configuration
    
    log_info "OVS initialization completed successfully!"
}

# Run main function
main
