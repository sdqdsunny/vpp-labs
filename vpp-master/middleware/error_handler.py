"""
Error Handling Middleware

Provides consistent error response formatting and error tracking for all API endpoints.
"""

import json
import uuid
from typing import Dict, Any, Optional
from bottle import request, response
from utils.errors import VPPException
from utils.logger import setup_logger
from utils.metrics import record_api_error

logger = setup_logger(__name__)


class ErrorHandler:
    """Handles error responses and formatting"""
    
    @staticmethod
    def format_error_response(
        error_code: str,
        message: str,
        http_status: int,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format error response in consistent JSON structure
        
        Args:
            error_code: Error code identifier
            message: Error message
            http_status: HTTP status code
            details: Additional error details
            request_id: Request ID for tracking
        
        Returns:
            Formatted error response dictionary
        """
        from datetime import datetime, timezone
        
        return {
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {},
                "request_id": request_id or str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    @staticmethod
    def handle_vpp_exception(exc: VPPException, request_id: str) -> tuple:
        """
        Handle VPP exceptions
        
        Args:
            exc: VPP exception instance
            request_id: Request ID for tracking
        
        Returns:
            Tuple of (response_body, http_status)
        """
        logger.warning(
            f"VPP Exception: {exc.error_code}",
            extra={
                "error_code": exc.error_code,
                "error_message": exc.message,
                "request_id": request_id,
                "details": exc.details
            }
        )
        
        record_api_error(exc.error_code)
        
        error_response = ErrorHandler.format_error_response(
            error_code=exc.error_code,
            message=exc.message,
            http_status=exc.http_status,
            details=exc.details,
            request_id=request_id
        )
        
        return json.dumps(error_response), exc.http_status
    
    @staticmethod
    def handle_validation_error(error: Exception, request_id: str) -> tuple:
        """
        Handle Pydantic validation errors
        
        Args:
            error: Validation error
            request_id: Request ID for tracking
        
        Returns:
            Tuple of (response_body, http_status)
        """
        logger.warning(
            f"Validation Error: {str(error)}",
            extra={
                "error_code": "INVALID_REQUEST",
                "request_id": request_id
            }
        )
        
        record_api_error("INVALID_REQUEST")
        
        # Extract validation details from Pydantic error
        error_details = {}
        if hasattr(error, 'errors'):
            for err in error.errors():
                field = '.'.join(str(x) for x in err['loc'])
                error_details[field] = err['msg']
        
        error_response = ErrorHandler.format_error_response(
            error_code="INVALID_REQUEST",
            message="Request validation failed",
            http_status=400,
            details=error_details,
            request_id=request_id
        )
        
        return json.dumps(error_response), 400
    
    @staticmethod
    def handle_generic_error(error: Exception, request_id: str) -> tuple:
        """
        Handle generic exceptions
        
        Args:
            error: Exception instance
            request_id: Request ID for tracking
        
        Returns:
            Tuple of (response_body, http_status)
        """
        logger.error(
            f"Internal Server Error: {str(error)}",
            extra={
                "error_code": "INTERNAL_ERROR",
                "request_id": request_id,
                "exception": str(error)
            },
            exc_info=True
        )
        
        record_api_error("INTERNAL_ERROR")
        
        error_response = ErrorHandler.format_error_response(
            error_code="INTERNAL_ERROR",
            message="Internal server error",
            http_status=500,
            details={"error_id": request_id},
            request_id=request_id
        )
        
        return json.dumps(error_response), 500


def setup_error_handling(app):
    """
    Setup error handling for Bottle app
    
    Args:
        app: Bottle application instance
    """
    
    @app.hook('before_request')
    def before_request_error_handling():
        """Generate request ID before request"""
        request.request_id = str(uuid.uuid4())
    
    @app.error(400)
    def error_400(err):
        """Handle 400 Bad Request"""
        response.content_type = 'application/json'
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        error_response = ErrorHandler.format_error_response(
            error_code="INVALID_REQUEST",
            message="Bad request",
            http_status=400,
            request_id=request_id
        )
        return json.dumps(error_response)
    
    @app.error(401)
    def error_401(err):
        """Handle 401 Unauthorized"""
        response.content_type = 'application/json'
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        error_response = ErrorHandler.format_error_response(
            error_code="UNAUTHORIZED",
            message="Unauthorized",
            http_status=401,
            request_id=request_id
        )
        return json.dumps(error_response)
    
    @app.error(403)
    def error_403(err):
        """Handle 403 Forbidden"""
        response.content_type = 'application/json'
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        error_response = ErrorHandler.format_error_response(
            error_code="FORBIDDEN",
            message="Forbidden",
            http_status=403,
            request_id=request_id
        )
        return json.dumps(error_response)
    
    @app.error(404)
    def error_404(err):
        """Handle 404 Not Found"""
        response.content_type = 'application/json'
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        error_response = ErrorHandler.format_error_response(
            error_code="NOT_FOUND",
            message="Resource not found",
            http_status=404,
            details={"path": request.path},
            request_id=request_id
        )
        return json.dumps(error_response)
    
    @app.error(429)
    def error_429(err):
        """Handle 429 Too Many Requests"""
        response.content_type = 'application/json'
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        error_response = ErrorHandler.format_error_response(
            error_code="RATE_LIMIT_EXCEEDED",
            message="Rate limit exceeded",
            http_status=429,
            request_id=request_id
        )
        return json.dumps(error_response)
    
    @app.error(500)
    def error_500(err):
        """Handle 500 Internal Server Error"""
        response.content_type = 'application/json'
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        logger.error(f"Internal server error: {err}", extra={"request_id": request_id})
        error_response = ErrorHandler.format_error_response(
            error_code="INTERNAL_ERROR",
            message="Internal server error",
            http_status=500,
            details={"error_id": request_id},
            request_id=request_id
        )
        return json.dumps(error_response)
    
    @app.error(503)
    def error_503(err):
        """Handle 503 Service Unavailable"""
        response.content_type = 'application/json'
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        error_response = ErrorHandler.format_error_response(
            error_code="SERVICE_UNAVAILABLE",
            message="Service temporarily unavailable",
            http_status=503,
            request_id=request_id
        )
        return json.dumps(error_response)
