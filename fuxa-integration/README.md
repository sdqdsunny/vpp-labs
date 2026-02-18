# FUXA Integration for VPP Traffic Visualization

**Project**: OVS Network Traffic Mirroring + VPP System  
**Status**: Implementation Framework  
**Approach**: Hybrid (MQTT + REST API + Custom Widgets)

---

## Overview

This directory contains the integration framework for connecting FUXA (web-based SCADA/HMI platform) with the VPP network traffic analysis system. The integration enables real-time visualization of traffic flow between VPP master station and functional modules (VCC, UPF, device simulators).

---

## Architecture

```
VPP System (Traffic Analyzer)
    ↓
MQTT Broker (Mosquitto)
    ↓
FUXA Platform (Node.js + Angular)
    ↓
Web Dashboard (Port 1881)
```

**Key Components**:
- **MQTT Publisher**: Publishes traffic statistics from analyzer
- **MQTT Broker**: Mosquitto for message distribution
- **FUXA Server**: Node.js backend for data aggregation
- **FUXA UI**: Angular frontend for visualization
- **Custom Widgets**: SVG-based network topology and flow visualization

---

## Directory Structure

```
fuxa-integration/
├── mqtt-publisher.py              # MQTT publisher for analyzer
├── rest-api.py                    # REST API wrapper (optional)
├── data-transformer.py            # Data transformation logic (optional)
├── fuxa-device-config.json        # FUXA device configuration
├── mosquitto.conf                 # Mosquitto MQTT broker config
├── docker-compose-fuxa.yml        # Docker Compose for FUXA stack
├── custom-widgets/
│   ├── network-topology.html      # Network topology widget
│   ├── flow-visualization.html    # Flow visualization widget
│   └── README.md                  # Widget documentation
├── tests/
│   ├── test_mqtt_publisher.py     # MQTT publisher tests
│   ├── test_rest_api.py           # REST API tests
│   └── test_integration.py        # Integration tests
├── INTEGRATION_GUIDE.md           # Step-by-step integration guide
├── DEPLOYMENT_GUIDE.md            # Production deployment guide
├── TROUBLESHOOTING.md             # Troubleshooting guide
└── README.md                      # This file
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OVS Network Mirror system running
- Python 3.8+ (for MQTT publisher)
- 2GB+ RAM
- 5GB+ disk space

### Step 1: Start FUXA Stack

```bash
cd fuxa-integration
docker-compose -f docker-compose-fuxa.yml up -d
```

### Step 2: Access FUXA

Open browser: http://localhost:1881

### Step 3: Configure MQTT Device

1. Go to **Devices** → **Add Device**
2. Select **MQTT**
3. Configure broker: `mosquitto:1883`
4. Subscribe to topics: `vpp/traffic/#`

### Step 4: Create Dashboard

1. Go to **Dashboards** → **New Dashboard**
2. Add widgets for visualization
3. Bind to MQTT topics

---

## Files Description

### mqtt-publisher.py
MQTT publisher class for publishing traffic statistics from the analyzer.

**Features**:
- Connect/disconnect from MQTT broker
- Publish overall statistics
- Publish packet rate
- Publish protocol distribution
- Publish top flows
- Publish component-specific stats

**Usage**:
```python
from mqtt_publisher import TrafficPublisher

publisher = TrafficPublisher(
    broker_host='mosquitto',
    broker_port=1883,
    topic_prefix='vpp/traffic'
)
publisher.connect()
publisher.publish_all(stats)
```

### fuxa-device-config.json
FUXA device configuration file defining:
- MQTT device connection settings
- Variables/topics to subscribe
- Dashboard layout
- Widget configuration

### mosquitto.conf
Mosquitto MQTT broker configuration:
- Listener on port 1883 (MQTT)
- Listener on port 9001 (WebSocket)
- Persistence enabled
- Logging configured

### docker-compose-fuxa.yml
Docker Compose configuration for complete FUXA stack:
- Mosquitto MQTT broker
- FUXA platform
- VPP analyzer with MQTT publishing
- Redis for caching (optional)
- REST API wrapper (optional)

---

## MQTT Topics

### Published Topics

| Topic | Payload | Frequency |
|-------|---------|-----------|
| vpp/traffic/stats | Overall statistics | 1 second |
| vpp/traffic/rate | Packet rate (pps) | 1 second |
| vpp/traffic/protocols | Protocol distribution | 5 seconds |
| vpp/traffic/flows | Top 10 flows | 5 seconds |
| vpp/traffic/components/master | Master station stats | 1 second |
| vpp/traffic/components/vcc | VCC coordinator stats | 1 second |
| vpp/traffic/components/upf | UPF stats | 1 second |
| vpp/traffic/components/gen | Generator stats | 1 second |

### Payload Format

```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "total_packets": 1234567,
  "packet_rate": 12.3,
  "protocols": {
    "IEC61850": 450000,
    "Modbus": 370000,
    "MQTT": 250000,
    "DNP3": 150000,
    "Unknown": 14567
  },
  "flows": [
    {"src": "10.0.1.10", "dst": "10.0.1.20", "packets": 450000}
  ],
  "components": {
    "master": {"packets": 450000, "bytes": 123456789}
  }
}
```

---

