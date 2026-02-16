"""
Enhanced structured logging for VPP Phase 2 Simulation Framework.

Provides comprehensive structured logging with request ID tracking, performance
logging, and error logging with stack traces.
"""

import json
import logging
import logging.handlers
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from uuid import uuid4
from functools import wraps
from contextlib import contextmanager


class StructuredLogger:
    """Enhanced structured logger with request tracking and performance logging."""

    def __init__(self, name: str, request_id: Optional[str] = None):
        """
        Initialize structured logger.

        Args:
            name: Logger name (typically __name__)
            request_id: Optional request ID for tracking
        """
        self.logger = logging.getLogger(name)
        self.request_id = request_id or str(uuid4())
        self.name = name

    def _build_log_data(
        self,
        level: str,
        message: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Build structured log data.

        Args:
            level: Log level
            message: Log message
            **kwargs: Additional fields to include

        Returns:
            Dictionary with structured log data
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger": self.name,
            "message": message,
            "request_id": self.request_id,
        }

        # Add tags if provided
        if "tags" in kwargs:
            log_data["tags"] = kwargs.pop("tags")

        # Add all other kwargs as fields
        log_data.update(kwargs)

        return log_data

    def info(self, message: str, **kwargs: Any) -> None:
        """
        Log info message with structured fields.

        Args:
            message: Log message
            **kwargs: Additional structured fields
        """
        log_data = self._build_log_data("INFO", message, **kwargs)
        self.logger.info(json.dumps(log_data))

    def debug(self, message: str, **kwargs: Any) -> None:
        """
        Log debug message with structured fields.

        Args:
            message: Log message
            **kwargs: Additional structured fields
        """
        log_data = self._build_log_data("DEBUG", message, **kwargs)
        self.logger.debug(json.dumps(log_data))

    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Log warning message with structured fields.

        Args:
            message: Log message
            **kwargs: Additional structured fields
        """
        log_data = self._build_log_data("WARNING", message, **kwargs)
        self.logger.warning(json.dumps(log_data))

    def error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        **kwargs: Any
    ) -> None:
        """
        Log error message with stack trace.

        Args:
            message: Log message
            exception: Optional exception to log
            **kwargs: Additional structured fields
        """
        log_data = self._build_log_data("ERROR", message, **kwargs)

        # Add exception info if provided
        if exception:
            log_data["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exc()
            }

        self.logger.error(json.dumps(log_data))

    def critical(self, message: str, **kwargs: Any) -> None:
        """
        Log critical message with structured fields.

        Args:
            message: Log message
            **kwargs: Additional structured fields
        """
        log_data = self._build_log_data("CRITICAL", message, **kwargs)
        self.logger.critical(json.dumps(log_data))

    @contextmanager
    def performance_context(
        self,
        operation: str,
        threshold_ms: int = 100,
        **context_fields: Any
    ):
        """
        Context manager for performance logging.

        Logs operation duration and alerts if it exceeds threshold.

        Args:
            operation: Operation name
            threshold_ms: Alert threshold in milliseconds
            **context_fields: Additional context fields

        Yields:
            None
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            log_level = "WARNING" if duration_ms > threshold_ms else "DEBUG"

            log_data = self._build_log_data(
                log_level,
                f"Operation completed: {operation}",
                operation=operation,
                duration_ms=round(duration_ms, 2),
                threshold_ms=threshold_ms,
                **context_fields
            )

            if log_level == "WARNING":
                self.logger.warning(json.dumps(log_data))
            else:
                self.logger.debug(json.dumps(log_data))

    def performance_decorator(
        self,
        threshold_ms: int = 100
    ) -> Callable:
        """
        Decorator for performance logging.

        Args:
            threshold_ms: Alert threshold in milliseconds

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    log_level = "WARNING" if duration_ms > threshold_ms else "DEBUG"

                    log_data = self._build_log_data(
                        log_level,
                        f"Function executed: {func.__name__}",
                        function=func.__name__,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=threshold_ms
                    )

                    if log_level == "WARNING":
                        self.logger.warning(json.dumps(log_data))
                    else:
                        self.logger.debug(json.dumps(log_data))

            return wrapper
        return decorator

    def set_request_id(self, request_id: str) -> None:
        """
        Set the request ID for this logger.

        Args:
            request_id: Request ID to set
        """
        self.request_id = request_id


def get_structured_logger(
    name: str,
    request_id: Optional[str] = None
) -> StructuredLogger:
    """
    Get or create a structured logger instance.

    Args:
        name: Logger name (typically __name__)
        request_id: Optional request ID for tracking

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, request_id)


def create_request_logger(request_id: Optional[str] = None) -> StructuredLogger:
    """
    Create a request-scoped structured logger.

    Args:
        request_id: Optional request ID (generated if not provided)

    Returns:
        StructuredLogger instance with request ID
    """
    return StructuredLogger("vpp_phase2_sim.request", request_id or str(uuid4()))
