"""
Error handling middleware for VPP Phase 2 Simulation Framework.

Provides consistent error response formatting and exception handling.
"""

import json
import logging
from typing import Any, Dict, Tuple
from uuid import uuid4

from bottle import request, response
from utils.errors import SimulationException

logger = logging.getLogger(__name__)


def error_handler(app):
    """
    Decorator to add error handling to Bottle app.

    Args:
        app: Bottle application instance

    Returns:
        Decorated app
    """

    @app.error(400)
    @app.error(404)
    @app.error(500)
    def handle_error(err):
        """Handle HTTP errors."""
        request_id = getattr(request, "request_id", str(uuid4()))
        
        error_response = {
            "error": {
                "code": "HTTP_ERROR",
                "message": err.body or str(err.status),
                "status": err.status_code,
                "request_id": request_id,
            }
        }

        response.content_type = "application/json"
        response.status = err.status_code
        return json.dumps(error_response)

    return app


def format_error_response(
    exception: Exception,
    request_id: str,
    status_code: int = 500
) -> Tuple[Dict[str, Any], int]:
    """
    Format exception as error response.

    Args:
        exception: Exception instance
        request_id: Request ID for tracking
        status_code: HTTP status code

    Returns:
        Tuple of (error_dict, status_code)
    """
    if isinstance(exception, SimulationException):
        error_dict = {
            "error": {
                "code": exception.code,
                "message": exception.message,
                "details": exception.details,
                "request_id": request_id,
            }
        }
        # Map error codes to HTTP status codes
        status_map = {
            "VALIDATION_ERROR": 400,
            "SIMULATOR_ERROR": 422,
            "SCENARIO_EXECUTION_ERROR": 422,
            "POWER_FLOW_ERROR": 422,
            "COMMUNICATION_ERROR": 422,
            "DATABASE_ERROR": 500,
            "CONFIGURATION_ERROR": 500,
            "TIMEOUT_ERROR": 504,
        }
        status_code = status_map.get(exception.code, 500)
    else:
        error_dict = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exception),
                "request_id": request_id,
            }
        }
        status_code = 500

    return error_dict, status_code


def log_error(
    exception: Exception,
    request_id: str,
    context: Dict[str, Any] = None
) -> None:
    """
    Log error with context.

    Args:
        exception: Exception instance
        request_id: Request ID for tracking
        context: Additional context information
    """
    context = context or {}
    
    log_data = {
        "request_id": request_id,
        "error_type": type(exception).__name__,
        "error_message": str(exception),
        **context
    }

    if isinstance(exception, SimulationException):
        logger.error(f"Simulation error: {exception.message}", extra=log_data)
    else:
        logger.exception(f"Unexpected error: {str(exception)}", extra=log_data)
