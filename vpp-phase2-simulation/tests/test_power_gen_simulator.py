"""
Unit tests for power generation simulators (solar and wind).

Tests solar and wind power output calculations, weather data integration,
and efficiency modeling.
"""

import pytest
import math
from datetime import datetime

from services.power_gen_simulator import SolarSimulator, WindSimulator, WeatherData
from services.device_emulator import DeviceCommand
from utils.errors import SimulatorError


class TestSolarSimulator:
    """Test solar power generation simulator."""

    @pytest.fixture
    def solar_params(self):
        """Solar simulator parameters."""
        return {
            "capacity_kw": 10.0,
            "efficiency": 0.18,
            "temperature_coefficient": -0.004,
            "location": "test_location"
        }

    @pytest.fixture
    def solar_sim(self, solar_params):
        """Create solar simulator instance."""
        return SolarSimulator("solar-001", solar_params)

    def test_solar_initialization(self, solar_sim):
        """Test solar simulator initialization."""
        assert solar_sim.device_id == "solar-001"
        assert solar_sim.device_type == "solar"
        assert solar_sim.state["power_output_kw"] == 0.0
        assert solar_sim.state["status"] == "idle"

    def test_solar_missing_required_parameters(self):
        """Test solar simulator with missing required parameters."""
        with pytest.raises(SimulatorError):
            SolarSimulator("solar-002", {"efficiency": 0.18})

    def test_solar_power_calculation_at_reference_conditions(self, solar_sim):
        """Test solar power calculation at reference conditions (1000 W/m², 25°C)."""
        # At reference conditions, power should be capacity × efficiency
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": 1000.0,
                "temperature": 25.0
            }
        )
        result = solar_sim.set_command(command)

        assert result.success is True
        expected_power = 10.0 * 0.18  # capacity × efficiency
        assert abs(result.data["power_output_kw"] - expected_power) < 0.01

    def test_solar_power_calculation_half_irradiance(self, solar_sim):
        """Test solar power calculation at half irradiance."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": 500.0,
                "temperature": 25.0
            }
        )
        result = solar_sim.set_command(command)

        assert result.success is True
        expected_power = 10.0 * 0.18 * 0.5  # capacity × efficiency × (irradiance/reference)
        assert abs(result.data["power_output_kw"] - expected_power) < 0.01

    def test_solar_power_calculation_zero_irradiance(self, solar_sim):
        """Test solar power calculation with zero irradiance."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": 0.0,
                "temperature": 25.0
            }
        )
        result = solar_sim.set_command(command)

        assert result.success is True
        assert result.data["power_output_kw"] == 0.0

    def test_solar_temperature_effect_on_efficiency(self, solar_sim):
        """Test temperature effect on solar efficiency."""
        # Higher temperature reduces efficiency
        command_hot = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": 1000.0,
                "temperature": 45.0  # 20°C above reference
            }
        )
        result_hot = solar_sim.set_command(command_hot)
        power_hot = result_hot.data["power_output_kw"]

        # Reset and test at reference temperature
        solar_sim.reset()
        command_ref = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": 1000.0,
                "temperature": 25.0
            }
        )
        result_ref = solar_sim.set_command(command_ref)
        power_ref = result_ref.data["power_output_kw"]

        # Power at higher temperature should be less
        assert power_hot < power_ref

    def test_solar_power_clamped_to_capacity(self, solar_sim):
        """Test that solar power is clamped to capacity."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": 2000.0,  # Above reference
                "temperature": 25.0
            }
        )
        result = solar_sim.set_command(command)

        assert result.success is True
        assert result.data["power_output_kw"] <= 10.0  # capacity

    def test_solar_invalid_irradiance(self, solar_sim):
        """Test solar simulator with invalid irradiance."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": -100.0,
                "temperature": 25.0
            }
        )
        result = solar_sim.set_command(command)

        assert result.success is False

    def test_solar_get_state(self, solar_sim):
        """Test getting solar simulator state."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": 800.0,
                "temperature": 30.0
            }
        )
        solar_sim.set_command(command)

        state = solar_sim.get_state()
        assert state.device_id == "solar-001"
        assert state.device_type == "solar"
        assert state.state_data["solar_irradiance"] == 800.0
        assert state.state_data["temperature"] == 30.0

    def test_solar_get_capabilities(self, solar_sim):
        """Test getting solar simulator capabilities."""
        capabilities = solar_sim.get_capabilities()

        assert capabilities["device_type"] == "solar"
        assert capabilities["capacity_kw"] == 10.0
        assert "set_weather" in capabilities["supported_commands"]
        assert "get_forecast" in capabilities["supported_commands"]

    def test_solar_get_forecast(self, solar_sim):
        """Test solar power forecast."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": 1000.0,
                "temperature": 25.0
            }
        )
        solar_sim.set_command(command)

        forecast_cmd = DeviceCommand(
            command_type="get_forecast",
            parameters={"hours": 24}
        )
        result = solar_sim.set_command(forecast_cmd)

        assert result.success is True
        assert len(result.data["forecast_kw"]) == 24

    def test_solar_reset(self, solar_sim):
        """Test solar simulator reset."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "solar_irradiance": 1000.0,
                "temperature": 25.0
            }
        )
        solar_sim.set_command(command)
        assert solar_sim.state["power_output_kw"] > 0

        solar_sim.reset()
        assert solar_sim.state["power_output_kw"] == 0.0
        assert solar_sim.state["status"] == "idle"


class TestWindSimulator:
    """Test wind power generation simulator."""

    @pytest.fixture
    def wind_params(self):
        """Wind simulator parameters."""
        return {
            "capacity_kw": 2000.0,
            "hub_height": 80,
            "cut_in_speed": 3.0,
            "rated_speed": 12.0,
            "cut_out_speed": 25.0,
            "location": "test_location"
        }

    @pytest.fixture
    def wind_sim(self, wind_params):
        """Create wind simulator instance."""
        return WindSimulator("wind-001", wind_params)

    def test_wind_initialization(self, wind_sim):
        """Test wind simulator initialization."""
        assert wind_sim.device_id == "wind-001"
        assert wind_sim.device_type == "wind"
        assert wind_sim.state["power_output_kw"] == 0.0
        assert wind_sim.state["status"] == "idle"

    def test_wind_missing_required_parameters(self):
        """Test wind simulator with missing required parameters."""
        with pytest.raises(SimulatorError):
            WindSimulator("wind-002", {"hub_height": 80})

    def test_wind_power_below_cut_in(self, wind_sim):
        """Test wind power below cut-in speed."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": 2.0,  # Below cut-in (3.0)
                "wind_direction": 0.0
            }
        )
        result = wind_sim.set_command(command)

        assert result.success is True
        assert result.data["power_output_kw"] == 0.0

    def test_wind_power_at_cut_in(self, wind_sim):
        """Test wind power at cut-in speed."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": 3.0,  # At cut-in
                "wind_direction": 0.0
            }
        )
        result = wind_sim.set_command(command)

        assert result.success is True
        assert result.data["power_output_kw"] >= 0.0

    def test_wind_power_at_rated_speed(self, wind_sim):
        """Test wind power at rated speed."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": 12.0,  # At rated speed
                "wind_direction": 0.0
            }
        )
        result = wind_sim.set_command(command)

        assert result.success is True
        assert abs(result.data["power_output_kw"] - 2000.0) < 0.1  # Should be at capacity

    def test_wind_power_above_cut_out(self, wind_sim):
        """Test wind power above cut-out speed."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": 30.0,  # Above cut-out (25.0)
                "wind_direction": 0.0
            }
        )
        result = wind_sim.set_command(command)

        assert result.success is True
        assert result.data["power_output_kw"] == 0.0

    def test_wind_power_curve_cubic_relationship(self, wind_sim):
        """Test wind power curve follows cubic relationship."""
        # Test at 50% of rated speed
        mid_speed = 7.5  # (3.0 + 12.0) / 2
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": mid_speed,
                "wind_direction": 0.0
            }
        )
        result = wind_sim.set_command(command)

        # At 50% speed, power should be 0.5^3 = 12.5% of capacity
        expected_power = 2000.0 * (0.5 ** 3)
        assert abs(result.data["power_output_kw"] - expected_power) < 1.0

    def test_wind_invalid_wind_speed(self, wind_sim):
        """Test wind simulator with invalid wind speed."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": -10.0,
                "wind_direction": 0.0
            }
        )
        result = wind_sim.set_command(command)

        assert result.success is False

    def test_wind_get_state(self, wind_sim):
        """Test getting wind simulator state."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": 10.0,
                "wind_direction": 180.0
            }
        )
        wind_sim.set_command(command)

        state = wind_sim.get_state()
        assert state.device_id == "wind-001"
        assert state.device_type == "wind"
        assert state.state_data["wind_speed"] == 10.0
        assert state.state_data["wind_direction"] == 180.0

    def test_wind_get_capabilities(self, wind_sim):
        """Test getting wind simulator capabilities."""
        capabilities = wind_sim.get_capabilities()

        assert capabilities["device_type"] == "wind"
        assert capabilities["capacity_kw"] == 2000.0
        assert capabilities["hub_height"] == 80
        assert "set_weather" in capabilities["supported_commands"]

    def test_wind_get_forecast(self, wind_sim):
        """Test wind power forecast."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": 12.0,
                "wind_direction": 0.0
            }
        )
        wind_sim.set_command(command)

        forecast_cmd = DeviceCommand(
            command_type="get_forecast",
            parameters={"hours": 48}
        )
        result = wind_sim.set_command(forecast_cmd)

        assert result.success is True
        assert len(result.data["forecast_kw"]) == 48

    def test_wind_reset(self, wind_sim):
        """Test wind simulator reset."""
        command = DeviceCommand(
            command_type="set_weather",
            parameters={
                "wind_speed": 15.0,
                "wind_direction": 0.0
            }
        )
        wind_sim.set_command(command)
        assert wind_sim.state["power_output_kw"] > 0

        wind_sim.reset()
        assert wind_sim.state["power_output_kw"] == 0.0
        assert wind_sim.state["status"] == "idle"

    def test_wind_unknown_command(self, wind_sim):
        """Test wind simulator with unknown command."""
        command = DeviceCommand(
            command_type="unknown_command",
            parameters={}
        )
        result = wind_sim.set_command(command)

        assert result.success is False


class TestWeatherData:
    """Test weather data class."""

    def test_weather_data_creation(self):
        """Test weather data creation."""
        weather = WeatherData(
            solar_irradiance=800.0,
            temperature=25.0,
            wind_speed=10.0,
            wind_direction=180.0
        )

        assert weather.solar_irradiance == 800.0
        assert weather.temperature == 25.0
        assert weather.wind_speed == 10.0
        assert weather.wind_direction == 180.0
        assert weather.timestamp is not None

    def test_weather_data_with_timestamp(self):
        """Test weather data with explicit timestamp."""
        now = datetime.utcnow()
        weather = WeatherData(
            solar_irradiance=800.0,
            temperature=25.0,
            wind_speed=10.0,
            wind_direction=180.0,
            timestamp=now
        )

        assert weather.timestamp == now
