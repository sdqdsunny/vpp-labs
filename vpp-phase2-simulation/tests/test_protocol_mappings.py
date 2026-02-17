"""
Protocol Mappings Tests

Tests for protocol mapping rules, transformers, and validators.
"""

import pytest
from services.protocol_adapters.mapper import ProtocolMessageMapper
from services.protocol_adapters.protocol_mappings import PROTOCOL_MAPPINGS
from services.protocol_adapters.transformers import TRANSFORMERS
from services.protocol_adapters.validators import VALIDATORS


class TestProtocolMappings:
    """Test protocol mapping rules"""

    def test_all_mappings_registered(self):
        """Test all 12 protocol mappings are defined"""
        expected_mappings = [
            "iec61850->modbus",
            "modbus->iec61850",
            "iec61850->dnp3",
            "dnp3->iec61850",
            "iec61850->mqtt",
            "mqtt->iec61850",
            "modbus->dnp3",
            "dnp3->modbus",
            "modbus->mqtt",
            "mqtt->modbus",
            "dnp3->mqtt",
            "mqtt->dnp3",
        ]
        
        for mapping in expected_mappings:
            assert mapping in PROTOCOL_MAPPINGS, f"Missing mapping: {mapping}"
        
        assert len(PROTOCOL_MAPPINGS) == 12

    def test_iec61850_to_modbus_mapping(self):
        """Test IEC 61850 to Modbus mapping rules"""
        mapping = PROTOCOL_MAPPINGS["iec61850->modbus"]
        
        # Check required fields
        assert "voltage_mv" in mapping
        assert "current_ma" in mapping
        assert "frequency" in mapping
        assert "power_kw" in mapping
        assert "status_coil" in mapping
        assert "timestamp" in mapping

    def test_modbus_to_iec61850_mapping(self):
        """Test Modbus to IEC 61850 mapping rules"""
        mapping = PROTOCOL_MAPPINGS["modbus->iec61850"]
        
        # Check required fields
        assert "voltage" in mapping
        assert "current" in mapping
        assert "frequency" in mapping
        assert "power" in mapping
        assert "status" in mapping
        assert "timestamp" in mapping

    def test_iec61850_to_dnp3_mapping(self):
        """Test IEC 61850 to DNP3 mapping rules"""
        mapping = PROTOCOL_MAPPINGS["iec61850->dnp3"]
        
        # Check required fields
        assert "voltage" in mapping
        assert "current" in mapping
        assert "frequency" in mapping
        assert "power" in mapping
        assert "status" in mapping
        assert "quality" in mapping

    def test_dnp3_to_iec61850_mapping(self):
        """Test DNP3 to IEC 61850 mapping rules"""
        mapping = PROTOCOL_MAPPINGS["dnp3->iec61850"]
        
        # Check required fields
        assert "voltage" in mapping
        assert "current" in mapping
        assert "frequency" in mapping
        assert "power" in mapping
        assert "status" in mapping
        assert "quality" in mapping

    def test_iec61850_to_mqtt_mapping(self):
        """Test IEC 61850 to MQTT mapping rules"""
        mapping = PROTOCOL_MAPPINGS["iec61850->mqtt"]
        
        # Check required fields
        assert "voltage" in mapping
        assert "current" in mapping
        assert "frequency" in mapping
        assert "power" in mapping
        assert "status" in mapping
        assert "timestamp" in mapping

    def test_mqtt_to_iec61850_mapping(self):
        """Test MQTT to IEC 61850 mapping rules"""
        mapping = PROTOCOL_MAPPINGS["mqtt->iec61850"]
        
        # Check required fields
        assert "voltage" in mapping
        assert "current" in mapping
        assert "frequency" in mapping
        assert "power" in mapping
        assert "status" in mapping
        assert "timestamp" in mapping

    def test_modbus_to_dnp3_mapping(self):
        """Test Modbus to DNP3 mapping rules"""
        mapping = PROTOCOL_MAPPINGS["modbus->dnp3"]
        
        # Check required fields
        assert "voltage" in mapping
        assert "current" in mapping
        assert "frequency" in mapping
        assert "power" in mapping
        assert "status" in mapping

    def test_dnp3_to_modbus_mapping(self):
        """Test DNP3 to Modbus mapping rules"""
        mapping = PROTOCOL_MAPPINGS["dnp3->modbus"]
        
        # Check required fields
        assert "voltage_mv" in mapping
        assert "current_ma" in mapping
        assert "frequency" in mapping
        assert "power_kw" in mapping
        assert "status_coil" in mapping

    def test_modbus_to_mqtt_mapping(self):
        """Test Modbus to MQTT mapping rules"""
        mapping = PROTOCOL_MAPPINGS["modbus->mqtt"]
        
        # Check required fields
        assert "voltage" in mapping
        assert "current" in mapping
        assert "frequency" in mapping
        assert "power" in mapping
        assert "status" in mapping

    def test_mqtt_to_modbus_mapping(self):
        """Test MQTT to Modbus mapping rules"""
        mapping = PROTOCOL_MAPPINGS["mqtt->modbus"]
        
        # Check required fields
        assert "voltage_mv" in mapping
        assert "current_ma" in mapping
        assert "frequency" in mapping
        assert "power_kw" in mapping
        assert "status_coil" in mapping

    def test_dnp3_to_mqtt_mapping(self):
        """Test DNP3 to MQTT mapping rules"""
        mapping = PROTOCOL_MAPPINGS["dnp3->mqtt"]
        
        # Check required fields
        assert "voltage" in mapping
        assert "current" in mapping
        assert "frequency" in mapping
        assert "power" in mapping
        assert "status" in mapping

    def test_mqtt_to_dnp3_mapping(self):
        """Test MQTT to DNP3 mapping rules"""
        mapping = PROTOCOL_MAPPINGS["mqtt->dnp3"]
        
        # Check required fields
        assert "voltage" in mapping
        assert "current" in mapping
        assert "frequency" in mapping
        assert "power" in mapping
        assert "status" in mapping


