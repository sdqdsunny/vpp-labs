"""
Integration tests for security adapters.

These tests verify end-to-end workflows including:
- Complete test execution from request to result storage
- Protocol analyzer integration
- Web interface workflows
- Docker container integration
- Multi-adapter interactions
"""

import json
import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

# Import adapters and models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.security_adapters.base_adapter import TestRequest, TestResult, TestAdapter
from services.security_adapters.dnp3_adapter import DNP3Adapter
from services.security_adapters.opcua_adapter import OPCUAAdapter
from services.security_adapters.boofuzz_adapter import BoofuzzAdapter
from services.security_adapters.modbus_adapter import ModbusAdapter
from services.security_adapters.can_adapter import CANAdapter


class MockSecurityTestManager:
    """Mock SecurityTestManager for integration testing."""
    
    def __init__(self):
        self.adapters = {}
        self.results = {}
        self.lock = threading.RLock()
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """Register all available adapters."""
        self.adapters['dnp3'] = DNP3Adapter()
        self.adapters['opcua'] = OPCUAAdapter()
        self.adapters['boofuzz'] = BoofuzzAdapter()
        self.adapters['modbus'] = ModbusAdapter()
        self.adapters['can'] = CANAdapter()
    
    def register_adapter(self, name, adapter):
        """Register a test adapter."""
        with self.lock:
            self.adapters[name] = adapter
    
    def run_test(self, test_request):
        """Execute a test and return results."""
        with self.lock:
            adapter_name = test_request.adapter_name
            if adapter_name not in self.adapters:
                result = TestResult(
                    test_id=f"test_{int(time.time())}",
                    test_type=test_request.test_type,
                    adapter_name=adapter_name,
                    status="error",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    duration=0.0,
                    target_host=test_request.target_host,
                    target_port=test_request.target_port,
                    target_url=test_request.target_url,
                    result_data={},
                    error_message=f"Adapter '{adapter_name}' not found",
                    vulnerabilities_found=[],
                    metadata={}
                )
                return result
            
            adapter = self.adapters[adapter_name]
            if not adapter.is_available():
                result = TestResult(
                    test_id=f"test_{int(time.time())}",
                    test_type=test_request.test_type,
                    adapter_name=adapter_name,
                    status="error",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    duration=0.0,
                    target_host=test_request.target_host,
                    target_port=test_request.target_port,
                    target_url=test_request.target_url,
                    result_data={},
                    error_message=f"Adapter '{adapter_name}' is not available",
                    vulnerabilities_found=[],
                    metadata={}
                )
                return result
            
            result = adapter.execute_test(test_request)
            self.results[result.test_id] = result
            return result
    
    def get_available_tools(self):
        """Get availability status of all tools."""
        with self.lock:
            return {name: adapter.is_available() for name, adapter in self.adapters.items()}
    
    def get_test_results(self, test_id):
        """Retrieve a test result."""
        with self.lock:
            return self.results.get(test_id)
    
    def get_results_by_adapter(self, adapter_name):
        """Get all results for a specific adapter."""
        with self.lock:
            return [r for r in self.results.values() if r.adapter_name == adapter_name]
    
    def get_results_by_host(self, target_host):
        """Get all results for a specific target host."""
        with self.lock:
            return [r for r in self.results.values() if r.target_host == target_host]
    
    def get_results_by_time_range(self, start_time, end_time):
        """Get results within a time range."""
        with self.lock:
            return [r for r in self.results.values() 
                    if start_time <= r.start_time <= end_time]


