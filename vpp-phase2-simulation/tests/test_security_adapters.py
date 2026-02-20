"""
Unit Tests for Security Testing Adapters

This module contains comprehensive unit tests for all security testing adapters.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.security_adapters import (
    TestAdapter, TestRequest, TestResult,
    DNP3Adapter, OPCUAAdapter, BoofuzzAdapter, ModbusAdapter, CANAdapter
)


class TestTestRequest:
    """Tests for TestRequest data class"""

    def test_create_basic_request(self):
        """Test creating a basic test request"""
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="localhost",
            target_port=502
        )
        
        assert request.test_type == "connection"
        assert request.adapter_name == "modbus"
        assert request.target_host == "localhost"
        assert request.target_port == 502
        assert request.timeout == 30

    def test_create_request_with_custom_timeout(self):
        """Test creating request with custom timeout"""
        request = TestRequest(
            test_type="connection",
            adapter_name="dnp3",
            target_host="10.0.8.2",
            target_port=20000,
            timeout=60
        )
        
        assert request.timeout == 60

    def test_create_request_with_url(self):
        """Test creating request with URL (for OPC UA)"""
        request = TestRequest(
            test_type="connection",
            adapter_name="opcua",
            target_host="10.0.8.2",
            target_port=4840,
            target_url="opc.tcp://10.0.8.2:4840"
        )
        
        assert request.target_url == "opc.tcp://10.0.8.2:4840"

    def test_create_request_with_parameters(self):
        """Test creating request with custom parameters"""
        params = {"interface": "vcan0", "bitrate": 500000}
        request = TestRequest(
            test_type="connection",
            adapter_name="can",
            target_host="localhost",
            target_port=0,
            parameters=params
        )
        
        assert request.parameters == params


class TestTestResult:
    """Tests for TestResult data class"""

    def test_create_result(self):
        """Test creating a test result"""
        result = TestResult(
            test_type="connection",
            adapter_name="modbus",
            target_host="localhost",
            target_port=502
        )
        
        assert result.test_type == "connection"
        assert result.adapter_name == "modbus"
        assert result.status == "pending"
        assert result.test_id is not None

    def test_mark_success(self):
        """Test marking result as successful"""
        result = TestResult(
            test_type="connection",
            adapter_name="modbus",
            target_host="localhost",
            target_port=502
        )
        
        result.mark_success()
        
        assert result.status == "success"
        assert result.end_time is not None
        assert result.duration > 0

    def test_mark_failed(self):
        """Test marking result as failed"""
        result = TestResult(
            test_type="connection",
            adapter_name="modbus",
            target_host="localhost",
            target_port=502
        )
        
        result.mark_failed("Connection refused")
        
        assert result.status == "failed"
        assert result.error_message == "Connection refused"
        assert result.end_time is not None

    def test_mark_error(self):
        """Test marking result as error"""
        result = TestResult(
            test_type="connection",
            adapter_name="modbus",
            target_host="localhost",
            target_port=502
        )
        
        result.mark_error("Timeout occurred")
        
        assert result.status == "error"
        assert result.error_message == "Timeout occurred"
        assert result.end_time is not None

    def test_result_to_dict(self):
        """Test converting result to dictionary"""
        result = TestResult(
            test_type="connection",
            adapter_name="modbus",
            target_host="localhost",
            target_port=502
        )
        result.mark_success()
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["test_type"] == "connection"
        assert result_dict["adapter_name"] == "modbus"
        assert result_dict["status"] == "success"
        assert isinstance(result_dict["start_time"], str)
        assert isinstance(result_dict["end_time"], str)


class TestDNP3Adapter:
    """Tests for DNP3Adapter"""

    def test_adapter_initialization(self):
        """Test DNP3 adapter initialization"""
        adapter = DNP3Adapter()
        
        assert adapter.name == "dnp3"
        assert isinstance(adapter.available, bool)

    def test_get_supported_tests(self):
        """Test getting supported test types"""
        adapter = DNP3Adapter()
        supported = adapter.get_supported_tests()
        
        assert isinstance(supported, list)
        assert "connection" in supported
        assert "scan" in supported
        assert "read_points" in supported
        assert "write_points" in supported
        assert "authentication" in supported

    def test_connection_test_success(self):
        """Test successful connection test"""
        adapter = DNP3Adapter()
        request = TestRequest(
            test_type="connection",
            adapter_name="dnp3",
            target_host="localhost",
            target_port=20000,
            timeout=5
        )
        
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value = mock_instance
            
            result = adapter.execute_test(request)
            
            assert result.test_type == "connection"
            assert result.adapter_name == "dnp3"
            assert result.target_host == "localhost"
            assert result.target_port == 20000

    def test_scan_test(self):
        """Test DNP3 scan test"""
        adapter = DNP3Adapter()
        request = TestRequest(
            test_type="scan",
            adapter_name="dnp3",
            target_host="localhost",
            target_port=20000
        )
        
        result = adapter.execute_test(request)
        
        assert result.test_type == "scan"
        assert result.adapter_name == "dnp3"
        # If adapter is available, check for scan_status
        if adapter.is_available():
            assert "scan_status" in result.result_data
        else:
            # If not available, should return error
            assert result.status == "error"

    def test_unsupported_test_type(self):
        """Test unsupported test type"""
        adapter = DNP3Adapter()
        request = TestRequest(
            test_type="invalid_test",
            adapter_name="dnp3",
            target_host="localhost",
            target_port=20000
        )
        
        result = adapter.execute_test(request)
        
        assert result.status == "error"
        # Error could be either "Unsupported test type" or "not installed"
        assert "Unsupported test type" in result.error_message or "not installed" in result.error_message


class TestOPCUAAdapter:
    """Tests for OPCUAAdapter"""

    def test_adapter_initialization(self):
        """Test OPC UA adapter initialization"""
        adapter = OPCUAAdapter()
        
        assert adapter.name == "opcua"
        assert isinstance(adapter.available, bool)

    def test_get_supported_tests(self):
        """Test getting supported test types"""
        adapter = OPCUAAdapter()
        supported = adapter.get_supported_tests()
        
        assert isinstance(supported, list)
        assert "connection" in supported
        assert "browse" in supported
        assert "read_attributes" in supported
        assert "write_attributes" in supported
        assert "security_scan" in supported

    def test_connection_test_with_url(self):
        """Test OPC UA connection test with URL"""
        adapter = OPCUAAdapter()
        request = TestRequest(
            test_type="connection",
            adapter_name="opcua",
            target_host="localhost",
            target_port=4840,
            target_url="opc.tcp://localhost:4840",
            timeout=5
        )
        
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value = mock_instance
            
            result = adapter.execute_test(request)
            
            assert result.test_type == "connection"
            assert result.adapter_name == "opcua"
            assert result.target_url == "opc.tcp://localhost:4840"

    def test_browse_test(self):
        """Test OPC UA browse test"""
        adapter = OPCUAAdapter()
        request = TestRequest(
            test_type="browse",
            adapter_name="opcua",
            target_host="localhost",
            target_port=4840
        )
        
        result = adapter.execute_test(request)
        
        assert result.test_type == "browse"
        assert result.adapter_name == "opcua"
        # If adapter is available, check for browse_status
        if adapter.is_available():
            assert "browse_status" in result.result_data
        else:
            # If not available, should return error
            assert result.status == "error"


class TestBoofuzzAdapter:
    """Tests for BoofuzzAdapter"""

    def test_adapter_initialization(self):
        """Test Boofuzz adapter initialization"""
        adapter = BoofuzzAdapter()
        
        assert adapter.name == "boofuzz"
        assert isinstance(adapter.available, bool)

    def test_get_supported_tests(self):
        """Test getting supported test types"""
        adapter = BoofuzzAdapter()
        supported = adapter.get_supported_tests()
        
        assert isinstance(supported, list)
        assert "modbus_fuzz" in supported
        assert "dnp3_fuzz" in supported
        assert "opcua_fuzz" in supported
        assert "generic_fuzz" in supported

    def test_modbus_fuzz_test(self):
        """Test Modbus fuzzing"""
        adapter = BoofuzzAdapter()
        request = TestRequest(
            test_type="modbus_fuzz",
            adapter_name="boofuzz",
            target_host="localhost",
            target_port=502,
            timeout=30
        )
        
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value = mock_instance
            
            result = adapter.execute_test(request)
            
            assert result.test_type == "modbus_fuzz"
            assert result.adapter_name == "boofuzz"
            # If adapter is available, check for fuzz_status
            if adapter.is_available():
                assert "fuzz_status" in result.result_data
            else:
                # If not available, should return error
                assert result.status == "error"

    def test_dnp3_fuzz_test(self):
        """Test DNP3 fuzzing"""
        adapter = BoofuzzAdapter()
        request = TestRequest(
            test_type="dnp3_fuzz",
            adapter_name="boofuzz",
            target_host="localhost",
            target_port=20000
        )
        
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value = mock_instance
            
            result = adapter.execute_test(request)
            
            assert result.test_type == "dnp3_fuzz"
            # If adapter is available, check for fuzz_status
            if adapter.is_available():
                assert "fuzz_status" in result.result_data
            else:
                # If not available, should return error
                assert result.status == "error"


class TestModbusAdapter:
    """Tests for ModbusAdapter"""

    def test_adapter_initialization(self):
        """Test Modbus adapter initialization"""
        adapter = ModbusAdapter()
        
        assert adapter.name == "modbus"
        assert isinstance(adapter.available, bool)

    def test_get_supported_tests(self):
        """Test getting supported test types"""
        adapter = ModbusAdapter()
        supported = adapter.get_supported_tests()
        
        assert isinstance(supported, list)
        assert "connection" in supported
        assert "read_coils" in supported
        assert "read_registers" in supported
        assert "write_coils" in supported
        assert "write_registers" in supported

    def test_connection_test(self):
        """Test Modbus connection test"""
        adapter = ModbusAdapter()
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="localhost",
            target_port=502,
            timeout=5
        )
        
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value = mock_instance
            
            result = adapter.execute_test(request)
            
            assert result.test_type == "connection"
            assert result.adapter_name == "modbus"

    def test_read_coils_test(self):
        """Test reading Modbus coils"""
        adapter = ModbusAdapter()
        request = TestRequest(
            test_type="read_coils",
            adapter_name="modbus",
            target_host="localhost",
            target_port=502
        )
        
        result = adapter.execute_test(request)
        
        assert result.test_type == "read_coils"
        # If adapter is available, check for read_status
        if adapter.is_available():
            assert "read_status" in result.result_data
        else:
            # If not available, should return error
            assert result.status == "error"


class TestCANAdapter:
    """Tests for CANAdapter"""

    def test_adapter_initialization(self):
        """Test CAN adapter initialization"""
        adapter = CANAdapter()
        
        assert adapter.name == "can"
        assert isinstance(adapter.available, bool)

    def test_get_supported_tests(self):
        """Test getting supported test types"""
        adapter = CANAdapter()
        supported = adapter.get_supported_tests()
        
        assert isinstance(supported, list)
        assert "connection" in supported
        assert "message_send" in supported
        assert "message_receive" in supported
        assert "bus_scan" in supported

    def test_connection_test(self):
        """Test CAN connection test"""
        adapter = CANAdapter()
        request = TestRequest(
            test_type="connection",
            adapter_name="can",
            target_host="localhost",
            target_port=0,
            parameters={"interface": "vcan0", "bitrate": 500000}
        )
        
        result = adapter.execute_test(request)
        
        assert result.test_type == "connection"
        assert result.adapter_name == "can"
        # If adapter is available, check for connection_status
        if adapter.is_available():
            assert "connection_status" in result.result_data
        else:
            # If not available, should return error
            assert result.status == "error"

    def test_message_send_test(self):
        """Test sending CAN messages"""
        adapter = CANAdapter()
        request = TestRequest(
            test_type="message_send",
            adapter_name="can",
            target_host="localhost",
            target_port=0
        )
        
        result = adapter.execute_test(request)
        
        assert result.test_type == "message_send"
        # If adapter is available, check for send_status
        if adapter.is_available():
            assert "send_status" in result.result_data
        else:
            # If not available, should return error
            assert result.status == "error"


class TestAdapterErrorHandling:
    """Tests for error handling in adapters"""

    def test_connection_timeout(self):
        """Test connection timeout handling"""
        adapter = ModbusAdapter()
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="localhost",
            target_port=502,
            timeout=1
        )
        
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value = mock_instance
            mock_instance.connect.side_effect = TimeoutError("Connection timeout")
            
            result = adapter.execute_test(request)
            
            # Result should handle the error gracefully
            assert result.adapter_name == "modbus"

    def test_connection_refused(self):
        """Test connection refused handling"""
        adapter = ModbusAdapter()
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="localhost",
            target_port=502
        )
        
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value = mock_instance
            mock_instance.connect.side_effect = ConnectionRefusedError("Connection refused")
            
            result = adapter.execute_test(request)
            
            assert result.adapter_name == "modbus"

    def test_generic_exception_handling(self):
        """Test generic exception handling"""
        adapter = DNP3Adapter()
        request = TestRequest(
            test_type="connection",
            adapter_name="dnp3",
            target_host="localhost",
            target_port=20000
        )
        
        with patch('socket.socket') as mock_socket:
            mock_socket.side_effect = Exception("Unexpected error")
            
            result = adapter.execute_test(request)
            
            assert result.adapter_name == "dnp3"


class TestAdapterAvailability:
    """Tests for adapter availability checking"""

    def test_adapter_availability_check(self):
        """Test that adapters check availability"""
        adapters = [
            DNP3Adapter(),
            OPCUAAdapter(),
            BoofuzzAdapter(),
            ModbusAdapter(),
            CANAdapter()
        ]
        
        for adapter in adapters:
            assert hasattr(adapter, 'available')
            assert isinstance(adapter.available, bool)
            assert adapter.is_available() == adapter.available

    def test_unavailable_adapter_returns_error(self):
        """Test that unavailable adapter returns error"""
        adapter = DNP3Adapter()
        
        # Mock the availability check to return False
        adapter.available = False
        
        request = TestRequest(
            test_type="connection",
            adapter_name="dnp3",
            target_host="localhost",
            target_port=20000
        )
        
        result = adapter.execute_test(request)
        
        assert result.status == "error"
        assert "not installed" in result.error_message


class TestResultDataIntegrity:
    """Tests for result data integrity"""

    def test_result_contains_all_required_fields(self):
        """Test that result contains all required fields"""
        adapter = ModbusAdapter()
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="10.0.8.2",
            target_port=502
        )
        
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value = mock_instance
            
            result = adapter.execute_test(request)
            
            # Check all required fields
            assert result.test_id is not None
            assert result.test_type == "connection"
            assert result.adapter_name == "modbus"
            assert result.status is not None
            assert result.start_time is not None
            assert result.target_host == "10.0.8.2"
            assert result.target_port == 502

    def test_result_data_is_serializable(self):
        """Test that result data is serializable to dict"""
        adapter = ModbusAdapter()
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="localhost",
            target_port=502
        )
        
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value = mock_instance
            
            result = adapter.execute_test(request)
            result_dict = result.to_dict()
            
            # Verify it's a valid dictionary
            assert isinstance(result_dict, dict)
            assert len(result_dict) > 0
            
            # Verify all values are serializable
            import json
            json_str = json.dumps(result_dict)
            assert isinstance(json_str, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
