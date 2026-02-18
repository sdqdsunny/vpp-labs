# Phase 1 Integration Guide - OPC UA, CAN, Profinet

## Overview

This guide documents the integration of three major industrial protocol adapters into the VPP Phase 2 Simulation Framework:

1. **OPC UA** - Open Platform Communications Unified Architecture
2. **CAN** - Controller Area Network
3. **Profinet** - Process Field Network

## Architecture

### New Adapters

All adapters follow the unified `ProtocolAdapter` base class pattern:

```
services/protocol_adapters/
├── opcua_adapter.py       # OPC UA client implementation
├── can_adapter.py         # CAN bus communication
├── profinet_adapter.py    # Profinet/Siemens PLC integration
├── base.py               # Updated with new protocol types
└── protocol_management.py # Updated adapter registration
```

### Protocol Types

New protocol types added to `ProtocolType` enum:

```python
class ProtocolType(Enum):
    OPCUA = "opcua"
    CAN = "can"
    PROFINET = "profinet"
```

## Dependencies

Added to `requirements.txt`:

```
# Phase 1 Integration - OPC UA, CAN, Profinet
opcua==0.98.13
asyncua==0.10.0
python-can==4.2.2
cantools==4.4.1
pycomm3==0.32.0
```

### Installation

```bash
pip install -r vpp-phase2-simulation/requirements.txt
```

## OPC UA Adapter

### Features

- Asynchronous and synchronous connection support
- Read/write variables from OPC UA servers
- Browse address space
- Subscription support (planned)

### Usage Example

```python
from services.protocol_adapters.opcua_adapter import OPCUAAdapter

# Create adapter
adapter = OPCUAAdapter("opcua-1")

# Connect to OPC UA server
config = {
    'endpoint': 'opc.tcp://localhost:4840',
    'namespace': 'http://vpp.simulation'
}
adapter.connect(config)

# Read variable
value = adapter.read_variable("ns=2;i=1001")

# Write variable
adapter.write_variable("ns=2;i=1002", 42)

# Browse address space
children = adapter.browse("i=85")

# Disconnect
adapter.disconnect()
```

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| endpoint | str | opc.tcp://localhost:4840 | OPC UA server endpoint |
| namespace | str | http://vpp.simulation | OPC UA namespace |

## CAN Adapter

### Features

- Multiple CAN interface support (SocketCAN, PEAK, Vector, etc.)
- Standard CAN and CAN FD support
- Message filtering
- Bus state monitoring

### Usage Example

```python
from services.protocol_adapters.can_adapter import CANAdapter
from services.protocol_adapters.base import ProtocolMessage

# Create adapter
adapter = CANAdapter("can-1")

# Connect to CAN bus
config = {
    'interface': 'socketcan',
    'channel': 'vcan0',
    'bitrate': 500000
}
adapter.connect(config)

# Send CAN message
message = ProtocolMessage(
    protocol="can",
    message_id="msg-1",
    source="vpp",
    destination="can-device",
    timestamp=time.time(),
    data={
        'can_id': 0x123,
        'data': b'\x01\x02\x03\x04\x05\x06\x07\x08',
        'is_extended': False
    }
)
adapter.send_message(message)

# Receive CAN message
received = adapter.receive_message(timeout=1.0)

# Add filter
adapter.add_filter(can_id=0x123, mask=0x7FF)

# Get bus state
state = adapter.get_bus_state()

# Disconnect
adapter.disconnect()
```

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| interface | str | socketcan | CAN interface type |
| channel | str | vcan0 | CAN channel/device |
| bitrate | int | 500000 | CAN bus bitrate (bps) |

### Supported Interfaces

- `socketcan` - Linux SocketCAN
- `peak` - PEAK PCAN
- `vector` - Vector CANoe
- `kvaser` - Kvaser Leaf
- `virtual` - Virtual CAN

## Profinet Adapter

### Features

- Siemens PLC communication via Profinet
- Read/write PLC variables
- Batch read/write operations
- Device information retrieval

