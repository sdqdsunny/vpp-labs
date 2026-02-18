"""
CAN Protocol Adapter

Implements CAN (Controller Area Network) communication for automotive and industrial applications.
Supports multiple CAN interfaces and message filtering.
"""

from typing import Dict, Any, Optional, List
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
import logging
import can
from can import Message, Bus, BusState

logger = logging.getLogger(__name__)


class CANConfig:
    """CAN Configuration"""
    
    def __init__(self, interface: str = 'socketcan', channel: str = 'vcan0', bitrate: int = 500000):
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.is_fd = False  # CAN FD support


class CANAdapter(ProtocolAdapter):
    """
    CAN Protocol Adapter
    
    Provides CAN communication for automotive and industrial control systems.
    Supports standard CAN, CAN FD, and multiple interface types.
    """
    
    def __init__(self, adapter_id: str = "can-adapter"):
        super().__init__(adapter_id, ProtocolType.CAN)
        self.bus: Optional[Bus] = None
        self.config: Optional[CANConfig] = None
        self.message_queue: List[Message] = []
        self.filters: List[Dict[str, Any]] = []
        
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Connect to CAN bus
        
        Args:
            config: Configuration with 'interface', 'channel', 'bitrate'
            
        Returns:
            True if connection successful
        """
        try:
            self.config = CANConfig(
                interface=config.get('interface', 'socketcan'),
                channel=config.get('channel', 'vcan0'),
                bitrate=config.get('bitrate', 500000)
            )
            
            self.bus = can.Bus(
                interface=self.config.interface,
                channel=self.config.channel,
                bitrate=self.config.bitrate,
                is_fd=self.config.is_fd
            )
            
            self.is_connected = True
            logger.info(f"Connected to CAN bus: {self.config.interface} on {self.config.channel}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to CAN bus: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from CAN bus"""
        try:
            if self.bus:
                self.bus.shutdown()
            self.is_connected = False
            logger.info("Disconnected from CAN bus")
            return True
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send CAN message
        
        Args:
            message: Protocol message with CAN ID and data
            
        Returns:
            True if send successful
        """
        try:
            if not self.is_connected or not self.bus:
                return False
            
            can_id = message.data.get('can_id', 0x123)
            data = message.data.get('data', b'')
            is_extended = message.data.get('is_extended', False)
            is_remote = message.data.get('is_remote', False)
            
            can_msg = Message(
                arbitration_id=can_id,
                data=data,
                is_extended_id=is_extended,
                is_remote_frame=is_remote
            )
            
            self.bus.send(can_msg)
            logger.debug(f"Sent CAN message: ID=0x{can_id:X}, Data={data.hex()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send CAN message: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive CAN message
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Protocol message or None if no message received
        """
        try:
            if not self.is_connected or not self.bus:
                return None
            
            msg = self.bus.recv(timeout=timeout)
            
            if msg is None:
                return None
            
            protocol_msg = ProtocolMessage(
                protocol_type=ProtocolType.CAN,
                data={
                    'can_id': msg.arbitration_id,
                    'data': msg.data,
                    'timestamp': msg.timestamp,
                    'is_extended': msg.is_extended_id,
                    'is_remote': msg.is_remote_frame,
                    'dlc': msg.dlc
                }
            )
            
            logger.debug(f"Received CAN message: ID=0x{msg.arbitration_id:X}")
            return protocol_msg
            
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None
    
    def add_filter(self, can_id: int, mask: int = 0x7FF) -> bool:
        """
        Add CAN message filter
        
        Args:
            can_id: CAN ID to filter
            mask: Filter mask
            
        Returns:
            True if filter added successfully
        """
        try:
            if not self.bus:
                return False
            
            filter_dict = {
                'can_id': can_id,
                'can_mask': mask,
                'extended': False
            }
            
            self.bus.set_filters([filter_dict])
            self.filters.append(filter_dict)
            logger.info(f"Added CAN filter: ID=0x{can_id:X}, Mask=0x{mask:X}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add filter: {e}")
            return False
    
    def clear_filters(self) -> bool:
        """Clear all CAN filters"""
        try:
            if self.bus:
                self.bus.set_filters(None)
            self.filters.clear()
            logger.info("Cleared all CAN filters")
            return True
        except Exception as e:
            logger.error(f"Failed to clear filters: {e}")
            return False
    
    def get_bus_state(self) -> Optional[str]:
        """Get current CAN bus state"""
        try:
            if not self.bus:
                return None
            
            state = self.bus.state
            return str(state)
        except Exception as e:
            logger.error(f"Failed to get bus state: {e}")
            return None
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """Parse CAN message data"""
        if len(data) < 2:
            return {}
        
        return {
            'can_id': int.from_bytes(data[0:2], 'big'),
            'dlc': data[2] if len(data) > 2 else 0,
            'payload': data[3:] if len(data) > 3 else b''
        }
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """Encode CAN message"""
        can_id = message.get('can_id', 0).to_bytes(2, 'big')
        dlc = bytes([message.get('dlc', 0)])
        payload = message.get('payload', b'')
        return can_id + dlc + payload
    
    def validate_message(self, data: bytes) -> bool:
        """Validate CAN message"""
        return len(data) >= 2
