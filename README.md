# VPP Virtual Power Plant Simulation and Visualization System

A comprehensive industrial control system simulation platform featuring Virtual Power Plant (VPP) coordination, real-time data visualization, and industrial protocol testing.

## 🎯 Project Overview

This project implements a complete VPP system with:
- **Real-time 3D Visualization**: Interactive 3D scene showing power flow between four nodes
- **Industrial Protocol Support**: 11 ICS protocols (Modbus, DNP3, OPC UA, CAN, PROFINET, IEC 61850, DLT 645, RS-232, RS-485, LoRaWAN, XMPP)
- **Security Testing Tools**: Comprehensive security testing for industrial protocols
- **Microservices Architecture**: Modular design with independent services for each VPP component

## 📦 System Components

### 1. VPP Traffic Visualization (3D)
Real-time 3D visualization of power flow and data exchange between VPP nodes.

**Location**: `vpp-traffic-visualization/`

**Features**:
- ✅ Real-time particle flow animation (red for control, cyan for telemetry)
- ✅ Chinese labels for all nodes (控制协调中心, 发电侧_01, 储能侧_01, 用电侧_01)
- ✅ Live statistics display (total bytes, packet count, data rate)
- ✅ WebSocket-based real-time updates

**Quick Start**:
```bash
cd vpp-traffic-visualization
docker-compose up -d
# Access at http://localhost:8080
```

### 2. VPP Phase 2 Simulation
Core VPP simulation with four modules and industrial protocol adapters.

**Location**: `vpp-phase2-simulation/`

**Modules**:
- Coordinator (VCC): Central coordination center
- Power Generation: Power generation module
- Energy Storage: Battery storage management
- Demand: Load management

**Protocols Implemented**:
- **ICS Protocols**: Modbus TCP/RTU, DNP3, OPC UA, CAN Bus, PROFINET, IEC 61850, DLT 645
- **Communication**: MQTT, HTTP/HTTPS, WebSocket
- **Serial**: RS-232, RS-485
- **IoT**: LoRaWAN, XMPP

### 3. Security Testing Tools
Comprehensive security testing framework for industrial protocols.

**Features**:
- DNP3 Attack Detection (5 detection rules)
- Modbus Security Testing
- OPC UA Security Testing
- CAN Bus Security Testing
- Boofuzz Fuzzing Framework

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.8+
- Git

### Deployment

**Option 1: Simple Deployment (Recommended)**
```bash
docker-compose -f docker-compose-simple.yml up -d
```

**Option 2: Full Microservices**
```bash
docker-compose -f docker-compose-microservices.yml up -d
```

**Option 3: Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Start VPP simulation
python vpp-phase2-simulation/app_coordinator.py

# In another terminal, start 3D visualization backend
cd vpp-traffic-visualization
python backend/app.py

