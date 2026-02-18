# Phase 2 Integration Guide - LoRaWAN

## Overview

This guide documents the integration of the LoRaWAN protocol adapter into the VPP Phase 2 Simulation Framework.

**LoRaWAN** - Long Range Wide Area Network for IoT applications

## Architecture

### New Adapter

```
services/protocol_adapters/
├── lorawan_adapter.py      # LoRaWAN network communication
├── base.py                 # Updated with LoRaWAN protocol type
└── protocol_management.py  # Updated adapter registration
```

### Protocol Type

New protocol type added to `ProtocolType` enum:

```python
class ProtocolType(Enum):
    LORAWAN = "lorawan"
```

## Dependencies

Added to `requirements.txt`:

```
# Phase 2 Integration - LoRaWAN
pylorawan==0.2.13
```

### Installation

```bash
pip install -r vpp-phase2-simulation/requirements.txt
```

## LoRaWAN Adapter

### Features

- Network server connection management
- Device registration and management
- Uplink/downlink message handling
- Message queue management
- Callback support for message events
- Device information retrieval
- Network information access

### Architecture

The adapter implements:

1. **LoRaWANConfig** - Network configuration
2. **LoRaWANDevice** - Device state management
3. **LoRaWANAdapter** - Main adapter class

### Usage Example

```python
from services.protocol_adapters.lorawan_adapter import LoRaWANAdapter

# Create adapter
adapter = LoRaWANAdapter("lorawan-1")

# Connect to LoRaWAN network
config = {
    'gateway_url': 'http://localhost:8080',
    'app_id': 'vpp-app',
    'app_key': 'app-key-123',
    'region': 'EU868',
    'class_type': 'A'
}
adapter.connect(config)

# Register device
device_config = {
    'dev_eui': '0011223344556677',
    'app_eui': '0011223344556677',
    'app_key': 'device-key-123'
}
adapter.register_device(device_config)

# Send uplink message
payload = b'\x01\x02\x03\x04'
adapter.send_uplink('0011223344556677', payload, port=1)

# Send downlink message
adapter.send_downlink('0011223344556677', b'\x05\x06\x07\x08', port=1)

# Get device info
info = adapter.get_device_info('0011223344556677')
print(f"Device: {info['dev_eui']}, Uplink count: {info['fcnt_up']}")

# List all devices
devices = adapter.list_devices()

# Receive message from queue
message = adapter.receive_message()

# Disconnect
adapter.disconnect()
```

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| gateway_url | str | http://localhost:8080 | LoRaWAN gateway URL |
| app_id | str | vpp-app | Application ID |
| app_key | str | default-key | Application key |
| region | str | EU868 | LoRaWAN region |
| class_type | str | A | LoRaWAN class (A, B, C) |

### Supported Regions

- EU868 - Europe
- US915 - United States
- AS923 - Asia
- AU915 - Australia
- CN470 - China
- CN779 - China
- IN865 - India
- KR920 - South Korea
- RU864 - Russia

### LoRaWAN Classes

- **Class A** - Bi-directional end devices (default)
- **Class B** - Bi-directional end devices with scheduled receive
- **Class C** - Bi-directional end devices with continuous receive

## Device Management

### Register Device

```python
device_config = {
    'dev_eui': '0011223344556677',
    'app_eui': '0011223344556677',
    'app_key': 'device-key'
}
adapter.register_device(device_config)
```

### Unregister Device

```python
adapter.unregister_device('0011223344556677')
```

### Get Device Info

```python
info = adapter.get_device_info('0011223344556677')
# Returns: {
#     'dev_eui': '0011223344556677',
#     'app_eui': '0011223344556677',
#     'fcnt_up': 5,
#     'fcnt_down': 2,
#     'last_seen': '2026-02-18T17:30:00'
# }
```

### List Devices

```python
devices = adapter.list_devices()
for device in devices:
    print(f"{device['dev_eui']}: Up={device['fcnt_up']}, Down={device['fcnt_down']}")
```

## Message Handling

### Send Uplink Message

```python
# Uplink: Device → Network Server
payload = b'\x01\x02\x03\x04'
adapter.send_uplink(
    dev_eui='0011223344556677',
    payload=payload,
    port=1  # LoRaWAN port (1-223)
)
```

### Send Downlink Message

```python
# Downlink: Network Server → Device
adapter.send_downlink(
    dev_eui='0011223344556677',
    payload=b'\x05\x06\x07\x08',
    port=1,
    confirmed=True  # Require confirmation
)
```

### Message Queue

