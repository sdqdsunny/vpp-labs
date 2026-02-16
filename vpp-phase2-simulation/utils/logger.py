"""
Structured logging configuration for VPP Phase 2 Simulation Framework.

Provides JSON-formatted logging with request tracking and performance metrics.
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "scenario_id"):
            log_data["scenario_id"] = record.scenario_id
        if hasattr(record, "device_id"):
            log_data["device_id"] = record.device_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = "json"
) -> logging.Logger:
    """
    Set up structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        log_format: Log format (json or standard)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("vpp_phase2_sim")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class RequestLogger:
    """Context manager for request-scoped logging."""

    def __init__(self, logger: logging.Logger, request_id: Optional[str] = None):
        """
        Initialize request logger.

        Args:
            logger: Logger instance
            request_id: Optional request ID (generated if not provided)
        """
        self.logger = logger
        self.request_id = request_id or str(uuid4())

    def __enter__(self) -> "RequestLogger":
        """Enter context."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context."""
        pass

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with request context."""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            "(unknown file)",
            0,
            message,
            (),
            None
        )
        record.request_id = self.request_id
        for key, value in kwargs.items():
            setattr(record, key, value)
        self.logger.handle(record)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with request context."""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.DEBUG,
            "(unknown file)",
            0,
            message,
            (),
            None
        )
        record.request_id = self.request_id
        for key, value in kwargs.items():
            setattr(record, key, value)
        self.logger.handle(record)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with request context."""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.ERROR,
            "(unknown file)",
            0,
            message,
            (),
            None
        )
        record.request_id = self.request_id
        for key, value in kwargs.items():
            setattr(record, key, value)
        self.logger.handle(record)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with request context."""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.WARNING,
            "(unknown file)",
            0,
            message,
            (),
            None
        )
        record.request_id = self.request_id
        for key, value in kwargs.items():
            setattr(record, key, value)
        self.logger.handle(record)


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
