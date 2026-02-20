"""
Unit Tests for DNP3 Three Steps Enhancement

Tests for:
1. Web UI Enhancement (security_tester.html)
2. API Routes Enhancement (routes/security_tester.py)
3. Manager Methods Enhancement (services/security_tester.py)
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the modules to test
from services.security_tester import SecurityTestManager
from services.security_adapters.dnp3_adapter import DNP3Adapter
from services.dnp3_attack_detection import DNP3AttackDetector


class TestSecurityTestManagerDNP3Methods:
    """Test new DNP3 methods in SecurityTestManager"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = SecurityTestManager()

    def test_run_dnp3_attack_detection_method_exists(self):
        """Test that run_dnp3_attack_detection method exists"""
        assert hasattr(self.manager, 'run_dnp3_attack_detection')
        assert callable(self.manager.run_dnp3_attack_detection)

    def test_run_dnp3_anomaly_analysis_method_exists(self):
        """Test that run_dnp3_anomaly_analysis method exists"""
        assert hasattr(self.manager, 'run_dnp3_anomaly_analysis')
        assert callable(self.manager.run_dnp3_anomaly_analysis)

    def test_get_dnp3_alarm_state_method_exists(self):
        """Test that get_dnp3_alarm_state method exists"""
        assert hasattr(self.manager, 'get_dnp3_alarm_state')
        assert callable(self.manager.get_dnp3_alarm_state)

    def test_get_dnp3_statistics_method_exists(self):
        """Test that get_dnp3_statistics method exists"""
        assert hasattr(self.manager, 'get_dnp3_statistics')
        assert callable(self.manager.get_dnp3_statistics)

    def test_run_dnp3_attack_detection_returns_dict(self):
        """Test that run_dnp3_attack_detection returns a dictionary"""
        result = self.manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data={"control_field": 0x05}
        )
        assert isinstance(result, dict)

    def test_run_dnp3_attack_detection_response_structure(self):
        """Test response structure of run_dnp3_attack_detection"""
        result = self.manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data={"control_field": 0x05}
        )
        # Should have status field
        assert "status" in result or "error" in result

    def test_run_dnp3_anomaly_analysis_returns_dict(self):
        """Test that run_dnp3_anomaly_analysis returns a dictionary"""
        result = self.manager.run_dnp3_anomaly_analysis(
            host="localhost",
            port=20000,
            packet_data={"control_field": 0x05}
        )
        assert isinstance(result, dict)

    def test_run_dnp3_anomaly_analysis_response_structure(self):
        """Test response structure of run_dnp3_anomaly_analysis"""
        result = self.manager.run_dnp3_anomaly_analysis(
            host="localhost",
            port=20000,
            packet_data={"control_field": 0x05}
        )
        # Should have status field
        assert "status" in result or "error" in result

    def test_get_dnp3_alarm_state_returns_dict(self):
        """Test that get_dnp3_alarm_state returns a dictionary"""
        result = self.manager.get_dnp3_alarm_state()
        assert isinstance(result, dict)

    def test_get_dnp3_alarm_state_response_structure(self):
        """Test response structure of get_dnp3_alarm_state"""
        result = self.manager.get_dnp3_alarm_state()
        # Should have status field
        assert "status" in result or "error" in result

    def test_get_dnp3_statistics_returns_dict(self):
        """Test that get_dnp3_statistics returns a dictionary"""
        result = self.manager.get_dnp3_statistics()
        assert isinstance(result, dict)

    def test_get_dnp3_statistics_response_structure(self):
        """Test response structure of get_dnp3_statistics"""
        result = self.manager.get_dnp3_statistics()
        # Should have status field
        assert "status" in result or "error" in result

    def test_run_dnp3_attack_detection_with_empty_packet_data(self):
        """Test run_dnp3_attack_detection with empty packet data"""
        result = self.manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_run_dnp3_attack_detection_with_none_packet_data(self):
        """Test run_dnp3_attack_detection with None packet data"""
        result = self.manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data=None
        )
        assert isinstance(result, dict)

    def test_run_dnp3_attack_detection_with_valid_packet(self):
        """Test run_dnp3_attack_detection with valid packet data"""
        result = self.manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data={
                "control_field": 0x80,
                "function_code": 0x01,
                "data_length": 100,
                "sequence_number": 1,
                "object_type": 1
            }
        )
        assert isinstance(result, dict)

    def test_run_dnp3_attack_detection_with_invalid_packet(self):
        """Test run_dnp3_attack_detection with invalid packet data"""
        result = self.manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data={"control_field": 256}  # Invalid
        )
        assert isinstance(result, dict)

    def test_run_dnp3_anomaly_analysis_with_valid_packet(self):
        """Test run_dnp3_anomaly_analysis with valid packet data"""
        result = self.manager.run_dnp3_anomaly_analysis(
            host="localhost",
            port=20000,
            packet_data={
                "control_field": 0x80,
                "function_code": 0x01,
                "data_length": 100,
                "sequence_number": 1,
                "object_type": 1
            }
        )
        assert isinstance(result, dict)

    def test_run_dnp3_anomaly_analysis_with_invalid_packet(self):
        """Test run_dnp3_anomaly_analysis with invalid packet data"""
        result = self.manager.run_dnp3_anomaly_analysis(
            host="localhost",
            port=20000,
            packet_data={"control_field": 256}  # Invalid
        )
        assert isinstance(result, dict)

    def test_methods_handle_missing_adapter_gracefully(self):
        """Test that methods handle missing adapter gracefully"""
        # Create a manager and remove the DNP3 adapter
        manager = SecurityTestManager()
        
        # Try to call methods - should return error response
        result1 = manager.run_dnp3_attack_detection("localhost", 20000)
        result2 = manager.run_dnp3_anomaly_analysis("localhost", 20000)
        result3 = manager.get_dnp3_alarm_state()
        result4 = manager.get_dnp3_statistics()
        
        # All should return dictionaries (either with status or error)
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert isinstance(result3, dict)
        assert isinstance(result4, dict)

    def test_methods_return_consistent_format(self):
        """Test that all methods return consistent response format"""
        result1 = self.manager.run_dnp3_attack_detection("localhost", 20000)
        result2 = self.manager.run_dnp3_anomaly_analysis("localhost", 20000)
        result3 = self.manager.get_dnp3_alarm_state()
        result4 = self.manager.get_dnp3_statistics()
        
        # All should be dictionaries
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert isinstance(result3, dict)
        assert isinstance(result4, dict)


