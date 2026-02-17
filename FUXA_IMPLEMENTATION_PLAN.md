# FUXA Integration Implementation Plan

**Project**: OVS Network Traffic Mirroring + VPP System  
**Date**: 2026-02-17  
**Status**: Implementation Planning  
**Approach**: Hybrid (MQTT + REST API + Custom Widgets)

---

## Overview

This document provides a detailed week-by-week implementation plan for integrating FUXA with the VPP network traffic analysis system. The integration will enable real-time visualization of traffic flow between VPP master station and functional modules (VCC, UPF, device simulators).

---

## Architecture Summary

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
- **MQTT Publisher**: Modified analyzer publishes traffic statistics
- **MQTT Broker**: Mosquitto for message distribution
- **FUXA Server**: Node.js backend for data aggregation
- **FUXA UI**: Angular frontend for visualization
- **Custom Widgets**: SVG-based network topology and flow visualization

---

## Implementation Timeline

### Week 1: Setup & Design (Days 1-5)

#### Day 1-2: Environment Setup
**Deliverables**:
- [ ] FUXA installed and running locally
- [ ] Mosquitto MQTT broker configured
- [ ] Development environment ready
- [ ] Docker setup verified

**Tasks**:
1. Pull FUXA Docker image
   ```bash
   docker pull frangoteam/fuxa:latest
   ```

2. Pull Mosquitto Docker image
   ```bash
   docker pull eclipse-mosquitto:latest
   ```

3. Create docker-compose-fuxa.yml for local development
4. Start services and verify connectivity
5. Access FUXA web UI at http://localhost:1881

**Acceptance Criteria**:
- FUXA web UI is accessible
- Mosquitto broker is running
- Both services are on same Docker network
- No errors in logs

#### Day 3-4: Architecture Analysis
**Deliverables**:
- [ ] FUXA architecture documented
- [ ] Device driver interface understood
- [ ] MQTT integration points identified
- [ ] Data flow diagram created

**Tasks**:
1. Study FUXA source code structure
   - `/server` - Node.js backend
   - `/client` - Angular frontend
   - `/devices` - Device drivers
   - `/plugins` - Plugin system

2. Analyze device driver interface
   - How devices are registered
   - How data is published
   - How real-time updates work

3. Review MQTT integration
   - MQTT device driver implementation
   - Topic subscription mechanism
   - Data transformation pipeline

4. Create detailed data flow diagram

**Acceptance Criteria**:
- Architecture document complete
- Device driver interface documented
- MQTT integration points identified
- Data flow diagram created

#### Day 5: Data Schema Design
**Deliverables**:
- [ ] MQTT topic structure defined
- [ ] Data payload format specified
- [ ] REST API endpoints designed
- [ ] Data transformation rules documented

**Tasks**:
1. Define MQTT topic hierarchy
   ```
   vpp/traffic/stats          - Overall statistics
   vpp/traffic/rate           - Packet rate
   vpp/traffic/protocols      - Protocol distribution
   vpp/traffic/flows          - Top flows
   vpp/components/master      - Master station stats
   vpp/components/vcc         - VCC coordinator stats
   vpp/components/upf         - UPF stats
   vpp/components/gen         - Device simulator stats
   ```

