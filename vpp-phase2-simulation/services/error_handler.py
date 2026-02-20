"""
Global Error Handler Service.

Implements:
- Global exception handling
- Error logging
- Standard error response format
"""

import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCode(str, Enum):
    """Standard error codes."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ErrorResponse:
    """Standard error response format."""

    def __init__(self, 
                 error_code: str,
                 message: str,
                 severity: str = ErrorSeverity.ERROR.value,
                 details: Optional[Dict[str, Any]] = None,
                 request_id: Optional[str] = None):
        """
        Initialize error response.
        
        Args:
            error_code: Error code
            message: Error message
            severity: Error severity level
            details: Additional error details
            request_id: Request ID for tracking
        """
        self.error_code = error_code
        self.message = message
        self.severity = severity
        self.details = details or {}
        self.request_id = request_id
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity,
            "details": self.details,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict())


class ErrorHandler:
    """Global error handler service."""

    def __init__(self):
        """Initialize error handler."""
        self.error_count = 0
        self.error_by_code: Dict[str, int] = {}
        self.error_by_severity: Dict[str, int] = {}
        self.last_error: Optional[ErrorResponse] = None

    def handle_exception(self,
                        exception: Exception,
                        error_code: str = ErrorCode.UNKNOWN_ERROR.value,
                        severity: str = ErrorSeverity.ERROR.value,
                        request_id: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None) -> ErrorResponse:
        """
        Handle an exception and create error response.
        
        Args:
            exception: Exception to handle
            error_code: Error code
            severity: Error severity
            request_id: Request ID for tracking
            context: Additional context information
            
        Returns:
            ErrorResponse object
        """
        try:
            # Extract error message
            error_message = str(exception)
            if not error_message:
                error_message = exception.__class__.__name__
            
            # Create error response
            details = context or {}
            details['exception_type'] = exception.__class__.__name__
            details['traceback'] = traceback.format_exc()
            
            error_response = ErrorResponse(
                error_code=error_code,
                message=error_message,
                severity=severity,
                details=details,
                request_id=request_id
            )
            
            # Update statistics
            self._update_stats(error_code, severity)
            self.last_error = error_response
            
            # Log error
            self._log_error(error_response)
            
            return error_response
            
        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}")
            # Return a generic error response
            return ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR.value,
                message="Error handling failed",
                severity=ErrorSeverity.CRITICAL.value,
                request_id=request_id
            )

    def handle_validation_error(self,
                               message: str,
                               request_id: Optional[str] = None,
                               details: Optional[Dict[str, Any]] = None) -> ErrorResponse:
        """
        Handle validation error.
        
        Args:
            message: Error message
            request_id: Request ID
            details: Additional details
            
        Returns:
            ErrorResponse object
        """
        error_response = ErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR.value,
            message=message,
            severity=ErrorSeverity.WARNING.value,
            details=details,
            request_id=request_id
        )
        
        self._update_stats(ErrorCode.VALIDATION_ERROR.value, ErrorSeverity.WARNING.value)
        self.last_error = error_response
        self._log_error(error_response)
        
        return error_response

    def handle_not_found_error(self,
                              resource: str,
                              request_id: Optional[str] = None) -> ErrorResponse:
        """
        Handle not found error.
        
        Args:
            resource: Resource that was not found
            request_id: Request ID
            
        Returns:
            ErrorResponse object
        """
        message = f"{resource} not found"
        error_response = ErrorResponse(
            error_code=ErrorCode.NOT_FOUND.value,
            message=message,
            severity=ErrorSeverity.WARNING.value,
            details={"resource": resource},
            request_id=request_id
        )
        
        self._update_stats(ErrorCode.NOT_FOUND.value, ErrorSeverity.WARNING.value)
        self.last_error = error_response
        self._log_error(error_response)
        
        return error_response

    def handle_timeout_error(self,
                            operation: str,
                            timeout_seconds: int,
                            request_id: Optional[str] = None) -> ErrorResponse:
        """
        Handle timeout error.
        
        Args:
            operation: Operation that timed out
            timeout_seconds: Timeout duration
            request_id: Request ID
            
        Returns:
            ErrorResponse object
        """
        message = f"Operation '{operation}' timed out after {timeout_seconds}s"
        error_response = ErrorResponse(
            error_code=ErrorCode.TIMEOUT_ERROR.value,
            message=message,
            severity=ErrorSeverity.ERROR.value,
            details={"operation": operation, "timeout_seconds": timeout_seconds},
            request_id=request_id
        )
        
        self._update_stats(ErrorCode.TIMEOUT_ERROR.value, ErrorSeverity.ERROR.value)
        self.last_error = error_response
        self._log_error(error_response)
        
        return error_response

    def handle_service_unavailable_error(self,
                                        service: str,
                                        request_id: Optional[str] = None) -> ErrorResponse:
        """
        Handle service unavailable error.
        
        Args:
            service: Service that is unavailable
            request_id: Request ID
            
        Returns:
            ErrorResponse object
        """
        message = f"Service '{service}' is unavailable"
        error_response = ErrorResponse(
            error_code=ErrorCode.SERVICE_UNAVAILABLE.value,
            message=message,
            severity=ErrorSeverity.CRITICAL.value,
            details={"service": service},
            request_id=request_id
        )
        
        self._update_stats(ErrorCode.SERVICE_UNAVAILABLE.value, ErrorSeverity.CRITICAL.value)
        self.last_error = error_response
        self._log_error(error_response)
        
        return error_response

    def _update_stats(self, error_code: str, severity: str):
        """Update error statistics."""
        self.error_count += 1
        self.error_by_code[error_code] = self.error_by_code.get(error_code, 0) + 1
        self.error_by_severity[severity] = self.error_by_severity.get(severity, 0) + 1

    def _log_error(self, error_response: ErrorResponse):
        """Log error response."""
        if error_response.severity == ErrorSeverity.CRITICAL.value:
            logger.critical(f"[{error_response.request_id}] {error_response.error_code}: {error_response.message}")
        elif error_response.severity == ErrorSeverity.ERROR.value:
            logger.error(f"[{error_response.request_id}] {error_response.error_code}: {error_response.message}")
        elif error_response.severity == ErrorSeverity.WARNING.value:
            logger.warning(f"[{error_response.request_id}] {error_response.error_code}: {error_response.message}")
        else:
            logger.info(f"[{error_response.request_id}] {error_response.error_code}: {error_response.message}")

    def get_stats(self) -> dict:
        """
        Get error statistics.
        
        Returns:
            dict: Error statistics
        """
        return {
            "total_errors": self.error_count,
            "errors_by_code": dict(self.error_by_code),
            "errors_by_severity": dict(self.error_by_severity),
            "last_error": self.last_error.to_dict() if self.last_error else None,
        }

    def clear_stats(self):
        """Clear error statistics."""
        self.error_count = 0
        self.error_by_code.clear()
        self.error_by_severity.clear()
        self.last_error = None
        logger.info("Error statistics cleared")


# Global error handler instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def init_error_handler() -> ErrorHandler:
    """Initialize global error handler."""
    global _error_handler
    _error_handler = ErrorHandler()
    return _error_handler
