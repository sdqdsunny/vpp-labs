"""
Prometheus Metrics - Simplified stub implementation.

This module provides a minimal metrics interface without external dependencies.
"""


class PrometheusMetrics:
    """Simplified metrics collector without Prometheus dependency."""
    
    def __init__(self, registry=None):
        """Initialize metrics collector."""
        pass
    
    def record_device_count(self, device_type: str, count: int) -> None:
        """Record device count."""
        pass
    
    def record_power_output(self, device_id: str, power_watts: float) -> None:
        """Record power output."""
        pass
    
    def record_storage_soc(self, device_id: str, soc_percent: float) -> None:
        """Record storage state of charge."""
        pass
    
    def record_load(self, device_id: str, load_watts: float) -> None:
        """Record load."""
        pass
    
    def record_scenario_execution_time(self, scenario_id: str, duration_ms: float) -> None:
        """Record scenario execution time."""
        pass
    
    def increment_scenario_count(self, status: str) -> None:
        """Increment scenario count."""
        pass
    
    def set_scenario_status(self, scenario_id: str, status_code: int) -> None:
        """Set scenario status."""
        pass
    
    def record_power_flow_calculation_time(self, duration_ms: float) -> None:
        """Record power flow calculation time."""
        pass
    
    def set_power_flow_violations(self, violation_type: str, count: int) -> None:
        """Set power flow violations."""
        pass
    
    def increment_convergence_failures(self) -> None:
        """Increment convergence failures."""
        pass
    
    def record_communication_latency(self, protocol: str, latency_ms: float) -> None:
        """Record communication latency."""
        pass
    
    def set_packet_loss_rate(self, protocol: str, loss_rate: float) -> None:
        """Set packet loss rate."""
        pass
    
    def increment_messages_processed(self, protocol: str, count: int = 1) -> None:
        """Increment messages processed."""
        pass
    
    def set_metrics_collection_rate(self, rate: float) -> None:
        """Set metrics collection rate."""
        pass
    
    def set_active_scenarios(self, count: int) -> None:
        """Set active scenarios."""
        pass
    
    def set_database_connections(self, count: int) -> None:
        """Set database connections."""
        pass
    
    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format."""
        return b"# No metrics available\n"


# Global metrics instance
_metrics_instance = None


def get_metrics() -> PrometheusMetrics:
    """Get the global metrics instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics()
    return _metrics_instance


def init_metrics(registry=None) -> PrometheusMetrics:
    """Initialize metrics."""
    global _metrics_instance
    _metrics_instance = PrometheusMetrics(registry)
    return _metrics_instance
