"""
RS-232 Protocol Adapter

Implements RS-232 serial communication for legacy industrial devices.
Supports various baud rates, data formats, and flow control.
"""

from typing import Dict, Any, Optional, List
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class RS232Config:
    """RS-232 Configuration"""
    
    def __init__(self, port: str = "COM1", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = 8
        self.stopbits = 1
        self.parity = 'N'  # None, Even, Odd
        self.timeout = 1.0
        self.xonxoff = False
        self.rtscts = False


class RS232Adapter(ProtocolAdapter):
    """
    RS-232 Protocol Adapter
    
    Provides RS-232 serial communication for legacy industrial devices.
    Supports various baud rates, data formats, and flow control.
    """
    
    def __init__(self, adapter_id: str = "rs232-adapter"):
        super().__init__(adapter_id, ProtocolType.RS232)
        self.config: Optional[RS232Config] = None
        self.serial_port = None
        self.message_queue: List[bytes] = []
        self.receive_callbacks: List[callable] = []
        
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Connect to RS-232 serial port
        
        Args:
            config: Configuration with 'port', 'baudrate', etc.
            
        Returns:
            True if connection successful
        """
        try:
            self.config = RS232Config(
                port=config.get('port', 'COM1'),
                baudrate=config.get('baudrate', 9600)
            )
            
            self.config.bytesize = config.get('bytesize', 8)
            self.config.stopbits = config.get('stopbits', 1)
            self.config.parity = config.get('parity', 'N')
            self.config.timeout = config.get('timeout', 1.0)
            self.config.xonxoff = config.get('xonxoff', False)
            self.config.rtscts = config.get('rtscts', False)
            
            # Simulate connection
            self.is_connected = True
            self.connection_time = time.time()
            
            logger.info(
                f"Connected to RS-232 port: {self.config.port} "
                f"({self.config.baudrate} baud)"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RS-232 port: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from RS-232 port"""
        try:
            self.is_connected = False
            self.message_queue.clear()
            logger.info("Disconnected from RS-232 port")
            return True
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def send_data(self, data: bytes) -> bool:
        """
        Send data through RS-232
        
        Args:
            data: Data to send
            
        Returns:
            True if send successful
        """
        try:
            if not self.is_connected:
                logger.error("Not connected to RS-232 port")
                return False
            
            # Simulate sending
            logger.debug(f"Sent {len(data)} bytes: {data.hex()}")
            self._record_message()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send data: {e}")
            return False
    
    def receive_data(self, timeout: float = 1.0) -> Optional[bytes]:
        """
        Receive data from RS-232
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Received data or None if timeout
        """
        try:
            if not self.is_connected:
                return None
            
            if not self.message_queue:
                return None
            
            data = self.message_queue.pop(0)
            logger.debug(f"Received {len(data)} bytes: {data.hex()}")
            return data
            
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send RS-232 message
        
        Args:
            message: Protocol message with data
            
        Returns:
            True if send successful
        """
        try:
            if not self.is_connected:
                return False
            
            data = message.data.get('data')
            if isinstance(data, str):
                data = data.encode('utf-8')
            elif not isinstance(data, bytes):
                data = bytes(data)
            
            return self.send_data(data)
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive RS-232 message
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Protocol message or None if timeout
        """
        try:
            data = self.receive_data(timeout)
            if data is None:
                return None
            
            protocol_msg = ProtocolMessage(
                protocol="rs232",
                message_id=f"msg-{int(time.time() * 1000)}",
                source=self.config.port if self.config else "unknown",
                destination="local",
                timestamp=time.time(),
                data={'data': data}
            )
            
            return protocol_msg
            
        except Exception as e:
            logger.error(f"Receive message error: {e}")
            return None
    
    def register_receive_callback(self, callback: callable) -> None:
        """Register callback for received data"""
        self.receive_callbacks.append(callback)
        logger.debug("Registered receive callback")
    
    def get_port_info(self) -> Optional[Dict[str, Any]]:
        """Get port information"""
        try:
            if not self.config:
                return None
            
            return {
                'port': self.config.port,
                'baudrate': self.config.baudrate,
                'bytesize': self.config.bytesize,
                'stopbits': self.config.stopbits,
                'parity': self.config.parity,
                'connected': self.is_connected
            }
            
        except Exception as e:
            logger.error(f"Failed to get port info: {e}")
            return None
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """Parse RS-232 message data"""
        return {
            'length': len(data),
            'data': data.hex(),
            'ascii': data.decode('utf-8', errors='ignore')
        }
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """Encode RS-232 message"""
        try:
            data = message.get('data')
            if isinstance(data, str):
                return data.encode('utf-8')
            elif isinstance(data, bytes):
                return data
            else:
                return bytes(data)
        except Exception as e:
            logger.error(f"Encode error: {e}")
            return b''
    
    def validate_message(self, data: bytes) -> bool:
        """Validate RS-232 message"""
        return len(data) > 0
