"""
Main application entry point for VPP Phase 2 Simulation Framework.

Initializes Bottle.py application with middleware, routes, and database.
"""

import logging
import json
from bottle import Bottle, request, response
from uuid import uuid4

from config import config
from utils.logger import setup_logging, RequestLogger
from utils.structured_logger import get_structured_logger
from utils.database import init_db, get_session
from utils.prometheus_metrics import init_metrics, get_metrics
from utils.swagger_ui import setup_swagger_ui
from middleware.error_handler import error_handler, format_error_response, log_error
from middleware.request_logger import add_request_id
from routes.visualization import create_visualization_routes
from routes.test_dashboard import create_test_dashboard_routes
from routes.phase1_integration import create_phase1_integration_routes
from routes.protocol_analyzer import create_protocol_analyzer_routes

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
    struct_logger = get_structured_logger("vpp_phase2_sim.request", request_id)
    request.logger = struct_logger
    
    # Log request start
    struct_logger.info(
        "Request started",
        method=request.method,
        path=request.path,
        tags={"component": "request_handler", "operation": "start"}
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
            tags={"component": "request_handler", "operation": "complete"}
        )


@app.route("/health", method="GET")
def health_check():
    """Health check endpoint."""
    response.content_type = "application/json"
    return json.dumps({
        "status": "healthy",
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
            "database": "connected"
        })
    except Exception as e:
        response.status = 503
        response.content_type = "application/json"
        return json.dumps({
            "status": "not_ready",
            "error": str(e)
        })


@app.route("/metrics", method="GET")
def metrics_endpoint():
    """Prometheus metrics endpoint."""
    metrics = get_metrics()
    response.content_type = "text/plain; version=0.0.4"
    return metrics.get_metrics()


@app.route("/analyzer", method="GET")
def analyzer_ui():
    """Serve protocol analyzer UI"""
    try:
        with open("static/protocol_analyzer.html", "r", encoding="utf-8") as f:
            response.content_type = "text/html; charset=utf-8"
            return f.read()
    except FileNotFoundError:
        response.status = 404
        return "Protocol Analyzer UI not found"


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
    Create and configure the Bottle application.

    Returns:
        Configured Bottle app instance
    """
    # Initialize database
    init_db()
    
    # Initialize metrics
    init_metrics()
    
    # Setup Swagger UI
    setup_swagger_ui(app)
    
    # Initialize and start Phase 1 Integration Service
    from services.phase1_integration import Phase1IntegrationService
    phase1_service = Phase1IntegrationService()
    phase1_service.start()
    
    # Register routes
    create_visualization_routes(app)
    create_test_dashboard_routes(app)
    create_phase1_integration_routes(app)
    create_protocol_analyzer_routes(app)
    
    logger.info("VPP Phase 2 Simulation Framework initialized")
    logger.info("Phase 1 Integration Service started with automatic synchronization")
    
    return app


if __name__ == "__main__":
    app = create_app()
    logger.info(f"Starting server on {config.API_HOST}:{config.API_PORT}")
    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.DEBUG,
        workers=config.API_WORKERS
    )
