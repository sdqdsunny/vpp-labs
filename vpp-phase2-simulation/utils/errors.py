"""
Custom exception classes for VPP Phase 2 Simulation Framework.

Provides a hierarchy of exceptions for different error scenarios.
"""


class SimulationException(Exception):
    """Base exception for all simulation errors."""

    def __init__(self, message: str, code: str = "SIMULATION_ERROR", details: dict = None):
        """
        Initialize simulation exception.

        Args:
            message: Error message
            code: Error code for API responses
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class SimulatorError(SimulationException):
    """Simulator execution failed."""

    def __init__(self, message: str, simulator_id: str = None, **kwargs):
        """Initialize simulator error."""
        super().__init__(message, code="SIMULATOR_ERROR", details=kwargs)
        self.simulator_id = simulator_id


class ScenarioExecutionError(SimulationException):
    """Scenario execution failed."""

    def __init__(self, message: str, scenario_id: str = None, **kwargs):
        """Initialize scenario execution error."""
        super().__init__(message, code="SCENARIO_EXECUTION_ERROR", details=kwargs)
        self.scenario_id = scenario_id


class PowerFlowError(SimulationException):
    """Power flow calculation failed."""

    def __init__(self, message: str, **kwargs):
        """Initialize power flow error."""
        super().__init__(message, code="POWER_FLOW_ERROR", details=kwargs)


class CommunicationSimulationError(SimulationException):
    """Communication simulation failed."""

    def __init__(self, message: str, protocol: str = None, **kwargs):
        """Initialize communication simulation error."""
        super().__init__(message, code="COMMUNICATION_ERROR", details=kwargs)
        self.protocol = protocol


class DatabaseError(SimulationException):
    """Database operation failed."""

    def __init__(self, message: str, **kwargs):
        """Initialize database error."""
        super().__init__(message, code="DATABASE_ERROR", details=kwargs)


class ValidationError(SimulationException):
    """Data validation failed."""

    def __init__(self, message: str, field: str = None, **kwargs):
        """Initialize validation error."""
        super().__init__(message, code="VALIDATION_ERROR", details=kwargs)
        self.field = field


class ConfigurationError(SimulationException):
    """Configuration error."""

    def __init__(self, message: str, **kwargs):
        """Initialize configuration error."""
        super().__init__(message, code="CONFIGURATION_ERROR", details=kwargs)


class TimeoutError(SimulationException):
    """Operation timeout."""

    def __init__(self, message: str, timeout_ms: int = None, **kwargs):
        """Initialize timeout error."""
        super().__init__(message, code="TIMEOUT_ERROR", details=kwargs)
        self.timeout_ms = timeout_ms
