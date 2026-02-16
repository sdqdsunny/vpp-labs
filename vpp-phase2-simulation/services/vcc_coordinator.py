"""
Virtual Control Center (VCC) Coordinator

Coordinates protocol mapping and 5G network simulation for VPP operations.
Maps VPP Master commands to device protocols and converts responses back.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from utils.errors import SimulatorError, ValidationError
from utils.logger import get_logger

logger = get_logger(__name__)


class ProtocolType(Enum):
    """Supported communication protocols."""
    IEC_104 = "iec104"
    MQTT = "mqtt"
    UNKNOWN = "unknown"


class CommandType(Enum):
    """VPP Master command types."""
    SET_POWER = "set_power"
    GET_STATE = "get_state"
    SET_DEMAND_RESPONSE = "set_demand_response"
    GET_AVAILABLE_POWER = "get_available_power"
    RESET = "reset"
    UNKNOWN = "unknown"


@dataclass
class VPPCommand:
    """VPP Master command format."""
    command_id: str
    device_id: str
    command_type: str
    parameters: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "command_id": self.command_id,
            "device_id": self.device_id,
            "command_type": self.command_type,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ProtocolMessage:
    """Protocol-specific message format."""
    message_id: str
    protocol: str
    source: str
    destination: str
    payload: Dict[str, Any]
    timestamp: datetime
    latency_ms: float = 0.0
    packet_loss: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "protocol": self.protocol,
            "source": self.source,
            "destination": self.destination,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "latency_ms": self.latency_ms,
            "packet_loss": self.packet_loss,
        }


@dataclass
class VPPResponse:
    """VPP Master response format."""
    response_id: str
    command_id: str
    device_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response_id": self.response_id,
            "command_id": self.command_id,
            "device_id": self.device_id,
            "status": self.status,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class VCCStatus:
    """VCC operational status."""
    vcc_id: str
    status: str
    active_messages: int
    total_messages_processed: int
    total_latency_ms: float
    packet_loss_count: int
    message_ordering_violations: int
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "vcc_id": self.vcc_id,
            "status": self.status,
            "active_messages": self.active_messages,
            "total_messages_processed": self.total_messages_processed,
            "total_latency_ms": self.total_latency_ms,
            "packet_loss_count": self.packet_loss_count,
            "message_ordering_violations": self.message_ordering_violations,
            "timestamp": self.timestamp.isoformat(),
        }


class VCCCoordinator:
    """
    Virtual Control Center Coordinator
    
    Coordinates protocol mapping and 5G network simulation for VPP operations.
    Maps VPP Master commands to device protocols and converts responses back.
    
    Requirements:
    - 4.1: Map commands to appropriate device protocols (IEC 104, MQTT)
    - 4.2: Convert responses back to VPP Master format
    - 4.3: Introduce realistic network delays (10-50ms)
    - 4.4: Introduce packet loss (0-5%)
    - 4.5: Maintain message ordering and integrity
    """
    
    def __init__(self, vcc_id: Optional[str] = None):
        """
        Initialize VCC Coordinator.
        
        Args:
            vcc_id: Unique VCC identifier (auto-generated if not provided)
        """
        self.vcc_id = vcc_id or f"vcc-{uuid.uuid4().hex[:8]}"
        self.status = "initialized"
        self.active_messages: Dict[str, ProtocolMessage] = {}
        self.message_queue: List[ProtocolMessage] = []
        self.total_messages_processed = 0
        self.total_latency_ms = 0.0
        self.packet_loss_count = 0
        self.message_ordering_violations = 0
        self.last_message_sequence: Dict[str, int] = {}
        
        logger.info(f"VCC Coordinator initialized: {self.vcc_id}")
    
    def map_command(
        self,
        vpp_command: VPPCommand,
        target_protocol: str
    ) -> ProtocolMessage:
        """
        Map VPP Master command to protocol-specific message.
        
        Args:
            vpp_command: VPP Master command
            target_protocol: Target protocol (iec104, mqtt)
            
        Returns:
            Protocol-specific message
            
        Raises:
            ValidationError: If command or protocol is invalid
        """
        if not vpp_command:
            raise ValidationError("VPP command cannot be None")
        
        if not target_protocol:
            raise ValidationError("Target protocol cannot be empty")
        
        # Validate protocol
        protocol_normalized = target_protocol.lower().replace("-", "_")
        try:
            if protocol_normalized == "iec104":
                protocol_type = ProtocolType.IEC_104
            elif protocol_normalized == "mqtt":
                protocol_type = ProtocolType.MQTT
            else:
                raise ValidationError(f"Unsupported protocol: {target_protocol}")
        except (KeyError, AttributeError):
            raise ValidationError(f"Unsupported protocol: {target_protocol}")
        
        # Map command to protocol-specific payload
        protocol_payload = self._map_command_to_protocol(
            vpp_command,
            protocol_type
        )
        
        # Create protocol message
        message = ProtocolMessage(
            message_id=f"msg-{uuid.uuid4().hex[:8]}",
            protocol=target_protocol,
            source="vcc",
            destination=vpp_command.device_id,
            payload=protocol_payload,
            timestamp=datetime.utcnow(),
        )
        
        # Track message
        self.active_messages[message.message_id] = message
        self.message_queue.append(message)
        
        logger.info(
            f"Command mapped to {target_protocol}: "
            f"cmd_id={vpp_command.command_id}, msg_id={message.message_id}"
        )
        
        return message
    
    def convert_response(
        self,
        protocol_message: ProtocolMessage
    ) -> VPPResponse:
        """
        Convert protocol-specific response back to VPP Master format.
        
        Args:
            protocol_message: Protocol-specific message
            
        Returns:
            VPP Master response
            
        Raises:
            ValidationError: If message is invalid
        """
        if not protocol_message:
            raise ValidationError("Protocol message cannot be None")
        
        # Extract VPP response from protocol payload
        vpp_data = self._convert_protocol_to_response(protocol_message)
        
        # Create VPP response
        response = VPPResponse(
            response_id=f"resp-{uuid.uuid4().hex[:8]}",
            command_id=protocol_message.payload.get("command_id", "unknown"),
            device_id=protocol_message.source,
            status="success" if not protocol_message.packet_loss else "degraded",
            data=vpp_data,
            timestamp=datetime.utcnow(),
        )
        
        # Remove from active messages
        if protocol_message.message_id in self.active_messages:
            del self.active_messages[protocol_message.message_id]
        
        logger.info(
            f"Response converted from {protocol_message.protocol}: "
            f"msg_id={protocol_message.message_id}, resp_id={response.response_id}"
        )
        
        return response
    
    def apply_network_conditions(
        self,
        message: ProtocolMessage,
        latency_ms: float = 0.0,
        packet_loss_probability: float = 0.0
    ) -> ProtocolMessage:
        """
        Apply network conditions to message.
        
        Args:
            message: Protocol message
            latency_ms: Network latency in milliseconds
            packet_loss_probability: Packet loss probability (0.0-1.0)
            
        Returns:
            Message with network conditions applied
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if not message:
            raise ValidationError("Message cannot be None")
        
        if latency_ms < 0:
            raise ValidationError("Latency cannot be negative")
        
        if not 0.0 <= packet_loss_probability <= 1.0:
            raise ValidationError("Packet loss probability must be 0.0-1.0")
        
        # Apply latency
        message.latency_ms = latency_ms
        self.total_latency_ms += latency_ms
        
        # Simulate packet loss
        import random
        if random.random() < packet_loss_probability:
            message.packet_loss = True
            self.packet_loss_count += 1
            logger.warning(
                f"Packet loss simulated for message: {message.message_id}"
            )
        
        return message
    
    def get_vcc_status(self) -> VCCStatus:
        """
        Get VCC operational status.
        
        Returns:
            VCC status information
        """
        return VCCStatus(
            vcc_id=self.vcc_id,
            status=self.status,
            active_messages=len(self.active_messages),
            total_messages_processed=self.total_messages_processed,
            total_latency_ms=self.total_latency_ms,
            packet_loss_count=self.packet_loss_count,
            message_ordering_violations=self.message_ordering_violations,
            timestamp=datetime.utcnow(),
        )
    
    def check_message_ordering(
        self,
        device_id: str,
        sequence_number: int
    ) -> bool:
        """
        Check if message ordering is maintained.
        
        Args:
            device_id: Device identifier
            sequence_number: Message sequence number
            
        Returns:
            True if ordering is correct, False otherwise
        """
        last_seq = self.last_message_sequence.get(device_id, -1)
        
        if sequence_number <= last_seq:
            self.message_ordering_violations += 1
            logger.warning(
                f"Message ordering violation for device {device_id}: "
                f"expected > {last_seq}, got {sequence_number}"
            )
            return False
        
        self.last_message_sequence[device_id] = sequence_number
        return True
    
    def reset(self) -> None:
        """Reset VCC state."""
        self.active_messages.clear()
        self.message_queue.clear()
        self.total_messages_processed = 0
        self.total_latency_ms = 0.0
        self.packet_loss_count = 0
        self.message_ordering_violations = 0
        self.last_message_sequence.clear()
        logger.info(f"VCC Coordinator reset: {self.vcc_id}")
    
    def _map_command_to_protocol(
        self,
        vpp_command: VPPCommand,
        protocol_type: ProtocolType
    ) -> Dict[str, Any]:
        """
        Map VPP command to protocol-specific payload.
        
        Args:
            vpp_command: VPP Master command
            protocol_type: Target protocol type
            
        Returns:
            Protocol-specific payload
        """
        base_payload = {
            "command_id": vpp_command.command_id,
            "device_id": vpp_command.device_id,
            "command_type": vpp_command.command_type,
            "parameters": vpp_command.parameters,
            "timestamp": vpp_command.timestamp.isoformat(),
        }
        
        if protocol_type == ProtocolType.IEC_104:
            return self._map_to_iec104(base_payload)
        elif protocol_type == ProtocolType.MQTT:
            return self._map_to_mqtt(base_payload)
        else:
            return base_payload
    
    def _convert_protocol_to_response(
        self,
        protocol_message: ProtocolMessage
    ) -> Dict[str, Any]:
        """
        Convert protocol-specific payload to VPP response data.
        
        Args:
            protocol_message: Protocol message
            
        Returns:
            VPP response data
        """
        protocol_type = protocol_message.protocol.lower()
        
        if protocol_type == "iec104":
            return self._convert_from_iec104(protocol_message.payload)
        elif protocol_type == "mqtt":
            return self._convert_from_mqtt(protocol_message.payload)
        else:
            return protocol_message.payload
    
    def _map_to_iec104(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Map VPP command to IEC 104 format."""
        return {
            "asdu_type": "C_SC_NA_1",  # Single command
            "information_object_address": payload.get("device_id", ""),
            "command_value": payload.get("parameters", {}).get("value", 0),
            "qualifier": 0,
            "cause_of_transmission": 6,  # Activation
            "originator_address": 0,
            "common_address": 1,
        }
    
    def _map_to_mqtt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Map VPP command to MQTT format."""
        return {
            "topic": f"vpp/device/{payload.get('device_id', '')}/command",
            "qos": 1,
            "retain": False,
            "payload": {
                "command_id": payload.get("command_id", ""),
                "command_type": payload.get("command_type", ""),
                "parameters": payload.get("parameters", {}),
            },
        }
    
    def _convert_from_iec104(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Convert IEC 104 response to VPP format."""
        return {
            "device_id": payload.get("information_object_address", ""),
            "status": "success",
            "value": payload.get("measured_value", 0),
            "timestamp": payload.get("timestamp", ""),
        }
    
    def _convert_from_mqtt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MQTT response to VPP format."""
        mqtt_payload = payload.get("payload", {})
        return {
            "device_id": payload.get("topic", "").split("/")[2],
            "status": mqtt_payload.get("status", "success"),
            "value": mqtt_payload.get("value", 0),
            "timestamp": mqtt_payload.get("timestamp", ""),
        }
