"""
Unit tests for monitoring and observability components.

Tests Prometheus metrics collection, structured logging, and request ID tracking.
"""

import pytest
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from prometheus_client import CollectorRegistry

from utils.prometheus_metrics import PrometheusMetrics, get_metrics, init_metrics
from utils.structured_logger import StructuredLogger, get_structured_logger, create_request_logger
from middleware.request_id import get_request_id


class TestPrometheusMetrics:
    """Test Prometheus metrics collection."""

    def test_metrics_initialization(self):
        """Test that metrics are properly initialized."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        assert metrics.device_count is not None
        assert metrics.power_output_watts is not None
        assert metrics.storage_soc_percent is not None
        assert metrics.load_watts is not None
        assert metrics.scenario_execution_time_seconds is not None
        assert metrics.scenario_count is not None
        assert metrics.scenario_status is not None
        assert metrics.power_flow_calculation_time_ms is not None
        assert metrics.power_flow_violations is not None
        assert metrics.power_flow_convergence_failures is not None
        assert metrics.communication_latency_ms is not None
        assert metrics.packet_loss_rate is not None
        assert metrics.messages_processed is not None
        assert metrics.metrics_collection_rate is not None
        assert metrics.active_scenarios is not None
        assert metrics.database_connections is not None

    def test_record_device_count(self):
        """Test recording device count."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.record_device_count("solar", 100)
        metrics.record_device_count("wind", 50)
        
        # Verify metrics were recorded
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_device_count{device_type="solar"} 100.0' in output
        assert 'vpp_sim_device_count{device_type="wind"} 50.0' in output

    def test_record_power_output(self):
        """Test recording power output."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.record_power_output("solar", "device-1", 5000.0)
        metrics.record_power_output("wind", "device-2", 3000.0)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_power_output_watts' in output

    def test_record_storage_soc(self):
        """Test recording battery state of charge."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.record_storage_soc("battery-1", 75.5)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_storage_soc_percent' in output

    def test_record_load(self):
        """Test recording load demand."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.record_load("load-1", 2000.0)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_load_watts' in output

    def test_record_scenario_execution_time(self):
        """Test recording scenario execution time."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.record_scenario_execution_time("scenario-1", 10.5)
        metrics.record_scenario_execution_time("scenario-1", 12.3)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_scenario_execution_time_seconds' in output

    def test_increment_scenario_count(self):
        """Test incrementing scenario count."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.increment_scenario_count("success")
        metrics.increment_scenario_count("success")
        metrics.increment_scenario_count("failure")
        
        output = metrics.get_metrics().decode('utf-8')
        # Prometheus counter adds _total suffix
        assert 'vpp_sim_scenario_count_total{status="success"} 2.0' in output
        assert 'vpp_sim_scenario_count_total{status="failure"} 1.0' in output

    def test_set_scenario_status(self):
        """Test setting scenario status."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.set_scenario_status("scenario-1", 1)  # running
        metrics.set_scenario_status("scenario-2", 2)  # completed
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_scenario_status' in output

    def test_record_power_flow_calculation_time(self):
        """Test recording power flow calculation time."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.record_power_flow_calculation_time(150.5)
        metrics.record_power_flow_calculation_time(200.3)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_power_flow_calculation_time_ms' in output

    def test_set_power_flow_violations(self):
        """Test setting power flow violations."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.set_power_flow_violations("voltage", 5)
        metrics.set_power_flow_violations("congestion", 2)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_power_flow_violations{violation_type="voltage"} 5.0' in output
        assert 'vpp_sim_power_flow_violations{violation_type="congestion"} 2.0' in output

    def test_increment_convergence_failures(self):
        """Test incrementing convergence failures."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.increment_convergence_failures()
        metrics.increment_convergence_failures()
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_power_flow_convergence_failures_total 2.0' in output

    def test_record_communication_latency(self):
        """Test recording communication latency."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.record_communication_latency("IEC104", 25.5)
        metrics.record_communication_latency("MQTT", 15.3)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_communication_latency_ms' in output

    def test_set_packet_loss_rate(self):
        """Test setting packet loss rate."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.set_packet_loss_rate("5G", 0.02)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_packet_loss_rate{protocol="5G"} 0.02' in output

    def test_increment_messages_processed(self):
        """Test incrementing messages processed."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.increment_messages_processed("IEC104", "command")
        metrics.increment_messages_processed("IEC104", "command")
        metrics.increment_messages_processed("MQTT", "response")
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_messages_processed' in output

    def test_set_metrics_collection_rate(self):
        """Test setting metrics collection rate."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.set_metrics_collection_rate(1000.5)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_metrics_collection_rate 1000.5' in output

    def test_set_active_scenarios(self):
        """Test setting active scenarios count."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.set_active_scenarios(5)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_active_scenarios 5.0' in output

    def test_set_database_connections(self):
        """Test setting database connections."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.set_database_connections(10)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_database_connections 10.0' in output

    def test_get_metrics_format(self):
        """Test that metrics are returned in Prometheus format."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        metrics.record_device_count("solar", 100)
        
        output = metrics.get_metrics()
        assert isinstance(output, bytes)
        
        # Verify it's valid Prometheus format
        decoded = output.decode('utf-8')
        assert 'vpp_sim_device_count' in decoded
        assert 'TYPE' in decoded or 'HELP' in decoded or 'device_type' in decoded

    def test_global_metrics_instance(self):
        """Test global metrics instance."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()
        
        assert metrics1 is metrics2

    def test_init_metrics(self):
        """Test initializing metrics with custom registry."""
        registry = CollectorRegistry()
        metrics = init_metrics(registry=registry)
        
        assert metrics is not None
        assert metrics.registry is registry


class TestStructuredLogger:
    """Test structured logging."""

    def test_logger_initialization(self):
        """Test that logger is properly initialized."""
        logger = StructuredLogger("test.logger")
        
        assert logger.name == "test.logger"
        assert logger.request_id is not None
        assert logger.logger is not None

    def test_logger_with_request_id(self):
        """Test logger with provided request ID."""
        request_id = "req-12345"
        logger = StructuredLogger("test.logger", request_id=request_id)
        
        assert logger.request_id == request_id

    def test_info_logging(self, caplog):
        """Test info level logging."""
        logger = StructuredLogger("test.logger", request_id="req-123")
        
        with caplog.at_level(logging.INFO):
            logger.info("Test message", scenario_id="scenario-1", device_count=100)
        
        # Verify log was recorded
        assert len(caplog.records) > 0
        log_record = caplog.records[0]
        assert "Test message" in log_record.message

    def test_debug_logging(self, caplog):
        """Test debug level logging."""
        logger = StructuredLogger("test.logger", request_id="req-123")
        
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message", operation="test")
        
        assert len(caplog.records) > 0

    def test_warning_logging(self, caplog):
        """Test warning level logging."""
        logger = StructuredLogger("test.logger", request_id="req-123")
        
        with caplog.at_level(logging.WARNING):
            logger.warning("Warning message", threshold=100)
        
        assert len(caplog.records) > 0

    def test_error_logging_with_exception(self, caplog):
        """Test error logging with exception."""
        logger = StructuredLogger("test.logger", request_id="req-123")
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            with caplog.at_level(logging.ERROR):
                logger.error("Error occurred", exception=e)
        
        assert len(caplog.records) > 0
        log_record = caplog.records[0]
        assert "Error occurred" in log_record.message

    def test_critical_logging(self, caplog):
        """Test critical level logging."""
        logger = StructuredLogger("test.logger", request_id="req-123")
        
        with caplog.at_level(logging.CRITICAL):
            logger.critical("Critical message", severity="high")
        
        assert len(caplog.records) > 0

    def test_performance_context(self, caplog):
        """Test performance context manager."""
        logger = StructuredLogger("test.logger", request_id="req-123")
        
        with caplog.at_level(logging.DEBUG):
            with logger.performance_context("test_operation", threshold_ms=50):
                pass
        
        assert len(caplog.records) > 0

    def test_performance_decorator(self, caplog):
        """Test performance decorator."""
        logger = StructuredLogger("test.logger", request_id="req-123")
        
        @logger.performance_decorator(threshold_ms=50)
        def test_function():
            return "result"
        
        with caplog.at_level(logging.DEBUG):
            result = test_function()
        
        assert result == "result"
        assert len(caplog.records) > 0

    def test_set_request_id(self):
        """Test setting request ID."""
        logger = StructuredLogger("test.logger", request_id="req-123")
        
        assert logger.request_id == "req-123"
        
        logger.set_request_id("req-456")
        assert logger.request_id == "req-456"

    def test_get_structured_logger(self):
        """Test getting structured logger."""
        logger = get_structured_logger("test.logger", request_id="req-123")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.request_id == "req-123"

    def test_create_request_logger(self):
        """Test creating request logger."""
        logger = create_request_logger(request_id="req-123")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.request_id == "req-123"

    def test_create_request_logger_without_id(self):
        """Test creating request logger without ID."""
        logger = create_request_logger()
        
        assert isinstance(logger, StructuredLogger)
        assert logger.request_id is not None

    def test_log_data_structure(self, caplog):
        """Test that log data has correct structure."""
        logger = StructuredLogger("test.logger", request_id="req-123")
        
        with caplog.at_level(logging.INFO):
            logger.info("Test message", scenario_id="scenario-1")
        
        log_record = caplog.records[0]
        message = log_record.message
        
        # Parse JSON from message
        log_data = json.loads(message)
        
        assert "timestamp" in log_data
        assert "level" in log_data
        assert "logger" in log_data
        assert "message" in log_data
        assert "request_id" in log_data
        assert log_data["request_id"] == "req-123"
        assert log_data["scenario_id"] == "scenario-1"

    def test_log_with_tags(self, caplog):
        """Test logging with tags."""
        logger = StructuredLogger("test.logger", request_id="req-123")
        
        with caplog.at_level(logging.INFO):
            logger.info(
                "Test message",
                tags={"component": "scenario_engine", "operation": "execute"}
            )
        
        log_record = caplog.records[0]
        log_data = json.loads(log_record.message)
        
        assert "tags" in log_data
        assert log_data["tags"]["component"] == "scenario_engine"


class TestRequestIdTracking:
    """Test request ID tracking."""

    def test_request_id_generation(self):
        """Test that request ID is generated."""
        request_id = get_request_id()
        
        assert request_id is not None
        assert len(request_id) > 0

    def test_request_id_format(self):
        """Test that request ID is in UUID format."""
        request_id = get_request_id()
        
        # Should be a valid UUID string
        parts = request_id.split('-')
        assert len(parts) == 5


class TestMetricsIntegration:
    """Test integration of metrics with other components."""

    def test_metrics_with_device_simulator(self):
        """Test metrics recording with device simulator data."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        # Simulate device simulator metrics
        metrics.record_device_count("solar", 100)
        metrics.record_power_output("solar", "device-1", 5000.0)
        metrics.record_device_count("wind", 50)
        metrics.record_power_output("wind", "device-2", 3000.0)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_device_count' in output
        assert 'vpp_sim_power_output_watts' in output

    def test_metrics_with_scenario_execution(self):
        """Test metrics recording with scenario execution."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        # Simulate scenario execution metrics
        metrics.set_scenario_status("scenario-1", 1)  # running
        metrics.record_scenario_execution_time("scenario-1", 10.5)
        metrics.increment_scenario_count("success")
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_scenario_status' in output
        assert 'vpp_sim_scenario_execution_time_seconds' in output
        assert 'vpp_sim_scenario_count' in output

    def test_metrics_with_power_flow(self):
        """Test metrics recording with power flow data."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        # Simulate power flow metrics
        metrics.record_power_flow_calculation_time(150.5)
        metrics.set_power_flow_violations("voltage", 5)
        metrics.set_power_flow_violations("congestion", 2)
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_power_flow_calculation_time_ms' in output
        assert 'vpp_sim_power_flow_violations' in output

    def test_metrics_with_communication(self):
        """Test metrics recording with communication data."""
        registry = CollectorRegistry()
        metrics = PrometheusMetrics(registry=registry)
        
        # Simulate communication metrics
        metrics.record_communication_latency("IEC104", 25.5)
        metrics.set_packet_loss_rate("5G", 0.02)
        metrics.increment_messages_processed("IEC104", "command")
        
        output = metrics.get_metrics().decode('utf-8')
        assert 'vpp_sim_communication_latency_ms' in output
        assert 'vpp_sim_packet_loss_rate' in output
        assert 'vpp_sim_messages_processed' in output
