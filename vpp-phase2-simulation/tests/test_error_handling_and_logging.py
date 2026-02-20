"""
Unit tests for Error Handling and Logging.

Tests:
- Error handler initialization
- Exception handling
- Error response format
- Error statistics
- Logger configuration
- Log file creation
- Log rotation
"""

import pytest
import os
import tempfile
import logging
from datetime import datetime

from services.error_handler import (
    ErrorHandler, ErrorResponse, ErrorCode, ErrorSeverity,
    get_error_handler, init_error_handler
)
from services.logger_config import (
    LoggerConfig, get_logger_config, init_logger_config
)


class TestErrorHandlerInitialization:
    """Test error handler initialization."""

    def test_error_handler_initialization(self):
        """Test that error handler initializes correctly."""
        handler = ErrorHandler()
        
        assert handler.error_count == 0
        assert len(handler.error_by_code) == 0
        assert len(handler.error_by_severity) == 0
        assert handler.last_error is None

    def test_error_handler_stats_on_init(self):
        """Test that stats are correct on initialization."""
        handler = ErrorHandler()
        stats = handler.get_stats()
        
        assert stats['total_errors'] == 0
        assert stats['errors_by_code'] == {}
        assert stats['errors_by_severity'] == {}
        assert stats['last_error'] is None


class TestErrorResponse:
    """Test error response."""

    def test_error_response_creation(self):
        """Test creating error response."""
        response = ErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR.value,
            message="Invalid input",
            severity=ErrorSeverity.WARNING.value,
            request_id="req_001"
        )
        
        assert response.error_code == ErrorCode.VALIDATION_ERROR.value
        assert response.message == "Invalid input"
        assert response.severity == ErrorSeverity.WARNING.value
        assert response.request_id == "req_001"
        assert response.timestamp is not None

    def test_error_response_to_dict(self):
        """Test converting error response to dict."""
        response = ErrorResponse(
            error_code=ErrorCode.NOT_FOUND.value,
            message="Resource not found",
            severity=ErrorSeverity.WARNING.value,
            details={"resource": "user_123"},
            request_id="req_002"
        )
        
        response_dict = response.to_dict()
        
        assert response_dict['error_code'] == ErrorCode.NOT_FOUND.value
        assert response_dict['message'] == "Resource not found"
        assert response_dict['severity'] == ErrorSeverity.WARNING.value
        assert response_dict['details']['resource'] == "user_123"
        assert response_dict['request_id'] == "req_002"
        assert 'timestamp' in response_dict

    def test_error_response_to_json(self):
        """Test converting error response to JSON."""
        response = ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR.value,
            message="Internal server error",
            severity=ErrorSeverity.ERROR.value
        )
        
        json_str = response.to_json()
        
        assert isinstance(json_str, str)
        assert ErrorCode.INTERNAL_ERROR.value in json_str
        assert "Internal server error" in json_str


class TestExceptionHandling:
    """Test exception handling."""

    def test_handle_exception(self):
        """Test handling an exception."""
        handler = ErrorHandler()
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            response = handler.handle_exception(
                e,
                error_code=ErrorCode.VALIDATION_ERROR.value,
                request_id="req_001"
            )
        
        assert response.error_code == ErrorCode.VALIDATION_ERROR.value
        assert "Test error" in response.message
        assert response.request_id == "req_001"
        assert handler.error_count == 1

    def test_handle_validation_error(self):
        """Test handling validation error."""
        handler = ErrorHandler()
        
        response = handler.handle_validation_error(
            message="Invalid email format",
            request_id="req_002",
            details={"field": "email"}
        )
        
        assert response.error_code == ErrorCode.VALIDATION_ERROR.value
        assert response.message == "Invalid email format"
        assert response.severity == ErrorSeverity.WARNING.value
        assert response.details['field'] == "email"
        assert handler.error_count == 1

    def test_handle_not_found_error(self):
        """Test handling not found error."""
        handler = ErrorHandler()
        
        response = handler.handle_not_found_error(
            resource="User",
            request_id="req_003"
        )
        
        assert response.error_code == ErrorCode.NOT_FOUND.value
        assert "User not found" in response.message
        assert response.severity == ErrorSeverity.WARNING.value
        assert handler.error_count == 1

    def test_handle_timeout_error(self):
        """Test handling timeout error."""
        handler = ErrorHandler()
        
        response = handler.handle_timeout_error(
            operation="database_query",
            timeout_seconds=30,
            request_id="req_004"
        )
        
        assert response.error_code == ErrorCode.TIMEOUT_ERROR.value
        assert "database_query" in response.message
        assert "30" in response.message
        assert response.severity == ErrorSeverity.ERROR.value
        assert handler.error_count == 1

    def test_handle_service_unavailable_error(self):
        """Test handling service unavailable error."""
        handler = ErrorHandler()
        
        response = handler.handle_service_unavailable_error(
            service="database",
            request_id="req_005"
        )
        
        assert response.error_code == ErrorCode.SERVICE_UNAVAILABLE.value
        assert "database" in response.message
        assert response.severity == ErrorSeverity.CRITICAL.value
        assert handler.error_count == 1


