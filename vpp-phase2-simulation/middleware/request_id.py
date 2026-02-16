"""
Request ID middleware for VPP Phase 2 Simulation Framework.

Generates and tracks unique request IDs across all operations for request tracing
and correlation in logs and metrics.
"""

from bottle import request, response
from uuid import uuid4
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


def add_request_id(app: Any) -> Any:
    """
    Middleware to add request ID to all requests.

    Generates a unique request ID for each request and adds it to the request
    context. The request ID is included in all logs and responses.

    Args:
        app: Bottle application instance

    Returns:
        Wrapped Bottle application with request ID middleware
    """
    def middleware(callback: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate or retrieve request ID
            request_id = request.headers.get("X-Request-ID")
            if not request_id:
                request_id = str(uuid4())

            # Store request ID in request context
            request.request_id = request_id

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log request start
            logger.debug(
                f"Request started",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path
                }
            )

            try:
                # Call the actual route handler
                result = callback(*args, **kwargs)
                return result
            finally:
                # Log request end
                logger.debug(
                    f"Request completed",
                    extra={
                        "request_id": request_id,
                        "status": response.status
                    }
                )

        return wrapper

    app.install(middleware)
    return app


def get_request_id() -> str:
    """
    Get the current request ID from the request context.

    Returns:
        Current request ID or a new UUID if not in request context

    Raises:
        RuntimeError: If called outside of request context
    """
    try:
        return request.request_id
    except (AttributeError, RuntimeError):
        # Not in request context, generate a new ID
        return str(uuid4())
