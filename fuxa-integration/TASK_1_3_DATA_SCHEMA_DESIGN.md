# Task 1.3: Data Schema Design - Completion Summary

**Date**: 2026-02-17  
**Status**: ✅ COMPLETED  
**All Acceptance Criteria**: ✅ MET

---

## Acceptance Criteria Verification

### ✅ MQTT topic structure finalized
- **Status**: VERIFIED
- **Details**: 
  - Topic hierarchy defined
  - 8 main topics identified
  - Naming convention established
  - Scalability considered

### ✅ Data payload format specified
- **Status**: VERIFIED
- **Details**:
  - JSON format selected
  - Payload structure defined
  - Field types specified
  - Size constraints documented

### ✅ REST API endpoints designed
- **Status**: VERIFIED
- **Details**:
  - 6 endpoints designed
  - Request/response formats specified
  - Error handling defined
  - Optional for Phase 1

### ✅ Transformation rules documented
- **Status**: VERIFIED
- **Details**:
  - Data mapping rules defined
  - Aggregation logic documented
  - Filtering rules specified
  - Validation rules documented

### ✅ Data flow diagram created
- **Status**: VERIFIED
- **Details**:
  - System components shown
  - Data flow illustrated
  - Integration points highlighted
  - Transformation steps documented

---

## MQTT Topic Hierarchy

### Topic Structure

```
vpp/traffic/
├── stats              # Overall statistics (1 sec)
├── rate               # Packet rate (1 sec)
├── protocols          # Protocol distribution (5 sec)
├── flows              # Top flows (5 sec)
└── components/
    ├── master         # Master station stats (1 sec)
    ├── vcc            # VCC coordinator stats (1 sec)
    ├── upf            # UPF stats (1 sec)
    └── gen            # Generator stats (1 sec)
```

### Topic Details

**1. vpp/traffic/stats** (Overall Statistics)
- **Frequency**: 1 second
- **QoS**: Level 1
- **Retention**: No
- **Purpose**: Publish all statistics in one message

**2. vpp/traffic/rate** (Packet Rate)
- **Frequency**: 1 second
- **QoS**: Level 1
- **Retention**: No
- **Purpose**: Real-time packet rate for gauges

**3. vpp/traffic/protocols** (Protocol Distribution)
- **Frequency**: 5 seconds
- **QoS**: Level 1
- **Retention**: No
- **Purpose**: Protocol breakdown for pie charts

**4. vpp/traffic/flows** (Top Flows)
- **Frequency**: 5 seconds
- **QoS**: Level 1
- **Retention**: No
- **Purpose**: Top 10 flows for analysis

**5. vpp/traffic/components/{component}** (Component Stats)
- **Frequency**: 1 second
- **QoS**: Level 1
- **Retention**: No
- **Purpose**: Per-component statistics
- **Components**: master, vcc, upf, gen

---

## Data Payload Format

