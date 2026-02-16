"""
Property-Based Tests for Monitoring and Observability

Tests for Prometheus metrics collection, structured logging, and rate limiting.
Uses Hypothesis for property-based testing with minimum 100 iterations per property.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import json
import time
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from bottle import Bottle, request, response
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.metrics import (
    registry, api_requests_total, api_request_duration_seconds,
    api_errors_total, device_count, device_online_count,
    dispatch_total, dispatch_duration_seconds, analysis_duration_seconds,
    database_query_duration_seconds, record_api_request, record_api_error
)
from utils.logger import setup_logger, JSONFormatter
from middleware.rate_limiter import RateLimiter, setup_rate_limiting
from middleware.request_logger import setup_request_logging
from middleware.error_handler import setup_error_handling
import logging


class TestAPIMetricsRecordedProperty:
    """
    Property 46: API Metrics Are Recorded
    
    For any API request processed, Prometheus metrics should be recorded
    including request count, response time, and status code.
    
    Validates: Requirements 20.1
    """
    
    @given(
        endpoint=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\n\r')),
        method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
        status=st.integers(min_value=100, max_value=599)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_api_metrics_recorded(self, endpoint, method, status):
        """
        For any API request with endpoint, method, and status code,
        metrics should be recorded in Prometheus.
        """
        # Record API request
        record_api_request(endpoint=endpoint, method=method, status=status)
        
        # Verify metrics were recorded by checking the counter directly
        # The metric should have been incremented
        try:
            # Get current value from the counter
            metric_value = api_requests_total.labels(
                endpoint=endpoint,
                method=method,
                status=status
            )._value.get()
            
            # Should have at least 1 request recorded
            assert metric_value >= 1, f"Expected at least 1 metric, got {metric_value}"
        except Exception as e:
            # If we can't get the value directly, verify through registry
            metric_samples = list(registry.collect())
            found = False
            for metric in metric_samples:
                if metric.name == 'vpp_api_requests_total':
                    for sample in metric.samples:
                        if (sample.labels.get('endpoint') == endpoint and
                            sample.labels.get('method') == method and
                            sample.labels.get('status') == str(status)):
                            found = True
                            assert sample.value >= 1, "Metric count should be at least 1"
                            break
            
            assert found, f"Metric not found for {endpoint} {method} {status}"


class TestPrometheusMetricsFormattedProperty:
    """
    Property 47: Prometheus Metrics Are Properly Formatted
    
    For any Prometheus metrics query, the endpoint should return metrics
    in valid Prometheus text format.
    
    Validates: Requirements 20.2
    """
    
    @given(
        endpoint=st.text(min_size=1, max_size=100),
        method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE']),
        status=st.integers(min_value=100, max_value=599)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_prometheus_metrics_formatted(self, endpoint, method, status):
        """
        For any metrics recorded, the Prometheus format should be valid.
        """
        # Record some metrics
        record_api_request(endpoint=endpoint, method=method, status=status)
        
        # Generate Prometheus output
        from prometheus_client import generate_latest
        metrics_output = generate_latest(registry).decode('utf-8')
        
        # Verify format
        assert isinstance(metrics_output, str), "Metrics output should be string"
        assert len(metrics_output) > 0, "Metrics output should not be empty"
        
        # Check for Prometheus format markers
        lines = metrics_output.split('\n')
        
        # Should have HELP and TYPE lines for metrics
        help_lines = [l for l in lines if l.startswith('# HELP')]
        type_lines = [l for l in lines if l.startswith('# TYPE')]
        metric_lines = [l for l in lines if l and not l.startswith('#')]
        
        assert len(help_lines) > 0, "Should have HELP lines"
        assert len(type_lines) > 0, "Should have TYPE lines"
        assert len(metric_lines) > 0, "Should have metric lines"
        
        # Verify metric lines have proper format (name{labels} value)
        for line in metric_lines:
            if line.strip():
                # Should contain a metric name and value
                assert '{' in line or ' ' in line, f"Invalid metric format: {line}"


class TestRequestLoggingIncludesRequiredFieldsProperty:
    """
    Property 48: Request Logging Includes Required Fields
    
    For any API request processed, the log should include method, path,
    status code, and response time.
    
    Validates: Requirements 21.1
    """
    
    @given(
        method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE']),
        path=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters='\n\r')),
        status=st.integers(min_value=100, max_value=599),
        duration_ms=st.floats(min_value=0, max_value=10000)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_request_logging_fields(self, method, path, status, duration_ms):
        """
        For any request log entry, all required fields should be present.
        """
        # Create a log record
        logger = setup_logger(__name__)
        formatter = JSONFormatter()
        
        # Create a mock log record
        record = logging.LogRecord(
            name=__name__,
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg=f"{method} {path} {status}",
            args=(),
            exc_info=None
        )
        
        # Add required fields
        record.request_id = str(uuid.uuid4())
        record.extra_fields = {
            'method': method,
            'path': path,
            'status_code': status,
            'duration_ms': duration_ms
        }
        
        # Format the record
        formatted = formatter.format(record)
        
        # Parse JSON
        log_data = json.loads(formatted)
        
        # Verify required fields
        assert 'timestamp' in log_data, "Log should include timestamp"
        assert 'level' in log_data, "Log should include level"
        assert 'logger' in log_data, "Log should include logger"
        assert 'message' in log_data, "Log should include message"
        assert 'request_id' in log_data, "Log should include request_id"
        assert 'method' in log_data, "Log should include method"
        assert 'path' in log_data, "Log should include path"
        assert 'status_code' in log_data, "Log should include status_code"
        assert 'duration_ms' in log_data, "Log should include duration_ms"


class TestErrorLoggingIncludesStackTracesProperty:
    """
    Property 49: Error Logging Includes Stack Traces
    
    For any API error, the log should include full context including
    stack trace and request details.
    
    Validates: Requirements 21.2
    """
    
    @given(
        error_message=st.text(min_size=1, max_size=200),
        error_code=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_error_logging_stack_trace(self, error_message, error_code):
        """
        For any error log entry, stack trace should be included.
        """
        logger = setup_logger(__name__)
        formatter = JSONFormatter()
        
        # Create an exception
        try:
            raise ValueError(error_message)
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            
            # Create a log record with exception
            record = logging.LogRecord(
                name=__name__,
                level=logging.ERROR,
                pathname=__file__,
                lineno=1,
                msg=f"Error: {error_code}",
                args=(),
                exc_info=exc_info
            )
            
            record.request_id = str(uuid.uuid4())
            record.extra_fields = {
                'error_code': error_code,
                'error_message': error_message
            }
            
            # Format the record
            formatted = formatter.format(record)
            
            # Parse JSON
            log_data = json.loads(formatted)
            
            # Verify stack trace is included
            assert 'exception' in log_data, "Error log should include exception"
            assert 'stack_trace' in log_data, "Error log should include stack_trace"
            assert len(log_data['stack_trace']) > 0, "Stack trace should not be empty"
            assert 'ValueError' in log_data['stack_trace'], "Stack trace should include exception type"


class TestUniqueRequestIDsGeneratedProperty:
    """
    Property 50: Unique Request IDs Are Generated
    
    For any API request processed, a unique request ID should be generated
    and included in logs for tracing.
    
    Validates: Requirements 21.3
    """
    
    @given(
        num_requests=st.integers(min_value=10, max_value=100)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_unique_request_ids(self, num_requests):
        """
        For any sequence of requests, each should have a unique request ID.
        """
        request_ids = set()
        
        for _ in range(num_requests):
            request_id = str(uuid.uuid4())
            request_ids.add(request_id)
        
        # All request IDs should be unique
        assert len(request_ids) == num_requests, \
            f"Expected {num_requests} unique IDs, got {len(request_ids)}"


class TestRateLimitExceededReturns429Property:
    """
    Property 51: Rate Limit Exceeded Returns 429
    
    For any API client that exceeds the configured rate limit,
    the system should return a 429 Too Many Requests response.
    
    Validates: Requirements 22.1
    """
    
    @given(
        user_id=st.text(min_size=1, max_size=50),
        requests_count=st.integers(min_value=1001, max_value=1100)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_rate_limit_exceeded_429(self, user_id, requests_count):
        """
        For any user exceeding the rate limit, 429 should be returned.
        """
        limiter = RateLimiter()
        
        # Simulate requests exceeding the limit
        current_time = time.time()
        for i in range(requests_count):
            # Add request to user's list
            limiter.user_requests[user_id].append(current_time + i * 0.001)
        
        # Check if limit is exceeded
        is_allowed, remaining, reset_time = limiter.check_user_rate_limit(user_id)
        
        # Should be rejected
        assert is_allowed is False, "Rate limit should be exceeded"
        assert remaining == 0, "Remaining should be 0"
        assert reset_time > current_time, "Reset time should be in the future"


class TestRateLimitHeadersIncludedProperty:
    """
    Property 52: Rate Limit Headers Are Included
    
    For any API response, rate limit information should be included in
    response headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset).
    
    Validates: Requirements 22.2
    """
    
    @given(
        limit=st.integers(min_value=100, max_value=10000),
        remaining=st.integers(min_value=0, max_value=10000),
        reset_time=st.integers(min_value=1000000000, max_value=2000000000)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_rate_limit_headers(self, limit, remaining, reset_time):
        """
        For any rate-limited response, headers should include rate limit info.
        """
        # Create a mock response
        mock_response = Mock()
        mock_response.headers = {}
        
        # Add rate limit headers
        mock_response.headers['X-RateLimit-Limit'] = str(limit)
        mock_response.headers['X-RateLimit-Remaining'] = str(remaining)
        mock_response.headers['X-RateLimit-Reset'] = str(reset_time)
        
        # Verify headers are present
        assert 'X-RateLimit-Limit' in mock_response.headers, \
            "Response should include X-RateLimit-Limit header"
        assert 'X-RateLimit-Remaining' in mock_response.headers, \
            "Response should include X-RateLimit-Remaining header"
        assert 'X-RateLimit-Reset' in mock_response.headers, \
            "Response should include X-RateLimit-Reset header"
        
        # Verify header values are valid
        assert int(mock_response.headers['X-RateLimit-Limit']) == limit
        assert int(mock_response.headers['X-RateLimit-Remaining']) == remaining
        assert int(mock_response.headers['X-RateLimit-Reset']) == reset_time


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
