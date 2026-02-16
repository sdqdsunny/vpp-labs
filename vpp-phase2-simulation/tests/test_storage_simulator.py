"""
Unit tests for battery energy storage simulator.

Tests charging/discharging behavior, SOC/SOH tracking, and efficiency modeling.
"""

import pytest
from datetime import datetime

from services.storage_simulator import BatterySimulator
from services.device_emulator import DeviceCommand
from utils.errors import SimulatorError


class TestBatterySimulator:
    """Test battery energy storage simulator."""

    @pytest.fixture
    def battery_params(self):
        """Battery simulator parameters."""
        return {
            "capacity_kwh": 100.0,
            "power_rating_kw": 50.0,
            "efficiency": 0.95,
            "min_soc": 10.0,
            "max_soc": 90.0,
            "initial_soc": 50.0
        }

    @pytest.fixture
    def battery_sim(self, battery_params):
        """Create battery simulator instance."""
        return BatterySimulator("battery-001", battery_params)

    def test_battery_initialization(self, battery_sim):
        """Test battery simulator initialization."""
        assert battery_sim.device_id == "battery-001"
        assert battery_sim.device_type == "battery"
        assert battery_sim.state["soc"] == 50.0
        assert battery_sim.state["soh"] == 100.0
        assert battery_sim.state["status"] == "idle"

    def test_battery_missing_required_parameters(self):
        """Test battery simulator with missing required parameters."""
        with pytest.raises(SimulatorError):
            BatterySimulator("battery-002", {"power_rating_kw": 50.0})

    def test_battery_charging(self, battery_sim):
        """Test battery charging."""
        command = DeviceCommand(
            command_type="charge",
            parameters={
                "power_kw": 50.0,
                "duration_hours": 1.0
            }
        )
        result = battery_sim.set_command(command)

        assert result.success is True
        assert result.data["soc"] > 50.0  # SOC should increase
        assert battery_sim.state["status"] == "charging"

    def test_battery_discharging(self, battery_sim):
        """Test battery discharging."""
        command = DeviceCommand(
            command_type="discharge",
            parameters={
                "power_kw": 30.0,
                "duration_hours": 1.0
            }
        )
        result = battery_sim.set_command(command)

        assert result.success is True
        assert result.data["soc"] < 50.0  # SOC should decrease
        assert battery_sim.state["status"] == "discharging"

    def test_battery_soc_limits(self, battery_sim):
        """Test battery SOC limits enforcement."""
        # Try to charge beyond max SOC
        battery_sim.state["soc"] = 90.0
        command = DeviceCommand(
            command_type="charge",
            parameters={
                "power_kw": 50.0,
                "duration_hours": 1.0
            }
        )
        result = battery_sim.set_command(command)

        assert result.success is False
        assert "maximum" in result.message.lower()

    def test_battery_discharge_at_min_soc(self, battery_sim):
        """Test battery discharge at minimum SOC."""
        battery_sim.state["soc"] = 10.0
        command = DeviceCommand(
            command_type="discharge",
            parameters={
                "power_kw": 30.0,
                "duration_hours": 1.0
            }
        )
        result = battery_sim.set_command(command)

        assert result.success is False
        assert "minimum" in result.message.lower()

    def test_battery_efficiency_loss(self, battery_sim):
        """Test battery efficiency loss during charge/discharge."""
        command = DeviceCommand(
            command_type="charge",
            parameters={
                "power_kw": 50.0,
                "duration_hours": 1.0
            }
        )
        result = battery_sim.set_command(command)

        # Energy loss should be calculated
        assert "energy_loss_kwh" in result.data
        assert result.data["energy_loss_kwh"] > 0

    def test_battery_set_power_positive(self, battery_sim):
        """Test set_power command with positive value (charging)."""
        command = DeviceCommand(
            command_type="set_power",
            parameters={
                "power_kw": 40.0,
                "duration_hours": 1.0
            }
        )
        result = battery_sim.set_command(command)

        assert result.success is True
        assert battery_sim.state["status"] == "charging"

    def test_battery_set_power_negative(self, battery_sim):
        """Test set_power command with negative value (discharging)."""
        command = DeviceCommand(
            command_type="set_power",
            parameters={
                "power_kw": -30.0,
                "duration_hours": 1.0
            }
        )
        result = battery_sim.set_command(command)

        assert result.success is True
        assert battery_sim.state["status"] == "discharging"

    def test_battery_set_power_zero(self, battery_sim):
        """Test set_power command with zero value (idle)."""
        command = DeviceCommand(
            command_type="set_power",
            parameters={
                "power_kw": 0.0,
                "duration_hours": 1.0
            }
        )
        result = battery_sim.set_command(command)

        assert result.success is True
        assert battery_sim.state["status"] == "idle"

    def test_battery_get_available_power(self, battery_sim):
        """Test getting available power."""
        command = DeviceCommand(
            command_type="get_available_power",
            parameters={}
        )
        result = battery_sim.set_command(command)

        assert result.success is True
        assert "charge_power_kw" in result.data
        assert "discharge_power_kw" in result.data
        assert result.data["charge_power_kw"] > 0
        assert result.data["discharge_power_kw"] > 0

    def test_battery_get_available_power_at_max_soc(self, battery_sim):
        """Test available power at maximum SOC."""
        battery_sim.state["soc"] = 90.0
        command = DeviceCommand(
            command_type="get_available_power",
            parameters={}
        )
        result = battery_sim.set_command(command)

        assert result.success is True
        assert result.data["charge_power_kw"] == 0.0  # Can't charge
        assert result.data["discharge_power_kw"] > 0  # Can discharge

    def test_battery_get_available_power_at_min_soc(self, battery_sim):
        """Test available power at minimum SOC."""
        battery_sim.state["soc"] = 10.0
        command = DeviceCommand(
            command_type="get_available_power",
            parameters={}
        )
        result = battery_sim.set_command(command)

        assert result.success is True
        assert result.data["charge_power_kw"] > 0  # Can charge
        assert result.data["discharge_power_kw"] == 0.0  # Can't discharge

    def test_battery_soh_degradation(self, battery_sim):
        """Test battery SOH degradation with cycles."""
        initial_soh = battery_sim.get_soh()
        
        # Simulate multiple charge/discharge cycles
        for _ in range(10):
            battery_sim.state["charge_cycles"] += 1.0
        
        new_soh = battery_sim.get_soh()
        assert new_soh < initial_soh  # SOH should degrade

    def test_battery_voltage_calculation(self, battery_sim):
        """Test battery voltage calculation based on SOC."""
        # At 50% SOC
        voltage_50 = battery_sim._calculate_voltage(50.0)
        
        # At 100% SOC
        voltage_100 = battery_sim._calculate_voltage(100.0)
        
        # At 0% SOC
        voltage_0 = battery_sim._calculate_voltage(0.0)
        
        # Voltage should increase with SOC
        assert voltage_0 < voltage_50 < voltage_100

    def test_battery_get_state(self, battery_sim):
        """Test getting battery state."""
        state = battery_sim.get_state()
        
        assert state.device_id == "battery-001"
        assert state.device_type == "battery"
        assert "soc" in state.state_data
        assert "soh" in state.state_data

    def test_battery_get_capabilities(self, battery_sim):
        """Test getting battery capabilities."""
        capabilities = battery_sim.get_capabilities()

        assert capabilities["device_type"] == "battery"
        assert capabilities["capacity_kwh"] == 100.0
        assert capabilities["power_rating_kw"] == 50.0
        assert "charge" in capabilities["supported_commands"]
        assert "discharge" in capabilities["supported_commands"]

    def test_battery_reset(self, battery_sim):
        """Test battery reset."""
        # Modify state
        battery_sim.state["soc"] = 20.0
        battery_sim.state["charge_cycles"] = 100
        
        # Reset
        battery_sim.reset()
        
        # Should return to initial state
        assert battery_sim.state["soc"] == 50.0
        assert battery_sim.state["charge_cycles"] == 0

    def test_battery_invalid_charge_power(self, battery_sim):
        """Test battery with invalid charge power."""
        command = DeviceCommand(
            command_type="charge",
            parameters={
                "power_kw": -10.0,
                "duration_hours": 1.0
            }
        )
        result = battery_sim.set_command(command)

        assert result.success is False

    def test_battery_invalid_discharge_power(self, battery_sim):
        """Test battery with invalid discharge power."""
        command = DeviceCommand(
            command_type="discharge",
            parameters={
                "power_kw": -10.0,
                "duration_hours": 1.0
            }
        )
        result = battery_sim.set_command(command)

        assert result.success is False

    def test_battery_unknown_command(self, battery_sim):
        """Test battery with unknown command."""
        command = DeviceCommand(
            command_type="unknown_command",
            parameters={}
        )
        result = battery_sim.set_command(command)

        assert result.success is False
