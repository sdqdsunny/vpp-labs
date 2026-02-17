"""
Protocol Adapter Base Tests

Provides test framework for protocol adapter implementations.
"""

import pytest
from abc import ABC
from services.protocol_adapters.base import (
    ProtocolAdapter,
    ProtocolMessage,
    ProtocolType,
    ProtocolException,
)


class ProtocolAdapterTestBase(ABC):
    """
    Base test class for protocol adapters.
    
    Subclasses should implement:
    - adapter() fixture
    - get_test_config()
    - get_test_message()
    - get_test_data()
    """

    @pytest.fixture
    def adapter(self) -> ProtocolAdapter:
        """Create adapter instance for testing"""
        raise NotImplementedError("Subclass must implement adapter fixture")

    def get_test_config(self) -> dict:
        """Get test configuration"""
        raise NotImplementedError("Subclass must implement get_test_config")

    def get_test_message(self) -> ProtocolMessage:
        """Get test message"""
        raise NotImplementedError("Subclass must implement get_test_message")

    def get_test_data(self) -> bytes:
        """Get test data"""
        raise NotImplementedError("Subclass must implement get_test_data")

    def test_adapter_initialization(self, adapter):
        """Test adapter initialization"""
        assert adapter.adapter_id is not None
        assert adapter.protocol_type is not None
        assert adapter.is_connected is False
        assert adapter.message_count == 0
        assert adapter.error_count == 0

    def test_get_status(self, adapter):
        """Test get_status method"""
        status = adapter.get_status()
        assert "adapter_id" in status
        assert "protocol_type" in status
        assert "is_connected" in status
        assert "message_count" in status
        assert "error_count" in status

    def test_connect(self, adapter):
        """Test connection"""
        config = self.get_test_config()
        result = adapter.connect(config)
        assert isinstance(result, bool)
        if result:
            assert adapter.is_connected is True

    def test_disconnect(self, adapter):
        """Test disconnection"""
        config = self.get_test_config()
        adapter.connect(config)
        result = adapter.disconnect()
        assert isinstance(result, bool)
        if result:
            assert adapter.is_connected is False

    def test_parse_message(self, adapter):
        """Test message parsing"""
        test_data = self.get_test_data()
        parsed = adapter.parse_message(test_data)
        assert isinstance(parsed, dict)

    def test_encode_message(self, adapter):
        """Test message encoding"""
        message = self.get_test_message()
        encoded = adapter.encode_message(message.data)
        assert isinstance(encoded, bytes)

    def test_validate_message(self, adapter):
        """Test message validation"""
        test_data = self.get_test_data()
        result = adapter.validate_message(test_data)
        assert isinstance(result, bool)

    def test_send_message(self, adapter):
        """Test sending message"""
        config = self.get_test_config()
        if adapter.connect(config):
            message = self.get_test_message()
            result = adapter.send_message(message)
            assert isinstance(result, bool)
            adapter.disconnect()

    def test_receive_message(self, adapter):
        """Test receiving message"""
        config = self.get_test_config()
        if adapter.connect(config):
            message = adapter.receive_message(timeout=0.1)
            # Message can be None if no data available
            assert message is None or isinstance(message, ProtocolMessage)
            adapter.disconnect()

    def test_error_handling(self, adapter):
        """Test error handling"""
        # Try to send message without connecting
        message = self.get_test_message()
        result = adapter.send_message(message)
        # Should fail gracefully
        assert isinstance(result, bool)
