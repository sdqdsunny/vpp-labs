"""
Real-time data exchange models for VPP system.

Defines data structures for:
- Power generation data
- Storage data
- Demand data
- Coordination results
- Commands
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Tuple, Optional
from enum import Enum


class DeviceStatus(str, Enum):
    """Device status enumeration."""
    RUNNING = "running"
    IDLE = "idle"
    ERROR = "error"


class ChargeStatus(str, Enum):
    """Charge status enumeration."""
    CHARGING = "charging"
    DISCHARGING = "discharging"
    IDLE = "idle"


class DRStatus(str, Enum):
    """Demand response status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class CommandStatus(str, Enum):
    """Command status enumeration."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PowerGenerationData:
    """Power generation side data model."""
    timestamp: datetime
    current_power: float  # Current power generation (kW)
    solar_power: float    # Solar power (kW)
    wind_power: float     # Wind power (kW)
    efficiency: float     # Generation efficiency (%)
    device_status: str    # Device status (running/idle/error)
    module_id: str = "vpp-power-generation"

    def to_dict(self):
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    def validate(self) -> bool:
        """Validate data completeness and ranges."""
        if not all([
            isinstance(self.current_power, (int, float)),
            isinstance(self.solar_power, (int, float)),
            isinstance(self.wind_power, (int, float)),
            isinstance(self.efficiency, (int, float)),
            self.device_status in [s.value for s in DeviceStatus],
        ]):
            return False
        
        # Check ranges
        if not (0 <= self.efficiency <= 100):
            return False
        if not (self.current_power >= 0 and self.solar_power >= 0 and self.wind_power >= 0):
            return False
        
        return True


@dataclass
class StorageData:
    """Storage side data model."""
    timestamp: datetime
    soc: float            # State of charge (%)
    soh: float            # State of health (%)
    current_power: float  # Current power (kW)
    charge_status: str    # Charge status (charging/discharging/idle)
    temperature: float    # Temperature (°C)
    module_id: str = "vpp-storage"

    def to_dict(self):
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    def validate(self) -> bool:
        """Validate data completeness and ranges."""
        if not all([
            isinstance(self.soc, (int, float)),
            isinstance(self.soh, (int, float)),
            isinstance(self.current_power, (int, float)),
            isinstance(self.temperature, (int, float)),
            self.charge_status in [s.value for s in ChargeStatus],
        ]):
            return False
        
        # Check ranges
        if not (0 <= self.soc <= 100 and 0 <= self.soh <= 100):
            return False
        if not (self.current_power >= 0):
            return False
        if not (-50 <= self.temperature <= 80):  # Reasonable temperature range
            return False
        
        return True


@dataclass
class DemandData:
    """Demand side data model."""
    timestamp: datetime
    current_load: float   # Current load (kW)
    forecast_load: float  # Forecasted load (kW)
    adjustable_range: Tuple[float, float]  # Adjustable range (min, max)
    dr_status: str        # Demand response status (active/inactive)
    module_id: str = "vpp-demand"

    def to_dict(self):
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['adjustable_range'] = list(self.adjustable_range)
        return data

    def validate(self) -> bool:
        """Validate data completeness and ranges."""
        if not all([
            isinstance(self.current_load, (int, float)),
            isinstance(self.forecast_load, (int, float)),
            isinstance(self.adjustable_range, (tuple, list)) and len(self.adjustable_range) == 2,
            self.dr_status in [s.value for s in DRStatus],
        ]):
            return False
        
        # Check ranges
        if not (self.current_load >= 0 and self.forecast_load >= 0):
            return False
        if not (self.adjustable_range[0] <= self.adjustable_range[1]):
            return False
        
        return True


@dataclass
class PowerCommand:
    """Power generation side command."""
    command_id: str
    target_power: float  # Target power (kW)
    duration: int        # Duration (seconds)
    priority: int        # Priority level

    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)

    def validate(self) -> bool:
        """Validate command."""
        if not all([
            isinstance(self.command_id, str) and len(self.command_id) > 0,
            isinstance(self.target_power, (int, float)) and self.target_power >= 0,
            isinstance(self.duration, int) and self.duration > 0,
            isinstance(self.priority, int) and 1 <= self.priority <= 10,
        ]):
            return False
        return True


@dataclass
class StorageCommand:
    """Storage side command."""
    command_id: str
    action: str          # Action (charging/discharging/idle)
    target_power: float  # Target power (kW)
    duration: int        # Duration (seconds)

    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)

    def validate(self) -> bool:
        """Validate command."""
        if not all([
            isinstance(self.command_id, str) and len(self.command_id) > 0,
            self.action in [s.value for s in ChargeStatus],
            isinstance(self.target_power, (int, float)) and self.target_power >= 0,
            isinstance(self.duration, int) and self.duration > 0,
        ]):
            return False
        return True


@dataclass
class DemandCommand:
    """Demand side command."""
    command_id: str
    action: str          # Action (increase/decrease/maintain)
    target_load: float   # Target load (kW)
    duration: int        # Duration (seconds)

    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)

    def validate(self) -> bool:
        """Validate command."""
        valid_actions = ["increase", "decrease", "maintain"]
        if not all([
            isinstance(self.command_id, str) and len(self.command_id) > 0,
            self.action in valid_actions,
            isinstance(self.target_load, (int, float)) and self.target_load >= 0,
            isinstance(self.duration, int) and self.duration > 0,
        ]):
            return False
        return True


@dataclass
class CommandResult:
    """Command execution result."""
    command_id: str
    status: str          # Status (pending/accepted/executing/completed/failed)
    result: Optional[dict] = None
    error_message: Optional[str] = None
    executed_at: Optional[datetime] = None

    def to_dict(self):
        """Convert to dictionary."""
        data = asdict(self)
        if self.executed_at:
            data['executed_at'] = self.executed_at.isoformat()
        return data


@dataclass
class CoordinationResult:
    """Coordination result from VCC."""
    timestamp: datetime
    power_command: PowerCommand
    storage_command: StorageCommand
    demand_command: DemandCommand
    optimization_score: float  # Optimization score (0-100)
    status: str                 # Status (success/failure)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'power_command': self.power_command.to_dict(),
            'storage_command': self.storage_command.to_dict(),
            'demand_command': self.demand_command.to_dict(),
            'optimization_score': self.optimization_score,
            'status': self.status,
        }
