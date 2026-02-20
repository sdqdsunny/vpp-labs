# OVS Network Traffic Mirroring - Requirements

**Feature Name**: OVS Network Traffic Mirroring  
**Version**: 1.0  
**Date**: 2026-02-17  
**Status**: Requirements Phase

---

## Overview

Implement a network traffic mirroring system using Open vSwitch (OVS) to capture and analyze industrial control protocol traffic between the VPP master station, VCC coordinator, 5G UPF, and device simulators. The system will clone traffic at the virtual switch level and route it to a protocol analysis tool for real-time inspection.

---

## User Stories

### US-1: Network Infrastructure Setup
**As a** system administrator  
**I want to** set up an OVS-based virtual network infrastructure  
**So that** all VPP components can communicate through a centralized virtual switch

**Acceptance Criteria**:
- OVS bridge (br-vpp) is created and operational
- All business components (master, VCC, UPF, device simulator) are connected via veth-pair ports
- Network connectivity is verified between all components
- Bridge configuration is persistent and can be recreated

### US-2: Traffic Mirroring Configuration
**As a** network engineer  
**I want to** configure traffic mirroring on the OVS bridge  
**So that** all business traffic is cloned to an analysis port without affecting business operations

**Acceptance Criteria**:
- Mirror port is created on the OVS bridge
- Mirror rule captures all traffic from business ports
- Mirrored traffic is delivered to the analysis port
- Business traffic is not affected by mirroring (zero packet loss)
- Mirror configuration can be verified and monitored

### US-3: Protocol Analysis Tool Integration
**As a** protocol analyst  
**I want to** capture and analyze industrial control protocol traffic  
**So that** I can inspect IEC61850, Modbus, DNP3, and MQTT traffic in real-time

**Acceptance Criteria**:
- Protocol analyzer receives mirrored traffic from OVS
- Analyzer identifies protocol types (IEC61850, Modbus, DNP3, MQTT)
- Traffic is captured to pcap files for offline analysis
- Real-time statistics are generated and logged
- Analyzer can be started/stopped without affecting business traffic

### US-4: Docker Containerization
**As a** DevOps engineer  
**I want to** deploy the entire system using Docker Compose  
**So that** the system can be easily deployed, scaled, and managed

**Acceptance Criteria**:
- All components run in Docker containers
- OVS initialization is automated via container
- Network connectivity between containers is established
- Health checks are configured for all services
- System can be started/stopped with single commands

### US-5: Monitoring and Troubleshooting
**As a** system operator  
**I want to** monitor the OVS network and troubleshoot issues  
**So that** I can ensure the system is operating correctly and diagnose problems

**Acceptance Criteria**:
- OVS configuration can be inspected via standard commands
- Port statistics are available and accurate
- Mirror configuration can be verified
- Logs are generated for all components
- Troubleshooting guide covers common issues

---

## Functional Requirements

### FR-1: OVS Bridge Management
- Create and configure OVS bridge with name "br-vpp"
- Support bridge IP configuration (10.0.1.1/24)
- Enable bridge to be created/destroyed via scripts
- Support bridge status verification

### FR-2: Virtual Network Ports
- Create veth-pair ports for each component:
  - veth-master (10.0.1.10) - Master station
  - veth-vcc (10.0.1.20) - VCC coordinator
  - veth-upf (10.0.1.30) - 5G UPF
  - veth-gen (10.0.1.40) - Device simulator
  - veth-analyzer (10.0.1.50) - Protocol analyzer
- Configure IP addresses for each port
- Enable/disable ports as needed
- Support port status monitoring

### FR-3: Traffic Mirroring
- Create mirror port on OVS bridge
- Configure mirror rule to capture all traffic
- Route mirrored traffic to analysis port
- Support mirror rule verification
- Support mirror statistics collection

### FR-4: Protocol Analysis
- Identify industrial control protocols:
  - IEC61850 (port 102)
  - Modbus (port 502)
  - DNP3 (port 20000)
  - MQTT (ports 1883, 8883)
- Capture packets to pcap files
- Generate traffic statistics
- Support real-time packet processing
- Support pcap file rotation

### FR-5: Docker Integration
- Provide docker-compose.yml for system orchestration
- Implement OVS initialization container
- Configure networking for all containers
- Implement health checks
- Support volume mounting for logs and pcap files

### FR-6: Monitoring and Logging
- Generate structured logs for all components
- Provide OVS command reference
- Support real-time traffic monitoring
- Generate statistics reports
- Support troubleshooting procedures

---

## Non-Functional Requirements

### NFR-1: Performance
- Mirroring should not introduce packet loss
- Analyzer should process packets in real-time
- System should handle traffic up to 1Gbps
- Pcap file rotation should not block packet capture

### NFR-2: Reliability
- OVS bridge should remain operational during analyzer restarts
- Business traffic should not be affected by analyzer failures
- System should recover from component failures
- Configuration should be persistent

### NFR-3: Scalability
- Support addition of new business ports
- Support multiple analyzer instances
- Support VLAN-based traffic isolation (optional)
- Support traffic sampling for high-volume scenarios

### NFR-4: Maintainability
- Code should follow PEP 8 standards
- All functions should have comprehensive docstrings
- Error handling should be comprehensive
- Logging should be structured and informative

### NFR-5: Security
- Network traffic should be isolated via VLAN (optional)
- Analyzer should have minimal privileges
- Pcap files should have restricted access
- System should support encrypted traffic inspection

---

## Technical Constraints

### TC-1: Environment (macOS/Development)
- Docker >= 20.10
- Docker Compose >= 1.29
- Python >= 3.8
- Scapy library for packet processing

### TC-2: Environment (Linux/Production - Future)
- Linux kernel >= 4.15
- Docker >= 20.10
- Docker Compose >= 1.29
- OVS >= 2.13
- Python >= 3.8

### TC-3: Network
- Subnet: 10.0.1.0/24
- Gateway: 10.0.1.1
- macOS: Docker bridge network (vpp-net)
- Linux: OVS bridge (br-vpp) with veth-pair ports
- Port naming convention: veth-{component}

### TC-4: Protocols
- Support IEC61850, Modbus, DNP3, MQTT
- Use Scapy for packet processing
- Generate pcap files in standard format

---

## Dependencies

### External Dependencies
- Open vSwitch (OVS)
- Docker & Docker Compose
- Python Scapy library
- Linux networking tools (ip, ifconfig, etc.)

### Internal Dependencies
- VPP master station
- VCC coordinator
- 5G UPF simulator
- Device simulator

---

## Success Criteria

1. ✅ OVS bridge is created and operational
2. ✅ All components are connected via veth-pair ports
3. ✅ Traffic mirroring is configured and working
4. ✅ Protocol analyzer captures and identifies traffic
5. ✅ Docker Compose deployment is successful
6. ✅ All tests pass (unit + integration)
7. ✅ Documentation is complete
8. ✅ System can be deployed in < 5 minutes

---

## Out of Scope

- VLAN configuration (optional enhancement)
- REST API for analyzer (future enhancement)
- Alerting system (future enhancement)
- DPDK acceleration (future optimization)
- Multi-site deployment (future enhancement)

---

## Glossary

- **OVS**: Open vSwitch - virtual switch software
- **veth-pair**: Virtual Ethernet pair - kernel network interface
- **Mirror**: Traffic cloning mechanism in OVS
- **Pcap**: Packet capture file format
- **IEC61850**: Industrial protocol for power systems
- **Modbus**: Industrial protocol for device communication
- **DNP3**: Industrial protocol for power systems
- **MQTT**: Message Queuing Telemetry Transport protocol
