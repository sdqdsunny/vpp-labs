"""
Protocol-Specific Command Mappers

Implements IEC 104 and MQTT command mapping for VPP operations.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from utils.errors import ValidationError
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class IEC104ASDU:
    """IEC 104 ASDU (Application Service Data Unit) structure."""
    asdu_type: int
    sequence_number: int
    cause_of_transmission: int
    originator_address: int
    common_address: int
    information_objects: list


class ProtocolMapper(ABC):
    """Abstract base class for protocol mappers."""
    
    @abstractmethod
    def map_command(self, vpp_command: Dict[str, Any]) -> Dict[str, Any]:
        """Map VPP command to protocol format."""
        pass
    
    @abstractmethod
    def convert_response(self, protocol_response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert protocol response to VPP format."""
        pass
    
    @abstractmethod
    def validate_message(self, message: Dict[str, Any]) -> bool:
        """Validate protocol message."""
        pass


class IEC104Mapper(ProtocolMapper):
    """
    IEC 104 Protocol Mapper
    
    Maps VPP commands to IEC 60870-5-104 standard format.
    Implements ASDU parsing and encoding.
    
    Requirements:
    - 4.1: Map commands to IEC 104 protocol
    - 5.1: Follow IEC 60870-5-104 standard
    """
    
    # IEC 104 ASDU Type Codes
    ASDU_TYPES = {
        "M_SP_NA_1": 1,    # Single-point information
        "M_DP_NA_1": 3,    # Double-point information
        "M_ST_NA_1": 5,    # Step position information
        "M_BO_NA_1": 7,    # Bitstring of 32 bits
        "M_ME_NA_1": 9,    # Measured value, normalized value
        "M_ME_TA_1": 10,   # Measured value, normalized value with time tag
        "M_ME_NB_1": 11,   # Measured value, scaled value
        "M_ME_TB_1": 12,   # Measured value, scaled value with time tag
        "M_ME_NC_1": 13,   # Measured value, short floating point number
        "M_ME_TC_1": 14,   # Measured value, short floating point number with time tag
        "M_IT_NA_1": 15,   # Integrated totals
        "M_PS_NA_1": 20,   # Packed single-point information with status change detection
        "M_ME_ND_1": 21,   # Measured value, normalized value without quality descriptor
        "M_SQ_NA_1": 30,   # Single command
        "M_DC_NA_1": 31,   # Double command
        "M_RC_NA_1": 32,   # Regulating step command
        "M_SE_NA_1": 34,   # Set-point command, normalized value
        "M_SE_NB_1": 35,   # Set-point command, scaled value
        "M_SE_NC_1": 36,   # Set-point command, short floating point number
        "M_BO_NA_1": 38,   # Bitstring command
        "C_SC_NA_1": 45,   # Single command
        "C_DC_NA_1": 46,   # Double command
        "C_RC_NA_1": 47,   # Regulating step command
        "C_SE_NA_1": 48,   # Set-point command, normalized value
        "C_SE_NB_1": 49,   # Set-point command, scaled value
        "C_SE_NC_1": 50,   # Set-point command, short floating point number
        "C_BO_NA_1": 51,   # Bitstring command
    }
    
    # Cause of Transmission codes
    COT_CODES = {
        "periodic": 1,
        "background": 2,
        "spontaneous": 3,
        "initialized": 4,
        "request": 5,
        "activation": 6,
        "activation_confirmation": 7,
        "deactivation": 8,
        "deactivation_confirmation": 9,
        "activation_termination": 10,
        "return_information_local": 20,
        "return_information_remote": 21,
        "file_transfer": 30,
    }
    
    def __init__(self):
        """Initialize IEC 104 mapper."""
        self.sequence_number = 0
        logger.info("IEC 104 Mapper initialized")
    
    def map_command(self, vpp_command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map VPP command to IEC 104 ASDU format.
        
        Args:
            vpp_command: VPP command dictionary
            
        Returns:
            IEC 104 ASDU format
            
        Raises:
            ValidationError: If command is invalid
        """
        if not vpp_command:
            raise ValidationError("VPP command cannot be None")
        
        command_type = vpp_command.get("command_type", "").lower()
        device_id = vpp_command.get("device_id", "")
        parameters = vpp_command.get("parameters", {})
        
        # Map command type to ASDU type
        if command_type == "set_power":
            asdu_type = self.ASDU_TYPES["C_SE_NC_1"]  # Set-point command
            value = parameters.get("power", 0.0)
        elif command_type == "set_demand_response":
            asdu_type = self.ASDU_TYPES["C_SE_NC_1"]  # Set-point command
            value = parameters.get("signal", 1.0)
        elif command_type == "get_state":
            asdu_type = self.ASDU_TYPES["M_ME_NC_1"]  # Measured value
            value = 0.0
        else:
            raise ValidationError(f"Unsupported command type: {command_type}")
        
        # Increment sequence number
        self.sequence_number = (self.sequence_number + 1) % 32768
        
        # Create ASDU
        asdu = {
            "asdu_type": asdu_type,
            "asdu_type_name": self._get_asdu_type_name(asdu_type),
            "sequence_number": self.sequence_number,
            "cause_of_transmission": self.COT_CODES["activation"],
            "originator_address": 0,
            "common_address": 1,
            "information_objects": [
                {
                    "information_object_address": int(device_id.split("-")[-1]) if "-" in device_id else 1,
                    "value": value,
                    "quality_descriptor": 0,
                    "timestamp": vpp_command.get("timestamp", ""),
                }
            ],
        }
        
        logger.info(
            f"VPP command mapped to IEC 104: "
            f"cmd_type={command_type}, asdu_type={asdu_type}"
        )
        
        return asdu
    
    def convert_response(self, protocol_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert IEC 104 response to VPP format.
        
        Args:
            protocol_response: IEC 104 ASDU response
            
        Returns:
            VPP response format
        """
        if not protocol_response:
            raise ValidationError("Protocol response cannot be None")
        
        info_objects = protocol_response.get("information_objects", [])
        if not info_objects:
            raise ValidationError("No information objects in response")
        
        first_object = info_objects[0]
        
        vpp_response = {
            "device_id": f"device-{first_object.get('information_object_address', 1)}",
            "status": "success",
            "value": first_object.get("value", 0),
            "quality": first_object.get("quality_descriptor", 0),
            "timestamp": first_object.get("timestamp", ""),
        }
        
        logger.info(
            f"IEC 104 response converted to VPP: "
            f"device_id={vpp_response['device_id']}"
        )
        
        return vpp_response
    
    def validate_message(self, message: Dict[str, Any]) -> bool:
        """
        Validate IEC 104 message format.
        
        Args:
            message: IEC 104 message
            
        Returns:
            True if valid, False otherwise
        """
        if not message:
            return False
        
        # Check required fields
        required_fields = ["asdu_type", "sequence_number", "cause_of_transmission"]
        for field in required_fields:
            if field not in message:
                logger.warning(f"Missing required field in IEC 104 message: {field}")
                return False
        
        # Validate ASDU type
        asdu_type = message.get("asdu_type")
        if asdu_type not in self.ASDU_TYPES.values():
            logger.warning(f"Invalid ASDU type: {asdu_type}")
            return False
        
        # Validate sequence number
        seq_num = message.get("sequence_number")
        if not isinstance(seq_num, int) or seq_num < 0 or seq_num >= 32768:
            logger.warning(f"Invalid sequence number: {seq_num}")
            return False
        
        return True
    
    def _get_asdu_type_name(self, asdu_type: int) -> str:
        """Get ASDU type name from code."""
        for name, code in self.ASDU_TYPES.items():
            if code == asdu_type:
                return name
        return "UNKNOWN"


class MQTTMapper(ProtocolMapper):
    """
    MQTT Protocol Mapper
    
    Maps VPP commands to MQTT 3.1.1 format.
    Implements QoS support and topic-based routing.
    
    Requirements:
    - 4.1: Map commands to MQTT protocol
    - 5.2: Follow MQTT 3.1.1 specification
    """
    
    # MQTT QoS levels
    QOS_LEVELS = {
        "at_most_once": 0,
        "at_least_once": 1,
        "exactly_once": 2,
    }
    
    def __init__(self):
        """Initialize MQTT mapper."""
        self.message_id = 0
        logger.info("MQTT Mapper initialized")
    
    def map_command(self, vpp_command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map VPP command to MQTT format.
        
        Args:
            vpp_command: VPP command dictionary
            
        Returns:
            MQTT message format
            
        Raises:
            ValidationError: If command is invalid
        """
        if not vpp_command:
            raise ValidationError("VPP command cannot be None")
        
        device_id = vpp_command.get("device_id", "")
        command_type = vpp_command.get("command_type", "").lower()
        parameters = vpp_command.get("parameters", {})
        
        # Build MQTT topic
        topic = f"vpp/device/{device_id}/command/{command_type}"
        
        # Increment message ID
        self.message_id = (self.message_id + 1) % 65536
        
        # Create MQTT message
        mqtt_message = {
            "message_id": self.message_id,
            "topic": topic,
            "qos": self.QOS_LEVELS["at_least_once"],
            "retain": False,
            "payload": {
                "command_id": vpp_command.get("command_id", ""),
                "device_id": device_id,
                "command_type": command_type,
                "parameters": parameters,
                "timestamp": vpp_command.get("timestamp", ""),
            },
        }
        
        logger.info(
            f"VPP command mapped to MQTT: "
            f"topic={topic}, qos={mqtt_message['qos']}"
        )
        
        return mqtt_message
    
    def convert_response(self, protocol_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert MQTT response to VPP format.
        
        Args:
            protocol_response: MQTT message response
            
        Returns:
            VPP response format
        """
        if not protocol_response:
            raise ValidationError("Protocol response cannot be None")
        
        payload = protocol_response.get("payload", {})
        
        vpp_response = {
            "device_id": payload.get("device_id", ""),
            "status": payload.get("status", "success"),
            "value": payload.get("value", 0),
            "timestamp": payload.get("timestamp", ""),
        }
        
        logger.info(
            f"MQTT response converted to VPP: "
            f"device_id={vpp_response['device_id']}"
        )
        
        return vpp_response
    
    def validate_message(self, message: Dict[str, Any]) -> bool:
        """
        Validate MQTT message format.
        
        Args:
            message: MQTT message
            
        Returns:
            True if valid, False otherwise
        """
        if not message:
            return False
        
        # Check required fields
        required_fields = ["topic", "qos", "payload"]
        for field in required_fields:
            if field not in message:
                logger.warning(f"Missing required field in MQTT message: {field}")
                return False
        
        # Validate topic
        topic = message.get("topic", "")
        if not isinstance(topic, str) or not topic:
            logger.warning(f"Invalid topic: {topic}")
            return False
        
        # Validate QoS
        qos = message.get("qos")
        if qos not in self.QOS_LEVELS.values():
            logger.warning(f"Invalid QoS level: {qos}")
            return False
        
        # Validate payload
        payload = message.get("payload")
        if not isinstance(payload, dict):
            logger.warning(f"Invalid payload type: {type(payload)}")
            return False
        
        return True
