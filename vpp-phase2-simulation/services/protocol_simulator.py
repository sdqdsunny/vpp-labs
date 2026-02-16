"""
Communication Protocol Simulator

Implements detailed protocol simulation for IEC 104 and MQTT with message
parsing, encoding, validation, and network condition simulation.
"""

import logging
import struct
import json
import random
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum

from utils.errors import ValidationError, SimulatorError
from utils.logger import get_logger

logger = get_logger(__name__)


class ProtocolType(Enum):
    """Supported protocol types."""
    IEC_104 = "iec104"
    MQTT = "mqtt"


@dataclass
class ProtocolMessage:
    """Generic protocol message."""
    protocol: str
    message_id: str
    source: str
    destination: str
    payload: bytes
    timestamp: datetime
    latency_ms: float = 0.0
    packet_loss: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "protocol": self.protocol,
            "message_id": self.message_id,
            "source": self.source,
            "destination": self.destination,
            "payload_size": len(self.payload),
            "timestamp": self.timestamp.isoformat(),
            "latency_ms": self.latency_ms,
            "packet_loss": self.packet_loss,
        }


@dataclass
class CommunicationEvent:
    """Communication event for logging."""
    event_id: str
    protocol: str
    source: str
    destination: str
    message_type: str
    latency_ms: float
    packet_loss: bool
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "protocol": self.protocol,
            "source": self.source,
            "destination": self.destination,
            "message_type": self.message_type,
            "latency_ms": self.latency_ms,
            "packet_loss": self.packet_loss,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class ProtocolAdapter(ABC):
    """Abstract base class for protocol adapters."""
    
    @abstractmethod
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """Parse protocol message from bytes."""
        pass
    
    @abstractmethod
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """Encode message to protocol format."""
        pass
    
    @abstractmethod
    def validate_message(self, data: bytes) -> bool:
        """Validate protocol message format."""
        pass


