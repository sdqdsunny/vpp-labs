"""
Error Handling Tests

Tests for error handling middleware and error response formatting.
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
    DuplicateDeviceError, DispatchExecutionError, AuthenticationError,
    AuthorizationError, RateLimitError, DatabaseError, ServiceUnavailableError
)
from middleware.error_handler import ErrorHandler
from middleware.request_validator import RequestValidator


class TestErrorResponseFormatting:
    """Test error response formatting"""
    
    def test_format_validation_error(self):
        """Test formatting validation error"""
        response, status = ErrorHandler.handle_vpp_exception(
            ValidationError("Invalid input"),
            "req-123"
        )
        
        data = json.loads(response)
        assert data["error"]["code"] == "INVALID_REQUEST"
        assert data["error"]["message"] == "Invalid input"
        assert data["error"]["request_id"] == "req-123"
        assert status == 400
    
    def test_format_device_not_found_error(self):
        """Test formatting device not found error"""
        response, status = ErrorHandler.handle_vpp_exception(
            DeviceNotFoundError("Device not found"),
            "req-124"
        )
        
        data = json.loads(response)
        assert data["error"]["code"] == "NOT_FOUND"
        assert status == 404
    
    def test_format_duplicate_device_error(self):
        """Test formatting duplicate device error"""
        response, status = ErrorHandler.handle_vpp_exception(
            DuplicateDeviceError("Device already exists"),
            "req-125"
        )
        
        data = json.loads(response)
        assert data["error"]["code"] == "CONFLICT"
        assert status == 409
    
    def test_format_dispatch_execution_error(self):
        """Test formatting dispatch execution error"""
        response, status = ErrorHandler.handle_vpp_exception(
            DispatchExecutionError("Dispatch failed"),
            "req-126"
        )
        
        data = json.loads(response)
        assert data["error"]["code"] == "DISPATCH_FAILED"
        assert status == 422
    
    def test_format_authentication_error(self):
        """Test formatting authentication error"""
        response, status = ErrorHandler.handle_vpp_exception(
            AuthenticationError("Invalid credentials"),
            "req-127"
        )
        
        data = json.loads(response)
        assert data["error"]["code"] == "UNAUTHORIZED"
        assert status == 401
    
    def test_format_authorization_error(self):
        """Test formatting authorization error"""
        response, status = ErrorHandler.handle_vpp_exception(
            AuthorizationError("Access denied"),
            "req-128"
        )
        
        data = json.loads(response)
        assert data["error"]["code"] == "FORBIDDEN"
        assert status == 403
    
    def test_format_rate_limit_error(self):
        """Test formatting rate limit error"""
        response, status = ErrorHandler.handle_vpp_exception(
            RateLimitError("Rate limit exceeded"),
            "req-129"
        )
        
        data = json.loads(response)
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert status == 429
    
    def test_format_database_error(self):
        """Test formatting database error"""
        response, status = ErrorHandler.handle_vpp_exception(
            DatabaseError("Database connection failed"),
            "req-130"
        )
        
        data = json.loads(response)
        assert data["error"]["code"] == "DATABASE_ERROR"
        assert status == 500
    
    def test_format_service_unavailable_error(self):
        """Test formatting service unavailable error"""
        response, status = ErrorHandler.handle_vpp_exception(
            ServiceUnavailableError("Service temporarily unavailable"),
            "req-131"
        )
        
        data = json.loads(response)
        assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert status == 503
    
    def test_error_response_includes_timestamp(self):
        """Test that error response includes timestamp"""
        response, status = ErrorHandler.handle_vpp_exception(
            ValidationError("Test error"),
            "req-132"
        )
        
        data = json.loads(response)
        assert "timestamp" in data["error"]
        # Verify timestamp is ISO format
        datetime.fromisoformat(data["error"]["timestamp"])
    
    def test_error_response_includes_details(self):
        """Test that error response includes details"""
        exc = ValidationError(
            "Validation failed",
            details={"field": "value", "error": "invalid"}
        )
        response, status = ErrorHandler.handle_vpp_exception(exc, "req-133")
        
        data = json.loads(response)
        assert data["error"]["details"]["field"] == "value"
        assert data["error"]["details"]["error"] == "invalid"


class TestRequestValidation:
    """Test request validation"""
    
    def test_validate_required_fields_success(self):
        """Test validating required fields - success case"""
        data = {"name": "test", "value": 100}
        # Should not raise
        RequestValidator.validate_required_fields(data, ["name", "value"])
    
    def test_validate_required_fields_missing(self):
        """Test validating required fields - missing field"""
        data = {"name": "test"}
        
        with pytest.raises(ValidationError) as exc_info:
            RequestValidator.validate_required_fields(data, ["name", "value"])
        
        assert exc_info.value.error_code == "INVALID_REQUEST"
        assert "value" in exc_info.value.details["missing_fields"]
    
    def test_validate_required_fields_none_value(self):
        """Test validating required fields - None value"""
        data = {"name": "test", "value": None}
        
        with pytest.raises(ValidationError) as exc_info:
            RequestValidator.validate_required_fields(data, ["name", "value"])
        
        assert "value" in exc_info.value.details["missing_fields"]
    
    def test_validate_field_types_success(self):
        """Test validating field types - success case"""
        data = {"name": "test", "count": 100, "active": True}
        # Should not raise
        RequestValidator.validate_field_types(
            data,
            {"name": str, "count": int, "active": bool}
        )
    
    def test_validate_field_types_invalid(self):
        """Test validating field types - invalid type"""
        data = {"name": "test", "count": "not_a_number"}
        
        with pytest.raises(ValidationError) as exc_info:
            RequestValidator.validate_field_types(
                data,
                {"name": str, "count": int}
            )
        
        assert "count" in exc_info.value.details
        assert "int" in exc_info.value.details["count"]
    
    def test_validate_field_types_missing_field(self):
        """Test validating field types - missing field (should not raise)"""
        data = {"name": "test"}
        # Should not raise for missing fields
        RequestValidator.validate_field_types(
            data,
            {"name": str, "count": int}
        )
    
    def test_validate_field_types_none_value(self):
        """Test validating field types - None value (should not raise)"""
        data = {"name": "test", "count": None}
        # Should not raise for None values
        RequestValidator.validate_field_types(
            data,
            {"name": str, "count": int}
        )


class TestErrorCodes:
    """Test error code mapping"""
    
    def test_validation_error_code(self):
        """Test validation error code"""
        exc = ValidationError("Test")
        assert exc.error_code == "INVALID_REQUEST"
        assert exc.http_status == 400
    
    def test_device_not_found_error_code(self):
        """Test device not found error code"""
        exc = DeviceNotFoundError("Test")
        assert exc.error_code == "NOT_FOUND"
        assert exc.http_status == 404
    
    def test_duplicate_device_error_code(self):
        """Test duplicate device error code"""
        exc = DuplicateDeviceError("Test")
        assert exc.error_code == "CONFLICT"
        assert exc.http_status == 409
    
    def test_dispatch_execution_error_code(self):
        """Test dispatch execution error code"""
        exc = DispatchExecutionError("Test")
        assert exc.error_code == "DISPATCH_FAILED"
        assert exc.http_status == 422
    
    def test_authentication_error_code(self):
        """Test authentication error code"""
        exc = AuthenticationError("Test")
        assert exc.error_code == "UNAUTHORIZED"
        assert exc.http_status == 401
    
    def test_authorization_error_code(self):
        """Test authorization error code"""
        exc = AuthorizationError("Test")
        assert exc.error_code == "FORBIDDEN"
        assert exc.http_status == 403
    
    def test_rate_limit_error_code(self):
        """Test rate limit error code"""
        exc = RateLimitError("Test")
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.http_status == 429
    
    def test_database_error_code(self):
        """Test database error code"""
        exc = DatabaseError("Test")
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.http_status == 500
    
    def test_service_unavailable_error_code(self):
        """Test service unavailable error code"""
        exc = ServiceUnavailableError("Test")
        assert exc.error_code == "SERVICE_UNAVAILABLE"
        assert exc.http_status == 503


class TestErrorDetails:
    """Test error details"""
    
    def test_error_with_details(self):
        """Test error with additional details"""
        exc = ValidationError(
            "Validation failed",
            details={"field1": "error1", "field2": "error2"}
        )
        
        assert exc.details["field1"] == "error1"
        assert exc.details["field2"] == "error2"
    
    def test_error_without_details(self):
        """Test error without details"""
        exc = ValidationError("Validation failed")
        assert exc.details == {}
    
    def test_error_details_in_response(self):
        """Test error details appear in response"""
        exc = ValidationError(
            "Validation failed",
            details={"field": "value"}
        )
        response, status = ErrorHandler.handle_vpp_exception(exc, "req-134")
        
        data = json.loads(response)
        assert data["error"]["details"]["field"] == "value"


class TestErrorInheritance:
    """Test error inheritance"""
    
    def test_all_errors_inherit_from_vpp_exception(self):
        """Test that all errors inherit from VPPException"""
        errors = [
            ValidationError("Test"),
            DeviceNotFoundError("Test"),
            DuplicateDeviceError("Test"),
            DispatchExecutionError("Test"),
            AuthenticationError("Test"),
            AuthorizationError("Test"),
            RateLimitError("Test"),
            DatabaseError("Test"),
            ServiceUnavailableError("Test")
        ]
        
        for error in errors:
            assert isinstance(error, VPPException)
    
    def test_error_attributes(self):
        """Test that all errors have required attributes"""
        exc = ValidationError("Test message")
        
        assert hasattr(exc, 'message')
        assert hasattr(exc, 'error_code')
        assert hasattr(exc, 'http_status')
        assert hasattr(exc, 'details')
        
        assert exc.message == "Test message"
        assert isinstance(exc.error_code, str)
        assert isinstance(exc.http_status, int)
        assert isinstance(exc.details, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
