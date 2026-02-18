"""
Phase 3 Integration Tests - XMPP, RS-232, RS-485, DL/T Adapters

Tests for the Phase 3 protocol adapters.
"""

import pytest
import time
from services.protocol_adapters.registry import ProtocolRegistry
from services.protocol_adapters.xmpp_adapter import XMPPAdapter
from services.protocol_adapters.rs232_adapter import RS232Adapter
from services.protocol_adapters.rs485_adapter import RS485Adapter
from services.protocol_adapters.dlt_adapter import DLTAdapter
from services.protocol_adapters.base import ProtocolType, ProtocolMessage


class TestXMPPAdapter:
    """Test XMPP Adapter"""
    
    def test_adapter_creation(self):
        """Test XMPP adapter creation"""
        adapter = XMPPAdapter("test-xmpp")
        assert adapter.adapter_id == "test-xmpp"
        assert adapter.protocol_type == ProtocolType.XMPP
        assert not adapter.is_connected
    
    def test_connect(self):
        """Test XMPP connection"""
        adapter = XMPPAdapter("test-xmpp")
        config = {
            'jid': 'user@localhost',
            'password': 'password',
            'server': 'localhost',
            'port': 5222
        }
        assert adapter.connect(config) is True
        assert adapter.is_connected is True
    
    def test_add_contact(self):
        """Test adding contact"""
        adapter = XMPPAdapter("test-xmpp")
        adapter.connect({'jid': 'user@localhost', 'password': 'password'})
        
        assert adapter.add_contact('contact@localhost') is True
        assert 'contact@localhost' in adapter.contacts
    
    def test_send_message(self):
        """Test sending message"""
        adapter = XMPPAdapter("test-xmpp")
        adapter.connect({'jid': 'user@localhost', 'password': 'password'})
        adapter.add_contact('contact@localhost')
        
        message = ProtocolMessage(
            protocol="xmpp",
            message_id="msg-1",
            source="user@localhost",
            destination="contact@localhost",
            timestamp=time.time(),
            data={
                'recipient': 'contact@localhost',
                'body': 'Hello',
                'type': 'chat'
            }
        )
        
        assert adapter.send_message(message) is True
        assert len(adapter.message_queue) == 1


class TestRS232Adapter:
    """Test RS-232 Adapter"""
    
    def test_adapter_creation(self):
        """Test RS-232 adapter creation"""
        adapter = RS232Adapter("test-rs232")
        assert adapter.adapter_id == "test-rs232"
        assert adapter.protocol_type == ProtocolType.RS232
        assert not adapter.is_connected
    
    def test_connect(self):
        """Test RS-232 connection"""
        adapter = RS232Adapter("test-rs232")
        config = {
            'port': 'COM1',
            'baudrate': 9600,
            'bytesize': 8,
            'stopbits': 1,
            'parity': 'N'
        }
        assert adapter.connect(config) is True
        assert adapter.is_connected is True
    
    def test_send_data(self):
        """Test sending data"""
        adapter = RS232Adapter("test-rs232")
        adapter.connect({'port': 'COM1', 'baudrate': 9600})
        
        data = b'\x01\x02\x03\x04'
        assert adapter.send_data(data) is True
    
    def test_port_info(self):
        """Test getting port info"""
        adapter = RS232Adapter("test-rs232")
        adapter.connect({'port': 'COM1', 'baudrate': 9600})
        
        info = adapter.get_port_info()
        assert info is not None
        assert info['port'] == 'COM1'
        assert info['baudrate'] == 9600


