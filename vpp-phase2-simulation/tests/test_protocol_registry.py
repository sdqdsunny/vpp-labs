"""
Protocol Registry Tests
"""

import pytest
from services.protocol_adapters.base import ProtocolAdapter, ProtocolType
from services.protocol_adapters.registry import ProtocolRegistry


class MockAdapter(ProtocolAdapter):
    """Mock adapter for testing"""

    def __init__(self, adapter_id: str):
        super().__init__(adapter_id, ProtocolType.MQTT)

    def connect(self, config):
        self.is_connected = True
        return True

    def disconnect(self):
        self.is_connected = False
        return True

    def send_message(self, message):
        self._record_message()
        return True

    def receive_message(self, timeout=1.0):
        return None

    def parse_message(self, data):
        return {}

    def encode_message(self, message):
        return b""

    def validate_message(self, data):
        return True


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry before each test"""
    ProtocolRegistry.clear()
    yield
    ProtocolRegistry.clear()


class TestProtocolRegistry:
    """Test protocol registry"""

    def test_register_adapter(self):
        """Test registering adapter"""
        ProtocolRegistry.register("mock", MockAdapter)
        assert ProtocolRegistry.is_protocol_supported("mock")

    def test_register_duplicate(self):
        """Test registering duplicate adapter"""
        ProtocolRegistry.register("mock", MockAdapter)
        with pytest.raises(ValueError):
            ProtocolRegistry.register("mock", MockAdapter)

    def test_unregister_adapter(self):
        """Test unregistering adapter"""
        ProtocolRegistry.register("mock", MockAdapter)
        ProtocolRegistry.unregister("mock")
        assert not ProtocolRegistry.is_protocol_supported("mock")

    def test_get_adapter_class(self):
        """Test getting adapter class"""
        ProtocolRegistry.register("mock", MockAdapter)
        adapter_class = ProtocolRegistry.get_adapter_class("mock")
        assert adapter_class == MockAdapter

    def test_get_adapter_class_not_found(self):
        """Test getting non-existent adapter class"""
        with pytest.raises(ValueError):
            ProtocolRegistry.get_adapter_class("nonexistent")

    def test_create_adapter(self):
        """Test creating adapter instance"""
        ProtocolRegistry.register("mock", MockAdapter)
        adapter = ProtocolRegistry.create_adapter("mock", "test-adapter-1")
        assert adapter is not None
        assert adapter.adapter_id == "test-adapter-1"

    def test_get_adapter(self):
        """Test getting adapter instance"""
        ProtocolRegistry.register("mock", MockAdapter)
        adapter = ProtocolRegistry.create_adapter("mock", "test-adapter-1")
        retrieved = ProtocolRegistry.get_adapter("test-adapter-1")
        assert retrieved == adapter

    def test_get_adapter_not_found(self):
        """Test getting non-existent adapter"""
        result = ProtocolRegistry.get_adapter("nonexistent")
        assert result is None

    def test_list_protocols(self):
        """Test listing protocols"""
        ProtocolRegistry.register("mock1", MockAdapter)
        ProtocolRegistry.register("mock2", MockAdapter)
        protocols = ProtocolRegistry.list_protocols()
        assert "mock1" in protocols
        assert "mock2" in protocols

    def test_list_adapters(self):
        """Test listing adapter instances"""
        ProtocolRegistry.register("mock", MockAdapter)
        ProtocolRegistry.create_adapter("mock", "adapter-1")
        ProtocolRegistry.create_adapter("mock", "adapter-2")
        adapters = ProtocolRegistry.list_adapters()
        assert "adapter-1" in adapters
        assert "adapter-2" in adapters

    def test_remove_adapter(self):
        """Test removing adapter instance"""
        ProtocolRegistry.register("mock", MockAdapter)
        adapter = ProtocolRegistry.create_adapter("mock", "test-adapter")
        ProtocolRegistry.remove_adapter("test-adapter")
        assert ProtocolRegistry.get_adapter("test-adapter") is None

    def test_get_status(self):
        """Test getting registry status"""
        ProtocolRegistry.register("mock1", MockAdapter)
        ProtocolRegistry.register("mock2", MockAdapter)
        ProtocolRegistry.create_adapter("mock1", "adapter-1")
        
        status = ProtocolRegistry.get_status()
        assert "registered_protocols" in status
        assert "active_adapters" in status
        assert status["total_protocols"] == 2
        assert status["total_instances"] == 1

    def test_is_protocol_supported(self):
        """Test checking protocol support"""
        ProtocolRegistry.register("mock", MockAdapter)
        assert ProtocolRegistry.is_protocol_supported("mock")
        assert not ProtocolRegistry.is_protocol_supported("nonexistent")
