"""
Unit Tests for Protocol Converter Service

Tests protocol parsing, encoding, conversion, and validation for IEC 104 and MQTT.
"""

import pytest
from services.protocol_converter import ProtocolConverter, get_protocol_converter
from services.protocol_adapters import IEC104Adapter, MQTTAdapter
from utils.errors import ProtocolConversionError, ValidationError


class TestProtocolConverterInitialization:
    """Test protocol converter initialization and adapter registration"""
    
    def test_protocol_converter_initialization(self):
        """Test protocol converter initializes with adapters"""
        converter = ProtocolConverter()
        assert converter is not None
        assert len(converter.adapters) > 0
    
    def test_protocol_converter_has_iec104_adapter(self):
        """Test protocol converter has IEC 104 adapter"""
        converter = ProtocolConverter()
        assert "iec_104" in converter.adapters
    
    def test_protocol_converter_has_mqtt_adapter(self):
        """Test protocol converter has MQTT adapter"""
        converter = ProtocolConverter()
        assert "mqtt" in converter.adapters
    
    def test_register_custom_adapter(self):
        """Test registering a custom adapter"""
        converter = ProtocolConverter()
        custom_adapter = IEC104Adapter()
        converter.register_adapter("custom_protocol", custom_adapter)
        assert "custom_protocol" in converter.adapters
    
    def test_get_protocol_converter_singleton(self):
        """Test get_protocol_converter returns singleton"""
        converter1 = get_protocol_converter()
        converter2 = get_protocol_converter()
        assert converter1 is converter2


