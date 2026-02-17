# FUXA Integration Guide

**Project**: OVS Network Traffic Mirroring + VPP System  
**Date**: 2026-02-17  
**Status**: Integration Guide

---

## Quick Start

### Prerequisites

- Docker & Docker Compose installed
- OVS Network Mirror system running
- Python 3.8+ (for MQTT publisher)
- 2GB+ RAM available
- 5GB+ disk space

### Step 1: Prepare Environment

```bash
# Navigate to fuxa-integration directory
cd fuxa-integration

# Create necessary directories
mkdir -p mosquitto/data mosquitto/log
mkdir -p fuxa_appdata fuxa_db
mkdir -p pcap_data analyzer_logs
```

### Step 2: Start FUXA Stack

```bash
# Start all services
docker-compose -f docker-compose-fuxa.yml up -d

# Verify services are running
docker-compose -f docker-compose-fuxa.yml ps

# Check logs
docker-compose -f docker-compose-fuxa.yml logs -f
```

### Step 3: Access FUXA

Open browser and navigate to:
```
http://localhost:1881
```

### Step 4: Configure MQTT Device

1. In FUXA, go to **Devices** → **Add Device**
2. Select **MQTT** as device type
3. Configure:
   - **Broker**: mosquitto:1883
   - **Client ID**: fuxa-vpp-analyzer
   - **Topics**: See device configuration below

### Step 5: Create Dashboard

1. Go to **Dashboards** → **New Dashboard**
2. Add widgets:
   - Network Topology (custom)
   - Real-time Statistics (gauges)
   - Protocol Distribution (pie chart)
   - Component Traffic (bar chart)
   - Component Health (indicators)

---

## Detailed Configuration

### MQTT Device Configuration

#### Connection Settings

| Setting | Value |
|---------|-------|
| Device Type | MQTT |
| Broker Host | mosquitto |
| Broker Port | 1883 |
| Client ID | fuxa-vpp-analyzer |
| Keep Alive | 60 seconds |
| QoS | 1 |
| Clean Session | true |

#### Topics to Subscribe

| Topic | Variable | Type | Description |
|-------|----------|------|-------------|
| vpp/traffic/stats | total_packets | number | Total packets captured |
| vpp/traffic/rate | packet_rate | number | Packets per second |
| vpp/traffic/protocols | protocol_dist | object | Protocol distribution |
| vpp/traffic/flows | top_flows | array | Top 10 flows |
| vpp/traffic/components/master | master_stats | object | Master station stats |
| vpp/traffic/components/vcc | vcc_stats | object | VCC coordinator stats |
| vpp/traffic/components/upf | upf_stats | object | UPF stats |
| vpp/traffic/components/gen | gen_stats | object | Generator stats |

### Dashboard Layout

#### Widget 1: Network Topology (Custom)
- **Type**: Custom SVG Widget
- **Position**: Top-left (6x6 grid)
- **Features**:
  - Component nodes (Master, VCC, UPF, Gen)
  - Connection lines
  - Animated traffic flow
  - Real-time updates

#### Widget 2: Total Packets (Gauge)
- **Type**: Gauge
- **Position**: Top-right (3x3 grid)
- **Range**: 0 - 10,000,000 packets
- **Variable**: total_packets

#### Widget 3: Packet Rate (Gauge)
- **Type**: Gauge
- **Position**: Top-right (3x3 grid)
- **Range**: 0 - 100,000 pps
- **Variable**: packet_rate

#### Widget 4: Protocol Distribution (Pie Chart)
- **Type**: Chart (Pie)
- **Position**: Middle-right (6x3 grid)
- **Variables**:
  - IEC61850 packets
  - Modbus packets
  - MQTT packets
  - DNP3 packets
  - Unknown packets

#### Widget 5: Component Traffic (Bar Chart)
- **Type**: Chart (Bar)
- **Position**: Bottom-left (6x3 grid)
- **Variables**:
  - Master packets
  - VCC packets
  - UPF packets
  - Generator packets

#### Widget 6: Component Health (Custom)
- **Type**: Custom Status Widget
- **Position**: Bottom-right (6x3 grid)
- **Components**:
  - Master station status
  - VCC coordinator status
  - UPF status
  - Generator status