### Usage Example

```python
from services.protocol_adapters.profinet_adapter import ProfinetAdapter

# Create adapter
adapter = ProfinetAdapter("profinet-1")

# Connect to PLC
config = {
    'ip_address': '192.168.1.100',
    'port': 2000,
    'slot': 1
}
adapter.connect(config)

# Read variable
value = adapter.read_variable("DB1.DBD0")

# Write variable
adapter.write_variable("DB1.DBD4", 123.45)

# Read multiple variables
values = adapter.read_multiple(["DB1.DBD0", "DB1.DBD4", "DB1.DBD8"])

# Write multiple variables
adapter.write_multiple({
    "DB1.DBD0": 100,
    "DB1.DBD4": 200,
    "DB1.DBD8": 300
})

# Get device info
info = adapter.get_device_info()

# Disconnect
adapter.disconnect()
```

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| ip_address | str | 192.168.1.100 | PLC IP address |
| port | int | 2000 | Profinet port |
| slot | int | 1 | PLC slot number |

### PLC Variable Naming

- `DB1.DBD0` - Double word at offset 0 in DB1
- `DB1.DBW0` - Word at offset 0 in DB1
- `DB1.DBB0` - Byte at offset 0 in DB1
- `DB1.DBX0.0` - Bit 0 at offset 0 in DB1

## Protocol Management Integration

### Adapter Registration

All adapters are automatically registered in `ProtocolManagementService`:

```python
from services.protocol_management import get_protocol_management_service

service = get_protocol_management_service()

# List supported protocols
protocols = service.list_supported_protocols()
# Output: ['iec61850', 'modbus', 'dnp3', 'mqtt', 'opcua', 'can', 'profinet']

# Create adapter
adapter_info = service.create_adapter("opcua", "opcua-1")

# Get adapter
adapter = service.get_adapter("opcua-1")

# List all adapters
adapters = service.list_adapters()
```

## Testing

### Run Tests

```bash
cd vpp-phase2-simulation
pytest tests/test_phase1_integration_adapters.py -v
```

### Test Coverage

- Adapter creation and initialization
- Protocol type definitions
- Message validation and parsing
- Registry operations
- Status reporting

## Docker Integration

### Build Image

```bash
cd vpp-phase2-simulation
docker build -f Dockerfile -t vpp-phase2:latest .
```

### Run Container

```bash
docker-compose up -d vpp-api
```

The container includes all Phase 1 protocol libraries.

## Next Steps

### Phase 2 Integration (Planned)

- LoRaWAN adapter
- BACnet adapter
- EtherCAT adapter

### Enhancements

- Subscription support for OPC UA
- CAN FD support improvements
- Profinet security features
- Protocol bridging (CAN ↔ OPC UA, etc.)

## Troubleshooting

### OPC UA Connection Issues

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check endpoint
adapter.config.endpoint  # Verify correct endpoint
```

### CAN Bus Issues

```bash
# Check virtual CAN interface
ip link show vcan0

# Create virtual CAN if needed
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

### Profinet Connection Issues

```python
# Verify PLC IP and port
adapter.config.ip_address
adapter.config.port

# Check device info
info = adapter.get_device_info()
```

## References

- [OPC UA Specification](https://opcfoundation.org/)
- [CAN Protocol](https://en.wikipedia.org/wiki/CAN_bus)
- [Profinet Standard](https://www.profibus.com/profinet/)
- [python-opcua Documentation](https://github.com/FreeOpcUa/python-opcua)
- [python-can Documentation](https://python-can.readthedocs.io/)
- [pycomm3 Documentation](https://github.com/ottowayi/pycomm3)

## Support

For issues or questions:

1. Check the test files: `tests/test_phase1_integration_adapters.py`
2. Review adapter implementations in `services/protocol_adapters/`
3. Check logs for error messages
4. Refer to library documentation

---

**Last Updated:** February 2026
**Status:** Phase 1 Integration Complete