```python
# Get queued messages
queue = adapter.get_message_queue()

# Receive message from queue
message = adapter.receive_message(timeout=1.0)

# Clear queue
adapter.clear_message_queue()
```

## Callbacks

### Register Uplink Callback

```python
def on_uplink(message):
    print(f"Uplink from {message['dev_eui']}: {message['payload']}")

adapter.register_uplink_callback(on_uplink)
```

### Register Downlink Callback

```python
def on_downlink(message):
    print(f"Downlink to {message['dev_eui']}: {message['payload']}")

adapter.register_downlink_callback(on_downlink)
```

## Protocol Message Format

### Send via Protocol Message

```python
from services.protocol_adapters.base import ProtocolMessage
import time

message = ProtocolMessage(
    protocol="lorawan",
    message_id="msg-1",
    source="vpp",
    destination="lorawan-network",
    timestamp=time.time(),
    data={
        'dev_eui': '0011223344556677',
        'payload': b'\x01\x02\x03\x04',
        'direction': 'uplink',  # or 'downlink'
        'port': 1,
        'confirmed': False
    }
)

adapter.send_message(message)
```

### Receive via Protocol Message

```python
message = adapter.receive_message()
if message:
    print(f"From: {message.source}")
    print(f"Data: {message.data}")
```

## Network Information

```python
info = adapter.get_network_info()
# Returns: {
#     'gateway_url': 'http://localhost:8080',
#     'app_id': 'vpp-app',
#     'region': 'EU868',
#     'class': 'A',
#     'connected': True,
#     'devices_count': 5,
#     'messages_queued': 2
# }
```

## Protocol Management Integration

### Adapter Registration

All adapters are automatically registered in `ProtocolManagementService`:

```python
from services.protocol_management import get_protocol_management_service

service = get_protocol_management_service()

# List supported protocols
protocols = service.list_supported_protocols()
# Output: [..., 'lorawan']

# Create adapter
adapter_info = service.create_adapter("lorawan", "lorawan-1")

# Get adapter
adapter = service.get_adapter("lorawan-1")

# List all adapters
adapters = service.list_adapters()
```

## Testing

### Run Tests

```bash
cd vpp-phase2-simulation
pytest tests/test_phase2_lorawan_adapter.py -v
```

### Test Coverage

- Adapter creation and initialization
- Connection management
- Device registration/unregistration
- Uplink/downlink messages
- Message queue operations
- Callback functionality
- Message validation and parsing
- Network information retrieval

## Docker Integration

### Build Image

```bash
cd vpp-phase2-simulation
docker build -f Dockerfile -t vpp-phase2:phase2 .
```

### Run Container

```bash
docker-compose up -d vpp-api
```

The container includes all Phase 2 protocol libraries.

## Message Format

### LoRaWAN Frame Structure

```
MHDR (1 byte) | DevAddr (4 bytes) | FCtrl (1 byte) | FCnt (2 bytes) | Payload (0-250 bytes)
```

### Parsed Message

```python
{
    'mhdr': 0x40,
    'dev_addr': '00000000',
    'fctrl': 0,
    'fcnt': 0,
    'payload': '01020304'
}
```

## Troubleshooting

### Connection Issues

```python
# Check configuration
print(adapter.config.__dict__)

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Device Not Found

```python
# List registered devices
devices = adapter.list_devices()
print(f"Registered devices: {len(devices)}")

# Check device info
info = adapter.get_device_info('0011223344556677')
if info is None:
    print("Device not registered")
```

### Message Queue Issues

```python
# Check queue size
queue = adapter.get_message_queue()
print(f"Messages in queue: {len(queue)}")

# Clear queue if needed
adapter.clear_message_queue()
```

## Performance Considerations

- Message queue is in-memory (suitable for simulation)
- Callbacks are synchronous (blocking)
- Frame counters are per-device
- No persistence between restarts

## Security Notes

- App keys should be stored securely
- Device EUIs should be unique
- Consider encryption for sensitive payloads
- Validate all incoming messages

## References

- [LoRaWAN Specification](https://lora-alliance.org/)
- [LoRaWAN Regional Parameters](https://lora-alliance.org/resource_hub/lorawan-regional-parameters/)
- [pylorawan Documentation](https://github.com/LoRa-Alliance/pylorawan)

## Support

For issues or questions:

1. Check the test files: `tests/test_phase2_lorawan_adapter.py`
2. Review adapter implementation: `services/protocol_adapters/lorawan_adapter.py`
3. Check logs for error messages
4. Refer to LoRaWAN specification

---

**Last Updated:** February 2026
**Status:** Phase 2 Integration Complete
**Next Phase:** Phase 3 (BACnet, EtherCAT)
