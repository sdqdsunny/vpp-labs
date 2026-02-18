"""
RS-485 Protocol Adapter

Implements RS-485 multi-drop serial communication for industrial networks.
Supports multiple devices on single bus with address-based communication.
"""

from typing import Dict, Any, Optional, List
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class RS485Config:
    """RS-485 Configuration"""
    
    def __init__(self, port: str = "COM1", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = 8
        self.stopbits = 1
        self.parity = 'E'  # Even parity common in RS-485
        self.timeout = 1.0
        self.rts_level = True  # RTS control


class RS485Device:
    """RS-485 Device on Bus"""
    
    def __init__(self, address: int):
        self.address = address
        self.last_seen = None
        self.messages: List[bytes] = []


class RS485Adapter(ProtocolAdapter):
    """
    RS-485 Protocol Adapter
    
    Provides RS-485 multi-drop serial communication for industrial networks.
    Supports multiple devices on single bus with address-based communication.
    """
    
    def __init__(self, adapter_id: str = "rs485-adapter"):
        super().__init__(adapter_id, ProtocolType.RS485)
        self.config: Optional[RS485Config] = None
        self.devices: Dict[int, RS485Device] = {}
        self.message_queue: List[Dict[str, Any]] = []
        self.receive_callbacks: List[callable] = []
        
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Connect to RS-485 bus
        
        Args:
            config: Configuration with 'port', 'baudrate', etc.
            
        Returns:
            True if connection successful
        """
        try:
            self.config = RS485Config(
                port=config.get('port', 'COM1'),
                baudrate=config.get('baudrate', 9600)
            )
            
            self.config.bytesize = config.get('bytesize', 8)
            self.config.stopbits = config.get('stopbits', 1)
            self.config.parity = config.get('parity', 'E')
            self.config.timeout = config.get('timeout', 1.0)
            self.config.rts_level = config.get('rts_level', True)
            
            self.is_connected = True
            self.connection_time = time.time()
            
            logger.info(
                f"Connected to RS-485 bus: {self.config.port} "
                f"({self.config.baudrate} baud)"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RS-485 bus: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from RS-485 bus"""
        try:
            self.is_connected = False
            self.devices.clear()
            self.message_queue.clear()
            logger.info("Disconnected from RS-485 bus")
            return True
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def add_device(self, address: int) -> bool:
        """
        Add device to RS-485 bus
        
        Args:
            address: Device address (0-247)
            
        Returns:
            True if device added
        """
        try:
            if not self.is_connected:
                return False
            
            if address not in self.devices:
                self.devices[address] = RS485Device(address)
                logger.info(f"Added RS-485 device at address: {address}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to add device: {e}")
            return False
    
    def remove_device(self, address: int) -> bool:
        """Remove device from RS-485 bus"""
        try:
            if address in self.devices:
                del self.devices[address]
                logger.info(f"Removed RS-485 device at address: {address}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove device: {e}")
            return False
    
    def send_data(self, address: int, data: bytes) -> bool:
        """
        Send data to RS-485 device
        
        Args:
            address: Target device address
            data: Data to send
            
        Returns:
            True if send successful
        """
        try:
            if not self.is_connected:
                logger.error("Not connected to RS-485 bus")
                return False
            
            if address not in self.devices:
                logger.error(f"Device not found at address: {address}")
                return False
            
            # Add address byte to frame
            frame = bytes([address]) + data
            
            msg_data = {
                'address': address,
                'data': data.hex(),
                'frame': frame.hex(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.message_queue.append(msg_data)
            self._record_message()
            
            logger.debug(f"Sent {len(data)} bytes to address {address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send data: {e}")
            return False
    
    def receive_data(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Receive data from RS-485 bus
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Received message or None if timeout
        """
        try:
            if not self.is_connected:
                return None
            
            if not self.message_queue:
                return None
            
            msg = self.message_queue.pop(0)
            logger.debug(f"Received from address {msg['address']}")
            return msg
            
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send RS-485 message
        
        Args:
            message: Protocol message with address and data
            
        Returns:
            True if send successful
        """
        try:
            if not self.is_connected:
                return False
            
            address = message.data.get('address')
            data = message.data.get('data')
            
            if address is None or data is None:
                logger.error("Invalid message: missing address or data")
                return False
            
            if isinstance(data, str):
                data = bytes.fromhex(data)
            elif not isinstance(data, bytes):
                data = bytes(data)
            
            return self.send_data(address, data)
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive RS-485 message
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Protocol message or None if timeout
        """
        try:
            msg_data = self.receive_data(timeout)
            if msg_data is None:
                return None
            
            protocol_msg = ProtocolMessage(
                protocol="rs485",
                message_id=f"msg-{int(time.time() * 1000)}",
                source=f"rs485-{msg_data['address']}",
                destination="bus",
                timestamp=time.time(),
                data=msg_data
            )
            
            return protocol_msg
            
        except Exception as e:
            logger.error(f"Receive message error: {e}")
            return None
    
    def get_device_info(self, address: int) -> Optional[Dict[str, Any]]:
        """Get device information"""
        try:
            if address not in self.devices:
                return None
            
            device = self.devices[address]
            return {
                'address': device.address,
                'last_seen': device.last_seen,
                'message_count': len(device.messages)
            }
            
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return None
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """List all devices on bus"""
        try:
            devices = []
            for address, device in self.devices.items():
                devices.append({
                    'address': device.address,
                    'last_seen': device.last_seen,
                    'message_count': len(device.messages)
                })
            return devices
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
            return []
    
    def register_receive_callback(self, callback: callable) -> None:
        """Register callback for received data"""
        self.receive_callbacks.append(callback)
        logger.debug("Registered receive callback")
    
    def get_bus_info(self) -> Optional[Dict[str, Any]]:
        """Get bus information"""
        try:
            if not self.config:
                return None
            
            return {
                'port': self.config.port,
                'baudrate': self.config.baudrate,
                'parity': self.config.parity,
                'connected': self.is_connected,
                'device_count': len(self.devices),
                'messages_queued': len(self.message_queue)
            }
            
        except Exception as e:
            logger.error(f"Failed to get bus info: {e}")
            return None
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """Parse RS-485 message data"""
        if len(data) < 1:
            return {}
        
        return {
            'address': data[0],
            'payload': data[1:].hex() if len(data) > 1 else '',
            'length': len(data)
        }
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """Encode RS-485 message"""
        try:
            address = bytes([message.get('address', 0)])
            payload = message.get('payload', b'')
            if isinstance(payload, str):
                payload = bytes.fromhex(payload)
            return address + payload
        except Exception as e:
            logger.error(f"Encode error: {e}")
            return b''
    
    def validate_message(self, data: bytes) -> bool:
        """Validate RS-485 message"""
        return len(data) >= 1
