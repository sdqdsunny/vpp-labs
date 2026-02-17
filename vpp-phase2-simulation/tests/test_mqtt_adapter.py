"""
MQTT Adapter Tests
"""

import pytest
import time
from services.protocol_adapters.mqtt_adapter import MQTTAdapter
from services.protocol_adapters.base import ProtocolMessage, ProtocolType


@pytest.fixture
def mqtt_adapter():
    """Create MQTT adapter instance"""
    return MQTTAdapter("test-mqtt-adapter")


class TestMQTTAdapter:
    """Test MQTT adapter"""

    def test_adapter_initialization(self, mqtt_adapter):
        """Test adapter initialization"""
        assert mqtt_adapter.adapter_id == "test-mqtt-adapter"
        assert mqtt_adapter.protocol_type == ProtocolType.MQTT
        assert mqtt_adapter.is_connected is False
        assert mqtt_adapter.message_count == 0
        assert mqtt_adapter.error_count == 0

    def test_get_status(self, mqtt_adapter):
        """Test get_status method"""
        status = mqtt_adapter.get_status()
        assert "adapter_id" in status
        assert "protocol_type" in status
        assert "is_connected" in status
        assert "subscribed_topics" in status
        assert "queued_messages" in status

    def test_parse_message(self, mqtt_adapter):
        """Test message parsing"""
        test_data = b'{"voltage": 230, "current": 10}'
        parsed = mqtt_adapter.parse_message(test_data)
        assert isinstance(parsed, dict)
        assert parsed.get("voltage") == 230
        assert parsed.get("current") == 10

    def test_parse_invalid_message(self, mqtt_adapter):
        """Test parsing invalid message"""
        test_data = b'invalid json'
        parsed = mqtt_adapter.parse_message(test_data)
        assert isinstance(parsed, dict)
        assert len(parsed) == 0

    def test_encode_message(self, mqtt_adapter):
        """Test message encoding"""
        message = {"voltage": 230, "current": 10}
        encoded = mqtt_adapter.encode_message(message)
        assert isinstance(encoded, bytes)
        assert b"voltage" in encoded
        assert b"230" in encoded

    def test_validate_message(self, mqtt_adapter):
        """Test message validation"""
        valid_data = b'{"voltage": 230}'
        assert mqtt_adapter.validate_message(valid_data) is True
        
        invalid_data = b'invalid json'
        assert mqtt_adapter.validate_message(invalid_data) is False

    def test_send_message_not_connected(self, mqtt_adapter):
        """Test sending message when not connected"""
        message = ProtocolMessage(
            protocol="mqtt",
            message_id="msg-1",
            source="device-1",
            destination="device-2",
            timestamp=time.time(),
            data={"value": 100},
        )
        result = mqtt_adapter.send_message(message)
        assert result is False
        assert mqtt_adapter.error_count > 0

    def test_receive_message_empty_queue(self, mqtt_adapter):
        """Test receiving message from empty queue"""
        message = mqtt_adapter.receive_message(timeout=0.1)
        assert message is None

    def test_subscribe_not_connected(self, mqtt_adapter):
        """Test subscribing when not connected"""
        result = mqtt_adapter.subscribe("vpp/test")
        assert result is False

    def test_unsubscribe_not_connected(self, mqtt_adapter):
        """Test unsubscribing when not connected"""
        result = mqtt_adapter.unsubscribe("vpp/test")
        assert result is False

    def test_disconnect_not_connected(self, mqtt_adapter):
        """Test disconnecting when not connected"""
        result = mqtt_adapter.disconnect()
        assert result is True
        assert mqtt_adapter.is_connected is False

    def test_message_encoding_decoding(self, mqtt_adapter):
        """Test message encoding and decoding"""
        original = {"voltage": 230, "current": 10, "frequency": 50}
        encoded = mqtt_adapter.encode_message(original)
        decoded = mqtt_adapter.parse_message(encoded)
        assert decoded == original

    def test_adapter_status_tracking(self, mqtt_adapter):
        """Test adapter status tracking"""
        initial_status = mqtt_adapter.get_status()
        assert initial_status["message_count"] == 0
        assert initial_status["error_count"] == 0
        
        # Simulate error
        mqtt_adapter._record_error("Test error")
        updated_status = mqtt_adapter.get_status()
        assert updated_status["error_count"] == 1
        assert updated_status["last_error"] == "Test error"
