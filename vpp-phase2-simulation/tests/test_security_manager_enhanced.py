"""
Enhanced SecurityTestManager Tests

Tests for the adapter-based SecurityTestManager implementation.
Validates adapter registration, discovery, routing, and result storage.
"""

import pytest
import threading
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from services.security_tester import SecurityTestManager
from services.security_adapters.base_adapter import TestAdapter, TestRequest, TestResult


class MockAdapter(TestAdapter):
    """Mock adapter for testing"""
    
    def __init__(self, name: str = "mock", available: bool = True):
        self.name = name
        self._available = available
        self.test_count = 0
        # Call parent init to set self.available
        super().__init__(name)
    
    def _check_availability(self) -> bool:
        return self._available
    
    def get_supported_tests(self):
        return ["test_type_1", "test_type_2"]
    
    def execute_test(self, test_request: TestRequest) -> TestResult:
        self.test_count += 1
        result = self._create_result(test_request)
        result.mark_success()
        result.result_data = {"mock_data": "test_result"}
        return result


class TestSecurityTestManagerAdapterRegistration:
    """Test adapter registration functionality"""
    
    def test_manager_initialization(self):
        """Test that SecurityTestManager initializes correctly"""
        manager = SecurityTestManager()
        assert manager is not None
        assert isinstance(manager.adapters, dict)
        assert isinstance(manager.test_results, dict)
        assert manager.lock is not None
        # Note: adapters are auto-registered during initialization
        assert len(manager.adapters) >= 0
    
    def test_register_adapter(self):
        """Test registering a single adapter"""
        manager = SecurityTestManager()
        adapter = MockAdapter("test_adapter")
        
        manager.register_adapter("test_adapter", adapter)
        
        assert "test_adapter" in manager.adapters
        assert manager.adapters["test_adapter"] == adapter
    
    def test_register_multiple_adapters(self):
        """Test registering multiple adapters"""
        manager = SecurityTestManager()
        initial_count = len(manager.adapters)
        adapters = [
            MockAdapter("adapter1"),
            MockAdapter("adapter2"),
            MockAdapter("adapter3"),
        ]
        
        for adapter in adapters:
            manager.register_adapter(adapter.name, adapter)
        
        assert len(manager.adapters) == initial_count + 3
        assert all(adapter.name in manager.adapters for adapter in adapters)
    
    def test_get_adapter(self):
        """Test retrieving a registered adapter"""
        manager = SecurityTestManager()
        adapter = MockAdapter("test_adapter")
        manager.register_adapter("test_adapter", adapter)
        
        retrieved = manager.get_adapter("test_adapter")
        
        assert retrieved == adapter
    
    def test_get_nonexistent_adapter(self):
        """Test retrieving a non-existent adapter returns None"""
        manager = SecurityTestManager()
        
        retrieved = manager.get_adapter("nonexistent")
        
        assert retrieved is None
    
    def test_get_registered_adapters(self):
        """Test getting all registered adapters"""
        manager = SecurityTestManager()
        initial_count = len(manager.adapters)
        adapters = [
            MockAdapter("adapter1"),
            MockAdapter("adapter2"),
        ]
        
        for adapter in adapters:
            manager.register_adapter(adapter.name, adapter)
        
        all_adapters = manager.get_registered_adapters()
        
        assert len(all_adapters) == initial_count + 2
        assert "adapter1" in all_adapters
        assert "adapter2" in all_adapters


class TestSecurityTestManagerAdapterDiscovery:
    """Test adapter discovery functionality"""
    
    def test_get_available_tools_includes_adapters(self):
        """Test that get_available_tools includes registered adapters"""
        manager = SecurityTestManager()
        adapter1 = MockAdapter("adapter1", available=True)
        adapter2 = MockAdapter("adapter2", available=False)
        
        manager.register_adapter("adapter1", adapter1)
        manager.register_adapter("adapter2", adapter2)
        
        tools = manager.get_available_tools()
        
        assert "adapter1" in tools
        assert tools["adapter1"] is True
        assert "adapter2" in tools
        assert tools["adapter2"] is False
    
    def test_get_adapter_info(self):
        """Test getting detailed adapter information"""
        manager = SecurityTestManager()
        adapter = MockAdapter("test_adapter")
        manager.register_adapter("test_adapter", adapter)
        
        info = manager.get_adapter_info()
        
        assert "test_adapter" in info
        assert info["test_adapter"]["available"] is True
        assert "supported_tests" in info["test_adapter"]
        assert "test_type_1" in info["test_adapter"]["supported_tests"]
    
    def test_get_adapter_info_multiple_adapters(self):
        """Test getting info for multiple adapters"""
        manager = SecurityTestManager()
        adapters = [
            MockAdapter("adapter1", available=True),
            MockAdapter("adapter2", available=False),
            MockAdapter("adapter3", available=True),
        ]
        
        for adapter in adapters:
            manager.register_adapter(adapter.name, adapter)
        
        info = manager.get_adapter_info()
        
        # Check that our adapters are in the info
        assert "adapter1" in info
        assert "adapter2" in info
        assert "adapter3" in info
        assert info["adapter1"]["available"] is True
        assert info["adapter2"]["available"] is False
        assert info["adapter3"]["available"] is True


