# Phase 3 Integration Guide - XMPP, RS-232, RS-485, DL/T Protocols

## Overview

This guide documents the integration of four protocol adapters into the VPP Phase 2 Simulation Framework:

1. **XMPP** - Extensible Messaging and Presence Protocol
2. **RS-232** - Serial communication protocol
3. **RS-485** - Multi-drop serial communication
4. **DL/T** - Chinese power grid protocols (634, 645, 698, 476)

## Architecture

### New Adapters

```
services/protocol_adapters/
├── xmpp_adapter.py         # XMPP messaging
├── rs232_adapter.py        # RS-232 serial
├── rs485_adapter.py        # RS-485 multi-drop
├── dlt_adapter.py          # DL/T power protocols
├── base.py                 # Updated with new types
└── protocol_management.py  # Updated registration
```

### Protocol Types

New protocol types added to `ProtocolType` enum:

```python
class ProtocolType(Enum):
    XMPP = "xmpp"
    RS232 = "rs232"
    RS485 = "rs485"
    DLT634 = "dlt634"
    DLT645 = "dlt645"
    DLT698 = "dlt698"
    DLT476 = "dlt476"
```

## Dependencies

Added to `requirements.txt`:

```
sleekxmpp==1.8.0
pyserial==3.5
pyserial-asyncio==0.6
```

## XMPP Adapter

### Features

- XMPP server connection
- Contact management
- Message sending/receiving
- Presence management
- Callback support

### Usage Example

```python
from services.protocol_adapters.xmpp_adapter import XMPPAdapter

adapter = XMPPAdapter("xmpp-1")
adapter.connect({
    'jid': 'user@localhost',
    'password': 'password',
    'server': 'localhost',
    'port': 5222
})

# Add contact
adapter.add_contact('device@localhost')

# Send message
adapter.send_message(ProtocolMessage(
    protocol="xmpp",
    message_id="msg-1",
    source="user@localhost",
    destination="device@localhost",
    timestamp=time.time(),
    data={
        'recipient': 'device@localhost',
        'body': 'Hello Device',
        'type': 'chat'
    }
))

# Set presence
adapter.set_presence("Available", "available")

# List contacts
contacts = adapter.list_contacts()
```

## RS-232 Adapter

### Features

- Serial port communication
- Configurable baud rates
- Data format options
- Flow control support

### Usage Example

```python
from services.protocol_adapters.rs232_adapter import RS232Adapter

adapter = RS232Adapter("rs232-1")
adapter.connect({
    'port': 'COM1',
    'baudrate': 9600,
    'bytesize': 8,
    'stopbits': 1,
    'parity': 'N'
})

# Send data
adapter.send_data(b'\x01\x02\x03\x04')

# Receive data
data = adapter.receive_data(timeout=1.0)

# Get port info
info = adapter.get_port_info()
```

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| port | str | COM1 | Serial port name |
| baudrate | int | 9600 | Baud rate |
| bytesize | int | 8 | Data bits |
| stopbits | int | 1 | Stop bits |
| parity | str | N | Parity (N/E/O) |
| timeout | float | 1.0 | Read timeout |

## RS-485 Adapter

### Features

- Multi-drop serial communication
- Device addressing (0-247)
- Device management
- Bus monitoring

### Usage Example

```python
from services.protocol_adapters.rs485_adapter import RS485Adapter

adapter = RS485Adapter("rs485-1")
adapter.connect({
    'port': 'COM1',
    'baudrate': 9600,
    'parity': 'E'
})

# Add devices
adapter.add_device(1)
adapter.add_device(2)
adapter.add_device(3)

# Send data to device
adapter.send_data(1, b'\x03\x04\x05\x06')

# Receive data
msg = adapter.receive_data(timeout=1.0)

# Get device info
info = adapter.get_device_info(1)

# List devices
devices = adapter.list_devices()

# Get bus info
bus_info = adapter.get_bus_info()
```

## DL/T Adapter

### Features

- Chinese power grid protocol support
- Meter data reading/writing
- Device management
- Multiple protocol versions

### Supported Protocols

- **DL/T 634** - Power system data exchange
- **DL/T 645** - Electric meter data exchange
- **DL/T 698** - Smart meter data exchange
- **DL/T 476** - Power system communication

