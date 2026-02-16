"""
Property-based tests for power generation simulators.

Uses Hypothesis to validate correctness properties across generated inputs.
Feature: vpp-phase2-simulation
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime

from services.power_gen_simulator import SolarSimulator, WindSimulator
from services.device_emulator import DeviceCommand


class TestSolarProperties:
    """Property-based tests for solar simulator."""

    @given(
        irradiance=st.floats(min_value=0, max_value=1500),
        temperature=st.floats(min_value=-20, max_value=60)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_solar_output_within_capacity(self, irradiance, temperature):
        """
        Property 1: Solar Output Calculation Accuracy

        For any solar simulator with valid parameters, the calculated power output
        should never exceed the installed capacity.

        Validates: Requirements 1.1, 1.4
        """
        solar = SolarSimulator("solar-test", {
            "capacity_kw": 10.0,
            "efficiency": 0.18,
            "temperature_coefficient": -0.004,
            "location": "test"
        })

        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": irradiance,
                "temperature": temperature
            }
        )
        result = solar.set_command(command)

        assert result.success is True
        assert 0 <= result.data["power_output_kw"] <= 10.0

    @given(
        irradiance=st.floats(min_value=0, max_value=1500),
        temperature=st.floats(min_value=-20, max_value=60)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_solar_output_monotonic_with_irradiance(self, irradiance, temperature):
        """
        Property 2: Solar Output Recalculation Speed

        For any solar simulator, when weather data is updated, the power output
        should be recalculated and available within 100ms (verified by execution time).

        Validates: Requirements 1.3
        """
        solar = SolarSimulator("solar-test", {
            "capacity_kw": 10.0,
            "efficiency": 0.18,
            "temperature_coefficient": -0.004,
            "location": "test"
        })

        import time
        start = time.time()

        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": irradiance,
                "temperature": temperature
            }
        )
        result = solar.set_command(command)

        elapsed_ms = (time.time() - start) * 1000

        assert result.success is True
        assert elapsed_ms < 100  # Should complete within 100ms

    @given(
        irradiance1=st.floats(min_value=0, max_value=1500),
        irradiance2=st.floats(min_value=0, max_value=1500),
        temperature=st.floats(min_value=-20, max_value=60)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_solar_output_monotonic_irradiance(self, irradiance1, irradiance2, temperature):
        """
        Property: Solar output increases monotonically with irradiance.

        For any solar simulator, if irradiance increases while temperature stays constant,
        power output should not decrease.

        Validates: Requirements 1.1, 1.4
        """
        solar = SolarSimulator("solar-test", {
            "capacity_kw": 10.0,
            "efficiency": 0.18,
            "temperature_coefficient": -0.004,
            "location": "test"
        })

        # First measurement
        cmd1 = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": irradiance1,
                "temperature": temperature
            }
        )
        result1 = solar.set_command(cmd1)
        power1 = result1.data["power_output_kw"]

        # Second measurement
        cmd2 = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": irradiance2,
                "temperature": temperature
            }
        )
        result2 = solar.set_command(cmd2)
        power2 = result2.data["power_output_kw"]

        # If irradiance increases, power should not decrease
        if irradiance2 > irradiance1:
            assert power2 >= power1 - 0.01  # Allow small floating point error

    @given(
        capacity=st.floats(min_value=1, max_value=100),
        efficiency=st.floats(min_value=0.1, max_value=0.25)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_solar_scalability(self, capacity, efficiency):
        """
        Property 5: Generator Scalability

        For any set of 1000+ solar generators, the simulator should calculate
        power output for all generators without performance degradation.

        Validates: Requirements 1.5
        """
        import time

        # Create 100 solar simulators (scaled down for testing)
        simulators = [
            SolarSimulator(f"solar-{i}", {
                "capacity_kw": capacity,
                "efficiency": efficiency,
                "temperature_coefficient": -0.004,
                "location": "test"
            })
            for i in range(100)
        ]

        start = time.time()

        # Update all simulators
        for sim in simulators:
            cmd = DeviceCommand(
                command_type="set_weather",
                parameters={
                    "solar_irradiance": 800.0,
                    "temperature": 25.0
                }
            )
            sim.set_command(cmd)

        elapsed_ms = (time.time() - start) * 1000

        # Should complete 100 updates in reasonable time
        assert elapsed_ms < 500  # 5ms per simulator


class TestWindProperties:
    """Property-based tests for wind simulator."""

    @given(
        wind_speed=st.floats(min_value=0, max_value=50),
        wind_direction=st.floats(min_value=0, max_value=360)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_wind_output_within_capacity(self, wind_speed, wind_direction):
        """
        Property 3: Wind Output Calculation Accuracy

        For any wind simulator with valid parameters, the calculated power output
        should never exceed the installed capacity.

        Validates: Requirements 1.1, 1.4
        """
        wind = WindSimulator("wind-test", {
            "capacity_kw": 2000.0,
            "hub_height": 80,
            "cut_in_speed": 3.0,
            "rated_speed": 12.0,
            "cut_out_speed": 25.0,
            "location": "test"
        })

        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": wind_speed,
                "wind_direction": wind_direction
            }
        )
        result = wind.set_command(command)

        assert result.success is True
        assert 0 <= result.data["power_output_kw"] <= 2000.0

    @given(
        wind_speed=st.floats(min_value=0, max_value=50),
        wind_direction=st.floats(min_value=0, max_value=360)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_wind_output_recalculation_speed(self, wind_speed, wind_direction):
        """
        Property 4: Wind Output Recalculation Speed

        For any wind simulator, when weather data is updated, the power output
        should be recalculated and available within 100ms.

        Validates: Requirements 1.3
        """
        wind = WindSimulator("wind-test", {
            "capacity_kw": 2000.0,
            "hub_height": 80,
            "cut_in_speed": 3.0,
            "rated_speed": 12.0,
            "cut_out_speed": 25.0,
            "location": "test"
        })

        import time
        start = time.time()

        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": wind_speed,
                "wind_direction": wind_direction
            }
        )
        result = wind.set_command(command)

        elapsed_ms = (time.time() - start) * 1000

        assert result.success is True
        assert elapsed_ms < 100  # Should complete within 100ms

    @given(
        wind_speed1=st.floats(min_value=3, max_value=12),
        wind_speed2=st.floats(min_value=3, max_value=12),
        wind_direction=st.floats(min_value=0, max_value=360)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_wind_output_monotonic_speed(self, wind_speed1, wind_speed2, wind_direction):
        """
        Property: Wind output increases monotonically with wind speed (in operating range).

        For any wind simulator in the operating range (cut-in to rated), if wind speed
        increases, power output should not decrease.

        Validates: Requirements 1.1, 1.4
        """
        wind = WindSimulator("wind-test", {
            "capacity_kw": 2000.0,
            "hub_height": 80,
            "cut_in_speed": 3.0,
            "rated_speed": 12.0,
            "cut_out_speed": 25.0,
            "location": "test"
        })

        # First measurement
        cmd1 = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": wind_speed1,
                "wind_direction": wind_direction
            }
        )
        result1 = wind.set_command(cmd1)
        power1 = result1.data["power_output_kw"]

        # Second measurement
        cmd2 = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": wind_speed2,
                "wind_direction": wind_direction
            }
        )
        result2 = wind.set_command(cmd2)
        power2 = result2.data["power_output_kw"]

        # If wind speed increases, power should not decrease
        if wind_speed2 > wind_speed1:
            assert power2 >= power1 - 0.01  # Allow small floating point error

    @given(
        capacity=st.floats(min_value=100, max_value=5000),
        hub_height=st.floats(min_value=50, max_value=150)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_wind_scalability(self, capacity, hub_height):
        """
        Property 5: Generator Scalability

        For any set of 1000+ wind generators, the simulator should calculate
        power output for all generators without performance degradation.

        Validates: Requirements 1.5
        """
        import time

        # Create 100 wind simulators (scaled down for testing)
        simulators = [
            WindSimulator(f"wind-{i}", {
                "capacity_kw": capacity,
                "hub_height": hub_height,
                "cut_in_speed": 3.0,
                "rated_speed": 12.0,
                "cut_out_speed": 25.0,
                "location": "test"
            })
            for i in range(100)
        ]

        start = time.time()

        # Update all simulators
        for sim in simulators:
            cmd = DeviceCommand(
                command_type="set_weather",
                parameters={
                    "wind_speed": 10.0,
                    "wind_direction": 0.0
                }
            )
            sim.set_command(cmd)

        elapsed_ms = (time.time() - start) * 1000

        # Should complete 100 updates in reasonable time
        assert elapsed_ms < 500  # 5ms per simulator
