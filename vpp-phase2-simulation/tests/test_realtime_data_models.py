"""
Unit tests for real-time data models.

Tests:
- Data model creation and validation
- Data model serialization
- Data model range validation
"""

import pytest
from datetime import datetime
from models.realtime_data_models import (
    PowerGenerationData, StorageData, DemandData,
    PowerCommand, StorageCommand, DemandCommand,
    CommandResult, CoordinationResult,
    DeviceStatus, ChargeStatus, DRStatus, CommandStatus
)


class TestPowerGenerationData:
    """Test PowerGenerationData model."""

    def test_create_valid_power_data(self):
        """Test creating valid power generation data."""
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        assert data.current_power == 150.5
        assert data.solar_power == 100.0
        assert data.wind_power == 50.5
        assert data.efficiency == 95.5
        assert data.device_status == "running"
        assert data.module_id == "vpp-power-generation"

    def test_power_data_validation_success(self):
        """Test power data validation with valid data."""
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        assert data.validate() is True

    def test_power_data_validation_invalid_efficiency(self):
        """Test power data validation with invalid efficiency."""
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=150.0,  # Invalid: > 100
            device_status="running"
        )
        assert data.validate() is False

    def test_power_data_validation_negative_power(self):
        """Test power data validation with negative power."""
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=-10.0,  # Invalid: negative
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        assert data.validate() is False

    def test_power_data_to_dict(self):
        """Test power data serialization to dict."""
        now = datetime.now()
        data = PowerGenerationData(
            timestamp=now,
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        result = data.to_dict()
        assert result['current_power'] == 150.5
        assert result['solar_power'] == 100.0
        assert result['wind_power'] == 50.5
        assert result['efficiency'] == 95.5
        assert result['device_status'] == "running"
        assert isinstance(result['timestamp'], str)


class TestStorageData:
    """Test StorageData model."""

    def test_create_valid_storage_data(self):
        """Test creating valid storage data."""
        data = StorageData(
            timestamp=datetime.now(),
            soc=75.5,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        assert data.soc == 75.5
        assert data.soh == 98.0
        assert data.current_power == 50.0
        assert data.charge_status == "charging"
        assert data.temperature == 25.5

    def test_storage_data_validation_success(self):
        """Test storage data validation with valid data."""
        data = StorageData(
            timestamp=datetime.now(),
            soc=75.5,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        assert data.validate() is True

    def test_storage_data_validation_invalid_soc(self):
        """Test storage data validation with invalid SOC."""
        data = StorageData(
            timestamp=datetime.now(),
            soc=150.0,  # Invalid: > 100
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        assert data.validate() is False

    def test_storage_data_validation_invalid_temperature(self):
        """Test storage data validation with invalid temperature."""
        data = StorageData(
            timestamp=datetime.now(),
            soc=75.5,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=100.0  # Invalid: > 80
        )
        assert data.validate() is False

    def test_storage_data_to_dict(self):
        """Test storage data serialization to dict."""
        now = datetime.now()
        data = StorageData(
            timestamp=now,
            soc=75.5,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        result = data.to_dict()
        assert result['soc'] == 75.5
        assert result['soh'] == 98.0
        assert result['current_power'] == 50.0
        assert result['charge_status'] == "charging"
        assert result['temperature'] == 25.5


class TestDemandData:
    """Test DemandData model."""

    def test_create_valid_demand_data(self):
        """Test creating valid demand data."""
        data = DemandData(
            timestamp=datetime.now(),
            current_load=200.0,
            forecast_load=210.0,
            adjustable_range=(180.0, 220.0),
            dr_status="active"
        )
        assert data.current_load == 200.0
        assert data.forecast_load == 210.0
        assert data.adjustable_range == (180.0, 220.0)
        assert data.dr_status == "active"

    def test_demand_data_validation_success(self):
        """Test demand data validation with valid data."""
        data = DemandData(
            timestamp=datetime.now(),
            current_load=200.0,
            forecast_load=210.0,
            adjustable_range=(180.0, 220.0),
            dr_status="active"
        )
        assert data.validate() is True

    def test_demand_data_validation_invalid_range(self):
        """Test demand data validation with invalid range."""
        data = DemandData(
            timestamp=datetime.now(),
            current_load=200.0,
            forecast_load=210.0,
            adjustable_range=(220.0, 180.0),  # Invalid: min > max
            dr_status="active"
        )
        assert data.validate() is False

    def test_demand_data_to_dict(self):
        """Test demand data serialization to dict."""
        now = datetime.now()
        data = DemandData(
            timestamp=now,
            current_load=200.0,
            forecast_load=210.0,
            adjustable_range=(180.0, 220.0),
            dr_status="active"
        )
        result = data.to_dict()
        assert result['current_load'] == 200.0
        assert result['forecast_load'] == 210.0
        assert result['adjustable_range'] == [180.0, 220.0]
        assert result['dr_status'] == "active"


class TestPowerCommand:
    """Test PowerCommand model."""

    def test_create_valid_power_command(self):
        """Test creating valid power command."""
        cmd = PowerCommand(
            command_id="cmd_001",
            target_power=160.0,
            duration=300,
            priority=1
        )
        assert cmd.command_id == "cmd_001"
        assert cmd.target_power == 160.0
        assert cmd.duration == 300
        assert cmd.priority == 1

    def test_power_command_validation_success(self):
        """Test power command validation with valid data."""
        cmd = PowerCommand(
            command_id="cmd_001",
            target_power=160.0,
            duration=300,
            priority=1
        )
        assert cmd.validate() is True

    def test_power_command_validation_invalid_priority(self):
        """Test power command validation with invalid priority."""
        cmd = PowerCommand(
            command_id="cmd_001",
            target_power=160.0,
            duration=300,
            priority=15  # Invalid: > 10
        )
        assert cmd.validate() is False

    def test_power_command_to_dict(self):
        """Test power command serialization to dict."""
        cmd = PowerCommand(
            command_id="cmd_001",
            target_power=160.0,
            duration=300,
            priority=1
        )
        result = cmd.to_dict()
        assert result['command_id'] == "cmd_001"
        assert result['target_power'] == 160.0
        assert result['duration'] == 300
        assert result['priority'] == 1


class TestStorageCommand:
    """Test StorageCommand model."""

    def test_create_valid_storage_command(self):
        """Test creating valid storage command."""
        cmd = StorageCommand(
            command_id="cmd_002",
            action="charging",
            target_power=50.0,
            duration=600
        )
        assert cmd.command_id == "cmd_002"
        assert cmd.action == "charging"
        assert cmd.target_power == 50.0
        assert cmd.duration == 600

    def test_storage_command_validation_success(self):
        """Test storage command validation with valid data."""
        cmd = StorageCommand(
            command_id="cmd_002",
            action="charging",
            target_power=50.0,
            duration=600
        )
        assert cmd.validate() is True

    def test_storage_command_validation_invalid_action(self):
        """Test storage command validation with invalid action."""
        cmd = StorageCommand(
            command_id="cmd_002",
            action="invalid",  # Invalid action
            target_power=50.0,
            duration=600
        )
        assert cmd.validate() is False


class TestDemandCommand:
    """Test DemandCommand model."""

    def test_create_valid_demand_command(self):
        """Test creating valid demand command."""
        cmd = DemandCommand(
            command_id="cmd_003",
            action="decrease",
            target_load=180.0,
            duration=300
        )
        assert cmd.command_id == "cmd_003"
        assert cmd.action == "decrease"
        assert cmd.target_load == 180.0
        assert cmd.duration == 300

    def test_demand_command_validation_success(self):
        """Test demand command validation with valid data."""
        cmd = DemandCommand(
            command_id="cmd_003",
            action="decrease",
            target_load=180.0,
            duration=300
        )
        assert cmd.validate() is True

    def test_demand_command_validation_invalid_action(self):
        """Test demand command validation with invalid action."""
        cmd = DemandCommand(
            command_id="cmd_003",
            action="invalid",  # Invalid action
            target_load=180.0,
            duration=300
        )
        assert cmd.validate() is False


class TestCommandResult:
    """Test CommandResult model."""

    def test_create_command_result(self):
        """Test creating command result."""
        result = CommandResult(
            command_id="cmd_001",
            status="completed",
            result={"power_adjusted": 160.0},
            executed_at=datetime.now()
        )
        assert result.command_id == "cmd_001"
        assert result.status == "completed"
        assert result.result["power_adjusted"] == 160.0

    def test_command_result_to_dict(self):
        """Test command result serialization to dict."""
        now = datetime.now()
        result = CommandResult(
            command_id="cmd_001",
            status="completed",
            result={"power_adjusted": 160.0},
            executed_at=now
        )
        data = result.to_dict()
        assert data['command_id'] == "cmd_001"
        assert data['status'] == "completed"
        assert isinstance(data['executed_at'], str)


class TestCoordinationResult:
    """Test CoordinationResult model."""

    def test_create_coordination_result(self):
        """Test creating coordination result."""
        power_cmd = PowerCommand("cmd_001", 160.0, 300, 1)
        storage_cmd = StorageCommand("cmd_002", "charging", 50.0, 600)
        demand_cmd = DemandCommand("cmd_003", "decrease", 180.0, 300)
        
        result = CoordinationResult(
            timestamp=datetime.now(),
            power_command=power_cmd,
            storage_command=storage_cmd,
            demand_command=demand_cmd,
            optimization_score=92.5,
            status="success"
        )
        assert result.optimization_score == 92.5
        assert result.status == "success"

    def test_coordination_result_to_dict(self):
        """Test coordination result serialization to dict."""
        power_cmd = PowerCommand("cmd_001", 160.0, 300, 1)
        storage_cmd = StorageCommand("cmd_002", "charging", 50.0, 600)
        demand_cmd = DemandCommand("cmd_003", "decrease", 180.0, 300)
        
        result = CoordinationResult(
            timestamp=datetime.now(),
            power_command=power_cmd,
            storage_command=storage_cmd,
            demand_command=demand_cmd,
            optimization_score=92.5,
            status="success"
        )
        data = result.to_dict()
        assert data['optimization_score'] == 92.5
        assert data['status'] == "success"
        assert 'power_command' in data
        assert 'storage_command' in data
        assert 'demand_command' in data
