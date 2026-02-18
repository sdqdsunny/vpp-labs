"""
Load Manager Service - Demand-side management.

Manages:
- Load forecasting
- Demand response
- Load balancing
"""

import logging
import json
from bottle import Bottle, request, response
from uuid import uuid4

from config import config
from utils.logger import setup_logging
from utils.structured_logger import get_structured_logger
from utils.database import init_db, get_session
from middleware.error_handler import error_handler, format_error_response, log_error
from middleware.request_logger import add_request_id

# Setup logging
logger = setup_logging(
    log_level=config.LOG_LEVEL,
    log_file=config.LOG_FILE,
    log_format=config.LOG_FORMAT
)

# Create Bottle app
app = Bottle()

# Apply middleware
app = error_handler(app)
app = add_request_id(app)


@app.hook("before_request")
def before_request():
    """Before request hook."""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.request_id = request_id
    request.db = get_session()
    
    # Create structured logger for this request
    struct_logger = get_structured_logger("vpp_load_manager.request", request_id)
    request.logger = struct_logger
    
    # Log request start
    struct_logger.info(
        "Request started",
        method=request.method,
        path=request.path,
        tags={"component": "load_manager", "operation": "start"}
    )


@app.hook("after_request")
def after_request():
    """After request hook."""
    if hasattr(request, "db"):
        request.db.close()
    
    # Log request completion with structured logging
    if hasattr(request, "logger"):
        request.logger.info(
            "Request completed",
            status=response.status,
            tags={"component": "load_manager", "operation": "complete"}
        )


@app.route("/health", method="GET")
def health_check():
    """Health check endpoint."""
    response.content_type = "application/json"
    return json.dumps({
        "status": "healthy",
        "service": "load_manager",
        "version": "0.1.0",
        "environment": config.ENV
    })


@app.route("/ready", method="GET")
def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check database connection
        from sqlalchemy import text
        session = get_session()
        session.execute(text("SELECT 1"))
        session.close()
        
        response.content_type = "application/json"
        return json.dumps({
            "status": "ready",
            "service": "load_manager",
            "database": "connected"
        })
    except Exception as e:
        response.status = 503
        response.content_type = "application/json"
        return json.dumps({
            "status": "not_ready",
            "service": "load_manager",
            "error": str(e)
        })


@app.route("/load/status", method="GET")
def load_status():
    """Get current load status."""
    response.content_type = "application/json"
    return json.dumps({
        "service": "load_manager",
        "current_load": 0.0,
        "forecasted_load": 0.0,
        "demand_response": 0.0,
        "status": "operational"
    })


@app.error(500)
def error_500(err):
    """Handle 500 errors."""
    request_id = getattr(request, "request_id", str(uuid4()))
    error_dict, status = format_error_response(err, request_id, 500)
    log_error(err, request_id)
    
    response.content_type = "application/json"
    response.status = status
    return json.dumps(error_dict)


def create_app():
    """
    Create and configure the Load Manager Service application.

    Returns:
        Configured Bottle app instance
    """
    # Initialize database
    init_db()
    
    logger.info("VPP Load Manager Service initialized")
    
    return app


if __name__ == "__main__":
    app = create_app()
    logger.info(f"Starting Load Manager Service on {config.API_HOST}:{config.API_PORT}")
    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.DEBUG,
        workers=config.API_WORKERS
    )
