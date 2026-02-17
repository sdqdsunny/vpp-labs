"""
Modbus Adapter Tests
"""

import pytest
import time
from services.protocol_adapters.modbus_adapter import ModbusAdapter
from services.protocol_adapters.base import ProtocolMessage, ProtocolType


@pytest.fixture
def modbus_adapter():
    """Create Modbus adapter instance"""
    return ModbusAdapter("test-modbus-adapter")


class TestModbusAdapter:
    """Test Modbus adapter"""

    def test_adapter_initialization(self, modbus_adapter):
        """Test adapter initialization"""
        assert modbus_adapter.adapter_id == "test-modbus-adapter"
        assert modbus_adapter.protocol_type == ProtocolType.MODBUS
        assert modbus_adapter.is_connected is False
        assert modbus_adapter.message_count == 0
        assert modbus_adapter.error_count == 0

    def test_get_status(self, modbus_adapter):
        """Test get_status method"""
        status = modbus_adapter.get_status()
        assert "adapter_id" in status
        assert "protocol_type" in status
        assert "is_connected" in status
        assert "message_count" in status

    def test_parse_message(self, modbus_adapter):
        """Test message parsing"""
        test_data = b'\x01\x03\x00\x00\x00\x02'
        parsed = modbus_adapter.parse_message(test_data)
        assert isinstance(parsed, dict)
        assert "raw_data" in parsed
        assert "length" in parsed

    def test_encode_message(self, modbus_adapter):
        """Test message encoding"""
        message = {"operation": "read_registers", "address": 0, "count": 10}
        encoded = modbus_adapter.encode_message(message)
        assert isinstance(encoded, bytes)

    def test_validate_message(self, modbus_adapter):
        """Test message validation"""
        valid_data = b'\x01\x03\x00\x00\x00\x02'
        assert modbus_adapter.validate_message(valid_data) is True
        
        invalid_data = b''
        assert modbus_adapter.validate_message(invalid_data) is False

    def test_send_message_not_connected(self, modbus_adapter):
        """Test sending message when not connected"""
        message = ProtocolMessage(
            protocol="modbus",
            message_id="msg-1",
            source="device-1",
            destination="device-2",
            timestamp=time.time(),
            data={
                "operation": "write_registers",
                "address": 0,
                "values": [100, 200],
            },
        )
        result = modbus_adapter.send_message(message)
        assert result is False
        assert modbus_adapter.error_count > 0

    def test_receive_message_not_connected(self, modbus_adapter):
        """Test receiving message when not connected"""
        message = modbus_adapter.receive_message(timeout=0.1)
        assert message is None

    def test_read_registers_not_connected(self, modbus_adapter):
        """Test reading registers when not connected"""
        result = modbus_adapter.read_registers(0, 10)
        assert result is None

    def test_write_registers_not_connected(self, modbus_adapter):
        """Test writing registers when not connected"""
        result = modbus_adapter.write_registers(0, [100, 200])
        assert result is False

    def test_read_coils_not_connected(self, modbus_adapter):
        """Test reading coils when not connected"""
        result = modbus_adapter.read_coils(0, 10)
        assert result is None

    def test_write_coils_not_connected(self, modbus_adapter):
        """Test writing coils when not connected"""
        result = modbus_adapter.write_coils(0, [True, False])
        assert result is False

    def test_disconnect_not_connected(self, modbus_adapter):
        """Test disconnecting when not connected"""
        result = modbus_adapter.disconnect()
        assert result is True
        assert modbus_adapter.is_connected is False

    def test_adapter_status_tracking(self, modbus_adapter):
        """Test adapter status tracking"""
        initial_status = modbus_adapter.get_status()
        assert initial_status["message_count"] == 0
        assert initial_status["error_count"] == 0
        
        # Simulate error
        modbus_adapter._record_error("Test error")
        updated_status = modbus_adapter.get_status()
        assert updated_status["error_count"] == 1
        assert updated_status["last_error"] == "Test error"

    def test_tcp_mode_config(self, modbus_adapter):
        """Test TCP mode configuration"""
        config = {
            "mode": "tcp",
            "host": "localhost",
            "port": 502,
            "timeout": 5,
        }
        # Connection will fail without actual server, but config should be stored
        modbus_adapter.connect(config)
        assert modbus_adapter.config == config
        assert modbus_adapter.mode == "tcp"

    def test_rtu_mode_config(self, modbus_adapter):
        """Test RTU mode configuration"""
        config = {
            "mode": "rtu",
            "port_name": "/dev/ttyUSB0",
            "baudrate": 9600,
            "timeout": 5,
        }
        # Connection will fail without actual serial port, but config should be stored
        modbus_adapter.connect(config)
        assert modbus_adapter.config == config
        assert modbus_adapter.mode == "rtu"
