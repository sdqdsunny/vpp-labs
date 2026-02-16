"""
Protocol Adapters

Implements protocol-specific parsing, encoding, and validation for:
- IEC 104 (IEC 60870-5-104)
- MQTT (MQTT 3.1.1)
"""

import struct
import logging
from typing import Dict, Any, List
from services.protocol_converter import ProtocolAdapter
from utils.errors import ProtocolConversionError, ValidationError

logger = logging.getLogger(__name__)


class IEC104Adapter(ProtocolAdapter):
    """
    IEC 104 Protocol Adapter
    
    Implements parsing, encoding, and validation for IEC 60870-5-104 protocol.
    Handles ASDU (Application Service Data Unit) parsing and generation.
    """
    
    # IEC 104 Constants
    START_BYTE = 0x68  # Start byte for IEC 104 frame
    APCI_LENGTH = 6    # APCI (Application Protocol Control Information) length
    
    # ASDU Type Identifiers
    ASDU_TYPES = {
        1: "M_SP_NA_1",   # Single-point information
        2: "M_SP_TA_1",   # Single-point information with time tag
        3: "M_DP_NA_1",   # Double-point information
        4: "M_DP_TA_1",   # Double-point information with time tag
        5: "M_ST_NA_1",   # Step position information
        6: "M_ST_TA_1",   # Step position information with time tag
        7: "M_BO_NA_1",   # Bitstring of 32 bits
        8: "M_BO_TA_1",   # Bitstring of 32 bits with time tag
        9: "M_ME_NA_1",   # Measured value, normalized
        10: "M_ME_TA_1",  # Measured value, normalized with time tag
        11: "M_ME_NB_1",  # Measured value, scaled
        12: "M_ME_TB_1",  # Measured value, scaled with time tag
        13: "M_ME_NC_1",  # Measured value, short floating point
        14: "M_ME_TC_1",  # Measured value, short floating point with time tag
        15: "M_IT_NA_1",  # Integrated totals
        16: "M_IT_TA_1",  # Integrated totals with time tag
        20: "M_PS_NA_1",  # Packed single-point information
        21: "M_ME_ND_1",  # Measured value, normalized without quality
        30: "M_SP_TB_1",  # Single-point information with time tag CP56Time2a
        31: "M_DP_TB_1",  # Double-point information with time tag CP56Time2a
        32: "M_ST_TB_1",  # Step position information with time tag CP56Time2a
        33: "M_BO_TB_1",  # Bitstring of 32 bits with time tag CP56Time2a
        34: "M_ME_TD_1",  # Measured value, normalized with time tag CP56Time2a
        35: "M_ME_TE_1",  # Measured value, scaled with time tag CP56Time2a
        36: "M_ME_TF_1",  # Measured value, short floating point with time tag CP56Time2a
        37: "M_IT_TB_1",  # Integrated totals with time tag CP56Time2a
        38: "M_EP_TA_1",  # Event of protection equipment with time tag
        39: "M_EP_TB_1",  # Event of protection equipment with time tag CP56Time2a
        40: "M_PS_TB_1",  # Packed single-point information with time tag CP56Time2a
        45: "C_SC_NA_1",  # Single command
        46: "C_DC_NA_1",  # Double command
        47: "C_RC_NA_1",  # Regulating step command
        48: "C_SE_NA_1",  # Set-point command, normalized value
        49: "C_SE_NB_1",  # Set-point command, scaled value
        50: "C_SE_NC_1",  # Set-point command, short floating point value
        51: "C_BO_NA_1",  # Bitstring 32 bits command
        58: "C_SC_TA_1",  # Single command with time tag CP56Time2a
        59: "C_DC_TA_1",  # Double command with time tag CP56Time2a
        60: "C_RC_TA_1",  # Regulating step command with time tag CP56Time2a
        61: "C_SE_TA_1",  # Set-point command, normalized value with time tag CP56Time2a
        62: "C_SE_TB_1",  # Set-point command, scaled value with time tag CP56Time2a
        63: "C_SE_TC_1",  # Set-point command, short floating point value with time tag CP56Time2a
        64: "C_BO_TA_1",  # Bitstring 32 bits command with time tag CP56Time2a
    }
    
    def parse_message(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Parse IEC 104 message.
        
        Args:
            raw_data: Raw IEC 104 message bytes
            
        Returns:
            Parsed message as dictionary
            
        Raises:
            ProtocolConversionError: If message structure is invalid
        """
        if len(raw_data) < self.APCI_LENGTH + 2:
            raise ProtocolConversionError(
                "IEC 104 message too short",
                details={"min_length": self.APCI_LENGTH + 2, "actual_length": len(raw_data)}
            )
        
        # Check start byte
        if raw_data[0] != self.START_BYTE:
            raise ProtocolConversionError(
                "Invalid IEC 104 start byte",
                details={"expected": hex(self.START_BYTE), "actual": hex(raw_data[0])}
            )
        
        # Parse length field
        length = raw_data[1]
        if len(raw_data) < length + 2:
            raise ProtocolConversionError(
                "IEC 104 message length mismatch",
                details={"declared_length": length, "actual_length": len(raw_data) - 2}
            )
        
        # Parse APCI
        apci_data = raw_data[2:8]
        send_seq = (apci_data[1] << 8) | apci_data[0]
        recv_seq = (apci_data[3] << 8) | apci_data[2]
        
        # Parse ASDU if present
        asdu_data = {}
        if length > self.APCI_LENGTH:
            asdu_bytes = raw_data[8:8 + length - self.APCI_LENGTH]
            asdu_data = self._parse_asdu(asdu_bytes)
        
        return {
            "protocol": "iec_104",
            "send_sequence": send_seq,
            "receive_sequence": recv_seq,
            "asdu": asdu_data,
            "raw_length": length
        }
    
    def _parse_asdu(self, asdu_bytes: bytes) -> Dict[str, Any]:
        """
        Parse ASDU (Application Service Data Unit).
        
        Args:
            asdu_bytes: ASDU bytes
            
        Returns:
            Parsed ASDU as dictionary
        """
        if len(asdu_bytes) < 6:
            raise ProtocolConversionError("ASDU too short")
        
        asdu_type = asdu_bytes[0]
        num_elements = asdu_bytes[1]
        cause_of_transmission = asdu_bytes[2]
        originator_address = asdu_bytes[3]
        common_address = (asdu_bytes[5] << 8) | asdu_bytes[4]
        
        type_name = self.ASDU_TYPES.get(asdu_type, f"UNKNOWN_{asdu_type}")
        
        return {
            "type": asdu_type,
            "type_name": type_name,
            "num_elements": num_elements,
            "cause_of_transmission": cause_of_transmission,
            "originator_address": originator_address,
            "common_address": common_address,
            "data": asdu_bytes[6:].hex() if len(asdu_bytes) > 6 else ""
        }
    
    def encode_message(self, data: Dict[str, Any]) -> bytes:
        """
        Encode data to IEC 104 message format.
        
        Args:
            data: Data to encode
            
        Returns:
            Encoded IEC 104 message bytes
            
        Raises:
            ProtocolConversionError: If encoding fails
        """
        # Validate data structure
        self.validate_message(data)
        
        # Build APCI
        send_seq = data.get("send_sequence", 0)
        recv_seq = data.get("receive_sequence", 0)
        
        apci = bytearray(6)
        apci[0] = send_seq & 0xFF
        apci[1] = (send_seq >> 8) & 0xFF
        apci[2] = recv_seq & 0xFF
        apci[3] = (recv_seq >> 8) & 0xFF
        apci[4] = 0x00
        apci[5] = 0x00
        
        # Build ASDU if present
        asdu_bytes = bytearray()
        if "asdu" in data and data["asdu"]:
            asdu_bytes = self._encode_asdu(data["asdu"])
        
        # Build frame
        frame = bytearray()
        frame.append(self.START_BYTE)
        frame.append(len(apci) + len(asdu_bytes))
        frame.extend(apci)
        frame.extend(asdu_bytes)
        
        return bytes(frame)
    
    def _encode_asdu(self, asdu_data: Dict[str, Any]) -> bytes:
        """
        Encode ASDU data.
        
        Args:
            asdu_data: ASDU data dictionary
            
        Returns:
            Encoded ASDU bytes
        """
        asdu = bytearray()
        
        asdu.append(asdu_data.get("type", 1))
        asdu.append(asdu_data.get("num_elements", 1))
        asdu.append(asdu_data.get("cause_of_transmission", 0))
        asdu.append(asdu_data.get("originator_address", 0))
        
        common_address = asdu_data.get("common_address", 0)
        asdu.append(common_address & 0xFF)
        asdu.append((common_address >> 8) & 0xFF)
        
        # Add data if present
        if "data" in asdu_data:
            data_str = asdu_data["data"]
            if isinstance(data_str, str):
                asdu.extend(bytes.fromhex(data_str))
            else:
                asdu.extend(data_str)
        
        return bytes(asdu)
    
    def validate_message(self, data: Dict[str, Any]) -> bool:
        """
        Validate IEC 104 message structure.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError("IEC 104 data must be a dictionary")
        
        if "protocol" in data and data["protocol"] != "iec_104":
            raise ValidationError(f"Invalid protocol: {data['protocol']}")
        
        # Validate sequence numbers
        if "send_sequence" in data:
            if not isinstance(data["send_sequence"], int) or data["send_sequence"] < 0:
                raise ValidationError("send_sequence must be non-negative integer")
        
        if "receive_sequence" in data:
            if not isinstance(data["receive_sequence"], int) or data["receive_sequence"] < 0:
                raise ValidationError("receive_sequence must be non-negative integer")
        
        # Validate ASDU if present
        if "asdu" in data and data["asdu"]:
            asdu = data["asdu"]
            if not isinstance(asdu, dict):
                raise ValidationError("ASDU must be a dictionary")
            
            if "type" in asdu:
                if not isinstance(asdu["type"], int) or asdu["type"] < 0 or asdu["type"] > 255:
                    raise ValidationError("ASDU type must be 0-255")
        
        return True


class MQTTAdapter(ProtocolAdapter):
    """
    MQTT Protocol Adapter
    
    Implements parsing, encoding, and validation for MQTT 3.1.1 protocol.
    """
    
    # MQTT Control Packet Types
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
        14: "DISCONNECT"
    }
    
    # QoS Levels
    QOS_LEVELS = {0, 1, 2}
    
    def parse_message(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Parse MQTT message.
        
        Args:
            raw_data: Raw MQTT message bytes
            
        Returns:
            Parsed message as dictionary
            
        Raises:
            ProtocolConversionError: If message structure is invalid
        """
        if len(raw_data) < 2:
            raise ProtocolConversionError("MQTT message too short")
        
        # Parse fixed header
        byte1 = raw_data[0]
        packet_type = (byte1 >> 4) & 0x0F
        flags = byte1 & 0x0F
        
        if packet_type not in self.PACKET_TYPES:
            raise ProtocolConversionError(
                f"Invalid MQTT packet type: {packet_type}"
            )
        
        # Parse remaining length
        remaining_length, length_bytes = self._decode_remaining_length(raw_data[1:])
        
        if len(raw_data) < 1 + length_bytes + remaining_length:
            raise ProtocolConversionError("MQTT message length mismatch")
        
        # Parse payload based on packet type
        payload_start = 1 + length_bytes
        payload = raw_data[payload_start:payload_start + remaining_length]
        
        result = {
            "protocol": "mqtt",
            "packet_type": packet_type,
            "packet_type_name": self.PACKET_TYPES[packet_type],
            "flags": flags,
            "remaining_length": remaining_length
        }
        
        # Parse PUBLISH packet payload
        if packet_type == 3:  # PUBLISH
            result.update(self._parse_publish(payload, flags))
        
        return result
    
    def _decode_remaining_length(self, data: bytes) -> tuple:
        """
        Decode MQTT remaining length field.
        
        Args:
            data: Bytes starting with remaining length
            
        Returns:
            Tuple of (remaining_length, bytes_used)
        """
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
        
        raise ProtocolConversionError("Invalid MQTT remaining length")
    
    def _parse_publish(self, payload: bytes, flags: int) -> Dict[str, Any]:
        """
        Parse MQTT PUBLISH packet payload.
        
        Args:
            payload: PUBLISH packet payload
            flags: Packet flags
            
        Returns:
            Parsed PUBLISH data
        """
        if len(payload) < 2:
            raise ProtocolConversionError("MQTT PUBLISH payload too short")
        
        # Parse topic name
        topic_length = (payload[0] << 8) | payload[1]
        if len(payload) < 2 + topic_length:
            raise ProtocolConversionError("MQTT topic length mismatch")
        
        topic = payload[2:2 + topic_length].decode('utf-8', errors='replace')
        
        # Parse QoS and packet ID if present
        offset = 2 + topic_length
        qos = (flags >> 1) & 0x03
        packet_id = None
        
        if qos > 0 and len(payload) >= offset + 2:
            packet_id = (payload[offset] << 8) | payload[offset + 1]
            offset += 2
        
        # Parse message payload
        message_payload = payload[offset:].decode('utf-8', errors='replace')
        
        return {
            "topic": topic,
            "qos": qos,
            "retain": (flags & 0x01) != 0,
            "dup": (flags & 0x08) != 0,
            "packet_id": packet_id,
            "payload": message_payload
        }
    
    def encode_message(self, data: Dict[str, Any]) -> bytes:
        """
        Encode data to MQTT message format.
        
        Args:
            data: Data to encode
            
        Returns:
            Encoded MQTT message bytes
            
        Raises:
            ProtocolConversionError: If encoding fails
        """
        # Validate data structure
        self.validate_message(data)
        
        packet_type = data.get("packet_type", 3)  # Default to PUBLISH
        
        if packet_type == 3:  # PUBLISH
            return self._encode_publish(data)
        else:
            raise ProtocolConversionError(f"Encoding for packet type {packet_type} not implemented")
    
    def _encode_publish(self, data: Dict[str, Any]) -> bytes:
        """
        Encode MQTT PUBLISH packet.
        
        Args:
            data: PUBLISH data
            
        Returns:
            Encoded PUBLISH packet bytes
        """
        topic = data.get("topic", "").encode('utf-8')
        payload = data.get("payload", "").encode('utf-8')
        qos = data.get("qos", 0)
        retain = data.get("retain", False)
        dup = data.get("dup", False)
        packet_id = data.get("packet_id", 0)
        
        # Build variable header
        variable_header = bytearray()
        variable_header.extend(len(topic).to_bytes(2, 'big'))
        variable_header.extend(topic)
        
        if qos > 0:
            variable_header.extend(packet_id.to_bytes(2, 'big'))
        
        # Build payload
        message_payload = payload
        
        # Build fixed header
        byte1 = (3 << 4)  # PUBLISH packet type
        if dup:
            byte1 |= 0x08
        byte1 |= (qos << 1)
        if retain:
            byte1 |= 0x01
        
        remaining_length = len(variable_header) + len(message_payload)
        
        # Encode remaining length
        encoded_length = self._encode_remaining_length(remaining_length)
        
        # Build complete message
        message = bytearray()
        message.append(byte1)
        message.extend(encoded_length)
        message.extend(variable_header)
        message.extend(message_payload)
        
        return bytes(message)
    
    def _encode_remaining_length(self, length: int) -> bytes:
        """
        Encode MQTT remaining length field.
        
        Args:
            length: Remaining length value
            
        Returns:
            Encoded remaining length bytes
        """
        encoded = bytearray()
        
        while length > 0:
            encoded_byte = length % 128
            length //= 128
            
            if length > 0:
                encoded_byte |= 0x80
            
            encoded.append(encoded_byte)
        
        return bytes(encoded) if encoded else bytes([0])
    
    def validate_message(self, data: Dict[str, Any]) -> bool:
        """
        Validate MQTT message structure.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError("MQTT data must be a dictionary")
        
        if "protocol" in data and data["protocol"] != "mqtt":
            raise ValidationError(f"Invalid protocol: {data['protocol']}")
        
        # Validate packet type
        if "packet_type" in data:
            packet_type = data["packet_type"]
            if not isinstance(packet_type, int) or packet_type < 1 or packet_type > 14:
                raise ValidationError("packet_type must be 1-14")
        
        # Validate QoS
        if "qos" in data:
            qos = data["qos"]
            if qos not in self.QOS_LEVELS:
                raise ValidationError(f"QoS must be one of {self.QOS_LEVELS}")
        
        # Validate topic
        if "topic" in data:
            topic = data["topic"]
            if not isinstance(topic, str) or len(topic) == 0:
                raise ValidationError("topic must be non-empty string")
            if len(topic) > 65535:
                raise ValidationError("topic exceeds maximum length")
        
        # Validate payload
        if "payload" in data:
            payload = data["payload"]
            if not isinstance(payload, str):
                raise ValidationError("payload must be string")
        
        return True
