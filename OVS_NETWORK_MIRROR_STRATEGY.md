# OVS Network Traffic Mirroring - Deployment Strategy

**Date**: 2026-02-17  
**Status**: Strategy Finalized  
**Decision**: Docker Native Networking (macOS) + OVS Ready (Linux)

---

## Executive Summary

The OVS Network Traffic Mirroring system will use **Docker native bridge networking** for macOS development and testing, with **OVS support prepared for future Linux production deployment**.

This approach provides:
- ✅ Immediate functionality on macOS without kernel module requirements
- ✅ Full protocol analysis capabilities for development
- ✅ Seamless migration path to OVS on Linux
- ✅ No code changes needed when switching platforms

---

## Architecture Decision

### macOS/Development (Current)

**Network Stack**:
- Docker bridge network (vpp-net)
- Subnet: 10.0.1.0/24
- Gateway: 10.0.1.1
- All containers connected via Docker network

**Components**:
```
vpp-master (10.0.1.10)
    ↓
vpp-vcc (10.0.1.20)
vpp-upf (10.0.1.30)
vpp-gen (10.0.1.40)
    ↓
vpp-analyzer (10.0.1.50) ← Captures eth0 traffic
    ↓
/pcap/*.pcap (Protocol analysis)
```

**Advantages**:
- Works on macOS without OVS kernel module
- No special host configuration needed
- Docker Compose handles all networking
- Analyzer captures all inter-container traffic
- Full protocol identification and pcap generation

**Limitations**:
- No explicit traffic mirroring (but Docker network captures all traffic)
- No OVS-specific features (VLAN, advanced QoS)
- Performance limited by Docker network bridge

### Linux/Production (Future)

**Network Stack**:
- OVS bridge (br-vpp)
- Veth-pair ports for each component
- Explicit traffic mirroring to mirror-port
- Subnet: 10.0.1.0/24
- Gateway: 10.0.1.1

**Components**:
```
OVS Bridge (br-vpp)
├─ veth-master-br (10.0.1.10)
├─ veth-vcc-br (10.0.1.20)
├─ veth-upf-br (10.0.1.30)
├─ veth-gen-br (10.0.1.40)
├─ mirror-port (internal, 10.0.1.100)
└─ veth-analyzer-br (10.0.1.50)

Mirror Rule: select-all → mirror-port
```

**Advantages**:
- Explicit traffic mirroring at switch level
- OVS-specific features (VLAN, QoS, statistics)
- Better performance for high-volume traffic
- Production-grade network infrastructure
- Advanced traffic analysis capabilities

**Preparation**:
- OVS scripts already implemented (`ovs-init.sh`, `ovs-cleanup.sh`)
- Analyzer code works with both Docker network and OVS
- Docker Compose can be updated for OVS deployment
- Documentation includes Linux deployment guide

---

## Implementation Status

### ✅ Completed

1. **Protocol Analyzer** (`network-mirror/analyzer/main.py`)
   - ProtocolIdentifier class
   - PacketAnalyzer class
   - Pcap file generation
   - Real-time statistics
   - Support for IEC61850, Modbus, DNP3, MQTT

2. **Docker Integration** (`network-mirror/docker-compose.yml`)
   - All services defined
   - Docker bridge network configured
   - Health checks implemented
   - Volume mounts for logs and pcap

3. **OVS Scripts** (for future Linux deployment)
   - `network-mirror/scripts/ovs-init.sh`
   - `network-mirror/scripts/ovs-cleanup.sh`
   - Complete OVS infrastructure setup

### 📋 Remaining Tasks

1. **Task 4**: Build and test Docker images
2. **Task 5**: Integration tests
3. **Task 6**: Property-based tests
4. **Task 7**: Documentation
5. **Task 8**: Final verification

---

## Migration Path: macOS → Linux

When deploying on Linux, the migration is straightforward:

### Step 1: Prepare Linux Host
```bash
# Install OVS
sudo apt-get install openvswitch-switch

# Run OVS initialization
sudo bash network-mirror/scripts/ovs-init.sh
```

### Step 2: Update Docker Compose (Optional)
- Change network mode from bridge to host
- Update CAPTURE_INTERFACE from eth0 to mirror-port
- Analyzer code remains unchanged

### Step 3: Deploy
```bash
docker-compose up -d
```

**Result**: Same analyzer functionality, but with OVS-based traffic mirroring

---

## Key Design Decisions

### 1. Docker Native Networking (macOS)
**Why**: 
- OVS requires Linux kernel modules
- macOS Docker runs in VM without kernel module support
- Docker bridge network is sufficient for development

### 2. Analyzer Interface Flexibility
**Why**:
- Analyzer can capture from any interface (eth0, mirror-port, etc.)
- Same code works on both Docker and OVS
- Environment variable controls interface selection

### 3. OVS Scripts Prepared
**Why**:
- Enables future Linux deployment without code changes
- Demonstrates production-grade architecture
- Provides clear migration path

### 4. Subnet Consistency
**Why**:
- Same 10.0.1.0/24 subnet on both platforms
- Same IP addresses for all components
- Simplifies configuration and documentation

---

## Testing Strategy

### macOS Development
- Unit tests for protocol identification
- Integration tests with Docker containers
- Property-based tests for correctness
- End-to-end traffic capture tests

### Linux Production (Future)
- Same test suite runs on OVS
- Additional OVS-specific tests
- Performance benchmarks
- High-volume traffic tests

---

## Documentation

### Current
- `network-mirror/README.md` - macOS quick start
- `network-mirror/DEPLOYMENT_GUIDE.md` - macOS deployment
- `.kiro/specs/ovs-network-mirror/` - Complete specification

### Future
- `network-mirror/LINUX_DEPLOYMENT.md` - Linux OVS deployment
- OVS troubleshooting guide
- Performance tuning guide

---

## Success Criteria

✅ **macOS Development**:
- All containers communicate via Docker network
- Analyzer captures all inter-container traffic
- Protocol identification works correctly
- Pcap files generated successfully
- All tests pass

✅ **Linux Production (Future)**:
- OVS bridge operational
- Traffic mirroring configured
- Analyzer captures mirrored traffic
- Same protocol identification works
- Performance meets requirements

---

## Next Steps

1. Execute Task 4: Build and test Docker images
2. Execute Task 5: Integration tests
3. Execute Task 6: Property-based tests
4. Execute Task 7: Documentation
5. Execute Task 8: Final verification

Then system is ready for:
- macOS development and testing
- Linux production deployment (when needed)

---

## References

- OVS Documentation: http://openvswitch.org/
- Docker Networking: https://docs.docker.com/network/
- Scapy: https://scapy.readthedocs.io/
- IEC61850, Modbus, DNP3, MQTT specifications

