"""
Message Validators for Protocol Conversion

Provides validation functions for ensuring message integrity and correctness
during protocol conversion.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Data Range Validators
# ============================================================================

def validate_voltage_range(message: Dict[str, Any]) -> bool:
    """
    Validate voltage is within acceptable range (0-500V).
    
    Args:
        message: Message dictionary containing voltage
        
    Returns:
        True if voltage is valid, False otherwise
    """
    voltage = message.get("voltage")
    if voltage is None:
        logger.warning("Voltage field missing")
        return False
    
    try:
        voltage = float(voltage)
        if voltage < 0 or voltage > 500:
            logger.warning(f"Voltage {voltage}V out of range [0-500V]")
            return False
        return True
    except (ValueError, TypeError):
        logger.warning(f"Invalid voltage value: {voltage}")
        return False


def validate_current_range(message: Dict[str, Any]) -> bool:
    """
    Validate current is within acceptable range (0-1000A).
    
    Args:
        message: Message dictionary containing current
        
    Returns:
        True if current is valid, False otherwise
    """
    current = message.get("current")
    if current is None:
        logger.warning("Current field missing")
        return False
    
    try:
        current = float(current)
        if current < 0 or current > 1000:
            logger.warning(f"Current {current}A out of range [0-1000A]")
            return False
        return True
    except (ValueError, TypeError):
        logger.warning(f"Invalid current value: {current}")
        return False


def validate_power_range(message: Dict[str, Any]) -> bool:
    """
    Validate power is within acceptable range (0-1000kW).
    
    Args:
        message: Message dictionary containing power
        
    Returns:
        True if power is valid, False otherwise
    """
    power = message.get("power")
    if power is None:
        logger.warning("Power field missing")
        return False
    
    try:
        power = float(power)
        if power < 0 or power > 1000000:  # 1000 kW = 1,000,000 W
            logger.warning(f"Power {power}W out of range [0-1000000W]")
            return False
        return True
    except (ValueError, TypeError):
        logger.warning(f"Invalid power value: {power}")
        return False


def validate_frequency_range(message: Dict[str, Any]) -> bool:
    """
    Validate frequency is within acceptable range (40-60Hz).
    
    Args:
        message: Message dictionary containing frequency
        
    Returns:
        True if frequency is valid, False otherwise
    """
    frequency = message.get("frequency", 50)
    
    try:
        frequency = float(frequency)
        if frequency < 40 or frequency > 60:
            logger.warning(f"Frequency {frequency}Hz out of range [40-60Hz]")
            return False
        return True
    except (ValueError, TypeError):
        logger.warning(f"Invalid frequency value: {frequency}")
        return False


# ============================================================================
# Format Validators
# ============================================================================

def validate_status_format(message: Dict[str, Any]) -> bool:
    """
    Validate status field has valid format.
    
    Args:
        message: Message dictionary containing status
        
    Returns:
        True if status format is valid, False otherwise
    """
    status = message.get("status")
    if status is None:
        logger.warning("Status field missing")
        return False
    
    valid_statuses = ["on", "off", "active", "inactive", "true", "false", "1", "0", "enabled", "disabled"]
    status_str = str(status).lower()
    
    if status_str not in valid_statuses:
        logger.warning(f"Invalid status value: {status}")
        return False
    
    return True


def validate_timestamp_format(message: Dict[str, Any]) -> bool:
    """
    Validate timestamp field has valid format.
    
    Args:
        message: Message dictionary containing timestamp
        
    Returns:
        True if timestamp format is valid, False otherwise
    """
    timestamp = message.get("timestamp")
    if timestamp is None:
        logger.warning("Timestamp field missing")
        return False
    
    try:
        timestamp = float(timestamp)
        # Timestamp should be positive and reasonable (after 2000-01-01)
        if timestamp < 946684800:  # 2000-01-01 00:00:00 UTC
            logger.warning(f"Timestamp {timestamp} is before 2000-01-01")
            return False
        return True
    except (ValueError, TypeError):
        logger.warning(f"Invalid timestamp value: {timestamp}")
        return False


def validate_quality_format(message: Dict[str, Any]) -> bool:
    """
    Validate quality field has valid format.
    
    Args:
        message: Message dictionary containing quality
        
    Returns:
        True if quality format is valid, False otherwise
    """
    quality = message.get("quality", "good")
    valid_qualities = ["good", "bad", "questionable", "reserved"]
    quality_str = str(quality).lower()
    
    if quality_str not in valid_qualities:
        logger.warning(f"Invalid quality value: {quality}")
        return False
    
    return True


# ============================================================================
# Completeness Validators
# ============================================================================

def validate_iec61850_message(message: Dict[str, Any]) -> bool:
    """
    Validate IEC 61850 message has all required fields.
    
    Args:
        message: Message dictionary
        
    Returns:
        True if message is complete, False otherwise
    """
    required_fields = ["voltage", "current", "frequency", "status", "timestamp"]
    
    for field in required_fields:
        if field not in message:
            logger.warning(f"IEC 61850 message missing required field: {field}")
            return False
    
    # Validate each field
    if not validate_voltage_range(message):
        return False
    if not validate_current_range(message):
        return False
    if not validate_frequency_range(message):
        return False
    if not validate_status_format(message):
        return False
    if not validate_timestamp_format(message):
        return False
    
    return True


def validate_modbus_message(message: Dict[str, Any]) -> bool:
    """
    Validate Modbus message has all required fields.
    
    Args:
        message: Message dictionary
        
    Returns:
        True if message is complete, False otherwise
    """
    # Modbus messages can have various fields depending on function code
    # At minimum, should have some data
    if not message or len(message) == 0:
        logger.warning("Modbus message is empty")
        return False
    
    # Validate numeric fields if present
    numeric_fields = ["voltage_mv", "current_ma", "power_kw", "frequency"]
    for field in numeric_fields:
        if field in message:
            try:
                float(message[field])
            except (ValueError, TypeError):
                logger.warning(f"Invalid numeric value for {field}: {message[field]}")
                return False
    
    return True


def validate_dnp3_message(message: Dict[str, Any]) -> bool:
    """
    Validate DNP3 message has all required fields.
    
    Args:
        message: Message dictionary
        
    Returns:
        True if message is complete, False otherwise
    """
    # DNP3 messages should have at least one data point
    if not message or len(message) == 0:
        logger.warning("DNP3 message is empty")
        return False
    
    # Validate quality field if present
    if "quality" in message:
        if not validate_quality_format(message):
            return False
    
    return True


def validate_mqtt_message(message: Dict[str, Any]) -> bool:
    """
    Validate MQTT message has valid format.
    
    Args:
        message: Message dictionary
        
    Returns:
        True if message is valid, False otherwise
    """
    # MQTT messages should have at least one field
    if not message or len(message) == 0:
        logger.warning("MQTT message is empty")
        return False
    
    # All values should be serializable to JSON
    try:
        import json
        json.dumps(message)
        return True
    except (TypeError, ValueError):
        logger.warning("MQTT message contains non-JSON-serializable values")
        return False


# ============================================================================
# Protocol-Specific Validators
# ============================================================================

def validate_iec61850_to_modbus(message: Dict[str, Any]) -> bool:
    """
    Validate IEC 61850 message before conversion to Modbus.
    
    Args:
        message: IEC 61850 message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_iec61850_message(message)


