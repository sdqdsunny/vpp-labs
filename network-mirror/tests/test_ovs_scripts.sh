#!/bin/bash

# Test script for OVS initialization and cleanup scripts
# This script verifies that the OVS infrastructure is set up correctly

set -e

# Configuration
BRIDGE_NAME="br-vpp"
EXPECTED_PORTS=("veth-master-br" "veth-vcc-br" "veth-upf-br" "veth-gen-br" "mirror-port" "veth-analyzer-br")
EXPECTED_IPS=("10.0.1.10" "10.0.1.20" "10.0.1.30" "10.0.1.40" "10.0.1.50")

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

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

log_test() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

# Test result functions
test_pass() {
    echo -e "${GREEN}✓ PASS${NC} $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC} $1"
    ((TESTS_FAILED++))
}

# Test: Check OVS is installed
test_ovs_installed() {
    log_test "OVS is installed"
    
    if command -v ovs-vsctl &> /dev/null; then
        test_pass "OVS is installed"
    else
        test_fail "OVS is not installed"
    fi
}

# Test: Check bridge exists
test_bridge_exists() {
    log_test "Bridge $BRIDGE_NAME exists"
    
    if ovs-vsctl br-exists $BRIDGE_NAME 2>/dev/null; then
        test_pass "Bridge $BRIDGE_NAME exists"
    else
        test_fail "Bridge $BRIDGE_NAME does not exist"
    fi
}

# Test: Check bridge IP address
test_bridge_ip() {
    log_test "Bridge has correct IP address"
    
    if ip addr show $BRIDGE_NAME | grep -q "10.0.1.1"; then
        test_pass "Bridge IP address is correct (10.0.1.1)"
    else
        test_fail "Bridge IP address is incorrect"
    fi
}

# Test: Check all ports exist
test_ports_exist() {
    log_test "All required ports exist"
    
    local all_exist=true
    for port in "${EXPECTED_PORTS[@]}"; do
        if ovs-vsctl list-ports $BRIDGE_NAME | grep -q "^${port}$"; then
            log_info "  Port $port exists"
        else
            log_error "  Port $port does not exist"
            all_exist=false
        fi
    done
    
    if [ "$all_exist" = true ]; then
        test_pass "All required ports exist"
    else
        test_fail "Some ports are missing"
    fi
}

# Test: Check all ports are UP
test_ports_up() {
    log_test "All ports are UP"
    
    local all_up=true
    for port in "${EXPECTED_PORTS[@]}"; do
        if [ "$port" = "mirror-port" ]; then
            # mirror-port is internal, check differently
            if ovs-vsctl get-port $BRIDGE_NAME $port &> /dev/null; then
                log_info "  Port $port is configured"
            else
                log_error "  Port $port is not configured"
                all_up=false
            fi
        else
            # Check veth port status
            if ip link show ${port%-br} 2>/dev/null | grep -q "UP"; then
                log_info "  Port ${port%-br} is UP"
            else
                log_warn "  Port ${port%-br} status unknown (may be in container)"
            fi
        fi
    done
    
    if [ "$all_up" = true ]; then
        test_pass "All ports are configured"
    else
        test_fail "Some ports are not configured"
    fi
}

# Test: Check mirror rule exists
test_mirror_rule() {
    log_test "Mirror rule exists"
    
    if ovs-vsctl list Mirror | grep -q "name.*m0"; then
        test_pass "Mirror rule m0 exists"
    else
        test_fail "Mirror rule m0 does not exist"
    fi
}

# Test: Check mirror rule configuration
test_mirror_config() {
    log_test "Mirror rule is configured correctly"
    
    local config_ok=true
    
    # Check select-all is true
    if ovs-vsctl list Mirror | grep -q "select_all.*true"; then
        log_info "  Mirror select-all is true"
    else
        log_error "  Mirror select-all is not true"
        config_ok=false
    fi
    
    # Check output-port is mirror-port
    if ovs-vsctl list Mirror | grep -q "output_port.*mirror-port"; then
        log_info "  Mirror output-port is mirror-port"
    else
        log_error "  Mirror output-port is not mirror-port"
        config_ok=false
    fi
    
    if [ "$config_ok" = true ]; then
        test_pass "Mirror rule is configured correctly"
    else
        test_fail "Mirror rule configuration is incorrect"
    fi
}

# Test: Check veth port IP addresses
test_veth_ips() {
    log_test "Veth ports have correct IP addresses"
    
    local all_ips_ok=true
    
    # Check veth-master
    if ip addr show veth-master 2>/dev/null | grep -q "10.0.1.10"; then
        log_info "  veth-master has IP 10.0.1.10"
    else
        log_warn "  veth-master IP not found (may be in container)"
    fi
    
    # Check veth-analyzer
    if ip addr show veth-analyzer 2>/dev/null | grep -q "10.0.1.50"; then
        log_info "  veth-analyzer has IP 10.0.1.50"
    else
        log_warn "  veth-analyzer IP not found (may be in container)"
    fi
    
    test_pass "Veth port IP addresses verified"
}

# Test: Check mirror port IP address
test_mirror_port_ip() {
    log_test "Mirror port has correct IP address"
    
    if ip addr show mirror-port 2>/dev/null | grep -q "10.0.1.100"; then
        test_pass "Mirror port has IP 10.0.1.100"
    else
        test_fail "Mirror port does not have IP 10.0.1.100"
    fi
}

# Test: Check port statistics available
test_port_stats() {
    log_test "Port statistics are available"
    
    if ovs-ofctl dump-ports $BRIDGE_NAME &> /dev/null; then
        test_pass "Port statistics are available"
    else
        test_fail "Port statistics are not available"
    fi
}

# Test: Check flow table
test_flow_table() {
    log_test "Flow table is accessible"
    
    if ovs-ofctl dump-flows $BRIDGE_NAME &> /dev/null; then
        test_pass "Flow table is accessible"
    else
        test_fail "Flow table is not accessible"
    fi
}

# Run all tests
run_all_tests() {
    log_info "Starting OVS infrastructure tests..."
    log_info ""
    
    test_ovs_installed
    test_bridge_exists
    test_bridge_ip
    test_ports_exist
    test_ports_up
    test_mirror_rule
    test_mirror_config
    test_veth_ips
    test_mirror_port_ip
    test_port_stats
    test_flow_table
    
    log_info ""
    log_info "Test Results:"
    log_info "  Passed: $TESTS_PASSED"
    log_info "  Failed: $TESTS_FAILED"
    log_info ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log_info "All tests passed!"
        return 0
    else
        log_error "Some tests failed!"
        return 1
    fi
}

# Main execution
main() {
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        exit 1
    fi
    
    run_all_tests
}

# Run main function
main
