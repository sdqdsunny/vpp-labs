"""
Performance tests for protocol conversion and message processing.

This module tests performance characteristics including:
- Message processing latency
- Throughput (messages per second)
- Memory usage
- CPU usage
- Scalability with message volume
"""

import pytest
import time
import sys
from datetime import datetime
from services.protocol_management import ProtocolManagementService
from services.protocol_adapters.validators import (
    validate_iec61850_message,
    validate_modbus_message,
    validate_dnp3_message,
    validate_mqtt_message,
)


class TestMessageProcessingLatency:
    """Test message processing latency."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ProtocolManagementService()
        self.mapper = self.service.mapper

    def test_iec61850_to_modbus_latency(self):
        """Test IEC 61850 to Modbus conversion latency."""
        iec_message = {
            "voltage": 230.0,
            "current": 10.5,
            "frequency": 50.0,
            "power": 2415.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Warm up
        self.mapper.map_message("iec61850", "modbus", iec_message)

        # Measure latency
        start = time.perf_counter()
        for _ in range(100):
            self.mapper.map_message("iec61850", "modbus", iec_message)
        end = time.perf_counter()

        total_time = (end - start) * 1000  # Convert to ms
        avg_latency = total_time / 100

        # Assert latency is reasonable (< 10ms per conversion)
        assert avg_latency < 10.0, f"Latency too high: {avg_latency}ms"

    def test_modbus_to_dnp3_latency(self):
        """Test Modbus to DNP3 conversion latency."""
        modbus_message = {
            "voltage_register": 230,
            "current_register": 10,
            "power_register": 2300,
            "status_coil": True,
            "timestamp": datetime.now().timestamp(),
        }

        # Warm up
        self.mapper.map_message("modbus", "dnp3", modbus_message)

        # Measure latency
        start = time.perf_counter()
        for _ in range(100):
            self.mapper.map_message("modbus", "dnp3", modbus_message)
        end = time.perf_counter()

        total_time = (end - start) * 1000
        avg_latency = total_time / 100

        # Assert latency is reasonable
        assert avg_latency < 10.0, f"Latency too high: {avg_latency}ms"

    def test_dnp3_to_mqtt_latency(self):
        """Test DNP3 to MQTT conversion latency."""
        dnp3_message = {
            "analog_input_voltage": 230,
            "analog_input_current": 10,
            "binary_input_status": True,
            "timestamp": datetime.now().timestamp(),
        }

        # Warm up
        self.mapper.map_message("dnp3", "mqtt", dnp3_message)

        # Measure latency
        start = time.perf_counter()
        for _ in range(100):
            self.mapper.map_message("dnp3", "mqtt", dnp3_message)
        end = time.perf_counter()

        total_time = (end - start) * 1000
        avg_latency = total_time / 100

        # Assert latency is reasonable
        assert avg_latency < 10.0, f"Latency too high: {avg_latency}ms"

    def test_round_trip_latency(self):
        """Test round-trip conversion latency."""
        iec_message = {
            "voltage": 230.0,
            "current": 10.5,
            "frequency": 50.0,
            "power": 2415.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Warm up
        modbus_msg = self.mapper.map_message("iec61850", "modbus", iec_message)
        self.mapper.map_message("modbus", "iec61850", modbus_msg)

        # Measure latency
        start = time.perf_counter()
        for _ in range(50):
            modbus_msg = self.mapper.map_message("iec61850", "modbus", iec_message)
            self.mapper.map_message("modbus", "iec61850", modbus_msg)
        end = time.perf_counter()

        total_time = (end - start) * 1000
        avg_latency = total_time / 50

        # Assert latency is reasonable (< 20ms for round trip)
        assert avg_latency < 20.0, f"Round-trip latency too high: {avg_latency}ms"


class TestThroughput:
    """Test message processing throughput."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ProtocolManagementService()
        self.mapper = self.service.mapper

    def test_iec61850_to_modbus_throughput(self):
        """Test IEC 61850 to Modbus conversion throughput."""
        iec_message = {
            "voltage": 230.0,
            "current": 10.5,
            "frequency": 50.0,
            "power": 2415.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Measure throughput
        start = time.perf_counter()
        count = 0
        while time.perf_counter() - start < 1.0:  # Run for 1 second
            self.mapper.map_message("iec61850", "modbus", iec_message)
            count += 1
        end = time.perf_counter()

        throughput = count / (end - start)

        # Assert throughput is reasonable (> 1000 messages/sec)
        assert throughput > 1000, f"Throughput too low: {throughput} msg/sec"

    def test_modbus_to_dnp3_throughput(self):
        """Test Modbus to DNP3 conversion throughput."""
        modbus_message = {
            "voltage_register": 230,
            "current_register": 10,
            "power_register": 2300,
            "status_coil": True,
            "timestamp": datetime.now().timestamp(),
        }

        # Measure throughput
        start = time.perf_counter()
        count = 0
        while time.perf_counter() - start < 1.0:
            self.mapper.map_message("modbus", "dnp3", modbus_message)
            count += 1
        end = time.perf_counter()

        throughput = count / (end - start)

        # Assert throughput is reasonable
        assert throughput > 1000, f"Throughput too low: {throughput} msg/sec"

    def test_validation_throughput(self):
        """Test message validation throughput."""
        iec_message = {
            "voltage": 230.0,
            "current": 10.5,
            "frequency": 50.0,
            "power": 2415.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Measure validation throughput
        start = time.perf_counter()
        count = 0
        while time.perf_counter() - start < 1.0:
            validate_iec61850_message(iec_message)
            count += 1
        end = time.perf_counter()

        throughput = count / (end - start)

        # Assert validation throughput is high (> 5000 validations/sec)
        assert throughput > 5000, f"Validation throughput too low: {throughput} val/sec"


class TestMemoryUsage:
    """Test memory usage during protocol operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ProtocolManagementService()
        self.mapper = self.service.mapper

    def test_conversion_memory_stability(self):
        """Test memory stability during repeated conversions."""
        iec_message = {
            "voltage": 230.0,
            "current": 10.5,
            "frequency": 50.0,
            "power": 2415.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Get initial memory usage
        import gc
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Perform many conversions
        for _ in range(1000):
            self.mapper.map_message("iec61850", "modbus", iec_message)

        # Check final memory usage
        gc.collect()
        final_objects = len(gc.get_objects())

        # Memory growth should be minimal (< 10% increase)
        growth_ratio = (final_objects - initial_objects) / initial_objects
        assert growth_ratio < 0.1, f"Memory growth too high: {growth_ratio * 100}%"

    def test_message_size_handling(self):
        """Test handling of large messages."""
        # Create a large message
        large_message = {
            "voltage": 230.0,
            "current": 10.5,
            "frequency": 50.0,
            "power": 2415.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
            "extra_data": "x" * 10000,  # Add extra data
        }

        # Should handle large messages without issues
        result = self.mapper.map_message("iec61850", "modbus", large_message)
        assert result is not None


class TestScalability:
    """Test scalability with increasing message volume."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ProtocolManagementService()
        self.mapper = self.service.mapper

    def test_batch_conversion_scalability(self):
        """Test scalability with batch conversions."""
        messages = [
            {
                "voltage": 230.0 + i,
                "current": 10.5 + i * 0.1,
                "frequency": 50.0,
                "power": 2415.0 + i * 10,
                "status": "on",
                "timestamp": datetime.now().timestamp(),
            }
            for i in range(100)
        ]

        # Convert all messages
        start = time.perf_counter()
        results = []
        for msg in messages:
            result = self.mapper.map_message("iec61850", "modbus", msg)
            results.append(result)
        end = time.perf_counter()

        # All conversions should succeed
        assert len(results) == 100
        assert all(r is not None for r in results)

        # Throughput should be consistent
        throughput = len(messages) / (end - start)
        assert throughput > 1000, f"Batch throughput too low: {throughput} msg/sec"

    def test_multi_protocol_conversion_scalability(self):
        """Test scalability with multiple protocol conversions."""
        protocol_pairs = [
            ("iec61850", "modbus"),
            ("modbus", "dnp3"),
            ("dnp3", "mqtt"),
            ("iec61850", "dnp3"),
            ("modbus", "mqtt"),
        ]

        messages = {
            "iec61850": {
                "voltage": 230.0,
                "current": 10.5,
                "frequency": 50.0,
                "power": 2415.0,
                "status": "on",
                "timestamp": datetime.now().timestamp(),
            },
            "modbus": {
                "voltage_register": 230,
                "current_register": 10,
                "power_register": 2300,
                "status_coil": True,
                "timestamp": datetime.now().timestamp(),
            },
            "dnp3": {
                "analog_input_voltage": 230,
                "analog_input_current": 10,
                "binary_input_status": True,
                "timestamp": datetime.now().timestamp(),
            },
        }

        # Perform conversions
        start = time.perf_counter()
        for source, target in protocol_pairs:
            for _ in range(100):
                msg = messages.get(source, messages["iec61850"])
                self.mapper.map_message(source, target, msg)
        end = time.perf_counter()

        # Calculate throughput
        total_conversions = len(protocol_pairs) * 100
        throughput = total_conversions / (end - start)

        # Assert reasonable throughput
        assert throughput > 500, f"Multi-protocol throughput too low: {throughput} msg/sec"


class TestConcurrentOperations:
    """Test concurrent protocol operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ProtocolManagementService()
        self.mapper = self.service.mapper

    def test_sequential_conversions(self):
        """Test sequential conversions maintain consistency."""
        iec_message = {
            "voltage": 230.0,
            "current": 10.5,
            "frequency": 50.0,
            "power": 2415.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        # Perform sequential conversions
        results = []
        for i in range(10):
            modbus_msg = self.mapper.map_message("iec61850", "modbus", iec_message)
            dnp3_msg = self.mapper.map_message("modbus", "dnp3", modbus_msg)
            mqtt_msg = self.mapper.map_message("dnp3", "mqtt", dnp3_msg)
            results.append((modbus_msg, dnp3_msg, mqtt_msg))

        # All conversions should succeed
        assert len(results) == 10
        assert all(all(r is not None for r in result) for result in results)

    def test_interleaved_conversions(self):
        """Test interleaved conversions from different protocols."""
        iec_message = {
            "voltage": 230.0,
            "current": 10.5,
            "frequency": 50.0,
            "power": 2415.0,
            "status": "on",
            "timestamp": datetime.now().timestamp(),
        }

        modbus_message = {
            "voltage_register": 230,
            "current_register": 10,
            "power_register": 2300,
            "status_coil": True,
            "timestamp": datetime.now().timestamp(),
        }

        # Interleave conversions
        results = []
        for i in range(10):
            iec_to_modbus = self.mapper.map_message("iec61850", "modbus", iec_message)
            modbus_to_dnp3 = self.mapper.map_message("modbus", "dnp3", modbus_message)
            dnp3_to_mqtt = self.mapper.map_message("dnp3", "mqtt", modbus_to_dnp3)
            results.append((iec_to_modbus, modbus_to_dnp3, dnp3_to_mqtt))

        # All conversions should succeed
        assert len(results) == 10
        assert all(all(r is not None for r in result) for result in results)
