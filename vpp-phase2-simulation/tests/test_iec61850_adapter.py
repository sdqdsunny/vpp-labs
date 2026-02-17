"""
IEC 61850 Adapter Tests
"""

import pytest
import time
from services.protocol_adapters.iec61850_adapter import IEC61850Adapter
from services.protocol_adapters.base import ProtocolMessage, ProtocolType


@pytest.fixture
def iec61850_adapter():
    """Create IEC 61850 adapter instance"""
    return IEC61850Adapter("test-iec61850-adapter")


class TestIEC61850Adapter:
    """Test IEC 61850 adapter"""

    def test_adapter_initialization(self, iec61850_adapter):
        """Test adapter initialization"""
        assert iec61850_adapter.adapter_id == "test-iec61850-adapter"
        assert iec61850_adapter.protocol_type == ProtocolType.IEC61850
        assert iec61850_adapter.is_connected is False
        assert iec61850_adapter.message_count == 0
        assert iec61850_adapter.error_count == 0

    def test_get_status(self, iec61850_adapter):
        """Test get_status method"""
        status = iec61850_adapter.get_status()
        assert "adapter_id" in status
        assert "protocol_type" in status
        assert "is_connected" in status
        assert "goose_queue_size" in status
        assert "sv_queue_size" in status

    def test_parse_message(self, iec61850_adapter):
        """Test message parsing"""
        test_data = b'\x01\x02\x03\x04'
        parsed = iec61850_adapter.parse_message(test_data)
        assert isinstance(parsed, dict)
        assert "raw_data" in parsed
        assert "length" in parsed

    def test_encode_message(self, iec61850_adapter):
        """Test message encoding"""
        message = {"voltage": 230, "current": 10}
        encoded = iec61850_adapter.encode_message(message)
        assert isinstance(encoded, bytes)

    def test_validate_message(self, iec61850_adapter):
        """Test message validation"""
        valid_data = b'\x01\x02\x03\x04'
        assert iec61850_adapter.validate_message(valid_data) is True
        
        invalid_data = b''
        assert iec61850_adapter.validate_message(invalid_data) is False

    def test_send_message_not_connected(self, iec61850_adapter):
        """Test sending message when not connected"""
        message = ProtocolMessage(
            protocol="iec61850",
            message_id="msg-1",
            source="device-1",
            destination="device-2",
            timestamp=time.time(),
            data={
                "message_type": "goose",
                "values": {"voltage": 230},
            },
        )
        result = iec61850_adapter.send_message(message)
        assert result is False
        assert iec61850_adapter.error_count > 0

    def test_receive_message_empty_queue(self, iec61850_adapter):
        """Test receiving message from empty queue"""
        message = iec61850_adapter.receive_message(timeout=0.1)
        assert message is None

    def test_disconnect_not_connected(self, iec61850_adapter):
        """Test disconnecting when not connected"""
        result = iec61850_adapter.disconnect()
        assert result is True
        assert iec61850_adapter.is_connected is False

    def test_send_goose_not_connected(self, iec61850_adapter):
        """Test sending GOOSE message when not connected"""
        result = iec61850_adapter.send_goose({"voltage": 230})
        assert result is False

    def test_send_sv_not_connected(self, iec61850_adapter):
        """Test sending SV message when not connected"""
        result = iec61850_adapter.send_sv({"current": 10})
        assert result is False

    def test_adapter_status_tracking(self, iec61850_adapter):
        """Test adapter status tracking"""
        initial_status = iec61850_adapter.get_status()
        assert initial_status["message_count"] == 0
        assert initial_status["error_count"] == 0
        
        # Simulate error
        iec61850_adapter._record_error("Test error")
        updated_status = iec61850_adapter.get_status()
        assert updated_status["error_count"] == 1
        assert updated_status["last_error"] == "Test error"

    def test_client_mode_config(self, iec61850_adapter):
        """Test client mode configuration"""
        config = {
            "mode": "client",
            "host": "localhost",
            "port": 102,
            "timeout": 5,
        }
        # Connection will fail without actual server, but config should be stored
        iec61850_adapter.connect(config)
        assert iec61850_adapter.config is not None
        assert iec61850_adapter.config.mode == "client"

    def test_server_mode_config(self, iec61850_adapter):
        """Test server mode configuration"""
        config = {
            "mode": "server",
            "port": 102,
            "timeout": 5,
        }
        # Connection will fail without actual setup, but config should be stored
        iec61850_adapter.connect(config)
        assert iec61850_adapter.config is not None
        assert iec61850_adapter.config.mode == "server"
