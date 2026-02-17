"""
Data Transformers for Protocol Conversion

Provides transformation functions for converting data between different
protocol formats, units, and representations.
"""

from typing import Dict, Any, Union
import json
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Voltage Transformers
# ============================================================================

def scale_voltage_to_mv(data: Dict[str, Any]) -> float:
    """
    Convert voltage from volts (V) to millivolts (mV).
    
    Args:
        data: Dictionary containing 'voltage' key in volts
        
    Returns:
        Voltage in millivolts
    """
    voltage = data.get("voltage", 0)
    return float(voltage) * 1000


def scale_mv_to_voltage(data: Dict[str, Any]) -> float:
    """
    Convert voltage from millivolts (mV) to volts (V).
    
    Args:
        data: Dictionary containing 'voltage_mv' key in millivolts
        
    Returns:
        Voltage in volts
    """
    voltage_mv = data.get("voltage_mv", 0)
    return float(voltage_mv) / 1000


def validate_voltage_range(data: Dict[str, Any]) -> float:
    """
    Validate and return voltage within acceptable range (0-500V).
    
    Args:
        data: Dictionary containing 'voltage' key
        
    Returns:
        Voltage value if valid
        
    Raises:
        ValueError: If voltage is out of range
    """
    voltage = data.get("voltage", 0)
    voltage = float(voltage)
    
    if voltage < 0 or voltage > 500:
        logger.warning(f"Voltage {voltage}V out of range [0-500V]")
        # Clamp to valid range
        voltage = max(0, min(500, voltage))
    
    return voltage


# ============================================================================
# Current Transformers
# ============================================================================

def scale_current_to_ma(data: Dict[str, Any]) -> float:
    """
    Convert current from amperes (A) to milliamperes (mA).
    
    Args:
        data: Dictionary containing 'current' key in amperes
        
    Returns:
        Current in milliamperes
    """
    current = data.get("current", 0)
    return float(current) * 1000


def scale_ma_to_current(data: Dict[str, Any]) -> float:
    """
    Convert current from milliamperes (mA) to amperes (A).
    
    Args:
        data: Dictionary containing 'current_ma' key in milliamperes
        
    Returns:
        Current in amperes
    """
    current_ma = data.get("current_ma", 0)
    return float(current_ma) / 1000


def validate_current_range(data: Dict[str, Any]) -> float:
    """
    Validate and return current within acceptable range (0-1000A).
    
    Args:
        data: Dictionary containing 'current' key
        
    Returns:
        Current value if valid
        
    Raises:
        ValueError: If current is out of range
    """
    current = data.get("current", 0)
    current = float(current)
    
    if current < 0 or current > 1000:
        logger.warning(f"Current {current}A out of range [0-1000A]")
        # Clamp to valid range
        current = max(0, min(1000, current))
    
    return current


# ============================================================================
# Power Transformers
# ============================================================================

def scale_power_to_kw(data: Dict[str, Any]) -> float:
    """
    Convert power from watts (W) to kilowatts (kW).
    
    Args:
        data: Dictionary containing 'power' key in watts
        
    Returns:
        Power in kilowatts
    """
    power = data.get("power", 0)
    return float(power) / 1000


def scale_kw_to_power(data: Dict[str, Any]) -> float:
    """
    Convert power from kilowatts (kW) to watts (W).
    
    Args:
        data: Dictionary containing 'power_kw' key in kilowatts
        
    Returns:
        Power in watts
    """
    power_kw = data.get("power_kw", 0)
    return float(power_kw) * 1000


def validate_power_range(data: Dict[str, Any]) -> float:
    """
    Validate and return power within acceptable range (0-1000kW).
    
    Args:
        data: Dictionary containing 'power' key
        
    Returns:
        Power value if valid
    """
    power = data.get("power", 0)
    power = float(power)
    
    if power < 0 or power > 1000000:  # 1000 kW = 1,000,000 W
        logger.warning(f"Power {power}W out of range [0-1000000W]")
        # Clamp to valid range
        power = max(0, min(1000000, power))
    
    return power


# ============================================================================
# Status Transformers
# ============================================================================

def status_to_coil(data: Dict[str, Any]) -> bool:
    """
    Convert status string to Modbus coil (boolean).
    
    Args:
        data: Dictionary containing 'status' key
        
    Returns:
        Boolean coil value (True for 'on'/'active', False for 'off'/'inactive')
    """
    status = data.get("status", "off").lower()
    return status in ["on", "active", "true", "1", "enabled"]


def coil_to_status(data: Dict[str, Any]) -> str:
    """
    Convert Modbus coil (boolean) to status string.
    
    Args:
        data: Dictionary containing 'status_coil' key
        
    Returns:
        Status string ('on' or 'off')
    """
    coil = data.get("status_coil", False)
    return "on" if coil else "off"


def status_to_binary(data: Dict[str, Any]) -> int:
    """
    Convert status string to DNP3 binary input (0 or 1).
    
    Args:
        data: Dictionary containing 'status' key
        
    Returns:
        Binary value (1 for 'on'/'active', 0 for 'off'/'inactive')
    """
    status = data.get("status", "off").lower()
    return 1 if status in ["on", "active", "true", "1", "enabled"] else 0


def binary_to_status(data: Dict[str, Any]) -> str:
    """
    Convert DNP3 binary input (0 or 1) to status string.
    
    Args:
        data: Dictionary containing 'status' key
        
    Returns:
        Status string ('on' or 'off')
    """
    status = data.get("status", 0)
    return "on" if status else "off"


