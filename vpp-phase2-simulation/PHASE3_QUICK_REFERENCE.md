# Phase 3 Quick Reference - XMPP, RS-232, RS-485, DL/T

## Quick Start

### XMPP Adapter

```python
from services.protocol_adapters.xmpp_adapter import XMPPAdapter

adapter = XMPPAdapter("xmpp-1")
adapter.connect({
    'jid': 'user@localhost',
    'password': 'password',
    'server': 'localhost',
    'port': 5222
})
adapter.add_contact('device@localhost')
adapter.set_presence("Available", "available")
```

### RS-232 Adapter

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
adapter.send_data(b'\x01\x02\x03\x04')
data = adapter.receive_data(timeout=1.0)
```

### RS-485 Adapter

```python
from services.protocol_adapters.rs485_adapter import RS485Adapter

adapter = RS485Adapter("rs485-1")
adapter.connect({
    'port': 'COM1',
    'baudrate': 9600,
    'parity': 'E'
})
adapter.add_device(1)
adapter.send_data(1, b'\x03\x04\x05\x06')
devices = adapter.list_devices()
```

### DL/T Adapter

```python
from services.protocol_adapters.dlt_adapter import DLTAdapter

adapter = DLTAdapter("dlt-1")
adapter.connect({
    'protocol_version': '645',
    'device_id': '001',
    'baud_rate': 1200
})
adapter.register_device('001001')
adapter.write_meter_data('001001', '00000000', 1234.56)
value = adapter.read_meter_data('001001', '00000000')
```

## Common Tasks

### XMPP: Send Message

```python
from services.protocol_adapters.base import ProtocolMessage
import time

message = ProtocolMessage(
    protocol="xmpp",
    message_id="msg-1",
    source="user@localhost",
    destination="contact@localhost",
    timestamp=time.time(),
    data={
        'recipient': 'contact@localhost',
        'body': 'Hello',
        'type': 'chat'
    }
)
adapter.send_message(message)
```

### RS-232: Configure Port

```python
config = {
    'port': '/dev/ttyUSB0',      # Linux
    'baudrate': 115200,
    'bytesize': 8,
    'stopbits': 1,
    'parity': 'N',
    'timeout': 2.0
}
adapter.connect(config)
```

### RS-485: Multi-Device Communication

```python
# Add multiple devices
for addr in range(1, 4):
    adapter.add_device(addr)

# Send to each device
for addr in adapter.list_devices():
    adapter.send_data(addr, b'\x01\x02\x03')
```

### DL/T: Read Multiple Meters

```python
# Register meters
for i in range(1, 4):
    adapter.register_device(f'001{i:03d}')

# Read data from all
for device in adapter.list_devices():
    value = adapter.read_meter_data(device['device_id'], '00000000')
    print(f"{device['device_id']}: {value}")
```

## Protocol Types

| Protocol | Type | Use Case |
|----------|------|----------|
| XMPP | Messaging | Real-time device communication |
| RS-232 | Serial | Point-to-point serial links |
| RS-485 | Serial | Multi-drop serial networks |
| DL/T 645 | Power | Electric meter data exchange |
| DL/T 634 | Power | Power system data exchange |
| DL/T 698 | Power | Smart meter data exchange |
| DL/T 476 | Power | Power system communication |

## Data Identifiers (DL/T 645)

```
00000000 - Total active energy
00000001 - Positive active energy
00000002 - Negative active energy
00010000 - Total reactive energy
00010001 - Positive reactive energy
00010002 - Negative reactive energy
00020000 - Total apparent energy
00020001 - Positive apparent energy
00020002 - Negative apparent energy
```

## Status Checking

```python
# Get adapter status
status = adapter.get_status()
print(f"Connected: {status['is_connected']}")
print(f"Messages: {status['message_count']}")
print(f"Errors: {status['error_count']}")
print(f"Uptime: {status['uptime_seconds']}s")
```

## Error Handling

```python
from services.protocol_adapters.base import ProtocolException

try:
    adapter.connect(config)
except ProtocolException as e:
    print(f"Connection failed: {e}")
```

## Testing

```bash
# Run all Phase 3 tests
pytest tests/test_phase3_adapters.py -v

# Run specific adapter tests
pytest tests/test_phase3_adapters.py::TestXMPPAdapter -v
pytest tests/test_phase3_adapters.py::TestRS232Adapter -v
pytest tests/test_phase3_adapters.py::TestRS485Adapter -v
pytest tests/test_phase3_adapters.py::TestDLTAdapter -v
```

## Integration with Protocol Management

```python
from services.protocol_management import get_protocol_management_service

service = get_protocol_management_service()

# List all protocols
protocols = service.list_supported_protocols()

# Create adapter
adapter_info = service.create_adapter("xmpp", "xmpp-1")

# Get adapter
adapter = service.get_adapter("xmpp-1")

# List all adapters
adapters = service.list_adapters()
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| XMPP connection fails | Check JID format, password, server address |
| RS-232 port not found | Use `python -m serial.tools.list_ports` |
| RS-485 no response | Check baud rate, parity, device address |
| DL/T device not responding | Verify device ID, protocol version, baud rate |

---

**Last Updated:** February 2026
**Phase:** 3 (XMPP, RS-232, RS-485, DL/T)
