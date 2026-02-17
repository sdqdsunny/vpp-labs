"""
DNP3 Adapter Tests
"""

import pytest
import time
from services.protocol_adapters.dnp3_adapter import DNP3Adapter
from services.protocol_adapters.base import ProtocolMessage, ProtocolType


@pytest.fixture
def dnp3_adapter():
    """Create DNP3 adapter instance"""
    return DNP3Adapter("test-dnp3-adapter")


class TestDNP3Adapter:
    """Test DNP3 adapter"""

    def test_adapter_initialization(self, dnp3_adapter):
        """Test adapter initialization"""
        assert dnp3_adapter.adapter_id == "test-dnp3-adapter"
        assert dnp3_adapter.protocol_type == ProtocolType.DNP3
        assert dnp3_adapter.is_connected is False
        assert dnp3_adapter.message_count == 0
        assert dnp3_adapter.error_count == 0

    def test_get_status(self, dnp3_adapter):
        """Test get_status method"""
        status = dnp3_adapter.get_status()
        assert "adapter_id" in status
        assert "protocol_type" in status
        assert "is_connected" in status
        assert "event_queue_size" in status

    def test_parse_message(self, dnp3_adapter):
        """Test message parsing"""
        test_data = b'\x05\x64\x00\x00\x00\x00'
        parsed = dnp3_adapter.parse_message(test_data)
        assert isinstance(parsed, dict)
        assert "raw_data" in parsed
        assert "length" in parsed

    def test_encode_message(self, dnp3_adapter):
        """Test message encoding"""
        message = {"command": "control_output", "index": 0, "value": 1}
        encoded = dnp3_adapter.encode_message(message)
        assert isinstance(encoded, bytes)

    def test_validate_message(self, dnp3_adapter):
        """Test message validation"""
        valid_data = b'\x05\x64\x00\x00\x00\x00'
        assert dnp3_adapter.validate_message(valid_data) is True
        
        invalid_data = b''
        assert dnp3_adapter.validate_message(invalid_data) is False

    def test_send_message_not_connected(self, dnp3_adapter):
        """Test sending message when not connected"""
        message = ProtocolMessage(
            protocol="dnp3",
            message_id="msg-1",
            source="device-1",
            destination="device-2",
            timestamp=time.time(),
            data={
                "message_type": "command",
                "values": {"command": "control_output"},
            },
        )
        result = dnp3_adapter.send_message(message)
        assert result is False
        assert dnp3_adapter.error_count > 0

    def test_receive_message_empty_queue(self, dnp3_adapter):
        """Test receiving message from empty queue"""
        message = dnp3_adapter.receive_message(timeout=0.1)
        assert message is None

    def test_disconnect_not_connected(self, dnp3_adapter):
        """Test disconnecting when not connected"""
        result = dnp3_adapter.disconnect()
        assert result is True
        assert dnp3_adapter.is_connected is False

    def test_send_command_not_connected(self, dnp3_adapter):
        """Test sending command when not connected"""
        result = dnp3_adapter.send_command({"command": "control_output"})
        assert result is False

    def test_report_event_not_connected(self, dnp3_adapter):
        """Test reporting event when not connected"""
        result = dnp3_adapter.report_event({"event_type": "analog_change"})
        assert result is False

    def test_adapter_status_tracking(self, dnp3_adapter):
        """Test adapter status tracking"""
        initial_status = dnp3_adapter.get_status()
        assert initial_status["message_count"] == 0
        assert initial_status["error_count"] == 0
        
        # Simulate error
        dnp3_adapter._record_error("Test error")
        updated_status = dnp3_adapter.get_status()
        assert updated_status["error_count"] == 1
        assert updated_status["last_error"] == "Test error"

    def test_master_mode_config(self, dnp3_adapter):
        """Test master mode configuration"""
        config = {
            "mode": "master",
            "host": "localhost",
            "port": 20000,
            "timeout": 5,
        }
        # Connection will fail without actual server, but config should be stored
        dnp3_adapter.connect(config)
        assert dnp3_adapter.config is not None
        assert dnp3_adapter.config.mode == "master"

    def test_outstation_mode_config(self, dnp3_adapter):
        """Test outstation mode configuration"""
        config = {
            "mode": "outstation",
            "port": 20000,
            "timeout": 5,
        }
        # Connection will fail without actual setup, but config should be stored
        dnp3_adapter.connect(config)
        assert dnp3_adapter.config is not None
        assert dnp3_adapter.config.mode == "outstation"

    def test_authentication_config(self, dnp3_adapter):
        """Test authentication configuration"""
        config = {
            "mode": "master",
            "host": "localhost",
            "port": 20000,
            "use_authentication": True,
            "username": "admin",
            "password": "password",
        }
        # Connection will fail without actual server, but config should be stored
        dnp3_adapter.connect(config)
        assert dnp3_adapter.config is not None
        assert dnp3_adapter.config.use_authentication is True
        assert dnp3_adapter.config.username == "admin"