### Payload 1: vpp/traffic/stats

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
    {
      "src": "10.0.1.10",
      "dst": "10.0.1.20",
      "packets": 450000,
      "bytes": 123456789
    }
  ],
  "components": {
    "master": {
      "packets": 450000,
      "bytes": 123456789
    },
    "vcc": {
      "packets": 370000,
      "bytes": 98765432
    },
    "upf": {
      "packets": 250000,
      "bytes": 87654321
    },
    "gen": {
      "packets": 150000,
      "bytes": 65432109
    }
  }
}
```

**Size**: ~800 bytes  
**Fields**: 15 total

### Payload 2: vpp/traffic/rate

```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "rate": 12.3
}
```

**Size**: ~50 bytes  
**Fields**: 2 total

### Payload 3: vpp/traffic/protocols

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

**Size**: ~150 bytes  
**Fields**: 6 total

### Payload 4: vpp/traffic/flows

```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "flows": [
    {
      "flow": "10.0.1.10->10.0.1.20",
      "packets": 450000,
      "bytes": 123456789
    },
    {
      "flow": "10.0.1.20->10.0.1.30",
      "packets": 370000,
      "bytes": 98765432
    }
  ]
}
```

**Size**: ~300 bytes  
**Fields**: 3 per flow

### Payload 5: vpp/traffic/components/{component}

```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "component": "master",
  "packets": 450000,
  "bytes": 123456789,
  "protocols": {
    "IEC61850": 450000,
    "Modbus": 0,
    "MQTT": 0,
    "DNP3": 0,
    "Unknown": 0
  }
}
```

**Size**: ~200 bytes  
**Fields**: 8 total

---

## REST API Endpoints (Optional)

### Endpoint 1: GET /api/traffic/stats

**Purpose**: Get current traffic statistics

**Request**:
```
GET /api/traffic/stats
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "total_packets": 1234567,
    "packet_rate": 12.3,
    "protocols": {...},
    "components": {...}
  }
}
```

### Endpoint 2: GET /api/traffic/rate

**Purpose**: Get current packet rate

**Request**:
```
GET /api/traffic/rate
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "rate": 12.3,
    "timestamp": "2026-02-17T10:30:00Z"
  }
}
```

### Endpoint 3: GET /api/traffic/protocols

**Purpose**: Get protocol distribution

**Request**:
```
GET /api/traffic/protocols
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "IEC61850": 450000,
    "Modbus": 370000,
    "MQTT": 250000,
    "DNP3": 150000,
    "Unknown": 14567
  }
}
```

### Endpoint 4: GET /api/traffic/flows

**Purpose**: Get top flows

**Request**:
```
GET /api/traffic/flows?limit=10
```

**Response**:
```json
{
  "status": "success",
  "data": [
    {
      "flow": "10.0.1.10->10.0.1.20",
      "packets": 450000,
      "bytes": 123456789
    }
  ]
}
```

### Endpoint 5: GET /api/traffic/components/{component}

**Purpose**: Get component-specific statistics

**Request**:
```
GET /api/traffic/components/master
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "component": "master",
    "packets": 450000,
    "bytes": 123456789,
    "protocols": {...}
  }
}
```

### Endpoint 6: GET /api/traffic/history

**Purpose**: Get historical data

**Request**:
```
GET /api/traffic/history?start=2026-02-17T10:00:00Z&end=2026-02-17T11:00:00Z
```

**Response**:
```json
{
  "status": "success",
  "data": [
    {
      "timestamp": "2026-02-17T10:00:00Z",
      "total_packets": 1000000,
      "packet_rate": 10.0
    }
  ]
}
```

---

## Data Transformation Rules

### Rule 1: Packet Count Aggregation
- **Source**: Individual packet captures
- **Transformation**: Sum all packet counts
- **Target**: total_packets field
- **Frequency**: Every 1 second

### Rule 2: Packet Rate Calculation
- **Source**: Packet count delta
- **Transformation**: (current_packets - previous_packets) / time_delta
- **Target**: packet_rate field
- **Frequency**: Every 1 second

### Rule 3: Protocol Distribution
- **Source**: Protocol field in each packet
- **Transformation**: Count packets per protocol
- **Target**: protocol_distribution object
- **Frequency**: Every 5 seconds

### Rule 4: Top Flows Extraction
- **Source**: Flow statistics
- **Transformation**: Sort by packet count, take top 10
- **Target**: top_flows array
- **Frequency**: Every 5 seconds

### Rule 5: Component Statistics
- **Source**: Source/destination IP addresses
- **Transformation**: Map IP to component, aggregate stats
- **Target**: components object
- **Frequency**: Every 1 second

### Rule 6: Byte Count Aggregation
- **Source**: Packet size in each packet
- **Transformation**: Sum all packet sizes
- **Target**: bytes field
- **Frequency**: Every 1 second

---

## Data Validation Rules

### Validation 1: Timestamp Format
- **Rule**: ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- **Action**: Reject if invalid
- **Example**: 2026-02-17T10:30:00Z

### Validation 2: Numeric Ranges
- **Rule**: All counts must be >= 0
- **Action**: Reject if negative
- **Example**: total_packets >= 0

### Validation 3: Protocol Names
- **Rule**: Must be one of: IEC61850, Modbus, MQTT, DNP3, Unknown
- **Action**: Reject if invalid
- **Example**: "IEC61850" is valid

### Validation 4: IP Address Format
- **Rule**: Valid IPv4 format (x.x.x.x)
- **Action**: Reject if invalid
- **Example**: 10.0.1.10 is valid

### Validation 5: Component Names
- **Rule**: Must be one of: master, vcc, upf, gen
- **Action**: Reject if invalid
- **Example**: "master" is valid

### Validation 6: Payload Size
- **Rule**: Must be < 1KB
- **Action**: Reject if too large
- **Example**: 800 bytes is valid

---

## Data Flow Diagram

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
│  │    - Captures packets                                │   │
│  │    - Extracts protocol, IP, size                     │   │
│  │    - Maintains statistics                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────────────────────────┐
        │  Data Transformation Layer           │
        │  - Aggregate packet counts           │
        │  - Calculate packet rate             │
        │  - Extract top flows                 │
        │  - Map IPs to components             │
        │  - Validate data                     │
        └──────────────────────────────────────┘
                           ↓
        ┌──────────────────────────────────────┐
        │  MQTT Publisher                      │
        │  - Format JSON payloads              │
        │  - Publish to topics                 │
        │  - Handle errors                     │
        └──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              MQTT Broker (Mosquitto)                         │
│  - Port 1883 (MQTT)                                          │
│  - Port 9001 (WebSocket)                                     │
│  - Topics: vpp/traffic/*                                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────────────────────────┐
        │  FUXA Device Manager                 │
        │  - Subscribe to topics               │
        │  - Parse JSON payloads               │
        │  - Update variables                  │
        │  - Trigger dashboard updates         │
        └──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    FUXA Dashboard                            │
│  - Network Topology Widget                                   │
│  - Statistics Gauges                                         │
│  - Protocol Distribution Chart                               │
│  - Component Traffic Chart                                   │
│  - Component Health Indicators                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
                    Browser (Port 1881)
```

