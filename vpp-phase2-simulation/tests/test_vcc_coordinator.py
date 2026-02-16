"""
Unit Tests for Virtual Control Center (VCC) Coordinator

Tests VCC command mapping, response conversion, and network condition application.
"""

import pytest
from datetime import datetime
from services.vcc_coordinator import (
    VCCCoordinator,
    VPPCommand,
    ProtocolMessage,
    VPPResponse,
    VCCStatus,
    ProtocolType,
)
from utils.errors import ValidationError


class TestVCCCoordinator:
    """Test VCC Coordinator functionality."""
    
    @pytest.fixture
    def vcc(self):
        """Create VCC coordinator instance."""
        return VCCCoordinator()
    
    @pytest.fixture
    def sample_command(self):
        """Create sample VPP command."""
        return VPPCommand(
            command_id="cmd-001",
            device_id="device-001",
            command_type="set_power",
            parameters={"power": 100.0},
            timestamp=datetime.utcnow(),
        )
    
    def test_vcc_initialization(self):
        """Test VCC coordinator initialization."""
        vcc = VCCCoordinator()
        assert vcc.vcc_id is not None
        assert vcc.status == "initialized"
        assert len(vcc.active_messages) == 0
        assert vcc.total_messages_processed == 0
    
    def test_vcc_initialization_with_id(self):
        """Test VCC initialization with custom ID."""
        vcc = VCCCoordinator(vcc_id="vcc-custom")
        assert vcc.vcc_id == "vcc-custom"
    
    def test_map_command_to_iec104(self, vcc, sample_command):
        """Test mapping VPP command to IEC 104."""
        message = vcc.map_command(sample_command, "iec104")
        
        assert message.message_id is not None
        assert message.protocol == "iec104"
        assert message.source == "vcc"
        assert message.destination == sample_command.device_id
        assert "asdu_type" in message.payload
        assert message.message_id in vcc.active_messages
    
    def test_map_command_to_mqtt(self, vcc, sample_command):
        """Test mapping VPP command to MQTT."""
        message = vcc.map_command(sample_command, "mqtt")
        
        assert message.message_id is not None
        assert message.protocol == "mqtt"
        assert "topic" in message.payload
        assert "qos" in message.payload
        assert message.message_id in vcc.active_messages
    
    def test_map_command_invalid_protocol(self, vcc, sample_command):
        """Test mapping with invalid protocol."""
        with pytest.raises(ValidationError):
            vcc.map_command(sample_command, "invalid_protocol")
    
    def test_map_command_none_command(self, vcc):
        """Test mapping with None command."""
        with pytest.raises(ValidationError):
            vcc.map_command(None, "iec104")
    
    def test_map_command_empty_protocol(self, vcc, sample_command):
        """Test mapping with empty protocol."""
        with pytest.raises(ValidationError):
            vcc.map_command(sample_command, "")
    
    def test_convert_response_iec104(self, vcc):
        """Test converting IEC 104 response to VPP format."""
        protocol_message = ProtocolMessage(
            message_id="msg-001",
            protocol="iec104",
            source="device-001",
            destination="vcc",
            payload={
                "command_id": "cmd-001",
                "information_object_address": "001",
                "measured_value": 100.0,
                "timestamp": datetime.utcnow().isoformat(),
            },
            timestamp=datetime.utcnow(),
        )
        
        response = vcc.convert_response(protocol_message)
        
        assert response.response_id is not None
        assert response.device_id == "device-001"
        assert response.status == "success"
        assert response.data["value"] == 100.0
    
    def test_convert_response_mqtt(self, vcc):
        """Test converting MQTT response to VPP format."""
        protocol_message = ProtocolMessage(
            message_id="msg-002",
            protocol="mqtt",
            source="device-002",
            destination="vcc",
            payload={
                "topic": "vpp/device/device-002/response",
                "payload": {
                    "status": "success",
                    "value": 50.0,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
            timestamp=datetime.utcnow(),
        )
        
        response = vcc.convert_response(protocol_message)
        
        assert response.response_id is not None
        assert response.status == "success"
        assert response.data["value"] == 50.0
    
    def test_convert_response_none_message(self, vcc):
        """Test converting None message."""
        with pytest.raises(ValidationError):
            vcc.convert_response(None)
    
    def test_apply_network_conditions(self, vcc):
        """Test applying network conditions to message."""
        message = ProtocolMessage(
            message_id="msg-003",
            protocol="iec104",
            source="vcc",
            destination="device-001",
            payload={"test": "data"},
            timestamp=datetime.utcnow(),
        )
        
        result = vcc.apply_network_conditions(message, latency_ms=25.0, packet_loss_probability=0.0)
        
        assert result.latency_ms == 25.0
        assert result.packet_loss == False
        assert vcc.total_latency_ms == 25.0
    
    def test_apply_network_conditions_with_packet_loss(self, vcc):
        """Test applying network conditions with packet loss."""
        message = ProtocolMessage(
            message_id="msg-004",
            protocol="mqtt",
            source="vcc",
            destination="device-002",
            payload={"test": "data"},
            timestamp=datetime.utcnow(),
        )
        
        # Set high packet loss probability to ensure loss
        result = vcc.apply_network_conditions(message, latency_ms=30.0, packet_loss_probability=1.0)
        
        assert result.packet_loss == True
        assert vcc.packet_loss_count == 1
    
    def test_apply_network_conditions_invalid_latency(self, vcc):
        """Test applying network conditions with invalid latency."""
        message = ProtocolMessage(
            message_id="msg-005",
            protocol="iec104",
            source="vcc",
            destination="device-001",
            payload={"test": "data"},
            timestamp=datetime.utcnow(),
        )
        
        with pytest.raises(ValidationError):
            vcc.apply_network_conditions(message, latency_ms=-10.0)
    
    def test_apply_network_conditions_invalid_packet_loss(self, vcc):
        """Test applying network conditions with invalid packet loss probability."""
        message = ProtocolMessage(
            message_id="msg-006",
            protocol="mqtt",
            source="vcc",
            destination="device-002",
            payload={"test": "data"},
            timestamp=datetime.utcnow(),
        )
        
        with pytest.raises(ValidationError):
            vcc.apply_network_conditions(message, packet_loss_probability=1.5)
    
    def test_get_vcc_status(self, vcc, sample_command):
        """Test getting VCC status."""
        # Map a command to add active message
        vcc.map_command(sample_command, "iec104")
        
        status = vcc.get_vcc_status()
        
        assert status.vcc_id == vcc.vcc_id
        assert status.status == "initialized"
        assert status.active_messages == 1
        assert status.total_messages_processed == 0
    
    def test_check_message_ordering_correct(self, vcc):
        """Test message ordering check with correct sequence."""
        device_id = "device-001"
        
        assert vcc.check_message_ordering(device_id, 1) == True
        assert vcc.check_message_ordering(device_id, 2) == True
        assert vcc.check_message_ordering(device_id, 3) == True
        assert vcc.message_ordering_violations == 0
    
    def test_check_message_ordering_violation(self, vcc):
        """Test message ordering check with violation."""
        device_id = "device-001"
        
        assert vcc.check_message_ordering(device_id, 1) == True
        assert vcc.check_message_ordering(device_id, 2) == True
        assert vcc.check_message_ordering(device_id, 2) == False  # Duplicate
        assert vcc.message_ordering_violations == 1
    
    def test_check_message_ordering_out_of_order(self, vcc):
        """Test message ordering check with out-of-order sequence."""
        device_id = "device-001"
        
        assert vcc.check_message_ordering(device_id, 1) == True
        assert vcc.check_message_ordering(device_id, 3) == True
        assert vcc.check_message_ordering(device_id, 2) == False  # Out of order
        assert vcc.message_ordering_violations == 1
    
    def test_reset(self, vcc, sample_command):
        """Test VCC reset."""
        # Add some state
        vcc.map_command(sample_command, "iec104")
        vcc.total_messages_processed = 10
        vcc.packet_loss_count = 5
        
        vcc.reset()
        
        assert len(vcc.active_messages) == 0
        assert len(vcc.message_queue) == 0
        assert vcc.total_messages_processed == 0
        assert vcc.packet_loss_count == 0
        assert vcc.message_ordering_violations == 0
    
    def test_vpp_command_to_dict(self, sample_command):
        """Test VPP command to dictionary conversion."""
        cmd_dict = sample_command.to_dict()
        
        assert cmd_dict["command_id"] == "cmd-001"
        assert cmd_dict["device_id"] == "device-001"
        assert cmd_dict["command_type"] == "set_power"
        assert cmd_dict["parameters"]["power"] == 100.0
    
    def test_protocol_message_to_dict(self):
        """Test protocol message to dictionary conversion."""
        message = ProtocolMessage(
            message_id="msg-001",
            protocol="iec104",
            source="vcc",
            destination="device-001",
            payload={"test": "data"},
            timestamp=datetime.utcnow(),
            latency_ms=25.0,
            packet_loss=False,
        )
        
        msg_dict = message.to_dict()
        
        assert msg_dict["message_id"] == "msg-001"
        assert msg_dict["protocol"] == "iec104"
        assert msg_dict["latency_ms"] == 25.0
        assert msg_dict["packet_loss"] == False
    
    def test_vpp_response_to_dict(self):
        """Test VPP response to dictionary conversion."""
        response = VPPResponse(
            response_id="resp-001",
            command_id="cmd-001",
            device_id="device-001",
            status="success",
            data={"value": 100.0},
            timestamp=datetime.utcnow(),
        )
        
        resp_dict = response.to_dict()
        
        assert resp_dict["response_id"] == "resp-001"
        assert resp_dict["command_id"] == "cmd-001"
        assert resp_dict["status"] == "success"
        assert resp_dict["data"]["value"] == 100.0
    
    def test_vcc_status_to_dict(self, vcc):
        """Test VCC status to dictionary conversion."""
        status = vcc.get_vcc_status()
        status_dict = status.to_dict()
        
        assert status_dict["vcc_id"] == vcc.vcc_id
        assert status_dict["status"] == "initialized"
        assert "active_messages" in status_dict
        assert "total_messages_processed" in status_dict
    
    def test_multiple_commands_mapping(self, vcc):
        """Test mapping multiple commands."""
        commands = [
            VPPCommand(
                command_id=f"cmd-{i:03d}",
                device_id=f"device-{i:03d}",
                command_type="set_power",
                parameters={"power": float(i * 10)},
                timestamp=datetime.utcnow(),
            )
            for i in range(1, 6)
        ]
        
        messages = []
        for cmd in commands:
            msg = vcc.map_command(cmd, "iec104")
            messages.append(msg)
        
        assert len(messages) == 5
        assert len(vcc.active_messages) == 5
        assert len(vcc.message_queue) == 5
    
    def test_command_response_flow(self, vcc, sample_command):
        """Test complete command-response flow."""
        # Map command
        message = vcc.map_command(sample_command, "iec104")
        assert message.message_id in vcc.active_messages
        
        # Apply network conditions
        message = vcc.apply_network_conditions(message, latency_ms=20.0)
        
        # Convert response
        response = vcc.convert_response(message)
        assert response.response_id is not None
        assert message.message_id not in vcc.active_messages
