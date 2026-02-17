"""
Base Protocol Adapter Framework

Provides unified interface for all protocol adapters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    """Supported protocol types"""
    IEC61850 = "iec61850"
    MODBUS = "modbus"
    DNP3 = "dnp3"
    MQTT = "mqtt"


class ProtocolException(Exception):
    """Base exception for protocol adapter errors"""
    pass


class ConnectionException(ProtocolException):
    """Raised when connection fails"""
    pass


class MessageException(ProtocolException):
    """Raised when message processing fails"""
    pass


@dataclass
class ProtocolMessage:
    """Unified protocol message format"""
    protocol: str
    message_id: str
    source: str
    destination: str
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "protocol": self.protocol,
            "message_id": self.message_id,
            "source": self.source,
            "destination": self.destination,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProtocolMessage":
        """Create message from dictionary"""
        return cls(
            protocol=data["protocol"],
            message_id=data["message_id"],
            source=data["source"],
            destination=data["destination"],
            timestamp=data["timestamp"],
            data=data["data"],
            metadata=data.get("metadata", {}),
        )


class ProtocolAdapter(ABC):
    """
    Base class for all protocol adapters.
    
    Provides unified interface for protocol-specific implementations.
    """

    def __init__(self, adapter_id: str, protocol_type: ProtocolType):
        """
        Initialize adapter.
        
        Args:
            adapter_id: Unique identifier for this adapter instance
            protocol_type: Type of protocol this adapter handles
        """
        self.adapter_id = adapter_id
        self.protocol_type = protocol_type
        self.is_connected = False
        self.message_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.connection_time: Optional[float] = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Establish connection to protocol endpoint.
        
        Args:
            config: Connection configuration (host, port, credentials, etc.)
            
        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to protocol endpoint.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send message through protocol.
        
        Args:
            message: Message to send
            
        Returns:
            True if send successful, False otherwise
        """
        pass

    @abstractmethod
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive message from protocol.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Received message or None if timeout
        """
        pass

    @abstractmethod
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """
        Parse raw protocol data into dictionary.
        
        Args:
            data: Raw protocol data
            
        Returns:
            Parsed message dictionary
        """
        pass

    @abstractmethod
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """
        Encode message dictionary into raw protocol data.
        
        Args:
            message: Message dictionary
            
        Returns:
            Encoded protocol data
        """
        pass

    @abstractmethod
    def validate_message(self, data: bytes) -> bool:
        """
        Validate raw protocol data.
        
        Args:
            data: Raw protocol data
            
        Returns:
            True if data is valid, False otherwise
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """
        Get adapter status.
        
        Returns:
            Status dictionary
        """
        uptime = None
        if self.connection_time:
            uptime = time.time() - self.connection_time

        return {
            "adapter_id": self.adapter_id,
            "protocol_type": self.protocol_type.value,
            "is_connected": self.is_connected,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "uptime_seconds": uptime,
        }

    def _record_error(self, error: str) -> None:
        """Record error for debugging"""
        self.error_count += 1
        self.last_error = error
        self.logger.error(f"Adapter error: {error}")

    def _record_message(self) -> None:
        """Record successful message"""
        self.message_count += 1