class TestRS485Adapter:
    """Test RS-485 Adapter"""
    
    def test_adapter_creation(self):
        """Test RS-485 adapter creation"""
        adapter = RS485Adapter("test-rs485")
        assert adapter.adapter_id == "test-rs485"
        assert adapter.protocol_type == ProtocolType.RS485
        assert not adapter.is_connected
    
    def test_connect(self):
        """Test RS-485 connection"""
        adapter = RS485Adapter("test-rs485")
        config = {
            'port': 'COM1',
            'baudrate': 9600,
            'parity': 'E'
        }
        assert adapter.connect(config) is True
        assert adapter.is_connected is True
    
    def test_add_device(self):
        """Test adding device"""
        adapter = RS485Adapter("test-rs485")
        adapter.connect({'port': 'COM1', 'baudrate': 9600})
        
        assert adapter.add_device(1) is True
        assert 1 in adapter.devices
    
    def test_send_data(self):
        """Test sending data"""
        adapter = RS485Adapter("test-rs485")
        adapter.connect({'port': 'COM1', 'baudrate': 9600})
        adapter.add_device(1)
        
        data = b'\x03\x04\x05\x06'
        assert adapter.send_data(1, data) is True
        assert len(adapter.message_queue) == 1
    
    def test_list_devices(self):
        """Test listing devices"""
        adapter = RS485Adapter("test-rs485")
        adapter.connect({'port': 'COM1', 'baudrate': 9600})
        
        adapter.add_device(1)
        adapter.add_device(2)
        adapter.add_device(3)
        
        devices = adapter.list_devices()
        assert len(devices) == 3


class TestDLTAdapter:
    """Test DL/T Adapter"""
    
    def test_adapter_creation(self):
        """Test DL/T adapter creation"""
        adapter = DLTAdapter("test-dlt")
        assert adapter.adapter_id == "test-dlt"
        assert adapter.protocol_type == ProtocolType.DLT634
        assert not adapter.is_connected
    
    def test_connect(self):
        """Test DL/T connection"""
        adapter = DLTAdapter("test-dlt")
        config = {
            'protocol_version': '645',
            'device_id': '001',
            'baud_rate': 1200
        }
        assert adapter.connect(config) is True
        assert adapter.is_connected is True
    
    def test_register_device(self):
        """Test registering device"""
        adapter = DLTAdapter("test-dlt")
        adapter.connect({'protocol_version': '645', 'device_id': '001'})
        
        assert adapter.register_device('001001') is True
        assert '001001' in adapter.devices
    
    def test_write_meter_data(self):
        """Test writing meter data"""
        adapter = DLTAdapter("test-dlt")
        adapter.connect({'protocol_version': '645', 'device_id': '001'})
        adapter.register_device('001001')
        
        assert adapter.write_meter_data('001001', '00000000', 1234.56) is True
        assert len(adapter.message_queue) == 1
    
    def test_read_meter_data(self):
        """Test reading meter data"""
        adapter = DLTAdapter("test-dlt")
        adapter.connect({'protocol_version': '645', 'device_id': '001'})
        adapter.register_device('001001')
        
        adapter.write_meter_data('001001', '00000000', 1234.56)
        value = adapter.read_meter_data('001001', '00000000')
        
        assert value == 1234.56
    
    def test_list_devices(self):
        """Test listing devices"""
        adapter = DLTAdapter("test-dlt")
        adapter.connect({'protocol_version': '645', 'device_id': '001'})
        
        adapter.register_device('001001')
        adapter.register_device('001002')
        
        devices = adapter.list_devices()
        assert len(devices) == 2


class TestProtocolRegistry:
    """Test Protocol Registry with Phase 3 adapters"""
    
    def test_register_all_phase3_adapters(self):
        """Test registering all Phase 3 adapters"""
        registry = ProtocolRegistry()
        registry.clear()
        
        registry.register("xmpp", XMPPAdapter)
        registry.register("rs232", RS232Adapter)
        registry.register("rs485", RS485Adapter)
        registry.register("dlt", DLTAdapter)
        
        protocols = registry.list_protocols()
        assert len(protocols) == 4
        assert "xmpp" in protocols
        assert "rs232" in protocols
        assert "rs485" in protocols
        assert "dlt" in protocols


class TestProtocolTypes:
    """Test Protocol Type Enum"""
    
    def test_phase3_protocol_types(self):
        """Test Phase 3 protocol types"""
        assert hasattr(ProtocolType, 'XMPP')
        assert hasattr(ProtocolType, 'RS232')
        assert hasattr(ProtocolType, 'RS485')
        assert hasattr(ProtocolType, 'DLT634')
        assert hasattr(ProtocolType, 'DLT645')
        assert hasattr(ProtocolType, 'DLT698')
        assert hasattr(ProtocolType, 'DLT476')
    
    def test_protocol_type_values(self):
        """Test protocol type values"""
        assert ProtocolType.XMPP.value == "xmpp"
        assert ProtocolType.RS232.value == "rs232"
        assert ProtocolType.RS485.value == "rs485"
        assert ProtocolType.DLT634.value == "dlt634"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
