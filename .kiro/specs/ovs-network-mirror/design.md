# OVS Network Traffic Mirroring - Design

**Feature Name**: OVS Network Traffic Mirroring  
**Version**: 1.0  
**Date**: 2026-02-17  
**Status**: Design Phase

---

## Architecture Overview

### Deployment Strategy

**macOS/Development (Current)**:
- Uses Docker native bridge networking (10.0.1.0/24)
- All containers communicate via Docker network
- Analyzer captures traffic from eth0 interface
- No OVS kernel module required

**Linux/Production (Future)**:
- Can use OVS bridge (br-vpp) with veth-pair ports
- OVS scripts provided for Linux deployment
- Same analyzer code works with OVS mirror-port
- Seamless migration path

### System Architecture Diagram (macOS/Docker)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Host (macOS)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Docker Bridge Network (vpp-net)                │   │
│  │           Subnet: 10.0.1.0/24, Gateway: 10.0.1.1        │   │
│  │                                                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │vpp-master│ │ vpp-vcc  │ │ vpp-upf  │ │ vpp-gen  │    │   │
│  │  │10.0.1.10 │ │10.0.1.20 │ │10.0.1.30 │ │10.0.1.40 │    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  │       ↓              ↓              ↓              ↓      │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │         vpp-analyzer (10.0.1.50)                 │   │   │
│  │  │  - Captures traffic from eth0                    │   │   │
│  │  │  - Protocol identification                       │   │   │
│  │  │  - Pcap file generation                          │   │   │
│  │  │  - Statistics collection                         │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │       ↓                                                  │   │
│  │  /pcap/*.pcap (Protocol analysis results)               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### System Architecture Diagram (Linux/OVS - Future)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Linux Host                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              OVS Virtual Switch (br-vpp)                 │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ Business Ports (veth-pair)                         │  │   │
│  │  │ ├─ veth-master-br (10.0.1.10)                      │  │   │
│  │  │ ├─ veth-vcc-br (10.0.1.20)                         │  │   │
│  │  │ ├─ veth-upf-br (10.0.1.30)                         │  │   │
│  │  │ └─ veth-gen-br (10.0.1.40)                         │  │   │
│  │  │                                                    │  │   │
│  │  │ Mirror Configuration                              │  │   │
│  │  │ └─ Mirror Rule: select-all → mirror-port          │  │   │
│  │  │                                                    │  │   │
│  │  │ Analysis Port                                      │  │   │
│  │  │ └─ mirror-port (internal, 10.0.1.100)             │  │   │
│  │  │ └─ veth-analyzer-br (10.0.1.50)                    │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Docker Containers                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │vpp-master│ │ vpp-vcc  │ │ vpp-upf  │ │ vpp-gen  │    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │         vpp-analyzer (Protocol Analysis)         │   │   │
│  │  │  - Packet capture from mirror-port              │   │   │
│  │  │  - Protocol identification                       │   │   │
│  │  │  - Pcap file generation                          │   │   │
│  │  │  - Statistics collection                         │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. OVS Bridge Component

**Responsibility**: Manage virtual network infrastructure

**Key Functions**:
- Create/destroy OVS bridge
- Manage veth-pair ports
- Configure IP addresses
- Enable/disable ports

**Implementation**:
- Script: `network-mirror/scripts/ovs-init.sh`
- Script: `network-mirror/scripts/ovs-cleanup.sh`
- Container: `ovs-init` service in docker-compose

**Port Configuration**:

| Port Name | Type | IP Address | Purpose |
|-----------|------|-----------|---------|
| veth-master-br | veth-pair | 10.0.1.10 | Master station connection |
| veth-vcc-br | veth-pair | 10.0.1.20 | VCC coordinator connection |
| veth-upf-br | veth-pair | 10.0.1.30 | 5G UPF connection |
| veth-gen-br | veth-pair | 10.0.1.40 | Device simulator connection |
| mirror-port | internal | 10.0.1.100 | Mirror destination |
| veth-analyzer-br | veth-pair | 10.0.1.50 | Analyzer connection |

### 2. Mirror Configuration Component

**Responsibility**: Configure traffic mirroring rules

**Key Functions**:
- Create mirror port
- Configure mirror rule (select-all)
- Route traffic to analysis port
- Verify mirror configuration

**Implementation**:
- OVS command: `ovs-vsctl -- --id=@m create Mirror ...`
- Verification: `ovs-vsctl list Mirror`

**Mirror Rule**:
```
Mirror Configuration:
  Name: m0
  Select All: true
  Output Port: mirror-port
  Statistics: enabled
```

### 3. Protocol Analyzer Component

**Responsibility**: Capture and analyze network traffic

**Key Functions**:
- Capture packets from mirror port
- Identify industrial control protocols
- Generate pcap files
- Collect statistics
- Provide logging

**Implementation**:
- File: `network-mirror/analyzer/main.py`
- Container: `vpp-analyzer` service
- Dependencies: Scapy, Python 3.8+

**Protocol Support**:

| Protocol | Port(s) | Type | Status |
|----------|---------|------|--------|
| IEC61850 | 102 | TCP | Supported |
| Modbus | 502 | TCP/UDP | Supported |
| DNP3 | 20000 | TCP/UDP | Supported |
| MQTT | 1883, 8883 | TCP | Supported |

**Analyzer Classes**:

#### ProtocolIdentifier
- Identifies protocol type from packet
- Maintains protocol-to-port mapping
- Returns protocol name or "Unknown"

#### PacketAnalyzer
- Captures packets from interface
- Processes each packet via callback
- Maintains statistics (protocol, flow)
- Rotates pcap files
- Logs statistics periodically

### 4. Docker Compose Orchestration

**Responsibility**: Manage containerized deployment

**Services**:

1. **ovs-init**
   - Image: ubuntu:22.04
   - Purpose: Initialize OVS infrastructure
   - Network: host
   - Privileged: true

2. **vpp-master**
   - Image: vpp-master:latest
   - IP: 10.0.1.10
   - Port: 8080
   - Health check: HTTP /health

3. **vpp-vcc**
   - Image: vpp-vcc:latest
   - IP: 10.0.1.20
   - Port: 8081
   - Depends on: vpp-master

4. **vpp-upf**
   - Image: vpp-upf:latest
   - IP: 10.0.1.30
   - Port: 8082
   - Depends on: vpp-master

5. **vpp-gen**
   - Image: vpp-gen:latest
   - IP: 10.0.1.40
   - Depends on: vpp-master

6. **vpp-analyzer**
   - Image: vpp-analyzer:latest
   - IP: 10.0.1.50
   - Capabilities: NET_ADMIN, NET_RAW
   - Volumes: /pcap, /var/log/vpp

**Network Configuration**:
- Driver: bridge
- Subnet: 10.0.1.0/24
- Gateway: 10.0.1.1

---

## Data Flow

### Traffic Flow Diagram

```
Business Traffic Flow:
┌─────────────┐
│ vpp-master  │ (10.0.1.10)
└──────┬──────┘
       │
       ├─→ vpp-vcc (10.0.1.20)
       │
       ├─→ vpp-upf (10.0.1.30)
       │
       └─→ vpp-gen (10.0.1.40)

Mirror Flow:
All traffic ──→ OVS Mirror ──→ mirror-port ──→ vpp-analyzer (10.0.1.50)

Analysis Output:
vpp-analyzer ──→ /pcap/*.pcap (files)
             ──→ /var/log/vpp/analyzer.log (logs)
             ──→ Statistics (stdout)
```

### Packet Processing Pipeline

```
1. Packet Capture
   └─ Interface: veth-analyzer
   └─ Source: OVS mirror-port

2. Protocol Identification
   └─ Extract IP layer
   └─ Check TCP/UDP ports
   └─ Match against protocol map

3. Statistics Update
   └─ Increment protocol counter
   └─ Update flow statistics
   └─ Track packet count

4. Pcap Storage
   └─ Buffer packets in memory
   └─ Rotate file every N packets
   └─ Write to /pcap directory

5. Logging
   └─ Log statistics every 100 packets
   └─ Log errors and warnings
   └─ Output to /var/log/vpp/analyzer.log
```

---

## Implementation Details

### OVS Initialization Script (ovs-init.sh)

**Purpose**: Set up OVS infrastructure

**Steps**:
1. Check OVS installation
2. Create bridge (br-vpp)
3. Configure bridge IP (10.0.1.1/24)
4. Create veth-pair ports for each component
5. Add ports to bridge
6. Configure IP addresses
7. Create mirror port
8. Configure mirror rule
9. Enable mirror-port
10. Display configuration

**Error Handling**:
- Check OVS installation
- Verify command execution
- Log all operations
- Provide error messages

### OVS Cleanup Script (ovs-cleanup.sh)

**Purpose**: Clean up OVS infrastructure

**Steps**:
1. Delete bridge
2. Delete veth-pair ports
3. Verify cleanup

### Protocol Analyzer (main.py)

**Purpose**: Capture and analyze traffic

**Classes**:

#### ProtocolIdentifier
```python
class ProtocolIdentifier:
    PROTOCOL_PORTS = {
        102: 'IEC61850',
        502: 'Modbus',
        20000: 'DNP3',
        1883: 'MQTT',
        8883: 'MQTT-TLS',
    }
    
    @staticmethod
    def identify(packet) -> Optional[str]:
        # Identify protocol from packet
```

#### PacketAnalyzer
```python
class PacketAnalyzer:
    def __init__(self, interface: str, output_dir: str):
        # Initialize analyzer
    
    def packet_callback(self, packet):
        # Process each packet
    
    def _save_pcap(self):
        # Save pcap file
    
    def _log_stats(self):
        # Log statistics
    
    def start_capture(self):
        # Start packet capture
    
    def stop_capture(self):
        # Stop packet capture
```

---

## Correctness Properties

### Property 1: Bridge Connectivity
**Description**: All business components can communicate through the OVS bridge

**Validation**:
- Ping test between all components
- Verify IP addresses are assigned
- Check port status is UP

### Property 2: Traffic Mirroring
**Description**: All traffic from business ports is mirrored to analysis port

**Validation**:
- Capture traffic on mirror-port
- Verify packet count matches business traffic
- Check no packet loss occurs

### Property 3: Protocol Identification
**Description**: Analyzer correctly identifies industrial control protocols

**Validation**:
- Send test packets for each protocol
- Verify protocol identification is correct
- Check statistics are accurate

### Property 4: Pcap File Generation
**Description**: Pcap files are generated correctly and contain captured traffic

**Validation**:
- Verify pcap files are created
- Check file format is valid
- Verify packet count in pcap matches captured count

### Property 5: No Business Impact
**Description**: Mirroring does not affect business traffic

**Validation**:
- Measure packet loss before/after mirroring
- Verify latency is not increased
- Check business traffic continues unaffected

### Property 6: Container Health
**Description**: All containers start successfully and remain healthy

**Validation**:
- Verify all containers are running
- Check health checks pass
- Verify no container restarts

---

## Testing Strategy

### Unit Tests
- Test ProtocolIdentifier.identify() with various packets
- Test PacketAnalyzer initialization
- Test pcap file generation
- Test statistics collection

### Integration Tests
- Test OVS bridge creation and cleanup
- Test veth-pair port creation
- Test mirror rule configuration
- Test end-to-end traffic capture

### System Tests
- Test Docker Compose deployment
- Test all containers start successfully
- Test traffic flows between components
- Test analyzer captures traffic
- Test pcap files are generated

### Property-Based Tests
- Test protocol identification with random packets
- Test statistics accuracy with various traffic patterns
- Test pcap file integrity with different packet sizes

---

## Deployment Architecture

### Deployment Phases

**Phase 1: Infrastructure Setup (5 minutes)**
- Install OVS
- Create OVS bridge
- Create veth-pair ports
- Configure IP addresses

**Phase 2: Container Deployment (5 minutes)**
- Build Docker images
- Start containers
- Verify connectivity
- Check health checks

**Phase 3: Verification (5 minutes)**
- Verify OVS configuration
- Verify traffic mirroring
- Verify analyzer is capturing
- Verify pcap files are generated

### Deployment Checklist

- [ ] OVS installed and running
- [ ] Bridge created (br-vpp)
- [ ] All veth-pair ports created
- [ ] IP addresses configured
- [ ] Mirror rule configured
- [ ] Docker images built
- [ ] All containers running
- [ ] Health checks passing
- [ ] Traffic flowing between components
- [ ] Analyzer capturing traffic
- [ ] Pcap files being generated

---

## Performance Considerations

### Throughput
- Target: Support up to 1Gbps traffic
- Mirroring overhead: < 5%
- Analyzer processing: Real-time

### Latency
- Mirroring latency: < 1ms
- Analyzer processing latency: < 10ms
- No impact on business traffic

### Resource Usage
- OVS memory: < 100MB
- Analyzer memory: < 200MB
- CPU usage: < 20% per component

### Scalability
- Support up to 10 business ports
- Support multiple analyzer instances
- Support traffic sampling for high-volume scenarios

---

## Security Considerations

### Network Isolation
- Use VLAN for traffic isolation (optional)
- Restrict analyzer network access
- Limit mirror port access

### Data Protection
- Encrypt pcap file transmission
- Restrict pcap file access permissions
- Implement pcap file retention policy

### Access Control
- Limit OVS command access
- Restrict container privileges
- Implement audit logging

---

## Error Handling

### OVS Errors
- Bridge creation failure → Log error, exit
- Port creation failure → Log error, continue
- Mirror configuration failure → Log error, retry

### Analyzer Errors
- Packet capture failure → Log error, retry
- Pcap write failure → Log error, skip packet
- Protocol identification failure → Log warning, mark as Unknown

### Container Errors
- Container startup failure → Log error, retry
- Health check failure → Log warning, restart
- Network connectivity failure → Log error, investigate

---

## Monitoring and Observability

### Metrics
- Packet count (total, per protocol)
- Flow count
- Pcap file count and size
- Analyzer uptime
- Mirror statistics

### Logging
- OVS operations (bridge, ports, mirror)
- Analyzer operations (capture, statistics)
- Container operations (startup, health)
- Error and warning messages

### Alerting
- Analyzer process down
- Mirror rule not active
- Pcap write failures
- Container health check failures

---

## Future Enhancements

### Phase 2
- REST API for real-time statistics
- Web dashboard for traffic visualization
- Alerting system for anomalies
- Traffic sampling for high-volume scenarios

### Phase 3
- DPDK acceleration for OVS
- Multi-site deployment support
- Advanced protocol analysis
- Machine learning for anomaly detection

---

## References

- [Open vSwitch Documentation](http://openvswitch.org/)
- [Scapy Documentation](https://scapy.readthedocs.io/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [IEC61850 Standard](https://en.wikipedia.org/wiki/IEC_61850)
- [Modbus Protocol](https://en.wikipedia.org/wiki/Modbus)
- [DNP3 Protocol](https://en.wikipedia.org/wiki/DNP3)
- [MQTT Protocol](https://mqtt.org/)
