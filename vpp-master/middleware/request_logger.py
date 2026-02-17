"""
Request Logging Middleware

Provides comprehensive request/response logging with structured JSON format.
"""

import time
import json
from bottle import request, response
from utils.logger import setup_logger
from utils.metrics import record_api_request

logger = setup_logger(__name__)


def setup_request_logging(app):
    """
    Setup request logging for Bottle app
    
    Args:
        app: Bottle application instance
    """
    
    @app.hook('before_request')
    def before_request_logging():
        """Log incoming request"""
        request.start_time = time.time()
        request_id = getattr(request, 'request_id', 'unknown')
        
        # Create a custom logger with request ID
        log_record = logger.makeRecord(
            logger.name,
            logger.level,
            __file__,
            0,
            f"{request.method} {request.path}",
            (),
            None
        )
        log_record.request_id = request_id
        log_record.extra_fields = {
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get('User-Agent', 'unknown'),
            "query_string": request.query_string
        }
        logger.handle(log_record)
    
    @app.hook('after_request')
    def after_request_logging():
        """Log outgoing response"""
        request_id = getattr(request, 'request_id', 'unknown')
        
        # Calculate request duration
        if hasattr(request, 'start_time'):
            duration_ms = (time.time() - request.start_time) * 1000
        else:
            duration_ms = 0
        
        # Get response status
        status_code = response.status_code
        
        # Record metrics
        record_api_request(
            endpoint=request.path,
            method=request.method,
            status=status_code
        )
        
        # Create a custom logger with request ID
        log_record = logger.makeRecord(
            logger.name,
            logger.level,
            __file__,
            0,
            f"{request.method} {request.path} {status_code}",
            (),
            None
        )
        log_record.request_id = request_id
        log_record.extra_fields = {
            "method": request.method,
            "path": request.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "content_length": response.content_length or 0
        }
        logger.handle(log_record)