class TestTransformers:
    """Test data transformers"""

    def test_all_transformers_registered(self):
        """Test all transformers are registered"""
        expected_transformers = [
            "scale_voltage_to_mv",
            "scale_mv_to_voltage",
            "validate_voltage_range",
            "scale_current_to_ma",
            "scale_ma_to_current",
            "validate_current_range",
            "scale_power_to_kw",
            "scale_kw_to_power",
            "validate_power_range",
            "status_to_coil",
            "coil_to_status",
            "status_to_binary",
            "binary_to_status",
            "coil_to_binary",
            "binary_to_coil",
            "timestamp_to_modbus",
            "timestamp_from_modbus",
            "format_for_mqtt",
            "parse_from_mqtt",
            "scale_and_format_mqtt",
            "parse_and_scale_mv",
            "parse_and_scale_ma",
            "parse_and_scale_kw",
        ]
        
        for transformer in expected_transformers:
            assert transformer in TRANSFORMERS, f"Missing transformer: {transformer}"

    def test_voltage_scaling(self):
        """Test voltage scaling transformers"""
        # V to mV
        result = TRANSFORMERS["scale_voltage_to_mv"]({"voltage": 230})
        assert result == 230000
        
        # mV to V
        result = TRANSFORMERS["scale_mv_to_voltage"]({"voltage_mv": 230000})
        assert result == 230

    def test_current_scaling(self):
        """Test current scaling transformers"""
        # A to mA
        result = TRANSFORMERS["scale_current_to_ma"]({"current": 10})
        assert result == 10000
        
        # mA to A
        result = TRANSFORMERS["scale_ma_to_current"]({"current_ma": 10000})
        assert result == 10

    def test_power_scaling(self):
        """Test power scaling transformers"""
        # W to kW
        result = TRANSFORMERS["scale_power_to_kw"]({"power": 50000})
        assert result == 50
        
        # kW to W
        result = TRANSFORMERS["scale_kw_to_power"]({"power_kw": 50})
        assert result == 50000

    def test_status_transformers(self):
        """Test status transformers"""
        # Status to coil
        result = TRANSFORMERS["status_to_coil"]({"status": "on"})
        assert result is True
        
        result = TRANSFORMERS["status_to_coil"]({"status": "off"})
        assert result is False
        
        # Coil to status
        result = TRANSFORMERS["coil_to_status"]({"status_coil": True})
        assert result == "on"
        
        result = TRANSFORMERS["coil_to_status"]({"status_coil": False})
        assert result == "off"

    def test_status_to_binary(self):
        """Test status to binary transformers"""
        result = TRANSFORMERS["status_to_binary"]({"status": "on"})
        assert result == 1
        
        result = TRANSFORMERS["status_to_binary"]({"status": "off"})
        assert result == 0

    def test_binary_to_status(self):
        """Test binary to status transformers"""
        result = TRANSFORMERS["binary_to_status"]({"status": 1})
        assert result == "on"
        
        result = TRANSFORMERS["binary_to_status"]({"status": 0})
        assert result == "off"

    def test_timestamp_transformers(self):
        """Test timestamp transformers"""
        # Float to int
        result = TRANSFORMERS["timestamp_to_modbus"]({"timestamp": 1645000000.5})
        assert result == 1645000000
        
        # Int to float
        result = TRANSFORMERS["timestamp_from_modbus"]({"timestamp": 1645000000})
        assert result == 1645000000.0