# Access frontend at http://localhost:8080
```

## 📊 Recent Fixes (Latest Commit: 4e20aa6)

### Fix 1: Total Bytes Display
- **Issue**: Right-side statistics showed total bytes as 0
- **Root Cause**: WebSocket field name mismatch (`size` vs `packet_size`)
- **Solution**: Updated backend to send correct field name
- **File**: `vpp-traffic-visualization/backend/app.py`

### Fix 2: Particle Flow Visibility
- **Issue**: No visible particle flow between nodes
- **Root Causes**: Low particle count, short lifetime, small size
- **Solutions**:
  - Increased particle count: 1-5 → 3-15
  - Increased lifetime: 2-3s → 3-5s
  - Increased size: 0.3-0.6 → 0.5-1.0
  - Increased packet size: 100 → 150 bytes
- **Files**: 
  - `vpp-traffic-visualization/frontend/js/main.js`
  - `vpp-traffic-visualization/backend/services/vpp_data_connector.py`

### Fix 3: Chinese Labels
- **Issue**: English names on nodes
- **Solution**: Added Chinese display names with proper font support
- **Names**:
  - Master → 控制协调中心 (Control Coordination Center)
  - Power_01 → 发电侧_01 (Power Generation Side_01)
  - Storage_01 → 储能侧_01 (Energy Storage Side_01)
  - Demand_01 → 用电侧_01 (Electricity Demand Side_01)
- **Files**:
  - `vpp-traffic-visualization/frontend/js/scene-manager.js`
  - `vpp-traffic-visualization/backend/services/vpp_data_connector.py`

## 📁 Project Structure

```
.
├── vpp-traffic-visualization/      # 3D visualization system
│   ├── backend/                    # Flask backend with WebSocket
│   ├── frontend/                   # Three.js 3D visualization
│   └── docker-compose.yml
├── vpp-phase2-simulation/          # VPP simulation core
│   ├── services/                   # Protocol adapters & modules
│   ├── routes/                     # API endpoints
│   ├── models/                     # Data models
│   └── tests/                      # Unit tests (142 tests, 100% passing)
├── vpp-master/                     # VPP master simulation
├── docker-compose-simple.yml       # Simple deployment
├── docker-compose-microservices.yml # Full microservices
└── README.md                       # This file
```

## 🧪 Testing

### Run All Tests
```bash
# VPP Phase 2 tests
pytest vpp-phase2-simulation/tests/ -v

# 3D Visualization tests
pytest vpp-traffic-visualization/backend/tests/ -v
```

### Test Coverage
- **Total Tests**: 142 unit tests
- **Pass Rate**: 100%
- **Coverage**: Core functionality, protocol adapters, security tools

## 📚 Documentation

- **3D Visualization**: See `vpp-traffic-visualization/README.md`
- **Protocol Adapters**: See `vpp-phase2-simulation/PHASE1_INTEGRATION_GUIDE.md`
- **Security Tools**: See `vpp-phase2-simulation/SECURITY_TOOLS_INTEGRATION_GUIDE.md`
- **Deployment**: See `DOCKER_DEPLOYMENT_GUIDE.md`

## 🔧 Configuration

### Environment Variables
```bash
# VPP Simulation
VPP_API_URL=http://vpp-simulation:8001
VPP_COORDINATOR_PORT=5000
VPP_POWER_PORT=5001
VPP_STORAGE_PORT=5002
VPP_DEMAND_PORT=5003

# 3D Visualization
BACKEND_PORT=5000
FRONTEND_PORT=8080
WEBSOCKET_URL=ws://localhost:5000
```

### Docker Compose Configuration
- **Simple Mode**: Single container with all services
- **Microservices Mode**: Separate containers for each component
- **Development Mode**: Local Python execution

## 🐛 Troubleshooting

### 3D Visualization Not Loading
1. Check backend is running: `docker ps | grep vpp`
2. Verify WebSocket connection: Check browser console
3. Check backend logs: `docker logs vpp-backend`

### No Particle Flow
1. Verify data is being generated: Check backend logs
2. Check particle parameters in `frontend/js/main.js`
3. Verify packet size in `backend/services/vpp_data_connector.py`

### Chinese Labels Not Displaying
1. Verify font support: Check `scene-manager.js` font configuration
2. Check canvas size: Should be 512×128 for proper rendering
3. Verify label size: Should be 8×2 for visibility

## 📞 Support

For issues or questions:
1. Check the documentation in the respective component directories
2. Review test files for usage examples
3. Check Docker logs: `docker logs <container-name>`

## 📄 License

See LICENSE file for details.

## 🎓 Project Status

✅ **All Core Features Implemented**
- 3D Visualization with real-time updates
- 11 Industrial protocols
- Security testing framework
- Comprehensive test coverage
- Production-ready deployment

**Last Updated**: February 21, 2026
**Latest Commit**: 4e20aa6 - Fix 3D visualization: packet_size field, particle flow, and Chinese labels