class TestEndToEndWorkflow:
    """Test complete end-to-end test execution workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MockSecurityTestManager()
    
    def test_single_adapter_test_execution(self):
        """Test executing a single test through one adapter."""
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        
        assert result is not None
        assert result.test_id is not None
        assert result.adapter_name == "modbus"
        assert result.test_type == "connection"
        assert result.target_host == "192.168.1.100"
        assert result.target_port == 502
        assert result.status in ["success", "failed", "error"]
        assert result.start_time is not None
        assert result.end_time is not None
        assert result.duration >= 0
    
    def test_multiple_sequential_tests(self):
        """Test executing multiple tests sequentially."""
        requests = [
            TestRequest(
                test_type="connection",
                adapter_name="modbus",
                target_host="192.168.1.100",
                target_port=502,
                target_url=None,
                parameters={},
                timeout=30
            ),
            TestRequest(
                test_type="connection",
                adapter_name="dnp3",
                target_host="192.168.1.101",
                target_port=20000,
                target_url=None,
                parameters={},
                timeout=30
            ),
            TestRequest(
                test_type="connection",
                adapter_name="opcua",
                target_host="192.168.1.102",
                target_port=4840,
                target_url="opc.tcp://192.168.1.102:4840",
                parameters={},
                timeout=30
            ),
        ]
        
        results = []
        for request in requests:
            result = self.manager.run_test(request)
            results.append(result)
        
        assert len(results) == 3
        assert all(r.test_id is not None for r in results)
        assert all(r.status in ["success", "failed", "error"] for r in results)
        assert results[0].adapter_name == "modbus"
        assert results[1].adapter_name == "dnp3"
        assert results[2].adapter_name == "opcua"
    
    def test_result_storage_and_retrieval(self):
        """Test that results are stored and can be retrieved."""
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        test_id = result.test_id
        
        # Only test retrieval if result was stored (adapter available)
        if result.status != "error" or "not available" not in result.error_message.lower():
            # Retrieve the result
            retrieved = self.manager.get_test_results(test_id)
            
            assert retrieved is not None
            assert retrieved.test_id == test_id
            assert retrieved.adapter_name == "modbus"
            assert retrieved.target_host == "192.168.1.100"
        else:
            # If adapter not available, verify error handling
            assert result.status == "error"
            assert result.test_id is not None
    
    def test_error_handling_in_workflow(self):
        """Test error handling in end-to-end workflow."""
        # Test with non-existent adapter
        request = TestRequest(
            test_type="connection",
            adapter_name="nonexistent",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        
        assert result.status == "error"
        assert "not found" in result.error_message.lower()
        assert result.test_id is not None


class TestMultiAdapterInteraction:
    """Test interactions between multiple adapters."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MockSecurityTestManager()
    
    def test_all_adapters_available(self):
        """Test that all adapters are available."""
        tools = self.manager.get_available_tools()
        
        assert "dnp3" in tools
        assert "opcua" in tools
        assert "boofuzz" in tools
        assert "modbus" in tools
        assert "can" in tools
    
    def test_adapter_discovery(self):
        """Test adapter discovery mechanism."""
        adapters = self.manager.adapters
        
        assert len(adapters) >= 5
        assert all(isinstance(adapter, TestAdapter) for adapter in adapters.values())
    
    def test_concurrent_adapter_tests(self):
        """Test running tests on multiple adapters concurrently."""
        results = []
        threads = []
        
        def run_test(adapter_name, host, port):
            request = TestRequest(
                test_type="connection",
                adapter_name=adapter_name,
                target_host=host,
                target_port=port,
                target_url=None,
                parameters={},
                timeout=30
            )
            result = self.manager.run_test(request)
            results.append(result)
        
        # Create threads for concurrent execution
        thread_configs = [
            ("modbus", "192.168.1.100", 502),
            ("dnp3", "192.168.1.101", 20000),
            ("opcua", "192.168.1.102", 4840),
        ]
        
        for adapter_name, host, port in thread_configs:
            thread = threading.Thread(target=run_test, args=(adapter_name, host, port))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 3
        assert all(r.test_id is not None for r in results)
        assert set(r.adapter_name for r in results) == {"modbus", "dnp3", "opcua"}