### Usage Example

```python
from services.protocol_adapters.dlt_adapter import DLTAdapter

adapter = DLTAdapter("dlt-1")
adapter.connect({
    'protocol_version': '645',
    'device_id': '001',
    'baud_rate': 1200
})

# Register meter
adapter.register_device('001001')

# Write meter data
adapter.write_meter_data('001001', '00000000', 1234.56)

# Read meter data
value = adapter.read_meter_data('001001', '00000000')

# Get device info
info = adapter.get_device_info('001001')

# List devices
devices = adapter.list_devices()

# Get network info
net_info = adapter.get_network_info()
```

### Data Identifiers (DL/T 645)

Common data identifiers:
- `00000000` - Total active energy
- `00000001` - Positive active energy
- `00000002` - Negative active energy
- `00010000` - Total reactive energy
- `00010001` - Positive reactive energy
- `00010002` - Negative reactive energy

## Protocol Management Integration

All adapters are automatically registered:

```python
from services.protocol_management import get_protocol_management_service

service = get_protocol_management_service()

# List all protocols
protocols = service.list_supported_protocols()
# [..., 'xmpp', 'rs232', 'rs485', 'dlt']

# Create adapter
adapter = service.create_adapter("xmpp", "xmpp-1")

# Get adapter
adapter = service.get_adapter("xmpp-1")
```

## Testing

### Run Tests

```bash
cd vpp-phase2-simulation
pytest tests/test_phase3_adapters.py -v
```

### Test Coverage

- Adapter creation and initialization
- Connection management
- Device/contact management
- Message handling
- Data reading/writing
- Status reporting

## Docker Integration

### Build Image

```bash
cd vpp-phase2-simulation
docker build -f Dockerfile -t vpp-phase2:phase3 .
```

### Run Container

```bash
docker-compose up -d vpp-api
```

## Message Format

### XMPP Message

```python
{
    'from': 'user@localhost',
    'to': 'contact@localhost',
    'body': 'Message text',
    'type': 'chat',
    'timestamp': '2026-02-18T17:30:00',
    'id': 'msg-1234567890'
}
```

### RS-232 Message

```python
{
    'data': b'\x01\x02\x03\x04',
    'length': 4,
    'timestamp': '2026-02-18T17:30:00'
}
```

### RS-485 Message

```python
{
    'address': 1,
    'data': '01020304',
    'frame': '0101020304',
    'timestamp': '2026-02-18T17:30:00'
}
```

### DL/T Message

```python
{
    'device_id': '001001',
    'data_identifier': '00000000',
    'value': 1234.56,
    'timestamp': '2026-02-18T17:30:00',
    'protocol': '645'
}
```

## Troubleshooting

### XMPP Connection Issues

```python
# Check configuration
print(adapter.config.__dict__)

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### RS-232 Port Issues

```bash
# List available ports
python -m serial.tools.list_ports

# Check port permissions (Linux)
ls -la /dev/ttyUSB0
```

### RS-485 Bus Issues

```python
# Check bus info
info = adapter.get_bus_info()
print(f"Devices: {info['device_count']}")
print(f"Queued: {info['messages_queued']}")
```

### DL/T Device Issues

```python
# List devices
devices = adapter.list_devices()
for device in devices:
    print(f"{device['device_id']}: {device['last_seen']}")
```

## References

- [XMPP RFC 6120](https://xmpp.org/rfcs/rfc6120.html)
- [RS-232 Standard](https://en.wikipedia.org/wiki/RS-232)
- [RS-485 Standard](https://en.wikipedia.org/wiki/RS-485)
- [DL/T 645 Specification](http://www.cec.org.cn/)
- [sleekxmpp Documentation](https://sleekxmpp.readthedocs.io/)
- [pyserial Documentation](https://pyserial.readthedocs.io/)

## Support

For issues or questions:

1. Check the test files: `tests/test_phase3_adapters.py`
2. Review adapter implementations
3. Check logs for error messages
4. Refer to protocol documentation

---

**Last Updated:** February 2026
**Status:** Phase 3 Integration Complete
**Next Phase:** Phase 4 (BACnet, EtherCAT)
