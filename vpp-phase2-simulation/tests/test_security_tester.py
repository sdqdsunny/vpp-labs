"""
Tests for Security Tester Service

Tests the security testing functionality
"""

import pytest
from services.security_tester import (
    SecurityTestManager, ModbusSecurityTester, DNP3SecurityTester,
    OPCUASecurityTester, CANSecurityTester, BoofuzzSecurityTester,
    get_security_manager
)


class TestSecurityTestManager:
    """Test cases for SecurityTestManager"""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh manager for each test"""
        manager = SecurityTestManager()
        yield manager
    
    def test_manager_initialization(self, manager):
        """Test manager initialization"""
        assert manager.modbus_tester is not None
        assert manager.dnp3_tester is not None
        assert manager.opcua_tester is not None
        assert manager.can_tester is not None
        assert manager.boofuzz_tester is not None
    
    def test_get_available_tools(self, manager):
        """Test getting available tools"""
        tools = manager.get_available_tools()
        
        assert isinstance(tools, dict)
        assert "pymodbus" in tools
        assert "opendnp3" in tools
        assert "python_opcua" in tools
        assert "socketcan" in tools
        assert "boofuzz" in tools
    
    def test_modbus_test_invalid_host(self, manager):
        """Test Modbus test with invalid host"""
        result = manager.run_modbus_test("scan", "invalid.host.local", 502)
        
        # Should return error or connection failed
        assert "error" in result or "Connection failed" in str(result)
    
    def test_dnp3_test_invalid_host(self, manager):
        """Test DNP3 test with invalid host"""
        result = manager.run_dnp3_test("connection", "invalid.host.local", 20000)
        
        # Should return unreachable status
        assert "status" in result or "error" in result
    
    def test_opcua_test_invalid_url(self, manager):
        """Test OPC UA test with invalid URL"""
        result = manager.run_opcua_test("connection", "opc.tcp://invalid.host.local:4840")
        
        # Should return error or unreachable
        assert "error" in result or "connected" in result
    
    def test_can_test_invalid_interface(self, manager):
        """Test CAN test with invalid interface"""
        result = manager.run_can_test("status", "invalid_interface")
        
        # Should return error or not found
        assert "error" in result or "status" in result
    
    def test_boofuzz_test_modbus(self, manager):
        """Test Boofuzz Modbus fuzzing"""
        result = manager.run_boofuzz_test("modbus_fuzz", "localhost", 502)
        
        # Should return result (may indicate setup required)
        assert isinstance(result, dict)
    
    def test_boofuzz_test_dnp3(self, manager):
        """Test Boofuzz DNP3 fuzzing"""
        result = manager.run_boofuzz_test("dnp3_fuzz", "localhost", 20000)
        
        # Should return result (may indicate setup required)
        assert isinstance(result, dict)
    
    def test_global_manager_instance(self):
        """Test global manager instance"""
        manager1 = get_security_manager()
        manager2 = get_security_manager()
        
        # Should be same instance
        assert manager1 is manager2


class TestModbusSecurityTester:
    """Test cases for ModbusSecurityTester"""
    
    @pytest.fixture
    def tester(self):
        """Create a fresh tester for each test"""
        return ModbusSecurityTester()
    
    def test_tester_initialization(self, tester):
        """Test tester initialization"""
        assert tester is not None
    
    def test_scan_devices_invalid_host(self, tester):
        """Test scanning invalid host"""
        result = tester.test_scan_devices("invalid.host.local", 502)
        
        assert isinstance(result, dict)
        assert "devices_found" in result or "error" in result


class TestDNP3SecurityTester:
    """Test cases for DNP3SecurityTester"""
    
    @pytest.fixture
    def tester(self):
        """Create a fresh tester for each test"""
        return DNP3SecurityTester()
    
    def test_tester_initialization(self, tester):
        """Test tester initialization"""
        assert tester is not None
    
    def test_connection_invalid_host(self, tester):
        """Test connection to invalid host"""
        result = tester.test_connection("invalid.host.local", 20000)
        
        assert isinstance(result, dict)
        assert "status" in result or "error" in result


class TestOPCUASecurityTester:
    """Test cases for OPCUASecurityTester"""
    
    @pytest.fixture
    def tester(self):
        """Create a fresh tester for each test"""
        return OPCUASecurityTester()
    
    def test_tester_initialization(self, tester):
        """Test tester initialization"""
        assert tester is not None
    
    def test_connection_invalid_url(self, tester):
        """Test connection to invalid URL"""
        result = tester.test_connection("opc.tcp://invalid.host.local:4840")
        
        assert isinstance(result, dict)
        # Either has url key or error key
        assert "url" in result or "error" in result


class TestCANSecurityTester:
    """Test cases for CANSecurityTester"""
    
    @pytest.fixture
    def tester(self):
        """Create a fresh tester for each test"""
        return CANSecurityTester()
    
    def test_tester_initialization(self, tester):
        """Test tester initialization"""
        assert tester is not None
    
    def test_interface_status(self, tester):
        """Test interface status check"""
        result = tester.test_interface_status("can0")
        
        assert isinstance(result, dict)
        assert "interface" in result
        assert "status" in result


class TestBoofuzzSecurityTester:
    """Test cases for BoofuzzSecurityTester"""
    
    @pytest.fixture
    def tester(self):
        """Create a fresh tester for each test"""
        return BoofuzzSecurityTester()
    
    def test_tester_initialization(self, tester):
        """Test tester initialization"""
        assert tester is not None
    
    def test_modbus_fuzz(self, tester):
        """Test Modbus fuzzing"""
        result = tester.test_modbus_fuzz("localhost", 502)
        
        assert isinstance(result, dict)
    
    def test_dnp3_fuzz(self, tester):
        """Test DNP3 fuzzing"""
        result = tester.test_dnp3_fuzz("localhost", 20000)
        
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
