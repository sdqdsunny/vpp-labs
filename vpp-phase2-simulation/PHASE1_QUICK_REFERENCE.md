# Phase 1 Integration - Quick Reference

## What's New

Three new industrial protocol adapters integrated:

| Protocol | Adapter | Use Case |
|----------|---------|----------|
| **OPC UA** | `OPCUAAdapter` | Industrial automation, data exchange |
| **CAN** | `CANAdapter` | Automotive, embedded systems |
| **Profinet** | `ProfinetAdapter` | Siemens PLC communication |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r vpp-phase2-simulation/requirements.txt
```

### 2. Create and Use Adapter

```python
from services.protocol_adapters.opcua_adapter import OPCUAAdapter

adapter = OPCUAAdapter("my-opcua")
adapter.connect({'endpoint': 'opc.tcp://localhost:4840'})
value = adapter.read_variable("ns=2;i=1001")
adapter.disconnect()
```

### 3. Use Protocol Management Service

```python
from services.protocol_management import get_protocol_management_service

service = get_protocol_management_service()
adapter = service.create_adapter("can", "my-can")
```

## Adapter Comparison

### OPC UA Adapter

```python
# Connect
adapter.connect({
    'endpoint': 'opc.tcp://localhost:4840',
    'namespace': 'http://vpp.simulation'
})

# Read/Write
value = adapter.read_variable("ns=2;i=1001")
adapter.write_variable("ns=2;i=1002", 42)

# Browse
children = adapter.browse("i=85")
```

### CAN Adapter

```python
# Connect
adapter.connect({
    'interface': 'socketcan',
    'channel': 'vcan0',
    'bitrate': 500000
})

# Send/Receive
adapter.send_message(message)
received = adapter.receive_message(timeout=1.0)

# Filter
adapter.add_filter(can_id=0x123)
```

### Profinet Adapter

```python
# Connect
adapter.connect({
    'ip_address': '192.168.1.100',
    'port': 2000,
    'slot': 1
})

# Read/Write
value = adapter.read_variable("DB1.DBD0")
adapter.write_variable("DB1.DBD4", 123.45)

# Batch operations
values = adapter.read_multiple(["DB1.DBD0", "DB1.DBD4"])
```

## File Structure

```
vpp-phase2-simulation/
├── services/protocol_adapters/
│   ├── opcua_adapter.py       ← NEW
│   ├── can_adapter.py         ← NEW
│   ├── profinet_adapter.py    ← NEW
│   ├── base.py                ← UPDATED
│   └── protocol_management.py ← UPDATED
├── tests/
│   └── test_phase1_integration_adapters.py ← NEW
├── requirements.txt           ← UPDATED
├── PHASE1_INTEGRATION_GUIDE.md ← NEW
└── PHASE1_QUICK_REFERENCE.md  ← NEW (this file)
```

## Testing

```bash
# Run all Phase 1 tests
pytest tests/test_phase1_integration_adapters.py -v

# Run specific test
pytest tests/test_phase1_integration_adapters.py::TestOPCUAAdapter -v
```

## Common Tasks

### Check Supported Protocols

```python
from services.protocol_management import get_protocol_management_service

service = get_protocol_management_service()
print(service.list_supported_protocols())
# Output: ['iec61850', 'modbus', 'dnp3', 'mqtt', 'opcua', 'can', 'profinet']
```

### Create Multiple Adapters

```python
service = get_protocol_management_service()

opcua = service.create_adapter("opcua", "opcua-1")
can = service.create_adapter("can", "can-1")
profinet = service.create_adapter("profinet", "profinet-1")
```

### Get Adapter Status

```python
adapter = service.get_adapter("opcua-1")
status = adapter['status']
print(f"Connected: {status['is_connected']}")
print(f"Messages: {status['message_count']}")
print(f"Errors: {status['error_count']}")
```

### List All Active Adapters

```python
adapters = service.list_adapters()
for adapter in adapters:
    print(f"{adapter['adapter_id']}: {adapter['protocol']}")
```

## Protocol Type Enum

```python
from services.protocol_adapters.base import ProtocolType

# Available types
ProtocolType.OPCUA      # "opcua"
ProtocolType.CAN        # "can"
ProtocolType.PROFINET   # "profinet"
ProtocolType.IEC61850   # "iec61850"
ProtocolType.MODBUS     # "modbus"
ProtocolType.DNP3       # "dnp3"
ProtocolType.MQTT       # "mqtt"
```

## Docker

### Build

```bash
cd vpp-phase2-simulation
docker build -f Dockerfile -t vpp-phase2:phase1 .
```

### Run

```bash
docker-compose up -d vpp-api
```

## Troubleshooting

### Import Error

```python
# Make sure you're in the right directory
import sys
sys.path.insert(0, '/path/to/vpp-phase2-simulation')
```

### Connection Failed

```python
# Check configuration
print(adapter.config.__dict__)

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### CAN Interface Not Found

```bash
# Create virtual CAN interface
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

## Next Phase

Phase 2 will add:
- LoRaWAN adapter
- BACnet adapter
- EtherCAT adapter

See `PHASE1_INTEGRATION_GUIDE.md` for detailed documentation.

---

**Quick Links:**
- [Full Integration Guide](PHASE1_INTEGRATION_GUIDE.md)
- [Test File](tests/test_phase1_integration_adapters.py)
- [Protocol Management](services/protocol_management.py)
- [Base Adapter](services/protocol_adapters/base.py)