## Integration Steps

### Step 1: Modify Analyzer (Week 2)

Update `network-mirror/analyzer/main.py`:

```python
from mqtt_publisher import TrafficPublisher

# In main():
publisher = TrafficPublisher(
    broker_host=os.getenv('MQTT_BROKER', 'localhost'),
    broker_port=int(os.getenv('MQTT_PORT', 1883))
)
publisher.connect()

# In packet_callback():
if analyzer.packet_count % 100 == 0:
    stats = {...}
    publisher.publish_all(stats)
```

### Step 2: Configure FUXA (Week 3)

1. Add MQTT device in FUXA
2. Subscribe to topics
3. Create dashboard
4. Add widgets

### Step 3: Deploy (Week 4)

1. Build Docker images
2. Deploy via docker-compose
3. Configure monitoring
4. Test end-to-end

---

## Dashboard Widgets

### Network Topology
- SVG-based visualization
- Component nodes (Master, VCC, UPF, Gen)
- Connection lines
- Animated traffic flow
- Real-time updates

### Real-time Statistics
- Total packets gauge
- Packet rate gauge
- Protocol distribution pie chart
- Component traffic bar chart
- Component health indicators

### Custom Widgets
- Network flow visualization
- Traffic heatmap
- Protocol analysis
- Performance metrics

---

## Performance Characteristics

### Throughput
- Support up to 1Gbps traffic
- MQTT broker: 1000+ messages/second
- FUXA: Real-time updates

### Latency
- MQTT publish latency: < 100ms
- Dashboard update latency: < 1 second
- Widget render latency: < 500ms

### Resource Usage
- Mosquitto: < 100MB RAM
- FUXA: < 500MB RAM
- Analyzer: < 200MB RAM
- Total: < 1GB RAM

---

## Monitoring

### Key Metrics

1. **MQTT Broker**
   - Connected clients
   - Published messages
   - Subscribed topics
   - Memory usage

2. **FUXA**
   - Dashboard load time
   - Widget update latency
   - Browser memory usage

3. **Analyzer**
   - Packet capture rate
   - MQTT publish success rate
   - Memory usage

### Monitoring Commands

```bash
# Check MQTT broker
docker exec vpp-mosquitto mosquitto_sub -h localhost -t '$SYS/#'

# Check FUXA logs
docker logs -f vpp-fuxa

# Check analyzer logs
docker logs -f vpp-analyzer-mqtt

# Monitor resources
docker stats
```

---

## Troubleshooting

### FUXA Cannot Connect to MQTT

1. Verify Mosquitto is running: `docker ps | grep mosquitto`
2. Check Mosquitto logs: `docker logs vpp-mosquitto`
3. Test MQTT connection: `mosquitto_sub -h localhost -t "test"`

### No Data in Dashboard

1. Verify analyzer is publishing: Check analyzer logs
2. Verify MQTT topics: `mosquitto_sub -h localhost -t "vpp/traffic/#"`
3. Check FUXA device configuration
4. Verify topic subscriptions

### High CPU Usage

1. Reduce dashboard refresh rate
2. Limit number of widgets
3. Check analyzer performance
4. Monitor MQTT broker load

---

## Testing

### Unit Tests

```bash
# Test MQTT publisher
python -m pytest tests/test_mqtt_publisher.py -v

# Test REST API
python -m pytest tests/test_rest_api.py -v
```

### Integration Tests

```bash
# Test end-to-end integration
python -m pytest tests/test_integration.py -v
```

### Manual Testing

1. Start FUXA stack: `docker-compose -f docker-compose-fuxa.yml up -d`
2. Access FUXA: http://localhost:1881
3. Configure MQTT device
4. Create dashboard
5. Verify data flow

---

## Deployment

### Development

```bash
docker-compose -f docker-compose-fuxa.yml up -d
```

### Production

1. Update docker-compose-fuxa.yml with production settings
2. Configure SSL/TLS for MQTT
3. Set up monitoring and alerting
4. Configure backup and recovery
5. Deploy via orchestration platform

---

## Documentation

- **INTEGRATION_GUIDE.md** - Step-by-step integration guide
- **DEPLOYMENT_GUIDE.md** - Production deployment guide
- **TROUBLESHOOTING.md** - Troubleshooting guide
- **FUXA_IMPLEMENTATION_PLAN.md** - Detailed implementation plan

---

## References

- **FUXA GitHub**: https://github.com/frangoteam/FUXA
- **FUXA Wiki**: https://github.com/frangoteam/FUXA/wiki
- **MQTT Protocol**: https://mqtt.org/
- **Mosquitto**: https://mosquitto.org/
- **Docker**: https://docs.docker.com/

---

## Support

For issues or questions:

1. Check TROUBLESHOOTING.md
2. Review FUXA documentation
3. Check MQTT documentation
4. Review Docker logs

---

## License

This integration framework is part of the OVS Network Traffic Mirroring project.

---

## Next Steps

1. **Week 1**: Set up environment and design architecture
2. **Week 2**: Implement MQTT publisher and REST API
3. **Week 3**: Configure FUXA and create dashboard
4. **Week 4**: Test and deploy to production

See **FUXA_IMPLEMENTATION_PLAN.md** for detailed timeline.

</content>
