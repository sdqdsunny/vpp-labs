# FUXA Integration - Design

**Feature Name**: FUXA Integration for VPP Traffic Visualization  
**Version**: 1.0  
**Date**: 2026-02-17  
**Status**: Design Phase

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VPP System                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ vpp-master   │  │ vpp-vcc      │  │ vpp-upf      │      │
│  │ (10.0.1.10)  │  │ (10.0.1.20)  │  │ (10.0.1.30)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                  ↓                  ↓              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    Network Traffic Analyzer (OVS Mirror)             │   │
│  │    - Captures traffic                                │   │
│  │    - Generates statistics                            │   │
│  │    - Publishes to MQTT                               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              MQTT Broker (Mosquitto)                         │
│  - Port 1883 (MQTT)                                          │
│  - Port 9001 (WebSocket)                                     │
│  - Topics: vpp/traffic/*                                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    FUXA Platform                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FUXA Server (Node.js)                               │   │
│  │  - Device Manager                                    │   │
│  │  - Data Aggregation                                  │   │
│  │  - Real-time Updates                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FUXA Web UI (Angular)                               │   │
│  │  - Network Topology Visualization                    │   │
│  │  - Traffic Flow Diagram                              │   │
│  │  - Real-time Statistics Dashboard                    │   │
│  │  - Protocol Distribution Charts                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↓
                    Browser (Port 1881)
```

---

## Component Design

### 1. MQTT Publisher Component

**Responsibility**: Publish traffic statistics to MQTT broker

**Location**: `fuxa-integration/mqtt-publisher.py`

**Key Classes**:

#### TrafficPublisher
```python
class TrafficPublisher:
    def __init__(broker_host, broker_port, topic_prefix, client_id)
    def connect()
    def disconnect()
    def publish_stats(stats)
    def publish_packet_rate(rate)
    def publish_protocols(protocols)
    def publish_flows(flows)
    def publish_component_stats(component, stats)
    def publish_all(stats)
    def is_connected()
```

**Methods**:
- `connect()`: Connect to MQTT broker
- `disconnect()`: Disconnect from MQTT broker
- `publish_stats()`: Publish overall statistics
- `publish_packet_rate()`: Publish packet rate
- `publish_protocols()`: Publish protocol distribution
- `publish_flows()`: Publish top flows
- `publish_component_stats()`: Publish component-specific stats
- `publish_all()`: Publish all statistics

**Features**:
- Automatic reconnection on connection loss
- QoS level 1 for reliability
- Comprehensive error handling
- Structured logging

### 2. MQTT Broker Component

**Responsibility**: Distribute traffic statistics messages

**Implementation**: Mosquitto MQTT broker

**Configuration**:
- MQTT listener: port 1883
- WebSocket listener: port 9001
- Persistence: enabled
- Logging: enabled

**Topics**:
- `vpp/traffic/stats` - Overall statistics
- `vpp/traffic/rate` - Packet rate
- `vpp/traffic/protocols` - Protocol distribution
- `vpp/traffic/flows` - Top flows
- `vpp/traffic/components/{component}` - Component stats

### 3. FUXA Device Component

**Responsibility**: Receive and aggregate traffic statistics

**Configuration**: `fuxa-integration/fuxa-device-config.json`

**Device Type**: MQTT

**Variables** (15 total):
- `total_packets` - Total packets captured
- `packet_rate` - Packets per second
- `iec61850_count` - IEC61850 protocol packets
- `modbus_count` - Modbus protocol packets
- `mqtt_count` - MQTT protocol packets
- `dnp3_count` - DNP3 protocol packets
- `unknown_count` - Unknown protocol packets
- `master_packets` - Master station packets
- `vcc_packets` - VCC coordinator packets
- `upf_packets` - UPF packets
- `gen_packets` - Generator packets
- `master_bytes` - Master station bytes
- `vcc_bytes` - VCC coordinator bytes
- `upf_bytes` - UPF bytes
- `gen_bytes` - Generator bytes

### 4. Dashboard Component

**Responsibility**: Display real-time traffic visualization

**Widgets** (6 total):

#### Widget 1: Network Topology (Custom SVG)
- Position: Top-left (6x6 grid)
- Features:
  - Component nodes (Master, VCC, UPF, Gen)
  - Connection lines
  - Animated traffic flow
  - Real-time updates

#### Widget 2: Total Packets (Gauge)
- Position: Top-right (3x3 grid)
- Range: 0 - 10,000,000 packets
- Variable: `total_packets`

#### Widget 3: Packet Rate (Gauge)
- Position: Top-right (3x3 grid)
- Range: 0 - 100,000 pps
- Variable: `packet_rate`

#### Widget 4: Protocol Distribution (Pie Chart)
- Position: Middle-right (6x3 grid)
- Variables: IEC61850, Modbus, MQTT, DNP3, Unknown
- Type: Pie chart

#### Widget 5: Component Traffic (Bar Chart)
- Position: Bottom-left (6x3 grid)
- Variables: Master, VCC, UPF, Generator
- Type: Bar chart

#### Widget 6: Component Health (Custom Status)
- Position: Bottom-right (6x3 grid)
- Components: Master, VCC, UPF, Generator
- Type: Status indicators

### 5. Docker Compose Component

**Responsibility**: Orchestrate containerized deployment

**Services**:

#### mosquitto
- Image: eclipse-mosquitto:latest
- Ports: 1883 (MQTT), 9001 (WebSocket)
- Volumes: config, data, logs
- Health check: MQTT connection test

#### fuxa
- Image: frangoteam/fuxa:latest
- Port: 1881 (HTTP)
- Volumes: appdata, database
- Health check: HTTP GET /
- Depends on: mosquitto

#### vpp-analyzer
- Image: vpp-analyzer:latest
- Environment: MQTT_BROKER, MQTT_TOPIC_PREFIX
- Volumes: pcap, logs
- Capabilities: NET_ADMIN, NET_RAW
- Depends on: mosquitto

#### redis (optional)
- Image: redis:7-alpine
- Port: 6379
- Volume: data
- Health check: redis-cli ping

#### analyzer-api (optional)
- Image: vpp-analyzer-api:latest
- Port: 8000
- Environment: MQTT_BROKER, REDIS_HOST
- Depends on: mosquitto, redis

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
All traffic ──→ OVS Mirror ──→ Analyzer ──→ MQTT Publisher

MQTT Flow:
MQTT Publisher ──→ Mosquitto ──→ FUXA ──→ Dashboard

Analysis Output:
Analyzer ──→ /pcap/*.pcap (files)
         ──→ /var/log/vpp/analyzer.log (logs)
         ──→ Statistics (MQTT)
```

### Packet Processing Pipeline

```
1. Packet Capture
   └─ Interface: eth0 (Docker network)
   └─ Source: OVS mirror or Docker network

2. Protocol Identification
   └─ Extract IP layer
   └─ Check TCP/UDP ports
   └─ Match against protocol map

3. Statistics Update
   └─ Increment protocol counter
   └─ Update flow statistics
   └─ Track packet count

4. MQTT Publishing
   └─ Collect statistics
   └─ Format as JSON
   └─ Publish to MQTT topics
   └─ Handle connection failures

5. FUXA Reception
   └─ Subscribe to MQTT topics
   └─ Receive statistics
   └─ Update variables
   └─ Trigger dashboard updates

6. Dashboard Display
   └─ Update widgets
   └─ Render visualizations
   └─ Animate traffic flow
```

---

## MQTT Topics & Payloads

### Topic: vpp/traffic/stats

**Payload**:
```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "total_packets": 1234567,
  "packet_rate": 12.3,
  "protocol_distribution": {
    "IEC61850": 450000,
    "Modbus": 370000,
    "MQTT": 250000,
    "DNP3": 150000,
    "Unknown": 14567
  },
  "top_flows": [
    {"src": "10.0.1.10", "dst": "10.0.1.20", "packets": 450000}
  ],
  "components": {
    "master": {"packets": 450000, "bytes": 123456789},
    "vcc": {"packets": 370000, "bytes": 98765432},
    "upf": {"packets": 250000, "bytes": 87654321},
    "gen": {"packets": 150000, "bytes": 65432109}
  }
}
```

**Frequency**: 1 second

### Topic: vpp/traffic/rate

**Payload**:
```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "rate": 12.3
}
```

**Frequency**: 1 second

### Topic: vpp/traffic/protocols

**Payload**:
```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "protocols": {
    "IEC61850": 450000,
    "Modbus": 370000,
    "MQTT": 250000,
    "DNP3": 150000,
    "Unknown": 14567
  }
}
```

**Frequency**: 5 seconds

### Topic: vpp/traffic/flows

**Payload**:
```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "flows": [
    {"flow": "10.0.1.10->10.0.1.20", "packets": 450000},
    {"flow": "10.0.1.20->10.0.1.30", "packets": 370000}
  ]
}
```

**Frequency**: 5 seconds

### Topic: vpp/traffic/components/{component}

**Payload**:
```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "component": "master",
  "packets": 450000,
  "bytes": 123456789,
  "protocols": {
    "IEC61850": 450000
  }
}
```

**Frequency**: 1 second

---

## Correctness Properties

### Property 1: MQTT Publisher Connectivity
**Description**: MQTT publisher maintains connection to broker

**Validation**:
- Publisher connects successfully
- Publisher reconnects on connection loss
- Publisher is_connected() returns correct status

### Property 2: Statistics Publishing
**Description**: All statistics are published to correct topics

**Validation**:
- Overall stats published to vpp/traffic/stats
- Packet rate published to vpp/traffic/rate
- Protocols published to vpp/traffic/protocols
- Flows published to vpp/traffic/flows
- Component stats published to vpp/traffic/components/{component}

### Property 3: FUXA Data Reception
**Description**: FUXA receives and displays statistics correctly

**Validation**:
- MQTT device subscribes to all topics
- Variables are updated with correct values
- Dashboard widgets display correct data

### Property 4: Real-Time Updates
**Description**: Dashboard updates in real-time

**Validation**:
- Updates occur within 1 second
- All widgets update simultaneously
- No data loss occurs

### Property 5: Docker Deployment
**Description**: All services start and remain healthy

**Validation**:
- All containers start successfully
- Health checks pass
- Services communicate correctly
- No container restarts

### Property 6: Data Accuracy
**Description**: Published statistics match analyzer data

**Validation**:
- Total packets match analyzer count
- Protocol distribution matches analyzer stats
- Component stats match analyzer data
- No data corruption occurs

---

## Testing Strategy

### Unit Tests
- Test TrafficPublisher class
- Test MQTT connection/disconnection
- Test payload formatting
- Test error handling

### Integration Tests
- Test MQTT publisher with Mosquitto
- Test FUXA device configuration
- Test data flow from analyzer to FUXA
- Test dashboard updates

### System Tests
- Test Docker Compose deployment
- Test all services start successfully
- Test end-to-end data flow
- Test real-time updates

### Property-Based Tests
- Test MQTT publisher with various statistics
- Test FUXA with various data patterns
- Test dashboard with various traffic patterns

---

## Deployment Architecture

### Development Deployment
- Docker Compose on macOS
- Docker bridge network (10.0.2.0/24)
- All services on same network

### Production Deployment
- Docker Compose on Linux
- Persistent volumes for data
- Health checks and monitoring
- Logging and alerting

---

## Performance Characteristics

### Throughput
- MQTT broker: 1000+ messages/second
- Analyzer: Real-time packet processing
- Dashboard: Real-time updates

### Latency
- MQTT publish: < 100ms
- Dashboard update: < 1 second
- Widget render: < 500ms

### Resource Usage
- Mosquitto: < 100MB RAM
- FUXA: < 500MB RAM
- Analyzer: < 200MB RAM
- Total: < 1GB RAM

---

## Error Handling

### MQTT Publisher Errors
- Connection failure → Log error, retry with backoff
- Publish failure → Log error, continue
- Payload error → Log error, skip message

### FUXA Errors
- Device configuration error → Log error, manual fix required
- Topic subscription error → Log error, retry
- Data binding error → Log error, manual fix required

### Docker Errors
- Container startup failure → Log error, retry
- Health check failure → Log error, restart
- Network connectivity failure → Log error, investigate

---

## Security Considerations

### MQTT Security
- Authentication: Optional (can be added)
- Encryption: Optional (can be added)
- Access control: Optional (can be added)

### FUXA Security
- Web UI authentication: Optional (can be added)
- API authentication: Optional (can be added)
- Data encryption: Optional (can be added)

### Docker Security
- Container privileges: Minimal (NET_ADMIN, NET_RAW for analyzer only)
- Volume permissions: Restricted
- Network isolation: Docker bridge network

---

## Future Enhancements

### Phase 2
- REST API for analyzer data
- Advanced FUXA customization
- Alerting system
- Traffic sampling for high-volume scenarios

### Phase 3
- DPDK acceleration
- Multi-site deployment
- Advanced protocol analysis
- Machine learning for anomaly detection

---

## References

- FUXA GitHub: https://github.com/frangoteam/FUXA
- MQTT Protocol: https://mqtt.org/
- Mosquitto: https://mosquitto.org/
- Docker: https://docs.docker.com/

</content>
