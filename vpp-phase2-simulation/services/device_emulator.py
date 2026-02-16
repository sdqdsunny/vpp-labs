"""
Device Emulator base class for VPP Phase 2 Simulation Framework.

Provides standard interface for all device simulators (solar, wind, battery, load).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DeviceCommand:
    """Represents a command issued to a device."""

    command_type: str  # e.g., "charge", "discharge", "set_output"
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CommandResult:
    """Result of executing a device command."""

    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DeviceState:
    """Current state of a device."""

    device_id: str
    device_type: str
    state_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DeviceEmulator(ABC):
    """
    Abstract base class for all device emulators.

    Defines standard interface for device simulators including initialization,
    state management, command processing, and capability reporting.
    """

    def __init__(
        self,
        device_id: str,
        device_type: str,
        parameters: Dict[str, Any]
    ):
        """
        Initialize device emulator.

        Args:
            device_id: Unique device identifier
            device_type: Type of device (solar, wind, battery, load)
            parameters: Device-specific parameters
        """
        self.device_id = device_id
        self.device_type = device_type
        self.parameters = parameters
        self.state: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()

        logger.info(
            f"Device emulator initialized: {device_id} ({device_type})",
            extra={"device_id": device_id, "device_type": device_type}
        )

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize device state.

        Called after __init__ to set up initial state.
        """
        pass

    @abstractmethod
    def update(self, time_delta: float) -> None:
        """
        Update device state for time step.

        Args:
            time_delta: Time elapsed since last update (seconds)
        """
        pass

    @abstractmethod
    def get_state(self) -> DeviceState:
        """
        Get current device state.

        Returns:
            DeviceState with current state data
        """
        pass

    @abstractmethod
    def set_command(self, command: DeviceCommand) -> CommandResult:
        """
        Process command and update device state.

        Args:
            command: Command to execute

        Returns:
            CommandResult with success status and data
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get device capabilities.

        Returns:
            Dictionary describing device capabilities
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset device to initial state."""
        pass

    def validate_parameters(self, required_params: List[str]) -> bool:
        """
        Validate that required parameters are present.

        Args:
            required_params: List of required parameter names

        Returns:
            True if all required parameters present
        """
        for param in required_params:
            if param not in self.parameters:
                logger.error(
                    f"Missing required parameter: {param}",
                    extra={"device_id": self.device_id, "parameter": param}
                )
                return False
        return True

    def _update_timestamp(self) -> None:
        """Update last_updated timestamp."""
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary."""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "parameters": self.parameters,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }
