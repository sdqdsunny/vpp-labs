"""
Unit tests for VCC Coordination Service.

Tests:
- Data collection and coordination
- Optimal schedule calculation
- Command generation
- Coordination algorithm logic
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from models.realtime_data_models import (
    PowerGenerationData, StorageData, DemandData,
    PowerCommand, StorageCommand, DemandCommand,
    CoordinationResult
)
from services.vcc_coordination import CoordinationService


class TestCoordinationServiceInitialization:
    """Test coordination service initialization."""

    def test_initialization(self):
        """Test service initialization."""
        service = CoordinationService()
        assert service.last_power_data is None
        assert service.last_storage_data is None
        assert service.last_demand_data is None
        assert service.coordination_count == 0
        assert service.last_coordination_time is None

    def test_get_stats_initial(self):
        """Test getting stats on initialization."""
        service = CoordinationService()
        stats = service.get_stats()
        
        assert stats["coordination_count"] == 0
        assert stats["last_coordination_time"] is None
        assert stats["has_power_data"] is False
        assert stats["has_storage_data"] is False
        assert stats["has_demand_data"] is False


class TestDataCollection:
    """Test data collection."""

    def test_set_power_data(self):
        """Test setting power data."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        
        service.set_latest_data(power_data=power_data)
        assert service.last_power_data == power_data

    def test_set_storage_data(self):
        """Test setting storage data."""
        service = CoordinationService()
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        
        service.set_latest_data(storage_data=storage_data)
        assert service.last_storage_data == storage_data

    def test_set_demand_data(self):
        """Test setting demand data."""
        service = CoordinationService()
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        service.set_latest_data(demand_data=demand_data)
        assert service.last_demand_data == demand_data

    def test_set_all_data(self):
        """Test setting all data at once."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        service.set_latest_data(power_data=power_data, storage_data=storage_data, demand_data=demand_data)
        
        assert service.last_power_data == power_data
        assert service.last_storage_data == storage_data
        assert service.last_demand_data == demand_data


class TestOptimalScheduleCalculation:
    """Test optimal schedule calculation."""

    def test_calculate_schedule_balanced_load(self):
        """Test schedule calculation with balanced load."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        power_cmd, storage_cmd, demand_cmd, score = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        assert isinstance(power_cmd, PowerCommand)
        assert isinstance(storage_cmd, StorageCommand)
        assert isinstance(demand_cmd, DemandCommand)
        assert 0 <= score <= 100
        assert power_cmd.target_power > 0
        assert storage_cmd.duration == 300
        assert demand_cmd.duration == 300

    def test_calculate_schedule_high_soc(self):
        """Test schedule calculation with high SOC."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=85.0,  # High SOC
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        power_cmd, storage_cmd, demand_cmd, score = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        # With high SOC, should discharge
        assert storage_cmd.action == "discharging"
        assert score > 70  # Good score with high SOC

    def test_calculate_schedule_low_soc(self):
        """Test schedule calculation with low SOC."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=15.0,  # Low SOC
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        power_cmd, storage_cmd, demand_cmd, score = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        # With low SOC, should charge
        assert storage_cmd.action == "charging"

    def test_calculate_schedule_power_shortage(self):
        """Test schedule calculation with power shortage."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=30.0,  # Very low power
            solar_power=20.0,
            wind_power=10.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=150.0,  # High demand
            forecast_load=160.0,
            adjustable_range=(80.0, 200.0),
            dr_status="active"
        )
        
        power_cmd, storage_cmd, demand_cmd, score = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        # With shortage (30 + 100 = 130 < 150), should discharge storage and reduce demand
        assert storage_cmd.action == "discharging"
        assert demand_cmd.action == "decrease"
        assert score < 80  # Lower score due to shortage

    def test_calculate_schedule_excess_power(self):
        """Test schedule calculation with excess power."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=200.0,  # High power
            solar_power=150.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=50.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,  # Low demand
            forecast_load=110.0,
            adjustable_range=(80.0, 150.0),
            dr_status="active"
        )
        
        power_cmd, storage_cmd, demand_cmd, score = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        # With excess power, can increase demand
        assert demand_cmd.action == "increase"
        assert score > 80  # Good score with excess power

    def test_calculate_schedule_target_load_within_range(self):
        """Test that target load stays within adjustable range."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        power_cmd, storage_cmd, demand_cmd, score = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        # Target load should be within range
        assert demand_data.adjustable_range[0] <= demand_cmd.target_load <= demand_data.adjustable_range[1]


class TestCoordination:
    """Test coordination execution."""

    def test_coordinate_without_data(self):
        """Test coordination without data."""
        service = CoordinationService()
        result = service.coordinate()
        
        assert result is None

    def test_coordinate_with_incomplete_data(self):
        """Test coordination with incomplete data."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        
        service.set_latest_data(power_data=power_data)
        result = service.coordinate()
        
        assert result is None

    def test_coordinate_with_all_data(self):
        """Test coordination with all data."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        service.set_latest_data(power_data=power_data, storage_data=storage_data, demand_data=demand_data)
        result = service.coordinate()
        
        assert result is not None
        assert isinstance(result, CoordinationResult)
        assert result.status == "success"
        assert 0 <= result.optimization_score <= 100
        assert service.coordination_count == 1
        assert service.last_coordination_time is not None

    def test_coordinate_multiple_times(self):
        """Test multiple coordination executions."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        service.set_latest_data(power_data=power_data, storage_data=storage_data, demand_data=demand_data)
        
        for i in range(3):
            result = service.coordinate()
            assert result is not None
            assert service.coordination_count == i + 1