class TestErrorStatistics:
    """Test error statistics."""

    def test_error_statistics_by_code(self):
        """Test error statistics by code."""
        handler = ErrorHandler()
        
        # Handle multiple errors
        handler.handle_validation_error("Error 1")
        handler.handle_validation_error("Error 2")
        handler.handle_not_found_error("Resource")
        
        stats = handler.get_stats()
        
        assert stats['total_errors'] == 3
        assert stats['errors_by_code'][ErrorCode.VALIDATION_ERROR.value] == 2
        assert stats['errors_by_code'][ErrorCode.NOT_FOUND.value] == 1

    def test_error_statistics_by_severity(self):
        """Test error statistics by severity."""
        handler = ErrorHandler()
        
        # Handle errors with different severities
        handler.handle_validation_error("Warning")
        handler.handle_timeout_error("operation", 30)
        handler.handle_service_unavailable_error("service")
        
        stats = handler.get_stats()
        
        assert stats['total_errors'] == 3
        assert stats['errors_by_severity'][ErrorSeverity.WARNING.value] == 1
        assert stats['errors_by_severity'][ErrorSeverity.ERROR.value] == 1
        assert stats['errors_by_severity'][ErrorSeverity.CRITICAL.value] == 1

    def test_last_error_tracking(self):
        """Test tracking of last error."""
        handler = ErrorHandler()
        
        handler.handle_validation_error("First error")
        first_error = handler.last_error
        
        handler.handle_not_found_error("Resource")
        second_error = handler.last_error
        
        assert first_error.error_code == ErrorCode.VALIDATION_ERROR.value
        assert second_error.error_code == ErrorCode.NOT_FOUND.value
        assert first_error != second_error

    def test_clear_statistics(self):
        """Test clearing statistics."""
        handler = ErrorHandler()
        
        handler.handle_validation_error("Error 1")
        handler.handle_not_found_error("Resource")
        
        assert handler.error_count == 2
        
        handler.clear_stats()
        
        assert handler.error_count == 0
        assert len(handler.error_by_code) == 0
        assert len(handler.error_by_severity) == 0
        assert handler.last_error is None


class TestGlobalErrorHandler:
    """Test global error handler."""

    def test_get_error_handler(self):
        """Test getting global error handler."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is handler2

    def test_init_error_handler(self):
        """Test initializing global error handler."""
        handler = init_error_handler()
        
        assert handler is not None
        assert handler.error_count == 0


class TestLoggerConfigInitialization:
    """Test logger configuration initialization."""

    def test_logger_config_initialization(self):
        """Test that logger config initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir)
            
            assert config.log_dir == tmpdir
            assert config.log_level == "INFO"
            assert os.path.exists(tmpdir)

    def test_logger_config_creates_log_directory(self):
        """Test that logger config creates log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "logs")
            config = LoggerConfig(log_dir=log_dir)
            
            assert os.path.exists(log_dir)


class TestLoggerConfiguration:
    """Test logger configuration."""

    def test_configure_logger_console_only(self):
        """Test configuring logger with console handler only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir)
            logger = config.configure_logger("test_logger")
            
            assert logger is not None
            assert logger.name == "test_logger"
            assert len(logger.handlers) > 0

    def test_configure_logger_with_file(self):
        """Test configuring logger with file handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir)
            logger = config.configure_logger("test_logger", log_file="test.log")
            
            assert logger is not None
            assert len(logger.handlers) >= 2  # Console + File
            
            # Check that log file was created
            log_file = os.path.join(tmpdir, "test.log")
            assert os.path.exists(log_file)

    def test_set_log_level(self):
        """Test setting log level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir, log_level="INFO")
            logger = config.configure_logger("test_logger")
            
            assert logger.level == logging.INFO
            
            config.set_log_level("test_logger", "DEBUG")
            
            assert logger.level == logging.DEBUG

    def test_get_logger(self):
        """Test getting a logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir)
            
            logger1 = config.get_logger("test_logger")
            logger2 = config.get_logger("test_logger")
            
            assert logger1 is logger2

    def test_get_unconfigured_logger(self):
        """Test getting an unconfigured logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir)
            
            logger = config.get_logger("new_logger")
            
            assert logger is not None
            assert logger.name == "new_logger"


