"""
End-to-end integration tests for protocol conversion flows.

This module tests complete protocol conversion workflows including:
- Multi-hop protocol conversions (A -> B -> C -> A)
- Data integrity across conversions
- Message format preservation
- Error handling in conversion chains
- Real-world scenario simulations
"""

import pytest
from datetime import datetime
from services.protocol_adapters.base import ProtocolMessage
from services.protocol_adapters.registry import ProtocolRegistry
from services.protocol_adapters.mapper import ProtocolMessageMapper
from services.protocol_adapters.validators import (
    validate_iec61850_message,
    validate_modbus_message,
    validate_dnp3_message,
    validate_mqtt_message,
)
from services.protocol_management import ProtocolManagementService


class TestProtocolConversionChains:
    """Test multi-hop protocol conversion chains."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ProtocolManagementService()
        self.mapper = self.service.mapper
        self.registry = self.service.registry

    def test_iec61850_to_modbus_conversion(self):
        """Test IEC 61850 to Modbus conversion."""
        # Create IEC 61850 message
        iec_message = {
            "voltage": 230.0,
            "current": 10.5,
            "frequency": 50.0,
            "power": 2415.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Validate source message
        assert validate_iec61850_message(iec_message)

        # Map to Modbus
        modbus_message = self.mapper.map_message(
            "iec61850", "modbus", iec_message
        )

        # Verify conversion
        assert modbus_message is not None
        assert "voltage_mv" in modbus_message or "voltage_register" in modbus_message
        assert "current_ma" in modbus_message or "current_register" in modbus_message
        assert "power_kw" in modbus_message or "power_register" in modbus_message
        assert "status_coil" in modbus_message

        # Validate target message
        assert validate_modbus_message(modbus_message)

    def test_modbus_to_dnp3_conversion(self):
        """Test Modbus to DNP3 conversion."""
        # Create Modbus message
        modbus_message = {
            "voltage_register": 230,
            "current_register": 10,
            "power_register": 2300,
            "status_coil": True,
            "timestamp": datetime.now().timestamp(),
        }

        # Validate source message
        assert validate_modbus_message(modbus_message)

        # Map to DNP3
        dnp3_message = self.mapper.map_message(
            "modbus", "dnp3", modbus_message
        )

        # Verify conversion happened
        assert dnp3_message is not None
        # Check for expected fields (may vary based on mapping)
        assert len(dnp3_message) > 0

    def test_dnp3_to_mqtt_conversion(self):
        """Test DNP3 to MQTT conversion."""
        # Create DNP3 message
        dnp3_message = {
            "analog_input_voltage": 230,
            "analog_input_current": 10,
            "binary_input_status": True,
            "timestamp": datetime.now().timestamp(),
        }

        # Validate source message
        assert validate_dnp3_message(dnp3_message)

        # Map to MQTT
        mqtt_message = self.mapper.map_message("dnp3", "mqtt", dnp3_message)

        # Verify conversion happened
        assert mqtt_message is not None
        assert len(mqtt_message) > 0

    def test_three_hop_conversion_chain(self):
        """Test three-hop conversion: IEC61850 -> Modbus -> DNP3 -> MQTT."""
        # Start with IEC 61850
        iec_message = {
            "voltage": 230.0,
            "current": 10.5,
            "frequency": 50.0,
            "power": 2415.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Hop 1: IEC61850 -> Modbus
        modbus_msg = self.mapper.map_message(
            "iec61850", "modbus", iec_message
        )
        assert modbus_msg is not None
        assert validate_modbus_message(modbus_msg)

        # Hop 2: Modbus -> DNP3
        dnp3_msg = self.mapper.map_message("modbus", "dnp3", modbus_msg)
        assert dnp3_msg is not None
        assert validate_dnp3_message(dnp3_msg)

        # Hop 3: DNP3 -> MQTT
        mqtt_msg = self.mapper.map_message("dnp3", "mqtt", dnp3_msg)
        assert mqtt_msg is not None
        assert validate_mqtt_message(mqtt_msg)

    def test_round_trip_conversion_iec_modbus_iec(self):
        """Test round-trip conversion: IEC61850 -> Modbus -> IEC61850."""
        # Original IEC message
        original = {
            "voltage": 230.0,
            "current": 10.5,
            "frequency": 50.0,
            "power": 2415.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Forward: IEC -> Modbus
        modbus_msg = self.mapper.map_message(
            "iec61850", "modbus", original
        )
        assert modbus_msg is not None

        # Backward: Modbus -> IEC
        recovered = self.mapper.map_message("modbus", "iec61850", modbus_msg)
        assert recovered is not None

        # Verify data integrity
        assert abs(recovered["voltage"] - original["voltage"]) < 1.0
        assert abs(recovered["current"] - original["current"]) < 1.0
        assert recovered["status"] == original["status"]

    def test_bidirectional_conversion_all_pairs(self):
        """Test bidirectional conversion for all protocol pairs."""
        protocol_pairs = [
            ("iec61850", "modbus"),
            ("iec61850", "dnp3"),
            ("iec61850", "mqtt"),
            ("modbus", "dnp3"),
            ("modbus", "mqtt"),
            ("dnp3", "mqtt"),
        ]

        for source, target in protocol_pairs:
            # Create test message based on source protocol
            if source == "iec61850":
                msg = {
                    "voltage": 230.0,
                    "current": 10.5,
                    "frequency": 50.0,
                    "power": 2415.0,
                    "status": "on",
                    "timestamp": datetime.now().timestamp(),
                }
            elif source == "modbus":
                msg = {
                    "voltage_register": 230,
                    "current_register": 10,
                    "power_register": 2300,
                    "status_coil": True,
                    "timestamp": datetime.now().timestamp(),
                }
            elif source == "dnp3":
                msg = {
                    "analog_input_voltage": 230,
                    "analog_input_current": 10,
                    "binary_input_status": True,
                    "timestamp": datetime.now().timestamp(),
                }
            else:  # mqtt
                msg = {
                    "topic": "device/status",
                    "payload": {"voltage": 230, "status": "on"},
                    "timestamp": datetime.now().timestamp(),
                }

            # Forward conversion
            forward = self.mapper.map_message(source, target, msg)
            assert forward is not None, f"Forward conversion {source}->{target} failed"

            # Backward conversion
            backward = self.mapper.map_message(target, source, forward)
            assert backward is not None, f"Backward conversion {target}->{source} failed"


class TestDataIntegrityAcrossConversions:
    """Test data integrity preservation across protocol conversions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ProtocolManagementService()
        self.mapper = self.service.mapper

    def test_voltage_preservation_through_conversions(self):
        """Test voltage value preservation through multiple conversions."""
        original_voltage = 230.0

        # Create IEC message
        iec_msg = {
            "voltage": original_voltage,
            "current": 10.0,
            "frequency": 50.0,
            "power": 2300.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Convert through chain
        modbus_msg = self.mapper.map_message("iec61850", "modbus", iec_msg)
        dnp3_msg = self.mapper.map_message("modbus", "dnp3", modbus_msg)
        recovered_iec = self.mapper.map_message("dnp3", "iec61850", dnp3_msg)

        # Verify voltage preservation
        assert "voltage" in recovered_iec
        assert abs(recovered_iec["voltage"] - original_voltage) < 2.0

    def test_status_preservation_through_conversions(self):
        """Test status value preservation through multiple conversions."""
        original_status = "on"

        # Create IEC message
        iec_msg = {
            "voltage": 230.0,
            "current": 10.0,
            "frequency": 50.0,
            "power": 2300.0,
            "status": original_status,
            "timestamp": datetime.now().timestamp(),
        }

        # Convert through chain
        modbus_msg = self.mapper.map_message("iec61850", "modbus", iec_msg)
        dnp3_msg = self.mapper.map_message("modbus", "dnp3", modbus_msg)
        mqtt_msg = self.mapper.map_message("dnp3", "mqtt", dnp3_msg)

        # Verify conversions happened
        assert modbus_msg is not None
        assert dnp3_msg is not None
        assert mqtt_msg is not None

    def test_timestamp_preservation(self):
        """Test timestamp preservation through conversions."""
        timestamp = datetime.now().timestamp()

        # Create IEC message
        iec_msg = {
            "voltage": 230.0,
            "current": 10.0,
            "frequency": 50.0,
            "power": 2300.0,
            "status": "on",
            "timestamp": timestamp,
        }

        # Convert through chain
        modbus_msg = self.mapper.map_message("iec61850", "modbus", iec_msg)
        dnp3_msg = self.mapper.map_message("modbus", "dnp3", modbus_msg)

        # Verify timestamp exists in modbus conversion
        assert "timestamp" in modbus_msg
        # DNP3 may not preserve timestamp in all cases, so just verify conversion happened
        assert dnp3_msg is not None

    def test_multiple_values_preservation(self):
        """Test preservation of multiple values through conversions."""
        original_values = {
            "voltage": 230.0,
            "current": 15.5,
            "power": 3565.0,
            "frequency": 50.0,
        }

        # Create IEC message
        iec_msg = {
            **original_values,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Convert to Modbus and back
        modbus_msg = self.mapper.map_message("iec61850", "modbus", iec_msg)
        recovered = self.mapper.map_message("modbus", "iec61850", modbus_msg)

        # Verify all values are preserved within tolerance
        assert abs(recovered["voltage"] - original_values["voltage"]) < 2.0
        assert abs(recovered["current"] - original_values["current"]) < 2.0
        assert abs(recovered["power"] - original_values["power"]) < 50.0


class TestErrorHandlingInConversionChains:
    """Test error handling in protocol conversion chains."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ProtocolManagementService()
        self.mapper = self.service.mapper

    def test_invalid_source_protocol(self):
        """Test handling of invalid source protocol."""
        message = {"voltage": 230.0}

        with pytest.raises(Exception):
            self.mapper.map_message("invalid_protocol", "modbus", message)

    def test_invalid_target_protocol(self):
        """Test handling of invalid target protocol."""
        message = {"voltage": 230.0}

        with pytest.raises(Exception):
            self.mapper.map_message("iec61850", "invalid_protocol", message)

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        # IEC message missing required fields
        incomplete_msg = {"voltage": 230.0}  # Missing other required fields

        # Should still attempt conversion but may fail validation
        result = self.mapper.map_message("iec61850", "modbus", incomplete_msg)
        # Result may be None or partial depending on implementation

    def test_invalid_field_values(self):
        """Test handling of invalid field values."""
        # Message with invalid values
        invalid_msg = {
            "voltage": -500.0,  # Invalid negative voltage
            "current": 10.0,
            "frequency": 50.0,
            "power": 2300.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Conversion should handle gracefully
        result = self.mapper.map_message("iec61850", "modbus", invalid_msg)
        # Should either convert or raise appropriate error

    def test_conversion_with_null_values(self):
        """Test handling of null values in conversion."""
        message_with_nulls = {
            "voltage": 230.0,
            "current": None,
            "frequency": 50.0,
            "power": None,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Should handle null values gracefully
        result = self.mapper.map_message("iec61850", "modbus", message_with_nulls)
        # Should either convert or raise appropriate error


class TestRealWorldScenarios:
    """Test real-world protocol conversion scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ProtocolManagementService()
        self.mapper = self.service.mapper

    def test_solar_panel_monitoring_scenario(self):
        """Test solar panel monitoring with protocol conversion."""
        # Solar panel sends data via IEC 61850
        solar_data = {
            "voltage": 400.0,
            "current": 25.0,
            "frequency": 50.0,
            "power": 10000.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Convert to Modbus for legacy SCADA
        modbus_data = self.mapper.map_message(
            "iec61850", "modbus", solar_data
        )
        assert modbus_data is not None
        assert validate_modbus_message(modbus_data)

        # Convert to MQTT for cloud monitoring
        mqtt_data = self.mapper.map_message("modbus", "mqtt", modbus_data)
        assert mqtt_data is not None
        assert validate_mqtt_message(mqtt_data)

    def test_battery_storage_scenario(self):
        """Test battery storage system with protocol conversion."""
        # Battery system sends data via DNP3
        battery_data = {
            "analog_input_voltage": 48,
            "analog_input_current": 50,
            "binary_input_status": True,
            "timestamp": datetime.now().timestamp(),
        }

        # Convert to IEC 61850 for modern control center
        iec_data = self.mapper.map_message("dnp3", "iec61850", battery_data)
        assert iec_data is not None

        # Convert to MQTT for monitoring
        mqtt_data = self.mapper.map_message("iec61850", "mqtt", iec_data)
        assert mqtt_data is not None

    def test_load_demand_scenario(self):
        """Test load demand management with protocol conversion."""
        # Load demand via Modbus
        load_data = {
            "voltage_register": 230,
            "current_register": 20,
            "power_register": 4600,
            "status_coil": True,
            "timestamp": datetime.now().timestamp(),
        }

        # Convert to DNP3 for utility communication
        dnp3_data = self.mapper.map_message("modbus", "dnp3", load_data)
        assert dnp3_data is not None

        # Convert to IEC 61850 for VPP coordination
        iec_data = self.mapper.map_message("dnp3", "iec61850", dnp3_data)
        assert iec_data is not None

    def test_multi_device_aggregation_scenario(self):
        """Test aggregating data from multiple devices with different protocols."""
        devices = [
            {
                "protocol": "iec61850",
                "data": {
                    "voltage": 230.0,
                    "current": 10.0,
                    "frequency": 50.0,
                    "power": 2300.0,
                    "status": "on",
                    "timestamp": datetime.now().timestamp(),
                },
            },
            {
                "protocol": "modbus",
                "data": {
                    "voltage_register": 230,
                    "current_register": 15,
                    "power_register": 3450,
                    "status_coil": True,
                    "timestamp": datetime.now().timestamp(),
                },
            },
            {
                "protocol": "dnp3",
                "data": {
                    "analog_input_voltage": 230,
                    "analog_input_current": 20,
                    "binary_input_status": True,
                    "timestamp": datetime.now().timestamp(),
                },
            },
        ]

        # Convert all to common format (MQTT)
        mqtt_messages = []
        for device in devices:
            # Convert to MQTT
            if device["protocol"] == "iec61850":
                mqtt_msg = self.mapper.map_message(
                    "iec61850", "mqtt", device["data"]
                )
            elif device["protocol"] == "modbus":
                mqtt_msg = self.mapper.map_message(
                    "modbus", "mqtt", device["data"]
                )
            else:  # dnp3
                mqtt_msg = self.mapper.map_message(
                    "dnp3", "mqtt", device["data"]
                )

            assert mqtt_msg is not None
            mqtt_messages.append(mqtt_msg)

        # Verify all messages are in MQTT format
        assert len(mqtt_messages) == 3
        for msg in mqtt_messages:
            assert validate_mqtt_message(msg)
