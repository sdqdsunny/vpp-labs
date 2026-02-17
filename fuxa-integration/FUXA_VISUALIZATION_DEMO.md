# FUXA Visualization Demo - Real-Time Traffic Monitoring

**Date**: 2026-02-17  
**Status**: ✅ System Running  
**Project**: FUXA Integration for VPP Traffic Visualization

---

## System Status Overview

All core components are running and operational:

- ✅ **VPP Master** (Port 8090) - Main station program
- ✅ **FUXA Platform** (Port 1881) - Visualization dashboard
- ✅ **Mosquitto MQTT Broker** (Port 1883) - Message broker
- ✅ **Network Analyzer** - Traffic analysis with MQTT publishing
- ✅ **Redis Cache** (Port 6379) - Data caching
- ✅ **Support Services** - PostgreSQL, Prometheus, Grafana

---

## Real-Time Data Flow Architecture

```
VPP Components (Traffic Generation)
    ↓
Network Traffic Analyzer (Packet Capture & Analysis)
    ↓
MQTT Publisher (Statistics Publishing)
    ↓
Mosquitto MQTT Broker (Message Distribution)
    ↓
FUXA Platform (Data Reception & Aggregation)
    ↓
Web Dashboard (Real-Time Visualization)
    ↓
Browser (User Interface)
```

---

## MQTT Data Flow Demonstration

### 1. Traffic Capture Phase

The analyzer captures traffic from the Docker network interface (eth0):

```
Captured Protocols:
├── IEC61850 (Industrial Protocol)
├── Modbus (Legacy Industrial Protocol)
├── MQTT (Message Broker Protocol)
├── DNP3 (Power System Protocol)
└── Unknown (Other protocols)

Component Sources:
├── vpp-master (10.0.1.10)
├── vpp-vcc (10.0.1.20)
├── vpp-upf (10.0.1.30)
└── vpp-gen (10.0.1.40)
```

### 2. Statistics Publishing Phase

Every 1 second, the analyzer publishes statistics to MQTT topics:

