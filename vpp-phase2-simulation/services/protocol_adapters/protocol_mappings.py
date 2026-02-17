"""
Protocol Mapping Rules

Defines mapping rules between different industrial control protocols.
Supports 6 bidirectional protocol pairs:
- IEC 61850 ↔ Modbus
- IEC 61850 ↔ DNP3
- IEC 61850 ↔ MQTT
- Modbus ↔ DNP3
- Modbus ↔ MQTT
- DNP3 ↔ MQTT
"""

from typing import Dict, Any


# ============================================================================
# IEC 61850 ↔ Modbus Mappings
# ============================================================================

IEC61850_TO_MODBUS = {
    # Voltage mapping: IEC 61850 voltage (V) → Modbus holding register (mV)
    "voltage_mv": {
        "source": "voltage",
        "transformer": "scale_voltage_to_mv",
    },
    # Current mapping: IEC 61850 current (A) → Modbus holding register (mA)
    "current_ma": {
        "source": "current",
        "transformer": "scale_current_to_ma",
    },
    # Frequency mapping: IEC 61850 frequency (Hz) → Modbus holding register
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: IEC 61850 power (W) → Modbus holding register (kW)
    "power_kw": {
        "source": "power",
        "transformer": "scale_power_to_kw",
    },
    # Status mapping: IEC 61850 status → Modbus coil
    "status_coil": {
        "source": "status",
        "transformer": "status_to_coil",
    },
    # Timestamp mapping: IEC 61850 timestamp → Modbus register
    "timestamp": {
        "source": "timestamp",
        "transformer": "timestamp_to_modbus",
    },
}

MODBUS_TO_IEC61850 = {
    # Voltage mapping: Modbus holding register (mV) → IEC 61850 voltage (V)
    "voltage": {
        "source": "voltage_mv",
        "transformer": "scale_mv_to_voltage",
    },
    # Current mapping: Modbus holding register (mA) → IEC 61850 current (A)
    "current": {
        "source": "current_ma",
        "transformer": "scale_ma_to_current",
    },
    # Frequency mapping: Modbus holding register → IEC 61850 frequency (Hz)
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: Modbus holding register (kW) → IEC 61850 power (W)
    "power": {
        "source": "power_kw",
        "transformer": "scale_kw_to_power",
    },
    # Status mapping: Modbus coil → IEC 61850 status
    "status": {
        "source": "status_coil",
        "transformer": "coil_to_status",
    },
    # Timestamp mapping: Modbus register → IEC 61850 timestamp
    "timestamp": {
        "source": "timestamp",
        "transformer": "timestamp_from_modbus",
    },
}


# ============================================================================
# IEC 61850 ↔ DNP3 Mappings
# ============================================================================

IEC61850_TO_DNP3 = {
    # Voltage mapping: IEC 61850 voltage (V) → DNP3 analog input
    "voltage": {
        "source": "voltage",
        "transformer": "validate_voltage_range",
    },
    # Current mapping: IEC 61850 current (A) → DNP3 analog input
    "current": {
        "source": "current",
        "transformer": "validate_current_range",
    },
    # Frequency mapping: IEC 61850 frequency (Hz) → DNP3 analog input
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: IEC 61850 power (W) → DNP3 analog input
    "power": {
        "source": "power",
        "transformer": "validate_power_range",
    },
    # Status mapping: IEC 61850 status → DNP3 binary input
    "status": {
        "source": "status",
        "transformer": "status_to_binary",
    },
    # Quality mapping: IEC 61850 quality → DNP3 quality flags
    "quality": {
        "source": "quality",
        "default": "good",
    },
}

DNP3_TO_IEC61850 = {
    # Voltage mapping: DNP3 analog input → IEC 61850 voltage (V)
    "voltage": {
        "source": "voltage",
        "transformer": "validate_voltage_range",
    },
    # Current mapping: DNP3 analog input → IEC 61850 current (A)
    "current": {
        "source": "current",
        "transformer": "validate_current_range",
    },
    # Frequency mapping: DNP3 analog input → IEC 61850 frequency (Hz)
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: DNP3 analog input → IEC 61850 power (W)
    "power": {
        "source": "power",
        "transformer": "validate_power_range",
    },
    # Status mapping: DNP3 binary input → IEC 61850 status
    "status": {
        "source": "status",
        "transformer": "binary_to_status",
    },
    # Quality mapping: DNP3 quality flags → IEC 61850 quality
    "quality": {
        "source": "quality",
        "default": "good",
    },
}


