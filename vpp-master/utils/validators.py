"""
Data Validation Utilities

Provides validation functions for API requests and data models using Pydantic.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    """Supported device types"""
    SOLAR = "solar"
    WIND = "wind"
    BATTERY = "battery"
    LOAD = "load"
    GRID = "grid"


class DeviceStatus(str, Enum):
    """Device status values"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class DispatchStatus(str, Enum):
    """Dispatch status values"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class CommandType(str, Enum):
    """Dispatch command types"""
    POWER_ADJUST = "power_adjust"
    MODE_CHANGE = "mode_change"
    PARAMETER_UPDATE = "parameter_update"
    EMERGENCY_STOP = "emergency_stop"


class Protocol(str, Enum):
    """Supported protocols"""
    IEC_104 = "iec_104"
    MQTT = "mqtt"
    IEC_61850 = "iec_61850"
    MODBUS = "modbus"


class DeviceRegistration(BaseModel):
    """Device registration request validation"""
    
    model_config = ConfigDict(use_enum_values=True)
    
    device_id: str = Field(..., min_length=1, max_length=255, description="Unique device identifier")
    device_type: DeviceType = Field(..., description="Type of device")
    location: str = Field(..., min_length=1, max_length=255, description="Device location")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Device capabilities")


class DeviceConfig(BaseModel):
    """Device configuration update validation"""
    
    model_config = ConfigDict(use_enum_values=True)
    
    power_limit: Optional[float] = Field(None, ge=0, description="Maximum power limit in kW")
    mode: Optional[str] = Field(None, description="Device operation mode")
    priority_level: Optional[int] = Field(None, ge=0, le=10, description="Priority level 0-10")


class DispatchRequest(BaseModel):
    """Dispatch command creation validation"""
    
    model_config = ConfigDict(use_enum_values=True)
    
    device_id: str = Field(..., min_length=1, description="Target device ID")
    command_type: CommandType = Field(..., description="Type of dispatch command")
    target_value: float = Field(..., description="Target value for the command")
    priority_level: int = Field(default=0, ge=0, le=10, description="Priority level 0-10")


class ScheduledDispatchRequest(BaseModel):
    """Scheduled dispatch creation validation"""
    
    model_config = ConfigDict(use_enum_values=True)
    
    device_id: str = Field(..., min_length=1, description="Target device ID")
    command_type: CommandType = Field(..., description="Type of dispatch command")
    target_value: float = Field(..., description="Target value for the command")
    priority_level: int = Field(default=0, ge=0, le=10, description="Priority level 0-10")
    execution_time: datetime = Field(..., description="Scheduled execution time")


class ProtocolMessage(BaseModel):
    """Protocol message validation"""
    
    model_config = ConfigDict(use_enum_values=True)
    
    protocol: Protocol = Field(..., description="Protocol type")
    data: Dict[str, Any] = Field(..., description="Message data")


class ProtocolMappingConfig(BaseModel):
    """Protocol mapping configuration validation"""
    
    model_config = ConfigDict(use_enum_values=True)
    
    source_protocol: Protocol = Field(..., description="Source protocol")
    target_protocol: Protocol = Field(..., description="Target protocol")
    mapping_rules: Dict[str, Any] = Field(..., description="Mapping rules")


class PowerFlowAnalysisRequest(BaseModel):
    """Power flow analysis request validation"""
    
    model_config = ConfigDict(use_enum_values=True)
    
    system_state: Dict[str, Any] = Field(..., description="Current system state")


class StabilityAnalysisRequest(BaseModel):
    """Stability analysis request validation"""
    
    model_config = ConfigDict(use_enum_values=True)
    
    system_state: Dict[str, Any] = Field(..., description="Current system state")


class MetricsRequest(BaseModel):
    """Metrics calculation request validation"""
    
    model_config = ConfigDict(use_enum_values=True)
    
    start_time: datetime = Field(..., description="Start time for metrics")
    end_time: datetime = Field(..., description="End time for metrics")
    aggregation: str = Field(default="hourly", description="Aggregation level: hourly, daily, monthly")


class ReportRequest(BaseModel):
    """Report generation request validation"""
    
    model_config = ConfigDict(use_enum_values=True)
    
    report_type: str = Field(..., description="Type of report: performance, vulnerability, analysis")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Report filters")


def validate_device_id(device_id: str) -> bool:
    """Validate device ID format"""
    return len(device_id) > 0 and len(device_id) <= 255


def validate_power_value(value: float) -> bool:
    """Validate power value"""
    return value >= 0


def validate_priority_level(level: int) -> bool:
    """Validate priority level"""
    return 0 <= level <= 10