class TestCommandGeneration:
    """Test command generation."""

    def test_power_command_validity(self):
        """Test power command validity."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        power_cmd, _, _, _ = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        assert power_cmd.validate()
        assert power_cmd.target_power > 0
        assert power_cmd.duration > 0
        assert 1 <= power_cmd.priority <= 10

    def test_storage_command_validity(self):
        """Test storage command validity."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        _, storage_cmd, _, _ = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        assert storage_cmd.validate()
        assert storage_cmd.action in ["charging", "discharging", "idle"]
        assert storage_cmd.target_power >= 0
        assert storage_cmd.duration > 0

    def test_demand_command_validity(self):
        """Test demand command validity."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        _, _, demand_cmd, _ = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        assert demand_cmd.validate()
        assert demand_cmd.action in ["increase", "decrease", "maintain"]
        assert demand_cmd.target_load > 0
        assert demand_cmd.duration > 0


class TestCoordinationAlgorithm:
    """Test coordination algorithm logic."""

    def test_algorithm_meets_demand_when_possible(self):
        """Test that algorithm tries to meet demand when possible."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=200.0,  # Sufficient power
            solar_power=150.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=150.0,
            forecast_load=160.0,
            adjustable_range=(100.0, 200.0),
            dr_status="active"
        )
        
        _, _, demand_cmd, score = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        # Should maintain or increase demand
        assert demand_cmd.action in ["maintain", "increase"]
        assert score > 70

    def test_algorithm_reduces_demand_on_shortage(self):
        """Test that algorithm reduces demand on shortage."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=50.0,  # Insufficient power
            solar_power=30.0,
            wind_power=20.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=30.0,  # Low SOC, limited discharge
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=200.0,  # High demand
            forecast_load=210.0,
            adjustable_range=(100.0, 250.0),
            dr_status="active"
        )
        
        _, _, demand_cmd, score = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        # Should reduce demand
        assert demand_cmd.action == "decrease"
        assert demand_cmd.target_load < demand_data.current_load
        assert score < 80

    def test_algorithm_charges_storage_when_low(self):
        """Test that algorithm charges storage when SOC is low."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=15.0,  # Very low SOC
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="active"
        )
        
        _, storage_cmd, _, _ = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        # Should charge storage
        assert storage_cmd.action == "charging"
        assert storage_cmd.target_power > 0

    def test_algorithm_discharges_storage_when_high(self):
        """Test that algorithm discharges storage when SOC is high."""
        service = CoordinationService()
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=100.0,
            solar_power=70.0,
            wind_power=30.0,
            efficiency=95.0,
            device_status="running"
        )
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=90.0,  # Very high SOC
            soh=98.0,
            current_power=50.0,
            charge_status="idle",
            temperature=25.0
        )
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=150.0,
            forecast_load=160.0,
            adjustable_range=(100.0, 200.0),
            dr_status="active"
        )
        
        _, storage_cmd, _, _ = service.calculate_optimal_schedule(
            power_data, storage_data, demand_data
        )
        
        # Should discharge storage
        assert storage_cmd.action == "discharging"