**Topic: vpp/traffic/stats**
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
  "components": {
    "master": {"packets": 450000, "bytes": 123456789},
    "vcc": {"packets": 370000, "bytes": 98765432},
    "upf": {"packets": 250000, "bytes": 87654321},
    "gen": {"packets": 150000, "bytes": 65432109}
  }
}
```

**Topic: vpp/traffic/rate**
```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "rate": 12.3
}
```

**Topic: vpp/traffic/protocols**
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

### 3. FUXA Reception Phase

FUXA subscribes to all MQTT topics and receives real-time updates:

- Mosquitto broker distributes messages to FUXA
- FUXA device manager receives and aggregates data
- Variables are updated in real-time
- Dashboard widgets refresh automatically

---

## Dashboard Visualization Components

### Widget 1: Network Topology (SVG Visualization)

**Location**: Top-left area  
**Type**: Custom SVG with animated traffic flow

```
┌─────────────────────────────────────┐
│                                     │
│    Master (10.0.1.10)               │
│         ↓                           │
│    ┌────────────┐                   │
│    │   VCC      │ ← VPP Coordinator │
│    │(10.0.1.20) │                   │
│    └────────────┘                   │
│         ↓                           │
│    ┌────────────┐                   │
│    │   UPF      │ ← UPF Station     │
│    │(10.0.1.30) │                   │
│    └────────────┘                   │
│         ↓                           │
│    ┌────
### Widget 1: Network Topology (SVG   
**Location**: Top-left area  
**Type**: Custom Sr  **Type**: Custom SVG with an0)
```
┌────────────???─???                                     │
│    Master (10.0.1.10)               │
│         ↓             ????    Master (10.0.1.10)               └?│         ↓                           ???    ┌───────────?f│    │   VCC      │ ← VPP Coordinator │
│    │(10.0.1.20vo│    │(10.0.1.20) │                   │
oc│    └──────────── 
│         ↓                           │
│    ┌────? │    ┌────────────│    │   UPF      │ ← UPF Station     │
│    │(10.0.1.30 ???    │(10.0.1.30) │                   │
????    └────────────et│         ↓                           │
│    ┌────
#ug│    ┌────
### Widget 1: Network*:### Widget 1: Network  **Location**: Top-left area  
**Type*??*Type**: Custom Sr  **Type*.3```
┌────────────???? ┓???    Master (10.0.1.10)               │
│         ↓             ????    Master (1 P│         ↓             ????    Masteon│    │(10.0.1.20vo│    │(10.0.1.20) │                   │
oc│    └──────────── 
│         ↓                           │
│    ┌────? │    ┌───├oc│    └──────────── 
│         ↓   : │         ↓                           │
?o│    ┌────? │    ┌──?t│    │(10.0.1.30 ???    │(10.0.1.30) │                   │
????    └────────────etck????    └────────────et│         ↓    4│    ┌────
#ug│    ┌────
### Widget 1: Network*:### Widget 1: Network ??ug│    ┌──? ### Widget 1: Network*:#  **Type*??*Type**: Custom Sr  **Type*.3```
┌─────────?t┌────────────?`│         ↓             ????    Master (1 P│         ↓             ????    Masteon?0oc│    └──────────── 
│         ↓                           │
│    ┌────? │    ┌───├oc│    └─?y│         ↓                           │
?U│    ┌────? │    ┌──?d│         ↓   : │         ↓                           │
?o│    ┌────? 0.?o│    ┌────? │    ┌──?t│    │(10.is????    └────────────etck????    └────────────et│         ↓ ar#ug│    ┌────
### Widget 1: Network*:### Widget 1: Network ??ug│    ┌──? ### Widget 1: Network*:#  **Type*??*Type**: Cupl### Widget 1: Network*:#Re┌─────────?t┌────────────?`│         ↓             ????    Master (1 P│         ?.│         ↓                           │
│    ┌────? │    ┌───├oc│    └─?y│         ↓                           │
?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? ?U│    ┌────? │    ┌──?d│         ↓   : │         ↓                         ac?o│    ┌────? 0.?o│    ┌────? │    ┌──?t│    │(10.is????    └─?.### Widget 1: Network*:### Widget 1: Network ??ug│    ┌──? ### Widget 1: Network*:#  **Type*??*Type**: Cupl### Widget 1: Network*:#Re┌─────────?t┌────────────?`│         ↓      er│    ┌────? │    ┌───├oc│    └─?y│         ↓                           │
?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? ?U│    ┌────? │    ┌──?d│         ↓   : │         ↓                     
|?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? -
?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? ?U│    ┌────? │    ┌──?d│         ↓   : │         ↓                     
|?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? -
?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? ?U│    ┌────? │    ┌──?d│         ↓   : │         ↓                     
|?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? -
?U│    ┌────? └?|?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? -
?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌─?? U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? ? |?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? -
?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌─?? U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? ???U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? -
?U│    ┌────? └?|?U│    ┌────? │    ┌──?d│         al│???U│    ┌────? └?|?U│    ┌────? │    ┌──?d│         al│    ┌│ ?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌─?? U│    ┌────? │    ┌???U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌─?? U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? ???U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌──? ??? U│    ┌────? └?|?U│    ┌────? │    ┌──?d│         al│???U│    ┌────? └?|?U│    ┌────? │    ┌──?d│         al│    ┌│ ?U│    ┌────? │    ┌──?d│         al│    ┌────? │    ┌─?? U│?              MQTT Broker (Mosquitto)                         │
│  - Port 1883 (MQTT)                                          │
│  - Port 9001 (WebSocket)                                     │
│  - Topics: vpp/traffic/*                                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    FUXA Platform                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FUXA Server (Node.js)                               │   │
│  │  - Device M│  - Port 1883 (MQTT)                                         D│  - Port 9001 (WebSocket)                                     ? │  - Topics: vpp/traffic/*                                     ??└─────────────────────??                           ↓
┌────────────────────────────────────────────────────┌─────────???                    FUXA Platform                             │
│  ┌─────────────────────────────────────  │  ┌───────────────────? │  │  FUXA Server (Node.js)                               │   │
│  │  - Device M│  - Port 1883 (MQTT)                                         D│  - Port 9001 (Web???  │  - Device M│  - Port 1883 (MQTT)                           ???────────────────────────────────────────────────────┌─────────???                    FUXA Platform                             │
│  ┌──────────────────  │  ┌─────────────────────────────────────  │  ┌───────────────────? │  │  FUXA Server (Node.js)                               │  as│  │  - Device M│  - Port 1883 (MQTT)                                         D│  - Port 9001 (Web???  │  - Device M│  - Port 1883 (MQTT)                           ???─────────────────────────? │  ┌──────────────────  │  ┌─────────────────────────────────────  │  ┌───────────────────? │  │  FUXA Server (Node.js)                               │  as│  │  - Device M│  - Port 1883 (MQTT)                                         D│  - Port 9001 (Web???  ?: `docker logs vpp-mosquitto`
4. Restart broker: `docker restart vpp-mosquitto`

### High Latency

**Symptom**: Updates delayed > 1 second

**Solution**:
1. Check CPU usage: `docker stats`
2. Check network: `docker network inspect fuxa_network`
3. Check MQTT queue: Monitor Mosquitto logs
4. Reduce publish frequency if needed

---

## Conclusion

The FUXA integration system is fully operational with:

- ✅ Real-time traffic visualization
- ✅ MQTT data flow verified
- ✅ Dashboard widgets displaying live data
- ✅ Performance metrics within targets
- ✅ All services healthy and communicating

The system successfully demonstrates VPP traffic analysis with real-time FUXA visualization.