def coil_to_binary(data: Dict[str, Any]) -> int:
    """
    Convert Modbus coil (boolean) to DNP3 binary input (0 or 1).
    
    Args:
        data: Dictionary containing 'status_coil' key
        
    Returns:
        Binary value (1 or 0)
    """
    coil = data.get("status_coil", False)
    return 1 if coil else 0


def binary_to_coil(data: Dict[str, Any]) -> bool:
    """
    Convert DNP3 binary input (0 or 1) to Modbus coil (boolean).
    
    Args:
        data: Dictionary containing 'status' key
        
    Returns:
        Boolean coil value
    """
    status = data.get("status", 0)
    return bool(status)


# ============================================================================
# Timestamp Transformers
# ============================================================================

def timestamp_to_modbus(data: Dict[str, Any]) -> int:
    """
    Convert IEC 61850 timestamp (float) to Modbus register (int).
    
    Args:
        data: Dictionary containing 'timestamp' key
        
    Returns:
        Timestamp as integer (seconds since epoch)
    """
    timestamp = data.get("timestamp", 0)
    return int(float(timestamp))


def timestamp_from_modbus(data: Dict[str, Any]) -> float:
    """
    Convert Modbus register (int) to IEC 61850 timestamp (float).
    
    Args:
        data: Dictionary containing 'timestamp' key
        
    Returns:
        Timestamp as float (seconds since epoch)
    """
    timestamp = data.get("timestamp", 0)
    return float(timestamp)


# ============================================================================
# MQTT Format Transformers
# ============================================================================

def format_for_mqtt(data: Dict[str, Any]) -> Any:
    """
    Format data for MQTT JSON payload.
    
    Args:
        data: Dictionary with any value
        
    Returns:
        Value formatted for MQTT (preserves type)
    """
    # Extract the first non-None value from the data dict
    for key, value in data.items():
        if value is not None:
            return value
    return None


def parse_from_mqtt(data: Dict[str, Any]) -> Any:
    """
    Parse data from MQTT JSON payload.
    
    Args:
        data: Dictionary with MQTT payload
        
    Returns:
        Parsed value
    """
    # Extract the first non-None value from the data dict
    for key, value in data.items():
        if value is not None:
            return value
    return None


def scale_and_format_mqtt(data: Dict[str, Any]) -> float:
    """
    Scale value and format for MQTT JSON payload.
    
    Handles conversion from mV/mA/kW to V/A/W and formats for MQTT.
    
    Args:
        data: Dictionary with scaled value (mV, mA, or kW)
        
    Returns:
        Scaled value formatted for MQTT
    """
    # Check which type of value we have
    if "voltage_mv" in data:
        return scale_mv_to_voltage(data)
    elif "current_ma" in data:
        return scale_ma_to_current(data)
    elif "power_kw" in data:
        return scale_kw_to_power(data)
    
    # Default: return first non-None value
    for key, value in data.items():
        if value is not None:
            return value
    return None


def parse_and_scale_mv(data: Dict[str, Any]) -> float:
    """
    Parse MQTT value and scale to millivolts.
    
    Args:
        data: Dictionary with voltage value in volts
        
    Returns:
        Voltage in millivolts
    """
    return scale_voltage_to_mv(data)


def parse_and_scale_ma(data: Dict[str, Any]) -> float:
    """
    Parse MQTT value and scale to milliamperes.
    
    Args:
        data: Dictionary with current value in amperes
        
    Returns:
        Current in milliamperes
    """
    return scale_current_to_ma(data)


def parse_and_scale_kw(data: Dict[str, Any]) -> float:
    """
    Parse MQTT value and scale to kilowatts.
    
    Args:
        data: Dictionary with power value in watts
        
    Returns:
        Power in kilowatts
    """
    return scale_power_to_kw(data)


# ============================================================================
# Transformer Registry
# ============================================================================

TRANSFORMERS = {
    # Voltage transformers
    "scale_voltage_to_mv": scale_voltage_to_mv,
    "scale_mv_to_voltage": scale_mv_to_voltage,
    "validate_voltage_range": validate_voltage_range,
    
    # Current transformers
    "scale_current_to_ma": scale_current_to_ma,
    "scale_ma_to_current": scale_ma_to_current,
    "validate_current_range": validate_current_range,
    
    # Power transformers
    "scale_power_to_kw": scale_power_to_kw,
    "scale_kw_to_power": scale_kw_to_power,
    "validate_power_range": validate_power_range,
    
    # Status transformers
    "status_to_coil": status_to_coil,
    "coil_to_status": coil_to_status,
    "status_to_binary": status_to_binary,
    "binary_to_status": binary_to_status,
    "coil_to_binary": coil_to_binary,
    "binary_to_coil": binary_to_coil,
    
    # Timestamp transformers
    "timestamp_to_modbus": timestamp_to_modbus,
    "timestamp_from_modbus": timestamp_from_modbus,
    
    # MQTT format transformers
    "format_for_mqtt": format_for_mqtt,
    "parse_from_mqtt": parse_from_mqtt,
    "scale_and_format_mqtt": scale_and_format_mqtt,
    "parse_and_scale_mv": parse_and_scale_mv,
    "parse_and_scale_ma": parse_and_scale_ma,
    "parse_and_scale_kw": parse_and_scale_kw,
}