---

## Data Processing Pipeline

```
1. Packet Capture
   └─ Interface: eth0 (Docker network)
   └─ Source: OVS mirror or Docker network
   └─ Output: Raw packets

2. Protocol Identification
   └─ Extract IP layer
   └─ Check TCP/UDP ports
   └─ Match against protocol map
   └─ Output: Protocol type

3. Statistics Update
   └─ Increment protocol counter
   └─ Update flow statistics
   └─ Track packet count
   └─ Accumulate byte count
   └─ Output: Updated statistics

4. Data Aggregation
   └─ Aggregate packet counts
   └─ Calculate packet rate
   └─ Extract top flows
   └─ Map IPs to components
   └─ Output: Aggregated data

5. Data Validation
   └─ Validate timestamp format
   └─ Validate numeric ranges
   └─ Validate protocol names
   └─ Validate IP addresses
   └─ Output: Validated data

6. JSON Formatting
   └─ Create JSON payloads
   └─ Add timestamps
   └─ Format nested objects
   └─ Output: JSON strings

7. MQTT Publishing
   └─ Connect to broker
   └─ Publish to topics
   └─ Handle errors
   └─ Output: Published messages

8. FUXA Reception
   └─ Subscribe to topics
   └─ Receive messages
   └─ Parse JSON
   └─ Update variables
   └─ Output: Updated variables

9. Dashboard Display
   └─ Update widgets
   └─ Render visualizations
   └─ Animate traffic flow
   └─ Output: Visual display
```

---

## Data Schema Summary

### MQTT Topics: 8 total
- vpp/traffic/stats
- vpp/traffic/rate
- vpp/traffic/protocols
- vpp/traffic/flows
- vpp/traffic/components/master
- vpp/traffic/components/vcc
- vpp/traffic/components/upf
- vpp/traffic/components/gen

### Payload Formats: 5 types
- Overall statistics (800 bytes)
- Packet rate (50 bytes)
- Protocol distribution (150 bytes)
- Top flows (300 bytes)
- Component statistics (200 bytes)

### REST API Endpoints: 6 total
- GET /api/traffic/stats
- GET /api/traffic/rate
- GET /api/traffic/protocols
- GET /api/traffic/flows
- GET /api/traffic/components/{component}
- GET /api/traffic/history

### Transformation Rules: 6 total
- Packet count aggregation
- Packet rate calculation
- Protocol distribution
- Top flows extraction
- Component statistics
- Byte count aggregation

### Validation Rules: 6 total
- Timestamp format
- Numeric ranges
- Protocol names
- IP address format
- Component names
- Payload size

---

## Next Steps

### Task 2.1: MQTT Publisher Implementation
- Create TrafficPublisher class
- Implement MQTT connection management
- Implement statistics publishing methods
- Add error handling and logging
- Create unit tests

### Task 2.2: Analyzer Integration
- Modify analyzer to use TrafficPublisher
- Add MQTT configuration via environment variables
- Integrate MQTT publishing into packet callback
- Add MQTT error handling
- Update Docker image

### Task 2.3: Docker Compose Stack
- Create docker-compose-fuxa.yml
- Configure Mosquitto service
- Configure FUXA service
- Configure analyzer service
- Add health checks

---

## Summary

✅ **Task 1.3 Complete**: Data schema design for FUXA integration is fully documented.

All acceptance criteria have been met:
- MQTT topic structure finalized
- Data payload format specified
- REST API endpoints designed
- Transformation rules documented
- Data flow diagram created

The data schema is well-defined and ready for implementation.

**Schema Status**: Complete ✅  
**Documentation Status**: Complete ✅  
**Diagram Status**: Complete ✅  
**Ready for Next Phase**: Yes ✅