class TestLogOperations:
    """Test logging operations."""

    def test_log_critical_operation(self):
        """Test logging critical operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir)
            logger = config.configure_logger("test_logger", log_file="test.log")
            
            config.log_critical_operation(
                logger,
                "database_migration",
                {"version": "2.0"}
            )
            
            # Check that log file contains the message
            log_file = os.path.join(tmpdir, "test.log")
            with open(log_file, 'r') as f:
                content = f.read()
                assert "CRITICAL OPERATION" in content
                assert "database_migration" in content

    def test_log_data_operation(self):
        """Test logging data operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir)
            logger = config.configure_logger("test_logger", log_file="test.log")
            
            config.log_data_operation(
                logger,
                "save",
                "power_data",
                100
            )
            
            log_file = os.path.join(tmpdir, "test.log")
            with open(log_file, 'r') as f:
                content = f.read()
                assert "DATA OPERATION" in content
                assert "save" in content
                assert "power_data" in content

    def test_log_api_call(self):
        """Test logging API call."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir)
            logger = config.configure_logger("test_logger", log_file="test.log")
            
            config.log_api_call(
                logger,
                "POST",
                "/api/vcc/report/power",
                200,
                45.5,
                "req_001"
            )
            
            log_file = os.path.join(tmpdir, "test.log")
            with open(log_file, 'r') as f:
                content = f.read()
                assert "API CALL" in content
                assert "POST" in content
                assert "/api/vcc/report/power" in content

    def test_log_coordination_event(self):
        """Test logging coordination event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir)
            logger = config.configure_logger("test_logger", log_file="test.log")
            
            config.log_coordination_event(
                logger,
                "coordination_completed",
                92.5,
                {"power_cmd": "sent", "storage_cmd": "sent"}
            )
            
            log_file = os.path.join(tmpdir, "test.log")
            with open(log_file, 'r') as f:
                content = f.read()
                assert "COORDINATION" in content
                assert "92.5" in content


class TestLoggerStatistics:
    """Test logger statistics."""

    def test_get_logger_stats(self):
        """Test getting logger statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir)
            config.configure_logger("logger1", log_file="log1.log")
            config.configure_logger("logger2", log_file="log2.log")
            
            stats = config.get_stats()
            
            assert stats['log_dir'] == tmpdir
            assert stats['log_level'] == "INFO"
            assert len(stats['configured_loggers']) == 2
            assert len(stats['log_files']) == 2

    def test_get_log_files(self):
        """Test getting log files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(log_dir=tmpdir)
            config.configure_logger("logger1", log_file="log1.log")
            config.configure_logger("logger2", log_file="log2.log")
            
            log_files = config._get_log_files()
            
            assert len(log_files) == 2
            assert any(f['name'] == 'log1.log' for f in log_files)
            assert any(f['name'] == 'log2.log' for f in log_files)


class TestLogRotation:
    """Test log rotation."""

    def test_log_rotation_on_size(self):
        """Test log rotation based on file size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config with small max_bytes to trigger rotation
            config = LoggerConfig(log_dir=tmpdir, max_bytes=100)
            logger = config.configure_logger("test_logger", log_file="test.log")
            
            # Write large amount of data to trigger rotation
            for i in range(50):
                logger.info(f"This is a test log message number {i}")
            
            # Check that backup files were created
            log_files = os.listdir(tmpdir)
            assert len(log_files) > 1  # Original + backups


class TestGlobalLoggerConfig:
    """Test global logger config."""

    def test_get_logger_config(self):
        """Test getting global logger config."""
        config1 = get_logger_config()
        config2 = get_logger_config()
        
        assert config1 is config2

    def test_init_logger_config(self):
        """Test initializing global logger config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = init_logger_config(log_dir=tmpdir)
            
            assert config is not None
            assert config.log_dir == tmpdir


class TestErrorHandlingIntegration:
    """Test error handling integration."""

    def test_error_handler_with_logger(self):
        """Test error handler with logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup logger
            logger_config = LoggerConfig(log_dir=tmpdir)
            logger = logger_config.configure_logger("test_logger", log_file="test.log")
            
            # Setup error handler
            error_handler = ErrorHandler()
            
            # Handle exception
            try:
                raise ValueError("Test error")
            except ValueError as e:
                response = error_handler.handle_exception(
                    e,
                    error_code=ErrorCode.VALIDATION_ERROR.value,
                    request_id="req_001"
                )
            
            # Verify error was handled
            assert response.error_code == ErrorCode.VALIDATION_ERROR.value
            assert error_handler.error_count == 1
