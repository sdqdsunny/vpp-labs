"""
Prometheus metrics collection for VPP Phase 2 Simulation Framework.

Provides comprehensive metrics collection for all simulation components including
device simulators, scenario execution, power flow, communication, and system metrics.
"""

from prometheus_client import (
    Counter, Gauge, Histogram, CollectorRegistry, generate_latest
)
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """Centralized Prometheus metrics collection."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize Prometheus metrics.

        Args:
            registry: Optional custom CollectorRegistry (uses default if None)
        """
        self.registry = registry or CollectorRegistry()

        # Device Simulator Metrics
        self.device_count = Gauge(
            "vpp_sim_device_count",
            "Number of active device simulators",
            ["device_type"],
            registry=self.registry
        )

        self.power_output_watts = Gauge(
            "vpp_sim_power_output_watts",
            "Current power output by device type",
            ["device_type", "device_id"],
            registry=self.registry
        )

        self.storage_soc_percent = Gauge(
            "vpp_sim_storage_soc_percent",
            "Battery state of charge percentage",
            ["device_id"],
            registry=self.registry
        )

        self.load_watts = Gauge(
            "vpp_sim_load_watts",
            "Current load demand in watts",
            ["device_id"],
            registry=self.registry
        )

        # Scenario Execution Metrics
        self.scenario_execution_time_seconds = Histogram(
            "vpp_sim_scenario_execution_time_seconds",
            "Scenario execution duration in seconds",
            ["scenario_id"],
            registry=self.registry
        )

        self.scenario_count = Counter(
            "vpp_sim_scenario_count",
            "Total scenarios executed",
            ["status"],
            registry=self.registry
        )

        self.scenario_status = Gauge(
            "vpp_sim_scenario_status",
            "Scenario status (0=pending, 1=running, 2=completed, 3=failed)",
            ["scenario_id"],
            registry=self.registry
        )

        # Power Flow Metrics
        self.power_flow_calculation_time_ms = Histogram(
            "vpp_sim_power_flow_calculation_time_ms",
            "Power flow calculation time in milliseconds",
            registry=self.registry
        )

        self.power_flow_violations = Gauge(
            "vpp_sim_power_flow_violations",
            "Number of power flow violations",
            ["violation_type"],
            registry=self.registry
        )

        self.power_flow_convergence_failures = Counter(
            "vpp_sim_power_flow_convergence_failures",
            "Power flow convergence failures",
            registry=self.registry
        )

        # Communication Metrics
        self.communication_latency_ms = Histogram(
            "vpp_sim_communication_latency_ms",
            "Communication latency in milliseconds",
            ["protocol"],
            registry=self.registry
        )

        self.packet_loss_rate = Gauge(
            "vpp_sim_packet_loss_rate",
            "Packet loss rate (0-1)",
            ["protocol"],
            registry=self.registry
        )

        self.messages_processed = Counter(
            "vpp_sim_messages_processed",
            "Total messages processed",
            ["protocol", "message_type"],
            registry=self.registry
        )

        # System Metrics
        self.metrics_collection_rate = Gauge(
            "vpp_sim_metrics_collection_rate",
            "Metrics collection rate (metrics per second)",
            registry=self.registry
        )

        self.active_scenarios = Gauge(
            "vpp_sim_active_scenarios",
            "Number of active scenarios",
            registry=self.registry
        )

        self.database_connections = Gauge(
            "vpp_sim_database_connections",
            "Database connection pool size",
            registry=self.registry
        )

    def record_device_count(self, device_type: str, count: int) -> None:
        """
        Record the number of active devices of a specific type.

        Args:
            device_type: Type of device (solar, wind, battery, load)
            count: Number of active devices
        """
        self.device_count.labels(device_type=device_type).set(count)
        logger.debug(f"Recorded device count: {device_type}={count}")

    def record_power_output(
        self,
        device_type: str,
        device_id: str,
        power_watts: float
    ) -> None:
        """
        Record power output for a device.

        Args:
            device_type: Type of device
            device_id: Unique device identifier
            power_watts: Power output in watts
        """
        self.power_output_watts.labels(
            device_type=device_type,
            device_id=device_id
        ).set(power_watts)

    def record_storage_soc(self, device_id: str, soc_percent: float) -> None:
        """
        Record battery state of charge.

        Args:
            device_id: Unique device identifier
            soc_percent: State of charge percentage (0-100)
        """
        self.storage_soc_percent.labels(device_id=device_id).set(soc_percent)

    def record_load(self, device_id: str, load_watts: float) -> None:
        """
        Record current load demand.

        Args:
            device_id: Unique device identifier
            load_watts: Load demand in watts
        """
        self.load_watts.labels(device_id=device_id).set(load_watts)

    def record_scenario_execution_time(
        self,
        scenario_id: str,
        duration_seconds: float
    ) -> None:
        """
        Record scenario execution time.

        Args:
            scenario_id: Unique scenario identifier
            duration_seconds: Execution duration in seconds
        """
        self.scenario_execution_time_seconds.labels(
            scenario_id=scenario_id
        ).observe(duration_seconds)

    def increment_scenario_count(self, status: str) -> None:
        """
        Increment scenario execution counter.

        Args:
            status: Scenario status (success, failure)
        """
        self.scenario_count.labels(status=status).inc()

    def set_scenario_status(self, scenario_id: str, status_code: int) -> None:
        """
        Set scenario status.

        Args:
            scenario_id: Unique scenario identifier
            status_code: Status code (0=pending, 1=running, 2=completed, 3=failed)
        """
        self.scenario_status.labels(scenario_id=scenario_id).set(status_code)

    def record_power_flow_calculation_time(self, duration_ms: float) -> None:
        """
        Record power flow calculation time.

        Args:
            duration_ms: Calculation duration in milliseconds
        """
        self.power_flow_calculation_time_ms.observe(duration_ms)

    def set_power_flow_violations(self, violation_type: str, count: int) -> None:
        """
        Set number of power flow violations.

        Args:
            violation_type: Type of violation (voltage, congestion)
            count: Number of violations
        """
        self.power_flow_violations.labels(violation_type=violation_type).set(count)

    def increment_convergence_failures(self) -> None:
        """Increment power flow convergence failure counter."""
        self.power_flow_convergence_failures.inc()

    def record_communication_latency(self, protocol: str, latency_ms: float) -> None:
        """
        Record communication latency.

        Args:
            protocol: Communication protocol (IEC104, MQTT, 5G)
            latency_ms: Latency in milliseconds
        """
        self.communication_latency_ms.labels(protocol=protocol).observe(latency_ms)

    def set_packet_loss_rate(self, protocol: str, loss_rate: float) -> None:
        """
        Set packet loss rate.

        Args:
            protocol: Communication protocol
            loss_rate: Packet loss rate (0-1)
        """
        self.packet_loss_rate.labels(protocol=protocol).set(loss_rate)

    def increment_messages_processed(
        self,
        protocol: str,
        message_type: str
    ) -> None:
        """
        Increment message processing counter.

        Args:
            protocol: Communication protocol
            message_type: Type of message
        """
        self.messages_processed.labels(
            protocol=protocol,
            message_type=message_type
        ).inc()

    def set_metrics_collection_rate(self, rate: float) -> None:
        """
        Set metrics collection rate.

        Args:
            rate: Metrics per second
        """
        self.metrics_collection_rate.set(rate)

    def set_active_scenarios(self, count: int) -> None:
        """
        Set number of active scenarios.

        Args:
            count: Number of active scenarios
        """
        self.active_scenarios.set(count)

    def set_database_connections(self, count: int) -> None:
        """
        Set database connection pool size.

        Args:
            count: Number of database connections
        """
        self.database_connections.set(count)

    def get_metrics(self) -> bytes:
        """
        Get all metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics as bytes
        """
        return generate_latest(self.registry)


# Global metrics instance
_metrics_instance: Optional[PrometheusMetrics] = None


def get_metrics() -> PrometheusMetrics:
    """
    Get or create the global metrics instance.

    Returns:
        PrometheusMetrics instance
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics()
    return _metrics_instance


def init_metrics(registry: Optional[CollectorRegistry] = None) -> PrometheusMetrics:
    """
    Initialize the global metrics instance.

    Args:
        registry: Optional custom CollectorRegistry

    Returns:
        PrometheusMetrics instance
    """
    global _metrics_instance
    _metrics_instance = PrometheusMetrics(registry=registry)
    return _metrics_instance
