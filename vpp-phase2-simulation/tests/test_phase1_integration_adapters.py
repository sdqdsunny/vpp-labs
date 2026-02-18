"""
Phase 1 Integration Tests - OPC UA, CAN, Profinet Adapters

Tests for the newly integrated industrial protocol adapters.
"""

import pytest
from services.protocol_adapters.registry import ProtocolRegistry
from services.protocol_adapters.opcua_adapter import OPCUAAdapter
from services.protocol_adapters.can_adapter import CANAdapter
from services.protocol_adapters.profinet_adapter import ProfinetAdapter
from services.protocol_adapters.base import ProtocolType, ProtocolMessage


class TestOPCUAAdapter:
    """Test OPC UA Adapter"""
    
    def test_adapter_creation(self):
        """Test OPC UA adapter creation"""
        adapter = OPCUAAdapter("test-opcua")
        assert adapter.adapter_id == "test-opcua"
        assert adapter.protocol_type == ProtocolType.OPCUA
        assert not adapter.is_connected
    
    def test_adapter_status(self):
        """Test adapter status"""
        adapter = OPCUAAdapter("test-opcua")
        status = adapter.get_status()
        
        assert status['adapter_id'] == "test-opcua"
        assert status['protocol_type'] == "opcua"
        assert status['is_connected'] is False
        assert status['message_count'] == 0
        assert status['error_count'] == 0


class TestCANAdapter:
    """Test CAN Adapter"""
    
    def test_adapter_creation(self):
        """Test CAN adapter creation"""
        adapter = CANAdapter("test-can")
        assert adapter.adapter_id == "test-can"
        assert adapter.protocol_type == ProtocolType.CAN
        assert not adapter.is_connected
    
    def test_adapter_status(self):
        """Test adapter status"""
        adapter = CANAdapter("test-can")
        status = adapter.get_status()
        
        assert status['adapter_id'] == "test-can"
        assert status['protocol_type'] == "can"
        assert status['is_connected'] is False
    
    def test_message_validation(self):
        """Test CAN message validation"""
        adapter = CANAdapter("test-can")
        
        # Valid CAN message
        valid_data = b'\x12\x34\x08\x01\x02\x03\x04\x05\x06\x07\x08'
        assert adapter.validate_message(valid_data) is True
        
        # Invalid CAN message (too short)
        invalid_data = b'\x12'
        assert adapter.validate_message(invalid_data) is False
    
    def test_message_parsing(self):
        """Test CAN message parsing"""
        adapter = CANAdapter("test-can")
        
        data = b'\x12\x34\x08\x01\x02\x03\x04\x05\x06\x07\x08'
        parsed = adapter.parse_message(data)
        
        assert parsed['can_id'] == 0x1234
        assert parsed['dlc'] == 0x08
        assert parsed['payload'] == b'\x01\x02\x03\x04\x05\x06\x07\x08'
    
    def test_message_encoding(self):
        """Test CAN message encoding"""
        adapter = CANAdapter("test-can")
        
        message = {
            'can_id': 0x123,
            'dlc': 8,
            'payload': b'\x01\x02\x03\x04\x05\x06\x07\x08'
        }
        
        encoded = adapter.encode_message(message)
        assert len(encoded) >= 2


class TestProfinetAdapter:
    """Test Profinet Adapter"""
    
    def test_adapter_creation(self):
        """Test Profinet adapter creation"""
        adapter = ProfinetAdapter("test-profinet")
        assert adapter.adapter_id == "test-profinet"
        assert adapter.protocol_type == ProtocolType.PROFINET
        assert not adapter.is_connected
    
    def test_adapter_status(self):
        """Test adapter status"""
        adapter = ProfinetAdapter("test-profinet")
        status = adapter.get_status()
        
        assert status['adapter_id'] == "test-profinet"
        assert status['protocol_type'] == "profinet"
        assert status['is_connected'] is False


class TestProtocolRegistry:
    """Test Protocol Registry with new adapters"""
    
    def test_register_opcua_adapter(self):
        """Test registering OPC UA adapter"""
        registry = ProtocolRegistry()
        registry.clear()
        
        registry.register("opcua", OPCUAAdapter)
        assert registry.is_protocol_supported("opcua")
        assert "opcua" in registry.list_protocols()
    
    def test_register_can_adapter(self):
        """Test registering CAN adapter"""
        registry = ProtocolRegistry()
        registry.clear()
        
        registry.register("can", CANAdapter)
        assert registry.is_protocol_supported("can")
        assert "can" in registry.list_protocols()
    
    def test_register_profinet_adapter(self):
        """Test registering Profinet adapter"""
        registry = ProtocolRegistry()
        registry.clear()
        
        registry.register("profinet", ProfinetAdapter)
        assert registry.is_protocol_supported("profinet")
        assert "profinet" in registry.list_protocols()
    
    def test_create_adapter_instances(self):
        """Test creating adapter instances"""
        registry = ProtocolRegistry()
        registry.clear()
        
        registry.register("opcua", OPCUAAdapter)
        registry.register("can", CANAdapter)
        registry.register("profinet", ProfinetAdapter)
        
        opcua_adapter = registry.create_adapter("opcua", "opcua-1")
        can_adapter = registry.create_adapter("can", "can-1")
        profinet_adapter = registry.create_adapter("profinet", "profinet-1")
        
        assert registry.get_adapter("opcua-1") is not None
        assert registry.get_adapter("can-1") is not None
        assert registry.get_adapter("profinet-1") is not None
    
    def test_list_all_adapters(self):
        """Test listing all adapters"""
        registry = ProtocolRegistry()
        registry.clear()
        
        registry.register("opcua", OPCUAAdapter)
        registry.register("can", CANAdapter)
        registry.register("profinet", ProfinetAdapter)
        
        protocols = registry.list_protocols()
        assert len(protocols) == 3
        assert "opcua" in protocols
        assert "can" in protocols
        assert "profinet" in protocols


class TestProtocolTypes:
    """Test Protocol Type Enum"""
    
    def test_protocol_types_exist(self):
        """Test that new protocol types are defined"""
        assert hasattr(ProtocolType, 'OPCUA')
        assert hasattr(ProtocolType, 'CAN')
        assert hasattr(ProtocolType, 'PROFINET')
    
    def test_protocol_type_values(self):
        """Test protocol type values"""
        assert ProtocolType.OPCUA.value == "opcua"
        assert ProtocolType.CAN.value == "can"
        assert ProtocolType.PROFINET.value == "profinet"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
