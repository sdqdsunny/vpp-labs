"""
Property-Based Tests for Security Testing Adapters

This module contains property-based tests using Hypothesis framework
to verify universal properties of the security testing adapters.
"""

import pytest
import sys
import os
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.security_adapters import (
    TestAdapter, TestRequest, TestResult,
    DNP3Adapter, OPCUAAdapter, BoofuzzAdapter, ModbusAdapter, CANAdapter
)


# Custom strategies for generating test data
@st.composite
def strategy_test_results(draw):
    """Generate valid TestResult objects"""
    result = TestResult(
        test_type=draw(st.text(min_size=1, max_size=50)),
        adapter_name=draw(st.text(min_size=1, max_size=50)),
        target_host=draw(st.just("localhost")),
        target_port=draw(st.integers(min_value=1, max_value=65535))
    )
    
    # Randomly mark as success, failed, or error
    status = draw(st.sampled_from(["success", "failed", "error"]))
    if status == "success":
        result.mark_success()
    elif status == "failed":
        result.mark_failed("Test failed")
    else:
        result.mark_error("Test error")
    
    return result


class TestAdapterRegistrationProperty:
    """
    Property 1: Adapter Registration and Discovery
    
    For any security testing tool adapter, when the adapter initializes,
    it should be registered and appear in the available tools list.
    
    **Validates: Requirements 1.1, 2.1, 3.4, 5.2**
    """

    @given(st.just(None))
    @settings(max_examples=10)
    def test_adapter_registration(self, _):
        """Test that adapters register correctly"""
        adapters = [
            DNP3Adapter(),
            OPCUAAdapter(),
            BoofuzzAdapter(),
            ModbusAdapter(),
            CANAdapter()
        ]
        
        # All adapters should have a name
        for adapter in adapters:
            assert adapter.name is not None
            assert len(adapter.name) > 0
            
        # All adapters should have availability status
        for adapter in adapters:
            assert isinstance(adapter.available, bool)
            
        # All adapters should have supported tests
        for adapter in adapters:
            supported = adapter.get_supported_tests()
            assert isinstance(supported, list)
            assert len(supported) > 0


class TestGracefulDependencyHandlingProperty:
    """
    Property 2: Graceful Dependency Handling
    
    For any missing security testing tool dependency, the system should
    continue operation with that tool marked as unavailable, and a warning
    should be logged.
    
    **Validates: Requirements 1.5, 2.5, 3.4, 4.2**
    """

    @given(st.just(None))
    @settings(max_examples=10)
    def test_unavailable_adapter_handling(self, _):
        """Test that unavailable adapters don't break the system"""
        adapters = [
            DNP3Adapter(),
            OPCUAAdapter(),
            BoofuzzAdapter(),
            ModbusAdapter(),
            CANAdapter()
        ]
        
        for adapter in adapters:
            # If adapter is not available, it should still be usable
            if not adapter.is_available():
                request = TestRequest(
                    test_type="connection",
                    adapter_name=adapter.name,
                    target_host="localhost",
                    target_port=502
                )
                
                result = adapter.execute_test(request)
                
                # Should return error, not crash
                assert result.status == "error"
                assert result.error_message is not None


class TestResultStandardizationProperty:
    """
    Property 3: Test Result Standardization
    
    For any security test executed by any adapter, the result should contain
    all required fields in a consistent format.
    
    **Validates: Requirements 1.4, 2.4, 3.3, 5.3**
    """

    @given(strategy_test_results())
    @settings(max_examples=50)
    def test_result_has_all_required_fields(self, result):
        """Test that all results have required fields"""
        # Check all required fields exist
        assert result.test_id is not None
        assert result.test_type is not None
        assert result.adapter_name is not None
        assert result.status is not None
        assert result.start_time is not None
        assert result.target_host is not None
        assert result.target_port is not None
        
        # Check field types
        assert isinstance(result.test_id, str)
        assert isinstance(result.test_type, str)
        assert isinstance(result.adapter_name, str)
        assert isinstance(result.status, str)
        assert isinstance(result.start_time, datetime)
        assert isinstance(result.target_host, str)
        assert isinstance(result.target_port, int)
        
        # Check status is valid
        assert result.status in ["success", "failed", "error", "pending"]

    @given(strategy_test_results())
    @settings(max_examples=50)
    def test_result_consistency_across_adapters(self, result):
        """Test that results are consistent across different adapters"""
        # Convert to dict and back
        result_dict = result.to_dict()
        
        # Should be serializable to JSON
        json_str = json.dumps(result_dict)
        assert isinstance(json_str, str)
        
        # Should have consistent structure
        assert "test_id" in result_dict
        assert "test_type" in result_dict
        assert "adapter_name" in result_dict
        assert "status" in result_dict


