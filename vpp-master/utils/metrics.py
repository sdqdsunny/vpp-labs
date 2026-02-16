"""
Prometheus Metrics Collection

Provides Prometheus metrics for monitoring VPP Master API performance and system health.
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import time
from functools import wraps
from typing import Callable, Any


# Create a registry for metrics
registry = CollectorRegistry()

# ============================================================================
# API Metrics
# ============================================================================

api_requests_total = Counter(
    'vpp_api_requests_total',
    'Total API requests by endpoint and method',
    ['endpoint', 'method', 'status'],
    registry=registry
)

api_request_duration_seconds = Histogram(
    'vpp_api_request_duration_seconds',
    'API request duration in seconds',
    ['endpoint', 'method'],
    registry=registry
)

api_errors_total = Counter(
    'vpp_api_errors_total',
    'Total API errors by error code',
    ['error_code'],
    registry=registry
)

# ============================================================================
# Device Metrics
# ============================================================================

device_count = Gauge(
    'vpp_device_count',
    'Current number of registered devices',
    registry=registry
)

device_online_count = Gauge(
    'vpp_device_online_count',
    'Number of online devices',
    registry=registry
)

device_registration_total = Counter(
    'vpp_device_registration_total',
    'Total device registrations',
    ['device_type'],
    registry=registry
)

# ============================================================================
# Dispatch Metrics
# ============================================================================

dispatch_total = Counter(
    'vpp_dispatch_total',
    'Total dispatch commands by status',
    ['status'],
    registry=registry
)

dispatch_duration_seconds = Histogram(
    'vpp_dispatch_duration_seconds',
    'Dispatch execution duration in seconds',
    ['command_type'],
    registry=registry
)

dispatch_retry_total = Counter(
    'vpp_dispatch_retry_total',
    'Total dispatch retries',
    ['command_type'],
    registry=registry
)

# ============================================================================
# Analysis Metrics
# ============================================================================

analysis_duration_seconds = Histogram(
    'vpp_analysis_duration_seconds',
    'Analysis execution duration in seconds',
    ['analysis_type'],
    registry=registry
)

analysis_total = Counter(
    'vpp_analysis_total',
    'Total analysis executions by type',
    ['analysis_type', 'status'],
    registry=registry
)

# ============================================================================
# Database Metrics
# ============================================================================

database_connection_pool_size = Gauge(
    'vpp_database_connection_pool_size',
    'Database connection pool size',
    registry=registry
)

database_query_duration_seconds = Histogram(
    'vpp_database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    registry=registry
)

database_errors_total = Counter(
    'vpp_database_errors_total',
    'Total database errors',
    ['error_type'],
    registry=registry
)

# ============================================================================
# Utility Functions
# ============================================================================

def record_api_request(endpoint: str, method: str, status: int):
    """Record API request metrics"""
    api_requests_total.labels(endpoint=endpoint, method=method, status=status).inc()


def record_api_error(error_code: str):
    """Record API error metrics"""
    api_errors_total.labels(error_code=error_code).inc()


def record_device_registration(device_type: str):
    """Record device registration metrics"""
    device_registration_total.labels(device_type=device_type).inc()


def record_dispatch_command(status: str):
    """Record dispatch command metrics"""
    dispatch_total.labels(status=status).inc()


def record_dispatch_retry(command_type: str):
    """Record dispatch retry metrics"""
    dispatch_retry_total.labels(command_type=command_type).inc()


def record_analysis(analysis_type: str, status: str):
    """Record analysis execution metrics"""
    analysis_total.labels(analysis_type=analysis_type, status=status).inc()


def record_database_error(error_type: str):
    """Record database error metrics"""
    database_errors_total.labels(error_type=error_type).inc()


def time_api_request(endpoint: str, method: str) -> Callable:
    """Decorator to time API requests"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                api_request_duration_seconds.labels(endpoint=endpoint, method=method).observe(duration)
        return wrapper
    return decorator


def time_dispatch_execution(command_type: str) -> Callable:
    """Decorator to time dispatch execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                dispatch_duration_seconds.labels(command_type=command_type).observe(duration)
        return wrapper
    return decorator


def time_analysis(analysis_type: str) -> Callable:
    """Decorator to time analysis execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                analysis_duration_seconds.labels(analysis_type=analysis_type).observe(duration)
        return wrapper
    return decorator


def time_database_query(query_type: str) -> Callable:
    """Decorator to time database queries"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                database_query_duration_seconds.labels(query_type=query_type).observe(duration)
        return wrapper
    return decorator
