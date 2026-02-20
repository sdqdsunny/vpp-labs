# FUXA Integration - Requirements

**Feature Name**: FUXA Integration for VPP Traffic Visualization  
**Version**: 1.0  
**Date**: 2026-02-17  
**Status**: Requirements Phase

---

## Overview

Integrate FUXA (web-based SCADA/HMI platform) with the OVS Network Traffic Mirroring system to enable real-time visualization of traffic flow between VPP master station and functional modules (VCC, UPF, device simulators).

---

## User Stories

### US-1: MQTT Publisher Integration
**As a** system administrator  
**I want to** publish traffic statistics from the analyzer to MQTT  
**So that** FUXA and other systems can consume real-time traffic data

**Acceptance Criteria**:
- Analyzer publishes statistics to MQTT broker
- Statistics include total packets, packet rate, protocol distribution, flows, and component stats
- Publishing occurs at configurable intervals
- MQTT connection is resilient with automatic reconnection
- All statistics are published successfully

### US-2: FUXA Device Configuration
**As a** FUXA administrator  
**I want to** configure FUXA to receive traffic statistics via MQTT  
**So that** the dashboard can display real-time traffic data

**Acceptance Criteria**:
- MQTT device is configured in FUXA
- All required topics are subscribed
- Variables are mapped to MQTT topics
- Data is received and displayed in real-time
- Configuration can be imported/exported

### US-3: Traffic Visualization Dashboard
**As a** network operator  
**I want to** view real-time traffic visualization in FUXA  
**So that** I can monitor VPP network traffic and component health

**Acceptance Criteria**:
- Dashboard displays network topology
- Real-time statistics are shown (total packets, packet rate)
- Protocol distribution is visualized (pie chart)
- Component traffic is displayed (bar chart)
- Component health status is shown
- Dashboard updates in real-time

### US-4: Custom Network Topology Widget
**As a** network operator  
**I want to** see an animated network topology diagram  
**So that** I can visualize traffic flow between components

**Acceptance Criteria**:
- Network topology shows all components (Master, VCC, UPF, Gen)
- Connection lines show traffic flow
- Traffic flow is animated
- Real-time updates are reflected
- Component status is indicated

### US-5: Docker Containerization
**As a** DevOps engineer  
**I want to** deploy FUXA integration using Docker Compose  
**So that** the system can be easily deployed and managed

**Acceptance Criteria**:
- All services run in Docker containers
- MQTT broker is containerized
- FUXA platform is containerized
- Analyzer with MQTT publishing is containerized
- Health checks are configured
- System can be started/stopped with single commands

### US-6: Integration Testing
**As a** QA engineer  
**I want to** test the FUXA integration end-to-end  
**So that** I can verify the system works correctly

**Acceptance Criteria**:
- MQTT publisher tests pass
- FUXA device configuration tests pass
- Dashboard data binding tests pass
- End-to-end integration tests pass
- Performance tests pass

---

## Functional Requirements

### FR-1: MQTT Publisher
- Publish traffic statistics to MQTT broker
- Support configurable broker host and port
- Support configurable topic prefix
- Publish overall statistics (total packets, packet rate, protocols, flows, components)
- Publish packet rate (real-time pps)
- Publish protocol distribution (IEC61850, Modbus, MQTT, DNP3, Unknown)
- Publish top flows (top 10 flows)
- Publish component-specific stats (Master, VCC, UPF, Generator)
- Handle MQTT connection failures gracefully
- Support automatic reconnection

### FR-2: FUXA Device Configuration
- Define MQTT device in FUXA
- Configure 15 variables for traffic metrics
- Map variables to MQTT topics
- Configure dashboard with 6 widgets
- Support widget data binding
- Support real-time updates

### FR-3: Traffic Visualization
- Display network topology diagram
- Display real-time statistics (gauges)
- Display protocol distribution (pie chart)
- Display component traffic (bar chart)
- Display component health (status indicators)
- Support real-time updates