2. Define data payload format
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
       {"src": "10.0.1.10", "dst": "10.0.1.20", "packets": 450000},
       {"src": "10.0.1.20", "dst": "10.0.1.30", "packets": 370000}
     ],
     "components": {
       "master": {"packets": 450000, "bytes": 123456789},
       "vcc": {"packets": 370000, "bytes": 98765432},
       "upf": {"packets": 250000, "bytes": 87654321},
       "gen": {"packets": 150000, "bytes": 65432109}
     }
   }
   ```

3. Design REST API endpoints
   - `GET /api/traffic/stats` - Current statistics
   - `GET /api/traffic/history` - Historical data
   - `GET /api/traffic/flows` - Top flows
   - `GET /api/components/status` - Component health

4. Document data transformation rules

**Acceptance Criteria**:
- MQTT topic structure finalized
- Data payload format specified
- REST API endpoints designed
- Transformation rules documented

---

### Week 2: Data Bridge Development (Days 6-10)

#### Day 6-7: MQTT Publisher Implementation
**Deliverables**:
- [ ] Modified analyzer with MQTT publishing
- [ ] MQTT publisher class created
- [ ] Statistics collection enhanced
- [ ] Tests passing

**Tasks**:
1. Create `network-mirror/analyzer/mqtt_publisher.py`
   - TrafficPublisher class
   - MQTT connection management
   - Topic publishing logic
   - Error handling

2. Modify `network-mirror/analyzer/main.py`
   - Integrate MQTT publisher
   - Publish statistics periodically
   - Handle MQTT connection failures
   - Add MQTT configuration via environment variables

3. Create unit tests for MQTT publisher
   - Test connection
   - Test publishing
   - Test error handling

4. Update Docker image
   - Add paho-mqtt dependency
   - Update Dockerfile
   - Rebuild image

**Acceptance Criteria**:
- MQTT publisher implemented
- Statistics published to MQTT topics
- Tests passing
- Docker image updated

#### Day 8: REST API Wrapper
**Deliverables**:
- [ ] REST API wrapper created
- [ ] Endpoints implemented
- [ ] Data caching implemented
- [ ] Tests passing

**Tasks**:
1. Create `network-mirror/analyzer/rest_api.py`
   - Flask/Bottle REST API
   - Endpoints for statistics
   - Data caching mechanism
   - Error handling

2. Implement endpoints
   - `/api/traffic/stats` - Current statistics
   - `/api/traffic/history` - Historical data
   - `/api/components/status` - Component health

3. Add data caching
   - In-memory cache
   - Cache expiration
   - Cache invalidation

4. Create integration tests

**Acceptance Criteria**:
- REST API implemented
- All endpoints working
- Data caching functional
- Tests passing

#### Day 9-10: Data Transformer & Integration
**Deliverables**:
- [ ] Data transformer created
- [ ] End-to-end data flow working
- [ ] Integration tests passing
- [ ] Performance verified

**Tasks**:
1. Create `network-mirror/analyzer/data_transformer.py`
   - Transform analyzer data to FUXA format
   - Handle data aggregation
   - Implement error handling
   - Add logging

2. Integrate all components
   - Analyzer → MQTT Publisher
   - Analyzer → REST API
   - Data Transformer → MQTT
   - Data Transformer → REST API

3. Create integration tests
   - Test data flow
   - Test transformations
   - Test error scenarios

4. Performance testing
   - Measure latency
   - Verify throughput
   - Check resource usage

**Acceptance Criteria**:
- Data transformer working
- End-to-end data flow verified
- Integration tests passing
- Performance acceptable

---

### Week 3: FUXA Integration (Days 11-15)

#### Day 11-12: FUXA Device Configuration
**Deliverables**:
- [ ] MQTT device configured in FUXA
- [ ] Topics subscribed
- [ ] Data flowing into FUXA
- [ ] Real-time updates working

**Tasks**:
1. Create FUXA device configuration
   - Device type: MQTT
   - Broker: mosquitto:1883
   - Topics: vpp/traffic/*
   - Update interval: 1 second

2. Configure FUXA device via UI
   - Add new device
   - Set MQTT parameters
   - Subscribe to topics
   - Test connection

3. Verify data flow
   - Check FUXA logs
   - Verify topic subscriptions
   - Monitor data updates

4. Create device configuration file
   - `fuxa-integration/fuxa-device-config.json`
   - Document configuration
   - Create import/export scripts

**Acceptance Criteria**:
- MQTT device configured
- Topics subscribed
- Data flowing into FUXA
- Real-time updates verified

#### Day 13: Dashboard Creation
**Deliverables**:
- [ ] Dashboard layout created
- [ ] Widgets added
- [ ] Real-time data displayed
- [ ] Dashboard saved

**Tasks**:
1. Create dashboard in FUXA
   - Set dashboard name: "VPP Traffic Visualization"
   - Set grid size and layout
   - Configure refresh rate

2. Add widgets
   - Network topology diagram (SVG)
   - Real-time statistics (gauges)
   - Protocol distribution (pie chart)
   - Top flows (table)
   - Component health (indicators)

3. Configure widget data bindings
   - Bind to MQTT topics
   - Set update intervals
   - Configure display formats

4. Test dashboard
   - Verify all widgets update
   - Check data accuracy
   - Monitor performance

**Acceptance Criteria**:
- Dashboard created
- All widgets functional
- Data displayed correctly
- Performance acceptable

#### Day 14-15: Custom Widgets Development
**Deliverables**:
- [ ] Custom network topology widget created
- [ ] Custom flow visualization widget created
- [ ] Widgets integrated into dashboard
- [ ] Tests passing

**Tasks**:
1. Create custom network topology widget
   - SVG-based visualization
   - Component nodes (master, VCC, UPF, gen)
   - Connection lines
   - Animated traffic flow
   - Real-time updates

2. Create custom flow visualization widget
   - Traffic flow diagram
   - Color-coded by protocol
   - Bandwidth indicators
   - Real-time animation

3. Integrate widgets into dashboard
   - Add to dashboard layout
   - Configure data bindings
   - Test functionality

4. Create widget documentation
   - Usage guide
   - Configuration options
   - Customization guide

**Acceptance Criteria**:
- Custom widgets created
- Widgets integrated
- Real-time updates working
- Documentation complete

---

### Week 4: Testing & Deployment (Days 16-20)

#### Day 16-17: Integration Testing
**Deliverables**:
- [ ] Integration test suite created
- [ ] All tests passing
- [ ] Test coverage > 80%
- [ ] Test report generated

**Tasks**:
1. Create integration test suite
   - Test MQTT publisher
   - Test REST API
   - Test data transformer
   - Test FUXA integration

2. Test scenarios
   - Normal operation
   - High traffic load
   - Component failures
   - Network issues

3. Performance testing
   - Measure latency
   - Verify throughput
   - Check resource usage
   - Monitor memory leaks

4. Generate test report

**Acceptance Criteria**:
- All tests passing
- Test coverage > 80%
- Performance acceptable
- Test report complete

#### Day 18: User Acceptance Testing
**Deliverables**:
- [ ] UAT test cases created
- [ ] UAT executed
- [ ] Issues documented
- [ ] Sign-off obtained

**Tasks**:
1. Create UAT test cases
   - Functional requirements
   - Non-functional requirements
   - User workflows
   - Edge cases

2. Execute UAT
   - Test with real traffic
   - Verify visualizations
   - Check accuracy
   - Test interactivity

3. Document issues
   - Bug reports
   - Enhancement requests
   - Performance issues

4. Obtain sign-off

**Acceptance Criteria**:
- UAT completed
- Issues documented
- Sign-off obtained
- Ready for production

#### Day 19-20: Production Deployment
**Deliverables**:
- [ ] Production environment prepared
- [ ] System deployed
- [ ] Monitoring configured
- [ ] Documentation complete

**Tasks**:
1. Prepare production environment
   - Configure servers
   - Set up networking
   - Configure security
   - Set up monitoring

2. Deploy system
   - Build Docker images
   - Push to registry
   - Deploy via docker-compose
   - Verify all services

3. Configure monitoring
   - Set up metrics collection
   - Configure alerting
   - Set up logging
   - Create dashboards

4. Create documentation
   - Deployment guide
   - Operations manual
   - Troubleshooting guide
   - User guide

**Acceptance Criteria**:
- System deployed
- All services running
- Monitoring configured
- Documentation complete

---

## Deliverables by Week

### Week 1: Setup & Design
- FUXA and Mosquitto running
- Architecture documentation
- Data schema defined
- MQTT topic structure
- REST API design

### Week 2: Data Bridge
- MQTT publisher implemented
- REST API wrapper created
- Data transformer developed
- Integration tests passing
- Docker image updated

### Week 3: FUXA Integration
- MQTT device configured
- Dashboard created
- Custom widgets developed
- Real-time updates working
- Widget documentation

### Week 4: Testing & Deployment
- Integration tests passing
- UAT completed
- Production deployment
- Monitoring configured
- Documentation complete

---

## File Structure

```
fuxa-integration/
├── mqtt-publisher.py              # MQTT publisher for analyzer
├── rest-api.py                    # REST API wrapper
├── data-transformer.py            # Data transformation logic
├── fuxa-device-config.json        # FUXA device configuration
├── docker-compose-fuxa.yml        # Docker Compose for FUXA stack
├── custom-widgets/
│   ├── network-topology.html      # Network topology widget
│   ├── flow-visualization.html    # Flow visualization widget
│   └── README.md                  # Widget documentation
├── tests/
│   ├── test_mqtt_publisher.py     # MQTT publisher tests
│   ├── test_rest_api.py           # REST API tests
│   ├── test_data_transformer.py   # Data transformer tests
│   └── test_integration.py        # Integration tests
├── INTEGRATION_GUIDE.md           # Step-by-step integration guide
├── DEPLOYMENT_GUIDE.md            # Production deployment guide
├── TROUBLESHOOTING.md             # Troubleshooting guide
└── README.md                      # Project overview
```

---

## Key Milestones

| Milestone | Date | Status |
|-----------|------|--------|
| Environment Setup | Day 2 | Planned |
| Architecture Design | Day 4 | Planned |
| Data Schema | Day 5 | Planned |
| MQTT Publisher | Day 7 | Planned |
| REST API | Day 8 | Planned |
| Data Transformer | Day 10 | Planned |
| FUXA Configuration | Day 12 | Planned |
| Dashboard Creation | Day 13 | Planned |
| Custom Widgets | Day 15 | Planned |
| Integration Testing | Day 17 | Planned |
| UAT | Day 18 | Planned |
| Production Deployment | Day 20 | Planned |

---

## Success Criteria

### Functional
- ✅ MQTT publisher publishes traffic statistics
- ✅ REST API provides access to analyzer data
- ✅ FUXA receives and displays real-time data
- ✅ Dashboard shows network topology
- ✅ Custom widgets display traffic flow
- ✅ Real-time updates working

### Non-Functional
- ✅ Latency < 1 second
- ✅ Throughput > 1000 packets/second
- ✅ Memory usage < 500MB
- ✅ CPU usage < 20%
- ✅ Uptime > 99.9%

### Quality
- ✅ Test coverage > 80%
- ✅ All tests passing
- ✅ No critical bugs
- ✅ Documentation complete
- ✅ Code reviewed

---

## Risk Mitigation

### Risk 1: MQTT Broker Performance
**Risk**: Mosquitto may not handle high message rate  
**Mitigation**: 
- Performance testing early
- Message batching if needed
- Alternative broker (RabbitMQ) if required

### Risk 2: FUXA Customization Complexity
**Risk**: Custom widgets may be difficult to implement  
**Mitigation**:
- Prototype early
- Use FUXA examples
- Consult community

### Risk 3: Data Accuracy
**Risk**: Transformed data may not match original  
**Mitigation**:
- Comprehensive testing
- Data validation
- Comparison with original

### Risk 4: Performance Degradation
**Risk**: System may slow down with high traffic  
**Mitigation**:
- Performance testing
- Optimization if needed
- Caching strategy

---

## Dependencies

### External
- FUXA (GitHub: frangoteam/FUXA)
- Mosquitto MQTT Broker
- Docker & Docker Compose
- Python 3.8+

### Internal
- OVS Network Mirror (existing)
- Protocol Analyzer (existing)
- VPP System (existing)

---

## Next Steps

1. **Immediate** (Today)
   - Review this plan
   - Confirm approach
   - Allocate resources

2. **Week 1** (Days 1-5)
   - Set up environment
   - Design architecture
   - Define data schema

3. **Week 2** (Days 6-10)
   - Implement data bridge
   - Create REST API
   - Develop transformer

4. **Week 3** (Days 11-15)
   - Configure FUXA
   - Create dashboard
   - Develop widgets

5. **Week 4** (Days 16-20)
   - Test system
   - Deploy production
   - Document

---

## Contact & Support

For questions or issues:
- Review FUXA documentation: https://github.com/frangoteam/FUXA/wiki
- Check MQTT documentation: https://mqtt.org/
- Consult Angular docs: https://angular.io/docs

</content>
