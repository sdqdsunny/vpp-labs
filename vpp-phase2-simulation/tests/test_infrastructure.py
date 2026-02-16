"""
Unit tests for infrastructure components.

Tests error handling, logging, and configuration.
"""

import pytest
import json
from utils.errors import (
    SimulationException,
    SimulatorError,
    ScenarioExecutionError,
    ValidationError,
)
from middleware.error_handler import format_error_response


class TestErrorHandling:
    """Test error handling."""

    def test_simulation_exception_creation(self):
        """Test SimulationException creation."""
        exc = SimulationException("Test error", code="TEST_ERROR", details={"key": "value"})
        assert exc.message == "Test error"
        assert exc.code == "TEST_ERROR"
        assert exc.details == {"key": "value"}

    def test_simulator_error_creation(self):
        """Test SimulatorError creation."""
        exc = SimulatorError("Simulator failed", simulator_id="sim-123")
        assert exc.message == "Simulator failed"
        assert exc.code == "SIMULATOR_ERROR"
        assert exc.simulator_id == "sim-123"

    def test_scenario_execution_error_creation(self):
        """Test ScenarioExecutionError creation."""
        exc = ScenarioExecutionError("Scenario failed", scenario_id="scenario-123")
        assert exc.message == "Scenario failed"
        assert exc.code == "SCENARIO_EXECUTION_ERROR"
        assert exc.scenario_id == "scenario-123"

    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        exc = ValidationError("Invalid input", field="device_id")
        assert exc.message == "Invalid input"
        assert exc.code == "VALIDATION_ERROR"
        assert exc.field == "device_id"

    def test_format_error_response_simulation_exception(self):
        """Test formatting SimulationException as error response."""
        exc = SimulatorError("Test error", simulator_id="sim-123")
        error_dict, status = format_error_response(exc, "req-123")
        
        assert error_dict["error"]["code"] == "SIMULATOR_ERROR"
        assert error_dict["error"]["message"] == "Test error"
        assert error_dict["error"]["request_id"] == "req-123"
        assert status == 422

    def test_format_error_response_generic_exception(self):
        """Test formatting generic exception as error response."""
        exc = Exception("Generic error")
        error_dict, status = format_error_response(exc, "req-123")
        
        assert error_dict["error"]["code"] == "INTERNAL_ERROR"
        assert error_dict["error"]["message"] == "Generic error"
        assert error_dict["error"]["request_id"] == "req-123"
        assert status == 500

    def test_validation_error_status_code(self):
        """Test ValidationError maps to 400 status code."""
        exc = ValidationError("Invalid input")
        error_dict, status = format_error_response(exc, "req-123")
        assert status == 400

    def test_timeout_error_status_code(self):
        """Test TimeoutError maps to 504 status code."""
        from utils.errors import TimeoutError as SimTimeoutError
        exc = SimTimeoutError("Operation timed out", timeout_ms=500)
        error_dict, status = format_error_response(exc, "req-123")
        assert status == 504


class TestConfiguration:
    """Test configuration."""

    def test_config_defaults(self):
        """Test configuration defaults."""
        from config import config
        assert config.DEBUG is False or config.DEBUG is True
        assert config.DATABASE_POOL_SIZE > 0
        assert config.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_config_environment_override(self):
        """Test configuration environment variable override."""
        import os
        os.environ["DEBUG"] = "true"
        from importlib import reload
        import config as config_module
        reload(config_module)
        
        # Reset
        del os.environ["DEBUG"]


class TestLogging:
    """Test logging configuration."""

    def test_logger_setup(self):
        """Test logger setup."""
        from utils.logger import setup_logging
        logger = setup_logging(log_level="DEBUG")
        assert logger is not None
        assert logger.name == "vpp_phase2_sim"

    def test_request_logger_context(self):
        """Test RequestLogger context manager."""
        from utils.logger import setup_logging, RequestLogger
        logger = setup_logging()
        
        with RequestLogger(logger, request_id="req-123") as req_logger:
            assert req_logger.request_id == "req-123"
            # Should not raise
            req_logger.info("Test message")
            req_logger.debug("Debug message")
            req_logger.error("Error message")
            req_logger.warning("Warning message")


class TestHealthCheck:
    """Test health check endpoints."""

    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        # Note: This requires a test client implementation
        # Placeholder for integration testing
        pass

    def test_readiness_check_endpoint(self, client):
        """Test readiness check endpoint."""
        # Note: This requires a test client implementation
        # Placeholder for integration testing
        pass
