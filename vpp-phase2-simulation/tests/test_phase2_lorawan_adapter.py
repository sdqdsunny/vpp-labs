"""
Phase 2 Integration Tests - LoRaWAN Adapter

Tests for the LoRaWAN protocol adapter.
"""

import pytest
import time
from services.protocol_adapters.registry import ProtocolRegistry
from services.protocol_adapters.lorawan_adapter import LoRaWANAdapter, LoRaWANDevice
from services.protocol_adapters.base import ProtocolType, ProtocolMessage


class TestLoRaWANAdapter:
    """Test LoRaWAN Adapter"""
    
    def test_adapter_creation(self):
        """Test LoRaWAN adapter creation"""
        adapter = LoRaWANAdapter("test-lorawan")
        assert adapter.adapter_id == "test-lorawan"
        assert adapter.protocol_type == ProtocolType.LORAWAN
        assert not adapter.is_connected
    
    def test_adapter_status(self):
        """Test adapter status"""
        adapter = LoRaWANAdapter("test-lorawan")
        status = adapter.get_status()
        
        assert status['adapter_id'] == "test-lorawan"
        assert status['protocol_type'] == "lorawan"
        assert status['is_connected'] is False
        assert status['message_count'] == 0
        assert status['error_count'] == 0
    
    def test_connect(self):
        """Test connection to LoRaWAN network"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key',
            'region': 'EU868'
        }
        
        assert adapter.connect(config) is True
        assert adapter.is_connected is True
        assert adapter.config is not None
        assert adapter.config.app_id == 'test-app'
    
    def test_disconnect(self):
        """Test disconnection from LoRaWAN network"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key'
        }
        
        adapter.connect(config)
        assert adapter.disconnect() is True
        assert adapter.is_connected is False
    
    def test_register_device(self):
        """Test device registration"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key'
        }
        
        adapter.connect(config)
        
        device_config = {
            'dev_eui': '0011223344556677',
            'app_eui': '0011223344556677',
            'app_key': 'device-key'
        }
        
        assert adapter.register_device(device_config) is True
        assert '0011223344556677' in adapter.devices
    
    def test_unregister_device(self):
        """Test device unregistration"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key'
        }
        
        adapter.connect(config)
        
        device_config = {
            'dev_eui': '0011223344556677',
            'app_eui': '0011223344556677',
            'app_key': 'device-key'
        }
        
        adapter.register_device(device_config)
        assert adapter.unregister_device('0011223344556677') is True
        assert '0011223344556677' not in adapter.devices
    
    def test_send_uplink(self):
        """Test sending uplink message"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key'
        }
        
        adapter.connect(config)
        
        device_config = {
            'dev_eui': '0011223344556677',
            'app_eui': '0011223344556677',
            'app_key': 'device-key'
        }
        
        adapter.register_device(device_config)
        
        payload = b'\x01\x02\x03\x04'
        assert adapter.send_uplink('0011223344556677', payload, port=1) is True
        assert len(adapter.message_queue) == 1
        assert adapter.message_queue[0]['type'] == 'uplink'
    
    def test_send_downlink(self):
        """Test sending downlink message"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key'
        }
        
        adapter.connect(config)
        
        device_config = {
            'dev_eui': '0011223344556677',
            'app_eui': '0011223344556677',
            'app_key': 'device-key'
        }
        
        adapter.register_device(device_config)
        
        payload = b'\x05\x06\x07\x08'
        assert adapter.send_downlink('0011223344556677', payload, port=1) is True
        assert len(adapter.message_queue) == 1
        assert adapter.message_queue[0]['type'] == 'downlink'
    
    def test_get_device_info(self):
        """Test getting device information"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key'
        }
        
        adapter.connect(config)
        
        device_config = {
            'dev_eui': '0011223344556677',
            'app_eui': '0011223344556677',
            'app_key': 'device-key'
        }
        
        adapter.register_device(device_config)
        
        info = adapter.get_device_info('0011223344556677')
        assert info is not None
        assert info['dev_eui'] == '0011223344556677'
        assert info['fcnt_up'] == 0
        assert info['fcnt_down'] == 0
    
    def test_list_devices(self):
        """Test listing devices"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key'
        }
        
        adapter.connect(config)
        
        device_config1 = {
            'dev_eui': '0011223344556677',
            'app_eui': '0011223344556677',
            'app_key': 'device-key'
        }
        
        device_config2 = {
            'dev_eui': '8899aabbccddeeff',
            'app_eui': '8899aabbccddeeff',
            'app_key': 'device-key-2'
        }
        
        adapter.register_device(device_config1)
        adapter.register_device(device_config2)
        
        devices = adapter.list_devices()
        assert len(devices) == 2
    
    def test_message_callbacks(self):
        """Test message callbacks"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key'
        }
        
        adapter.connect(config)
        
        device_config = {
            'dev_eui': '0011223344556677',
            'app_eui': '0011223344556677',
            'app_key': 'device-key'
        }
        
        adapter.register_device(device_config)
        
        # Register callbacks
        uplink_called = []
        downlink_called = []
        
        def uplink_callback(msg):
            uplink_called.append(msg)
        
        def downlink_callback(msg):
            downlink_called.append(msg)
        
        adapter.register_uplink_callback(uplink_callback)
        adapter.register_downlink_callback(downlink_callback)
        
        # Send messages
        adapter.send_uplink('0011223344556677', b'\x01\x02')
        adapter.send_downlink('0011223344556677', b'\x03\x04')
        
        assert len(uplink_called) == 1
        assert len(downlink_called) == 1
    
    def test_message_queue(self):
        """Test message queue operations"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key'
        }
        
        adapter.connect(config)
        
        device_config = {
            'dev_eui': '0011223344556677',
            'app_eui': '0011223344556677',
            'app_key': 'device-key'
        }
        
        adapter.register_device(device_config)
        
        adapter.send_uplink('0011223344556677', b'\x01\x02')
        adapter.send_uplink('0011223344556677', b'\x03\x04')
        
        queue = adapter.get_message_queue()
        assert len(queue) == 2
        
        adapter.clear_message_queue()
        queue = adapter.get_message_queue()
        assert len(queue) == 0
    
    def test_send_message(self):
        """Test sending protocol message"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key'
        }
        
        adapter.connect(config)
        
        device_config = {
            'dev_eui': '0011223344556677',
            'app_eui': '0011223344556677',
            'app_key': 'device-key'
        }
        
        adapter.register_device(device_config)
        
        message = ProtocolMessage(
            protocol="lorawan",
            message_id="msg-1",
            source="test",
            destination="test-app",
            timestamp=time.time(),
            data={
                'dev_eui': '0011223344556677',
                'payload': b'\x01\x02\x03\x04',
                'direction': 'uplink',
                'port': 1
            }
        )
        
        assert adapter.send_message(message) is True
    
    def test_receive_message(self):
        """Test receiving message from queue"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key'
        }
        
        adapter.connect(config)
        
        device_config = {
            'dev_eui': '0011223344556677',
            'app_eui': '0011223344556677',
            'app_key': 'device-key'
        }
        
        adapter.register_device(device_config)
        
        adapter.send_uplink('0011223344556677', b'\x01\x02\x03\x04')
        
        msg = adapter.receive_message()
        assert msg is not None
        assert msg.data['type'] == 'uplink'
    
    def test_message_validation(self):
        """Test message validation"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        # Valid message (13+ bytes)
        valid_data = b'\x40\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04'
        assert adapter.validate_message(valid_data) is True
        
        # Invalid message (too short)
        invalid_data = b'\x40\x00\x00'
        assert adapter.validate_message(invalid_data) is False
    
    def test_message_parsing(self):
        """Test message parsing"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        data = b'\x40\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04'
        parsed = adapter.parse_message(data)
        
        assert parsed['mhdr'] == 0x40
        assert parsed['fcnt'] == 0
        assert parsed['payload'] == '01020304'
    
    def test_message_encoding(self):
        """Test message encoding"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        message = {
            'mhdr': 0x40,
            'dev_addr': '00000000',
            'fctrl': 0,
            'fcnt': 0,
            'payload': '01020304'
        }
        
        encoded = adapter.encode_message(message)
        assert len(encoded) >= 13
    
    def test_get_network_info(self):
        """Test getting network information"""
        adapter = LoRaWANAdapter("test-lorawan")
        
        config = {
            'gateway_url': 'http://localhost:8080',
            'app_id': 'test-app',
            'app_key': 'test-key',
            'region': 'EU868'
        }
        
        adapter.connect(config)
        
        info = adapter.get_network_info()
        assert info is not None
        assert info['app_id'] == 'test-app'
        assert info['region'] == 'EU868'
        assert info['connected'] is True


class TestLoRaWANDevice:
    """Test LoRaWAN Device"""
    
    def test_device_creation(self):
        """Test device creation"""
        device = LoRaWANDevice(
            dev_eui='0011223344556677',
            app_eui='0011223344556677',
            app_key='device-key'
        )
        
        assert device.dev_eui == '0011223344556677'
        assert device.app_eui == '0011223344556677'
        assert device.fcnt_up == 0
        assert device.fcnt_down == 0


class TestProtocolRegistry:
    """Test Protocol Registry with LoRaWAN"""
    
    def test_register_lorawan_adapter(self):
        """Test registering LoRaWAN adapter"""
        registry = ProtocolRegistry()
        registry.clear()
        
        registry.register("lorawan", LoRaWANAdapter)
        assert registry.is_protocol_supported("lorawan")
        assert "lorawan" in registry.list_protocols()
    
    def test_create_lorawan_adapter(self):
        """Test creating LoRaWAN adapter instance"""
        registry = ProtocolRegistry()
        registry.clear()
        
        registry.register("lorawan", LoRaWANAdapter)
        adapter = registry.create_adapter("lorawan", "lorawan-1")
        
        assert registry.get_adapter("lorawan-1") is not None


class TestProtocolTypes:
    """Test Protocol Type Enum"""
    
    def test_lorawan_protocol_type(self):
        """Test LoRaWAN protocol type"""
        assert hasattr(ProtocolType, 'LORAWAN')
        assert ProtocolType.LORAWAN.value == "lorawan"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
