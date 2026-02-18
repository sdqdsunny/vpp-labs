# Phase 2 Integration - LoRaWAN Quick Reference

## What's New

One new IoT protocol adapter integrated:

| Protocol | Adapter | Use Case |
|----------|---------|----------|
| **LoRaWAN** | `LoRaWANAdapter` | Long-range IoT communication |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r vpp-phase2-simulation/requirements.txt
```

### 2. Create and Use Adapter

```python
from services.protocol_adapters.lorawan_adapter import LoRaWANAdapter

adapter = LoRaWANAdapter("my-lorawan")
adapter.connect({
    'gateway_url': 'http://localhost:8080',
    'app_id': 'my-app',
    'app_key': 'my-key'
})

# Register device
adapter.register_device({
    'dev_eui': '0011223344556677',
    'app_eui': '0011223344556677',
    'app_key': 'device-key'
})

# Send uplink
adapter.send_uplink('0011223344556677', b'\x01\x02\x03\x04')

# Receive message
msg = adapter.receive_message()
```

### 3. Use Protocol Management Service

```python
from services.protocol_management import get_protocol_management_service

service = get_protocol_management_service()
adapter = service.create_adapter("lorawan", "my-lorawan")
```

## Common Tasks

### Connect to Network

```python
adapter.connect({
    'gateway_url': 'http://localhost:8080',
    'app_id': 'vpp-app',
    'app_key': 'app-key-123',
    'region': 'EU868',
    'class_type': 'A'
})
```

### Register Device

```python
adapter.register_device({
    'dev_eui': '0011223344556677',
    'app_eui': '0011223344556677',
    'app_key': 'device-key'
})
```

### Send Uplink Message

```python
# Device → Network Server
adapter.send_uplink(
    dev_eui='0011223344556677',
    payload=b'\x01\x02\x03\x04',
    port=1
)
```

### Send Downlink Message

```python
# Network Server → Device
adapter.send_downlink(
    dev_eui='0011223344556677',
    payload=b'\x05\x06\x07\x08',
    port=1,
    confirmed=True
)
```

### Get Device Info

```python
info = adapter.get_device_info('0011223344556677')
print(f"Uplink count: {info['fcnt_up']}")
print(f"Downlink count: {info['fcnt_down']}")
```

### List All Devices

```python
devices = adapter.list_devices()
for device in devices:
    print(f"{device['dev_eui']}: {device['last_seen']}")
```

### Register Callbacks

```python
def on_uplink(msg):
    print(f"Uplink: {msg['payload']}")

def on_downlink(msg):
    print(f"Downlink: {msg['payload']}")

adapter.register_uplink_callback(on_uplink)
adapter.register_downlink_callback(on_downlink)
```

### Message Queue

```python
# Get queue
queue = adapter.get_message_queue()

# Receive from queue
msg = adapter.receive_message()

# Clear queue
adapter.clear_message_queue()
```

### Get Network Info

```python
info = adapter.get_network_info()
print(f"Connected: {info['connected']}")
print(f"Devices: {info['devices_count']}")
print(f"Queued: {info['messages_queued']}")
```

## File Structure

```
vpp-phase2-simulation/
├── services/protocol_adapters/
│   ├── lorawan_adapter.py        [NEW] 400+ lines
│   ├── base.py                   [UPDATED] Added LoRaWAN type
│   └── protocol_management.py    [UPDATED] Added registration
├── tests/
│   └── test_phase2_lorawan_adapter.py [NEW] 300+ lines
├── requirements.txt              [UPDATED] Added pylorawan
├── PHASE2_INTEGRATION_GUIDE.md   [NEW] Complete guide
└── PHASE2_QUICK_REFERENCE.md    [NEW] This file
```

## Testing

```bash
# Run all Phase 2 tests
pytest tests/test_phase2_lorawan_adapter.py -v

# Run specific test
pytest tests/test_phase2_lorawan_adapter.py::TestLoRaWANAdapter::test_send_uplink -v
```

## LoRaWAN Regions

```python
# Supported regions
'EU868'   # Europe
'US915'   # United States
'AS923'   # Asia
'AU915'   # Australia
'CN470'   # China
'CN779'   # China
'IN865'   # India
'KR920'   # South Korea
'RU864'   # Russia
```

## LoRaWAN Classes

```python
'A'  # Bi-directional (default)
'B'  # Bi-directional with scheduled receive
'C'  # Bi-directional with continuous receive
```

## Protocol Type Enum

```python
from services.protocol_adapters.base import ProtocolType

ProtocolType.LORAWAN  # "lorawan"
```

## Docker

### Build

```bash
cd vpp-phase2-simulation
docker build -f Dockerfile -t vpp-phase2:phase2 .
```

### Run

```bash
docker-compose up -d vpp-api
```

## Troubleshooting

### Import Error

```python
import sys
sys.path.insert(0, '/path/to/vpp-phase2-simulation')
```

### Connection Failed

```python
# Check config
print(adapter.config.__dict__)

# Enable debug
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Device Not Found

```python
# List devices
devices = adapter.list_devices()
print(f"Total: {len(devices)}")
```

## Message Format

### Uplink Message

```python
{
    'type': 'uplink',
    'dev_eui': '0011223344556677',
    'payload': '01020304',
    'port': 1,
    'fcnt': 5,
    'timestamp': '2026-02-18T17:30:00',
    'rssi': -100,
    'snr': 10.0
}
```

### Downlink Message

```python
{
    'type': 'downlink',
    'dev_eui': '0011223344556677',
    'payload': '05060708',
    'port': 1,
    'fcnt': 2,
    'confirmed': True,
    'timestamp': '2026-02-18T17:30:00'
}
```

## API Reference

### Adapter Methods

| Method | Purpose |
|--------|---------|
| `connect(config)` | Connect to network |
| `disconnect()` | Disconnect from network |
| `register_device(config)` | Register device |
| `unregister_device(dev_eui)` | Unregister device |
| `send_uplink(dev_eui, payload, port)` | Send uplink |
| `send_downlink(dev_eui, payload, port, confirmed)` | Send downlink |
| `get_device_info(dev_eui)` | Get device info |
| `list_devices()` | List all devices |
| `register_uplink_callback(callback)` | Register callback |
| `register_downlink_callback(callback)` | Register callback |
| `get_message_queue()` | Get queue |
| `clear_message_queue()` | Clear queue |
| `send_message(message)` | Send protocol message |
| `receive_message(timeout)` | Receive from queue |
| `get_network_info()` | Get network info |

## Next Phase

Phase 3 will add:
- BACnet adapter
- EtherCAT adapter

See `PHASE2_INTEGRATION_GUIDE.md` for detailed documentation.

---

**Quick Links:**
- [Full Integration Guide](PHASE2_INTEGRATION_GUIDE.md)
- [Test File](tests/test_phase2_lorawan_adapter.py)
- [LoRaWAN Adapter](services/protocol_adapters/lorawan_adapter.py)
- [Protocol Management](services/protocol_management.py)