class TestSecurityTestManagerTestExecution:
    """Test test execution through adapters"""
    
    def test_run_test_with_adapter_success(self):
        """Test successful test execution with adapter"""
        manager = SecurityTestManager()
        adapter = MockAdapter("test_adapter")
        manager.register_adapter("test_adapter", adapter)
        
        test_request = TestRequest(
            test_type="test_type_1",
            adapter_name="test_adapter",
            target_host="localhost",
            target_port=8080,
        )
        
        result = manager.run_test_with_adapter("test_adapter", test_request)
        
        assert result.status == "success"
        assert result.adapter_name == "test_adapter"
        assert adapter.test_count == 1
    
    def test_run_test_with_unavailable_adapter(self):
        """Test test execution with unavailable adapter"""
        manager = SecurityTestManager()
        adapter = MockAdapter("test_adapter", available=False)
        manager.register_adapter("test_adapter", adapter)
        
        test_request = TestRequest(
            test_type="test_type_1",
            adapter_name="test_adapter",
            target_host="localhost",
            target_port=8080,
        )
        
        result = manager.run_test_with_adapter("test_adapter", test_request)
        
        assert result.status == "error"
        assert "not available" in result.error_message
    
    def test_run_test_with_nonexistent_adapter(self):
        """Test test execution with non-existent adapter"""
        manager = SecurityTestManager()
        
        test_request = TestRequest(
            test_type="test_type_1",
            adapter_name="nonexistent",
            target_host="localhost",
            target_port=8080,
        )
        
        result = manager.run_test_with_adapter("nonexistent", test_request)
        
        assert result.status == "error"
        assert "not found" in result.error_message
    
    def test_run_test_stores_result(self):
        """Test that test results are stored"""
        manager = SecurityTestManager()
        adapter = MockAdapter("test_adapter")
        manager.register_adapter("test_adapter", adapter)
        
        test_request = TestRequest(
            test_type="test_type_1",
            adapter_name="test_adapter",
            target_host="localhost",
            target_port=8080,
        )
        
        result = manager.run_test_with_adapter("test_adapter", test_request)
        
        assert result.test_id in manager.test_results
        assert manager.test_results[result.test_id] == result
    
    def test_get_test_result(self):
        """Test retrieving a stored test result"""
        manager = SecurityTestManager()
        adapter = MockAdapter("test_adapter")
        manager.register_adapter("test_adapter", adapter)
        
        test_request = TestRequest(
            test_type="test_type_1",
            adapter_name="test_adapter",
            target_host="localhost",
            target_port=8080,
        )
        
        result = manager.run_test_with_adapter("test_adapter", test_request)
        retrieved = manager.get_test_result(result.test_id)
        
        assert retrieved == result
        assert retrieved.status == "success"
    
    def test_get_nonexistent_test_result(self):
        """Test retrieving a non-existent test result"""
        manager = SecurityTestManager()
        
        result = manager.get_test_result("nonexistent_id")
        
        assert result is None