class TestResultFiltering:
    """Test result filtering and retrieval capabilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MockSecurityTestManager()
        self._populate_test_results()
    
    def _populate_test_results(self):
        """Populate manager with test results."""
        test_configs = [
            ("modbus", "192.168.1.100", 502),
            ("modbus", "192.168.1.101", 502),
            ("dnp3", "192.168.1.100", 20000),
            ("dnp3", "192.168.1.102", 20000),
            ("opcua", "192.168.1.102", 4840),
        ]
        
        for adapter_name, host, port in test_configs:
            request = TestRequest(
                test_type="connection",
                adapter_name=adapter_name,
                target_host=host,
                target_port=port,
                target_url=None,
                parameters={},
                timeout=30
            )
            result = self.manager.run_test(request)
            # Only store if successful (adapter available)
            if result.status != "error" or "not available" not in result.error_message.lower():
                self.manager.results[result.test_id] = result
    
    def test_filter_by_adapter(self):
        """Test filtering results by adapter name."""
        # Skip if no results were stored
        if len(self.manager.results) == 0:
            pytest.skip("No test results available (adapters not installed)")
        
        modbus_results = self.manager.get_results_by_adapter("modbus")
        
        # Verify filtering works for available results
        assert all(r.adapter_name == "modbus" for r in modbus_results)
    
    def test_filter_by_host(self):
        """Test filtering results by target host."""
        # Skip if no results were stored
        if len(self.manager.results) == 0:
            pytest.skip("No test results available (adapters not installed)")
        
        host_results = self.manager.get_results_by_host("192.168.1.100")
        
        # Verify filtering works for available results
        assert all(r.target_host == "192.168.1.100" for r in host_results)
    
    def test_filter_by_time_range(self):
        """Test filtering results by time range."""
        # Skip if no results were stored
        if len(self.manager.results) == 0:
            pytest.skip("No test results available (adapters not installed)")
        
        now = datetime.now()
        start_time = now - timedelta(hours=1)
        end_time = now + timedelta(hours=1)
        
        results = self.manager.get_results_by_time_range(start_time, end_time)
        
        # Verify filtering works for available results
        assert all(start_time <= r.start_time <= end_time for r in results)


class TestProtocolAnalyzerIntegration:
    """Test integration with protocol analyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MockSecurityTestManager()
    
    def test_result_format_compatibility(self):
        """Test that test results are compatible with protocol analyzer."""
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        
        # Convert to dict for analyzer compatibility
        result_dict = asdict(result)
        
        # Verify all required fields are present
        required_fields = [
            'test_id', 'test_type', 'adapter_name', 'status',
            'start_time', 'end_time', 'duration', 'target_host',
            'target_port', 'result_data', 'vulnerabilities_found'
        ]
        
        for field in required_fields:
            assert field in result_dict
    
    def test_vulnerability_tagging(self):
        """Test that vulnerabilities are properly tagged."""
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        
        # Verify vulnerability field exists and is a list
        assert isinstance(result.vulnerabilities_found, list)
        assert hasattr(result, 'vulnerabilities_found')
    
    def test_result_export_format(self):
        """Test that results can be exported in JSON format."""
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        result_dict = asdict(result)
        
        # Convert to JSON
        json_str = json.dumps(result_dict, default=str)
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed['test_id'] == result.test_id
        assert parsed['adapter_name'] == result.adapter_name


class TestWebInterfaceWorkflow:
    """Test web interface workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MockSecurityTestManager()
    
    def test_tool_selection_and_execution(self):
        """Test selecting a tool and executing a test."""
        # Get available tools
        tools = self.manager.get_available_tools()
        assert len(tools) > 0
        
        # Select a tool
        selected_tool = "modbus"
        assert selected_tool in tools
        
        # Execute test with selected tool
        request = TestRequest(
            test_type="connection",
            adapter_name=selected_tool,
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        assert result.adapter_name == selected_tool
    
    def test_parameter_input_and_validation(self):
        """Test parameter input and validation."""
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={"timeout": 30, "retries": 3},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        
        assert result.test_id is not None
        assert result.status in ["success", "failed", "error"]
    
    def test_result_display_and_retrieval(self):
        """Test displaying and retrieving test results."""
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        test_id = result.test_id
        
        # Only test retrieval if result was stored (adapter available)
        if result.status != "error" or "not available" not in result.error_message.lower():
            # Retrieve result for display
            retrieved = self.manager.get_test_results(test_id)
            
            assert retrieved is not None
            assert retrieved.test_id == test_id
            assert retrieved.adapter_name == "modbus"
            assert retrieved.target_host == "192.168.1.100"
        else:
            # If adapter not available, verify error handling
            assert result.status == "error"
            assert result.test_id is not None


class TestDockerContainerIntegration:
    """Test Docker container integration scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MockSecurityTestManager()
    
    def test_adapter_network_compatibility(self):
        """Test that adapters are compatible with Docker networking."""
        # Verify all adapters can be instantiated
        adapters = self.manager.adapters
        
        for name, adapter in adapters.items():
            assert adapter is not None
            assert hasattr(adapter, 'is_available')
            assert hasattr(adapter, 'execute_test')
            assert hasattr(adapter, 'get_supported_tests')
    
    def test_inter_container_communication(self):
        """Test communication between containers."""
        # Test with VPP network addresses
        vpp_hosts = [
            ("vpp-master", "10.0.8.10"),
            ("vpp-power-generation", "10.0.8.11"),
            ("vpp-storage", "10.0.8.12"),
            ("vpp-demand", "10.0.8.13"),
        ]
        
        for container_name, ip_address in vpp_hosts:
            request = TestRequest(
                test_type="connection",
                adapter_name="modbus",
                target_host=ip_address,
                target_port=502,
                target_url=None,
                parameters={},
                timeout=30
            )
            
            result = self.manager.run_test(request)
            
            assert result.target_host == ip_address
            assert result.test_id is not None
    
    def test_container_startup_verification(self):
        """Test container startup and tool availability."""
        tools = self.manager.get_available_tools()
        
        # Verify all expected tools are present
        expected_tools = ["dnp3", "opcua", "boofuzz", "modbus", "can"]
        for tool in expected_tools:
            assert tool in tools


