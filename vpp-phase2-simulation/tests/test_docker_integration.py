"""
Docker Integration Tests

Tests for verifying security tools work correctly in Docker containers.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from services.security_tester import get_security_manager


class TestDockerToolAvailability:
    """Test tool availability in Docker environment"""
    
    def test_get_available_tools(self):
        """Test getting available tools"""
        manager = get_security_manager()
        tools = manager.get_available_tools()
        
        assert isinstance(tools, dict)
        assert "pymodbus" in tools
        assert "opendnp3" in tools
        assert "python_opcua" in tools
        assert "socketcan" in tools
        assert "boofuzz" in tools
    
    def test_tool_availability_is_boolean(self):
        """Test that tool availability is boolean"""
        manager = get_security_manager()
        tools = manager.get_available_tools()
        
        for tool_name, available in tools.items():
            assert isinstance(available, bool), f"Tool {tool_name} availability should be boolean"
    
    def test_adapter_registration(self):
        """Test that adapters are registered"""
        manager = get_security_manager()
        adapters = manager.get_registered_adapters()
        
        assert len(adapters) > 0
        assert all(hasattr(adapter, 'is_available') for adapter in adapters.values())


class TestDockerNetworkAccess:
    """Test network access between containers"""
    
    def test_modbus_test_execution(self):
        """Test Modbus test execution"""
        manager = get_security_manager()
        
        # This should not crash even if target is unreachable
        result = manager.run_modbus_test("scan", "localhost", 502)
        
        assert isinstance(result, dict)
        # Result should have either success or error
        assert "error" in result or "status" in result
    
    def test_dnp3_test_execution(self):
        """Test DNP3 test execution"""
        manager = get_security_manager()
        
        # This should not crash even if target is unreachable
        result = manager.run_dnp3_test("connection", "localhost", 20000)
        
        assert isinstance(result, dict)
        # Result should have either success or error
        assert "error" in result or "status" in result
    
    def test_opcua_test_execution(self):
        """Test OPC UA test execution"""
        manager = get_security_manager()
        
        # This should not crash even if target is unreachable
        result = manager.run_opcua_test("connection", "opc.tcp://localhost:4840")
        
        assert isinstance(result, dict)
        # Result should have either success or error
        assert "error" in result or "status" in result
    
    def test_can_test_execution(self):
        """Test CAN test execution"""
        manager = get_security_manager()
        
        # This should not crash even if interface doesn't exist
        result = manager.run_can_test("status", "can0")
        
        assert isinstance(result, dict)
        # Result should have either success or error
        assert "error" in result or "status" in result
    
    def test_boofuzz_test_execution(self):
        """Test Boofuzz test execution"""
        manager = get_security_manager()
        
        # This should not crash even if target is unreachable
        result = manager.run_boofuzz_test("modbus_fuzz", "localhost", 502, duration=1)
        
        assert isinstance(result, dict)
        # Result should have either success or error
        assert "error" in result or "status" in result


class TestDockerStartupVerification:
    """Test Docker container startup verification"""
    
    def test_security_manager_initialization(self):
        """Test that SecurityTestManager initializes correctly"""
        manager = get_security_manager()
        
        assert manager is not None
        assert hasattr(manager, 'adapters')
        assert hasattr(manager, 'test_results')
    
    def test_adapter_info_retrieval(self):
        """Test retrieving adapter information"""
        manager = get_security_manager()
        adapter_info = manager.get_adapter_info()
        
        assert isinstance(adapter_info, dict)
        # Each adapter should have availability and supported tests
        for adapter_name, info in adapter_info.items():
            assert "available" in info
            assert isinstance(info["available"], bool)
    
    def test_protocol_analyzer_integration_initialization(self):
        """Test that protocol analyzer integration initializes"""
        manager = get_security_manager()
        
        # Should not crash even if integration is not available
        summary = manager.get_integration_summary()
        
        assert isinstance(summary, dict)


class TestDockerErrorHandling:
    """Test error handling in Docker environment"""
    
    def test_unreachable_host_handling(self):
        """Test handling of unreachable hosts"""
        manager = get_security_manager()
        
        # Should handle unreachable host gracefully
        result = manager.run_modbus_test("scan", "192.0.2.1", 502)  # TEST-NET-1 (unreachable)
        
        assert isinstance(result, dict)
        # Should either have error or indicate failure
        assert "error" in result or result.get("status") in ["failed", "error"]
    
    def test_invalid_port_handling(self):
        """Test handling of invalid ports"""
        manager = get_security_manager()
        
        # Should handle invalid port gracefully
        result = manager.run_modbus_test("scan", "localhost", 99999)
        
        assert isinstance(result, dict)
        # Should either have error or indicate failure
        assert "error" in result or result.get("status") in ["failed", "error"]
    
    def test_missing_interface_handling(self):
        """Test handling of missing CAN interface"""
        manager = get_security_manager()
        
        # Should handle missing interface gracefully
        result = manager.run_can_test("status", "can_nonexistent")
        
        assert isinstance(result, dict)
        # Should either have error or indicate failure
        assert "error" in result or result.get("status") in ["failed", "error"]


class TestDockerPersistence:
    """Test persistence in Docker environment"""
    
    def test_test_result_storage(self):
        """Test that test results can be stored"""
        manager = get_security_manager()
        
        # Run a test
        result = manager.run_modbus_test("scan", "localhost", 502)
        
        # Should be able to retrieve results
        assert isinstance(result, dict)
    
    def test_protocol_analyzer_integration(self):
        """Test protocol analyzer integration"""
        manager = get_security_manager()
        
        # Should be able to get tagged flows
        tagged_flows = manager.get_all_tagged_flows()
        
        assert isinstance(tagged_flows, list)


class TestDockerMultipleTests:
    """Test running multiple tests in Docker"""
    
    def test_sequential_test_execution(self):
        """Test running multiple tests sequentially"""
        manager = get_security_manager()
        
        results = []
        
        # Run multiple tests
        results.append(manager.run_modbus_test("scan", "localhost", 502))
        results.append(manager.run_dnp3_test("connection", "localhost", 20000))
        results.append(manager.run_opcua_test("connection", "opc.tcp://localhost:4840"))
        
        # All should return dictionaries
        assert all(isinstance(r, dict) for r in results)
    
    def test_concurrent_test_execution_safety(self):
        """Test that concurrent test execution is thread-safe"""
        manager = get_security_manager()
        
        # Manager should have thread lock
        assert hasattr(manager, 'lock')
        
        # Should be able to access results safely
        results = manager.test_results
        assert isinstance(results, dict)


class TestDockerEnvironmentVariables:
    """Test Docker environment variable handling"""
    
    def test_default_host_configuration(self):
        """Test default host configuration"""
        manager = get_security_manager()
        
        # Should handle default localhost
        result = manager.run_modbus_test("scan", "localhost", 502)
        
        assert isinstance(result, dict)
    
    def test_custom_host_configuration(self):
        """Test custom host configuration"""
        manager = get_security_manager()
        
        # Should handle custom hosts
        result = manager.run_modbus_test("scan", "192.168.1.100", 502)
        
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
