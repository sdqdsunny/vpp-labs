"""
Protocol Message Mapper Tests
"""

import pytest
from services.protocol_adapters.mapper import ProtocolMessageMapper
from services.protocol_adapters.base import MessageException


@pytest.fixture
def mapper():
    """Create mapper instance"""
    return ProtocolMessageMapper()


class TestProtocolMessageMapper:
    """Test protocol message mapper"""

    def test_register_mapping(self, mapper):
        """Test registering mapping"""
        rules = {"voltage": "holding_register_0"}
        mapper.register_mapping("iec61850", "modbus", rules)
        assert "iec61850->modbus" in mapper.mappings

    def test_register_transformer(self, mapper):
        """Test registering transformer"""
        def scale_current(data):
            return data.get("current", 0) * 1000

        mapper.register_transformer("scale_current", scale_current)
        assert "scale_current" in mapper.transformers

    def test_register_validator(self, mapper):
        """Test registering validator"""
        def validate_voltage(message):
            return 0 <= message.get("voltage", 0) <= 400

        mapper.register_validator("validate_voltage", validate_voltage)
        assert "validate_voltage" in mapper.validators

    def test_direct_field_mapping(self, mapper):
        """Test direct field mapping"""
        rules = {
            "voltage": "source_voltage",
            "current": "source_current",
        }
        mapper.register_mapping("iec61850", "modbus", rules)

        message = {
            "source_voltage": 230,
            "source_current": 10,
        }

        result = mapper.map_message("iec61850", "modbus", message)
        assert result["voltage"] == 230
        assert result["current"] == 10

    def test_transformer_mapping(self, mapper):
        """Test transformer mapping"""
        def scale_current(data):
            return data.get("current", 0) * 1000

        mapper.register_transformer("scale_current", scale_current)
        rules = {
            "voltage": "voltage",
            "current_ma": {"transformer": "scale_current"},
        }
        mapper.register_mapping("iec61850", "modbus", rules)

        message = {"voltage": 230, "current": 0.01}
        result = mapper.map_message("iec61850", "modbus", message)
        assert result["voltage"] == 230
        assert result["current_ma"] == 10

    def test_conditional_mapping(self, mapper):
        """Test conditional mapping"""
        rules = {
            "status": {
                "condition": {
                    "field": "voltage",
                    "operator": "gt",
                    "value": 200,
                },
                "value": "normal",
            }
        }
        mapper.register_mapping("iec61850", "modbus", rules)

        message = {"voltage": 230}
        result = mapper.map_message("iec61850", "modbus", message)
        assert result["status"] == "normal"

    def test_default_value_mapping(self, mapper):
        """Test default value mapping"""
        rules = {
            "status": {"default": "unknown"},
        }
        mapper.register_mapping("iec61850", "modbus", rules)

        message = {}
        result = mapper.map_message("iec61850", "modbus", message)
        assert result["status"] == "unknown"

    def test_mapping_not_found(self, mapper):
        """Test mapping not found"""
        message = {"voltage": 230}
        with pytest.raises(MessageException):
            mapper.map_message("iec61850", "modbus", message)

    def test_transform_data(self, mapper):
        """Test transforming data"""
        def scale_current(data):
            return data.get("current", 0) * 1000

        mapper.register_transformer("scale_current", scale_current)
        result = mapper.transform_data("scale_current", {"current": 0.01})
        assert result == 10

    def test_transform_data_not_found(self, mapper):
        """Test transforming with non-existent transformer"""
        with pytest.raises(MessageException):
            mapper.transform_data("nonexistent", {})

    def test_validate_message(self, mapper):
        """Test validating message"""
        def validate_voltage(message):
            return 0 <= message.get("voltage", 0) <= 400

        mapper.register_validator("validate_voltage", validate_voltage)
        assert mapper.validate_message("validate_voltage", {"voltage": 230})
        assert not mapper.validate_message("validate_voltage", {"voltage": 500})

    def test_validate_message_not_found(self, mapper):
        """Test validating with non-existent validator"""
        result = mapper.validate_message("nonexistent", {})
        assert result is True  # Returns True by default

    def test_condition_operators(self, mapper):
        """Test various condition operators"""
        test_cases = [
            ({"field": "value", "operator": "eq", "value": 10}, {"value": 10}, True),
            ({"field": "value", "operator": "ne", "value": 10}, {"value": 20}, True),
            ({"field": "value", "operator": "gt", "value": 10}, {"value": 20}, True),
            ({"field": "value", "operator": "lt", "value": 10}, {"value": 5}, True),
            ({"field": "value", "operator": "gte", "value": 10}, {"value": 10}, True),
            ({"field": "value", "operator": "lte", "value": 10}, {"value": 10}, True),
            ({"field": "value", "operator": "in", "value": [1, 2, 3]}, {"value": 2}, True),
            ({"field": "value", "operator": "not_in", "value": [1, 2, 3]}, {"value": 4}, True),
        ]

        for condition, message, expected in test_cases:
            result = mapper._evaluate_condition(message, condition)
            assert result == expected

    def test_get_mapping_info(self, mapper):
        """Test getting mapper info"""
        mapper.register_mapping("iec61850", "modbus", {})
        mapper.register_transformer("scale", lambda x: x)
        mapper.register_validator("validate", lambda x: True)

        info = mapper.get_mapping_info()
        assert "mappings" in info
        assert "transformers" in info
        assert "validators" in info
        assert info["total_mappings"] == 1
        assert info["total_transformers"] == 1
        assert info["total_validators"] == 1

    def test_complex_mapping(self, mapper):
        """Test complex mapping with multiple rules"""
        def scale_current(data):
            return data.get("current", 0) * 1000

        mapper.register_transformer("scale_current", scale_current)
        rules = {
            "voltage": "source_voltage",
            "current_ma": {"transformer": "scale_current"},
            "frequency": {"default": 50},
            "status": {
                "condition": {
                    "field": "source_voltage",
                    "operator": "gt",
                    "value": 200,
                },
                "value": "normal",
            },
        }
        mapper.register_mapping("iec61850", "modbus", rules)

        message = {
            "source_voltage": 230,
            "current": 0.01,
        }
        result = mapper.map_message("iec61850", "modbus", message)
        assert result["voltage"] == 230
        assert result["current_ma"] == 10
        assert result["frequency"] == 50
        assert result["status"] == "normal"