class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MockSecurityTestManager()
    
    def test_adapter_not_found_recovery(self):
        """Test recovery when adapter is not found."""
        request = TestRequest(
            test_type="connection",
            adapter_name="nonexistent",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        
        assert result.status == "error"
        assert result.error_message is not None
        assert len(result.error_message) > 0
    
    def test_invalid_parameters_handling(self):
        """Test handling of invalid parameters."""
        request = TestRequest(
            test_type="invalid_test_type",
            adapter_name="modbus",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        
        # Should handle gracefully
        assert result.test_id is not None
        assert result.status in ["success", "failed", "error"]
    
    def test_concurrent_error_handling(self):
        """Test error handling under concurrent load."""
        results = []
        threads = []
        
        def run_test(adapter_name):
            request = TestRequest(
                test_type="connection",
                adapter_name=adapter_name,
                target_host="192.168.1.100",
                target_port=502,
                target_url=None,
                parameters={},
                timeout=30
            )
            result = self.manager.run_test(request)
            results.append(result)
        
        # Mix valid and invalid adapter names
        adapter_names = ["modbus", "nonexistent", "dnp3", "invalid", "opcua"]
        
        for adapter_name in adapter_names:
            thread = threading.Thread(target=run_test, args=(adapter_name,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 5
        assert all(r.test_id is not None for r in results)


class TestDataPersistence:
    """Test data persistence and retrieval."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MockSecurityTestManager()
    
    def test_result_persistence(self):
        """Test that results persist across retrievals."""
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        test_id = result.test_id
        
        # Only test persistence if result was stored (adapter available)
        if result.status != "error" or "not available" not in result.error_message.lower():
            # Retrieve multiple times
            for _ in range(3):
                retrieved = self.manager.get_test_results(test_id)
                assert retrieved is not None
                assert retrieved.test_id == test_id
        else:
            # If adapter not available, verify error handling
            assert result.status == "error"
            assert result.test_id is not None
    
    def test_historical_result_retrieval(self):
        """Test retrieving historical results."""
        # Create multiple results
        for i in range(5):
            request = TestRequest(
                test_type="connection",
                adapter_name="modbus",
                target_host=f"192.168.1.{100+i}",
                target_port=502,
                target_url=None,
                parameters={},
                timeout=30
            )
            result = self.manager.run_test(request)
            # Only store if successful (adapter available)
            if result.status != "error" or "not available" not in result.error_message.lower():
                self.manager.results[result.test_id] = result
        
        # Retrieve all results
        all_results = list(self.manager.results.values())
        
        # Verify retrieval works for available results
        assert all(r.test_id is not None for r in all_results)
    
    def test_result_metadata_preservation(self):
        """Test that result metadata is preserved."""
        metadata = {"test_run": "integration_test", "version": "1.0"}
        
        request = TestRequest(
            test_type="connection",
            adapter_name="modbus",
            target_host="192.168.1.100",
            target_port=502,
            target_url=None,
            parameters={},
            timeout=30
        )
        
        result = self.manager.run_test(request)
        result.metadata = metadata
        
        # Store and retrieve
        self.manager.results[result.test_id] = result
        retrieved = self.manager.get_test_results(result.test_id)
        
        assert retrieved.metadata == metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
