"""
DL/T Protocol Adapter

Implements Chinese power grid protocols:
- DL/T 634: Power system data exchange protocol
- DL/T 645: Electric meter data exchange protocol
- DL/T 698: Smart meter data exchange protocol
- DL/T 476: Power system communication protocol

These are standard protocols used in China's power grid systems.
"""

from typing import Dict, Any, Optional, List
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class DLTConfig:
    """DL/T Protocol Configuration"""
    
    def __init__(self, protocol_version: str = "645", device_id: str = "001"):
        self.protocol_version = protocol_version  # 634, 645, 698, 476
        self.device_id = device_id
        self.baud_rate = 1200  # DL/T 645 default
        self.timeout = 2.0


class DLTDevice:
    """DL/T Device Information"""
    
    def __init__(self, device_id: str, protocol: str):
        self.device_id = device_id
        self.protocol = protocol
        self.last_seen = None
        self.data_items: Dict[str, Any] = {}


class DLTAdapter(ProtocolAdapter):
    """
    DL/T Protocol Adapter
    
    Implements Chinese power grid protocols for meter reading and power system communication.
    Supports DL/T 634, 645, 698, and 476 protocols.
    """
    
    def __init__(self, adapter_id: str = "dlt-adapter"):
        super().__init__(adapter_id, ProtocolType.DLT634)
        self.config: Optional[DLTConfig] = None
        self.devices: Dict[str, DLTDevice] = {}
        self.message_queue: List[Dict[str, Any]] = []
        self.data_callbacks: List[callable] = []
        
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Connect to DL/T network
        
        Args:
            config: Configuration with 'protocol_version', 'device_id'
            
        Returns:
            True if connection successful
        """
        try:
            self.config = DLTConfig(
                protocol_version=config.get('protocol_version', '645'),
                device_id=config.get('device_id', '001')
            )
            
            self.config.baud_rate = config.get('baud_rate', 1200)
            self.config.timeout = config.get('timeout', 2.0)
            
            self.is_connected = True
            self.connection_time = time.time()
            
            logger.info(
                f"Connected to DL/T {self.config.protocol_version} network "
                f"(Device: {self.config.device_id})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to DL/T network: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from DL/T network"""
        try:
            self.is_connected = False
            self.devices.clear()
            self.message_queue.clear()
            logger.info("Disconnected from DL/T network")
            return True
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def register_device(self, device_id: str) -> bool:
        """
        Register DL/T device
        
        Args:
            device_id: Device ID (meter number)
            
        Returns:
            True if device registered
        """
        try:
            if not self.is_connected:
                return False
            
            if device_id not in self.devices:
                self.devices[device_id] = DLTDevice(device_id, self.config.protocol_version)
                logger.info(f"Registered DL/T device: {device_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            return False
    
    def unregister_device(self, device_id: str) -> bool:
        """Unregister DL/T device"""
        try:
            if device_id in self.devices:
                del self.devices[device_id]
                logger.info(f"Unregistered DL/T device: {device_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister device: {e}")
            return False
    
    def read_meter_data(self, device_id: str, data_identifier: str) -> Optional[Any]:
        """
        Read meter data
        
        Args:
            device_id: Device ID
            data_identifier: Data identifier (e.g., "00000000" for total energy)
            
        Returns:
            Meter data or None if not found
        """
        try:
            if device_id not in self.devices:
                logger.error(f"Device not found: {device_id}")
                return None
            
            device = self.devices[device_id]
            return device.data_items.get(data_identifier)
            
        except Exception as e:
            logger.error(f"Failed to read meter data: {e}")
            return None
    
    def write_meter_data(self, device_id: str, data_identifier: str, value: Any) -> bool:
        """
        Write meter data
        
        Args:
            device_id: Device ID
            data_identifier: Data identifier
            value: Data value
            
        Returns:
            True if write successful
        """
        try:
            if not self.is_connected:
                return False
            
            if device_id not in self.devices:
                logger.error(f"Device not found: {device_id}")
                return False
            
            device = self.devices[device_id]
            device.data_items[data_identifier] = value
            device.last_seen = datetime.utcnow().isoformat()
            
            msg_data = {
                'device_id': device_id,
                'data_identifier': data_identifier,
                'value': value,
                'timestamp': device.last_seen,
                'protocol': self.config.protocol_version
            }
            
            self.message_queue.append(msg_data)
            self._record_message()
            
            # Trigger callbacks
            for callback in self.data_callbacks:
                try:
                    callback(msg_data)
                except Exception as e:
                    logger.error(f"Data callback error: {e}")
            
            logger.debug(f"Wrote data to {device_id}: {data_identifier}={value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write meter data: {e}")
            return False
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send DL/T message
        
        Args:
            message: Protocol message with device_id and data
            
        Returns:
            True if send successful
        """
        try:
            if not self.is_connected:
                return False
            
            device_id = message.data.get('device_id')
            data_identifier = message.data.get('data_identifier')
            value = message.data.get('value')
            
            if not all([device_id, data_identifier, value is not None]):
                logger.error("Invalid message: missing required fields")
                return False
            
            return self.write_meter_data(device_id, data_identifier, value)
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive DL/T message from queue
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Protocol message or None if queue empty
        """
        try:
            if not self.message_queue:
                return None
            
            msg_data = self.message_queue.pop(0)
            
            protocol_msg = ProtocolMessage(
                protocol=f"dlt{msg_data['protocol']}",
                message_id=f"msg-{int(time.time() * 1000)}",
                source=msg_data['device_id'],
                destination="collector",
                timestamp=time.time(),
                data=msg_data
            )
            
            return protocol_msg
            
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None
    
    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device information"""
        try:
            if device_id not in self.devices:
                return None
            
            device = self.devices[device_id]
            return {
                'device_id': device.device_id,
                'protocol': device.protocol,
                'last_seen': device.last_seen,
                'data_items': len(device.data_items)
            }
            
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return None
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """List all registered devices"""
        try:
            devices = []
            for device_id, device in self.devices.items():
                devices.append({
                    'device_id': device.device_id,
                    'protocol': device.protocol,
                    'last_seen': device.last_seen,
                    'data_items': len(device.data_items)
                })
            return devices
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
            return []
    
    def register_data_callback(self, callback: callable) -> None:
        """Register callback for data updates"""
        self.data_callbacks.append(callback)
        logger.debug("Registered data callback")
    
    def get_network_info(self) -> Optional[Dict[str, Any]]:
        """Get network information"""
        try:
            if not self.config:
                return None
            
            return {
                'protocol_version': self.config.protocol_version,
                'device_id': self.config.device_id,
                'baud_rate': self.config.baud_rate,
                'connected': self.is_connected,
                'device_count': len(self.devices),
                'messages_queued': len(self.message_queue)
            }
            
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            return None
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """Parse DL/T message data"""
        try:
            if len(data) < 10:
                return {}
            
            return {
                'start_flag': data[0],
                'address': data[1:7].hex(),
                'control': data[7],
                'length': data[8:10],
                'payload': data[10:].hex()
            }
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return {}
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """Encode DL/T message"""
        try:
            # DL/T frame structure
            start_flag = bytes([0x68])  # Start flag
            address = bytes.fromhex(message.get('address', '000000000000'))
            control = bytes([message.get('control', 0x01)])
            payload = bytes.fromhex(message.get('payload', ''))
            length = len(payload).to_bytes(2, 'little')
            end_flag = bytes([0x16])  # End flag
            
            return start_flag + address + control + length + payload + end_flag
        except Exception as e:
            logger.error(f"Encode error: {e}")
            return b''
    
    def validate_message(self, data: bytes) -> bool:
        """Validate DL/T message"""
        if len(data) < 10:
            return False
        
        # Check start and end flags
        return data[0] == 0x68 and data[-1] == 0x16
