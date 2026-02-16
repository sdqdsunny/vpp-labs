"""
Unit tests for demand-side load simulator.

Tests load profile generation, demand response, and flexibility modeling.
"""

import pytest
from datetime import datetime

from services.demand_simulator import LoadSimulator
from services.device_emulator import DeviceCommand
from utils.errors import SimulatorError


class TestLoadSimulator:
    """Test demand-side load simulator."""

    @pytest.fixture
    def load_params(self):
        """Load simulator parameters."""
        return {
            "base_load_kw": 100.0,
            "min_load_kw": 80.0,
            "max_load_kw": 120.0,
            "flexibility_range": (0.8, 1.2)
        }

    @pytest.fixture
    def load_sim(self, load_params):
        """Create load simulator instance."""
        return LoadSimulator("load-001", load_params)

    def test_load_initialization(self, load_sim):
        """Test load simulator initialization."""
        assert load_sim.device_id == "load-001"
        assert load_sim.device_type == "load"
        assert load_sim.state["current_load_kw"] == 100.0
        assert load_sim.state["base_load_kw"] == 100.0
        assert load_sim.state["demand_response_signal"] == 1.0

    def test_load_missing_required_parameters(self):
        """Test load simulator with missing required parameters."""
        with pytest.raises(SimulatorError):
            LoadSimulator("load-002", {})

    def test_load_get_current_load(self, load_sim):
        """Test getting current load."""
        command = DeviceCommand(
            command_type="get_current_load",
            parameters={}
        )
        result = load_sim.set_command(command)

        assert result.success is True
        assert result.data["current_load_kw"] == 100.0

    def test_load_demand_response_reduction(self, load_sim):
        """Test demand response signal for load reduction."""
        command = DeviceCommand(
            command_type="set_demand_response",
            parameters={"signal": 0.8}  # 20% reduction
        )
        result = load_sim.set_command(command)

        assert result.success is True
        assert result.data["current_load_kw"] < 100.0
        assert load_sim.state["status"] == "reduced"

    def test_load_demand_response_increase(self, load_sim):
        """Test demand response signal for load increase."""
        # Set hour to noon (peak load time)
        load_sim.state["hour_of_day"] = 12.0
        
        command = DeviceCommand(
            command_type="set_demand_response",
            parameters={"signal": 1.2}  # 20% increase
        )
        result = load_sim.set_command(command)

        assert result.success is True
        # Load should increase but be clamped to max_load_kw (120.0)
        assert result.data["current_load_kw"] >= 100.0
        assert load_sim.state["status"] == "increased"

    def test_load_demand_response_normal(self, load_sim):
        """Test demand response signal for normal operation."""
        # Set hour to noon (peak load time)
        load_sim.state["hour_of_day"] = 12.0
        
        command = DeviceCommand(
            command_type="set_demand_response",
            parameters={"signal": 1.0}
        )
        result = load_sim.set_command(command)

        assert result.success is True
        # At signal 1.0 and noon, load should be close to base load
        assert result.data["current_load_kw"] >= 90.0  # Allow for daily pattern
        assert load_sim.state["status"] == "normal"

    def test_load_demand_response_invalid_signal_low(self, load_sim):
        """Test demand response with invalid signal (too low)."""
        command = DeviceCommand(
            command_type="set_demand_response",
            parameters={"signal": 0.3}  # Below 0.5
        )
        result = load_sim.set_command(command)

        assert result.success is False

    def test_load_demand_response_invalid_signal_high(self, load_sim):
        """Test demand response with invalid signal (too high)."""
        command = DeviceCommand(
            command_type="set_demand_response",
            parameters={"signal": 1.8}  # Above 1.5
        )
        result = load_sim.set_command(command)

        assert result.success is False

    def test_load_flexibility_range(self, load_sim):
        """Test getting flexibility range."""
        command = DeviceCommand(
            command_type="get_flexibility_range",
            parameters={}
        )
        result = load_sim.set_command(command)

        assert result.success is True
        assert result.data["min_load_kw"] == 80.0
        assert result.data["max_load_kw"] == 120.0

    def test_load_clamped_to_flexibility_range(self, load_sim):
        """Test that load is clamped to flexibility range."""
        # Set demand response to extreme value
        command = DeviceCommand(
            command_type="set_demand_response",
            parameters={"signal": 1.5}  # Maximum
        )
        load_sim.set_command(command)

        # Load should not exceed max
        assert load_sim.state["current_load_kw"] <= 120.0

    def test_load_daily_pattern(self, load_sim):
        """Test daily load pattern generation."""
        pattern = load_sim.state["daily_pattern"]

        # Pattern should have 24 hours
        assert len(pattern) == 24

        # All factors should be between 0.5 and 1.5
        for hour, factor in pattern.items():
            assert 0.5 <= factor <= 1.5

    def test_load_forecast_generation(self, load_sim):
        """Test load forecast generation."""
        command = DeviceCommand(
            command_type="get_load_forecast",
            parameters={"hours": 24}
        )
        result = load_sim.set_command(command)

        assert result.success is True
        assert len(result.data["forecast_kw"]) == 24

        # All forecasted loads should be within flexibility range
        for load in result.data["forecast_kw"]:
            assert 80.0 <= load <= 120.0

    def test_load_forecast_with_demand_response(self, load_sim):
        """Test load forecast with demand response signal."""
        # Set demand response
        dr_command = DeviceCommand(
            command_type="set_demand_response",
            parameters={"signal": 0.9}
        )
        load_sim.set_command(dr_command)

        # Get forecast
        forecast_command = DeviceCommand(
            command_type="get_load_forecast",
            parameters={"hours": 24}
        )
        result = load_sim.set_command(forecast_command)

        assert result.success is True
        # Forecast should reflect reduced demand
        avg_forecast = sum(result.data["forecast_kw"]) / len(result.data["forecast_kw"])
        assert avg_forecast < 100.0

    def test_load_seasonal_factor(self, load_sim):
        """Test seasonal factor adjustment."""
        initial_load = load_sim.get_current_load()

        # Apply summer factor (higher load)
        load_sim.set_seasonal_factor(1.2)
        summer_load = load_sim.get_current_load()

        # Reset and apply winter factor (lower load)
        load_sim.set_seasonal_factor(1.0)
        normal_load = load_sim.get_current_load()

        load_sim.set_seasonal_factor(0.8)
        winter_load = load_sim.get_current_load()

        # Summer >= Normal >= Winter (accounting for clamping)
        assert summer_load >= normal_load >= winter_load

    def test_load_seasonal_factor_clamped(self, load_sim):
        """Test seasonal factor is clamped to valid range."""
        # Try to set extreme values
        load_sim.set_seasonal_factor(2.0)  # Should be clamped to 1.5
        assert load_sim.state["seasonal_factor"] == 1.5

        load_sim.set_seasonal_factor(0.2)  # Should be clamped to 0.5
        assert load_sim.state["seasonal_factor"] == 0.5

    def test_load_update_with_time_delta(self, load_sim):
        """Test load update with time delta."""
        initial_hour = load_sim.state["hour_of_day"]

        # Update with 1 hour time delta
        load_sim.update(3600.0)  # 3600 seconds = 1 hour

        # Hour should advance
        assert load_sim.state["hour_of_day"] > initial_hour

    def test_load_get_state(self, load_sim):
        """Test getting load state."""
        state = load_sim.get_state()

        assert state.device_id == "load-001"
        assert state.device_type == "load"
        assert "current_load_kw" in state.state_data
        assert "demand_response_signal" in state.state_data

    def test_load_get_capabilities(self, load_sim):
        """Test getting load capabilities."""
        capabilities = load_sim.get_capabilities()

        assert capabilities["device_type"] == "load"
        assert capabilities["base_load_kw"] == 100.0
        assert "set_demand_response" in capabilities["supported_commands"]
        assert "get_current_load" in capabilities["supported_commands"]
        assert "get_load_forecast" in capabilities["supported_commands"]

    def test_load_reset(self, load_sim):
        """Test load reset."""
        # Modify state
        load_sim.state["demand_response_signal"] = 0.8
        load_sim.state["seasonal_factor"] = 1.2
        load_sim.state["hour_of_day"] = 12.0

        # Reset
        load_sim.reset()

        # Should return to initial state
        assert load_sim.state["demand_response_signal"] == 1.0
        assert load_sim.state["seasonal_factor"] == 1.0
        assert load_sim.state["hour_of_day"] == 0

    def test_load_unknown_command(self, load_sim):
        """Test load with unknown command."""
        command = DeviceCommand(
            command_type="unknown_command",
            parameters={}
        )
        result = load_sim.set_command(command)

        assert result.success is False

    def test_load_get_current_load_method(self, load_sim):
        """Test get_current_load method."""
        load = load_sim.get_current_load()
        assert load == 100.0

    def test_load_get_load_forecast_method(self, load_sim):
        """Test get_load_forecast method."""
        forecast = load_sim.get_load_forecast(24)
        assert len(forecast) == 24

    def test_load_get_flexibility_range_method(self, load_sim):
        """Test get_flexibility_range method."""
        min_load, max_load = load_sim.get_flexibility_range()
        assert min_load == 80.0
        assert max_load == 120.0