# ============================================================================
# IEC 61850 ↔ MQTT Mappings
# ============================================================================

IEC61850_TO_MQTT = {
    # Voltage mapping: IEC 61850 voltage (V) → MQTT JSON payload
    "voltage": {
        "source": "voltage",
        "transformer": "format_for_mqtt",
    },
    # Current mapping: IEC 61850 current (A) → MQTT JSON payload
    "current": {
        "source": "current",
        "transformer": "format_for_mqtt",
    },
    # Frequency mapping: IEC 61850 frequency (Hz) → MQTT JSON payload
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: IEC 61850 power (W) → MQTT JSON payload
    "power": {
        "source": "power",
        "transformer": "format_for_mqtt",
    },
    # Status mapping: IEC 61850 status → MQTT JSON payload
    "status": {
        "source": "status",
        "transformer": "format_for_mqtt",
    },
    # Timestamp mapping: IEC 61850 timestamp → MQTT JSON payload
    "timestamp": {
        "source": "timestamp",
        "transformer": "format_for_mqtt",
    },
}

MQTT_TO_IEC61850 = {
    # Voltage mapping: MQTT JSON payload → IEC 61850 voltage (V)
    "voltage": {
        "source": "voltage",
        "transformer": "parse_from_mqtt",
    },
    # Current mapping: MQTT JSON payload → IEC 61850 current (A)
    "current": {
        "source": "current",
        "transformer": "parse_from_mqtt",
    },
    # Frequency mapping: MQTT JSON payload → IEC 61850 frequency (Hz)
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: MQTT JSON payload → IEC 61850 power (W)
    "power": {
        "source": "power",
        "transformer": "parse_from_mqtt",
    },
    # Status mapping: MQTT JSON payload → IEC 61850 status
    "status": {
        "source": "status",
        "transformer": "parse_from_mqtt",
    },
    # Timestamp mapping: MQTT JSON payload → IEC 61850 timestamp
    "timestamp": {
        "source": "timestamp",
        "transformer": "parse_from_mqtt",
    },
}


# ============================================================================
# Modbus ↔ DNP3 Mappings
# ============================================================================

MODBUS_TO_DNP3 = {
    # Voltage mapping: Modbus holding register (mV) → DNP3 analog input (V)
    "voltage": {
        "source": "voltage_mv",
        "transformer": "scale_mv_to_voltage",
    },
    # Current mapping: Modbus holding register (mA) → DNP3 analog input (A)
    "current": {
        "source": "current_ma",
        "transformer": "scale_ma_to_current",
    },
    # Frequency mapping: Modbus holding register → DNP3 analog input
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: Modbus holding register (kW) → DNP3 analog input (W)
    "power": {
        "source": "power_kw",
        "transformer": "scale_kw_to_power",
    },
    # Status mapping: Modbus coil → DNP3 binary input
    "status": {
        "source": "status_coil",
        "transformer": "coil_to_binary",
    },
}

DNP3_TO_MODBUS = {
    # Voltage mapping: DNP3 analog input (V) → Modbus holding register (mV)
    "voltage_mv": {
        "source": "voltage",
        "transformer": "scale_voltage_to_mv",
    },
    # Current mapping: DNP3 analog input (A) → Modbus holding register (mA)
    "current_ma": {
        "source": "current",
        "transformer": "scale_current_to_ma",
    },
    # Frequency mapping: DNP3 analog input → Modbus holding register
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: DNP3 analog input (W) → Modbus holding register (kW)
    "power_kw": {
        "source": "power",
        "transformer": "scale_power_to_kw",
    },
    # Status mapping: DNP3 binary input → Modbus coil
    "status_coil": {
        "source": "status",
        "transformer": "binary_to_coil",
    },
}


# ============================================================================
# Modbus ↔ MQTT Mappings
# ============================================================================