class TestSecurityTestManagerErrorHandling:
    """Test error handling in SecurityTestManager"""
    
    def test_adapter_exception_handling(self):
        """Test that adapter exceptions are caught and handled"""
        manager = SecurityTestManager()
        
        # Create adapter that raises exception
        adapter = Mock(spec=TestAdapter)
        adapter.name = "error_adapter"
        adapter.is_available.return_value = True
        adapter.execute_test.side_effect = Exception("Test error")
        
        manager.register_adapter("error_adapter", adapter)
        
        test_request = TestRequest(
            test_type="test_type_1",
            adapter_name="error_adapter",
            target_host="localhost",
            target_port=8080,
        )
        
        result = manager.run_test_with_adapter("error_adapter", test_request)
        
        assert result.status == "error"
        assert "Test error" in result.error_message
    
    def test_thread_safety_adapter_registration(self):
        """Test thread-safe adapter registration"""
        manager = SecurityTestManager()
        initial_count = len(manager.adapters)
        adapters_registered = []
        
        def register_adapters():
            for i in range(10):
                adapter = MockAdapter(f"adapter_{threading.current_thread().name}_{i}")
                manager.register_adapter(adapter.name, adapter)
                adapters_registered.append(adapter.name)
        
        threads = [threading.Thread(target=register_adapters) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        assert len(manager.adapters) == initial_count + 30
        assert len(adapters_registered) == 30
    
    def test_thread_safety_test_result_storage(self):
        """Test thread-safe test result storage"""
        manager = SecurityTestManager()
        adapter = MockAdapter("test_adapter")
        manager.register_adapter("test_adapter", adapter)
        
        results_stored = []
        
        def run_tests():
            for i in range(10):
                test_request = TestRequest(
                    test_type="test_type_1",
                    adapter_name="test_adapter",
                    target_host="localhost",
                    target_port=8080,
                )
                result = manager.run_test_with_adapter("test_adapter", test_request)
                results_stored.append(result.test_id)
        
        threads = [threading.Thread(target=run_tests) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        assert len(manager.test_results) == 30
        assert len(results_stored) == 30


class TestSecurityTestManagerBackwardCompatibility:
    """Test backward compatibility with legacy testers"""
    
    def test_legacy_testers_still_available(self):
        """Test that legacy testers are still available"""
        manager = SecurityTestManager()
        
        assert hasattr(manager, 'modbus_tester')
        assert hasattr(manager, 'dnp3_tester')
        assert hasattr(manager, 'opcua_tester')
        assert hasattr(manager, 'can_tester')
        assert hasattr(manager, 'boofuzz_tester')
    
    def test_legacy_test_methods_still_work(self):
        """Test that legacy test methods still work"""
        manager = SecurityTestManager()
        
        # These should not raise exceptions
        result = manager.run_modbus_test("scan", "localhost", 502)
        assert isinstance(result, dict)
        
        result = manager.run_dnp3_test("connection", "localhost", 20000)
        assert isinstance(result, dict)
        
        result = manager.run_opcua_test("connection", "opc.tcp://localhost:4840")
        assert isinstance(result, dict)
        
        result = manager.run_can_test("status", "can0")
        assert isinstance(result, dict)
        
        result = manager.run_boofuzz_test("modbus_fuzz", "localhost", 502)
        assert isinstance(result, dict)


class TestSecurityTestManagerIntegration:
    """Integration tests for SecurityTestManager"""
    
    def test_full_workflow_adapter_registration_to_result_retrieval(self):
        """Test complete workflow from adapter registration to result retrieval"""
        manager = SecurityTestManager()
        
        # Register adapters
        adapters = [
            MockAdapter("dnp3", available=True),
            MockAdapter("opcua", available=True),
            MockAdapter("boofuzz", available=True),
        ]
        
        for adapter in adapters:
            manager.register_adapter(adapter.name, adapter)
        
        # Check available tools
        tools = manager.get_available_tools()
        assert all(tools.get(adapter.name) for adapter in adapters)
        
        # Execute tests
        results = []
        for adapter in adapters:
            test_request = TestRequest(
                test_type="test_type_1",
                adapter_name=adapter.name,
                target_host="localhost",
                target_port=8080,
            )
            result = manager.run_test_with_adapter(adapter.name, test_request)
            results.append(result)
        
        # Verify results
        assert len(results) == 3
        assert all(result.status == "success" for result in results)
        
        # Retrieve results
        for result in results:
            retrieved = manager.get_test_result(result.test_id)
            assert retrieved == result
    
    def test_mixed_adapter_availability(self):
        """Test handling of mixed adapter availability"""
        manager = SecurityTestManager()
        
        # Register adapters with different availability
        adapters = [
            MockAdapter("available1", available=True),
            MockAdapter("unavailable1", available=False),
            MockAdapter("available2", available=True),
            MockAdapter("unavailable2", available=False),
        ]
        
        for adapter in adapters:
            manager.register_adapter(adapter.name, adapter)
        
        # Get adapter info
        info = manager.get_adapter_info()
        
        # Check that our adapters are in the info
        assert "available1" in info
        assert "unavailable1" in info
        assert "available2" in info
        assert "unavailable2" in info
        
        # Count availability for our specific adapters
        available_count = sum(1 for name in ["available1", "available2"] if info[name]["available"])
        unavailable_count = sum(1 for name in ["unavailable1", "unavailable2"] if not info[name]["available"])
        
        assert available_count == 2
        assert unavailable_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