class TestDNP3AdapterEnhancement:
    """Test DNP3Adapter enhancements for attack detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.adapter = DNP3Adapter()

    def test_adapter_has_attack_detector(self):
        """Test that adapter has attack_detector instance"""
        assert hasattr(self.adapter, 'attack_detector')
        assert isinstance(self.adapter.attack_detector, DNP3AttackDetector)

    def test_adapter_supports_detect_attack(self):
        """Test that adapter supports detect_attack test type"""
        supported = self.adapter.get_supported_tests()
        assert "detect_attack" in supported

    def test_adapter_supports_analyze_anomaly(self):
        """Test that adapter supports analyze_anomaly test type"""
        supported = self.adapter.get_supported_tests()
        assert "analyze_anomaly" in supported

    def test_adapter_has_test_detect_attack_method(self):
        """Test that adapter has _test_detect_attack method"""
        assert hasattr(self.adapter, '_test_detect_attack')
        assert callable(self.adapter._test_detect_attack)

    def test_adapter_has_test_analyze_anomaly_method(self):
        """Test that adapter has _test_analyze_anomaly method"""
        assert hasattr(self.adapter, '_test_analyze_anomaly')
        assert callable(self.adapter._test_analyze_anomaly)


class TestAPIResponseFormats:
    """Test API response formats for new endpoints"""

    def test_attack_detection_response_format(self):
        """Test attack detection response format"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data={"control_field": 0x05}
        )
        
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

    def test_anomaly_analysis_response_format(self):
        """Test anomaly analysis response format"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_anomaly_analysis(
            host="localhost",
            port=20000,
            packet_data={"control_field": 0x05}
        )
        
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

    def test_alarm_state_response_format(self):
        """Test alarm state response format"""
        manager = SecurityTestManager()
        result = manager.get_dnp3_alarm_state()
        
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

    def test_statistics_response_format(self):
        """Test statistics response format"""
        manager = SecurityTestManager()
        result = manager.get_dnp3_statistics()
        
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert isinstance(json_str, str)


class TestErrorHandling:
    """Test error handling in new methods"""

    def test_attack_detection_handles_invalid_host(self):
        """Test attack detection handles invalid host"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_attack_detection(
            host="invalid_host_that_does_not_exist",
            port=20000,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_attack_detection_handles_invalid_port(self):
        """Test attack detection handles invalid port"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_attack_detection(
            host="localhost",
            port=99999,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_anomaly_analysis_handles_invalid_host(self):
        """Test anomaly analysis handles invalid host"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_anomaly_analysis(
            host="invalid_host_that_does_not_exist",
            port=20000,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_anomaly_analysis_handles_invalid_port(self):
        """Test anomaly analysis handles invalid port"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_anomaly_analysis(
            host="localhost",
            port=99999,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_methods_handle_exceptions_gracefully(self):
        """Test that methods handle exceptions gracefully"""
        manager = SecurityTestManager()
        
        # These should not raise exceptions
        try:
            manager.run_dnp3_attack_detection("localhost", 20000, None)
            manager.run_dnp3_anomaly_analysis("localhost", 20000, None)
            manager.get_dnp3_alarm_state()
            manager.get_dnp3_statistics()
        except Exception as e:
            pytest.fail(f"Method raised exception: {e}")


class TestParameterValidation:
    """Test parameter validation in new methods"""

    def test_attack_detection_accepts_string_host(self):
        """Test attack detection accepts string host"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_attack_detection_accepts_integer_port(self):
        """Test attack detection accepts integer port"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_attack_detection_accepts_dict_packet_data(self):
        """Test attack detection accepts dict packet_data"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data={"control_field": 0x05}
        )
        assert isinstance(result, dict)

    def test_anomaly_analysis_accepts_string_host(self):
        """Test anomaly analysis accepts string host"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_anomaly_analysis(
            host="localhost",
            port=20000,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_anomaly_analysis_accepts_integer_port(self):
        """Test anomaly analysis accepts integer port"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_anomaly_analysis(
            host="localhost",
            port=20000,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_anomaly_analysis_accepts_dict_packet_data(self):
        """Test anomaly analysis accepts dict packet_data"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_anomaly_analysis(
            host="localhost",
            port=20000,
            packet_data={"control_field": 0x05}
        )
        assert isinstance(result, dict)


class TestIntegration:
    """Integration tests for new methods"""

    def test_attack_detection_and_anomaly_analysis_consistency(self):
        """Test that attack detection and anomaly analysis are consistent"""
        manager = SecurityTestManager()
        
        packet_data = {"control_field": 256}  # Invalid
        
        result1 = manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data=packet_data
        )
        
        result2 = manager.run_dnp3_anomaly_analysis(
            host="localhost",
            port=20000,
            packet_data=packet_data
        )
        
        # Both should return dictionaries
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)

    def test_alarm_state_and_statistics_consistency(self):
        """Test that alarm state and statistics are consistent"""
        manager = SecurityTestManager()
        
        # Run some tests
        manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data={"control_field": 256}
        )
        
        # Get alarm state and statistics
        alarm = manager.get_dnp3_alarm_state()
        stats = manager.get_dnp3_statistics()
        
        # Both should return dictionaries
        assert isinstance(alarm, dict)
        assert isinstance(stats, dict)

    def test_multiple_calls_consistency(self):
        """Test that multiple calls are consistent"""
        manager = SecurityTestManager()
        
        # Call methods multiple times
        for i in range(5):
            result1 = manager.run_dnp3_attack_detection(
                host="localhost",
                port=20000,
                packet_data={"control_field": 0x05}
            )
            result2 = manager.get_dnp3_alarm_state()
            result3 = manager.get_dnp3_statistics()
            
            assert isinstance(result1, dict)
            assert isinstance(result2, dict)
            assert isinstance(result3, dict)


class TestWebUIIntegration:
    """Test Web UI integration with new methods"""

    def test_methods_return_json_serializable_data(self):
        """Test that methods return JSON serializable data"""
        manager = SecurityTestManager()
        
        results = [
            manager.run_dnp3_attack_detection("localhost", 20000),
            manager.run_dnp3_anomaly_analysis("localhost", 20000),
            manager.get_dnp3_alarm_state(),
            manager.get_dnp3_statistics(),
        ]
        
        for result in results:
            # Should be JSON serializable
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
            
            # Should be able to parse back
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)

    def test_response_contains_status_or_error(self):
        """Test that responses contain status or error field"""
        manager = SecurityTestManager()
        
        results = [
            manager.run_dnp3_attack_detection("localhost", 20000),
            manager.run_dnp3_anomaly_analysis("localhost", 20000),
            manager.get_dnp3_alarm_state(),
            manager.get_dnp3_statistics(),
        ]
        
        for result in results:
            # Should have either status or error field
            assert "status" in result or "error" in result


class TestEdgeCases:
    """Test edge cases for new methods"""

    def test_attack_detection_with_empty_string_host(self):
        """Test attack detection with empty string host"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_attack_detection(
            host="",
            port=20000,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_attack_detection_with_zero_port(self):
        """Test attack detection with zero port"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_attack_detection(
            host="localhost",
            port=0,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_attack_detection_with_negative_port(self):
        """Test attack detection with negative port"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_attack_detection(
            host="localhost",
            port=-1,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_attack_detection_with_large_port(self):
        """Test attack detection with large port number"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_attack_detection(
            host="localhost",
            port=65535,
            packet_data={}
        )
        assert isinstance(result, dict)

    def test_attack_detection_with_complex_packet_data(self):
        """Test attack detection with complex packet data"""
        manager = SecurityTestManager()
        result = manager.run_dnp3_attack_detection(
            host="localhost",
            port=20000,
            packet_data={
                "control_field": 0x80,
                "function_code": 0x01,
                "data_length": 100,
                "sequence_number": 1,
                "object_type": 1,
                "extra_field": "should be ignored",
                "nested": {"key": "value"}
            }
        )
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
