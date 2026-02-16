"""
Unit Tests for Protocol Mappers

Tests IEC 104 and MQTT protocol mapping functionality.
"""

import pytest
from datetime import datetime
from services.protocol_mappers import IEC104Mapper, MQTTMapper
from utils.errors import ValidationError


class TestIEC104Mapper:
    """Test IEC 104 protocol mapper."""
    
    @pytest.fixture
    def mapper(self):
        """Create IEC 104 mapper instance."""
        return IEC104Mapper()
    
    @pytest.fixture
    def sample_command(self):
        """Create sample VPP command."""
        return {
            "command_id": "cmd-001",
            "device_id": "device-001",
            "command_type": "set_power",
            "parameters": {"power": 100.0},
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def test_mapper_initialization(self):
        """Test IEC 104 mapper initialization."""
        mapper = IEC104Mapper()
        assert mapper.sequence_number == 0
    
    def test_map_set_power_command(self, mapper, sample_command):
        """Test mapping set_power command to IEC 104."""
        asdu = mapper.map_command(sample_command)
        
        assert "asdu_type" in asdu
        assert "sequence_number" in asdu
        assert "cause_of_transmission" in asdu
        assert "information_objects" in asdu
        assert len(asdu["information_objects"]) > 0
        assert asdu["information_objects"][0]["value"] == 100.0
    
    def test_map_set_demand_response_command(self, mapper):
        """Test mapping set_demand_response command to IEC 104."""
        command = {
            "command_id": "cmd-002",
            "device_id": "device-002",
            "command_type": "set_demand_response",
            "parameters": {"signal": 0.8},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        asdu = mapper.map_command(command)
        
        assert asdu["information_objects"][0]["value"] == 0.8
    
    def test_map_get_state_command(self, mapper):
        """Test mapping get_state command to IEC 104."""
        command = {
            "command_id": "cmd-003",
            "device_id": "device-003",
            "command_type": "get_state",
            "parameters": {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        asdu = mapper.map_command(command)
        
        assert "asdu_type" in asdu
        assert asdu["information_objects"][0]["value"] == 0.0
    
    def test_map_command_invalid_type(self, mapper):
        """Test mapping invalid command type."""
        command = {
            "command_id": "cmd-004",
            "device_id": "device-004",
            "command_type": "invalid_command",
            "parameters": {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        with pytest.raises(ValidationError):
            mapper.map_command(command)
    
    def test_map_command_none(self, mapper):
        """Test mapping None command."""
        with pytest.raises(ValidationError):
            mapper.map_command(None)
    
    def test_sequence_number_increment(self, mapper, sample_command):
        """Test sequence number increments correctly."""
        asdu1 = mapper.map_command(sample_command)
        seq1 = asdu1["sequence_number"]
        
        asdu2 = mapper.map_command(sample_command)
        seq2 = asdu2["sequence_number"]
        
        assert seq2 == seq1 + 1
    
    def test_sequence_number_wraparound(self, mapper, sample_command):
        """Test sequence number wraparound at 32768."""
        mapper.sequence_number = 32767
        
        asdu = mapper.map_command(sample_command)
        
        assert asdu["sequence_number"] == 0
    
    def test_convert_response(self, mapper):
        """Test converting IEC 104 response to VPP format."""
        response = {
            "asdu_type": 9,
            "sequence_number": 1,
            "cause_of_transmission": 3,
            "information_objects": [
                {
                    "information_object_address": 1,
                    "value": 100.0,
                    "quality_descriptor": 0,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
        }
        
        vpp_response = mapper.convert_response(response)
        
        assert vpp_response["device_id"] == "device-1"
        assert vpp_response["status"] == "success"
        assert vpp_response["value"] == 100.0
    
    def test_convert_response_none(self, mapper):
        """Test converting None response."""
        with pytest.raises(ValidationError):
            mapper.convert_response(None)
    
    def test_convert_response_no_objects(self, mapper):
        """Test converting response with no information objects."""
        response = {
            "asdu_type": 9,
            "sequence_number": 1,
            "information_objects": [],
        }
        
        with pytest.raises(ValidationError):
            mapper.convert_response(response)
    
    def test_validate_message_valid(self, mapper):
        """Test validating valid IEC 104 message."""
        message = {
            "asdu_type": 9,
            "sequence_number": 1,
            "cause_of_transmission": 3,
            "information_objects": [{"value": 100.0}],
        }
        
        assert mapper.validate_message(message) == True
    
    def test_validate_message_missing_field(self, mapper):
        """Test validating message with missing field."""
        message = {
            "asdu_type": 9,
            "sequence_number": 1,
            # Missing cause_of_transmission
            "information_objects": [{"value": 100.0}],
        }
        
        assert mapper.validate_message(message) == False
    
    def test_validate_message_invalid_asdu_type(self, mapper):
        """Test validating message with invalid ASDU type."""
        message = {
            "asdu_type": 999,  # Invalid
            "sequence_number": 1,
            "cause_of_transmission": 3,
            "information_objects": [{"value": 100.0}],
        }
        
        assert mapper.validate_message(message) == False
    
    def test_validate_message_invalid_sequence(self, mapper):
        """Test validating message with invalid sequence number."""
        message = {
            "asdu_type": 9,
            "sequence_number": 32768,  # Out of range
            "cause_of_transmission": 3,
            "information_objects": [{"value": 100.0}],
        }
        
        assert mapper.validate_message(message) == False
    
    def test_validate_message_none(self, mapper):
        """Test validating None message."""
        assert mapper.validate_message(None) == False


class TestMQTTMapper:
    """Test MQTT protocol mapper."""
    
    @pytest.fixture
    def mapper(self):
        """Create MQTT mapper instance."""
        return MQTTMapper()
    
    @pytest.fixture
    def sample_command(self):
        """Create sample VPP command."""
        return {
            "command_id": "cmd-001",
            "device_id": "device-001",
            "command_type": "set_power",
            "parameters": {"power": 100.0},
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def test_mapper_initialization(self):
        """Test MQTT mapper initialization."""
        mapper = MQTTMapper()
        assert mapper.message_id == 0
    
    def test_map_command(self, mapper, sample_command):
        """Test mapping VPP command to MQTT."""
        mqtt_msg = mapper.map_command(sample_command)
        
        assert "message_id" in mqtt_msg
        assert "topic" in mqtt_msg
        assert "qos" in mqtt_msg
        assert "payload" in mqtt_msg
        assert mqtt_msg["topic"] == "vpp/device/device-001/command/set_power"
        assert mqtt_msg["qos"] == 1  # at_least_once
    
    def test_map_command_different_types(self, mapper):
        """Test mapping different command types."""
        commands = [
            ("set_power", "vpp/device/device-001/command/set_power"),
            ("set_demand_response", "vpp/device/device-001/command/set_demand_response"),
            ("get_state", "vpp/device/device-001/command/get_state"),
        ]
        
        for cmd_type, expected_topic in commands:
            command = {
                "command_id": "cmd-001",
                "device_id": "device-001",
                "command_type": cmd_type,
                "parameters": {},
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            mqtt_msg = mapper.map_command(command)
            assert mqtt_msg["topic"] == expected_topic
    
    def test_map_command_none(self, mapper):
        """Test mapping None command."""
        with pytest.raises(ValidationError):
            mapper.map_command(None)
    
    def test_message_id_increment(self, mapper, sample_command):
        """Test message ID increments correctly."""
        msg1 = mapper.map_command(sample_command)
        id1 = msg1["message_id"]
        
        msg2 = mapper.map_command(sample_command)
        id2 = msg2["message_id"]
        
        assert id2 == id1 + 1
    
    def test_message_id_wraparound(self, mapper, sample_command):
        """Test message ID wraparound at 65536."""
        mapper.message_id = 65535
        
        msg = mapper.map_command(sample_command)
        
        assert msg["message_id"] == 0
    
    def test_convert_response(self, mapper):
        """Test converting MQTT response to VPP format."""
        response = {
            "topic": "vpp/device/device-001/response",
            "payload": {
                "device_id": "device-001",
                "status": "success",
                "value": 100.0,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
        
        vpp_response = mapper.convert_response(response)
        
        assert vpp_response["device_id"] == "device-001"
        assert vpp_response["status"] == "success"
        assert vpp_response["value"] == 100.0
    
    def test_convert_response_none(self, mapper):
        """Test converting None response."""
        with pytest.raises(ValidationError):
            mapper.convert_response(None)
    
    def test_validate_message_valid(self, mapper):
        """Test validating valid MQTT message."""
        message = {
            "topic": "vpp/device/device-001/command/set_power",
            "qos": 1,
            "payload": {"power": 100.0},
        }
        
        assert mapper.validate_message(message) == True
    
    def test_validate_message_missing_field(self, mapper):
        """Test validating message with missing field."""
        message = {
            "topic": "vpp/device/device-001/command/set_power",
            # Missing qos
            "payload": {"power": 100.0},
        }
        
        assert mapper.validate_message(message) == False
    
    def test_validate_message_invalid_qos(self, mapper):
        """Test validating message with invalid QoS."""
        message = {
            "topic": "vpp/device/device-001/command/set_power",
            "qos": 5,  # Invalid
            "payload": {"power": 100.0},
        }
        
        assert mapper.validate_message(message) == False
    
    def test_validate_message_invalid_payload_type(self, mapper):
        """Test validating message with invalid payload type."""
        message = {
            "topic": "vpp/device/device-001/command/set_power",
            "qos": 1,
            "payload": "invalid",  # Should be dict
        }
        
        assert mapper.validate_message(message) == False
    
    def test_validate_message_none(self, mapper):
        """Test validating None message."""
        assert mapper.validate_message(None) == False
    
    def test_payload_structure(self, mapper, sample_command):
        """Test MQTT payload structure."""
        mqtt_msg = mapper.map_command(sample_command)
        payload = mqtt_msg["payload"]
        
        assert payload["command_id"] == "cmd-001"
        assert payload["device_id"] == "device-001"
        assert payload["command_type"] == "set_power"
        assert payload["parameters"]["power"] == 100.0