class IEC104Adapter(ProtocolAdapter):
    """
    IEC 104 Protocol Adapter
    
    Implements detailed IEC 60870-5-104 protocol simulation with APDU
    (Application Protocol Data Unit) parsing and encoding.
    
    Requirements:
    - 5.1: Follow IEC 60870-5-104 standard
    - 5.3: Add configurable latency (0-1000ms)
    - 5.4: Simulate packet loss (0-10%)
    - 5.5: Log errors with full context
    """
    
    # APDU types
    APDU_TYPE_I = 0x00  # I-format (Information transfer)
    APDU_TYPE_S = 0x01  # S-format (Supervisory)
    APDU_TYPE_U = 0x03  # U-format (Unnumbered)
    
    # APDU lengths
    APDU_MIN_LENGTH = 4
    APDU_MAX_LENGTH = 255
    
    def __init__(self):
        """Initialize IEC 104 adapter."""
        self.send_sequence = 0
        self.receive_sequence = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.errors = []
        logger.info("IEC 104 Adapter initialized")
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """
        Parse IEC 104 APDU message.
        
        Args:
            data: Raw message bytes
            
        Returns:
            Parsed message dictionary
            
        Raises:
            ValidationError: If message format is invalid
        """
        if not data:
            raise ValidationError("Message data cannot be empty")
        
        if len(data) < self.APDU_MIN_LENGTH:
            raise ValidationError(
                f"Message too short: {len(data)} < {self.APDU_MIN_LENGTH}"
            )
        
        # Parse APDU header
        start_byte = data[0]
        if start_byte != 0x68:  # Start byte
            raise ValidationError(f"Invalid start byte: 0x{start_byte:02x}")
        
        apdu_length = data[1]
        if len(data) < apdu_length + 2:
            raise ValidationError(
                f"Incomplete message: expected {apdu_length + 2}, got {len(data)}"
            )
        
        # Extract control bytes
        control_byte1 = data[2]
        control_byte2 = data[3]
        
        # Determine APDU type
        apdu_type = control_byte1 & 0x03
        
        # Parse based on type
        if apdu_type == self.APDU_TYPE_I:
            return self._parse_i_format(data, apdu_length)
        elif apdu_type == self.APDU_TYPE_S:
            return self._parse_s_format(data, apdu_length)
        elif apdu_type == self.APDU_TYPE_U:
            return self._parse_u_format(data, apdu_length)
        else:
            raise ValidationError(f"Unknown APDU type: {apdu_type}")
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """
        Encode message to IEC 104 APDU format.
        
        Args:
            message: Message dictionary
            
        Returns:
            Encoded message bytes
            
        Raises:
            ValidationError: If message is invalid
        """
        if not message:
            raise ValidationError("Message cannot be None")
        
        message_type = message.get("type", "I")
        
        if message_type == "I":
            return self._encode_i_format(message)
        elif message_type == "S":
            return self._encode_s_format(message)
        elif message_type == "U":
            return self._encode_u_format(message)
        else:
            raise ValidationError(f"Unknown message type: {message_type}")
    
    def validate_message(self, data: bytes) -> bool:
        """
        Validate IEC 104 message format.
        
        Args:
            data: Message bytes
            
        Returns:
            True if valid, False otherwise
        """
        if not data or len(data) < self.APDU_MIN_LENGTH:
            return False
        
        # Check start byte
        if data[0] != 0x68:
            return False
        
        # Check length
        apdu_length = data[1]
        if len(data) < apdu_length + 2:
            return False
        
        # Check end bytes (should be 0x16)
        if data[apdu_length + 1] != 0x16:
            return False
        
        return True
    
    def _parse_i_format(self, data: bytes, length: int) -> Dict[str, Any]:
        """Parse I-format (Information transfer) APDU."""
        control_byte1 = data[2]
        control_byte2 = data[3]
        
        # Extract send and receive sequence numbers
        send_seq = ((control_byte2 & 0xFE) >> 1) | ((data[4] & 0x01) << 7)
        receive_seq = ((data[4] & 0xFE) >> 1) | ((data[5] & 0x01) << 7)
        
        # Extract ASDU data
        asdu_data = data[6:-1]  # Exclude start, length, control, and end bytes
        
        self.messages_received += 1
        self.receive_sequence = receive_seq
        
        return {
            "type": "I",
            "send_sequence": send_seq,
            "receive_sequence": receive_seq,
            "asdu_data": asdu_data.hex(),
            "length": length,
        }
    
    def _parse_s_format(self, data: bytes, length: int) -> Dict[str, Any]:
        """Parse S-format (Supervisory) APDU."""
        control_byte1 = data[2]
        control_byte2 = data[3]
        
        # Extract receive sequence number
        receive_seq = ((control_byte2 & 0xFE) >> 1) | ((data[4] & 0x01) << 7)
        
        self.messages_received += 1
        
        return {
            "type": "S",
            "receive_sequence": receive_seq,
            "length": length,
        }
    
    def _parse_u_format(self, data: bytes, length: int) -> Dict[str, Any]:
        """Parse U-format (Unnumbered) APDU."""
        control_byte1 = data[2]
        control_byte2 = data[3]
        
        # Extract function code
        function_code = (control_byte1 >> 2) & 0x3F
        
        self.messages_received += 1
        
        return {
            "type": "U",
            "function_code": function_code,
            "length": length,
        }
    
    def _encode_i_format(self, message: Dict[str, Any]) -> bytes:
        """Encode I-format APDU."""
        asdu_data = bytes.fromhex(message.get("asdu_data", ""))
        # Use adapter's internal sequence number for sending
        send_seq = self.send_sequence
        receive_seq = message.get("receive_sequence", self.receive_sequence)
        
        # Build APDU
        apdu = bytearray()
        apdu.append(0x68)  # Start byte
        
        # Length (will be updated)
        length_pos = len(apdu)
        apdu.append(0x00)
        
        # Control bytes
        control1 = 0x00  # I-format
        control2 = (send_seq << 1) & 0xFE
        apdu.append(control1)
        apdu.append(control2)
        
        # Sequence bytes
        apdu.append((send_seq >> 7) & 0x01 | ((receive_seq << 1) & 0xFE))
        apdu.append((receive_seq >> 7) & 0x01)
        
        # ASDU data
        apdu.extend(asdu_data)
        
        # Update length
        apdu[length_pos] = len(apdu) - 2
        
        # End byte
        apdu.append(0x16)
        
        self.messages_sent += 1
        self.send_sequence = (send_seq + 1) % 128
        
        return bytes(apdu)
    
    def _encode_s_format(self, message: Dict[str, Any]) -> bytes:
        """Encode S-format APDU."""
        receive_seq = message.get("receive_sequence", self.receive_sequence)
        
        # Build APDU
        apdu = bytearray()
        apdu.append(0x68)  # Start byte
        apdu.append(0x04)  # Length
        apdu.append(0x01)  # Control byte 1 (S-format)
        apdu.append(0x00)  # Control byte 2
        apdu.append((receive_seq << 1) & 0xFE)
        apdu.append((receive_seq >> 7) & 0x01)
        apdu.append(0x16)  # End byte
        
        self.messages_sent += 1
        
        return bytes(apdu)
    
    def _encode_u_format(self, message: Dict[str, Any]) -> bytes:
        """Encode U-format APDU."""
        function_code = message.get("function_code", 0)
        
        # Build APDU
        apdu = bytearray()
        apdu.append(0x68)  # Start byte
        apdu.append(0x04)  # Length
        apdu.append(0x03 | ((function_code << 2) & 0xFC))  # Control byte 1 (U-format)
        apdu.append(0x00)  # Control byte 2
        apdu.append(0x00)  # Sequence byte 1
        apdu.append(0x00)  # Sequence byte 2
        apdu.append(0x16)  # End byte
        
        self.messages_sent += 1
        
        return bytes(apdu)


