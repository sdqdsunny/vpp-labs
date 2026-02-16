"""
Infrastructure Tests

Tests for core infrastructure components including error handling, logging, and metrics.
"""

import pytest
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.errors import (
    VPPException, ValidationError, DeviceNotFoundError, 
    DuplicateDeviceError, DispatchExecutionError
)
from utils.validators import (
    DeviceRegistration, DeviceConfig, DispatchRequest,
    DeviceType, DeviceStatus, DispatchStatus
)
from middleware.error_handler import ErrorHandler
from utils.metrics import (
    api_requests_total, api_errors_total, device_count,
    record_api_request, record_api_error
)


class TestErrorHandling:
    """Test error handling infrastructure"""
    
    def test_vpp_exception_creation(self):
        """Test VPP exception creation"""
        exc = VPPException(
            message="Test error",
            error_code="TEST_ERROR",
            http_status=400,
            details={"field": "value"}
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.http_status == 400
        assert exc.details == {"field": "value"}
    
    def test_validation_error(self):
        """Test validation error"""
        exc = ValidationError("Invalid input")
        assert exc.error_code == "INVALID_REQUEST"
        assert exc.http_status == 400
    
    def test_device_not_found_error(self):
        """Test device not found error"""
        exc = DeviceNotFoundError("Device not found")
        assert exc.error_code == "NOT_FOUND"
        assert exc.http_status == 404
    
    def test_duplicate_device_error(self):
        """Test duplicate device error"""
        exc = DuplicateDeviceError("Device already exists")
        assert exc.error_code == "CONFLICT"
        assert exc.http_status == 409
    
    def test_dispatch_execution_error(self):
        """Test dispatch execution error"""
        exc = DispatchExecutionError("Dispatch failed")
        assert exc.error_code == "DISPATCH_FAILED"
        assert exc.http_status == 422
    
    def test_error_response_formatting(self):
        """Test error response formatting"""
        response = ErrorHandler.format_error_response(
            error_code="TEST_ERROR",
            message="Test message",
            http_status=400,
            details={"field": "value"},
            request_id="req-123"
        )
        
        assert response["error"]["code"] == "TEST_ERROR"
        assert response["error"]["message"] == "Test message"
        assert response["error"]["details"] == {"field": "value"}
        assert response["error"]["request_id"] == "req-123"
        assert "timestamp" in response["error"]


class TestValidators:
    """Test data validators"""
    
    def test_device_registration_valid(self):
        """Test valid device registration"""
        data = {
            "device_id": "device-001",
            "device_type": "solar",
            "location": "Building A",
            "capabilities": {"power": 100}
        }
        
        device = DeviceRegistration(**data)
        assert device.device_id == "device-001"
        assert device.device_type == "solar"
        assert device.location == "Building A"
    
    def test_device_registration_missing_required_field(self):
        """Test device registration with missing required field"""
        data = {
            "device_id": "device-001",
            "device_type": "solar"
            # Missing location
        }
        
        with pytest.raises(ValueError):
            DeviceRegistration(**data)
    
    def test_device_config_valid(self):
        """Test valid device configuration"""
        data = {
            "power_limit": 100.0,
            "mode": "auto",
            "priority_level": 5
        }
        
        config = DeviceConfig(**data)
        assert config.power_limit == 100.0
        assert config.mode == "auto"
        assert config.priority_level == 5
    
    def test_device_config_invalid_priority(self):
        """Test device config with invalid priority"""
        data = {
            "priority_level": 15  # Should be 0-10
        }
        
        with pytest.raises(ValueError):
            DeviceConfig(**data)
    
    def test_dispatch_request_valid(self):
        """Test valid dispatch request"""
        data = {
            "device_id": "device-001",
            "command_type": "power_adjust",
            "target_value": 50.0,
            "priority_level": 5
        }
        
        dispatch = DispatchRequest(**data)
        assert dispatch.device_id == "device-001"
        assert dispatch.command_type == "power_adjust"
        assert dispatch.target_value == 50.0
    
    def test_dispatch_request_missing_required_field(self):
        """Test dispatch request with missing required field"""
        data = {
            "device_id": "device-001",
            "command_type": "power_adjust"
            # Missing target_value
        }
        
        with pytest.raises(ValueError):
            DispatchRequest(**data)


class TestMetrics:
    """Test metrics collection"""
    
    def test_record_api_request(self):
        """Test recording API request"""
        # Get initial count
        initial_count = api_requests_total.labels(
            endpoint="/api/v1/devices",
            method="GET",
            status=200
        )._value.get()
        
        # Record request
        record_api_request("/api/v1/devices", "GET", 200)
        
        # Verify count increased
        new_count = api_requests_total.labels(
            endpoint="/api/v1/devices",
            method="GET",
            status=200
        )._value.get()
        
        assert new_count > initial_count
    
    def test_record_api_error(self):
        """Test recording API error"""
        # Get initial count
        initial_count = api_errors_total.labels(
            error_code="INVALID_REQUEST"
        )._value.get()
        
        # Record error
        record_api_error("INVALID_REQUEST")
        
        # Verify count increased
        new_count = api_errors_total.labels(
            error_code="INVALID_REQUEST"
        )._value.get()
        
        assert new_count > initial_count


class TestEnums:
    """Test enum definitions"""
    
    def test_device_type_enum(self):
        """Test device type enum"""
        assert DeviceType.SOLAR.value == "solar"
        assert DeviceType.WIND.value == "wind"
        assert DeviceType.BATTERY.value == "battery"
        assert DeviceType.LOAD.value == "load"
    
    def test_device_status_enum(self):
        """Test device status enum"""
        assert DeviceStatus.ONLINE.value == "online"
        assert DeviceStatus.OFFLINE.value == "offline"
        assert DeviceStatus.ERROR.value == "error"
    
    def test_dispatch_status_enum(self):
        """Test dispatch status enum"""
        assert DispatchStatus.PENDING.value == "pending"
        assert DispatchStatus.EXECUTING.value == "executing"
        assert DispatchStatus.COMPLETED.value == "completed"
        assert DispatchStatus.FAILED.value == "failed"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