class TestValidators:
    """Test message validators"""

    def test_all_validators_registered(self):
        """Test all validators are registered"""
        expected_validators = [
            "validate_voltage_range",
            "validate_current_range",
            "validate_power_range",
            "validate_frequency_range",
            "validate_status_format",
            "validate_timestamp_format",
            "validate_quality_format",
            "validate_iec61850_message",
            "validate_modbus_message",
            "validate_dnp3_message",
            "validate_mqtt_message",
            "validate_iec61850_to_modbus",
            "validate_modbus_to_iec61850",
            "validate_iec61850_to_dnp3",
            "validate_dnp3_to_iec61850",
            "validate_iec61850_to_mqtt",
            "validate_mqtt_to_iec61850",
            "validate_modbus_to_dnp3",
            "validate_dnp3_to_modbus",
            "validate_modbus_to_mqtt",
            "validate_mqtt_to_modbus",
            "validate_dnp3_to_mqtt",
            "validate_mqtt_to_dnp3",
        ]
        
        for validator in expected_validators:
            assert validator in VALIDATORS, f"Missing validator: {validator}"

    def test_voltage_range_validation(self):
        """Test voltage range validation"""
        # Valid voltage
        assert VALIDATORS["validate_voltage_range"]({"voltage": 230}) is True
        
        # Out of range
        assert VALIDATORS["validate_voltage_range"]({"voltage": 600}) is False
        
        # Negative voltage
        assert VALIDATORS["validate_voltage_range"]({"voltage": -10}) is False
        
        # Missing field
        assert VALIDATORS["validate_voltage_range"]({}) is False

    def test_current_range_validation(self):
        """Test current range validation"""
        # Valid current
        assert VALIDATORS["validate_current_range"]({"current": 100}) is True
        
        # Out of range
        assert VALIDATORS["validate_current_range"]({"current": 2000}) is False
        
        # Negative current
        assert VALIDATORS["validate_current_range"]({"current": -5}) is False

    def test_power_range_validation(self):
        """Test power range validation"""
        # Valid power
        assert VALIDATORS["validate_power_range"]({"power": 500000}) is True
        
        # Out of range
        assert VALIDATORS["validate_power_range"]({"power": 2000000}) is False
        
        # Negative power
        assert VALIDATORS["validate_power_range"]({"power": -1000}) is False

    def test_frequency_range_validation(self):
        """Test frequency range validation"""
        # Valid frequency
        assert VALIDATORS["validate_frequency_range"]({"frequency": 50}) is True
        
        # Out of range
        assert VALIDATORS["validate_frequency_range"]({"frequency": 70}) is False
        
        # Default frequency
        assert VALIDATORS["validate_frequency_range"]({}) is True

    def test_status_format_validation(self):
        """Test status format validation"""
        # Valid statuses
        assert VALIDATORS["validate_status_format"]({"status": "on"}) is True
        assert VALIDATORS["validate_status_format"]({"status": "off"}) is True
        assert VALIDATORS["validate_status_format"]({"status": "active"}) is True
        
        # Invalid status
        assert VALIDATORS["validate_status_format"]({"status": "invalid"}) is False

    def test_timestamp_format_validation(self):
        """Test timestamp format validation"""
        # Valid timestamp (after 2000-01-01)
        assert VALIDATORS["validate_timestamp_format"]({"timestamp": 1645000000}) is True
        
        # Invalid timestamp (before 2000-01-01)
        assert VALIDATORS["validate_timestamp_format"]({"timestamp": 100000}) is False
        
        # Missing field
        assert VALIDATORS["validate_timestamp_format"]({}) is False

    def test_quality_format_validation(self):
        """Test quality format validation"""
        # Valid qualities
        assert VALIDATORS["validate_quality_format"]({"quality": "good"}) is True
        assert VALIDATORS["validate_quality_format"]({"quality": "bad"}) is True
        
        # Invalid quality
        assert VALIDATORS["validate_quality_format"]({"quality": "invalid"}) is False
        
        # Default quality
        assert VALIDATORS["validate_quality_format"]({}) is True

    def test_iec61850_message_validation(self):
        """Test IEC 61850 message validation"""
        valid_message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "status": "on",
            "timestamp": 1645000000,
        }
        assert VALIDATORS["validate_iec61850_message"](valid_message) is True
        
        # Missing field
        incomplete_message = {
            "voltage": 230,
            "current": 10,
        }
        assert VALIDATORS["validate_iec61850_message"](incomplete_message) is False

    def test_modbus_message_validation(self):
        """Test Modbus message validation"""
        valid_message = {
            "voltage_mv": 230000,
            "current_ma": 10000,
        }
        assert VALIDATORS["validate_modbus_message"](valid_message) is True
        
        # Empty message
        assert VALIDATORS["validate_modbus_message"]({}) is False

    def test_dnp3_message_validation(self):
        """Test DNP3 message validation"""
        valid_message = {
            "voltage": 230,
            "quality": "good",
        }
        assert VALIDATORS["validate_dnp3_message"](valid_message) is True
        
        # Empty message
        assert VALIDATORS["validate_dnp3_message"]({}) is False

    def test_mqtt_message_validation(self):
        """Test MQTT message validation"""
        valid_message = {
            "voltage": 230,
            "current": 10,
        }
        assert VALIDATORS["validate_mqtt_message"](valid_message) is True
        
        # Empty message
        assert VALIDATORS["validate_mqtt_message"]({}) is False