---

## MQTT Publisher Integration

### Modify Analyzer

The analyzer needs to be modified to publish statistics to MQTT. Follow these steps:

#### Step 1: Install MQTT Library

```bash
pip install paho-mqtt
```

#### Step 2: Integrate MQTT Publisher

In `network-mirror/analyzer/main.py`, add:

```python
from mqtt_publisher import TrafficPublisher

# In main():
publisher = TrafficPublisher(
    broker_host=os.getenv('MQTT_BROKER', 'localhost'),
    broker_port=int(os.getenv('MQTT_PORT', 1883)),
    topic_prefix=os.getenv('MQTT_TOPIC_PREFIX', 'vpp/traffic')
)
publisher.connect()

# In packet_callback(), after updating statistics:
if analyzer.packet_count % 100 == 0:
    stats = {
        'total_packets': analyzer.packet_count,
        'packet_rate': calculate_rate(),
        'protocol_distribution': analyzer.protocol_stats,
        'top_flows': sorted(analyzer.flow_stats.items(), key=lambda x: x[1], reverse=True)[:10],
        'components': extract_component_stats()
    }
    publisher.publish_all(stats)
```

#### Step 3: Update Docker Image

Update `network-mirror/Dockerfile`:

```dockerfile
RUN pip install paho-mqtt
COPY mqtt_publisher.py /app/
```

#### Step 4: Rebuild Image

```bash
cd network-mirror
docker build -t vpp-analyzer:latest .
```

---

## REST API Integration (Optional)

### Create REST API Wrapper

Create `fuxa-integration/rest-api.py`:

```python
from flask import Flask, jsonify
import redis
import json
from datetime import datetime

app = Flask(__name__)
redis_client = redis.Redis(host='redis', port=6379, db=0)

@app.route('/api/traffic/stats', methods=['GET'])
def get_stats():
    """Get current traffic statistics"""
    stats = redis_client.get('vpp:traffic:stats')
    if stats:
        return jsonify(json.loads(stats))
    return jsonify({'error': 'No data available'}), 404

@app.route('/api/traffic/history', methods=['GET'])
def get_history():
    """Get historical traffic data"""
    history = redis_client.lrange('vpp:traffic:history', 0, -1)
    return jsonify([json.loads(h) for h in history])

@app.route('/api/components/status', methods=['GET'])
def get_component_status():
    """Get component health status"""
    components = {}
    for comp in ['master', 'vcc', 'upf', 'gen']:
        status = redis_client.get(f'vpp:component:{comp}:status')
        components[comp] = json.loads(status) if status else {'status': 'unknown'}
    return jsonify(components)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

---

## Custom Widgets

### Network Topology Widget

Create `fuxa-integration/custom-widgets/network-topology.html`:

```html
<div id="network-topology" style="width: 100%; height: 100%;">
  <svg id="topology-svg" width="100%" height="100%"></svg>
</div>

<script>
class NetworkTopologyWidget {
  constructor(elementId) {
    this.svg = document.getElementById('topology-svg');
    this.components = [
      { id: 'master', label: 'Master', x: 150, y: 100, color: '#FF6B6B' },
      { id: 'vcc', label: 'VCC', x: 350, y: 100, color: '#4ECDC4' },
      { id: 'upf', label: 'UPF', x: 150, y: 250, color: '#45B7D1' },
      { id: 'gen', label: 'Generator', x: 350, y: 250, color: '#FFA07A' }
    ];
    this.draw();
  }

  draw() {
    // Draw connections
    this.components.forEach((comp1, i) => {
      this.components.forEach((comp2, j) => {
        if (i < j) {
          const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
          line.setAttribute('x1', comp1.x);
          line.setAttribute('y1', comp1.y);
          line.setAttribute('x2', comp2.x);
          line.setAttribute('y2', comp2.y);
          line.setAttribute('stroke', '#ccc');
          line.setAttribute('stroke-width', '2');
          this.svg.appendChild(line);
        }
      });
    });

    // Draw components
    this.components.forEach(comp => {
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', comp.x);
      circle.setAttribute('cy', comp.y);
      circle.setAttribute('r', '40');
      circle.setAttribute('fill', comp.color);
      circle.setAttribute('opacity', '0.8');
      this.svg.appendChild(circle);

      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', comp.x);
      text.setAttribute('y', comp.y);
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('dy', '0.3em');
      text.setAttribute('fill', 'white');
      text.setAttribute('font-weight', 'bold');
      text.textContent = comp.label;
      this.svg.appendChild(text);
    });
  }