def validate_modbus_to_iec61850(message: Dict[str, Any]) -> bool:
    """
    Validate Modbus message before conversion to IEC 61850.
    
    Args:
        message: Modbus message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_modbus_message(message)


def validate_iec61850_to_dnp3(message: Dict[str, Any]) -> bool:
    """
    Validate IEC 61850 message before conversion to DNP3.
    
    Args:
        message: IEC 61850 message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_iec61850_message(message)


def validate_dnp3_to_iec61850(message: Dict[str, Any]) -> bool:
    """
    Validate DNP3 message before conversion to IEC 61850.
    
    Args:
        message: DNP3 message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_dnp3_message(message)


def validate_iec61850_to_mqtt(message: Dict[str, Any]) -> bool:
    """
    Validate IEC 61850 message before conversion to MQTT.
    
    Args:
        message: IEC 61850 message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_iec61850_message(message)


def validate_mqtt_to_iec61850(message: Dict[str, Any]) -> bool:
    """
    Validate MQTT message before conversion to IEC 61850.
    
    Args:
        message: MQTT message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_mqtt_message(message)


def validate_modbus_to_dnp3(message: Dict[str, Any]) -> bool:
    """
    Validate Modbus message before conversion to DNP3.
    
    Args:
        message: Modbus message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_modbus_message(message)


def validate_dnp3_to_modbus(message: Dict[str, Any]) -> bool:
    """
    Validate DNP3 message before conversion to Modbus.
    
    Args:
        message: DNP3 message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_dnp3_message(message)


def validate_modbus_to_mqtt(message: Dict[str, Any]) -> bool:
    """
    Validate Modbus message before conversion to MQTT.
    
    Args:
        message: Modbus message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_modbus_message(message)


def validate_mqtt_to_modbus(message: Dict[str, Any]) -> bool:
    """
    Validate MQTT message before conversion to Modbus.
    
    Args:
        message: MQTT message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_mqtt_message(message)


def validate_dnp3_to_mqtt(message: Dict[str, Any]) -> bool:
    """
    Validate DNP3 message before conversion to MQTT.
    
    Args:
        message: DNP3 message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_dnp3_message(message)


def validate_mqtt_to_dnp3(message: Dict[str, Any]) -> bool:
    """
    Validate MQTT message before conversion to DNP3.
    
    Args:
        message: MQTT message
        
    Returns:
        True if message is valid for conversion, False otherwise
    """
    return validate_mqtt_message(message)


# ============================================================================
# Validator Registry
# ============================================================================

VALIDATORS = {
    # Data range validators
    "validate_voltage_range": validate_voltage_range,
    "validate_current_range": validate_current_range,
    "validate_power_range": validate_power_range,
    "validate_frequency_range": validate_frequency_range,
    
    # Format validators
    "validate_status_format": validate_status_format,
    "validate_timestamp_format": validate_timestamp_format,
    "validate_quality_format": validate_quality_format,
    
    # Completeness validators
    "validate_iec61850_message": validate_iec61850_message,
    "validate_modbus_message": validate_modbus_message,
    "validate_dnp3_message": validate_dnp3_message,
    "validate_mqtt_message": validate_mqtt_message,
    
    # Protocol-specific validators
    "validate_iec61850_to_modbus": validate_iec61850_to_modbus,
    "validate_modbus_to_iec61850": validate_modbus_to_iec61850,
    "validate_iec61850_to_dnp3": validate_iec61850_to_dnp3,
    "validate_dnp3_to_iec61850": validate_dnp3_to_iec61850,
    "validate_iec61850_to_mqtt": validate_iec61850_to_mqtt,
    "validate_mqtt_to_iec61850": validate_mqtt_to_iec61850,
    "validate_modbus_to_dnp3": validate_modbus_to_dnp3,
    "validate_dnp3_to_modbus": validate_dnp3_to_modbus,
    "validate_modbus_to_mqtt": validate_modbus_to_mqtt,
    "validate_mqtt_to_modbus": validate_mqtt_to_modbus,
    "validate_dnp3_to_mqtt": validate_dnp3_to_mqtt,
    "validate_mqtt_to_dnp3": validate_mqtt_to_dnp3,
}