class MQTTAdapter(ProtocolAdapter):
    """
    MQTT Protocol Adapter
    
    Implements detailed MQTT 3.1.1 protocol simulation with message
    parsing, encoding, and validation.
    
    Requirements:
    - 5.2: Follow MQTT 3.1.1 specification
    - 5.3: Add configurable latency (0-1000ms)
    - 5.4: Simulate packet loss (0-10%)
    - 5.5: Log errors with full context
    """
    
    # MQTT Control Packet types
    RESERVED = 0
    CONNECT = 1
    CONNACK = 2
    PUBLISH = 3
    PUBACK = 4
    PUBREC = 5
    PUBREL = 6
    PUBCOMP = 7
    SUBSCRIBE = 8
    SUBACK = 9
    UNSUBSCRIBE = 10
    UNSUBACK = 11
    PINGREQ = 12
    PINGRESP = 13
    DISCONNECT = 14
    
    PACKET_TYPES = {
        1: "CONNECT",
        2: "CONNACK",
        3: "PUBLISH",
        4: "PUBACK",
        5: "PUBREC",
        6: "PUBREL",
        7: "PUBCOMP",
        8: "SUBSCRIBE",
        9: "SUBACK",
        10: "UNSUBSCRIBE",
        11: "UNSUBACK",
        12: "PINGREQ",
        13: "PINGRESP",
        14: "DISCONNECT",
    }
    
    def __init__(self):
        """Initialize MQTT adapter."""
        self.packet_id = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.errors = []
        logger.info("MQTT Adapter initialized")
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """
        Parse MQTT message.
        
        Args:
            data: Raw message bytes
            
        Returns:
            Parsed message dictionary
            
        Raises:
            ValidationError: If message format is invalid
        """
        if not data or len(data) < 2:
            raise ValidationError("Message too short")
        
        # Parse fixed header
        byte1 = data[0]
        packet_type = (byte1 >> 4) & 0x0F
        flags = byte1 & 0x0F
        
        # Parse remaining length
        remaining_length, length_bytes = self._decode_remaining_length(data[1:])
        
        if packet_type not in self.PACKET_TYPES:
            raise ValidationError(f"Unknown packet type: {packet_type}")
        
        # Parse variable header and payload
        header_start = 1 + length_bytes
        payload_start = header_start + 2  # Minimum variable header size
        
        self.messages_received += 1
        
        return {
            "packet_type": packet_type,
            "packet_type_name": self.PACKET_TYPES[packet_type],
            "flags": flags,
            "remaining_length": remaining_length,
            "payload_size": len(data) - payload_start,
        }
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """
        Encode message to MQTT format.
        
        Args:
            message: Message dictionary
            
        Returns:
            Encoded message bytes
            
        Raises:
            ValidationError: If message is invalid
        """
        if not message:
            raise ValidationError("Message cannot be None")
        
        packet_type = message.get("packet_type", self.PUBLISH)
        flags = message.get("flags", 0)
        payload = message.get("payload", b"")
        
        # Build fixed header
        byte1 = (packet_type << 4) | flags
        
        # Encode remaining length
        remaining_length = len(payload) + 2  # Minimum variable header
        length_bytes = self._encode_remaining_length(remaining_length)
        
        # Build message
        mqtt_msg = bytearray()
        mqtt_msg.append(byte1)
        mqtt_msg.extend(length_bytes)
        mqtt_msg.extend(payload)
        
        self.messages_sent += 1
        self.packet_id = (self.packet_id + 1) % 65536
        
        return bytes(mqtt_msg)
    
    def validate_message(self, data: bytes) -> bool:
        """
        Validate MQTT message format.
        
        Args:
            data: Message bytes
            
        Returns:
            True if valid, False otherwise
        """
        if not data or len(data) < 2:
            return False
        
        # Check packet type
        packet_type = (data[0] >> 4) & 0x0F
        if packet_type not in self.PACKET_TYPES:
            return False
        
        # Check remaining length encoding
        try:
            remaining_length, length_bytes = self._decode_remaining_length(data[1:])
            if len(data) < 1 + length_bytes + remaining_length:
                return False
        except (ValidationError, IndexError):
            return False
        
        return True
    
    def _decode_remaining_length(self, data: bytes) -> Tuple[int, int]:
        """Decode MQTT remaining length."""
        multiplier = 1
        value = 0
        index = 0
        
        while index < len(data) and index < 4:
            encoded_byte = data[index]
            value += (encoded_byte & 0x7F) * multiplier
            
            if (encoded_byte & 0x80) == 0:
                return value, index + 1
            
            multiplier *= 128
            index += 1
        
        raise ValidationError("Invalid remaining length encoding")
    
    def _encode_remaining_length(self, length: int) -> bytes:
        """Encode MQTT remaining length."""
        encoded = bytearray()
        
        while length > 0:
            encoded_byte = length % 128
            length //= 128
            
            if length > 0:
                encoded_byte |= 0x80
            
            encoded.append(encoded_byte)
        
        return bytes(encoded)