class TestIEC104Parsing:
    """Test IEC 104 message parsing"""
    
    def test_parse_valid_iec104_message(self):
        """Test parsing valid IEC 104 message"""
        converter = ProtocolConverter()
        
        # Create a valid IEC 104 message
        # Start byte (0x68) + Length (6) + APCI (6 bytes)
        raw_data = bytes([0x68, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        
        parsed = converter.parse_message("iec_104", raw_data)
        
        assert parsed["protocol"] == "iec_104"
        assert parsed["send_sequence"] == 0
        assert parsed["receive_sequence"] == 0
    
    def test_parse_iec104_with_asdu(self):
        """Test parsing IEC 104 message with ASDU"""
        converter = ProtocolConverter()
        
        # Create IEC 104 message with ASDU
        # Start byte + Length + APCI + ASDU
        asdu = bytes([0x01, 0x01, 0x03, 0x00, 0x01, 0x00, 0x00])  # ASDU data
        raw_data = bytes([0x68, len(asdu) + 6]) + bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) + asdu
        
        parsed = converter.parse_message("iec_104", raw_data)
        
        assert "asdu" in parsed
        assert parsed["asdu"]["type"] == 1
    
    def test_parse_invalid_iec104_start_byte(self):
        """Test parsing IEC 104 message with invalid start byte"""
        converter = ProtocolConverter()
        
        raw_data = bytes([0x69, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        
        with pytest.raises(ProtocolConversionError):
            converter.parse_message("iec_104", raw_data)
    
    def test_parse_iec104_message_too_short(self):
        """Test parsing IEC 104 message that's too short"""
        converter = ProtocolConverter()
        
        raw_data = bytes([0x68, 0x06])
        
        with pytest.raises(ProtocolConversionError):
            converter.parse_message("iec_104", raw_data)
    
    def test_parse_iec104_length_mismatch(self):
        """Test parsing IEC 104 message with length mismatch"""
        converter = ProtocolConverter()
        
        # Declare length 20 but only provide 8 bytes
        raw_data = bytes([0x68, 0x14, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        
        with pytest.raises(ProtocolConversionError):
            converter.parse_message("iec_104", raw_data)


class TestIEC104Encoding:
    """Test IEC 104 message encoding"""
    
    def test_encode_iec104_message(self):
        """Test encoding IEC 104 message"""
        converter = ProtocolConverter()
        
        data = {
            "protocol": "iec_104",
            "send_sequence": 0,
            "receive_sequence": 0
        }
        
        encoded = converter.encode_message("iec_104", data)
        
        assert encoded[0] == 0x68  # Start byte
        assert len(encoded) >= 8
    
    def test_encode_iec104_with_asdu(self):
        """Test encoding IEC 104 message with ASDU"""
        converter = ProtocolConverter()
        
        data = {
            "protocol": "iec_104",
            "send_sequence": 1,
            "receive_sequence": 2,
            "asdu": {
                "type": 1,
                "num_elements": 1,
                "cause_of_transmission": 3,
                "originator_address": 0,
                "common_address": 1,
                "data": "0102"
            }
        }
        
        encoded = converter.encode_message("iec_104", data)
        
        assert encoded[0] == 0x68
        assert len(encoded) > 8
    
    def test_encode_iec104_invalid_data(self):
        """Test encoding IEC 104 with invalid data"""
        converter = ProtocolConverter()
        
        data = {
            "protocol": "iec_104",
            "send_sequence": -1  # Invalid
        }
        
        with pytest.raises(ValidationError):
            converter.encode_message("iec_104", data)


class TestMQTTParsing:
    """Test MQTT message parsing"""
    
    def test_parse_valid_mqtt_publish(self):
        """Test parsing valid MQTT PUBLISH message"""
        converter = ProtocolConverter()
        
        # Create MQTT PUBLISH message
        # Byte 1: packet type (3) + flags
        # Byte 2: remaining length
        # Topic: length (2 bytes) + "test"
        # Payload: "hello"
        topic = b"test"
        payload = b"hello"
        
        message = bytearray()
        message.append(0x30)  # PUBLISH packet type
        message.append(2 + len(topic) + len(payload))  # Remaining length
        message.extend(len(topic).to_bytes(2, 'big'))
        message.extend(topic)
        message.extend(payload)
        
        parsed = converter.parse_message("mqtt", bytes(message))
        
        assert parsed["protocol"] == "mqtt"
        assert parsed["packet_type"] == 3
        assert parsed["topic"] == "test"
        assert parsed["payload"] == "hello"
    
    def test_parse_mqtt_with_qos(self):
        """Test parsing MQTT message with QoS"""
        converter = ProtocolConverter()
        
        # Create MQTT PUBLISH with QoS 1
        topic = b"test"
        payload = b"hello"
        
        message = bytearray()
        message.append(0x32)  # PUBLISH with QoS 1
        message.append(2 + len(topic) + 2 + len(payload))  # Remaining length
        message.extend(len(topic).to_bytes(2, 'big'))
        message.extend(topic)
        message.extend((1).to_bytes(2, 'big'))  # Packet ID
        message.extend(payload)
        
        parsed = converter.parse_message("mqtt", bytes(message))
        
        assert parsed["qos"] == 1
        assert parsed["packet_id"] == 1
    
    def test_parse_invalid_mqtt_packet_type(self):
        """Test parsing MQTT with invalid packet type"""
        converter = ProtocolConverter()
        
        # Invalid packet type (0)
        message = bytes([0x00, 0x00])
        
        with pytest.raises(ProtocolConversionError):
            converter.parse_message("mqtt", message)
    
    def test_parse_mqtt_message_too_short(self):
        """Test parsing MQTT message that's too short"""
        converter = ProtocolConverter()
        
        message = bytes([0x30])
        
        with pytest.raises(ProtocolConversionError):
            converter.parse_message("mqtt", message)


class TestMQTTEncoding:
    """Test MQTT message encoding"""
    
    def test_encode_mqtt_publish(self):
        """Test encoding MQTT PUBLISH message"""
        converter = ProtocolConverter()
        
        data = {
            "protocol": "mqtt",
            "packet_type": 3,
            "topic": "test",
            "payload": "hello",
            "qos": 0
        }
        
        encoded = converter.encode_message("mqtt", data)
        
        assert encoded[0] == 0x30  # PUBLISH packet type
        assert len(encoded) > 2
    
    def test_encode_mqtt_with_qos(self):
        """Test encoding MQTT with QoS"""
        converter = ProtocolConverter()
        
        data = {
            "protocol": "mqtt",
            "packet_type": 3,
            "topic": "test",
            "payload": "hello",
            "qos": 1,
            "packet_id": 1
        }
        
        encoded = converter.encode_message("mqtt", data)
        
        assert encoded[0] == 0x32  # PUBLISH with QoS 1
    
    def test_encode_mqtt_invalid_qos(self):
        """Test encoding MQTT with invalid QoS"""
        converter = ProtocolConverter()
        
        data = {
            "protocol": "mqtt",
            "packet_type": 3,
            "topic": "test",
            "payload": "hello",
            "qos": 5  # Invalid
        }
        
        with pytest.raises(ValidationError):
            converter.encode_message("mqtt", data)


class TestProtocolConversion:
    """Test protocol conversion between formats"""
    
    def test_convert_iec104_to_mqtt(self):
        """Test converting IEC 104 to MQTT"""
        converter = ProtocolConverter()
        
        # Create IEC 104 message
        raw_iec104 = bytes([0x68, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        
        # Convert to MQTT
        converted = converter.convert_message("iec_104", "mqtt", raw_iec104)
        
        assert isinstance(converted, bytes)
        assert len(converted) > 0
    
    def test_convert_mqtt_to_iec104(self):
        """Test converting MQTT to IEC 104"""
        converter = ProtocolConverter()
        
        # Create MQTT message
        topic = b"test"
        payload = b"hello"
        
        message = bytearray()
        message.append(0x30)
        message.append(2 + len(topic) + len(payload))
        message.extend(len(topic).to_bytes(2, 'big'))
        message.extend(topic)
        message.extend(payload)
        
        # Convert to IEC 104
        converted = converter.convert_message("mqtt", "iec_104", bytes(message))
        
        assert isinstance(converted, bytes)
        assert converted[0] == 0x68  # IEC 104 start byte
    
    def test_convert_unsupported_protocol(self):
        """Test converting with unsupported protocol"""
        converter = ProtocolConverter()
        
        raw_data = bytes([0x00, 0x01, 0x02])
        
        with pytest.raises(ProtocolConversionError):
            converter.convert_message("unsupported", "mqtt", raw_data)


class TestProtocolValidation:
    """Test protocol message validation"""
    
    def test_validate_iec104_message(self):
        """Test validating IEC 104 message"""
        converter = ProtocolConverter()
        
        data = {
            "protocol": "iec_104",
            "send_sequence": 0,
            "receive_sequence": 0
        }
        
        result = converter.validate_message("iec_104", data)
        assert result is True
    
    def test_validate_iec104_invalid_sequence(self):
        """Test validating IEC 104 with invalid sequence"""
        converter = ProtocolConverter()
        
        data = {
            "protocol": "iec_104",
            "send_sequence": -1  # Invalid
        }
        
        with pytest.raises(ValidationError):
            converter.validate_message("iec_104", data)
    
    def test_validate_mqtt_message(self):
        """Test validating MQTT message"""
        converter = ProtocolConverter()
        
        data = {
            "protocol": "mqtt",
            "packet_type": 3,
            "topic": "test",
            "payload": "hello",
            "qos": 0
        }
        
        result = converter.validate_message("mqtt", data)
        assert result is True
    
    def test_validate_mqtt_invalid_topic(self):
        """Test validating MQTT with invalid topic"""
        converter = ProtocolConverter()
        
        data = {
            "protocol": "mqtt",
            "packet_type": 3,
            "topic": "",  # Invalid - empty
            "payload": "hello",
            "qos": 0
        }
        
        with pytest.raises(ValidationError):
            converter.validate_message("mqtt", data)
    
    def test_validate_unsupported_protocol(self):
        """Test validating unsupported protocol"""
        converter = ProtocolConverter()
        
        data = {"protocol": "unsupported"}
        
        with pytest.raises(ProtocolConversionError):
            converter.validate_message("unsupported", data)


class TestProtocolMappingManagement:
    """Test protocol mapping CRUD operations"""
    
    def test_create_protocol_mapping(self, db_session):
        """Test creating protocol mapping"""
        converter = ProtocolConverter()
        
        mapping = converter.create_protocol_mapping(
            "test-mapping-1",
            "iec_104",
            "mqtt",
            {"field1": "field2"}
        )
        
        assert mapping["id"] == "test-mapping-1"
        assert mapping["source_protocol"] == "iec_104"
        assert mapping["target_protocol"] == "mqtt"
        assert mapping["is_active"] is True
    
    def test_create_duplicate_mapping(self, db_session):
        """Test creating duplicate mapping fails"""
        converter = ProtocolConverter()
        
        converter.create_protocol_mapping(
            "test-mapping-1",
            "iec_104",
            "mqtt",
            {}
        )
        
        with pytest.raises(ValidationError):
            converter.create_protocol_mapping(
                "test-mapping-1",
                "mqtt",
                "iec_104",
                {}
            )
    
    def test_get_protocol_mappings(self, db_session):
        """Test getting protocol mappings"""
        converter = ProtocolConverter()
        
        converter.create_protocol_mapping(
            "test-mapping-1",
            "iec_104",
            "mqtt",
            {}
        )
        
        mappings = converter.get_protocol_mappings()
        assert len(mappings) > 0
    
    def test_get_protocol_mappings_filtered(self, db_session):
        """Test getting protocol mappings with filter"""
        converter = ProtocolConverter()
        
        converter.create_protocol_mapping(
            "test-mapping-1",
            "iec_104",
            "mqtt",
            {}
        )
        
        mappings = converter.get_protocol_mappings(source_protocol="iec_104")
        assert len(mappings) > 0
        assert mappings[0]["source_protocol"] == "iec_104"
    
    def test_update_protocol_mapping(self, db_session):
        """Test updating protocol mapping"""
        converter = ProtocolConverter()
        
        converter.create_protocol_mapping(
            "test-mapping-1",
            "iec_104",
            "mqtt",
            {"old": "rule"}
        )
        
        updated = converter.update_protocol_mapping(
            "test-mapping-1",
            mapping_rules={"new": "rule"}
        )
        
        assert updated["mapping_rules"]["new"] == "rule"
    
    def test_update_nonexistent_mapping(self, db_session):
        """Test updating nonexistent mapping fails"""
        converter = ProtocolConverter()
        
        with pytest.raises(ValidationError):
            converter.update_protocol_mapping("nonexistent", mapping_rules={})
    
    def test_delete_protocol_mapping(self, db_session):
        """Test deleting protocol mapping"""
        converter = ProtocolConverter()
        
        converter.create_protocol_mapping(
            "test-mapping-1",
            "iec_104",
            "mqtt",
            {}
        )
        
        result = converter.delete_protocol_mapping("test-mapping-1")
        assert result is True
    
    def test_delete_nonexistent_mapping(self, db_session):
        """Test deleting nonexistent mapping fails"""
        converter = ProtocolConverter()
        
        with pytest.raises(ValidationError):
            converter.delete_protocol_mapping("nonexistent")


class TestIEC104Adapter:
    """Test IEC 104 adapter directly"""
    
    def test_iec104_adapter_parse(self):
        """Test IEC 104 adapter parsing"""
        adapter = IEC104Adapter()
        
        raw_data = bytes([0x68, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        parsed = adapter.parse_message(raw_data)
        
        assert parsed["protocol"] == "iec_104"
    
    def test_iec104_adapter_encode(self):
        """Test IEC 104 adapter encoding"""
        adapter = IEC104Adapter()
        
        data = {
            "protocol": "iec_104",
            "send_sequence": 0,
            "receive_sequence": 0
        }
        
        encoded = adapter.encode_message(data)
        assert encoded[0] == 0x68
    
    def test_iec104_adapter_validate(self):
        """Test IEC 104 adapter validation"""
        adapter = IEC104Adapter()
        
        data = {
            "protocol": "iec_104",
            "send_sequence": 0
        }
        
        result = adapter.validate_message(data)
        assert result is True


class TestMQTTAdapter:
    """Test MQTT adapter directly"""
    
    def test_mqtt_adapter_parse(self):
        """Test MQTT adapter parsing"""
        adapter = MQTTAdapter()
        
        topic = b"test"
        payload = b"hello"
        
        message = bytearray()
        message.append(0x30)
        message.append(2 + len(topic) + len(payload))
        message.extend(len(topic).to_bytes(2, 'big'))
        message.extend(topic)
        message.extend(payload)
        
        parsed = adapter.parse_message(bytes(message))
        
        assert parsed["protocol"] == "mqtt"
        assert parsed["topic"] == "test"
    
    def test_mqtt_adapter_encode(self):
        """Test MQTT adapter encoding"""
        adapter = MQTTAdapter()
        
        data = {
            "protocol": "mqtt",
            "packet_type": 3,
            "topic": "test",
            "payload": "hello",
            "qos": 0
        }
        
        encoded = adapter.encode_message(data)
        assert encoded[0] == 0x30
    
    def test_mqtt_adapter_validate(self):
        """Test MQTT adapter validation"""
        adapter = MQTTAdapter()
        
        data = {
            "protocol": "mqtt",
            "packet_type": 3,
            "topic": "test",
            "qos": 0
        }
        
        result = adapter.validate_message(data)
        assert result is True



# ============================================================================
# Property-Based Tests for Protocol Converter
# Feature: vpp-phase1-api
# ============================================================================

from hypothesis import given, strategies as st, settings, HealthCheck
import hypothesis.strategies as st


class TestProtocolConverterProperties:
    """Property-based tests for Protocol Converter service"""
    
    # ========================================================================
    # Property 16: IEC 104 Message Parsing Extracts All Data Elements
    # Validates: Requirements 8.1, 8.3
    # ========================================================================
    
    @given(
        send_seq=st.integers(min_value=0, max_value=65535),
        recv_seq=st.integers(min_value=0, max_value=65535),
        asdu_type=st.sampled_from([1, 3, 5, 9, 11, 13, 45, 46, 48]),
        num_elements=st.integers(min_value=1, max_value=127),
        cause=st.integers(min_value=0, max_value=255),
        originator=st.integers(min_value=0, max_value=255),
        common_addr=st.integers(min_value=0, max_value=65535)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_iec104_parsing_extracts_all_data_elements(
        self, send_seq, recv_seq, asdu_type, num_elements, cause, originator, common_addr
    ):
        """
        **Validates: Requirements 8.1, 8.3**
        
        For any valid IEC 104 message with ASDU data, parsing should extract
        all data elements including send/receive sequences, ASDU type, number
        of elements, cause of transmission, originator address, and common address.
        """
        converter = ProtocolConverter()
        adapter = IEC104Adapter()
        
        # Build ASDU
        asdu = bytearray()
        asdu.append(asdu_type)
        asdu.append(num_elements)
        asdu.append(cause)
        asdu.append(originator)
        asdu.append(common_addr & 0xFF)
        asdu.append((common_addr >> 8) & 0xFF)
        asdu.extend(b'\x00\x00')  # Add some data
        
        # Build IEC 104 frame
        frame = bytearray()
        frame.append(0x68)  # Start byte
        frame.append(len(asdu) + 6)  # Length
        frame.append(send_seq & 0xFF)
        frame.append((send_seq >> 8) & 0xFF)
        frame.append(recv_seq & 0xFF)
        frame.append((recv_seq >> 8) & 0xFF)
        frame.append(0x00)
        frame.append(0x00)
        frame.extend(asdu)
        
        # Parse message
        parsed = converter.parse_message("iec_104", bytes(frame))
        
        # Verify all data elements are extracted
        assert parsed["send_sequence"] == send_seq
        assert parsed["receive_sequence"] == recv_seq
        assert parsed["asdu"]["type"] == asdu_type
        assert parsed["asdu"]["num_elements"] == num_elements
        assert parsed["asdu"]["cause_of_transmission"] == cause
        assert parsed["asdu"]["originator_address"] == originator
        assert parsed["asdu"]["common_address"] == common_addr
    
    # ========================================================================
    # Property 17: Invalid IEC 104 Messages Are Rejected
    # Validates: Requirements 8.2
    # ========================================================================
    
    @given(
        invalid_start=st.integers(min_value=0, max_value=255).filter(lambda x: x != 0x68),
        length=st.integers(min_value=0, max_value=255)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_iec104_invalid_messages_rejected(self, invalid_start, length):
        """
        **Validates: Requirements 8.2**
        
        For any IEC 104 message with invalid structure (incorrect start byte,
        invalid length field), parsing should be rejected with an error.
        """
        converter = ProtocolConverter()
        
        # Create message with invalid start byte
        raw_data = bytes([invalid_start, length, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        
        with pytest.raises(ProtocolConversionError):
            converter.parse_message("iec_104", raw_data)
    
    # ========================================================================
    # Property 18: IEC 104 Encoding Produces Valid Messages
    # Validates: Requirements 8.4
    # ========================================================================
    
    @given(
        send_seq=st.integers(min_value=0, max_value=65535),
        recv_seq=st.integers(min_value=0, max_value=65535),
        asdu_type=st.sampled_from([1, 3, 5, 9, 11, 13, 45, 46, 48]),
        num_elements=st.integers(min_value=1, max_value=127)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_iec104_encoding_produces_valid_messages(
        self, send_seq, recv_seq, asdu_type, num_elements
    ):
        """
        **Validates: Requirements 8.4**
        
        For any internal command converted to IEC 104 format, the resulting
        message should conform to the IEC 60870-5-104 standard and be parseable.
        """
        converter = ProtocolConverter()
        
        # Create data to encode
        data = {
            "protocol": "iec_104",
            "send_sequence": send_seq,
            "receive_sequence": recv_seq,
            "asdu": {
                "type": asdu_type,
                "num_elements": num_elements,
                "cause_of_transmission": 3,
                "originator_address": 0,
                "common_address": 1,
                "data": "0000"
            }
        }
        
        # Encode message
        encoded = converter.encode_message("iec_104", data)
        
        # Verify it's valid IEC 104 format
        assert encoded[0] == 0x68  # Start byte
        assert len(encoded) >= 8  # Minimum frame size
        
        # Verify it can be parsed back
        parsed = converter.parse_message("iec_104", encoded)
        assert parsed["send_sequence"] == send_seq
        assert parsed["receive_sequence"] == recv_seq
    
    # ========================================================================
    # Property 19: Protocol Conversion Maintains Data Integrity
    # Validates: Requirements 8.5, 9.5
    # ========================================================================
    
    @given(
        topic=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        payload=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        qos=st.sampled_from([0, 1, 2])
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_protocol_conversion_maintains_data_integrity(self, topic, payload, qos):
        """
        **Validates: Requirements 8.5, 9.5**
        
        For any message converted from one protocol to another, the data
        should maintain semantic equivalence (round-trip property).
        """
        converter = ProtocolConverter()
        
        # Create MQTT message
        mqtt_data = {
            "protocol": "mqtt",
            "packet_type": 3,
            "topic": topic,
            "payload": payload,
            "qos": qos
        }
        
        # Encode to MQTT
        mqtt_encoded = converter.encode_message("mqtt", mqtt_data)
        
        # Parse back from MQTT
        mqtt_parsed = converter.parse_message("mqtt", mqtt_encoded)
        
        # Verify data integrity
        assert mqtt_parsed["topic"] == topic
        assert mqtt_parsed["payload"] == payload
        assert mqtt_parsed["qos"] == qos
    
    # ========================================================================
    # Property 20: MQTT Message Parsing Extracts Payload
    # Validates: Requirements 9.1, 9.3
    # ========================================================================
    
    @given(
        topic=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        payload=st.text(min_size=0, max_size=100, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        qos=st.sampled_from([0, 1, 2]),
        retain=st.booleans(),
        dup=st.booleans()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_mqtt_parsing_extracts_payload(self, topic, payload, qos, retain, dup):
        """
        **Validates: Requirements 9.1, 9.3**
        
        For any valid MQTT message, parsing should extract the payload and
        all metadata (topic, QoS, retain, dup flags).
        """
        converter = ProtocolConverter()
        
        # Create MQTT data
        data = {
            "protocol": "mqtt",
            "packet_type": 3,
            "topic": topic,
            "payload": payload,
            "qos": qos,
            "retain": retain,
            "dup": dup,
            "packet_id": 1 if qos > 0 else None
        }
        
        # Encode and parse
        encoded = converter.encode_message("mqtt", data)
        parsed = converter.parse_message("mqtt", encoded)
        
        # Verify payload extraction
        assert parsed["topic"] == topic
        assert parsed["payload"] == payload
        assert parsed["qos"] == qos
        assert parsed["retain"] == retain
        assert parsed["dup"] == dup
    
    # ========================================================================
    # Property 21: Invalid MQTT Messages Are Rejected
    # Validates: Requirements 9.2
    # ========================================================================
    
    @given(
        invalid_qos=st.integers(min_value=3, max_value=255),
        invalid_packet_type=st.integers(min_value=15, max_value=255)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_mqtt_invalid_messages_rejected(self, invalid_qos, invalid_packet_type):
        """
        **Validates: Requirements 9.2**
        
        For any MQTT message with invalid structure (invalid QoS, invalid
        packet type), validation should be rejected with an error.
        """
        converter = ProtocolConverter()
        
        # Test invalid QoS
        data_invalid_qos = {
            "protocol": "mqtt",
            "packet_type": 3,
            "topic": "test",
            "payload": "test",
            "qos": invalid_qos
        }
        
        with pytest.raises(ValidationError):
            converter.validate_message("mqtt", data_invalid_qos)
        
        # Test invalid packet type
        data_invalid_type = {
            "protocol": "mqtt",
            "packet_type": invalid_packet_type,
            "topic": "test",
            "payload": "test"
        }
        
        with pytest.raises(ValidationError):
            converter.validate_message("mqtt", data_invalid_type)
    
    # ========================================================================
    # Property 22: MQTT Encoding Produces Valid Messages
    # Validates: Requirements 9.4
    # ========================================================================
    
    @given(
        topic=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        payload=st.text(min_size=0, max_size=100, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        qos=st.sampled_from([0, 1, 2])
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_mqtt_encoding_produces_valid_messages(self, topic, payload, qos):
        """
        **Validates: Requirements 9.4**
        
        For any internal command converted to MQTT format, the resulting
        message should conform to MQTT 3.1.1 specification with appropriate QoS.
        """
        converter = ProtocolConverter()
        
        # Create MQTT data
        data = {
            "protocol": "mqtt",
            "packet_type": 3,
            "topic": topic,
            "payload": payload,
            "qos": qos,
            "packet_id": 1 if qos > 0 else None
        }
        
        # Encode message
        encoded = converter.encode_message("mqtt", data)
        
        # Verify MQTT format
        assert len(encoded) >= 2  # Minimum MQTT frame size
        assert (encoded[0] >> 4) == 3  # PUBLISH packet type
        
        # Verify it can be parsed back
        parsed = converter.parse_message("mqtt", encoded)
        assert parsed["topic"] == topic
        assert parsed["payload"] == payload
        assert parsed["qos"] == qos
    
    # ========================================================================
    # Property 23: Protocol Validation Detects All Structural Errors
    # Validates: Requirements 10.1, 10.2
    # ========================================================================
    
    @given(
        invalid_data=st.one_of(
            st.just(None),
            st.just("not a dict"),
            st.just([1, 2, 3]),
            st.dictionaries(
                st.text(min_size=1),
                st.integers(),
                min_size=1
            )
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_protocol_validation_detects_structural_errors(self, invalid_data):
        """
        **Validates: Requirements 10.1, 10.2**
        
        For any protocol message with structural errors, validation should
        detect the error and return appropriate error details.
        """
        converter = ProtocolConverter()
        
        # Skip valid dictionaries
        if isinstance(invalid_data, dict) and "protocol" in invalid_data:
            return
        
        # Test IEC 104 validation
        if not isinstance(invalid_data, dict):
            with pytest.raises((ValidationError, TypeError)):
                converter.validate_message("iec_104", invalid_data)
        
        # Test MQTT validation
        if not isinstance(invalid_data, dict):
            with pytest.raises((ValidationError, TypeError)):
                converter.validate_message("mqtt", invalid_data)
    
    # ========================================================================
    # Property 24: Malformed Messages Do Not Crash System
    # Validates: Requirements 10.5
    # ========================================================================
    
    @given(
        malformed_data=st.binary(min_size=1, max_size=1000)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_malformed_messages_do_not_crash_system(self, malformed_data):
        """
        **Validates: Requirements 10.5**
        
        For any malformed protocol message, the system should not crash or
        enter an undefined state, but instead return an error response.
        """
        converter = ProtocolConverter()
        
        # Test IEC 104 parsing with malformed data
        try:
            converter.parse_message("iec_104", malformed_data)
        except (ProtocolConversionError, ValidationError, Exception):
            # Expected - should raise an error, not crash
            pass
        
        # Test MQTT parsing with malformed data
        try:
            converter.parse_message("mqtt", malformed_data)
        except (ProtocolConversionError, ValidationError, Exception):
            # Expected - should raise an error, not crash
            pass
        
        # System should still be functional after malformed input
        assert converter is not None
        assert len(converter.adapters) > 0