MODBUS_TO_MQTT = {
    # Voltage mapping: Modbus holding register (mV) → MQTT JSON payload
    "voltage": {
        "source": "voltage_mv",
        "transformer": "scale_and_format_mqtt",
    },
    # Current mapping: Modbus holding register (mA) → MQTT JSON payload
    "current": {
        "source": "current_ma",
        "transformer": "scale_and_format_mqtt",
    },
    # Frequency mapping: Modbus holding register → MQTT JSON payload
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: Modbus holding register (kW) → MQTT JSON payload
    "power": {
        "source": "power_kw",
        "transformer": "scale_and_format_mqtt",
    },
    # Status mapping: Modbus coil → MQTT JSON payload
    "status": {
        "source": "status_coil",
        "transformer": "format_for_mqtt",
    },
}

MQTT_TO_MODBUS = {
    # Voltage mapping: MQTT JSON payload → Modbus holding register (mV)
    "voltage_mv": {
        "source": "voltage",
        "transformer": "parse_and_scale_mv",
    },
    # Current mapping: MQTT JSON payload → Modbus holding register (mA)
    "current_ma": {
        "source": "current",
        "transformer": "parse_and_scale_ma",
    },
    # Frequency mapping: MQTT JSON payload → Modbus holding register
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: MQTT JSON payload → Modbus holding register (kW)
    "power_kw": {
        "source": "power",
        "transformer": "parse_and_scale_kw",
    },
    # Status mapping: MQTT JSON payload → Modbus coil
    "status_coil": {
        "source": "status",
        "transformer": "parse_from_mqtt",
    },
}


# ============================================================================
# DNP3 ↔ MQTT Mappings
# ============================================================================

DNP3_TO_MQTT = {
    # Voltage mapping: DNP3 analog input (V) → MQTT JSON payload
    "voltage": {
        "source": "voltage",
        "transformer": "format_for_mqtt",
    },
    # Current mapping: DNP3 analog input (A) → MQTT JSON payload
    "current": {
        "source": "current",
        "transformer": "format_for_mqtt",
    },
    # Frequency mapping: DNP3 analog input (Hz) → MQTT JSON payload
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: DNP3 analog input (W) → MQTT JSON payload
    "power": {
        "source": "power",
        "transformer": "format_for_mqtt",
    },
    # Status mapping: DNP3 binary input → MQTT JSON payload
    "status": {
        "source": "status",
        "transformer": "format_for_mqtt",
    },
}

MQTT_TO_DNP3 = {
    # Voltage mapping: MQTT JSON payload → DNP3 analog input (V)
    "voltage": {
        "source": "voltage",
        "transformer": "parse_from_mqtt",
    },
    # Current mapping: MQTT JSON payload → DNP3 analog input (A)
    "current": {
        "source": "current",
        "transformer": "parse_from_mqtt",
    },
    # Frequency mapping: MQTT JSON payload → DNP3 analog input (Hz)
    "frequency": {
        "source": "frequency",
        "default": 50,
    },
    # Power mapping: MQTT JSON payload → DNP3 analog input (W)
    "power": {
        "source": "power",
        "transformer": "parse_from_mqtt",
    },
    # Status mapping: MQTT JSON payload → DNP3 binary input
    "status": {
        "source": "status",
        "transformer": "parse_from_mqtt",
    },
}


# ============================================================================
# Mapping Registry
# ============================================================================

PROTOCOL_MAPPINGS = {
    "iec61850->modbus": IEC61850_TO_MODBUS,
    "modbus->iec61850": MODBUS_TO_IEC61850,
    "iec61850->dnp3": IEC61850_TO_DNP3,
    "dnp3->iec61850": DNP3_TO_IEC61850,
    "iec61850->mqtt": IEC61850_TO_MQTT,
    "mqtt->iec61850": MQTT_TO_IEC61850,
    "modbus->dnp3": MODBUS_TO_DNP3,
    "dnp3->modbus": DNP3_TO_MODBUS,
    "modbus->mqtt": MODBUS_TO_MQTT,
    "mqtt->modbus": MQTT_TO_MODBUS,
    "dnp3->mqtt": DNP3_TO_MQTT,
    "mqtt->dnp3": MQTT_TO_DNP3,
}