### FR-4: Custom Widgets
- Create network topology widget (SVG-based)
- Create flow visualization widget
- Support animated traffic flow
- Support real-time updates
- Support component status indication

### FR-5: Docker Integration
- Provide docker-compose.yml for complete stack
- Include Mosquitto MQTT broker
- Include FUXA platform
- Include analyzer with MQTT publishing
- Include Redis for caching (optional)
- Include REST API wrapper (optional)
- Configure health checks
- Configure volume management

### FR-6: Integration Testing
- Unit tests for MQTT publisher
- Integration tests for FUXA device configuration
- End-to-end tests for data flow
- Performance tests for throughput and latency
- Dashboard functionality tests

---

## Non-Functional Requirements

### NFR-1: Performance
- MQTT publish latency: < 100ms
- Dashboard update latency: < 1 second
- Widget render latency: < 500ms
- Support throughput: > 1000 packets/second
- Memory usage: < 1GB total

### NFR-2: Reliability
- MQTT connection resilience with automatic reconnection
- Error handling for all failure scenarios
- Health checks for all services
- Graceful degradation on component failure
- Data consistency across updates

### NFR-3: Scalability
- Support up to 1Gbps traffic
- Support multiple analyzer instances
- Support horizontal scaling
- Support traffic sampling for high-volume scenarios

### NFR-4: Maintainability
- Code follows PEP 8 standards
- Comprehensive docstrings for all functions
- Error handling is comprehensive
- Logging is structured and informative
- Configuration is externalized

### NFR-5: Security
- MQTT broker authentication (optional)
- Secure MQTT connections (optional)
- Access control for FUXA (optional)
- Data encryption in transit (optional)

---

## Technical Constraints

### TC-1: Environment
- Docker >= 20.10
- Docker Compose >= 1.29
- Python >= 3.8
- Node.js (FUXA)
- Angular (FUXA)

### TC-2: MQTT
- Mosquitto MQTT broker
- MQTT protocol version 3.1.1
- QoS level 1
- Topic-based publish/subscribe

### TC-3: Network
- Subnet: 10.0.2.0/24 (FUXA stack)
- MQTT broker port: 1883
- FUXA web port: 1881
- WebSocket port: 9001

### TC-4: Protocols
- Support IEC61850, Modbus, DNP3, MQTT
- Use Scapy for packet processing
- Generate pcap files in standard format

---

## Dependencies

### External Dependencies
- FUXA (GitHub: frangoteam/FUXA)
- Mosquitto MQTT Broker
- Docker & Docker Compose
- Python paho-mqtt library

### Internal Dependencies
- OVS Network Mirror system
- Protocol Analyzer (network-mirror/analyzer/main.py)
- VPP System (master, VCC, UPF, generator)

---

## Success Criteria

1. ✅ MQTT publisher publishes traffic statistics
2. ✅ FUXA receives and displays real-time data
3. ✅ Dashboard shows network topology
4. ✅ Custom widgets display traffic flow
5. ✅ Real-time updates working
6. ✅ Docker Compose deployment successful
7. ✅ All tests pass (unit + integration)
8. ✅ Documentation is complete

---

## Out of Scope

- Advanced FUXA customization (beyond basic widgets)
- REST API implementation (optional enhancement)
- Data transformer implementation (optional enhancement)
- Alerting system (future enhancement)
- Multi-site deployment (future enhancement)
- VLAN configuration (future enhancement)

---

## Glossary

- **FUXA**: Web-based SCADA/HMI/Dashboard platform
- **MQTT**: Message Queuing Telemetry Transport protocol
- **Mosquitto**: MQTT broker implementation
- **Widget**: UI component in FUXA dashboard
- **Topic**: MQTT message channel
- **QoS**: Quality of Service (MQTT reliability level)
- **Pcap**: Packet capture file format
- **IEC61850**: Industrial protocol for power systems
- **Modbus**: Industrial protocol for device communication
- **DNP3**: Industrial protocol for power systems

</content>