class TestMapperIntegration:
    """Test mapper integration with mappings, transformers, and validators"""

    def test_mapper_with_all_transformers(self):
        """Test mapper can use all transformers"""
        mapper = ProtocolMessageMapper()
        
        # Register all transformers
        for name, transformer in TRANSFORMERS.items():
            mapper.register_transformer(name, transformer)
        
        # Register all validators
        for name, validator in VALIDATORS.items():
            mapper.register_validator(name, validator)
        
        # Register all mappings
        for mapping_key, rules in PROTOCOL_MAPPINGS.items():
            source, target = mapping_key.split("->")
            mapper.register_mapping(source, target, rules)
        
        # Verify all registered
        info = mapper.get_mapping_info()
        assert len(info["mappings"]) == 12
        assert len(info["transformers"]) == 23
        assert len(info["validators"]) == 23

    def test_iec61850_to_modbus_conversion(self):
        """Test IEC 61850 to Modbus message conversion"""
        mapper = ProtocolMessageMapper()
        
        # Register transformers and mappings
        for name, transformer in TRANSFORMERS.items():
            mapper.register_transformer(name, transformer)
        
        mapper.register_mapping(
            "iec61850",
            "modbus",
            PROTOCOL_MAPPINGS["iec61850->modbus"]
        )
        
        # Convert message
        iec_message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
            "timestamp": 1645000000,
        }
        
        modbus_message = mapper.map_message("iec61850", "modbus", iec_message)
        
        # Verify conversion
        assert modbus_message["voltage_mv"] == 230000
        assert modbus_message["current_ma"] == 10000
        assert modbus_message["frequency"] == 50
        assert modbus_message["power_kw"] == 2.3
        assert modbus_message["status_coil"] is True
        assert modbus_message["timestamp"] == 1645000000

    def test_modbus_to_iec61850_conversion(self):
        """Test Modbus to IEC 61850 message conversion"""
        mapper = ProtocolMessageMapper()
        
        # Register transformers and mappings
        for name, transformer in TRANSFORMERS.items():
            mapper.register_transformer(name, transformer)
        
        mapper.register_mapping(
            "modbus",
            "iec61850",
            PROTOCOL_MAPPINGS["modbus->iec61850"]
        )
        
        # Convert message
        modbus_message = {
            "voltage_mv": 230000,
            "current_ma": 10000,
            "frequency": 50,
            "power_kw": 2.3,
            "status_coil": True,
            "timestamp": 1645000000,
        }
        
        iec_message = mapper.map_message("modbus", "iec61850", modbus_message)
        
        # Verify conversion
        assert iec_message["voltage"] == 230
        assert iec_message["current"] == 10
        assert iec_message["frequency"] == 50
        assert iec_message["power"] == 2300
        assert iec_message["status"] == "on"
        assert iec_message["timestamp"] == 1645000000.0

    def test_bidirectional_conversion(self):
        """Test bidirectional conversion preserves data"""
        mapper = ProtocolMessageMapper()
        
        # Register transformers and mappings
        for name, transformer in TRANSFORMERS.items():
            mapper.register_transformer(name, transformer)
        
        mapper.register_mapping(
            "iec61850",
            "modbus",
            PROTOCOL_MAPPINGS["iec61850->modbus"]
        )
        mapper.register_mapping(
            "modbus",
            "iec61850",
            PROTOCOL_MAPPINGS["modbus->iec61850"]
        )
        
        # Original message
        original = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
            "timestamp": 1645000000,
        }
        
        # Convert to Modbus and back
        modbus_msg = mapper.map_message("iec61850", "modbus", original)
        recovered = mapper.map_message("modbus", "iec61850", modbus_msg)
        
        # Verify data integrity
        assert recovered["voltage"] == original["voltage"]
        assert recovered["current"] == original["current"]
        assert recovered["frequency"] == original["frequency"]
        assert recovered["power"] == original["power"]
        assert recovered["status"] == original["status"]
