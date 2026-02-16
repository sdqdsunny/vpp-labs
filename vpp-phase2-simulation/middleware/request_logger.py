"""
Request logging middleware for VPP Phase 2 Simulation Framework.

Logs all requests and responses with request ID tracking.
"""

import logging
import time
from uuid import uuid4
from bottle import request, response

logger = logging.getLogger(__name__)


def add_request_id(app):
    """
    Add request ID to all requests.

    Args:
        app: Bottle application instance

    Returns:
        Decorated app
    """

    @app.hook("before_request")
    def before_request():
        """Add request ID before processing request."""
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.request_id = request_id
        request.start_time = time.time()

    @app.hook("after_request")
    def after_request():
        """Log request after processing."""
        duration_ms = (time.time() - request.start_time) * 1000
        
        log_data = {
            "request_id": request.request_id,
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        }

        logger.info(
            f"{request.method} {request.path} - {response.status_code}",
            extra=log_data
        )

    return app