  updateTraffic(flows) {
    // Update animated traffic flow
    // Implementation depends on FUXA widget API
  }
}

// Initialize widget
const topology = new NetworkTopologyWidget('network-topology');
</script>
```

---

## Troubleshooting

### Issue: FUXA Cannot Connect to MQTT Broker

**Solution**:
1. Verify Mosquitto is running: `docker ps | grep mosquitto`
2. Check Mosquitto logs: `docker logs vpp-mosquitto`
3. Verify network connectivity: `docker network inspect vpp-net`
4. Test MQTT connection: `mosquitto_sub -h localhost -t "test"`

### Issue: No Data in FUXA Dashboard

**Solution**:
1. Verify analyzer is publishing: Check analyzer logs
2. Verify MQTT topics: `mosquitto_sub -h localhost -t "vpp/traffic/#"`
3. Check FUXA device configuration
4. Verify topic subscriptions in FUXA

### Issue: High CPU Usage

**Solution**:
1. Reduce update frequency in dashboard
2. Limit number of widgets
3. Check analyzer performance
4. Monitor MQTT broker load

### Issue: Memory Leak

**Solution**:
1. Check FUXA logs for errors
2. Restart FUXA service
3. Clear browser cache
4. Monitor Redis memory usage

---

## Performance Tuning

### MQTT Broker Optimization

```conf
# In mosquitto.conf
max_connections -1
max_queued_messages 1000
message_size_limit 0
max_inflight_messages 20
```

### FUXA Optimization

1. Reduce dashboard refresh rate
2. Limit number of widgets
3. Use data aggregation
4. Implement caching

### Analyzer Optimization

1. Increase pcap rotation interval
2. Reduce logging frequency
3. Optimize protocol identification
4. Use packet sampling for high traffic

---

## Monitoring

### Key Metrics to Monitor

1. **MQTT Broker**
   - Connected clients
   - Published messages
   - Subscribed topics
   - Memory usage

2. **FUXA**
   - Dashboard load time
   - Widget update latency
   - Browser memory usage
   - CPU usage

3. **Analyzer**
   - Packet capture rate
   - Protocol identification accuracy
   - MQTT publish success rate
   - Memory usage

### Monitoring Commands

```bash
# Check MQTT broker status
docker exec vpp-mosquitto mosquitto_sub -h localhost -t '$SYS/#'

# Check FUXA logs
docker logs -f vpp-fuxa

# Check analyzer logs
docker logs -f vpp-analyzer-mqtt

# Monitor resource usage
docker stats
```

---

## Maintenance

### Regular Tasks

1. **Daily**
   - Check service health
   - Monitor error logs
   - Verify data flow

2. **Weekly**
   - Review performance metrics
   - Clean up old pcap files
   - Update documentation

3. **Monthly**
   - Update Docker images
   - Review security settings
   - Optimize performance

### Backup & Recovery

```bash
# Backup FUXA configuration
docker cp vpp-fuxa:/usr/src/app/FUXA/server/_appdata ./backup/

# Backup MQTT data
docker cp vpp-mosquitto:/mosquitto/data ./backup/

# Restore from backup
docker cp ./backup/_appdata vpp-fuxa:/usr/src/app/FUXA/server/
```

---

## Next Steps

1. **Week 1**: Set up environment and configure MQTT
2. **Week 2**: Integrate MQTT publisher with analyzer
3. **Week 3**: Create FUXA dashboard and widgets
4. **Week 4**: Test and deploy to production

---

## Support & Resources

- **FUXA Documentation**: https://github.com/frangoteam/FUXA/wiki
- **MQTT Documentation**: https://mqtt.org/
- **Docker Documentation**: https://docs.docker.com/
- **Mosquitto Documentation**: https://mosquitto.org/

</content>