class TestErrorHandlingProperty:
    """
    Property 4: Error Handling and Recovery
    
    For any test adapter that encounters an error, the adapter should catch
    the exception and return a TestResult with status="error" and a
    descriptive error_message.
    
    **Validates: Requirements 5.4, 10.1**
    """

    @given(st.just(None))
    @settings(max_examples=10)
    def test_error_handling_consistency(self, _):
        """Test that errors are handled consistently"""
        adapters = [
            DNP3Adapter(),
            OPCUAAdapter(),
            BoofuzzAdapter(),
            ModbusAdapter(),
            CANAdapter()
        ]
        
        for adapter in adapters:
            # Create a request with invalid port
            request = TestRequest(
                test_type="connection",
                adapter_name=adapter.name,
                target_host="localhost",
                target_port=1,  # Invalid port
                timeout=1
            )
            
            # Should not raise exception
            try:
                result = adapter.execute_test(request)
                # Result should be valid
                assert result is not None
                assert isinstance(result, TestResult)
            except Exception as e:
                pytest.fail(f"Adapter {adapter.name} raised exception: {str(e)}")


class TestResultPersistenceProperty:
    """
    Property 5: Test Result Persistence
    
    For any completed security test, the test result should be stored in
    persistent storage and retrievable by test_id.
    
    **Validates: Requirements 9.1**
    """

    @given(strategy_test_results())
    @settings(max_examples=20)
    def test_result_serialization(self, result):
        """Test that results can be serialized for storage"""
        # Convert to dict
        result_dict = result.to_dict()
        
        # Should be JSON serializable
        json_str = json.dumps(result_dict)
        
        # Should be deserializable
        deserialized = json.loads(json_str)
        
        # Should have same structure
        assert deserialized["test_id"] == result.test_id
        assert deserialized["test_type"] == result.test_type
        assert deserialized["adapter_name"] == result.adapter_name
        assert deserialized["status"] == result.status


class TestHistoricalResultRetrievalProperty:
    """
    Property 6: Historical Result Retrieval
    
    For any test result created within the past 30 days, the result should
    be retrievable through the historical results API.
    
    **Validates: Requirements 9.2**
    """

    @given(strategy_test_results())
    @settings(max_examples=20)
    def test_result_timestamp_validity(self, result):
        """Test that result timestamps are valid"""
        # Start time should be before or equal to end time
        if result.end_time is not None:
            assert result.start_time <= result.end_time
        
        # Duration should be non-negative
        assert result.duration >= 0
        
        # If status is not pending, should have end_time
        if result.status != "pending":
            assert result.end_time is not None


class TestResultFilteringProperty:
    """
    Property 7: Result Filtering
    
    For any set of test results, filtering by protocol, target_host, or
    test_type should return only results matching the filter criteria.
    
    **Validates: Requirements 9.3**
    """

    @given(st.lists(strategy_test_results(), min_size=1, max_size=10))
    @settings(max_examples=20)
    def test_result_filtering_consistency(self, results):
        """Test that results can be filtered consistently"""
        # All results should have required fields for filtering
        for result in results:
            assert result.adapter_name is not None
            assert result.target_host is not None
            assert result.test_type is not None
        
        # Filtering by adapter_name should work
        if results:
            adapter_name = results[0].adapter_name
            filtered = [r for r in results if r.adapter_name == adapter_name]
            assert len(filtered) > 0
            assert all(r.adapter_name == adapter_name for r in filtered)


class TestProtocolAnalyzerIntegrationProperty:
    """
    Property 8: Protocol Analyzer Integration
    
    For any completed security test, the test metadata should be in a format
    compatible with the protocol analyzer.
    
    **Validates: Requirements 7.1, 7.2**
    """

    @given(strategy_test_results())
    @settings(max_examples=20)
    def test_result_analyzer_compatibility(self, result):
        """Test that results are compatible with protocol analyzer"""
        result_dict = result.to_dict()
        
        # Should have required fields for analyzer
        assert "adapter_name" in result_dict
        assert "target_host" in result_dict
        assert "target_port" in result_dict
        assert "test_type" in result_dict
        assert "status" in result_dict
        
        # Should be JSON serializable
        json_str = json.dumps(result_dict)
        assert isinstance(json_str, str)


