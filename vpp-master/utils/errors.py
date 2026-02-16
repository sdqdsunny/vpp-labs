"""
Custom Exception Classes for VPP Master

Defines the exception hierarchy for all VPP errors with consistent error codes
and HTTP status mappings.
"""

from typing import Optional, Dict, Any


class VPPException(Exception):
    """Base exception for all VPP errors"""
    
    error_code: str = "INTERNAL_ERROR"
    http_status: int = 500
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        http_status: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize VPP exception
        
        Args:
            message: Error message
            error_code: Error code (overrides class default)
            http_status: HTTP status code (overrides class default)
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code or self.error_code
        self.http_status = http_status or self.http_status
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(VPPException):
    """Data validation failed"""
    
    error_code = "INVALID_REQUEST"
    http_status = 400


class DeviceNotFoundError(VPPException):
    """Device not found"""
    
    error_code = "NOT_FOUND"
    http_status = 404


class DuplicateDeviceError(VPPException):
    """Device with duplicate ID already exists"""
    
    error_code = "CONFLICT"
    http_status = 409


class DispatchExecutionError(VPPException):
    """Dispatch execution failed"""
    
    error_code = "DISPATCH_FAILED"
    http_status = 422


class ProtocolConversionError(VPPException):
    """Protocol conversion failed"""
    
    error_code = "PROTOCOL_ERROR"
    http_status = 422


class AnalysisError(VPPException):
    """Analysis execution failed"""
    
    error_code = "ANALYSIS_FAILED"
    http_status = 422


class AuthenticationError(VPPException):
    """Authentication failed"""
    
    error_code = "UNAUTHORIZED"
    http_status = 401


class AuthorizationError(VPPException):
    """Authorization failed"""
    
    error_code = "FORBIDDEN"
    http_status = 403


class RateLimitError(VPPException):
    """Rate limit exceeded"""
    
    error_code = "RATE_LIMIT_EXCEEDED"
    http_status = 429


class DatabaseError(VPPException):
    """Database operation failed"""
    
    error_code = "DATABASE_ERROR"
    http_status = 500


class ServiceUnavailableError(VPPException):
    """Service temporarily unavailable"""
    
    error_code = "SERVICE_UNAVAILABLE"
    http_status = 503