class ProtocolSimulator:
    """
    Communication Protocol Simulator
    
    Simulates IEC 104 and MQTT protocols with message parsing, encoding,
    validation, and network condition simulation.
    
    Requirements:
    - 5.1: Follow IEC 60870-5-104 standard
    - 5.2: Follow MQTT 3.1.1 specification
    - 5.3: Add configurable latency (0-1000ms)
    - 5.4: Simulate packet loss (0-10%)
    - 5.5: Log errors with full context
    """
    
    def __init__(self, simulator_id: Optional[str] = None):
        """
        Initialize Protocol Simulator.
        
        Args:
            simulator_id: Unique simulator identifier
        """
        self.simulator_id = simulator_id or f"proto-sim-{random.randint(1000, 9999)}"
        self.iec104_adapter = IEC104Adapter()
        self.mqtt_adapter = MQTTAdapter()
        self.communication_events: List[CommunicationEvent] = []
        self.messages_processed = 0
        self.messages_dropped = 0
        self.errors_logged = 0
        
        logger.info(f"Protocol Simulator initialized: {self.simulator_id}")
    
    def process_message(
        self,
        protocol: str,
        data: bytes,
        source: str,
        destination: str,
        latency_ms: float = 0.0,
        packet_loss_probability: float = 0.0
    ) -> Tuple[Optional[Dict[str, Any]], CommunicationEvent]:
        """
        Process protocol message with network conditions.
        
        Args:
            protocol: Protocol type (iec104, mqtt)
            data: Message bytes
            source: Source identifier
            destination: Destination identifier
            latency_ms: Network latency in milliseconds
            packet_loss_probability: Packet loss probability (0.0-1.0)
            
        Returns:
            Tuple of (parsed_message or None, communication_event)
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if not protocol:
            raise ValidationError("Protocol cannot be empty")
        
        if not data:
            raise ValidationError("Data cannot be empty")
        
        if not 0.0 <= packet_loss_probability <= 1.0:
            raise ValidationError("Packet loss probability must be 0.0-1.0")
        
        message_id = f"msg-{self.messages_processed:06d}"
        self.messages_processed += 1
        
        # Simulate packet loss
        packet_loss = random.random() < packet_loss_probability
        if packet_loss:
            self.messages_dropped += 1
            event = CommunicationEvent(
                event_id=message_id,
                protocol=protocol,
                source=source,
                destination=destination,
                message_type="unknown",
                latency_ms=latency_ms,
                packet_loss=True,
                error="Packet loss simulated",
            )
            self.communication_events.append(event)
            logger.warning(f"Packet loss: {message_id}")
            return None, event
        
        # Parse message
        try:
            if protocol.lower() == "iec104":
                adapter = self.iec104_adapter
            elif protocol.lower() == "mqtt":
                adapter = self.mqtt_adapter
            else:
                raise ValidationError(f"Unsupported protocol: {protocol}")
            
            # Validate message
            if not adapter.validate_message(data):
                raise ValidationError("Invalid message format")
            
            # Parse message
            parsed = adapter.parse_message(data)
            message_type = parsed.get("packet_type_name", parsed.get("type", "unknown"))
            
            event = CommunicationEvent(
                event_id=message_id,
                protocol=protocol,
                source=source,
                destination=destination,
                message_type=message_type,
                latency_ms=latency_ms,
                packet_loss=False,
            )
            
            self.communication_events.append(event)
            logger.info(f"Message processed: {message_id}, type={message_type}")
            
            return parsed, event
            
        except (ValidationError, Exception) as e:
            self.errors_logged += 1
            error_msg = str(e)
            
            event = CommunicationEvent(
                event_id=message_id,
                protocol=protocol,
                source=source,
                destination=destination,
                message_type="error",
                latency_ms=latency_ms,
                packet_loss=False,
                error=error_msg,
            )
            
            self.communication_events.append(event)
            logger.error(f"Message processing error: {message_id}, error={error_msg}")
            
            return None, event
    
    def get_simulator_status(self) -> Dict[str, Any]:
        """Get simulator status."""
        return {
            "simulator_id": self.simulator_id,
            "messages_processed": self.messages_processed,
            "messages_dropped": self.messages_dropped,
            "errors_logged": self.errors_logged,
            "iec104_messages_sent": self.iec104_adapter.messages_sent,
            "iec104_messages_received": self.iec104_adapter.messages_received,
            "mqtt_messages_sent": self.mqtt_adapter.messages_sent,
            "mqtt_messages_received": self.mqtt_adapter.messages_received,
            "total_events": len(self.communication_events),
        }
    
    def reset(self) -> None:
        """Reset simulator state."""
        self.communication_events.clear()
        self.messages_processed = 0
        self.messages_dropped = 0
        self.errors_logged = 0
        self.iec104_adapter = IEC104Adapter()
        self.mqtt_adapter = MQTTAdapter()
        logger.info(f"Protocol Simulator reset: {self.simulator_id}")