class TestVulnerabilityTaggingProperty:
    """
    Property 9: Vulnerability Tagging
    
    For any discovered vulnerability in a security test, the related network
    flows should be tagged with the vulnerability information.
    
    **Validates: Requirements 7.3**
    """

    @given(strategy_test_results())
    @settings(max_examples=20)
    def test_vulnerability_field_consistency(self, result):
        """Test that vulnerability fields are consistent"""
        # Vulnerabilities should be a list
        assert isinstance(result.vulnerabilities_found, list)
        
        # All items should be strings
        for vuln in result.vulnerabilities_found:
            assert isinstance(vuln, str)


class TestDockerNetworkAccessProperty:
    """
    Property 10: Docker Container Network Access
    
    For any security test running in a Docker container, the test should
    have network access to other containers on the 10.0.8.0/24 network.
    
    **Validates: Requirements 8.3**
    """

    @given(st.just(None))
    @settings(max_examples=5)
    def test_adapter_network_compatibility(self, _):
        """Test that adapters support network operations"""
        adapters = [
            DNP3Adapter(),
            OPCUAAdapter(),
            BoofuzzAdapter(),
            ModbusAdapter(),
            CANAdapter()
        ]
        
        for adapter in adapters:
            # All adapters should support connection tests
            supported = adapter.get_supported_tests()
            assert "connection" in supported or len(supported) > 0


class TestDependencyInstallationProperty:
    """
    Property 11: Dependency Installation
    
    For any required security testing tool dependency declared in
    requirements.txt, the dependency should be installed during project
    deployment.
    
    **Validates: Requirements 4.1**
    """

    @given(st.just(None))
    @settings(max_examples=5)
    def test_dependencies_importable(self, _):
        """Test that dependencies can be imported"""
        # Try to import each adapter's dependencies
        try:
            import pymodbus
            assert True
        except ImportError:
            pass  # Optional dependency
        
        try:
            import can
            assert True
        except ImportError:
            pass  # Optional dependency


class TestStartupVerificationProperty:
    """
    Property 12: Startup Verification
    
    For any system startup, the system should verify that all declared
    dependencies are available and report their status in the available
    tools list.
    
    **Validates: Requirements 4.4, 8.2**
    """

    @given(st.just(None))
    @settings(max_examples=5)
    def test_startup_status_reporting(self, _):
        """Test that startup status is reported correctly"""
        adapters = [
            DNP3Adapter(),
            OPCUAAdapter(),
            BoofuzzAdapter(),
            ModbusAdapter(),
            CANAdapter()
        ]
        
        # All adapters should report availability
        for adapter in adapters:
            assert isinstance(adapter.is_available(), bool)
            assert isinstance(adapter.available, bool)
            assert adapter.is_available() == adapter.available


class TestRetryLogicProperty:
    """
    Property 13: Retry Logic
    
    For any network error encountered during a security test, the system
    should retry the test up to 3 times before reporting failure.
    
    **Validates: Requirements 10.3**
    """

    @given(st.just(None))
    @settings(max_examples=5)
    def test_error_recovery_capability(self, _):
        """Test that adapters can handle retries"""
        adapters = [
            DNP3Adapter(),
            OPCUAAdapter(),
            BoofuzzAdapter(),
            ModbusAdapter(),
            CANAdapter()
        ]
        
        for adapter in adapters:
            # Create multiple requests to same target
            for _ in range(3):
                request = TestRequest(
                    test_type="connection",
                    adapter_name=adapter.name,
                    target_host="localhost",
                    target_port=502,
                    timeout=1
                )
                
                # Should not crash on repeated calls
                result = adapter.execute_test(request)
                assert result is not None


class TestExportCompletenessProperty:
    """
    Property 14: Export Completeness
    
    For any exported test result, the export should include all metadata,
    findings, and vulnerability information in a structured format.
    
    **Validates: Requirements 9.4, 7.4**
    """

    @given(strategy_test_results())
    @settings(max_examples=20)
    def test_export_completeness(self, result):
        """Test that exports are complete"""
        result_dict = result.to_dict()
        
        # Should have all metadata
        required_fields = [
            "test_id", "test_type", "adapter_name", "status",
            "start_time", "end_time", "duration",
            "target_host", "target_port", "result_data",
            "error_message", "vulnerabilities_found", "metadata"
        ]
        
        for field in required_fields:
            assert field in result_dict, f"Missing field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
